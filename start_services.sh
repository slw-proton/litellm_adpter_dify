#!/bin/bash

# LiteLLM适配器服务启动脚本
# 用于启动业务API和LiteLLM代理服务

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "=== LiteLLM适配器服务启动脚本 ==="
echo "项目根目录: $PROJECT_ROOT"

# 检查环境配置文件
ENV_FILE="$PROJECT_ROOT/productAdapter/config/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "警告: 环境配置文件 $ENV_FILE 不存在"
    echo "将使用默认配置"
else
    echo "找到环境配置文件: $ENV_FILE"
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: Python未安装或不在PATH中"
    exit 1
fi

echo "Python版本: $(python --version)"

# 检查依赖
echo "检查Python依赖..."
cd "$PROJECT_ROOT"
python -c "import fastapi, uvicorn, litellm, requests" 2>/dev/null || {
    echo "错误: 缺少必要的Python依赖"
    echo "请运行: pip install -r requirements.txt"
    exit 1
}

# 启动业务API
echo ""
echo "=== 启动业务API ==="
echo "端口: 8002"
echo "主机: 0.0.0.0"

# 在后台启动业务API
cd "$PROJECT_ROOT"
python productAdapter/api/business_api_example.py --env-file "$ENV_FILE" --port 8002 --host 0.0.0.0 &
BUSINESS_API_PID=$!

echo "业务API进程ID: $BUSINESS_API_PID"

# 等待业务API启动
echo "等待业务API启动..."
sleep 5

# 检查业务API是否启动成功
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✓ 业务API启动成功"
else
    echo "✗ 业务API启动失败"
    kill $BUSINESS_API_PID 2>/dev/null || true
    exit 1
fi

# 启动LiteLLM代理
echo ""
echo "=== 启动LiteLLM代理 ==="
echo "端口: 8080"
echo "主机: 0.0.0.0"

# 在后台启动LiteLLM代理（使用标准方式）
cd "$PROJECT_ROOT"
litellm --config config.yaml --host 0.0.0.0 --port 8080 &
LITELLM_PROXY_PID=$!

echo "LiteLLM代理进程ID: $LITELLM_PROXY_PID"

# 等待LiteLLM代理启动
echo "等待LiteLLM代理启动..."
sleep 10

# 检查LiteLLM代理是否启动成功
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ LiteLLM代理启动成功"
else
    echo "✗ LiteLLM代理启动失败"
    echo "检查日志文件: src/logs/litellm_proxy_*.log"
fi

echo ""
echo "=== 服务启动完成 ==="
echo "业务API: http://localhost:8002"
echo "LiteLLM代理: http://localhost:8080"
echo ""
echo "运行测试:"
echo "python src/liteLLMAdapter/example.py"
echo ""
echo "停止服务:"
echo "kill $BUSINESS_API_PID $LITELLM_PROXY_PID"
echo ""
echo "进程ID已保存，可以使用以下命令停止服务:"
echo "pkill -f 'business_api_example.py'"
echo "pkill -f 'start_proxy.py'"

# 保存进程ID到文件
echo "$BUSINESS_API_PID" > /tmp/business_api.pid
echo "$LITELLM_PROXY_PID" > /tmp/litellm_proxy.pid

echo ""
echo "进程ID已保存到:"
echo "/tmp/business_api.pid"
echo "/tmp/litellm_proxy.pid" 