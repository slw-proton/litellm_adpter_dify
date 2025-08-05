#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ProductAdapter - LiteLLM自定义适配器包

扁平化目录结构版本，便于管理和维护。

主要组件:
- handlers: 自定义LLM处理器
- adapters: 请求/响应适配器
- utils: 工具类和配置
- api: 业务API实现
- config: 配置文件
- tests: 测试文件
- docs: 文档
"""

__version__ = "2.0.0"
__author__ = "ProductAdapter Team"

# 便捷导入
try:
    from .utils.env_loader import get_env, load_env_file
    from .utils.logging_config import setup_logging
    from .utils.logging_init import (
        init_logger_with_env_loader,
        setup_basic_logger,
        load_env_file_if_exists,
        log_environment_info
    )

    __all__ = [
        'get_env',
        'load_env_file',
        'setup_logging',
        'init_logger_with_env_loader',
        'setup_basic_logger',
        'load_env_file_if_exists',
        'log_environment_info'
    ]
except ImportError as e:
    # 在某些情况下（如文档生成），依赖可能不可用
    __all__ = [] 