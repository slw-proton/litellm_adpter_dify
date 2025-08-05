#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自定义LiteLLM处理器
根据LiteLLM官方文档创建
"""

import os
import sys
import json
import time
import uuid
import logging
import requests
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入LiteLLM相关模块
import litellm
from litellm import CustomLLM, completion, get_llm_provider

# 设置日志
logger = logging.getLogger(__name__)

class MyCustomLLM(CustomLLM):
    """
    自定义LLM处理器
    继承自LiteLLM的CustomLLM基类
    """
    
    def __init__(self):
        super().__init__()
        self.api_base = "http://localhost:8002/api/process"
        logger.info("MyCustomLLM初始化完成")
    
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        """
        同步完成方法
        根据官方文档实现
        """
        try:
            # 从kwargs中提取参数
            model = kwargs.get("model", "business-api")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 100)
            temperature = kwargs.get("temperature", 0.7)
            
            logger.info(f"处理completion请求: model={model}, messages={messages}")
            
            # 提取用户查询
            user_query = ""
            if messages:
                for msg in messages:
                    if msg.get("role") == "user":
                        user_query = msg.get("content", "")
                        break
            
            # 构建业务API请求
            business_request = {
                "query": user_query,
                "model_info": {
                    "name": model
                },
                "response_type": "text",
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            logger.info(f"发送到业务API的请求: {business_request}")
            
            # 发送请求到业务API
            response = requests.post(
                self.api_base,
                json=business_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                business_response = response.json()
                logger.info(f"业务API响应: {business_response}")
                
                # 使用LiteLLM的completion函数创建标准响应
                mock_response = business_response.get("response", "Hello from custom LLM!")
                
                return litellm.completion(
                    model="gpt-3.5-turbo",  # 使用一个已知的模型格式
                    messages=[{"role": "user", "content": user_query}],
                    mock_response=mock_response,
                )
            else:
                logger.error(f"业务API错误: {response.status_code} - {response.text}")
                # 返回错误响应
                return litellm.completion(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_query}],
                    mock_response="抱歉，服务暂时不可用。",
                )
                
        except Exception as e:
            logger.error(f"处理completion请求时出错: {str(e)}")
            # 返回错误响应
            return litellm.completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": ""}],
                mock_response="抱歉，处理请求时出现错误。",
            )

    async def acompletion(self, *args, **kwargs) -> litellm.ModelResponse:
        """
        异步完成方法
        根据官方文档实现
        """
        # 对于简单实现，直接调用同步方法
        return self.completion(*args, **kwargs)

# 创建实例
my_custom_llm = MyCustomLLM() 