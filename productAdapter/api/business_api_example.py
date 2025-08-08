#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
业务API示例实现
用于测试LiteLLM适配器
"""

import os
import sys
import json
import time
import uuid
import argparse
import logging
from typing import Dict, Any, Optional, AsyncGenerator

# FastAPI相关导入
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目内部模块 - 使用绝对导入
from productAdapter.utils.logging_init import (
    init_logger_with_env_loader, 
    load_env_file_if_exists,
    log_environment_info
)
from productAdapter.utils.env_loader import get_env, get_env_int, load_env_file
from productAdapter.api.dify_workflow_client import DifyWorkflowClient

# 初始化日志记录器
logger = init_logger_with_env_loader("business_api", project_root)

# 定义请求模型
class ModelInfo(BaseModel):
    name: str = Field(..., description="模型名称")

class BusinessRequest(BaseModel):
    query: Any = Field(..., description="用户查询或消息数组")  # 改为Any类型以接受messages数组
    response_type: str = Field("text", description="响应类型，text或json")
    stream: bool = Field(False, description="是否使用流式响应")
    model_info: ModelInfo = Field(..., description="模型信息")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    response_format: Optional[Dict[str, Any]] = Field(None, description="响应格式配置，用于structured output")

# 定义响应模型
class BusinessResponse(BaseModel):
    response_id: str = Field(..., description="响应ID")
    content: Any = Field(..., description="响应内容")
    timestamp: int = Field(..., description="时间戳")
    processing_time: float = Field(..., description="处理时间")

# 创建FastAPI应用
app = FastAPI(title="业务API示例", description="用于测试LiteLLM适配器的业务API示例")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_dify_response(query: Any, response_id: str, start_time: float) -> AsyncGenerator[str, None]:
    """
    流式处理Dify响应
    
    Args:
        query: 查询内容
        response_id: 响应ID
        start_time: 开始时间
        
    Yields:
        SSE格式的数据块
    """
    try:
        logger.info(f"🔄 开始流式处理Dify工作流查询")
        
        import sys, asyncio
        # 使用DifyWorkflowClient的流式响应方法
        chunk_count = 0
        async for line in DifyWorkflowClient.stream_dify_response(query, response_id, start_time):
            try:
                chunk_count += 1
                print(f"[business_api] 🔄 第{chunk_count}个数据块: {line[:100]}...")
                
                # 确保line是字符串格式
                if isinstance(line, str):
                    print(f"[business_api] 📤 Yielding 第{chunk_count}个chunk")
                    yield line
                else:
                    # 如果不是字符串，转换为字符串
                    print(f"[business_api] 📤 Yielding 第{chunk_count}个chunk(转换后)")
                    yield str(line)
                await asyncio.sleep(0)
                sys.stdout.flush()
            except Exception as line_error:
                logger.error(f"❌ 处理流式数据行时出错: {str(line_error)}")
                error_msg = f"数据处理错误: {str(line_error)}"
                yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                break
        
        print(f"[business_api] 🏁 总共处理了{chunk_count}个数据块")
                
    except Exception as e:
        error_msg = f"流式处理失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"🔍 异常详情: {type(e).__name__}: {str(e)}")
        yield json.dumps({'error': error_msg}, ensure_ascii=False)

@app.post("/api/process")
async def process(request: BusinessRequest):
    """
    处理业务请求 - 使用Dify工作流API
    支持普通模式和SSE流式模式
    """
    # 记录开始时间
    start_time = time.time()
    
    # 生成响应ID
    response_id = f"resp-{uuid.uuid4().hex[:10]}"
    print(f"requestparams: {json.dumps(request.model_dump(), ensure_ascii=False, indent=2)}")
    
    # 根据stream参数动态设置response_mode
    response_mode = "streaming" if request.stream else "blocking"
    logger.info(f"📊 响应模式: {response_mode} (stream={request.stream})")
    
    # 如果是流式模式，返回SSE响应
    if request.stream:
        logger.info(f"🔄 使用SSE流式模式")
        response = StreamingResponse(
            stream_dify_response(request.query, response_id, start_time),
            media_type="text/event-stream"
        )
        response.headers["X-Accel-Buffering"] = "no"
        response.headers["Cache-Control"] = "no-cache"
        return response
    
    # 普通模式处理
    logger.info(f"📝 使用普通阻塞模式")
    
    # 使用Dify工作流处理查询 - 直接传递request.query
    result = DifyWorkflowClient.process_query_with_config(
        query=request.query
    )
    
    if result["success"]:
        content = result["content"]
        logger.info(f"从Dify工作流获取到内容: {content}")
    else:
        # 当Dify工作流失败时，返回一个默认的响应而不是空内容
        error_msg = result.get("error", "未知错误")
        content = f"抱歉，Dify工作流执行失败: {error_msg}"
        logger.error(f"Dify工作流执行失败: {error_msg}")
    
    # 确保content不为空
    if not content or content.strip() == "":
        content = "抱歉，服务暂时不可用，请稍后重试。"
        logger.warning("Dify工作流返回空内容，使用默认响应")
    
    # 如果响应类型为json，转换为json格式
    if request.response_type == "json":
        if isinstance(content, dict):
            # 如果content已经是字典，直接使用
            pass
        else:
            # 否则包装成标准格式
            content = {"message": content, "type": "dify_workflow_response"}
    
    # 计算处理时间
    processing_time = time.time() - start_time
    
    # 构建响应
    response = BusinessResponse(
        response_id=response_id,
        content=content,
        timestamp=int(time.time()),
        processing_time=processing_time
    )
    
    return response.dict()

@app.get("/models")
async def list_models():
    """
    获取可用模型列表
    兼容OpenAI API格式
    """
    models_data = {
        "object": "list",
        "data": [
            {
                "id": "my-custom-model",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "business-api",
                "permission": [],
                "root": "my-custom-model",
                "parent": None
            },
            {
                "id": "business-presentation-model",
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "business-api",
                "permission": [],
                "root": "business-presentation-model",
                "parent": None
            }
        ]
    }
    logger.info(f"models_data: {json.dumps(models_data, ensure_ascii=False, indent=2)}")
    return models_data

@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "ok", "service": "business-api", "timestamp": int(time.time())}

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    # 从环境变量获取默认值
    default_host = get_env("BUSINESS_API_HOST", "0.0.0.0")
    default_port = get_env_int("BUSINESS_API_PORT", 8002)
    
    parser = argparse.ArgumentParser(description="Start Business API server")
    parser.add_argument("--host", type=str, default=default_host, 
                        help=f"Host to bind the server to (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, 
                        help=f"Port to bind the server to (default: {default_port})")
    parser.add_argument("--env-file", type=str, 
                        help="Path to .env file for loading environment variables")
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 自动加载环境变量文件（如果存在）
    # 首先尝试从productAdapter/config/.env加载
    config_env_file = os.path.join(project_root, "productAdapter", "config", ".env")
    if os.path.exists(config_env_file):
        success = load_env_file_if_exists(config_env_file, load_env_file, logger)
        if success:
            logger.info(f"已加载环境变量文件: {config_env_file}")
        else:
            logger.warning(f"环境变量文件存在但无法加载: {config_env_file}")
    
    # 如果指定了环境变量文件，也加载它（会覆盖之前的配置）
    if args.env_file:
        success = load_env_file_if_exists(args.env_file, load_env_file, logger)
        if not success and os.path.exists(args.env_file):
            logger.warning(f"Environment file exists but could not be loaded: {args.env_file}")
    
    # 记录环境变量信息
    env_vars = {
        'BUSINESS_API_HOST': 'BUSINESS_API_HOST',
        'BUSINESS_API_PORT': 'BUSINESS_API_PORT', 
        'LOG_LEVEL': 'LOG_LEVEL',
        'DIFY_API_KEY': 'DIFY_API_KEY',
        'DIFY_BASE_URL': 'DIFY_BASE_URL',
        'DIFY_WORKFLOW_ID': 'DIFY_WORKFLOW_ID'
    }
    
    log_environment_info(logger, env_vars, get_env)
    
    # 启动服务器
    logger.info(f"Starting Business API server at http://{args.host}:{args.port}")
    print(f"Starting Business API server at http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()