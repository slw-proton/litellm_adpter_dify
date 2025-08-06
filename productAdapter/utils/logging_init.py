#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志初始化模块
提供通用的日志初始化功能，支持环境变量配置和fallback机制
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

def get_env_fallback(key: str, default: Any = None) -> Any:
    """
    获取环境变量的fallback函数
    
    Args:
        key: 环境变量键名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(key, default)

def get_env_int_fallback(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    获取整数类型环境变量的fallback函数
    
    Args:
        key: 环境变量键名
        default: 默认值
        
    Returns:
        环境变量整数值或默认值
    """
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def get_env_bool_fallback(key: str, default: Optional[bool] = None) -> Optional[bool]:
    """
    获取布尔类型环境变量的fallback函数
    
    Args:
        key: 环境变量键名
        default: 默认值
        
    Returns:
        环境变量布尔值或默认值
    """
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', 'yes', '1', 't', 'y')

def setup_basic_logger(
    name: str, 
    log_level: Optional[str] = None,
    get_env_func: Optional[callable] = None
) -> logging.Logger:
    """
    设置基础日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别字符串，如果为None则从环境变量获取
        get_env_func: 获取环境变量的函数，如果为None则使用fallback函数
        
    Returns:
        配置好的日志记录器
    """
    # 使用提供的环境变量获取函数或fallback函数
    if get_env_func is None:
        get_env_func = get_env_fallback
    
    # 设置日志级别
    if log_level is None:
        log_level = get_env_func("LOG_LEVEL", "INFO")
    
    log_level_str = log_level.upper()
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level_mapping.get(log_level_str, logging.INFO)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有处理器（避免重复）
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger

def init_logger_with_env_loader(
    name: str,
    project_root: Optional[str] = None
) -> logging.Logger:
    """
    使用环境变量加载器初始化日志记录器
    
    Args:
        name: 日志记录器名称
        project_root: 项目根目录路径
        
    Returns:
        配置好的日志记录器
    """
    # 尝试导入环境变量加载器和日志配置
    try:
        # 如果提供了项目根目录，添加到sys.path
        if project_root and project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # 尝试导入高级日志配置
        try:
            from productAdapter.utils.logging_config import setup_logging
            return setup_logging(name)
        except ImportError:
            # 如果导入失败，尝试导入环境变量加载器
            try:
                from productAdapter.utils.env_loader import get_env
                return setup_basic_logger(name, get_env_func=get_env)
            except ImportError:
                # 如果都失败了，使用基础配置
                return setup_basic_logger(name)
        
    except ImportError:
        # 如果导入失败，尝试导入环境变量加载器
        try:
            from productAdapter.utils.env_loader import get_env
            return setup_basic_logger(name, get_env_func=get_env)
        except ImportError:
            # 如果都失败了，使用基础配置
            return setup_basic_logger(name)

def load_env_file_if_exists(
    env_file_path: str,
    load_env_file_func: Optional[callable] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    如果环境文件存在则加载它
    
    Args:
        env_file_path: 环境文件路径
        load_env_file_func: 加载环境文件的函数
        logger: 日志记录器
        
    Returns:
        是否成功加载
    """
    if not os.path.exists(env_file_path):
        return False
    
    try:
        if load_env_file_func:
            load_env_file_func(env_file_path)
            if logger:
                logger.info(f"Loaded environment variables from {env_file_path}")
            return True
        else:
            if logger:
                logger.warning(f"Environment file exists but no loader function provided: {env_file_path}")
            return False
    except Exception as e:
        if logger:
            logger.error(f"Error loading environment variables from {env_file_path}: {str(e)}")
        return False

def log_environment_info(
    logger: logging.Logger,
    env_vars: Dict[str, str],
    get_env_func: Optional[callable] = None
) -> None:
    """
    记录环境变量信息
    
    Args:
        logger: 日志记录器
        env_vars: 要记录的环境变量字典 {变量名: 描述}
        get_env_func: 获取环境变量的函数
    """
    if get_env_func is None:
        get_env_func = get_env_fallback
    
    env_info = []
    for var_name, description in env_vars.items():
        value = get_env_func(var_name, 'Not set')
        env_info.append(f"{description}={value}")
    
    logger.info(f"Environment variables: {', '.join(env_info)}") 