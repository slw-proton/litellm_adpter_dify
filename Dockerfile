# 使用基础镜像
ARG BASE_IMAGE=litellm-adapter-base:latest
FROM ${BASE_IMAGE}

# 复制项目源代码
COPY . /app

# 创建配置目录
RUN mkdir -p /app/productAdapter/config

# 修复脚本换行符问题（Windows CRLF -> Unix LF）
RUN find /app -name "*.sh" -exec sed -i 's/\r$//' {} \;

# 安装时区数据并设置时区
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 默认环境变量（可在运行时覆盖）
ENV LOG_LEVEL=DEBUG \
    LITELLM_LOG_LEVEL=DEBUG \
    LITELLM_LOG=DEBUG \
    LITELLM_SET_VERBOSE=true \
    LITE_LLM_DISABLE_CHECKS=True \
    BUSINESS_API_HOST=0.0.0.0 \
    BUSINESS_API_PORT=8002 \
    TZ=Asia/Shanghai

EXPOSE 8002 8080

# 入口脚本
RUN chmod +x /app/docker/entrypoint.sh || true
ENTRYPOINT ["/bin/sh", "/app/docker/entrypoint.sh"]


