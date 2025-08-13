#!/bin/sh
set -e

# 日志目录（容器内）
LOG_DIR=${LOG_DIR:-/var/log/trae-litellm}
mkdir -p "$LOG_DIR"

echo "[entrypoint] LOG_DIR=$LOG_DIR"
echo "[entrypoint] 启动 Business API 与 LiteLLM 代理"

# 启动 Business API
(
  uvicorn productAdapter.api.business_api_example:app \
    --host "${BUSINESS_API_HOST:-0.0.0.0}" \
    --port "${BUSINESS_API_PORT:-8002}" \
    --http h11 2>&1 | tee -a "$LOG_DIR/business_api.log"
) &
BUSINESS_API_PID=$!
echo "[entrypoint] BUSINESS_API_PID=$BUSINESS_API_PID"

# 等待业务API就绪
sleep 3

# 启动 LiteLLM 代理
(
  litellm --config /app/config.yaml --host 0.0.0.0 --port 8080 --detailed_debug \
    2>&1 | tee -a "$LOG_DIR/litellm.log"
) &
LITELLM_PID=$!
echo "[entrypoint] LITELLM_PID=$LITELLM_PID"

echo "[entrypoint] Services started. Business API :8002, LiteLLM :8080"

# 健康等待（可选）
sleep 2

# 监控子进程：任一退出则容器退出（触发重启策略）
while true; do
  if ! kill -0 "$BUSINESS_API_PID" 2>/dev/null; then
    echo "[entrypoint] Business API exited"
    exit 1
  fi
  if ! kill -0 "$LITELLM_PID" 2>/dev/null; then
    echo "[entrypoint] LiteLLM exited"
    exit 1
  fi
  sleep 2
done


