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
    
    def _extract_response_format(self, kwargs: dict, key: str = "response_format") -> tuple[Optional[Dict[str, Any]], str]:
        """
        从kwargs中提取指定参数并确定响应类型
        
        Args:
            kwargs: 包含optional_params和指定参数的参数字典
            key: 要提取的参数名称，默认为 "response_format"
            
        Returns:
            tuple: (extracted_value, response_type)
                - extracted_value: 提取的参数值或None
                - response_type: 响应类型字符串 ("text" 或 "json")
        
        Examples:
            # 提取response_format参数
            response_format, response_type = self._extract_response_format(kwargs, "response_format")
            
            # 提取temperature参数
            temperature, _ = self._extract_response_format(kwargs, "temperature")
        """
        if not isinstance(kwargs, dict):
            print(f"[custom_handler] ⚠️ kwargs不是字典类型: {type(kwargs)}")
            return None, "text"
        
        # 安全地检查optional_params中的指定参数
        optional_params = kwargs.get('optional_params', {})
        if optional_params and not isinstance(optional_params, dict):
            print(f"[custom_handler] ⚠️ optional_params不是字典类型: {type(optional_params)}")
            optional_params = {}
        
        print(f"[custom_handler] optional_params keys: {list(optional_params.keys()) if optional_params else 'None'}")
        
        # 优先从optional_params中获取指定参数，如果没有再从kwargs中获取
        extracted_value = None
        if optional_params and key in optional_params:
            extracted_value = optional_params[key]
            print(f"[custom_handler] ✅ 从optional_params检测到{key}: {extracted_value.get('type', 'unknown') if isinstance(extracted_value, dict) else extracted_value}")
            if extracted_value and isinstance(extracted_value, dict):
                print(f"[custom_handler] optional_params.{key}详情: {json.dumps(extracted_value, ensure_ascii=False, indent=2)}")
        elif kwargs.get(key) is not None:
            extracted_value = kwargs.get(key)
            print(f"[custom_handler] ✅ 从kwargs检测到{key}: {extracted_value.get('type', 'unknown') if isinstance(extracted_value, dict) else extracted_value}")
            if isinstance(extracted_value, dict):
                print(f"[custom_handler] {key}详情: {json.dumps(extracted_value, ensure_ascii=False, indent=2)}")
        else:
            print(f"[custom_handler] ⚠️ 未检测到{key}参数（kwargs.{key}={kwargs.get(key)}, optional_params.{key}={optional_params.get(key) if optional_params else 'N/A'}）")
        
        # 确定响应类型（仅对response_format参数）
        response_type = "text"
        if key == "response_format" and extracted_value:
            if isinstance(extracted_value, dict):
                if extracted_value.get("type") == "json_schema":
                    response_type = "json"
                    print(f"[custom_handler] 设置响应类型为JSON（structured output）")
                elif extracted_value.get("type") == "json_object":
                    response_type = "json"
                    print(f"[custom_handler] 设置响应类型为JSON object")
        
        return extracted_value, response_type
    
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
            print(f'[custom_handler] messages: {messages}')
            # 确保messages是数组格式
            if not isinstance(messages, list):
                print(f"[custom_handler] 警告：messages不是数组格式，类型为{type(messages)}，转换为数组")
                if isinstance(messages, str):
                    messages = [{"role": "user", "content": messages}]
                elif messages is None:
                    messages = []
                else:
                    messages = [{"role": "user", "content": str(messages)}]
            
            print(f"[custom_handler] 处理completion请求: model={model}, messages={len(messages)}条消息")
            print(f"[custom_handler] 完整kwargs keys: {list(kwargs.keys())}")
            
            # 提取response_format并确定响应类型
            response_format, response_type = self._extract_response_format(kwargs, "response_format")
            messages.append({"role": "response_format", "content": response_format})
            
            # 构建业务API请求
            business_request = {
                "query": messages,  # 全量转发完整的messages数组
                "model_info": {
                    "name": model
                },
                "response_type": response_type,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
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
                
                # 确保mock_response不为空
                if not mock_response or mock_response.strip() == "":
                    mock_response = "Hello from custom LLM! (业务API返回空内容)"
                    print(f"[custom_handler] 业务API返回空内容，使用默认响应: {mock_response}")
                
                return litellm.completion(
                    model="gpt-3.5-turbo",  # 使用一个已知的模型格式
                    messages=messages,  # 使用完整的messages数组
                    mock_response=mock_response,
                    api_key="dummy-key",  # 添加api_key参数
                )
            else:
                print(f"[custom_handler] 业务API错误: {response.status_code} - {response.text}")
                # 返回错误响应
                return litellm.completion(
                    model="gpt-3.5-turbo",
                    messages=messages,  # 使用完整的messages数组
                    mock_response="抱歉，服务暂时不可用。",
                    api_key="dummy-key",  # 添加api_key参数
                )
                
        except Exception as e:
            print(f"[custom_handler] 处理completion请求时出错: {str(e)}")
            # 确保messages是数组格式
            if 'messages' in locals():
                if not isinstance(messages, list):
                    if isinstance(messages, str):
                        messages = [{"role": "user", "content": messages}]
                    elif messages is None:
                        messages = []
                    else:
                        messages = [{"role": "user", "content": str(messages)}]
            else:
                messages = []
            
            # 返回错误响应
            return litellm.completion(
                model="gpt-3.5-turbo",
                messages=messages,  # 使用完整的messages数组
                mock_response="抱歉，处理请求时出现错误。",
                api_key="dummy-key",  # 添加api_key参数
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
