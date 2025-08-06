#!/bin/bash

# 非入侵式日志配置脚本
# 设置LiteLLM的内置日志选项

echo "=== 配置LiteLLM日志环境变量 ==="

# LiteLLM 内置日志配置
export LITELLM_LOG=DEBUG                          # 设置日志级别
export LITELLM_LOG_LEVEL=DEBUG                    # 详细日志级别
export LITELLM_SET_VERBOSE=true                   # 启用详细日志
export LITELLM_JSON_LOGS=true                     # JSON格式日志

# Python 日志配置
export PYTHONPATH="${PYTHONPATH}:."              # 添加项目路径
export PYTHON_LOG_LEVEL=DEBUG                    # Python日志级别

# 创建日志目录
mkdir -p logs

echo "✅ 日志环境变量配置完成"
echo "现在启动服务将包含详细日志"