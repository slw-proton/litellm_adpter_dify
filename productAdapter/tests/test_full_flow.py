#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
完整流程测试脚本
测试从业务API到LiteLLM代理再到OpenAI客户端的完整流程
"""

import os
import sys
import json
import time
import subprocess
import signal
import argparse
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def start_business_api(host="0.0.0.0", port=8001):
    """
    启动业务API服务器
    
    Args:
        host: 主机地址
        port: 端口
        
    Returns:
        进程对象
    """
    print(f"\n启动业务API服务器 (http://{host}:{port})...")
    
    # 构建命令
    cmd = [
        sys.executable,
        "-m",
        "liteLLMAdapter.business_api_example",
        "--host", host,
        "--port", str(port)
    ]
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务器启动
    time.sleep(2)
    
    return process

def start_litellm_proxy(host="0.0.0.0", port=8080, api_base="http://localhost:8001/api/process"):
    """
    启动LiteLLM代理服务器
    
    Args:
        host: 主机地址
        port: 端口
        api_base: 业务API基础URL
        
    Returns:
        进程对象
    """
    print(f"\n启动LiteLLM代理服务器 (http://{host}:{port})...")
    
    # 构建命令
    cmd = [
        sys.executable,
        "-m",
        "liteLLMAdapter.start_proxy",
        "--host", host,
        "--port", str(port),
        "--api-base", api_base
    ]
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待服务器启动
    time.sleep(2)
    
    return process

def test_with_openai_client(base_url="http://localhost:8080/v1"):
    """
    使用OpenAI客户端测试
    
    Args:
        base_url: LiteLLM代理的基础URL
    """
    print(f"\n使用OpenAI客户端测试 (base_url: {base_url})...")
    
    try:
        from openai import OpenAI
        
        # 创建OpenAI客户端
        client = OpenAI(
            api_key="dummy-key",
            base_url=base_url
        )
        
        # 发送请求
        print("\n发送请求...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": "请用一句话介绍人工智能。"}
            ]
        )
        
        # 打印响应
        print("\n收到响应:")
        print(response)
        
        return True
    
    except ImportError:
        print("Error: OpenAI Python client not installed. Please install it with 'pip install openai'.")
        return False
    except Exception as e:
        print(f"Error using OpenAI client: {str(e)}")
        return False

def test_direct_adapter(api_base_url="http://localhost:8001/api/process"):
    """
    直接使用适配器测试
    
    Args:
        api_base_url: 业务API的基础URL
    """
    print(f"\n直接使用适配器测试 (api_base_url: {api_base_url})...")
    
    try:
        from liteLLMAdapter.adapter import LiteLLMAdapter
        
        # 创建适配器
        adapter = LiteLLMAdapter(api_base_url)
        
        # 构建OpenAI格式的请求
        openai_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": "你好，请介绍一下自己。"}
            ]
        }
        
        # 处理请求
        print("\n发送请求...")
        response = adapter.handle_chat_completion(openai_request)
        
        # 打印响应
        print("\n收到响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
        return True
    
    except Exception as e:
        print(f"Error using adapter directly: {str(e)}")
        return False

def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description="Test full flow from Business API to LiteLLM Proxy to OpenAI client")
    parser.add_argument("--business-host", type=str, default="0.0.0.0", help="Business API host")
    parser.add_argument("--business-port", type=int, default=8001, help="Business API port")
    parser.add_argument("--proxy-host", type=str, default="0.0.0.0", help="LiteLLM Proxy host")
    parser.add_argument("--proxy-port", type=int, default=8080, help="LiteLLM Proxy port")
    parser.add_argument("--skip-server", action="store_true", help="Skip starting servers")
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 进程列表
    processes = []
    
    try:
        # 启动服务器
        if not args.skip_server:
            # 启动业务API服务器
            business_api_process = start_business_api(args.business_host, args.business_port)
            processes.append(business_api_process)
            
            # 启动LiteLLM代理服务器
            api_base = f"http://localhost:{args.business_port}/api/process"
            litellm_proxy_process = start_litellm_proxy(args.proxy_host, args.proxy_port, api_base)
            processes.append(litellm_proxy_process)
        
        # 等待服务器完全启动
        time.sleep(3)
        
        # 测试直接使用适配器
        api_base_url = f"http://localhost:{args.business_port}/api/process"
        test_direct_adapter(api_base_url)
        
        # 测试使用OpenAI客户端
        base_url = f"http://localhost:{args.proxy_port}/v1"
        test_with_openai_client(base_url)
    
    finally:
        # 关闭进程
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

if __name__ == "__main__":
    main()