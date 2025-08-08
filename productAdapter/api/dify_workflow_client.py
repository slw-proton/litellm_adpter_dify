#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dify工作流客户端模块
用于与Dify平台的工作流API进行交互
"""

import json
import logging
import os
import sys
import time
import requests
from typing import Dict, Any, AsyncGenerator

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目内部模块
try:
    from productAdapter.utils.logging_init import init_logger_with_env_loader
    # 使用统一的日志配置
    logger = init_logger_with_env_loader("dify_workflow_client", project_root)
except ImportError:
    # 如果导入失败，使用默认日志配置
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

class DifyWorkflowClient:
    """
    Dify工作流客户端
    用于调用Dify平台的工作流API
    """
    
    # 类级别的配置
    _api_key = None
    _base_url = None
    _workflow_id = None
    
    @classmethod
    def _load_config(cls):
        """加载配置"""
        if cls._api_key is None:
            cls._api_key = os.getenv("DIFY_API_KEY", "")
        if cls._base_url is None:
            cls._base_url = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
        if cls._workflow_id is None:
            cls._workflow_id = os.getenv("DIFY_WORKFLOW_ID", "")
    
    def __init__(self, api_key: str = None, base_url: str = None, workflow_id: str = None):
        """
        初始化Dify工作流客户端
        
        Args:
            api_key: Dify API密钥（如果为None，将从环境变量获取）
            base_url: Dify API基础URL（如果为None，将从环境变量获取）
            workflow_id: 工作流ID（如果为None，将从环境变量获取）
        """
        # 加载配置
        self._load_config()
        
        # 使用提供的参数或默认配置
        self.api_key = api_key or self._api_key
        self.base_url = (base_url or self._base_url).rstrip('/')
        self.workflow_id = workflow_id or self._workflow_id
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"DifyWorkflowClient初始化完成，基础URL: {self.base_url}")
    
    def run_workflow(self, workflow_id: str, input_data: Dict[str, Any], response_mode: str = "blocking") -> Dict[str, Any]:
        """
        运行指定的工作流
        
        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据，包含App定义的各变量值
            response_mode: 响应模式 (blocking, streaming)
            
        Returns:
            响应结果
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/workflows/run"
        payload = {
            "workflow_id": workflow_id,
            "inputs": input_data,  # inputs字段是必需的，包含App定义的各变量值
            "response_mode": response_mode,
            "user": "api-user"
        }
        
        logger.info(f"🌐 调用Dify工作流API")
        logger.info(f"   📍 URL: {url}")
        logger.info(f"   🆔 工作流ID: {workflow_id}")
        logger.info(f"   📊 响应模式: {response_mode}")
        logger.info(f"   📤 请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            logger.info(f"🚀 发送POST请求到Dify API...")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            logger.info(f"📊 收到响应: 状态码={response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Dify工作流API调用成功")
                logger.info(f"📋 响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                error_msg = f"请求失败，状态码：{response.status_code}，响应内容：{response.text}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 响应头: {dict(response.headers)}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Dify工作流API调用超时"
            logger.error(f"⏰ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Dify工作流API调用异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常类型: {type(e).__name__}")
            raise Exception(error_msg)
    
    def run_workflow_streaming(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行指定的工作流（流式模式）
        
        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据，包含App定义的各变量值
            
        Returns:
            响应结果
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/workflows/run"
        payload = {
            "workflow_id": workflow_id,
            "inputs": input_data,  # inputs字段是必需的，包含App定义的各变量值
            "response_mode": "streaming",
            "user": "api-user"
        }
        
        logger.info(f"🌐 调用Dify工作流API（流式模式）")
        logger.info(f"   📍 URL: {url}")
        logger.info(f"   🆔 工作流ID: {workflow_id}")
        logger.info(f"   📊 响应模式: streaming")
        logger.info(f"   📤 请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            logger.info(f"🚀 发送POST请求到Dify API（流式模式）...")
            # 使用stream=True来获取流式响应
            response = requests.post(url, headers=self.headers, json=payload, timeout=30, stream=True)
            
            logger.info(f"📊 收到流式响应: 状态码={response.status_code}")
            
            if response.status_code == 200:
                # 对于流式响应，我们需要逐步读取数据
                result = {"streaming": True, "response": response}
                logger.info(f"✅ Dify工作流API流式调用成功")
                return result
            else:
                error_msg = f"流式请求失败，状态码：{response.status_code}，响应内容：{response.text}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 响应头: {dict(response.headers)}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Dify工作流API流式调用超时"
            logger.error(f"⏰ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Dify工作流API流式调用异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常类型: {type(e).__name__}")
            raise Exception(error_msg)

    def get_workflow_status(self, workflow_run_id: str) -> Dict[str, Any]:
        """
        获取工作流执行状态
        
        Args:
            workflow_run_id: 工作流运行 ID
            
        Returns:
            执行状态
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/workflows/run/{workflow_run_id}"
        logger.info(f"🔄 获取工作流执行状态")
        logger.info(f"   📍 URL: {url}")
        logger.info(f"   🆔 运行ID: {workflow_run_id}")
        
        try:
            logger.info(f"🚀 发送GET请求到Dify API...")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            logger.info(f"📊 收到响应: 状态码={response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 获取工作流执行状态成功")
                logger.info(f"📋 状态结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                # 确保返回有效的字典，即使是空字典
                return result if isinstance(result, dict) else {}
            else:
                error_msg = f"请求失败，状态码：{response.status_code}，响应内容：{response.text}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 响应头: {dict(response.headers)}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "获取工作流执行状态超时"
            logger.error(f"⏰ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"获取工作流执行状态异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常类型: {type(e).__name__}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"获取工作流执行状态时发生未知错误: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常类型: {type(e).__name__}")
            raise Exception(error_msg)
    
    def stop_workflow_execution(self, task_id: str, user: str = "api-user") -> Dict[str, Any]:
        """
        停止工作流执行
        
        Args:
            task_id: 任务 ID，可在流式返回 Chunk 中获取
            user: 用户标识，必须和执行 workflow 接口传入的 user 保持一致
            
        Returns:
            响应结果
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/workflows/tasks/{task_id}/stop"
        logger.info(f"停止工作流执行: {url}")
        logger.info(f"用户标识: {user}")
        
        # 构建请求体
        payload = {
            "user": user
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("停止工作流执行成功")
                return result
            else:
                error_msg = f"请求失败，状态码：{response.status_code}，响应内容：{response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "停止工作流执行超时"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"停止工作流执行异常: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def health_check(self) -> bool:
        """
        检查Dify API连接状态
        
        Returns:
            True: 连接正常
            False: 连接异常
        """
        try:
            # 尝试访问一个简单的端点来检查连接
            test_url = f"{self.base_url}/health"
            response = requests.get(test_url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Dify API健康检查失败: {str(e)}")
            return False
    
    def format_input_data(self, query: Any) -> Dict[str, Any]:
        """
        格式化输入数据，从messages数组中提取不同角色的内容
        
        Args:
            query: 用户查询内容或消息数组
            
        Returns:
            Dict[str, Any]: 格式化后的输入数据字典
        """
        input_data = {}
        
        if isinstance(query, list):
            # 如果是messages数组，提取不同角色的内容
            system_content = ""
            user_content = ""
            response_format_content = None
            
            for msg in query:
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    
                    if role == "system":
                        system_content = content
                    elif role == "user":
                        user_content = content
                    elif role == "response_format":
                        response_format_content = content
            
            # 将提取的内容放入input_data
            if system_content:
                input_data["system"] = system_content
            if user_content:
                input_data["user"] = user_content
            if response_format_content is not None:
                input_data["response_format"] = json.dumps(response_format_content)
            
            # # 始终生成querydata字段，优先使用user内容，如果没有则使用整个query的JSON
            # if user_content:
            #     input_data["querydata"] = user_content
            # else:
            #     query_string = json.dumps(query, ensure_ascii=False)
            #     input_data["querydata"] = query_string
        else:
            # 如果是字符串，直接使用querydata字段
            input_data["querydata"] = str(query)
        
        return input_data

    def format_output_data(self, outputs: Any) -> str:
        """
        格式化输出数据，从Dify工作流返回的outputs中提取内容
        
        Args:
            outputs: Dify工作流返回的输出数据
            
        Returns:
            str: 格式化后的内容字符串
        """
        if not outputs:
            return "工作流执行完成，但未返回输出数据。"
        
        if isinstance(outputs, dict):
            # 如果是字典，尝试从不同字段中提取内容
            if "text" in outputs:
                content = outputs["text"]
                logger.info(f"✅ 从outputs.text中提取到内容")
            elif "querydata" in outputs:
                content = outputs["querydata"]
                logger.info(f"✅ 从outputs.querydata中提取到内容")
            else:
                # 如果都没有，使用整个outputs
                content = json.dumps(outputs, ensure_ascii=False)
                logger.info(f"✅ 使用整个outputs作为内容")
        elif isinstance(outputs, str):
            # 如果是字符串，直接使用
            content = outputs
            logger.info(f"✅ 直接使用outputs字符串作为内容")
        else:
            # 其他类型，转换为字符串
            content = str(outputs)
            logger.info(f"✅ 将outputs转换为字符串作为内容")
        
        logger.info(f"📄 提取到的内容: {json.dumps(content, ensure_ascii=False, indent=2)}")
        return content

    def process_query(self, query: Any, workflow_id: str) -> Dict[str, Any]:
        """
        处理查询的便捷方法
        完整的工作流调用流程：运行工作流 -> 获取状态 -> 提取结果
        
        Args:
            query: 用户查询内容或消息数组
            workflow_id: 工作流ID
            
        Returns:
            包含处理结果的字典，格式如下：
            {
                "success": bool,
                "content": str,
                "workflow_run_id": str,
                "error": str,
                "processing_time": float
            }
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 开始处理Dify工作流查询")
            # 使用format_input_data函数格式化输入数据
            input_data = self.format_input_data(query)
            
            logger.info(f"🆔 工作流ID: {workflow_id}")
            logger.info(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            logger.info(f"📝 使用阻塞模式处理")
            # 运行工作流
            workflow_result = self.run_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                response_mode="blocking"
            )
            
            # 获取工作流执行状态和结果
            workflow_run_id = workflow_result.get("workflow_run_id")
            if not workflow_run_id:
                error_msg = "工作流执行失败，未获取到执行ID"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 工作流结果详情: {json.dumps(workflow_result, ensure_ascii=False, indent=2)}")
                raise Exception(error_msg)
            
            logger.info(f"✅ 工作流执行成功，执行ID: {workflow_run_id}")
            logger.info(f"📋 工作流结果: {json.dumps(workflow_result, ensure_ascii=False, indent=2)}")
            
            # 获取执行状态
            logger.info(f"🔄 获取工作流执行状态...")
            status_result = self.get_workflow_status(workflow_run_id)
            
            # 检查status_result是否有效
            if not isinstance(status_result, dict):
                error_msg = f"获取工作流执行状态失败，返回了无效类型: {type(status_result)}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
            logger.info(f"📊 工作流执行状态: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
            
            # 从data.outputs中获取内容 
            outputs = status_result.get("outputs", {})
            
            logger.info(f"📤 原始outputs: {json.dumps(outputs, ensure_ascii=False, indent=2)}")
            
            # 使用format_output_data函数格式化输出数据
            content = self.format_output_data(outputs)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ 查询处理完成，耗时: {processing_time:.2f}秒")
            logger.info(f"📊 最终结果: {json.dumps({'success': True, 'content_length': len(str(content)), 'workflow_run_id': workflow_run_id, 'processing_time': processing_time}, ensure_ascii=False, indent=2)}")
            
            return {
                "success": True,
                "content": content,
                "workflow_run_id": workflow_run_id,
                "error": "",
                "processing_time": processing_time
            }
            
        except Exception as e:
            error_msg = f"查询处理失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常详情: {type(e).__name__}: {str(e)}")
            processing_time = time.time() - start_time
            logger.error(f"⏱️ 处理耗时: {processing_time:.2f}秒")
            
            return {
                "success": False,
                "content": "",
                "workflow_run_id": "",
                "error": error_msg,
                "processing_time": processing_time
            }

    @classmethod
    def process_query_with_config(cls, query: Any, api_key: str = None, base_url: str = None, workflow_id: str = None) -> Dict[str, Any]:
        """
        带配置检查的查询处理方法
        包含完整的配置验证和错误处理
        
        Args:
            query: 用户查询内容或消息数组
            api_key: Dify API密钥（如果为None，将从环境变量获取）
            base_url: Dify API基础URL（如果为None，将从环境变量获取）
            workflow_id: 工作流ID（如果为None，将从环境变量获取）
            
        Returns:
            包含处理结果的字典，格式如下：
            {
                "success": bool,
                "content": str,
                "workflow_run_id": str,
                "error": str,
                "processing_time": float
            }
        """
        start_time = time.time()
        
        logger.info(f"🔧 开始Dify工作流配置检查...")
        
        # 加载配置
        cls._load_config()
        
        # 使用提供的参数或默认配置
        api_key = api_key or cls._api_key
        base_url = base_url or cls._base_url
        workflow_id = workflow_id or cls._workflow_id
        
        logger.info(f"📋 配置信息:")
        logger.info(f"   🔑 API密钥: {'已设置' if api_key else '未设置'}")
        logger.info(f"   🌐 基础URL: {base_url}")
        logger.info(f"   🆔 工作流ID: {workflow_id if workflow_id else '未设置'}")
        
        # 配置检查
        if not api_key or not workflow_id:
            error_msg = "Dify配置不完整，请检查DIFY_API_KEY和DIFY_WORKFLOW_ID环境变量"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 配置详情: API_KEY={'已设置' if api_key else '未设置'}, WORKFLOW_ID={'已设置' if workflow_id else '未设置'}")
            return {
                "success": False,
                "content": "Dify配置不完整，请检查环境变量配置。",
                "workflow_run_id": "",
                "error": error_msg,
                "processing_time": time.time() - start_time
            }
        
        # 查询内容检查
        if isinstance(query, list):
            # 如果是messages数组，检查是否为空
            if not query:
                error_msg = "请提供有效的查询内容"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 查询内容: 空消息数组")
                return {
                    "success": False,
                    "content": "请提供有效的查询内容。",
                    "workflow_run_id": "",
                    "error": error_msg,
                    "processing_time": time.time() - start_time
                }
            query_content = query  # 直接使用query，不做转换
        else:
            # 如果是字符串，检查是否为空
            if not query or not str(query).strip():
                error_msg = "请提供有效的查询内容"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 查询内容: '{query}'")
                return {
                    "success": False,
                    "content": "请提供有效的查询内容。",
                    "workflow_run_id": "",
                    "error": error_msg,
                    "processing_time": time.time() - start_time
                }
            query_content = query  # 直接使用query，不做转换
        
        logger.info(f"✅ 配置检查通过，开始处理查询...")
        
        try:
            # 初始化客户端并处理查询
            logger.info(f"🔧 初始化DifyWorkflowClient...")
            client = cls(api_key=api_key, base_url=base_url, workflow_id=workflow_id)
            logger.info(f"✅ DifyWorkflowClient初始化完成")
            
            result = client.process_query(
                query=query_content,
                workflow_id=workflow_id
            )
            
            # 添加配置检查的处理时间
            result["processing_time"] += time.time() - start_time
            logger.info(f"📊 总处理时间: {result['processing_time']:.2f}秒")
            
            return result
            
        except Exception as e:
            error_msg = f"Dify工作流执行失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"🔍 异常详情: {type(e).__name__}: {str(e)}")
            processing_time = time.time() - start_time
            logger.error(f"⏱️ 总处理耗时: {processing_time:.2f}秒")
            
            return {
                "success": False,
                "content": f"工作流执行失败: {str(e)}",
                "workflow_run_id": "",
                "error": error_msg,
                "processing_time": processing_time
            }

    @classmethod
    async def stream_dify_response(cls, query: Any, response_id: str = None, start_time: float = None) -> AsyncGenerator[str, None]:
        """
        流式处理Dify响应
        
        Args:
            query: 查询内容
            response_id: 响应ID（可选）
            start_time: 开始时间（可选）
            
        Yields:
            SSE格式的数据块
        """
        try:
            logger.info(f"🔄 开始流式处理Dify工作流查询")
            
            # 加载配置
            cls._load_config()
            
            if not cls._api_key or not cls._workflow_id:
                error_msg = "Dify配置不完整"
                logger.error(f"❌ {error_msg}")
                yield json.dumps({'error': error_msg}, ensure_ascii=False)
                return
            
            # 初始化客户端
            client = cls(api_key=cls._api_key, base_url=cls._base_url, workflow_id=cls._workflow_id)
            
            # 格式化输入数据
            input_data = client.format_input_data(query)
            
            # 构建请求
            url = f"{cls._base_url}/workflows/run"
            payload = {
                "workflow_id": cls._workflow_id,
                "inputs": input_data,
                "response_mode": "streaming",
                "user": "api-user"
            }
            
            headers = {
                "Authorization": f"Bearer {cls._api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"🌐 调用Dify工作流API（流式模式）")
            logger.info(f"   📍 URL: {url}")
            logger.info(f"   🆔 工作流ID: {cls._workflow_id}")
            
            # 发送流式请求，添加重试机制
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    logger.info(f"🔄 尝试第 {retry_count + 1} 次请求...")
                    
                    # 使用更长的超时时间和重试机制
                    response = requests.post(
                        url, 
                        headers=headers, 
                        json=payload, 
                        timeout=(10, 60),  # (连接超时, 读取超时)
                        stream=True,
                        # verify=True  # 确保SSL验证
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Dify工作流API流式调用成功")
                        
                        # 直接转发Dify的SSE数据
                        chunk_count = 0
                        for line in response.iter_lines(decode_unicode=True):
                            if line:
                                chunk_count += 1
                                print(f"[dify_workflow_client] 🔄 第{chunk_count}个数据块: {json.dumps(line, ensure_ascii=True, indent=2)}")
                                # 直接返回Dify的原始数据
                                # print(f"[dify_workflow_client] 📤 Yielding 第{chunk_count}个chunk")
                                yield line
                        
                        print(f"[dify_workflow_client] 🏁 总共处理了{chunk_count}个数据块")
                        break  # 成功，跳出重试循环
                    else:
                        error_msg = f"Dify API错误: {response.status_code} - {response.text}"
                        logger.error(f"❌ {error_msg}")
                        yield json.dumps({'error': error_msg}, ensure_ascii=False)
                        break
                        
                except requests.exceptions.SSLError as ssl_error:
                    retry_count += 1
                    error_msg = f"SSL连接错误 (尝试 {retry_count}/{max_retries}): {str(ssl_error)}"
                    logger.error(f"❌ {error_msg}")
                    
                    if retry_count >= max_retries:
                        yield json.dumps({'error': error_msg}, ensure_ascii=False)
                        break
                    else:
                        logger.info(f"⏳ 等待 2 秒后重试...")
                        time.sleep(2)
                        
                except requests.exceptions.Timeout as timeout_error:
                    retry_count += 1
                    error_msg = f"请求超时 (尝试 {retry_count}/{max_retries}): {str(timeout_error)}"
                    logger.error(f"❌ {error_msg}")
                    
                    if retry_count >= max_retries:
                        yield json.dumps({'error': error_msg}, ensure_ascii=False)
                        break
                    else:
                        logger.info(f"⏳ 等待 2 秒后重试...")
                        time.sleep(2)
                        
                except requests.exceptions.ConnectionError as conn_error:
                    retry_count += 1
                    error_msg = f"连接错误 (尝试 {retry_count}/{max_retries}): {str(conn_error)}"
                    logger.error(f"❌ {error_msg}")
                    
                    if retry_count >= max_retries:
                        yield json.dumps({'error': error_msg}, ensure_ascii=False)
                        break
                    else:
                        logger.info(f"⏳ 等待 2 秒后重试...")
                        time.sleep(2)
                        
                except requests.exceptions.RequestException as req_error:
                    retry_count += 1
                    error_msg = f"请求异常 (尝试 {retry_count}/{max_retries}): {str(req_error)}"
                    logger.error(f"❌ {error_msg}")
                    
                    if retry_count >= max_retries:
                        yield json.dumps({'error': error_msg}, ensure_ascii=False)
                        break
                    else:
                        logger.info(f"⏳ 等待 2 秒后重试...")
                        time.sleep(2)
                
        except Exception as e:
            error_msg = f"流式处理失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            yield json.dumps({'error': error_msg}, ensure_ascii=False) 