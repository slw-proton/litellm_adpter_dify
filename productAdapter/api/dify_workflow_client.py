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
from typing import Dict, Any

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
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai/v1"):
        """
        初始化Dify工作流客户端
        
        Args:
            api_key: Dify API密钥
            base_url: Dify API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"DifyWorkflowClient初始化完成，基础URL: {self.base_url}")
    
    def run_workflow(self, workflow_id: str, input_data: Dict[str, Any], response_mode: str = "blocking") -> Dict[str, Any]:
        """
        运行指定的工作流
        
        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据
            response_mode: 响应模式 (blocking, streaming)
            
        Returns:
            响应结果
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        url = f"{self.base_url}/workflows/run"
        payload = {
            "workflow_id": workflow_id,
            "inputs": input_data,
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
                return result
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
    
    def process_query(self, query: str, workflow_id: str, response_mode: str = "blocking") -> Dict[str, Any]:
        """
        处理查询的便捷方法
        完整的工作流调用流程：运行工作流 -> 获取状态 -> 提取结果
        
        Args:
            query: 用户查询内容
            workflow_id: 工作流ID
            response_mode: 响应模式 (blocking, streaming)
            
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
            # 构建输入数据
            input_data = {"querydata": query}
            logger.info(f"🔍 开始处理Dify工作流查询")
            logger.info(f"📝 查询内容: {query[:100]}{'...' if len(query) > 100 else ''}")
            logger.info(f"🆔 工作流ID: {workflow_id}")
            logger.info(f"📊 响应模式: {response_mode}")
            logger.info(f"📤 输入数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
            
            # 运行工作流
            logger.info(f"🚀 开始调用Dify工作流API...")
            workflow_result = self.run_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                response_mode=response_mode
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
            logger.info(f"📊 工作流执行状态: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
            
            # 从data.outputs中获取内容
            data = status_result.get("data", {})
            outputs = data.get("outputs", {})
            
            logger.info(f"🔍 解析输出数据...")
            logger.info(f"📊 原始data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            logger.info(f"📤 原始outputs: {json.dumps(outputs, ensure_ascii=False, indent=2)}")
            
            # 提取content数据
            if outputs:
                if isinstance(outputs, dict) and "querydata" in outputs:
                    content = outputs["querydata"]
                    logger.info(f"✅ 从outputs.querydata中提取到内容")
                else:
                    content = outputs
                    logger.info(f"✅ 直接使用outputs作为内容")
                
                logger.info(f"📄 提取到的内容: {content[:200]}{'...' if len(str(content)) > 200 else ''}")
            else:
                content = "工作流执行完成，但未返回输出数据。"
                logger.warning(f"⚠️ 工作流执行完成，但未返回输出数据")
            
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
    def process_query_with_config(cls, query: str, api_key: str = None, base_url: str = None, workflow_id: str = None, response_mode: str = "blocking") -> Dict[str, Any]:
        """
        带配置检查的查询处理方法
        包含完整的配置验证和错误处理
        
        Args:
            query: 用户查询内容
            api_key: Dify API密钥（如果为None，将从环境变量获取）
            base_url: Dify API基础URL（如果为None，将从环境变量获取）
            workflow_id: 工作流ID（如果为None，将从环境变量获取）
            response_mode: 响应模式 (blocking, streaming)
            
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
        
        # 从环境变量获取配置（如果未提供）
        api_key = api_key or os.getenv("DIFY_API_KEY", "")
        base_url = base_url or os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
        workflow_id = workflow_id or os.getenv("DIFY_WORKFLOW_ID", "")
        
        logger.info(f"📋 配置信息:")
        logger.info(f"   🔑 API密钥: {'已设置' if api_key else '未设置'}")
        logger.info(f"   🌐 基础URL: {base_url}")
        logger.info(f"   🆔 工作流ID: {workflow_id if workflow_id else '未设置'}")
        logger.info(f"   📊 响应模式: {response_mode}")
        
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
        if not query or not query.strip():
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
        
        logger.info(f"✅ 配置检查通过，开始处理查询...")
        
        try:
            # 初始化客户端并处理查询
            logger.info(f"🔧 初始化DifyWorkflowClient...")
            client = cls(api_key=api_key, base_url=base_url)
            logger.info(f"✅ DifyWorkflowClient初始化完成")
            
            result = client.process_query(
                query=query.strip(),
                workflow_id=workflow_id,
                response_mode=response_mode
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