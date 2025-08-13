ARG BASE_IMAGE=dify-openai-base:latest
FROM ${BASE_IMAGE}

# 复制项目源代码
COPY . /app
COPY productAdapter/config/.env.product /app/productAdapter/config/.env

# 默认环境变量（可在运行时覆盖）
ENV LOG_LEVEL=DEBUG \
    LITELLM_LOG_LEVEL=DEBUG \
    LITELLM_LOG=DEBUG \
    LITELLM_SET_VERBOSE=true \
    LITE_LLM_DISABLE_CHECKS=True \
    BUSINESS_API_HOST=0.0.0.0 \
    BUSINESS_API_PORT=8002 \
    TZ=Asia/Shanghai

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8002 8080

# 入口脚本
RUN chmod +x /app/docker/entrypoint.sh || true
ENTRYPOINT ["/bin/sh", "/app/docker/entrypoint.sh"]


