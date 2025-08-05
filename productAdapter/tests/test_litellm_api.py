#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试LiteLLM API
直接使用LiteLLM的API来测试，看看问题出在哪里
"""

import os
import sys
import json
import requests
import logging
from typing import Dict, Any

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, project_root)

# 尝试导入环境变量加载器
try:
    from src.env_loader import get_env, get_env_int, get_env_bool, load_env_file
    # 尝试加载.env文件
    env_file = get_env("ENV_FILE", os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    if os.path.exists(env_file):
        load_env_file(env_file)
        print(f"Loaded environment variables from {env_file}")
except ImportError:
    print("env_loader module not found, using default environment variable loading")
    # 如果找不到环境变量加载器，使用默认的环境变量获取方法
    def get_env(key, default=None):
        return os.environ.get(key, default)
    
    def get_env_int(key, default=None):
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_env_bool(key, default=None):
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 't', 'y')

# 尝试导入日志配置
try:
    from src.logging_config import setup_logging
    logger = setup_logging("test_litellm_api")
except ImportError:
    # 导入日志模块
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from logger import get_logger
    # 获取日志记录器
    logger = get_logger("test_litellm_api")

def test_litellm_api():
    """
    测试LiteLLM API
    """
    logger.info("=== 开始测试LiteLLM API ===")
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    
    # 构建LiteLLM代理的URL
    api_url = f"http://{host}:{port}/v1/chat/completions"
    logger.debug(f"API URL: {api_url}")
    logger.info(f"使用LiteLLM代理URL: {api_url}")
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    logger.debug(f"请求头: {headers}")
    
    # 从环境变量获取默认模型
    default_model = get_env("DEFAULT_MODEL", "default-model")
    model_name = f"custom/{default_model}"
    logger.info(f"使用模型: {model_name}")
    
    # 构建请求
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是一个有用的AI助手。"},
            {"role": "user", "content": "请用一句话介绍人工智能。"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    # 发送请求
    logger.info("发送请求...")
    logger.info(f"请求负载: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        logger.debug("开始发送HTTP请求")
        response = requests.post(api_url, headers=headers, json=payload)
        logger.debug(f"HTTP请求完成，状态码: {response.status_code}")
        
        # 打印响应
        logger.info(f"响应状态码: {response.status_code}")
        
        # 获取响应内容
        response_json = response.json()
        logger.info("响应内容:")
        logger.info(json.dumps(response_json, ensure_ascii=False, indent=2))
        
        # 检查是否有错误
        if response.status_code >= 400:
            logger.error(f"请求失败，状态码: {response.status_code}")
            if "error" in response_json:
                error_msg = response_json.get("error", {}).get("message", "未知错误")
                logger.error(f"错误信息: {error_msg}")
        
        # 打印到控制台
        print(f"\n响应状态码: {response.status_code}")
        print("响应内容:")
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
    
    except Exception as e:
        error_msg = f"请求异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"Error: {error_msg}")

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test LiteLLM API")
    parser.add_argument("--env-file", type=str, 
                        help="Path to .env file for loading environment variables")
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果指定了环境变量文件，加载它
    if args.env_file and os.path.exists(args.env_file):
        try:
            load_env_file(args.env_file)
            logger.info(f"Loaded environment variables from {args.env_file}")
        except Exception as e:
            logger.error(f"Error loading environment variables from {args.env_file}: {str(e)}")
    
    # 记录环境变量信息
    logger.info(f"Environment variables: LITELLM_PROXY_HOST={get_env('LITELLM_PROXY_HOST', 'Not set')}, "
               f"LITELLM_PROXY_PORT={get_env('LITELLM_PROXY_PORT', 'Not set')}, "
               f"DEFAULT_MODEL={get_env('DEFAULT_MODEL', 'Not set')}, "
               f"LOG_LEVEL={get_env('LOG_LEVEL', 'Not set')}")
    
    # 执行测试
    test_litellm_api()

if __name__ == "__main__":
    main()