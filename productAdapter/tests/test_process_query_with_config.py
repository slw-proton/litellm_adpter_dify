#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试DifyWorkflowClient的process_query_with_config方法
"""

import os
import sys
import json

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_process_query_with_config_method():
    """测试process_query_with_config方法"""
    print("=== 测试process_query_with_config方法 ===")
    
    try:
        from productAdapter.api.dify_workflow_client import DifyWorkflowClient
    except ImportError:
        print("❌ 无法导入DifyWorkflowClient")
        return False
    
    # 测试方法存在
    if hasattr(DifyWorkflowClient, 'process_query_with_config'):
        print("✅ process_query_with_config方法存在")
    else:
        print("❌ process_query_with_config方法不存在")
        return False
    
    # 测试方法签名
    import inspect
    sig = inspect.signature(DifyWorkflowClient.process_query_with_config)
    params = list(sig.parameters.keys())
    expected_params = ['query', 'api_key', 'base_url', 'workflow_id']
    
    for param in expected_params:
        if param in params:
            print(f"✅ 参数 {param} 存在")
        else:
            print(f"❌ 参数 {param} 不存在")
            return False
    
    print("✅ process_query_with_config方法签名正确")
    return True

def test_process_query_with_config_functionality():
    """测试process_query_with_config功能"""
    print("\n=== 测试process_query_with_config功能 ===")
    
    try:
        from productAdapter.api.dify_workflow_client import DifyWorkflowClient
    except ImportError:
        print("❌ 无法导入DifyWorkflowClient")
        return False
    
    # 测试1: 空查询
    print("测试1: 空查询")
    result = DifyWorkflowClient.process_query_with_config("")
    if not result["success"] and "请提供有效的查询内容" in result["content"]:
        print("✅ 空查询处理正确")
    else:
        print("❌ 空查询处理错误")
        return False
    
    # 测试2: 配置不完整
    print("测试2: 配置不完整")
    # 临时清除环境变量
    original_api_key = os.environ.get("DIFY_API_KEY")
    original_workflow_id = os.environ.get("DIFY_WORKFLOW_ID")
    
    if "DIFY_API_KEY" in os.environ:
        del os.environ["DIFY_API_KEY"]
    if "DIFY_WORKFLOW_ID" in os.environ:
        del os.environ["DIFY_WORKFLOW_ID"]

    # 重置类级缓存，确保重新从环境变量加载
    try:
        from productAdapter.api.dify_workflow_client import DifyWorkflowClient as _ClientForReset
        _ClientForReset._api_key = None
        _ClientForReset._base_url = None
        _ClientForReset._workflow_id = None
    except Exception:
        pass
    
    result = DifyWorkflowClient.process_query_with_config("测试查询")
    if not result["success"] and "Dify配置不完整" in result["content"]:
        print("✅ 配置不完整处理正确")
    else:
        print("❌ 配置不完整处理错误")
        return False
    
    # 恢复环境变量
    if original_api_key:
        os.environ["DIFY_API_KEY"] = original_api_key
    if original_workflow_id:
        os.environ["DIFY_WORKFLOW_ID"] = original_workflow_id
    
    print("✅ process_query_with_config功能测试通过")
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试process_query_with_config方法")
    print("=" * 50)
    
    # 测试方法存在性
    method_exists = test_process_query_with_config_method()
    
    if method_exists:
        # 测试功能
        functionality_correct = test_process_query_with_config_functionality()
        
        if functionality_correct:
            print("\n🎉 process_query_with_config方法测试通过！")
            print("\n方法特性:")
            print("- ✅ 自动配置检查")
            print("- ✅ 环境变量支持")
            print("- ✅ 查询内容验证")
            print("- ✅ 完整的错误处理")
            print("- ✅ 统一的返回格式")
            return True
        else:
            print("\n❌ 功能测试失败")
            return False
    else:
        print("\n❌ 方法存在性测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

