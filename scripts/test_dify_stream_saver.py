#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import argparse
from datetime import datetime

import requests

# 确保可导入项目内模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def ensure_logs_dir(root_path: str) -> str:
    logs_dir = os.path.join(root_path, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def stream_and_save_sse(url: str, payload: dict, output_prefix: str = "dify_curl") -> str:
    logs_dir = ensure_logs_dir(PROJECT_ROOT)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_file = os.path.join(logs_dir, f"{output_prefix}_{timestamp}.txt")

    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
    print(f"输出文件: {os.path.abspath(target_file)}")

    with requests.post(url, json=payload, stream=True, timeout=(10, 60)) as resp:
        print(f"HTTP状态: {resp.status_code}")
        if resp.status_code != 200:
            print(f"响应内容: {resp.text[:500]}")
            raise SystemExit(1)

        chunk_count = 0
        start_time = time.time()
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(f"# curl流式抓取 - {timestamp}\n")
            f.write(f"# URL: {url}\n")
            f.write("=" * 50 + "\n\n")
            for line in resp.iter_lines(decode_unicode=True, chunk_size=1024):
                if not line:
                    continue
                chunk_count += 1
                f.write(line)
                if not line.endswith("\n"):
                    f.write("\n")
                f.write("\n")
                if chunk_count % 50 == 0:
                    f.flush()

        elapsed = time.time() - start_time
        size = os.path.getsize(target_file)
        print(f"✅ 完成: 共{chunk_count}块, 耗时{elapsed:.2f}s, 大小{size}B")
        return target_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="请求业务API的SSE并保存到本地文件")
    parser.add_argument("--url", default="http://localhost:8002/api/process", help="业务API地址")
    parser.add_argument("--query", default="测试stream保存(curl)", help="请求的query内容")
    parser.add_argument("--model", default="dify-test", help="model_info.name")
    parser.add_argument("--output-prefix", default="dify_curl", help="输出文件前缀")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    payload = {
        "query": args.query,
        "model_info": {"name": args.model},
        "response_type": "text",
        "stream": True,
    }

    try:
        file_path = stream_and_save_sse(args.url, payload, args.output_prefix)
        print(f"保存完成: {file_path}")
        return 0
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


