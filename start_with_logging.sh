#!/bin/bash

# 增强版启动脚本 - 包含日志重定向
# 非入侵式日志收集

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "=== 带日志收集的LiteLLM服务启动 ==="

# 创建日志目录
mkdir -p logs

# 创建基于日期的日志目录结构
create_log_dirs() {
    local year=$(date +%Y)
    local month=$(date +%m)
    local day=$(date +%d)
    local log_date_dir="logs/$year/$month/$day"
    mkdir -p "$log_date_dir"
    echo "$log_date_dir"
}

# 获取日志目录
LOG_DATE_DIR=$(create_log_dirs)
echo "📁 日志目录: $LOG_DATE_DIR"

# 设置日志环境变量
export LITELLM_LOG=DEBUG
export LITELLM_SET_VERBOSE=true
export PYTHON_LOG_LEVEL=DEBUG

# 设置Python根日志级别为INFO，确保custom_handler日志可见
export PYTHONUNBUFFERED=1
export LITELLM_LOG_LEVEL=INFO

# 配置Python日志
export PYTHONPATH="${PYTHONPATH}:."
if [ -f "logging.yaml" ]; then
    echo "使用logging.yaml配置Python日志"
    python -c "
import logging.config
import yaml
try:
    with open('logging.yaml', 'r') as f:
        config = yaml.safe_load(f)
        print('YAML配置加载完成')
        # 检查配置完整性
        if config and 'loggers' in config and config['loggers'] is not None:
            logging.config.dictConfig(config)
            print('✅ Python日志配置加载成功')
        else:
            print('⚠️ logging.yaml配置不完整，使用基础配置')
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
except Exception as e:
    print(f'❌ 日志配置加载失败: {e}')
    print('使用基础日志配置')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
" || echo "日志配置出错，继续启动..."
else
    echo "⚠️ logging.yaml文件不存在，使用默认配置"
fi

# 启动业务API（带日志重定向）
echo ""
echo "=== 启动业务API（带日志） ==="
cd "$PROJECT_ROOT"
python productAdapter/api/business_api_example.py --port 8002 --host 0.0.0.0 \
    2>&1 | tee -a "$LOG_DATE_DIR/business_api.log" &
BUSINESS_API_PID=$!

echo "业务API进程ID: $BUSINESS_API_PID"

# 等待业务API启动
echo "等待业务API启动..."
sleep 5

# 检查业务API
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✓ 业务API启动成功"
else
    echo "✗ 业务API启动失败"
    kill $BUSINESS_API_PID 2>/dev/null || true
    exit 1
fi

# 启动LiteLLM代理（带详细日志和重定向）
echo ""
echo "=== 启动LiteLLM代理（带详细日志） ==="
litellm --config config.yaml --host 0.0.0.0 --port 8080 --detailed_debug \
    2>&1 | tee -a "$LOG_DATE_DIR/litellm.log" &
LITELLM_PROXY_PID=$!

echo "LiteLLM代理进程ID: $LITELLM_PROXY_PID"

# 等待LiteLLM代理启动
echo "等待LiteLLM代理启动..."
sleep 10

# 检查LiteLLM代理
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ LiteLLM代理启动成功"
else
    echo "✗ LiteLLM代理启动失败"
    echo "检查日志文件: $LOG_DATE_DIR/litellm.log"
fi

echo ""
echo "=== 服务启动完成 ==="
echo "业务API: http://localhost:8002"
echo "LiteLLM代理: http://localhost:8080"
echo ""
echo "日志文件位置:"
echo "- 业务API: $LOG_DATE_DIR/business_api.log"
echo "- LiteLLM代理: $LOG_DATE_DIR/litellm.log (包含自定义处理器日志)"
echo ""
echo "停止服务:"
echo "pkill -f 'business_api_example.py'"
echo "pkill -f litellm"

# 保存进程ID
echo "$BUSINESS_API_PID" > /tmp/business_api.pid
echo "$LITELLM_PROXY_PID" > /tmp/litellm_proxy.pid