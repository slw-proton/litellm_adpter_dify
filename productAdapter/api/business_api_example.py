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
from typing import Dict, Any, Optional, Union, List

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 定义基础环境变量函数（fallback）
def get_env_fallback(key, default=None):
    return os.environ.get(key, default)

def get_env_int_fallback(key, default=None):
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def get_env_bool_fallback(key, default=None):
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', 'yes', '1', 't', 'y')

# 导入日志初始化模块
try:
    from ..utils.logging_init import (
        init_logger_with_env_loader, 
        load_env_file_if_exists,
        log_environment_info
    )
    # 初始化日志记录器
    logger = init_logger_with_env_loader("business_api", project_root)
    
    # 尝试导入环境变量加载器
    try:
        from ..utils.env_loader import get_env, get_env_int, get_env_bool, load_env_file
        env_loader_available = True
    except ImportError:
        print("env_loader module not found, using fallback functions")
        get_env = get_env_fallback
        get_env_int = get_env_int_fallback  
        get_env_bool = get_env_bool_fallback
        load_env_file = None
        env_loader_available = False
        
except ImportError:
    print("logging_init module not found, using basic logging setup")
    # 基础日志设置fallback
    logger = logging.getLogger("business_api")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 使用基础环境变量函数
    get_env = get_env_fallback
    get_env_int = get_env_int_fallback
    get_env_bool = get_env_bool_fallback
    load_env_file = None
    env_loader_available = False

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("Error: FastAPI or Uvicorn not installed. Please install them with 'pip install fastapi uvicorn'.")
    sys.exit(1)

# 定义请求模型
class ModelInfo(BaseModel):
    name: str = Field(..., description="模型名称")

class BusinessRequest(BaseModel):
    query: str = Field(..., description="用户查询")
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

def generate_presentation_response(query: str) -> str:
    """
    生成演示文稿的结构化响应
    基于query中的内容生成符合schema的JSON响应
    """
    return "{\"title\": \"333          English...\", \"slides\": [{\"title\": \"项目概述\", \"body\": \"介绍项目的核心理念、目标和价值主张\", \"description\": \"这是关于项目概述的详细介绍，介绍项目的核心理念、目标和价值主张\"}, {\"title\": \"市场分析\", \"body\": \"分析目标市场规模、竞争环境和机会\", \"description\": \"这是关于市场分析的详细介绍，分析目标市场规模、竞争环境和机会\"}, {\"title\": \"产品特性\", \"body\": \"详细介绍产品功能、优势和差异化特点\", \"description\": \"这是关于产品特性的详细介绍，详细介绍产品功能、优势和差异化特点\"}, {\"title\": \"商业模式\", \"body\": \"阐述盈利模式、收入来源和成本结构\", \"description\": \"这是关于商业模式的详细介绍，阐述盈利模式、收入来源和成本结构\"}, {\"title\": \"团队介绍\", \"body\": \"展示核心团队成员的背景和专业能力\", \"description\": \"这是关于团队介绍的详细介绍，展示核心团队成员的背景和专业能力\"}], \"notes\": [\"这是一个关于333          English          8          None的5页演示文稿，涵盖了主要内容要点。\"]}"

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

@app.post("/api/process")
async def process(request: BusinessRequest):
    """
    处理业务请求
    """
    # 记录开始时间
    start_time = time.time()
    
    # 生成响应ID
    response_id = f"resp-{uuid.uuid4().hex[:10]}"
    print(f"requestparams: {json.dumps(request.model_dump(), ensure_ascii=False, indent=2)}")
    
    # 检查是否有response_format配置
    if request.response_format:
        print(f"📋 收到response_format配置: {json.dumps(request.response_format, ensure_ascii=False, indent=2)}")
    
    # 根据请求生成响应内容
    if request.query.strip():
        content = generate_presentation_response(request.query)
    else:
        content = "请提供有效的查询内容。"
    
    # 如果响应类型为json，转换为json格式
    if request.response_type == "json":
        if isinstance(content, dict):
            # 如果content已经是字典，直接使用
            pass
        else:
            # 否则包装成标准格式
            content = {"message": content, "type": "business_api_response"}
    
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
    
    # 如果指定了环境变量文件，加载它
    if args.env_file:
        if env_loader_available and load_env_file:
            success = load_env_file_if_exists(args.env_file, load_env_file, logger)
            if not success and os.path.exists(args.env_file):
                logger.warning(f"Environment file exists but could not be loaded: {args.env_file}")
        else:
            if os.path.exists(args.env_file):
                logger.warning(f"Environment file exists but no loader available: {args.env_file}")
    
    # 记录环境变量信息
    env_vars = {
        'BUSINESS_API_HOST': 'BUSINESS_API_HOST',
        'BUSINESS_API_PORT': 'BUSINESS_API_PORT', 
        'LOG_LEVEL': 'LOG_LEVEL'
    }
    
    try:
        log_environment_info(logger, env_vars, get_env)
    except NameError:
        # 如果log_environment_info不可用，使用基础方式
        logger.info(f"Environment variables: BUSINESS_API_HOST={get_env('BUSINESS_API_HOST', 'Not set')}, "
                   f"BUSINESS_API_PORT={get_env('BUSINESS_API_PORT', 'Not set')}, "
                   f"LOG_LEVEL={get_env('LOG_LEVEL', 'Not set')}")
    
    # 启动服务器
    logger.info(f"Starting Business API server at http://{args.host}:{args.port}")
    print(f"Starting Business API server at http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()