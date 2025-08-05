#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
环境变量加载模块
用于从.env文件加载环境变量，并提供获取环境变量的工具函数
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# 尝试导入dotenv库
try:
    from dotenv import load_dotenv
except ImportError:
    print("警告: python-dotenv 未安装，无法从.env文件加载环境变量。请使用 'pip install python-dotenv' 安装。")
    load_dotenv = lambda *args, **kwargs: None

# 尝试导入日志配置
try:
    from logging_config import setup_logging
    logger = setup_logging("env_loader", logging.INFO)
except ImportError:
    # 如果找不到logging_config模块，则使用内置的logger模块
    logger = logging.getLogger("env_loader")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# 环境变量默认值
DEFAULTS = {
    # 业务 API 配置
    "BUSINESS_API_URL": "http://localhost:8002/api/process",
    "BUSINESS_API_KEY": "",
    "DEFAULT_MODEL": "default-model",
    
    # LiteLLM 代理服务器配置
    "LITELLM_PROXY_HOST": "0.0.0.0",
    "LITELLM_PROXY_PORT": "8080",
    
    # 日志级别配置
    "LOG_LEVEL": "INFO",
}

def load_env_file(env_file: Optional[str] = None) -> bool:
    """
    加载环境变量文件
    
    Args:
        env_file: 环境变量文件路径，如果为None，则尝试加载默认的.env文件
        
    Returns:
        是否成功加载环境变量文件
    """
    # 如果未指定环境变量文件，则尝试在当前目录和上级目录查找.env文件
    if env_file is None:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.absolute()
        
        # 尝试在当前目录查找.env文件
        env_file = current_dir / ".env"
        if not env_file.exists():
            # 尝试在上级目录查找.env文件
            env_file = current_dir.parent / ".env"
            if not env_file.exists():
                logger.warning("未找到.env文件，将使用默认环境变量值")
                return False
    
    # 加载环境变量文件
    try:
        load_dotenv(env_file)
        logger.info(f"已加载环境变量文件: {env_file}")
        return True
    except Exception as e:
        logger.error(f"加载环境变量文件时出错: {e}")
        return False

def get_env(key: str, default: Optional[str] = None) -> str:
    """
    获取环境变量值
    
    Args:
        key: 环境变量名称
        default: 默认值，如果未指定则使用DEFAULTS中的默认值
        
    Returns:
        环境变量值
    """
    # 如果未指定默认值，则使用DEFAULTS中的默认值
    if default is None and key in DEFAULTS:
        default = DEFAULTS[key]
        
    # 获取环境变量值
    value = os.environ.get(key, default)
    
    return value

def get_env_int(key: str, default: Optional[int] = None) -> int:
    """
    获取整数类型的环境变量值
    
    Args:
        key: 环境变量名称
        default: 默认值，如果未指定则使用DEFAULTS中的默认值
        
    Returns:
        环境变量值（整数类型）
    """
    # 获取环境变量值
    value = get_env(key, str(default) if default is not None else None)
    
    # 转换为整数类型
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"环境变量 {key} 的值 '{value}' 不是有效的整数，将使用默认值 {default}")
        return default if default is not None else 0

def get_env_bool(key: str, default: Optional[bool] = None) -> bool:
    """
    获取布尔类型的环境变量值
    
    Args:
        key: 环境变量名称
        default: 默认值，如果未指定则使用DEFAULTS中的默认值
        
    Returns:
        环境变量值（布尔类型）
    """
    # 获取环境变量值
    value = get_env(key, str(default).lower() if default is not None else None)
    
    # 转换为布尔类型
    if value.lower() in ("true", "yes", "1", "t", "y"):
        return True
    elif value.lower() in ("false", "no", "0", "f", "n"):
        return False
    else:
        logger.warning(f"环境变量 {key} 的值 '{value}' 不是有效的布尔值，将使用默认值 {default}")
        return default if default is not None else False

# 初始化时自动加载环境变量
load_env_file()