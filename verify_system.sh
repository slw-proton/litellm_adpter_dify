#!/bin/bash

# LiteLLM自定义适配器系统验证脚本
# 用于快速验证整个系统是否正常工作

set -e

echo "=== LiteLLM自定义适配器系统验证 ==="
echo "开始时间: $(date)"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local url=$2
    local expected_pattern=$3
    
    echo -n "检查 $service_name ... "
    
    if response=$(curl -s --max-time 10 "$url" 2>/dev/null); then
        if [[ $response =~ $expected_pattern ]]; then
            echo -e "${GREEN}✓ 正常${NC}"
            return 0
        else
            echo -e "${RED}✗ 响应异常${NC}"
            echo "  响应内容: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ 连接失败${NC}"
        return 1
    fi
}

# 测试API调用
test_api_call() {
    local name=$1
    local url=$2
    local data=$3
    local expected_pattern=$4
    
    echo -n "测试 $name ... "
    
    if response=$(curl -s --max-time 15 -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" 2>/dev/null); then
        if [[ $response =~ $expected_pattern ]]; then
            echo -e "${GREEN}✓ 成功${NC}"
            return 0
        else
            echo -e "${RED}✗ 响应异常${NC}"
            echo "  响应内容: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ 调用失败${NC}"
        return 1
    fi
}

# 1. 检查环境配置
echo -e "${BLUE}1. 检查环境配置${NC}"
echo "项目根目录: $(pwd)"

if [ ! -f "productAdapter/config/.env" ]; then
    echo -e "${RED}✗ 环境配置文件 productAdapter/config/.env 不存在${NC}"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo -e "${RED}✗ LiteLLM配置文件 config.yaml 不存在${NC}"
    exit 1
fi

if [ ! -f "custom_handler.py" ]; then
echo -e "${RED}✗ 自定义处理器 custom_handler.py 不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 配置文件检查通过${NC}"
echo ""

# 2. 检查服务状态
echo -e "${BLUE}2. 检查服务状态${NC}"

# 检查业务API
check_service "业务API (8002)" "http://localhost:8002/health" '"status":"ok"'
business_api_status=$?

# 检查LiteLLM代理
check_service "LiteLLM代理 (8080)" "http://localhost:8080/health" "healthy_endpoints"
litellm_status=$?

echo ""

# 3. 测试API调用
echo -e "${BLUE}3. 测试API调用${NC}"

if [ $business_api_status -eq 0 ]; then
    # 测试业务API直接调用
    business_data='{"query":"测试消息","model_info":{"name":"test-model"},"response_type":"text"}'
    test_api_call "业务API直接调用" "http://localhost:8002/api/process" "$business_data" '"content"'
fi

if [ $litellm_status -eq 0 ]; then
    # 测试LiteLLM代理调用
    litellm_data='{"model":"my-custom-model","messages":[{"role":"user","content":"你好，请介绍一下自己"}],"max_tokens":100}'
    test_api_call "LiteLLM代理调用" "http://localhost:8080/chat/completions" "$litellm_data" '"choices"'
fi

echo ""

# 4. 完整调用链测试
echo -e "${BLUE}4. 完整调用链测试${NC}"

if [ $business_api_status -eq 0 ] && [ $litellm_status -eq 0 ]; then
    echo "测试完整调用链: OpenAI客户端 → LiteLLM代理 → 自定义处理器 → 业务API"
    
    # 详细测试
    test_data='{"model":"my-custom-model","messages":[{"role":"user","content":"测试完整调用链路"}],"max_tokens":150}'
    
    echo -n "执行完整调用链测试 ... "
    if response=$(curl -s --max-time 20 -X POST "http://localhost:8080/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$test_data" 2>/dev/null); then
        
        # 检查响应格式
        if echo "$response" | grep -q '"choices"' && echo "$response" | grep -q '"message"' && echo "$response" | grep -q '"content"'; then
            echo -e "${GREEN}✓ 成功${NC}"
            echo "  响应摘要: $(echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null || echo "解析失败")"
        else
            echo -e "${RED}✗ 响应格式异常${NC}"
            echo "  完整响应: $response"
        fi
    else
        echo -e "${RED}✗ 调用失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 跳过完整调用链测试（服务未就绪）${NC}"
fi

echo ""

# 5. 系统状态总结
echo -e "${BLUE}5. 系统状态总结${NC}"

if [ $business_api_status -eq 0 ] && [ $litellm_status -eq 0 ]; then
    echo -e "${GREEN}🎉 系统运行正常！${NC}"
    echo ""
    echo "可用的API端点："
    echo "  • 业务API健康检查: http://localhost:8002/health"
    echo "  • 业务API处理接口: http://localhost:8002/api/process"
    echo "  • LiteLLM代理健康检查: http://localhost:8080/health"
    echo "  • LiteLLM聊天完成接口: http://localhost:8080/chat/completions"
    echo ""
    echo "示例调用："
    echo "  curl -X POST http://localhost:8080/chat/completions \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"model\":\"my-custom-model\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
else
    echo -e "${RED}❌ 系统存在问题${NC}"
    echo ""
    if [ $business_api_status -ne 0 ]; then
        echo "• 业务API (8002端口) 未正常运行"
        echo "  启动命令: python src/liteLLMAdapter/business_api_example.py --env-file src/.env --port 8002 --host 0.0.0.0"
    fi
    if [ $litellm_status -ne 0 ]; then
        echo "• LiteLLM代理 (8080端口) 未正常运行"
        echo "  启动命令: cd src && litellm --config config.yaml --host 0.0.0.0 --port 8080"
    fi
fi

echo ""
echo "验证完成时间: $(date)"
echo "详细启动指南请参考: STARTUP_GUIDE.md" 