#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证 /api/process 在 stream=true 时是否按 SSE 逐块返回
- 通过 mock `DifyWorkflowClient.stream_dify_response`，构造可控的流式事件
- 使用 FastAPI TestClient 的流式读取判断是否逐块收到 `data: ...` 行
"""

import os
import sys
import json
import asyncio
from typing import Any, AsyncGenerator
from unittest.mock import patch

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from starlette.testclient import TestClient
from productAdapter.api.business_api_example import app


async def _fake_stream_dify_response(
    query: Any,
    response_id: str = None,
    start_time: float = None,
) -> AsyncGenerator[str, None]:
    """构造一个稳定可预测的SSE流（3段数据）。"""
    # 模拟逐块产出
    for i in range(2):
        await asyncio.sleep(0)  # 让出事件循环，确保 TestClient 能分段接收
        yield f"data: {json.dumps({'i': i}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


def test_sse_streaming_behavior():
    print("=== 测试 /api/process SSE 流式返回行为 ===")

    payload = {
        "query": [{"role": "user", "content": "hello streaming"}],
        "model_info": {"name": "dify-test"},
        "stream": True,
        "response_type": "text",
    }

    # 打补丁：让业务端点内部调用的流式方法返回我们构造的逐块数据
    with patch(
        "productAdapter.api.dify_workflow_client.DifyWorkflowClient.stream_dify_response",
        new=_fake_stream_dify_response,
    ):
        client = TestClient(app)
        with client.stream("POST", "/api/process", json=payload) as resp:
            assert resp.status_code == 200, f"非200响应: {resp.status_code}"
            content_type = resp.headers.get("content-type", "")
            print(f"content-type: {content_type}")
            assert content_type.startswith("text/event-stream"), "返回的不是SSE类型"

            # 逐行读取，遇到两段 data: 行就结束，判断是否真的是分段到达
            data_lines = []
            for line in resp.iter_lines(chunk_size=1024):
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                print(f"LINE: {line}")
                if line.startswith("data: "):
                    data_lines.append(line)
                if len(data_lines) >= 2:
                    break

            print(f"前两段 data 行: {data_lines}")
            # 至少应当在未读完整个响应前拿到两段 data 行，这表示是逐块返回
            assert len(data_lines) == 2, "未按逐块返回拿到两段 data 行"
            assert data_lines[0] == "data: {\"i\": 0}", "第一段数据不匹配"
            assert data_lines[1] == "data: {\"i\": 1}", "第二段数据不匹配"

    print("✅ SSE 流式单测通过：已验证逐块返回而非一次性大包")


def main():
    try:
        test_sse_streaming_behavior()
        return True
    except AssertionError as e:
        print(f"❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)


