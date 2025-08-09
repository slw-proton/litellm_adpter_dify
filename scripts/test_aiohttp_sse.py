#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立的 aiohttp SSE 测试程序
直接测试业务API的流式响应
"""

import asyncio
import aiohttp
import json
import time

async def test_aiohttp_sse_streaming():
    """
    使用 aiohttp 测试业务API的SSE流式响应
    """
    
    # 业务API请求数据
    business_request = {
        "query": [
            {
                "role": "user",
                "content": "请简单介绍一下LiteLLM"
            },
            {
                "role": "response_format",
                "content": None
            }
        ],
        "model_info": {
            "name": "my-model"
        },
        "response_type": "text",
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print("=== 开始 aiohttp SSE 流式测试 ===")
    print(f"请求数据: {json.dumps(business_request, ensure_ascii=False, indent=2)}")
    print()
    
    start_time = time.time()
    chunk_count = 0
    total_content = ""
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📡 发送请求到业务API...")
            async with session.post(
                "http://localhost:8002/api/process",
                json=business_request,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                print(f"📊 响应状态: {response.status}")
                print(f"📋 响应头: {dict(response.headers)}")
                print()
                
                if response.status == 200:
                    print("🔄 开始接收流式数据...")
                    print("-" * 80)
                    
                    # 方法1: 使用 iter_chunked(1) 逐字节读取
                    buffer = ""
                    async for chunk in response.content.iter_chunked(1):
                        if chunk:
                            # 解码字节为字符串
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            buffer += chunk_str
                            
                            # 只要有换行就处理
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                if line:
                                    chunk_count += 1
                                    elapsed = time.time() - start_time
                                    print(f"[{elapsed:.3f}s] 📦 第{chunk_count}个数据块: {line[:100]}...")
                                    total_content += line + "\n"
                    
                    # 处理剩余的buffer
                    if buffer.strip():
                        chunk_count += 1
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.3f}s] 📦 第{chunk_count}个数据块(剩余): {buffer.strip()[:100]}...")
                        total_content += buffer.strip() + "\n"
                    
                    print("-" * 80)
                    print(f"✅ 流式接收完成，总共收到 {chunk_count} 个数据块")
                    print(f"⏱️  总耗时: {time.time() - start_time:.3f}s")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 业务API返回错误: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return
    
    print()
    print("=== 完整响应内容 ===")
    print(total_content[:1000] + ("..." if len(total_content) > 1000 else ""))
    print()

async def test_aiohttp_sse_streaming_method2():
    """
    使用 aiohttp 测试业务API的SSE流式响应 - 方法2: 使用更大的chunk size
    """
    
    # 业务API请求数据
    business_request = {
        "query": [
            {
                "role": "user",
                "content": "请简单介绍一下LiteLLM"
            },
            {
                "role": "response_format",
                "content": None
            }
        ],
        "model_info": {
            "name": "my-model"
        },
        "response_type": "text",
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print("=== 开始 aiohttp SSE 流式测试 (方法2: chunk=1024) ===")
    
    start_time = time.time()
    chunk_count = 0
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8002/api/process",
                json=business_request,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status == 200:
                    print("🔄 开始接收流式数据 (chunk=1024)...")
                    print("-" * 80)
                    
                    # 方法2: 使用 iter_chunked(1024) 读取
                    buffer = ""
                    async for chunk in response.content.iter_chunked(1024):
                        if chunk:
                            chunk_count += 1
                            elapsed = time.time() - start_time
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            # print(f"[{elapsed:.3f}s] 📦 第{chunk_count}个网络块 (大小: {len(chunk)}字节): {chunk_str[:100]}...")
                            print(f"第{chunk_count}个网络块{json.dumps(chunk_str, ensure_ascii=True, indent=2)}")
                            
                            buffer += chunk_str
                            # 按行分割
                            lines = buffer.split('\n')
                            buffer = lines[-1]  # 保留最后一个不完整的行
                            
                            for line in lines[:-1]:  # 处理完整的行
                                line = line.strip()
                                if line:
                                    print(f"    → SSE行: {line[:100]}...")
                    
                    print("-" * 80)
                    print(f"✅ 流式接收完成，总共收到 {chunk_count} 个网络块")
                    print(f"⏱️  总耗时: {time.time() - start_time:.3f}s")
                    
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

async def main():
    """
    主函数
    """
    print("🚀 开始测试 aiohttp 客户端接收 SSE 流式响应")
    print()
    
    # 测试方法1: 逐字节读取
    # await test_aiohttp_sse_streaming()
    
    print("\n" + "="*100 + "\n")
    
    # 测试方法2: 1024字节块读取
    await test_aiohttp_sse_streaming_method2()

if __name__ == "__main__":
    asyncio.run(main())
