#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本：直连业务API图片生成接口 (/api/generate_image)

用法示例：
1) 直接调用（默认使用FastAPI TestClient，服务无需启动）：
   python -m productAdapter.tests.test_image_api --prompt "a cute cat" --n 1 --size 1024x1024

2) 通过HTTP调用（需要先启动 business_api_example 服务）：
   python -m productAdapter.tests.test_image_api --http --base-url http://localhost:8002 \
     --prompt "a cute cat" --n 1 --size 1024x1024

可通过重定向将输出保存：
   python -m productAdapter.tests.test_image_api --prompt "a cat" > tmp_image_test.log
"""

import os
import sys
import json
import argparse
from typing import Any, Dict


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "prompt": args.prompt,
        "model": args.model,
        "n": args.n,
        "size": args.size,
        "response_format": args.response_format,
    }


def run_http(args: argparse.Namespace) -> Dict[str, Any]:
    import requests
    base_url = args.base_url.rstrip("/")
    url = f"{base_url}/api/generate_image"
    payload = build_payload(args)
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_inprocess(args: argparse.Namespace) -> Dict[str, Any]:
    # 直接导入 FastAPI app，使用 TestClient 调用，无需启动 uvicorn
    from fastapi.testclient import TestClient
    from productAdapter.api.business_api_example import app

    client = TestClient(app)
    payload = build_payload(args)
    resp = client.post("/api/generate_image", json=payload)
    return resp.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Business API /api/generate_image")
    parser.add_argument("--http", action="store_true", help="使用HTTP方式请求(需要服务已启动)")
    parser.add_argument("--base-url", type=str, default=os.getenv("BUSINESS_API_BASE_URL", "http://localhost:8002"),
                        help="业务API基础URL，仅在 --http 模式下有效")
    parser.add_argument("--prompt", type=str, default="a cute cat sitting on a chair", help="图片生成提示词")
    parser.add_argument("--model", type=str, default="business-api-image", help="模型名称")
    parser.add_argument("--n", type=int, default=1, help="生成图片数量")
    parser.add_argument("--size", type=str, default="1024x1024", help="图片尺寸，如1024x1024")
    parser.add_argument("--response-format", type=str, default="url", choices=["url", "b64_json"], help="响应格式")
    parser.add_argument("--out", type=str, default=None, help="将响应写入文件路径(可选)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = run_http(args) if args.http else run_inprocess(args)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output + "\n")
        print(f"response: {output}")
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


