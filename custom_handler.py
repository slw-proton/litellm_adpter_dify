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
from typing import Dict, List, Any, Optional, Iterator, AsyncIterator

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入LiteLLM相关模块
import litellm
from litellm import CustomLLM, completion, get_llm_provider
from litellm.types.utils import GenericStreamingChunk, ModelResponse

# 设置日志
logger = logging.getLogger(__name__)

class MyCustomLLM(CustomLLM):
    """
    自定义LLM处理器
    继承自LiteLLM的CustomLLM基类
    """
    
    def __init__(self):
        super().__init__()
        # 使用模拟SSE服务器进行测试
        self.api_base = "http://localhost:8002/api/process"
        print("[custom_handler] MyCustomLLM初始化完成 - 使用模拟SSE服务器")
    
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
            stream = self._extract_response_format(kwargs, "stream")
            # 构建业务API请求
            business_request = {
                "query": messages,  # 全量转发完整的messages数组
                "model_info": {
                    "name": model
                },
                "response_type": response_type,
                "stream": stream,
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
        try:
            # 从kwargs中提取参数
            model = kwargs.get("model", "business-api")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 100)
            temperature = kwargs.get("temperature", 0.7)
            stream = kwargs.get("stream", False)
            
            print(f'[custom_handler] async messages: {messages}')
            # 确保messages是数组格式
            if not isinstance(messages, list):
                print(f"[custom_handler] 警告：messages不是数组格式，类型为{type(messages)}，转换为数组")
                if isinstance(messages, str):
                    messages = [{"role": "user", "content": messages}]
                elif messages is None:
                    messages = []
                else:
                    messages = [{"role": "user", "content": str(messages)}]
            
            print(f"[custom_handler] 处理async completion请求: model={model}, messages={len(messages)}条消息, stream={stream}")
            
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
                "stream": stream,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            print(f"[custom_handler] 发送到业务API的异步请求: {json.dumps(business_request, ensure_ascii=False, indent=2)}")
            
            # 使用aiohttp进行异步请求
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_base,
                    json=business_request,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        business_response = await response.json()
                        print(f"[custom_handler] 业务API异步响应: {json.dumps(business_response, ensure_ascii=False, indent=2)}")
                        
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
                        error_text = await response.text()
                        print(f"[custom_handler] 业务API错误: {response.status} - {error_text}")
                        # 返回错误响应
                        return litellm.completion(
                            model="gpt-3.5-turbo",
                            messages=messages,  # 使用完整的messages数组
                            mock_response="抱歉，服务暂时不可用。",
                            api_key="dummy-key",  # 添加api_key参数
                        )
                        
        except Exception as e:
            print(f"[custom_handler] 处理async completion请求时出错: {str(e)}")
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

    def streaming(self, *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        """
        同步流式处理方法
        根据官方文档实现
        """
        try:
            # 从kwargs中提取参数
            model = kwargs.get("model", "business-api")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 100)
            temperature = kwargs.get("temperature", 0.7)
            
            print(f'[custom_handler] streaming messages: {messages}')
            # 确保messages是数组格式
            if not isinstance(messages, list):
                if isinstance(messages, str):
                    messages = [{"role": "user", "content": messages}]
                elif messages is None:
                    messages = []
                else:
                    messages = [{"role": "user", "content": str(messages)}]
            
            print(f"[custom_handler] 处理streaming请求: model={model}, messages={len(messages)}条消息")
            
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
                "stream": True,  # 强制设置为流式
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            print(f"[custom_handler] 发送到业务API的同步流式请求: {json.dumps(business_request, ensure_ascii=False, indent=2)}")
            
            # 使用requests进行同步请求
            import requests
            
            try:
                response = requests.post(
                    self.api_base,
                    json=business_request,
                    headers={"Content-Type": "application/json"},
                    timeout=60,
                    stream=True
                )
                
                if response.status_code == 200:
                    # 处理流式响应 - 逐个返回每个SSE数据块
                    chunk_count = 0
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            chunk_count += 1
                            print(f"[custom_handler] 🔄 STREAMING 第{chunk_count}个数据块: {line[:100]}...")
                            
                            # 解析SSE数据
                            if line.startswith('data: '):
                                try:
                                    # 移除 "data: " 前缀
                                    data_content = line[6:].strip()  # 移除 "data: " 前缀并去除空白
                                    
                                    if data_content == '[DONE]':
                                        # 流结束
                                        print(f"[custom_handler] 🏁 STREAMING 流结束信号")
                                        final_chunk: GenericStreamingChunk = {
                                            "finish_reason": "stop",
                                            "index": 0,
                                            "is_finished": True,
                                            "text": "",
                                            "tool_use": None,
                                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                        }
                                        yield final_chunk
                                        break
                                    else:
                                        # 尝试解析外层JSON数据（Dify的嵌套格式）
                                        try:
                                            outer_data = json.loads(data_content)
                                            
                                            # 检查是否是Dify的嵌套格式
                                            if isinstance(outer_data, dict) and "type" in outer_data and "chunk" in outer_data:
                                                # 这是Dify的嵌套格式，需要解析内层的chunk
                                                chunk_content = outer_data.get("chunk", "")
                                                if chunk_content:
                                                    # 解析内层的chunk内容
                                                    try:
                                                        inner_data = json.loads(chunk_content)
                                                        text_content = self._extract_text_from_sse_data(inner_data)
                                                        if text_content == "__WORKFLOW_FINISHED__":
                                                            print(f"[custom_handler] 🏁 STREAMING 工作流完成(修复后)")
                                                            final_chunk: GenericStreamingChunk = {
                                                                "finish_reason": "stop",
                                                                "index": 0,
                                                                "is_finished": True,
                                                                "text": "",
                                                                "tool_use": None,
                                                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                            }
                                                            yield final_chunk
                                                            return
                                                        elif text_content:
                                                            print(f"[custom_handler] 📤 STREAMING Yielding text_chunk内容(修复后): {text_content[:50]}...")
                                                            generic_streaming_chunk: GenericStreamingChunk = {
                                                                "finish_reason": None,
                                                                "index": 0,
                                                                "is_finished": False,
                                                                "text": text_content,
                                                                "tool_use": None,
                                                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                            }
                                                            yield generic_streaming_chunk
                                                        else:
                                                            print(f"[custom_handler] ⚠️ STREAMING text_chunk内容为空，跳过")
                                                            
                                                    except json.JSONDecodeError as inner_e:
                                                        # 内层JSON解析失败，可能是部分数据或单引号格式
                                                        print(f"[custom_handler] ⚠️ 内层JSON解析失败: {str(inner_e)}, chunk内容: {chunk_content[:100]}...")
                                                        # 尝试处理单引号格式
                                                        try:
                                                            # 替换单引号为双引号
                                                            chunk_content_fixed = chunk_content.replace("'", '"')
                                                            inner_data = json.loads(chunk_content_fixed)
                                                            text_content = self._extract_text_from_sse_data(inner_data)
                                                            if text_content:
                                                                print(f"[custom_handler] 📤 STREAMING Yielding text_chunk内容(修复后): {text_content[:50]}...")
                                                                generic_streaming_chunk: GenericStreamingChunk = {
                                                                    "finish_reason": None,
                                                                    "index": 0,
                                                                    "is_finished": False,
                                                                    "text": text_content,
                                                                    "tool_use": None,
                                                                    "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                                }
                                                                yield generic_streaming_chunk
                                                        except:
                                                            continue
                                            else:
                                                # 不是Dify的嵌套格式，按原来的方式处理
                                                text_content = self._extract_text_from_sse_data(outer_data)
                                                if text_content == "__WORKFLOW_FINISHED__":
                                                    print(f"[custom_handler] 🏁 STREAMING 工作流完成(修复后外层)")
                                                    final_chunk: GenericStreamingChunk = {
                                                        "finish_reason": "stop",
                                                        "index": 0,
                                                        "is_finished": True,
                                                        "text": "",
                                                        "tool_use": None,
                                                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                    }
                                                    yield final_chunk
                                                    return
                                                elif text_content:
                                                    print(f"[custom_handler] 📤 STREAMING Yielding内容(修复后): {text_content[:50]}...")
                                                    generic_streaming_chunk: GenericStreamingChunk = {
                                                        "finish_reason": None,
                                                        "index": 0,
                                                        "is_finished": False,
                                                        "text": text_content,
                                                        "tool_use": None,
                                                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                    }
                                                    yield generic_streaming_chunk
                                                else:
                                                    print(f"[custom_handler] ⚠️ STREAMING 直接内容为空，跳过")
                                                    
                                        except json.JSONDecodeError as outer_e:
                                            # 外层JSON解析失败，可能是部分数据或其他格式
                                            print(f"[custom_handler] ⚠️ 外层JSON解析失败: {str(outer_e)}, 原始内容: {data_content[:100]}...")
                                            # 尝试处理单引号格式
                                            try:
                                                # 替换单引号为双引号
                                                data_content_fixed = data_content.replace("'", '"')
                                                outer_data = json.loads(data_content_fixed)
                                                text_content = self._extract_text_from_sse_data(outer_data)
                                                if text_content:
                                                    print(f"[custom_handler] 📤 STREAMING Yielding内容(修复后): {text_content[:50]}...")
                                                    generic_streaming_chunk: GenericStreamingChunk = {
                                                        "finish_reason": None,
                                                        "index": 0,
                                                        "is_finished": False,
                                                        "text": text_content,
                                                        "tool_use": None,
                                                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                    }
                                                    yield generic_streaming_chunk
                                            except:
                                                continue
                                            
                                except Exception as e:
                                    # 如果整体解析失败，记录错误但继续处理
                                    print(f"[custom_handler] ⚠️ SSE解析异常: {str(e)}, 行内容: {line[:100]}...")
                                    continue
                    
                    # 确保发送完成信号
                    print(f"[custom_handler] 🏁 STREAMING 发送最终完成信号，总共处理了{chunk_count}个数据块")
                    final_chunk: GenericStreamingChunk = {
                        "finish_reason": "stop",
                        "index": 0,
                        "is_finished": True,
                        "text": "",
                        "tool_use": None,
                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                    }
                    yield final_chunk
                else:
                    error_text = response.text
                    print(f"[custom_handler] 业务API返回错误: {response.status_code} - {error_text}")
                    # 发送错误块
                    error_chunk: GenericStreamingChunk = {
                        "finish_reason": "stop",
                        "index": 0,
                        "is_finished": True,
                        "text": f"业务API错误: {response.status_code} - {error_text}",
                        "tool_use": None,
                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                    }
                    yield error_chunk
                    
            except Exception as e:
                error_msg = f"请求业务API失败: {str(e)}"
                print(f"[custom_handler] {error_msg}")
                # 发送错误块
                error_chunk: GenericStreamingChunk = {
                    "finish_reason": "stop",
                    "index": 0,
                    "is_finished": True,
                    "text": f"请求失败: {error_msg}",
                    "tool_use": None,
                    "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                }
                yield error_chunk
                
        except Exception as e:
            error_msg = f"同步流式处理失败: {str(e)}"
            print(f"❌ [custom_handler] {error_msg}")
            logger.error(f"❌ [custom_handler] {error_msg}")
            # 发送错误块
            error_chunk: GenericStreamingChunk = {
                "finish_reason": "stop",
                "index": 0,
                "is_finished": True,
                "text": f"处理失败: {error_msg}",
                "tool_use": None,
                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
            }
            yield error_chunk

    async def astreaming(self, *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """
        异步流式处理方法
        使用真正的异步流式读取，保持即时处理
        """
        try:
            # 从kwargs中提取参数
            model = kwargs.get("model", "business-api")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 100)
            temperature = kwargs.get("temperature", 0.7)
            
            print(f'[custom_handler] async streaming messages: {messages}')
            # 确保messages是数组格式
            if not isinstance(messages, list):
                if isinstance(messages, str):
                    messages = [{"role": "user", "content": messages}]
                elif messages is None:
                    messages = []
                else:
                    messages = [{"role": "user", "content": str(messages)}]
            
            print(f"[custom_handler] 处理async streaming请求: model={model}, messages={len(messages)}条消息")
            
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
                "stream": True,  # 强制设置为流式
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            print(f"[custom_handler] 发送到业务API的异步流式请求: {json.dumps(business_request, ensure_ascii=False, indent=2)}")
            
            # 使用aiohttp进行异步请求
            import aiohttp
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_base,
                        json=business_request,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            # 处理流式响应 - 保持即时处理
                            chunk_count = 0
                            
                            print(f"[custom_handler] 🔄 开始异步流式读取响应...")
                            
                            # 使用较小的chunk size提高实时性，但保持即时处理
                            async for chunk in response.content.iter_chunked(256):
                                if chunk:
                                    chunk_count += 1
                                    # 解码字节为字符串
                                    chunk_str = chunk.decode('utf-8', errors='ignore')
                                    print(f"[custom_handler] 🔄 ASYNC_STREAMING 第{chunk_count}个网络块 (大小: {len(chunk)}字节): {chunk_str[:200]}...")
                                    
                                    # 按行分割并立即处理每个SSE行 - 保持即时处理
                                    lines = chunk_str.split('\n')
                                    for line in lines:
                                        line_str = line.strip()
                                        if line_str and line_str.startswith('data: '):
                                            try:
                                                # 移除 "data: " 前缀
                                                data_content = line_str[6:].strip()
                                                
                                                if data_content == '[DONE]':
                                                    print(f"[custom_handler] 🏁 ASYNC_STREAMING 流结束信号")
                                                    final_chunk: GenericStreamingChunk = {
                                                        "finish_reason": "stop",
                                                        "index": 0,
                                                        "is_finished": True,
                                                        "text": "",
                                                        "tool_use": None,
                                                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                    }
                                                    yield final_chunk
                                                    return
                                                
                                                # 解析JSON数据
                                                outer_data = json.loads(data_content)
                                                
                                                # 处理Dify的嵌套格式
                                                if isinstance(outer_data, dict) and "type" in outer_data and "chunk" in outer_data:
                                                    chunk_content = outer_data.get("chunk", "")
                                                    if chunk_content:
                                                        try:
                                                            inner_data = json.loads(chunk_content)
                                                            text_content = self._extract_text_from_sse_data(inner_data)
                                                        except json.JSONDecodeError:
                                                            # 尝试修复单引号格式
                                                            chunk_content_fixed = chunk_content.replace("'", '"')
                                                            try:
                                                                inner_data = json.loads(chunk_content_fixed)
                                                                text_content = self._extract_text_from_sse_data(inner_data)
                                                            except:
                                                                text_content = ""
                                                                continue
                                                        
                                                        if text_content == "__WORKFLOW_FINISHED__":
                                                            print(f"[custom_handler] 🏁 ASYNC_STREAMING 工作流完成")
                                                            final_chunk: GenericStreamingChunk = {
                                                                "finish_reason": "stop",
                                                                "index": 0,
                                                                "is_finished": True,
                                                                "text": "",
                                                                "tool_use": None,
                                                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                            }
                                                            yield final_chunk
                                                            return
                                                        elif text_content:
                                                            print(f"[custom_handler] 📤 ASYNC_STREAMING Yielding text_chunk内容: {text_content[:50]}...")
                                                            generic_streaming_chunk: GenericStreamingChunk = {
                                                                "finish_reason": None,
                                                                "index": 0,
                                                                "is_finished": False,
                                                                "text": text_content,
                                                                "tool_use": None,
                                                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                            }
                                                            yield generic_streaming_chunk
                                                
                                                # 处理Dify的直接事件格式
                                                elif isinstance(outer_data, dict) and "type" in outer_data:
                                                    text_content = self._extract_text_from_sse_data(outer_data)
                                                    if text_content == "__WORKFLOW_FINISHED__":
                                                        print(f"[custom_handler] 🏁 ASYNC_STREAMING 工作流完成(直接事件)")
                                                        final_chunk: GenericStreamingChunk = {
                                                            "finish_reason": "stop",
                                                            "index": 0,
                                                            "is_finished": True,
                                                            "text": "",
                                                            "tool_use": None,
                                                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                        }
                                                        yield final_chunk
                                                        return
                                                    elif text_content:
                                                        print(f"[custom_handler] 📤 ASYNC_STREAMING Yielding直接事件内容: {text_content[:50]}...")
                                                        generic_streaming_chunk: GenericStreamingChunk = {
                                                            "finish_reason": None,
                                                            "index": 0,
                                                            "is_finished": False,
                                                            "text": text_content,
                                                            "tool_use": None,
                                                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                        }
                                                        yield generic_streaming_chunk
                                                
                                                # 处理其他格式
                                                else:
                                                    text_content = self._extract_text_from_sse_data(outer_data)
                                                    if text_content == "__WORKFLOW_FINISHED__":
                                                        print(f"[custom_handler] 🏁 ASYNC_STREAMING 工作流完成(直接格式)")
                                                        final_chunk: GenericStreamingChunk = {
                                                            "finish_reason": "stop",
                                                            "index": 0,
                                                            "is_finished": True,
                                                            "text": "",
                                                            "tool_use": None,
                                                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                        }
                                                        yield final_chunk
                                                        return
                                                    elif text_content:
                                                        print(f"[custom_handler] 📤 ASYNC_STREAMING Yielding直接内容: {text_content[:50]}...")
                                                        generic_streaming_chunk: GenericStreamingChunk = {
                                                            "finish_reason": None,
                                                            "index": 0,
                                                            "is_finished": False,
                                                            "text": text_content,
                                                            "tool_use": None,
                                                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                                                        }
                                                        yield generic_streaming_chunk
                                            
                                            except json.JSONDecodeError as e:
                                                # JSON解析失败，可能是部分数据或其他格式
                                                print(f"[custom_handler] ⚠️ JSON解析失败: {str(e)}, 原始内容: {data_content[:100]}...")
                                                continue
                                            except Exception as e:
                                                # 如果整体解析失败，记录错误但继续处理
                                                print(f"[custom_handler] ⚠️ SSE解析异常: {str(e)}, 行内容: {line_str[:100]}...")
                                                continue
                            
                            # 确保发送完成信号
                            print(f"[custom_handler] 🏁 ASYNC_STREAMING 发送最终完成信号，总共处理了{chunk_count}个数据块")
                            final_chunk: GenericStreamingChunk = {
                                "finish_reason": "stop",
                                "index": 0,
                                "is_finished": True,
                                "text": "",
                                "tool_use": None,
                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                            }
                            yield final_chunk
                        else:
                            error_text = await response.text()
                            print(f"[custom_handler] 业务API返回错误: {response.status} - {error_text}")
                            # 发送错误块
                            error_chunk: GenericStreamingChunk = {
                                "finish_reason": "stop",
                                "index": 0,
                                "is_finished": True,
                                "text": f"业务API错误: {response.status} - {error_text}",
                                "tool_use": None,
                                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                            }
                            yield error_chunk
                            
            except Exception as e:
                error_msg = f"请求业务API失败: {str(e)}"
                print(f"[custom_handler] {error_msg}")
                # 发送错误块
                error_chunk: GenericStreamingChunk = {
                    "finish_reason": "stop",
                    "index": 0,
                    "is_finished": True,
                    "text": f"请求失败: {error_msg}",
                    "tool_use": None,
                    "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                }
                yield error_chunk
                
        except Exception as e:
            error_msg = f"异步流式处理失败: {str(e)}"
            print(f"❌ [custom_handler] {error_msg}")
            logger.error(f"❌ [custom_handler] {error_msg}")
            # 发送错误块
            error_chunk: GenericStreamingChunk = {
                "finish_reason": "stop",
                "index": 0,
                "is_finished": True,
                "text": f"处理失败: {error_msg}",
                "tool_use": None,
                "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
            }
            yield error_chunk

    def _extract_text_from_sse_data(self, sse_data: dict) -> str:
        """
        从SSE数据中提取文本内容
        
        Args:
            sse_data: SSE数据字典
            
        Returns:
            str: 提取的文本内容，如果没有文本内容则返回空字符串，如果是workflow_finished则返回特殊标记
        """
        if not isinstance(sse_data, dict):
            return ""
        
        # 处理text_chunk事件
        if sse_data.get("event") == "text_chunk":
            text_content = sse_data.get("data", {}).get("text", "")
            if text_content:
                return text_content
        
        # 处理workflow_finished事件
        elif sse_data.get("event") == "workflow_finished":
            # 工作流完成，返回特殊标记
            return "__WORKFLOW_FINISHED__"
        
        # 处理Dify的chunk事件（直接返回chunk内容）
        elif sse_data.get("type") == "chunk":
            chunk_content = sse_data.get("chunk", "")
            if chunk_content:
                return chunk_content
        
        # 处理Dify的status事件（记录但不返回内容）
        elif sse_data.get("type") == "status":
            status_message = sse_data.get("status", "")
            print(f"[custom_handler] 📊 状态更新: {status_message}")
            return ""  # 状态事件不返回内容
        
        # 处理Dify的complete事件
        elif sse_data.get("type") == "complete":
            print(f"[custom_handler] 🏁 收到完成事件")
            return "__WORKFLOW_FINISHED__"
        
        # 处理其他事件类型（node_started, node_finished等）
        elif sse_data.get("event") in ["node_started", "node_finished", "workflow_started"]:
            # 这些事件不包含文本内容，返回空字符串
            return ""
        
        # 如果不是事件格式，尝试直接提取text或content字段
        else:
            text_content = sse_data.get("text", "") or sse_data.get("content", "")
            if text_content:
                return text_content
        
        return ""

# 创建实例
my_custom_llm = MyCustomLLM()
