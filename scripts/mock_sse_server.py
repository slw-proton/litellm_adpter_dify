#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟SSE服务器
用于测试aiohttp客户端的异步流式读取
"""

import asyncio
import json
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI(title="Mock SSE Server")

async def generate_mock_sse_data():
    """
    生成模拟的SSE数据流
    """
    print("[mock_server] 🚀 开始生成模拟SSE数据流")
    
    # 发送开始事件
    start_data = {
        "event": "stream_start",
        "timestamp": time.time(),
        "message": "开始模拟SSE数据流"
    }
    yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"
    
    # 发送10个数据块，每个间隔1秒
    for i in range(1, 11):
        print(f"[mock_server] 📦 生成第{i}个SSE数据块")
        
        chunk_data = {
            "event": "text_chunk",
            "chunk_id": i,
            "content": f"这是第{i}个模拟SSE数据块，当前时间: {time.strftime('%H:%M:%S')}",
            "timestamp": time.time(),
            "progress": f"{i}/10"
        }
        
        sse_line = f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
        print(f"[mock_server] 📤 发送: {sse_line.strip()}")
        yield sse_line
        
        # 等待1秒，模拟真实的流式间隔
        await asyncio.sleep(1)
    
    # 发送结束信号
    print("[mock_server] 🏁 发送结束信号")
    end_data = {
        "event": "stream_end", 
        "timestamp": time.time(),
        "total_chunks": 10,
        "message": "SSE数据流结束"
    }
    yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"
    
    # 发送标准的[DONE]信号
    yield "data: [DONE]\n\n"
    
    print("[mock_server] ✅ SSE数据流生成完成")

@app.post("/api/process")
async def mock_process():
    """
    模拟业务API的process接口
    返回SSE流式数据
    """
    print("[mock_server] 🔄 收到流式请求")
    
    return StreamingResponse(
        generate_mock_sse_data(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/health")
async def health():
    """
    健康检查接口
    """
    return {"status": "ok", "message": "Mock SSE Server is running"}

@app.get("/")
async def root():
    """
    根接口
    """
    return {
        "name": "Mock SSE Server",
        "version": "1.0.0",
        "endpoints": {
            "process": "/api/process (POST) - 返回模拟SSE数据流",
            "health": "/health (GET) - 健康检查"
        }
    }

if __name__ == "__main__":
    print("🚀 启动模拟SSE服务器...")
    print("📡 服务地址: http://localhost:8003")
    print("🔗 测试接口: POST http://localhost:8003/api/process")
    print("❤️  健康检查: GET http://localhost:8003/health")
    print()
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
