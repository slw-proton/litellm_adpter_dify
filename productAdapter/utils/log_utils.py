#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块
提供日志路径管理和目录创建功能
"""

import os
from datetime import datetime

def create_date_based_log_path(base_dir, filename):
    """
    创建基于日期的日志文件路径（年/月/日结构）
    
    Args:
        base_dir: 基础日志目录
        filename: 日志文件名（不包含路径）
        
    Returns:
        tuple: (full_path, relative_path)
    """
    # 获取当前日期
    now = datetime.now()
    year = str(now.year)
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"
    
    # 创建年/月/日目录结构
    date_dir = os.path.join(base_dir, year, month, day)
    
    # 确保目录存在
    try:
        os.makedirs(date_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating log directory {date_dir}: {str(e)}")
        # 如果创建失败，回退到基础目录
        date_dir = base_dir
    
    # 构建完整路径
    full_path = os.path.join(date_dir, filename)
    relative_path = os.path.join(year, month, day, filename)
    
    return full_path, relative_path

def get_log_path_for_service(base_dir, service_name, include_timestamp=True):
    """
    为服务获取日志文件路径
    
    Args:
        base_dir: 基础日志目录
        service_name: 服务名称（如 'business_api', 'litellm'）
        include_timestamp: 是否在文件名中包含时间戳
        
    Returns:
        tuple: (full_path, relative_path)
    """
    if include_timestamp:
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{service_name}_{timestamp}.log"
    else:
        filename = f"{service_name}.log"
    
    return create_date_based_log_path(base_dir, filename) 