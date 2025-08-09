#!/bin/bash

# LiteLLM适配器服务停止脚本（增强版）

set -e

echo "=== 停止LiteLLM适配器服务 ==="

kill_by_pid_file() {
  local pid_file="$1"
  local name="$2"
  if [ -f "$pid_file" ]; then
    local pid
    pid=$(cat "$pid_file" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "停止$name (PID=$pid)..."
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
  fi
}

kill_by_pattern() {
  local pattern="$1"
  local name="$2"
  echo "按模式停止: $name ($pattern) ..."
  pkill -f "$pattern" 2>/dev/null || true
  sleep 1
}

kill_by_port() {
  local port="$1"
  local name="$2"
  echo "释放端口: $port ($name) ..."
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -i:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo "检测到占用端口$port的进程: $pids，尝试结束..."
      kill $pids 2>/dev/null || true
      sleep 1
      kill -9 $pids 2>/dev/null || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k -n tcp "$port" 2>/dev/null || true
  else
    echo "未找到 lsof/fuser，跳过端口释放"
  fi
}

# 停止业务API（uvicorn）
echo "停止业务API..."
kill_by_pid_file "/tmp/business_api.pid" "业务API"
kill_by_pattern "uvicorn productAdapter.api.business_api_example" "业务API(uvicorn)"
kill_by_pattern "business_api_example:app" "业务API(uvicorn)"
kill_by_pattern "business_api_example.py" "业务API脚本"
kill_by_port 8002 "业务API端口"

# 停止LiteLLM代理
echo "停止LiteLLM代理..."
kill_by_pid_file "/tmp/litellm_proxy.pid" "LiteLLM代理"
kill_by_pattern "litellm --config" "LiteLLM代理"
kill_by_pattern "litellm" "LiteLLM进程"
kill_by_port 8080 "LiteLLM端口"

echo "✓ 所有服务已停止"