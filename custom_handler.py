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

# 流式保存工具
try:
    from productAdapter.utils.dify_data_saver import (
        start_dify_stream_saver,
        DifyStreamingFileWriter,
    )
except Exception as _e:  # 兜底，避免导入失败导致运行中断
    start_dify_stream_saver = None  # type: ignore
    DifyStreamingFileWriter = None  # type: ignore

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

    # --- 流式保存封装 ---
    def init_start_dify_stream_saver(
        self,
        query_messages: Any,
        filename_prefix: str = "litellm_custom",
        response_id: Optional[str] = None,
        enable_stream_save: bool = True,
    ) -> tuple[Optional[DifyStreamingFileWriter], bool, Optional[str]]:
        """初始化并启动流式保存器，返回 (stream_saver, enable, response_id)。

        - 当保存器不可用或失败时，返回 (None, False, None)。
        - query_messages: 可为 messages 数组或简单字符串
        """
        if start_dify_stream_saver is None:
            return None, False, None
        try:
            project_root = os.path.abspath(os.path.dirname(__file__))
            rid = response_id or f"custom-{uuid.uuid4().hex[:10]}"
            stream_saver, enabled = start_dify_stream_saver(
                response_id=rid,
                query=query_messages,
                project_root=project_root,
                filename_prefix=filename_prefix,
                enable_stream_save=enable_stream_save,
            )
            logger.info(
                f"[custom_handler] init_start_dify_stream_saver: enabled={enabled}, response_id={rid}, saver={stream_saver}"
            )
            return stream_saver, enabled, rid
        except Exception as se:
            logger.warning(f"[custom_handler] 启动流式保存器失败: {se}")
            return None, False, None

    def save_stream_chunk(
        self,
        stream_saver: Optional[DifyStreamingFileWriter],
        enabled: bool,
        data: Any,
    ) -> None:
        """边流边写入一段数据。"""
        if not enabled or stream_saver is None:
            return
        try:
            stream_saver.write(data if isinstance(data, str) else str(data))
        except Exception:
            pass

    def finalize_stream_saver(
        self,
        stream_saver: Optional[DifyStreamingFileWriter],
        enabled: bool,
        chunk_count: int,
        processing_time: float = 0.0,
    ) -> None:
        """安全收尾保存器。"""
        try:
            if enabled and stream_saver is not None:
                stream_saver.set_final_stats(chunk_count=chunk_count, processing_time=processing_time)
                stream_saver.close()
        except Exception:
            pass

    async def _async_parse_standard_sse_to_generic_chunks(
        self,
        response,
        stream_saver: Optional[DifyStreamingFileWriter],
        enable_stream_save: bool,
        stats: Optional[Dict[str, int]] = None,
    ) -> AsyncIterator[GenericStreamingChunk]:
        """
        解析标准SSE (data: ...\n\n)，提取JSON中的 data.outputs.text，并转换为 GenericStreamingChunk 逐条输出。

        Args:
            response: aiohttp.ClientResponse 对象
            stream_saver: 日志保存器
            enable_stream_save: 是否保存流日志
            stats: 可选统计字典，包含 'chunk_count' 键用于回传计数
        """
        if stats is None:
            stats = {"chunk_count": 0, "event_count": 0}

        buffer = ""
        previous_text_fragment: Optional[str] = None
        seen_structured_chunk: bool = False
        have_seen_non_snapshot_chunk: bool = False
        full_snapshot_emitted: bool = False

        def parse_sse_block(block: str) -> tuple[Optional[str], str]:
            event_type: Optional[str] = None
            data_lines: list[str] = []
            for raw in block.splitlines():
                if raw.startswith(":"):
                    continue
                if raw.startswith("event:"):
                    event_type = raw[len("event:"):].strip() or None
                elif raw.startswith("data:"):
                    data_lines.append(raw[len("data:"):].lstrip())
            return event_type, "\n".join(data_lines)

        async for chunk in response.content.iter_chunked(1024):
            if not chunk:
                continue
            try:
                chunk_str = chunk.decode("utf-8", errors="ignore")
            except Exception:
                continue

            buffer += chunk_str

            # 按双换行拆分完整事件块
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                block = block.strip("\r\n")
                if not block:
                    continue

                event_type, data_payload = parse_sse_block(block)

                # 保存原始块（带 data 拼接后的内容）
                self.save_stream_chunk(stream_saver, enable_stream_save, f"[block] event={event_type or 'message'}\n{block}\n\n")

                # 统计事件数量（包含 ping / message / response 等）
                stats["event_count"] = stats.get("event_count", 0) + 1

                # 跳过 ping 或空数据
                if event_type == "ping" or not data_payload.strip():
                    continue

                if data_payload.strip() == "[DONE]":
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

                # 解析 JSON，兼容多种Dify格式，尽可能提取增量文本
                try:
                    payload = json.loads(data_payload)
                except Exception:
                    payload = data_payload  # 保留原始文本

                # 无论是否处于 structured chunk 流，优先检测完成事件，避免卡死
                try:
                    if (event_type == "workflow_finished") or (
                        isinstance(payload, dict) and (
                            payload.get("event") == "workflow_finished" or payload.get("type") == "complete"
                        )
                    ):
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
                except Exception:
                    pass

                extracted_text: str = ""
                try:
                    if isinstance(payload, dict):
                        # 优先直接透传 chunk 的原始字符串，避免内层JSON解析失败
                        if "type" in payload and "chunk" in payload:
                            inner_chunk = payload.get("chunk", "")
                            if isinstance(inner_chunk, str) and inner_chunk:
                                extracted_text = inner_chunk
                                seen_structured_chunk = True
                        # 当检测到 structured chunk 流时，避免同时再输出 text_chunk，防止重复累积导致上游解析出错
                        if not extracted_text and not seen_structured_chunk:
                            extracted_text = self._extract_text_from_sse_data(payload)
                        if not extracted_text:
                            extracted_text = (
                                payload.get("data", {})
                                .get("outputs", {})
                                .get("text", "")
                            )
                    elif isinstance(payload, str):
                        extracted_text = payload
                except Exception:
                    extracted_text = ""

                if extracted_text == "__WORKFLOW_FINISHED__":
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

                if isinstance(extracted_text, str) and extracted_text:
                    stripped_text = extracted_text.strip()
                    is_full_json_snapshot = stripped_text.startswith('{') and stripped_text.endswith('}')

                    # 若已输出过增量片段，则丢弃后续完整快照，避免上游累积两份JSON
                    if is_full_json_snapshot and have_seen_non_snapshot_chunk:
                        continue
                    # 完整快照只允许输出一次
                    if is_full_json_snapshot and full_snapshot_emitted:
                        continue
                    # 去重（忽略纯空白差异）
                    if previous_text_fragment is not None and stripped_text == previous_text_fragment.strip():
                        continue

                    previous_text_fragment = extracted_text
                    if is_full_json_snapshot:
                        full_snapshot_emitted = True
                    else:
                        have_seen_non_snapshot_chunk = True

                    stats["chunk_count"] = stats.get("chunk_count", 0) + 1
                    generic_streaming_chunk: GenericStreamingChunk = {
                        "finish_reason": None,
                        "index": 0,
                        "is_finished": False,
                        "text": extracted_text,
                        "tool_use": None,
                        "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                    }
                    yield generic_streaming_chunk

        # 处理连接结束后 buffer 中遗留的最后一块（若没有以空行结束）
        tail = buffer.strip("\r\n")
        if tail:
            event_type, data_payload = parse_sse_block(tail)
            self.save_stream_chunk(stream_saver, enable_stream_save, f"[tail-block] event={event_type or 'message'}\n{tail}\n")
            stats["event_count"] = stats.get("event_count", 0) + 1
            if data_payload.strip() and event_type != "ping":
                if data_payload.strip() == "[DONE]":
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
                try:
                    payload = json.loads(data_payload)
                except Exception:
                    payload = data_payload
                # 尾块也要优先检测完成事件，避免卡死
                try:
                    if (event_type == "workflow_finished") or (
                        isinstance(payload, dict) and (
                            payload.get("event") == "workflow_finished" or payload.get("type") == "complete"
                        )
                    ):
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
                except Exception:
                    pass
                extracted_text = ""
                try:
                    if isinstance(payload, dict):
                        if "type" in payload and "chunk" in payload:
                            inner_chunk = payload.get("chunk", "")
                            if isinstance(inner_chunk, str) and inner_chunk:
                                extracted_text = inner_chunk
                                seen_structured_chunk = True
                        if not extracted_text and not seen_structured_chunk:
                            extracted_text = self._extract_text_from_sse_data(payload)
                        if not extracted_text:
                            extracted_text = (
                                payload.get("data", {})
                                .get("outputs", {})
                                .get("text", "")
                            )
                    elif isinstance(payload, str):
                        extracted_text = payload
                except Exception:
                    extracted_text = ""

                if isinstance(extracted_text, str) and extracted_text:
                    stripped_text = extracted_text.strip()
                    is_full_json_snapshot = stripped_text.startswith('{') and stripped_text.endswith('}')
                    if is_full_json_snapshot and have_seen_non_snapshot_chunk:
                        pass
                    elif is_full_json_snapshot and full_snapshot_emitted:
                        pass
                    elif previous_text_fragment is not None and stripped_text == previous_text_fragment.strip():
                        pass
                    else:
                        previous_text_fragment = extracted_text
                        if is_full_json_snapshot:
                            full_snapshot_emitted = True
                        else:
                            have_seen_non_snapshot_chunk = True
                        stats["chunk_count"] = stats.get("chunk_count", 0) + 1
                        generic_streaming_chunk: GenericStreamingChunk = {
                            "finish_reason": None,
                            "index": 0,
                            "is_finished": False,
                            "text": extracted_text,
                            "tool_use": None,
                            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
                        }
                        yield generic_streaming_chunk

        # 结束兜底
        final_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": "",
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield final_chunk
    
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

            # 启动流式保存器（封装）
            stream_saver, enable_stream_save, _resp_id = self.init_start_dify_stream_saver(
                query_messages=messages,
                filename_prefix="litellm_custom",
                response_id=f"custom-sync-{uuid.uuid4().hex[:10]}",
                enable_stream_save=True,
            )
            
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
                                # 边流边保存原始SSE行
                            self.save_stream_chunk(stream_saver, enable_stream_save, line)
                            
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
            err_text = f"同步流式处理失败: {e}"
            print(f"❌ [custom_handler] {err_text}")
            logger.error(f"❌ [custom_handler] {err_text}")
        finally:
            # 收尾保存器
            try:
                if enable_stream_save and stream_saver is not None:
                    stream_saver.set_final_stats(chunk_count=locals().get('chunk_count', 0), processing_time=0.0)
                    stream_saver.close()
            except Exception:
                pass
            # 仅在异常路径上发送错误块
            if 'err_text' in locals():
                error_chunk: GenericStreamingChunk = {
                    "finish_reason": "stop",
                    "index": 0,
                    "is_finished": True,
                    "text": err_text,
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

            # 启动流式保存器（封装）
            stream_saver, enable_stream_save, _resp_id = self.init_start_dify_stream_saver(
                query_messages=messages,
                filename_prefix="litellm_custom",
                response_id=f"custom-async-{uuid.uuid4().hex[:10]}",
                enable_stream_save=True,
            )
            
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
                            # 提取为独立方法，提升可读性与复用性
                            stats: Dict[str, int] = {"chunk_count": 0}
                            async for generic_chunk in self._async_parse_standard_sse_to_generic_chunks(
                                response=response,
                                stream_saver=stream_saver,
                                enable_stream_save=enable_stream_save,
                                stats=stats,
                            ):
                                yield generic_chunk
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
            err_text = f"异步流式处理失败: {e}"
            print(f"❌ [custom_handler] {err_text}")
            logger.error(f"❌ [custom_handler] {err_text}")
        finally:
            # 收尾保存器
            try:
                if enable_stream_save and stream_saver is not None:
                    # 优先使用统计字典中的chunk_count
                    _stats = locals().get('stats', {}) if isinstance(locals().get('stats', {}), dict) else {}
                    final_count = _stats.get('chunk_count', 0)
                    stream_saver.set_final_stats(chunk_count=final_count, processing_time=0.0)
                    stream_saver.close()
            except Exception:
                pass
            # 仅在异常路径上发送错误块
            if 'err_text' in locals():
                error_chunk: GenericStreamingChunk = {
                    "finish_reason": "stop",
                    "index": 0,
                    "is_finished": True,
                    "text": err_text,
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
