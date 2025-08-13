#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图片生成服务模块
- 封装 LiteLLM 图片生成逻辑
- 提供模拟URL回退能力，便于前端联调
"""

import os
import sys
import uuid
from typing import Any, List, Optional, Tuple, Dict
import json

from productAdapter.utils.env_loader import get_env
from productAdapter.utils.logging_init import init_logger_with_env_loader
from productAdapter.api.dify_workflow_client import DifyWorkflowClient


# 对齐 business_api_example.py 的日志初始化
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = init_logger_with_env_loader("image_generation_service", project_root)


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _extract_images_from_dify_content(content_str: str) -> List[Dict[str, Any]]:
    """
    从 Dify 返回的 content 字符串中提取图片条目列表（每项包含 url 或 b64_json）。
    兼容两层结构 {"text": "{...}"} 或直接对象 { data: [...] }。
    """
    try:
        parsed = json.loads(content_str) if isinstance(content_str, str) else content_str
        # 两层结构：外层 {"text": "{...}"}
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            inner = parsed.get("text")
            try:
                inner_parsed = json.loads(inner) if isinstance(inner, str) else inner
                if isinstance(inner_parsed, dict) and isinstance(inner_parsed.get("data"), list):
                    return inner_parsed.get("data")
            except Exception:
                return []
        # 直接对象：{ data: [...] }
        if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
            return parsed.get("data")
    except Exception:
        return []
    return []


def _normalize_images(images: List[Dict[str, Any]], response_format: str, limit: int) -> List[Dict[str, Any]]:
    """
    规范化图片条目：
    - 仅保留与 response_format 匹配的键（url 或 b64_json）
    - 裁剪至 limit 数量
    - 忽略不符合格式的条目
    """
    normalized: List[Dict[str, Any]] = []
    key = "b64_json" if (response_format or "url") == "b64_json" else "url"
    for item in images:
        if not isinstance(item, dict):
            continue
        if key in item and item.get(key):
            normalized.append({key: item[key]})
        if len(normalized) >= max(1, int(limit)):
            break
    return normalized


def _generate_mock_images(response_format: str, img_size: str, num_images: int) -> List[Dict[str, Any]]:
    """
    生成模拟图片条目列表（仅用于非生产或显式允许回退的场景）。
    - response_format=url: 返回占位URL
    - response_format=b64_json: 返回1x1透明PNG的base64占位
    """
    if response_format == "b64_json":
        placeholder_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        )
        return [{"b64_json": placeholder_b64} for _ in range(max(1, int(num_images)))]

    base_url = get_env("MOCK_IMAGE_BASE_URL", "https://picsum.photos")
    parts = (img_size or "1024x1024").lower().split("x")
    if len(parts) != 2:
        width, height = "1024", "1024"
    else:
        width, height = parts[0].strip() or "1024", parts[1].strip() or "1024"
    return [
        {"url": f"{base_url}/{width}/{height}?random={uuid.uuid4().hex[:8]}"}
        for _ in range(max(1, int(num_images)))
    ]


def _generate_images_via_litellm(
    prompt: str,
    model: str,
    size: str,
    n: int,
    response_format: str,
) -> List[Any]:
    """
    使用LiteLLM进行图片生成。返回与OpenAI一致的结构：[{"url": ...}] 或 [{"b64_json": ...}]
    """
    try:
        import litellm
    except Exception as import_err:
        raise RuntimeError(f"未安装或无法导入litellm: {import_err}")

    try:
        result = litellm.image_generation(
            model=model,
            prompt=prompt,
            size=size,
            n=n,
            response_format=response_format,
        )
        data = result.get("data") if isinstance(result, dict) else None
        if not data:
            try:
                data = getattr(result, "data")  # 兼容某些返回对象
            except Exception:
                data = None
        if not data:
            raise RuntimeError("LiteLLM图片生成返回空数据")
        return data
    except Exception as e:
        raise RuntimeError(f"LiteLLM图片生成失败: {type(e).__name__}: {e}")


def _perform_image_generation(
    prompt: str,
    model: Optional[str],
    size: Optional[str],
    n: Optional[int],
    response_format: Optional[str],
) -> Tuple[List[Any], str]:
    enable_litellm = _is_truthy(get_env("ENABLE_LITELLM_IMAGE", "false"))
    chosen_model = model or get_env("LITELLM_IMAGE_MODEL", "openai/gpt-image-1")
    img_size = size or "1024x1024"
    num_images = int(n or 1)
    fmt = response_format or "url"

    # 优先通过 Dify 工作流生成
    try:
        logger.info("调用Dify工作流进行图片生成（PPT专用配置）")
        # 图片生成服务配置
        llm_image_api_key = get_env("LLM_IMAGE_API_KEY", None)
        llm_image_base_url = get_env("LLM_IMAGE_BASE_URL", None)
        # dify平台配置
        dify_base_url = get_env("DIFY_BASE_URL", None)
        dify_api_key = get_env("DIFY_PPT_IMAGE_API_KEY", None)
        dify_workflow_id = get_env("DIFY_PPT_IMAGE__WORKFLOW_ID", None)

        # 构造 messages，供 DifyWorkflowClient.format_input_data 提取 user 内容
        messages: List[dict] = [
            {
                "prompt": prompt,
                "size": img_size,
                "n": num_images,
                "response_format": fmt,
                "llm_image_api_key": llm_image_api_key,
                "llm_image_base_url": llm_image_base_url,
            }
        ]

        logger.info(
            f"generate_images messages: {json.dumps(messages, ensure_ascii=False, indent=2)}"
        )
        dify_result = DifyWorkflowClient.process_query_with_config(
            query=messages,
            api_key=dify_api_key,
            base_url=dify_base_url,
            workflow_id=dify_workflow_id,
            questType="image_generation",
        )
        logger.info(
            f"generate_images process_query_with_config: {json.dumps(dify_result, ensure_ascii=False, indent=2    )}"
        )
        if dify_result.get("success"):
            content_str = dify_result.get("content", "")
            images = _extract_images_from_dify_content(content_str)
            if images:
                images = _normalize_images(images, fmt, num_images)
                logger.info(f"已通过Dify工作流提取图片列表: 数量={len(images)} (规范化后)")
                return images, chosen_model
            else:
                logger.warning("Dify工作流content未提取到图片列表，继续后续分支")
        else:
            logger.error(f"Dify工作流失败: {dify_result.get('error')}")
    except Exception as e:
        logger.error(f"调用Dify工作流异常，将回退: {e}")

    # 次选：LiteLLM 图片接口
    if enable_litellm:
        try:
            data_list = _generate_images_via_litellm(
                prompt=prompt,
                model=chosen_model,
                size=img_size,
                n=num_images,
                response_format=fmt,
            )
            logger.info(
                f"通过LiteLLM生成图片成功: 数量={len(data_list)}, 模型={chosen_model}, 尺寸={img_size}, 格式={fmt}"
            )
            data_list = _normalize_images(data_list, fmt, num_images)
            return data_list, chosen_model
        except Exception as e:
            logger.error(f"调用LiteLLM生成图片失败，将回退为模拟: {e}")

    # 回退：生成模拟URL（按生产开关控制）
    environment = get_env("ENVIRONMENT", "production").lower()
    allow_mock = _is_truthy(get_env("IMAGE_MOCK_FALLBACK_ENABLED", "false"))
    if environment in ("prod", "production"):
        allow_mock = False

    if not allow_mock:
        logger.error(
            "图片生成不可用：Dify与LiteLLM均失败，且生产环境禁用模拟回退 | env=%s, fmt=%s, model=%s, size=%s, n=%s",
            environment,
            fmt,
            chosen_model,
            img_size,
            num_images,
        )
        raise RuntimeError("Image generation unavailable: all providers failed and mock fallback is disabled")

    mock_list = _generate_mock_images(fmt, img_size, num_images)
    mock_list = _normalize_images(mock_list, fmt, num_images)
    logger.warning(
        "使用模拟回退生成图片（非生产或显式允许）: 数量=%s, fmt=%s", len(mock_list), fmt
    )
    return mock_list, chosen_model


def generate_images(
    prompt: str,
    model: Optional[str],
    size: Optional[str],
    n: Optional[int],
    response_format: Optional[str],
) -> Tuple[List[Any], str]:
    """
    统一入口：根据环境变量决定是否调用LiteLLM，否则返回模拟URL。
    对外仅作薄封装，委托 _perform_image_generation 实现。

    Returns:
        (data, chosen_model)
    """
    return _perform_image_generation(
        prompt=prompt,
        model=model,
        size=size,
        n=n,
        response_format=response_format,
    )
