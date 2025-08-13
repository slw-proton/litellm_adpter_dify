#!/usr/bin/env bash
set -euo pipefail

# 一键：打包 → 构建 → 启动 → 健康检查（Ubuntu 环境）
# 参考 docs/DEPLOYMENT_DOCKER.md

# 颜色
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 默认对外端口（与 docker-compose.yml 保持一致）
EXTERNAL_BUSINESS_PORT=${EXTERNAL_BUSINESS_PORT:-18002}
EXTERNAL_LITELLM_PORT=${EXTERNAL_LITELLM_PORT:-18080}

# 参数
REBUILD_BASE=false
NO_CACHE=false
FOLLOW_LOGS=false

usage() {
  cat <<USAGE
用法: $(basename "$0") [选项]

选项:
  --rebuild-base     重新构建基础镜像 (Dockerfile.base)
  --no-cache         构建不使用缓存
  --logs             启动后跟随日志输出 (等价于 docker compose logs -f)
  -h, --help         查看帮助

环境变量:
  EXTERNAL_BUSINESS_PORT  对外业务端口 (默认: ${EXTERNAL_BUSINESS_PORT})
  EXTERNAL_LITELLM_PORT   对外 LiteLLM 端口 (默认: ${EXTERNAL_LITELLM_PORT})
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild-base) REBUILD_BASE=true; shift ;;
    --no-cache)     NO_CACHE=true; shift ;;
    --logs)         FOLLOW_LOGS=true; shift ;;
    -h|--help)      usage; exit 0 ;;
    *) warn "未知参数: $1"; usage; exit 1 ;;
  esac
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    error "未找到命令: $1"
    exit 1
  fi
}

check_dependencies() {
  info "检查依赖..."
  require_cmd docker
  if ! docker compose version >/dev/null 2>&1; then
    error "未检测到 docker compose，请安装 Docker Compose 插件或使用较新 Docker 版本"
    exit 1
  fi
  success "依赖检查通过"
}

ensure_logs_dir() {
  LOGS_DIR_HOST="${PROJECT_ROOT}/logs/docker"
  mkdir -p "$LOGS_DIR_HOST"
  info "日志目录: $LOGS_DIR_HOST"
}

build_base_image() {
  if [[ "$REBUILD_BASE" == "true" ]]; then
    info "构建基础镜像 dify-openai-base:<fingerprint> (Dockerfile.base)"
    local FINGERPRINT
    if command -v sha256sum >/dev/null 2>&1; then
      FINGERPRINT=$(sha256sum requirements.txt | cut -c1-12)
    else
      FINGERPRINT=$(date +%s)
    fi
    local BASE_TAG="dify-openai-base:${FINGERPRINT}"
    if [[ "$NO_CACHE" == "true" ]]; then
      docker build --no-cache -f Dockerfile.base --build-arg PYTHON_IMAGE=python:3.11-slim -t "${BASE_TAG}" .
    else
      docker build -f Dockerfile.base --build-arg PYTHON_IMAGE=python:3.11-slim -t "${BASE_TAG}" .
    fi
    success "基础镜像构建完成: ${BASE_TAG}"
    # 写入应用构建使用的 --build-arg
    export BASE_IMAGE_ARG="--build-arg BASE_IMAGE=${BASE_TAG}"
  else
    warn "跳过基础镜像构建（如需构建，添加 --rebuild-base）"
    # 若未重建，默认使用 latest
    export BASE_IMAGE_ARG="--build-arg BASE_IMAGE=dify-openai-base:latest"
  fi
}

build_app_image() {
  info "构建业务镜像 (docker compose build)"
  if [[ "$NO_CACHE" == "true" ]]; then
    DOCKER_BUILDKIT=1 docker compose build --no-cache ${BASE_IMAGE_ARG:-}
  else
    DOCKER_BUILDKIT=1 docker compose build ${BASE_IMAGE_ARG:-}
  fi
  success "业务镜像构建完成"
}

start_services() {
  info "启动容器 (docker compose up -d)"
  docker compose up -d
  success "容器启动指令已下发"
}

wait_for_health() {
  HEALTH_URL="http://localhost:${EXTERNAL_BUSINESS_PORT}/health"
  info "等待 Business API 健康检查: $HEALTH_URL"
  local RETRY=30
  local SLEEP=2
  for ((i=1; i<=RETRY; i++)); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      success "Business API 健康检查通过"
      return 0
    fi
    sleep "$SLEEP"
  done
  error "Business API 健康检查失败"
  docker compose logs --tail=200 || true
  return 1
}

verify_litellm_models() {
  local MODELS_URL="http://localhost:${EXTERNAL_LITELLM_PORT}/models"
  info "验证 LiteLLM /models ($MODELS_URL)"
  if curl -fsS "$MODELS_URL" >/dev/null 2>&1; then
    success "LiteLLM /models 可访问"
  else
    warn "LiteLLM /models 暂不可访问，请检查日志"
  fi
}

print_status() {
  info "当前容器状态:"
  docker compose ps || true
}

tail_or_hint_logs() {
  if [[ "$FOLLOW_LOGS" == "true" ]]; then
    info "跟随日志输出，按 Ctrl+C 退出"
    docker compose logs -f --tail=200
  else
    info "查看日志命令: docker compose logs -f --tail=200"
    info "业务API:  http://localhost:${EXTERNAL_BUSINESS_PORT}"
    info "LiteLLM:  http://localhost:${EXTERNAL_LITELLM_PORT}"
  fi
}

stop_services() {
  warn "停止已运行的容器（若存在）..."
  # 优先通过 compose 停止与清理孤儿容器
  docker compose down --remove-orphans || true
  # 兜底清理命名容器
  docker rm -f trae-litellm 2>/dev/null || true
}

main() {
  check_dependencies
  stop_services
  ensure_logs_dir
  build_base_image
  build_app_image
  start_services
  wait_for_health || exit 1
  verify_litellm_models
  print_status
  tail_or_hint_logs
  success "完成"
}

main "$@"


