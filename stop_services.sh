#!/bin/bash

# LiteLLM适配器服务停止脚本

echo "=== 停止LiteLLM适配器服务 ==="

# 停止业务API
echo "停止业务API..."
pkill -f "business_api_example.py" || echo "业务API进程未运行"

# 停止LiteLLM代理
echo "停止LiteLLM代理..."
pkill -f "litellm --config" || echo "LiteLLM代理进程未运行"

# 停止litellm进程
echo "停止litellm进程..."
pkill -f "litellm" || echo "litellm进程未运行"

# 清理PID文件
rm -f /tmp/business_api.pid
rm -f /tmp/litellm_proxy.pid

echo "✓ 所有服务已停止" 