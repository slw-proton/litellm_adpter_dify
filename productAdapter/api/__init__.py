# -*- coding: utf-8 -*-

"""
productAdapter API模块
包含业务API和Dify工作流客户端
"""

try:
    from .dify_workflow_client import DifyWorkflowClient
    __all__ = ['DifyWorkflowClient']
except ImportError:
    # 如果导入失败，不暴露DifyWorkflowClient
    __all__ = []
