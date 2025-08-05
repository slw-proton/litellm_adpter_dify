#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志配置模块
用于配置日志输出格式和目标
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 尝试导入环境变量加载器
try:
    from env_loader import get_env, get_env_int, get_env_bool
except ImportError:
    # 如果找不到环境变量加载器，使用默认的环境变量获取方法
    def get_env(key, default=None):
        return os.environ.get(key, default)
    
    def get_env_int(key, default=None):
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_env_bool(key, default=None):
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 't', 'y')

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# 确保日志目录存在
def ensure_log_dir():
    """
    确保日志目录存在
    """
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            print(f"Error creating log directory: {str(e)}")
            return False
    return True

def setup_logging(name="litellm_adapter", level=None):
    """
    设置日志配置
    
    Args:
        name: 日志记录器名称
        level: 日志级别，如果为None，则从环境变量LOG_LEVEL获取
        
    Returns:
        配置好的日志记录器
    """
    # 如果未指定日志级别，从环境变量获取
    if level is None:
        log_level_str = get_env("LOG_LEVEL", "INFO").upper()
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_mapping.get(log_level_str, logging.INFO)
    
    # 确保日志目录存在
    ensure_log_dir()
    
    # 创建日志文件名（包含日期）
    current_date = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"{name}_{current_date}.log")
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 创建文件处理器（滚动日志文件，最大10MB，最多保留5个备份）
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # 添加文件处理器到日志记录器
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # 添加控制台处理器到日志记录器
    logger.addHandler(console_handler)
    
    # 记录环境变量信息
    logger.debug(f"Environment variables: LOG_LEVEL={get_env('LOG_LEVEL', 'Not set')}")
    return logger
    
