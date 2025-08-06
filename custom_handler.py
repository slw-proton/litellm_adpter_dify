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
        print("[custom_handler] MyCustomLLM初始化完成")
    
    def _extract_response_format(self, kwargs: dict) -> tuple[Optional[Dict[str, Any]], str]:
        """
        从kwargs中提取response_format并确定响应类型
        
        Args:
            kwargs: 包含optional_params和response_format的参数字典
            
        Returns:
            tuple: (response_format, response_type)
                - response_format: response_format字典或None
                - response_type: 响应类型字符串 ("text" 或 "json")
        """
        # 安全地检查optional_params中的response_format
        optional_params = kwargs.get('optional_params', {})
        print(f"[custom_handler] optional_params keys: {list(optional_params.keys()) if optional_params else 'None'}")
        
        # 优先从optional_params中获取response_format，如果没有再从kwargs中获取
        response_format = None
        if optional_params and 'response_format' in optional_params:
            response_format = optional_params['response_format']
            print(f"[custom_handler] ✅ 从optional_params检测到response_format: {response_format.get('type', 'unknown') if response_format else 'None'}")
            if response_format:
                print(f"[custom_handler] optional_params.response_format详情: {json.dumps(response_format, ensure_ascii=False, indent=2)}")
        elif kwargs.get("response_format"):
            response_format = kwargs.get("response_format")
            print(f"[custom_handler] ✅ 从kwargs检测到response_format: {response_format.get('type', 'unknown')}")
            print(f"[custom_handler] response_format详情: {json.dumps(response_format, ensure_ascii=False, indent=2)}")
        else:
            print(f"[custom_handler] ⚠️ 未检测到response_format参数（kwargs.response_format={kwargs.get('response_format')}, optional_params.response_format={optional_params.get('response_format') if optional_params else 'N/A'}）")
        
        # 确定响应类型
        response_type = "text"
        if response_format:
            if response_format.get("type") == "json_schema":
                response_type = "json"
                print(f"[custom_handler] 设置响应类型为JSON（structured output）")
            elif response_format.get("type") == "json_object":
                response_type = "json"
                print(f"[custom_handler] 设置响应类型为JSON object")
        
        return response_format, response_type
    
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
            
            print(f"[custom_handler] 处理completion请求: model={model}, messages={len(messages)}条消息")
            print(f"[custom_handler] 完整kwargs keys: {list(kwargs.keys())}")
            
            # 提取用户查询（完整的消息内容）
            user_query = ""
            system_message = ""
            if messages:
                for msg in messages:
                    if msg.get("role") == "user":
                        user_query = msg.get("content", "")
                    elif msg.get("role") == "system":
                        system_message = msg.get("content", "")
                
                # 如果有system消息，将其包含在查询中
                if system_message and user_query:
                    user_query = f"System: {system_message}\n\nUser: {user_query}"
                elif system_message:
                    user_query = system_message
            
            # 提取response_format并确定响应类型
            response_format, response_type = self._extract_response_format(kwargs)
            
            # 构建业务API请求
            business_request = {
                "query": user_query,
                "model_info": {
                    "name": model
                },
                "response_type": response_type,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 如果有response_format，添加到请求中
            if response_format:
                business_request["response_format"] = response_format
            
            print(f"[custom_handler] 发送到业务API的请求: {json.dumps(business_request, ensure_ascii=False, indent=2)}")
            # 发送请求到业务API
            response = requests.post(
                self.api_base,
                json=business_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                business_response = response.json()
                print(f"[custom_handler] 业务API响应: {json.dumps(business_response, ensure_ascii=False, indent=2)}")
                
                # 修复：正确提取content字段
                content = business_response.get("content", "Hello from custom LLM!")
                if isinstance(content, dict) and "message" in content:
                    # 提取message字段中的JSON字符串
                    mock_response = content["message"]
                    print(f"[custom_handler] 提取到JSON内容: {mock_response[:100]}...")
                else:
                    # 如果不是预期格式，直接使用content
                    mock_response = content if isinstance(content, str) else str(content)
                    print(f"[custom_handler] 使用原始内容: {mock_response}")
                
                return litellm.completion(
                    model="gpt-3.5-turbo",  # 使用一个已知的模型格式
                    messages=[{"role": "user", "content": user_query}],
                    mock_response=mock_response,
                )
            else:
                print(f"[custom_handler] 业务API错误: {response.status_code} - {response.text}")
                # 返回错误响应
                return litellm.completion(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_query}],
                    mock_response="抱歉，服务暂时不可用。",
                )
                
        except Exception as e:
            print(f"[custom_handler] 处理completion请求时出错: {str(e)}")
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
