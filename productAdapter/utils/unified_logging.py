#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一日志配置：所有模块输出到同一个按日期滚动的文件，并输出到控制台。
文件路径：logs/YYYY/MM/DD/app.log
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

_CONFIGURED = False


def _ensure_date_dir(project_root: str) -> str:
    logs_dir = os.path.join(project_root, "logs")
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    day = datetime.now().strftime("%d")
    date_dir = os.path.join(logs_dir, year, month, day)
    os.makedirs(date_dir, exist_ok=True)
    return date_dir


def setup_unified_logging(
    project_root: str,
    level: Optional[str] = None,
    filename: str = "app.log",
) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    # 级别
    level_str = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level_str, logging.INFO)

    # 目标文件
    date_dir = _ensure_date_dir(project_root)
    target_file = os.path.join(date_dir, filename)

    root = logging.getLogger()
    root.setLevel(log_level)
    # 清空旧处理器，避免重复
    root.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 文件处理器
    file_handler = RotatingFileHandler(target_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 控制台处理器
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # 关键logger统一到root
    for name in [
        "business_api",
        "productAdapter",
        "dify_workflow_client",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "httpx",
    ]:
        lg = logging.getLogger(name)
        lg.setLevel(log_level)
        lg.propagate = True
        # 不额外添加handler，全部透传到root
        lg.handlers.clear()

    logging.getLogger("unified_logging").info(
        f"Unified logging configured. File: {target_file}, Level: {level_str}"
    )

    _CONFIGURED = True


