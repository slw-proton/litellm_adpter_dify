#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本地测试 _async_parse_standard_sse_to_generic_chunks 的脚本

用法:
  python scripts/test_parse_sse_chunks.py --scenario 1
  python scripts/test_parse_sse_chunks.py --scenario 2

说明:
- scenario 1: 先发若干 response/status 与 response/chunk 碎片, 结尾用 workflow_finished
- scenario 2: 仅发 response/chunk 碎片, 过程中重复发送两次完整JSON快照, 结尾用 [DONE]
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional, AsyncIterator

# 确保可以从项目根目录导入 custom_handler
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from custom_handler import my_custom_llm


def sse_event_block(event: Optional[str], data_lines: list[str]) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    for dl in data_lines:
        lines.append(f"data: {dl}")
    return "\n".join(lines) + "\n\n"


def build_sse_stream_text(scenario: int) -> str:
    # 一个较小的完整JSON示例
    full_json = {
        "title": "Introduction to the United Kingdom",
        "notes": None,
        "slides": [
            {"title": "Overview of the UK", "body": "The UK consists of ..."}
        ],
    }
    full_json_text = json.dumps(full_json, ensure_ascii=False, indent=2)
    # 将完整JSON放入 chunk 的字符串字段里
    chunk_with_full_snapshot = json.dumps(
        {"type": "chunk", "chunk": full_json_text}, ensure_ascii=False
    )

    blocks: list[str] = []

    if scenario == 1:
        # 状态 + 若干碎片 + workflow_finished
        blocks.append(
            sse_event_block("response", [json.dumps({"type": "status", "status": "Generating presentation outlines..."}, ensure_ascii=False)])
        )
        # 一些增量 chunk 碎片
        inc_chunks = [
            {"type": "chunk", "chunk": "{\n"},
            {"type": "chunk", "chunk": " \"title\": \"Intro\""},
            {"type": "chunk", "chunk": "\n}"},
        ]
        for obj in inc_chunks:
            blocks.append(sse_event_block("response", [json.dumps(obj, ensure_ascii=False)]))
        # 完成事件
        blocks.append(sse_event_block("response", [json.dumps({"event": "workflow_finished"}, ensure_ascii=False)]))

    elif scenario == 2:
        # 一些增量 chunk 碎片
        inc_chunks = [
            {"type": "chunk", "chunk": "{\n  \"title\": \"Intro\","},
            {"type": "chunk", "chunk": "\n  \"notes\": null\n}"},
        ]
        for obj in inc_chunks:
            blocks.append(sse_event_block("response", [json.dumps(obj, ensure_ascii=False)]))
        # 插入两次完整JSON快照(应被去重/快照过滤策略处理)
        blocks.append(sse_event_block("response", [chunk_with_full_snapshot]))
        blocks.append(sse_event_block("response", [chunk_with_full_snapshot]))
        # 尾部 [DONE]
        blocks.append(sse_event_block("response", ["[DONE]"]))

    else:
        # 默认: 简单一条 chunk + [DONE]
        blocks.append(sse_event_block("response", [json.dumps({"type": "chunk", "chunk": "hello"}, ensure_ascii=False)]))
        blocks.append(sse_event_block("response", ["[DONE]"]))

    return "".join(blocks)


class FakeContent:
    def __init__(self, data: bytes, chunk_size: int = 1024) -> None:
        self._data = data
        self._chunk_size = chunk_size

    async def iter_chunked(self, _n: int) -> AsyncIterator[bytes]:
        # 忽略 _n, 使用我们自己的 chunk_size 切片
        for i in range(0, len(self._data), self._chunk_size):
            yield self._data[i : i + self._chunk_size]


class FakeResponse:
    def __init__(self, data: bytes) -> None:
        self.content = FakeContent(data)


async def run_once(scenario: int) -> None:
    sse_text = build_sse_stream_text(scenario)
    data = sse_text.encode("utf-8")

    stats = {"chunk_count": 0, "event_count": 0}
    chunks = []

    print("[test] ===== SSE Input Preview =====")
    preview = sse_text.splitlines()[:30]
    print("\n".join(preview))
    print("[test] =================================\n")

    async for chunk in my_custom_llm._async_parse_standard_sse_to_generic_chunks(
        response=FakeResponse(data),
        stream_saver=None,
        enable_stream_save=False,
        stats=stats,
    ):
        chunks.append(chunk)
        print("[test] chunk:")
        print(json.dumps(chunk, ensure_ascii=False, indent=2))

    print("\n[test] ===== Summary =====")
    print(json.dumps({"event_count": stats.get("event_count"), "emitted_chunk_count": stats.get("chunk_count"), "received_chunks": len(chunks)}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test _async_parse_standard_sse_to_generic_chunks")
    parser.add_argument("--scenario", type=int, default=1, help="1: workflow_finished; 2: duplicate full snapshot + [DONE]")
    args = parser.parse_args()
    asyncio.run(run_once(args.scenario))


if __name__ == "__main__":
    main()


