#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LiteLLM适配器核心模块
用于将业务API的请求和响应转换为OpenAI格式
"""

import os
import sys
import time
import uuid
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Generator

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# 导入日志配置
try:
    from ..utils.logging_config import setup_logging
    # 设置日志记录器
    logger = setup_logging("litellm_adapter", logging.INFO)
except ImportError:
    # 如果找不到logging_config模块，则使用内置的logger模块
    from liteLLMAdapter.logger import get_logger
    logger = get_logger("adapter")

class LiteLLMAdapter:
    """LiteLLM适配器类"""
    
    def __init__(self, api_base: str, api_key: Optional[str]):
        self.api_base = api_base
        self.api_key = api_key
    
    def _get_headers(self) -> Dict[str, str]: 
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def handle_chat_completion(self, openai_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        将LiteLLM的OpenAI格式请求转换为你的业务API格式，并发送请求。
        """
        # 1. 从LiteLLM的OpenAI格式请求中提取所需数据
        model = openai_request.get("model", "default-model")
        
        # 处理不同的参数格式
        # LiteLLM可能传递params字段，也可能直接传递参数
        params = openai_request.get("params", {})
        
        # 提取用户消息
        user_query = ""
        
        if params:
            # 如果存在params字段，从中提取参数
            messages = params.get("messages", [])
            prompt = params.get("prompt", [])
            
            # 如果messages为空但有prompt，将prompt转换为用户查询
            if not messages and prompt:
                if isinstance(prompt, list):
                    # 如果是数组，取第一个元素作为用户消息
                    user_query = prompt[0] if prompt else ""
                else:
                    user_query = str(prompt)
            elif messages:
                # 从messages中提取用户消息
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_query = msg.get("content", "")
                        break
        else:
            # 直接传递的参数
            messages = openai_request.get("messages", [])
            if messages:
                # 找到最后一条用户消息
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_query = msg.get("content", "")
                        break
            
            # 如果没有找到用户消息，尝试从prompt字段提取
            if not user_query:
                prompt = openai_request.get("prompt", [])
                if isinstance(prompt, list) and prompt:
                    user_query = str(prompt[0])
                elif isinstance(prompt, str):
                    user_query = prompt
        
        # 提取其他参数
        kwargs = {k: v for k, v in openai_request.items() if k not in ["model", "messages", "stream", "params"]}
        
        # 如果存在params字段，合并其中的参数
        if params:
            for k, v in params.items():
                if k not in ["messages", "prompt"]:
                    kwargs[k] = v

        # 2. 构建符合你的业务API BusinessRequest 模型的请求体
        business_api_request = {
            "query": user_query,
            "response_type": "text",  # 根据你的业务API需要设置，这里假设为text
            "stream": openai_request.get("stream", False),
            "model_info": {
                "name": model.split("/")[-1] if "/" in model else model  # 提取模型名称，去掉前缀
            }
        }
        
        # 添加其他参数
        if "temperature" in kwargs:
            business_api_request["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            business_api_request["max_tokens"] = kwargs["max_tokens"]
        
        logger.debug(f"转换后的业务API请求体: {json.dumps(business_api_request, ensure_ascii=False, indent=2)}")

        # 3. 向你的业务API发送POST请求
        try:
            response = requests.post(
                self.api_base, # 完整的API端点
                json=business_api_request,
                headers=self._get_headers(),
                timeout=60 # 设置超时时间
            )
            response.raise_for_status()  # 如果状态码不是2xx，则抛出HTTPError

            # 4. 将业务API响应转换为LiteLLM期望的OpenAI格式
            business_response = response.json()
            content = business_response.get("content")

            # 构造OpenAI兼容的响应格式
            openai_response = {
                "id": business_response.get("response_id"),
                "object": "chat.completion",
                "created": business_response.get("timestamp"),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            return openai_response

        except requests.exceptions.RequestException as e:
            # 处理网络或HTTP错误
            logger.error(f"请求业务API时发生错误: {e}")
            raise Exception(f"请求业务API时发生错误: {e}")