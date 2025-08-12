#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DifyWorkflowClient模块测试脚本
"""

import os
import sys
import json

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_dify_client_import():
    """测试DifyWorkflowClient模块导入"""
    print("=== 测试DifyWorkflowClient模块导入 ===")
    
    try:
        from dify_workflow_client import DifyWorkflowClient
        print("✅ 相对导入成功")
        return True
    except ImportError as e:
        print(f"❌ 相对导入失败: {e}")
        
        try:
            from productAdapter.api.dify_workflow_client import DifyWorkflowClient
            print("✅ 绝对导入成功")
            return True
        except ImportError as e:
            print(f"❌ 绝对导入失败: {e}")
            return False

def test_dify_client_initialization():
    """测试DifyWorkflowClient初始化"""
    print("\n=== 测试DifyWorkflowClient初始化 ===")
    
    try:
        from dify_workflow_client import DifyWorkflowClient
    except ImportError:
        try:
            from productAdapter.api.dify_workflow_client import DifyWorkflowClient
        except ImportError:
            print("❌ 无法导入DifyWorkflowClient")
            return False
    
    # 测试初始化
    try:
        client = DifyWorkflowClient(api_key="test_key", base_url="https://api.dify.ai/v1")
        print("✅ DifyWorkflowClient初始化成功")
        print(f"   基础URL: {client.base_url}")
        print(f"   API密钥: {client.api_key[:8]}...")
        return True
    except Exception as e:
        print(f"❌ DifyWorkflowClient初始化失败: {e}")
        return False

def test_dify_client_methods():
    """测试DifyWorkflowClient方法"""
    print("\n=== 测试DifyWorkflowClient方法 ===")
    
    try:
        from dify_workflow_client import DifyWorkflowClient
    except ImportError:
        try:
            from productAdapter.api.dify_workflow_client import DifyWorkflowClient
        except ImportError:
            print("❌ 无法导入DifyWorkflowClient")
            return False
    
    # 测试方法存在性
    client = DifyWorkflowClient(api_key="test_key")
    
    methods = [
        'run_workflow',
        'get_workflow_status', 
        'stop_workflow_execution',
        'health_check',
        'process_query',
        'process_query_with_config'
    ]
    
    for method in methods:
        if hasattr(client, method):
            print(f"✅ 方法 {method} 存在")
        else:
            print(f"❌ 方法 {method} 不存在")
            return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试DifyWorkflowClient模块")
    print("=" * 50)
    
    # 测试导入
    import_success = test_dify_client_import()
    
    if import_success:
        # 测试初始化
        init_success = test_dify_client_initialization()
        
        if init_success:
            # 测试方法
            methods_success = test_dify_client_methods()
            
            if methods_success:
                print("\n🎉 所有测试通过！DifyWorkflowClient模块工作正常")
                return True
            else:
                print("\n❌ 方法测试失败")
                return False
        else:
            print("\n❌ 初始化测试失败")
            return False
    else:
        print("\n❌ 导入测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

