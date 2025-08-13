#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
image_handler
- 提供通过业务API进行图片生成的同步/异步封装
- 返回LiteLLM的 ImageResponse，兼容 url / b64_json
"""

import json
import time
import logging
from typing import Any, Dict, List

import requests
from litellm.types.utils import ImageResponse, ImageObject

logger = logging.getLogger("image_handler")


def image_generation_via_business_api(
    image_api_url: str,
    *,
    model: str,
    prompt: str,
    n: int = 1,
    size: str = "1024x1024",
    response_format: str = "url",
) -> ImageResponse:
    """同步图片生成，通过业务API调用，返回 ImageResponse。"""
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "n": int(n),
        "size": size,
        "response_format": response_format,
    }
    logger.info("[image_handler] request -> %s", json.dumps(payload, ensure_ascii=False))

    image_objects: List[ImageObject] = []
    try:
        resp = requests.post(
            image_api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            logger.info("[image_handler] response <- %s", json.dumps(data, ensure_ascii=False))
            items = data.get("data", []) if isinstance(data, dict) else []
            for item in items:
                if response_format == "b64_json" and isinstance(item, dict) and item.get("b64_json"):
                    image_objects.append(ImageObject(b64_json=item["b64_json"]))
                elif isinstance(item, dict) and item.get("url"):
                    image_objects.append(ImageObject(url=item["url"]))
        else:
            logger.error("[image_handler] business api error: %s - %s", resp.status_code, resp.text)
    except Exception as e:
        logger.error("[image_handler] request failed: %s", e)

    if not image_objects:
        image_objects = [ImageObject(url="https://picsum.photos/1024/1024?fallback=1")]
    return ImageResponse(created=int(time.time()), data=image_objects)


async def aimage_generation_via_business_api(
    image_api_url: str,
    *,
    model: str,
    prompt: str,
    n: int = 1,
    size: str = "1024x1024",
    response_format: str = "url",
) -> ImageResponse:
    """异步图片生成，通过业务API调用，返回 ImageResponse。"""
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "n": int(n),
        "size": size,
        "response_format": response_format,
    }
    logger.info("[image_handler] async request -> %s", json.dumps(payload, ensure_ascii=False))

    image_objects: List[ImageObject] = []
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                image_api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info("[image_handler] async response <- %s", json.dumps(data, ensure_ascii=False))
                    items = data.get("data", []) if isinstance(data, dict) else []
                    for item in items:
                        if response_format == "b64_json" and isinstance(item, dict) and item.get("b64_json"):
                            image_objects.append(ImageObject(b64_json=item["b64_json"]))
                        elif isinstance(item, dict) and item.get("url"):
                            image_objects.append(ImageObject(url=item["url"]))
                else:
                    err_text = await resp.text()
                    logger.error("[image_handler] business api error: %s - %s", resp.status, err_text)
    except Exception as e:
        logger.error("[image_handler] async request failed: %s", e)

    if not image_objects:
        image_objects = [ImageObject(url="https://picsum.photos/1024/1024?fallback=1")]
    return ImageResponse(created=int(time.time()), data=image_objects)


