"""
平台工具模块

提供平台相关的功能，包括：
- 平台函数定义
- 平台信息处理
- 平台相关的请求参数构建
"""

import json
import logging
from typing import Dict, List, Optional, Any


def get_platform_functions(platform: str = "PPT") -> List[Dict[str, Any]]:
    """
    获取平台相关的函数定义
    
    Args:
        platform (str): 当前平台名称，默认为 "PPT"
    
    Returns:
        list: 包含平台相关函数的列表
    """
    return [
        {
            "name": "get_current_platform",
            "description": f"获取当前平台信息。当前运行环境是 {platform} 平台，请返回 {platform} 作为平台名称。",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": f"当前平台名称，当前环境是 {platform} 平台，请返回 '{platform}'",
                        "enum": ["PPT", "WEB", "MOBILE", "DESKTOP"],
                        "default": platform
                    },
                    "version": {
                        "type": "string",
                        "description": "平台版本号，例如 '1.0.0'",
                        "default": "1.0.0"
                    },
                    "features": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": f"平台支持的功能列表，{platform}平台支持 ['presentation', 'slides', 'charts', 'templates']",
                        "default": ["presentation", "slides", "charts", "templates"]
                    }
                },
                "required": ["platform"]
            }
        }
    ]


def add_functions_to_request(
    request_params: Dict[str, Any], 
    functions: Optional[List[Dict[str, Any]]] = None, 
    function_name: Optional[str] = None, 
    platform: str = "PPT"
) -> Dict[str, Any]:
    """
    将函数定义添加到请求参数中
    
    Args:
        request_params (dict): 请求参数字典
        functions (list, optional): 函数定义列表，如果为None则使用默认的平台函数
        function_name (str, optional): 要调用的函数名称，如果为None则使用第一个函数
        platform (str, optional): 当前平台名称，默认为 "PPT"
    
    Returns:
        dict: 更新后的请求参数字典
    """
    if functions is None:
        functions = get_platform_functions(platform)
    
    # 如果指定了平台，更新函数描述
    if platform and functions:
        for func in functions:
            if func["name"] == "get_current_platform":
                func["description"] = f"获取当前平台信息。当前运行环境是 {platform} 平台，请返回 {platform} 作为平台名称。"
                # 更新参数描述
                if "parameters" in func and "properties" in func["parameters"]:
                    if "platform" in func["parameters"]["properties"]:
                        func["parameters"]["properties"]["platform"]["description"] = f"当前平台名称，当前环境是 {platform} 平台，请返回 '{platform}'"
                        func["parameters"]["properties"]["platform"]["default"] = platform
    
    request_params["functions"] = functions
    
    if function_name is None and functions:
        function_name = functions[0]["name"]
    
    if function_name:
        request_params["function_call"] = {"name": function_name}
    
    return request_params


def process_function_call(function_call: Any, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    处理函数调用响应
    
    Args:
        function_call: 函数调用对象
        logger: 日志记录器
    
    Returns:
        dict: 解析后的函数参数
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    print(f"\n🎯 函数调用响应:")
    print(f"  函数名称: {function_call.name}")
    print(f"  函数参数: {function_call.arguments}")
    
    try:
        function_args = json.loads(function_call.arguments)
        print(f"  解析后的参数: {json.dumps(function_args, ensure_ascii=False, indent=2)}")
        
        # 处理 get_current_platform 函数调用
        if function_call.name == "get_current_platform":
            platform = function_args.get("platform", "未知")
            version = function_args.get("version", "1.0.0")
            features = function_args.get("features", [])
            
            print(f"\n📊 平台信息:")
            print(f"  平台: {platform}")
            print(f"  版本: {version}")
            print(f"  功能: {features}")
            
            if platform == "PPT":
                print("✅ 确认当前平台是 PPT")
            else:
                print(f"⚠️ 当前平台是 {platform}，不是 PPT")
        
        return function_args
        
    except json.JSONDecodeError as e:
        error_msg = f"解析函数参数失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return {}
    except Exception as e:
        error_msg = f"处理函数调用失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return {}


def add_platform_system_message(messages: List[Dict[str, Any]], platform: str = "PPT") -> List[Dict[str, Any]]:
    """
    在消息列表开头添加平台相关的系统消息
    
    Args:
        messages (list): 消息列表
        platform (str): 当前平台名称，默认为 "PPT"
    
    Returns:
        list: 更新后的消息列表
    """
    system_message = {
        "role": "system",
        "content": f"当前运行环境是 {platform} 平台。当需要获取平台信息时，请返回 {platform} 作为平台名称。"
    }
    
    if messages:
        # 在第一条消息前插入系统消息
        messages.insert(0, system_message)
    else:
        # 如果没有消息，添加系统消息
        messages = [system_message]
    
    return messages


def get_platform_info(platform: str = "PPT") -> Dict[str, Any]:
    """
    获取平台信息
    
    Args:
        platform (str): 平台名称，默认为 "PPT"
    
    Returns:
        dict: 平台信息字典
    """
    platform_info = {
        "PPT": {
            "name": "PPT",
            "version": "1.0.0",
            "features": ["presentation", "slides", "charts", "templates"],
            "description": "PPT 演示文稿平台"
        },
        "WEB": {
            "name": "WEB",
            "version": "1.0.0",
            "features": ["web", "browser", "responsive"],
            "description": "Web 网页平台"
        },
        "MOBILE": {
            "name": "MOBILE",
            "version": "1.0.0",
            "features": ["mobile", "touch", "gesture"],
            "description": "移动端平台"
        },
        "DESKTOP": {
            "name": "DESKTOP",
            "version": "1.0.0",
            "features": ["desktop", "native", "offline"],
            "description": "桌面端平台"
        }
    }
    
    return platform_info.get(platform, platform_info["PPT"])
