#!/bin/bash

# 增强版启动脚本 - 包含日志重定向
# 非入侵式日志收集

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 全局变量
LOG_DATE_DIR=""
BUSINESS_API_PID=""
LITELLM_PROXY_PID=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 创建基于日期的日志目录结构
create_log_dirs() {
    local year=$(date +%Y)
    local month=$(date +%m)
    local day=$(date +%d)
    local log_date_dir="logs/$year/$month/$day"
    mkdir -p "$log_date_dir"
    echo "$log_date_dir"
}

# 设置环境变量
setup_environment() {
    print_info "设置环境变量..."
    
    # 创建日志目录
    mkdir -p logs
    LOG_DATE_DIR=$(create_log_dirs)
    print_info "📁 日志目录: $LOG_DATE_DIR"
    
    # 设置日志环境变量
    export LITELLM_LOG=DEBUG
    export LITELLM_SET_VERBOSE=true
    export PYTHON_LOG_LEVEL=DEBUG
    export PYTHONUNBUFFERED=1
    export LITELLM_LOG_LEVEL=INFO
    export PYTHONPATH="${PYTHONPATH}:."
    
    print_success "环境变量设置完成"
}

# 配置Python日志
setup_python_logging() {
    print_info "配置Python日志..."
    
    if [ -f "logging.yaml" ]; then
        print_info "使用logging.yaml配置Python日志"
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
" || print_warning "日志配置出错，继续启动..."
    else
        print_warning "logging.yaml文件不存在，使用默认配置"
    fi
}

# 检查服务是否运行
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout="${3:-5}"
    
    print_info "检查 $service_name 状态..."
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        print_success "$service_name 运行正常"
        return 0
    else
        print_error "$service_name 未运行或响应异常"
        return 1
    fi
}

# 启动业务API
start_business_api() {
    print_info "=== 启动业务API（带日志） ==="
    
    cd "$PROJECT_ROOT"
    python productAdapter/api/business_api_example.py --port 8002 --host 0.0.0.0 \
        2>&1 | tee -a "$LOG_DATE_DIR/business_api.log" &
    BUSINESS_API_PID=$!
    
    print_info "业务API进程ID: $BUSINESS_API_PID"
    
    # 等待业务API启动
    print_info "等待业务API启动..."
    sleep 5
    
    # 检查业务API
    if check_service "业务API" "http://localhost:8002/health"; then
        print_success "业务API启动成功"
    else
        print_error "业务API启动失败"
        kill $BUSINESS_API_PID 2>/dev/null || true
        exit 1
    fi
}

# 启动LiteLLM代理
start_litellm_proxy() {
    print_info "=== 启动LiteLLM代理（带详细日志） ==="
    
    litellm --config config.yaml --host 0.0.0.0 --port 8080 --detailed_debug \
        2>&1 | tee -a "$LOG_DATE_DIR/litellm.log" &
    LITELLM_PROXY_PID=$!
    
    print_info "LiteLLM代理进程ID: $LITELLM_PROXY_PID"
    
    # 等待LiteLLM代理启动
    print_info "等待LiteLLM代理启动..."
    sleep 10
    
    # 检查LiteLLM代理
    if check_service "LiteLLM代理" "http://localhost:8080/health"; then
        print_success "LiteLLM代理启动成功"
    else
        print_warning "LiteLLM代理启动失败"
        print_info "检查日志文件: $LOG_DATE_DIR/litellm.log"
    fi
}

# 保存进程ID
save_process_ids() {
    echo "$BUSINESS_API_PID" > /tmp/business_api.pid
    echo "$LITELLM_PROXY_PID" > /tmp/litellm_proxy.pid
    print_info "进程ID已保存到 /tmp/business_api.pid 和 /tmp/litellm_proxy.pid"
}

# 检查Dify配置
check_dify_config() {
    if [ -f "productAdapter/config/.env" ]; then
        print_success "找到Dify配置文件"
        # 加载环境变量
        export $(grep -v '^#' productAdapter/config/.env | xargs)
        
        # 检查Dify配置
        if [ -n "$DIFY_API_KEY" ] && [ -n "$DIFY_WORKFLOW_ID" ]; then
            print_success "Dify配置检查通过"
            return 0
        else
            print_warning "Dify配置不完整，跳过集成测试"
            print_info "请在 productAdapter/config/.env 中设置 DIFY_API_KEY 和 DIFY_WORKFLOW_ID"
            return 1
        fi
    else
        print_warning "未找到Dify配置文件，跳过集成测试"
        print_info "请运行: cp productAdapter/config/env.example productAdapter/config/.env"
        return 1
    fi
}

# 运行Dify集成测试
run_dify_test() {
    print_info "=== 运行Dify集成测试 ==="
    
    if ! check_dify_config; then
        return 1
    fi
    
    # 等待服务完全启动
    print_info "等待服务完全启动..."
    sleep 3
    
    # 运行简单的Dify集成测试
    print_info "测试Dify工作流集成..."
    test_response=$(curl -s -X POST http://localhost:8002/api/process \
        -H 'Content-Type: application/json' \
        -d '{
            "query": "测试Dify集成",
            "model_info": {"name": "dify-test"},
            "response_type": "text"
        }' 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$test_response" | grep -q "content"; then
        print_success "Dify集成测试成功"
        local content=$(echo "$test_response" | jq -r '.content' | head -c 100 2>/dev/null || echo "$test_response" | head -c 100)
        print_info "响应内容: ${content}..."
    else
        print_warning "Dify集成测试失败，请检查配置和网络连接"
        print_info "响应: $test_response"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    print_info "=== 服务启动完成 ==="
    echo "业务API: http://localhost:8002"
    echo "LiteLLM代理: http://localhost:8080"
    echo ""
    print_info "日志文件位置:"
    echo "- 业务API: $LOG_DATE_DIR/business_api.log"
    echo "- LiteLLM代理: $LOG_DATE_DIR/litellm.log (包含自定义处理器日志)"
    echo ""
    print_info "停止服务:"
    echo "pkill -f 'business_api_example.py'"
    echo "pkill -f litellm"
}

# 显示使用说明
show_usage() {
    echo ""
    print_info "=== 启动完成 ==="
    print_info "使用 --test-dify 参数可以运行Dify集成测试"
    print_info "示例: ./start_with_logging.sh --test-dify"
}

# 主函数
main() {
    echo "=== 带日志收集的LiteLLM服务启动 ==="
    
    # 设置环境
    setup_environment
    
    # 配置Python日志
    setup_python_logging
    
    # 启动业务API
    start_business_api
    
    # 启动LiteLLM代理
    start_litellm_proxy
    
    # 保存进程ID
    save_process_ids
    
    # 显示服务信息
    show_service_info
    
    # 检查是否需要进行Dify集成测试
    if [ "$1" = "--test-dify" ] || [ "$2" = "--test-dify" ]; then
        run_dify_test
    fi
    
    # 显示使用说明
    show_usage
}

# 脚本入口
main "$@"