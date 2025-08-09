#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSE 流式测试脚本
目标：调用 business_api_example.py 暴露的 /api/process 接口（stream 模式），
并按完整的 SSE 事件边界逐个打印事件。

用法示例：
  python scripts/test_stream_api_process.py \
    --url http://127.0.0.1:8002/api/process \
    --query "请根据以下内容生成演示文稿布局" \
    --model business-presentation-model \
    --verbose

你也可以将输出通过管道写入本地临时文件便于调试：
  python scripts/test_stream_api_process.py | tee /tmp/sse_test.log
"""

import argparse
import asyncio
import json
from typing import Tuple, Optional

import httpx


def parse_sse_block(block: str) -> Tuple[Optional[str], str]:
    """将一个完整的 SSE 事件块解析为 (event_type, data_payload)。

    - block: 不包含事件间的空行分隔（即已按 \n\n 切分）
    - 返回：event_type（可能为 None 或 "message"）、data_payload（拼接后的 data 文本）
    """
    event_type: Optional[str] = None
    data_lines = []
    for raw in block.splitlines():
        if raw.startswith(":"):  # 注释行，忽略
            continue
        if raw.startswith("event:"):
            event_type = raw[len("event:"):].strip() or None
        elif raw.startswith("data:"):
            data_lines.append(raw[len("data:"):].lstrip())
        # 其它字段如 id:, retry: 按需扩展
    data_payload = "\n".join(data_lines)
    return event_type, data_payload


async def stream_process(url: str, query: str, model_name: str, timeout: float, verbose: bool) -> None:
    payload = {
        "query": query,
        "response_type": "text",
        "stream": True,
        "model_info": {"name": model_name},
        # 其他可选字段按需加入，如 temperature / max_tokens / response_format
    }

    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        # 注意：若经过 Nginx，后端也应设置 X-Accel-Buffering: no
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            print(f"[client] ✅ 已连接，状态码: {resp.status_code}")

            buffer = ""
            event_index = 0
            async for chunk in resp.aiter_text():
                if not chunk:
                    continue
                buffer += chunk

                # 按 SSE 事件边界拆分（以空行分隔）
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    block = block.strip("\r\n")
                    if not block:
                        continue
                    event_type, data_payload = parse_sse_block(block)

                    # 跳过 ping 或无数据的事件
                    if (event_type == "ping") or (not data_payload.strip()):
                        if verbose:
                            print(f"[client] ⏩ 跳过事件: event={event_type!r}, data(省略)")
                        continue

                    event_index += 1
                    # 尝试解析 JSON
                    parsed_obj = None
                    try:
                        parsed_obj = json.loads(data_payload)
                    except Exception:
                        pass

                    print("=" * 80)
                    print(f"[client] 📦 完整SSE事件 #{event_index}")
                    print(f"[client] event: {event_type or 'message'}")
                    if parsed_obj is not None:
                        print("[client] data(JSON):")
                        print(json.dumps(parsed_obj, ensure_ascii=False, indent=2))
                    else:
                        print("[client] data(text):")
                        print(data_payload)

            # 处理连接结束后 buffer 中遗留的最后一块（若没有以空行结束）
            tail = buffer.strip("\r\n")
            if tail:
                event_type, data_payload = parse_sse_block(tail)
                if data_payload.strip() and event_type != "ping":
                    event_index += 1
                    try:
                        parsed_obj = json.loads(data_payload)
                    except Exception:
                        parsed_obj = None
                    print("=" * 80)
                    print(f"[client] 📦(尾块) 完整SSE事件 #{event_index}")
                    print(f"[client] event: {event_type or 'message'}")
                    if parsed_obj is not None:
                        print("[client] data(JSON):")
                        print(json.dumps(parsed_obj, ensure_ascii=False, indent=2))
                    else:
                        print("[client] data(text):")
                        print(data_payload)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="测试 /api/process 的 SSE 流式返回")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8002/api/process", help="接口地址")
    parser.add_argument("--query", type=str, default="请根据这段内容返回演示用的流式输出", help="查询内容")
    parser.add_argument("--model", type=str, default="business-presentation-model", help="模型名称")
    parser.add_argument("--timeout", type=float, default=300.0, help="请求超时时间(秒)")
    parser.add_argument("--verbose", action="store_true", help="打印调试信息")
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    # 简单高效打印当前配置
    print("[client] 请求配置:")
    print(json.dumps({
        "url": args.url,
        "model": args.model,
        "timeout": args.timeout,
        "query": args.query,
    }, ensure_ascii=False, indent=2))

    asyncio.run(stream_process(args.url, args.query, args.model, args.timeout, args.verbose))


if __name__ == "__main__":
    main()


