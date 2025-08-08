#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用OpenAI客户端测试LiteLLM接口
测试通过OpenAI Python库调用LiteLLM代理服务器
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
import openai
# from platform_utils import (
#     get_platform_functions,
#     add_functions_to_request,
#     process_function_call,
#     add_platform_system_message,
#     get_platform_info
# )

# 导入通用的日志配置
try:
    from productAdapter.utils.logging_config import setup_logging, create_date_based_log_path
except ImportError:
    # 如果导入失败，创建一个简单的本地版本
    def create_date_based_log_path(base_dir, filename):
        """创建基于日期的日志文件路径（年/月/日结构）"""
        now = datetime.now()
        year = str(now.year)
        month = f"{now.month:02d}"
        day = f"{now.day:02d}"
        
        date_dir = os.path.join(base_dir, year, month, day)
        try:
            os.makedirs(date_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory {date_dir}: {str(e)}")
            date_dir = base_dir
        
        full_path = os.path.join(date_dir, filename)
        relative_path = os.path.join(year, month, day, filename)
        return full_path, relative_path
    
    def setup_logging(name="test_openai_client", level=None):
        """简单的本地日志配置函数"""
        # 创建logs目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名
        log_filename = f"{name}.log"
        log_file, relative_path = create_date_based_log_path(log_dir, log_filename)
        
        # 配置根日志器
        logging.basicConfig(
            level=level or logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file, mode='a', encoding='utf-8')
            ],
            force=True
        )
        
        # 创建专用的测试日志器
        logger = logging.getLogger(name)
        
        # 检查是否为新文件（当日首次运行）
        is_new_file = not os.path.exists(log_file) or os.path.getsize(log_file) == 0
        
        if is_new_file:
            logger.info("=" * 80)
            logger.info(f"📅 测试日志开始 - {datetime.now().strftime('%Y年%m月%d日')}")
            logger.info("=" * 80)
        else:
            logger.info("-" * 50)
            logger.info(f"🔄 新测试会话开始 - {datetime.now().strftime('%H:%M:%S')}")
            logger.info("-" * 50)
        
        logger.info(f"📝 日志文件: {relative_path}")
        
        return logger

def get_test_logger():
    """
    获取测试专用的日志记录器
    
    Returns:
        tuple: (logger, log_file_path)
    """
    # 使用通用的setup_logging函数
    logger = setup_logging(name="test_openai_client", level=logging.INFO)
    
    # 计算日志文件路径
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    log_filename = "test_openai_client.log"
    log_file, relative_path = create_date_based_log_path(log_dir, log_filename)
    
    return logger, log_file

# 简单的环境变量获取函数
def get_env(key, default=None):
    return os.environ.get(key, default)

def get_env_int(key, default=None):
    """获取环境变量并转换为整数"""
    value = get_env(key, default)
    return int(value) if value is not None else default

def test_openai_sync_client(logger=None):
    """
    测试同步OpenAI客户端调用LiteLLM
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始测试同步OpenAI客户端 ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置OpenAI客户端
    client = openai.OpenAI(
        base_url=base_url,
        api_key="dummy-key"  # LiteLLM代理不需要真实API密钥
    )
    
    # 从环境变量获取模型名称
    default_model = get_env("DEFAULT_MODEL", "my-custom-model")
    model_name = default_model
    message = f"使用模型: {model_name}"
    print(message)
    logger.info(message)
    
    try:
        message = "发起同步聊天请求..."
        print(message)
        logger.info(message)
        
        # 发起聊天请求
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个有用的AI助手，请用简洁明了的中文回答问题。"},
                {"role": "user", "content": "什么是人工智能？请用一句话回答。"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        message = "✅ 同步请求成功"
        print(message)
        logger.info(message)
        
        # 打印详细响应信息
        print("\n=== 同步OpenAI客户端测试结果 ===")
        print(f"模型: {response.model}")
        print(f"响应内容: {response.choices[0].message.content}")
        print(f"完成原因: {response.choices[0].finish_reason}")
        print(f"Token使用情况: {response.usage}")
        
        return True
        
    except Exception as e:
        error_msg = f"同步请求失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False

def load_request_test_data():
    """
    从request_test.json文件加载测试数据
    """
    try:
        request_test_file = os.path.join(os.path.dirname(__file__), "request_test.json")
        if os.path.exists(request_test_file):
            with open(request_test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ 成功加载测试数据: {request_test_file}")
                return data.get("data", {})
        else:
            print(f"⚠️ 测试数据文件不存在: {request_test_file}")
            return None
    except Exception as e:
        print(f"❌ 加载测试数据失败: {str(e)}")
        return None

async def test_openai_async_client(logger=None):
    """
    测试异步OpenAI客户端调用LiteLLM，使用request_test.json中的数据
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, log_file = get_test_logger()
    else:
        log_file = None  # 如果传入了logger，不需要log_file
    
    # 你可以在这里打印各种级别的日志
    logger.info("🚀 开始测试异步OpenAI客户端")
    logger.info("📝 这是信息级别的日志")
    logger.warning("⚠️ 这是警告级别的日志")
    logger.error("❌ 这是错误级别的日志")
    
    print("=== 开始测试异步OpenAI客户端 ===")
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置异步OpenAI客户端
    async_client = openai.AsyncOpenAI(
        base_url=base_url,
        api_key="dummy-key"  # LiteLLM代理不需要真实API密钥
    )
    
    # 加载测试数据
    test_data = load_request_test_data()
    logger.info(f"加载测试数据: {test_data}，log_file: {log_file}") 
    if test_data is None:
        message = "❌ 无法加载测试数据，使用默认参数"
        print(message)
        logger.warning(message)
        # 使用默认参数
        model_name = get_env("DEFAULT_MODEL", "my-custom-model")
        messages = [
            {"role": "system", "content": "你是一个专业的技术助手，请用中文回答技术问题。"},
            {"role": "user", "content": "请简单介绍一下LiteLLM是什么？"}
        ]
        request_params = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 150
        }
    else:
        message = "✅ 使用request_test.json中的测试数据"
        print(message)
        logger.info(message)
        # 使用测试数据，但将模型名称替换为可用的模型
        model_name = get_env("DEFAULT_MODEL", "my-custom-model")
        
        # 构建请求参数
        request_params = {
            "model": model_name,  # 使用可用的模型
            "messages": test_data.get("messages", []),
            "temperature": test_data.get("temperature", 0.7),
            "max_tokens": test_data.get("max_tokens", 1000),
            "stream": True
        }
        
        # 如果有response_format，也包含进去（但可能需要简化以适配当前模型）
        if "response_format" in test_data:
            message = "📝 包含structured output格式"
            print(message)
            logger.info(message)
            # 使用get方法安全获取response_format
            request_params["response_format"] = test_data.get("response_format")
        
        # 如果有stream参数
        if "stream" in test_data:
            message = f"🔄 流式模式: {test_data['stream']}"
            print(message)
            logger.info(message)
            request_params["stream"] = test_data.get("stream", False)  # 使用test_data中的stream值
    
    # message = f"使用模型: {request_params['model']}"
    # print(message)
    # logger.info(message)
    # message = f"消息数量: {len(request_params['messages'])}"
    # print(message)
    # logger.info(message)
    
    try:
        message = "发起异步聊天请求..."
        print(message)
        logger.info(message)
        
        # 检查是否为流式模式
        if request_params.get("stream", False):
            message = "🔄 使用异步流式模式..."
            print(message)
            logger.info(message)
            
            try:
                # 发起异步流式聊天请求
                stream = await async_client.chat.completions.create(**request_params)
                
                print("\n=== 异步流式OpenAI客户端测试结果 ===")
                print("流式响应内容:")
                
                collected_content = ""
                try:
                    # 使用正确的异步流式处理方式
                    async for chunk in stream:
                        if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            collected_content += content
                            print(content, end="", flush=True)
                        elif hasattr(chunk.choices[0], 'message') and chunk.choices[0].message.content is not None:
                            content = chunk.choices[0].message.content
                            collected_content += content
                            print(content, end="", flush=True)
                except TypeError as stream_error:
                    # 处理 'coroutine' object is not an iterator 错误
                    error_msg = f"异步流式处理失败（LiteLLM兼容性问题）: {str(stream_error)}"
                    logger.warning(f"⚠️ {error_msg}")
                    print(f"\n⚠️ {error_msg}")
                    
                    # 尝试使用非流式模式作为备选方案
                    message = "🔄 尝试使用非流式模式作为备选方案..."
                    print(message)
                    logger.info(message)
                    
                    # 创建非流式请求参数
                    non_stream_params = request_params.copy()
                    non_stream_params["stream"] = False
                    
                    # 发起非流式请求
                    response = await async_client.chat.completions.create(**non_stream_params)
                    
                    if hasattr(response.choices[0], 'message') and response.choices[0].message.content:
                        content = response.choices[0].message.content
                        collected_content = content
                        print(f"📝 备选方案响应内容: {content}")
                        logger.info(f"📝 备选方案响应内容: {content}")
                    else:
                        error_msg = "备选方案也失败了"
                        logger.error(f"❌ {error_msg}")
                        print(f"❌ {error_msg}")
                        return False
                        
                except Exception as stream_error:
                    error_msg = f"流式处理失败: {str(stream_error)}"
                    logger.error(f"❌ {error_msg}")
                    print(f"\n❌ {error_msg}")
                    return False
                
                print("\n")  # 换行
                message = "✅ 异步流式请求成功"
                print(message)
                logger.info(message)
                
                # 打印收集到的完整内容
                print(f"📝 完整响应内容: {collected_content}")
                logger.info(f"📝 完整响应内容: {collected_content}")
                
            except Exception as e:
                error_msg = f"异步流式请求失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                print(f"❌ {error_msg}")
                
                # 尝试使用非流式模式作为备选方案
                message = "🔄 尝试使用非流式模式作为备选方案..."
                print(message)
                logger.info(message)
                
                try:
                    # 创建非流式请求参数
                    non_stream_params = request_params.copy()
                    non_stream_params["stream"] = False
                    
                    # 发起非流式请求
                    response = await async_client.chat.completions.create(**non_stream_params)
                    
                    if hasattr(response.choices[0], 'message') and response.choices[0].message.content:
                        content = response.choices[0].message.content
                        print(f"📝 备选方案响应内容: {content}")
                        logger.info(f"📝 备选方案响应内容: {content}")
                        return True
                    else:
                        error_msg = "备选方案也失败了"
                        logger.error(f"❌ {error_msg}")
                        print(f"❌ {error_msg}")
                        return False
                        
                except Exception as backup_error:
                    error_msg = f"备选方案也失败了: {str(backup_error)}"
                    logger.error(f"❌ {error_msg}")
                    print(f"❌ {error_msg}")
                    return False
        
        else:
            # 发起普通异步聊天请求
            response = await async_client.chat.completions.create(**request_params)
            
            message = "✅ 异步请求成功"
            print(message)
            logger.info(message)
            
            # 打印详细响应信息
            print("\n=== 异步OpenAI客户端测试结果 ===")
            print(f"模型: {response.model}")
            print(f"响应内容: {response.choices[0].message.content}")
            print(f"完成原因: {response.choices[0].finish_reason}")
            print(f"Token使用情况: {response.usage}")
        
        return True
        
    except Exception as e:
        error_msg = f"异步请求失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False

async def test_openai_structured_output(logger=None):
    """
    测试异步OpenAI客户端的structured output功能，使用request_test.json中的完整数据
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始测试OpenAI structured output ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置异步OpenAI客户端
    async_client = openai.AsyncOpenAI(
        base_url=base_url,
        api_key="dummy-key"  # LiteLLM代理不需要真实API密钥
    )
    
    # 加载测试数据
    test_data = load_request_test_data()
    if test_data is None:
        message = "❌ 无法加载测试数据，跳过structured output测试"
        print(message)
        logger.warning(message)
        return False
    
    message = "✅ 使用request_test.json中的完整测试数据"
    print(message)
    logger.info(message)
    
    # 使用测试数据中的所有参数，但替换模型名称
    model_name = get_env("DEFAULT_MODEL", "my-custom-model")
    
    # 构建完整的请求参数
    request_params = {
        "model": model_name,  # 使用可用的模型
        "messages": test_data.get("messages", []),
        # "temperature": test_data.get("temperature", 0.7),
        # "max_tokens": test_data.get("max_tokens", 1000)
    }
    
    # 使用平台工具模块添加系统消息，明确告诉 LLM 当前平台是 PPT
    # request_params["messages"] = add_platform_system_message(request_params["messages"], platform="PPT")
    # logger.info("✅ 使用平台工具模块添加了系统消息，明确告诉 LLM 当前平台是 PPT")
    
    # 使用平台工具模块添加 functions 参数，明确指定平台为 PPT
    # request_params = add_functions_to_request(request_params, platform="PPT")
    # logger.info("✅ 使用平台工具模块添加了 functions 参数，明确指定平台为 PPT")

    # logger.info(f"🔍 添加了 functions 参数: {json.dumps(request_params.get('functions'), ensure_ascii=False, indent=2)}")

    logger.info(f"🔍 完整response_format: {json.dumps(test_data.get('response_format'), ensure_ascii=False, indent=2)}")

    # 包含response_format（如果支持的话）
    if "response_format" in test_data:
        message = "📝 测试structured output格式"
        print(message)
        logger.info(message)
        try:
            request_params["response_format"] = test_data.get("response_format")
        except Exception as e:
            message = f"⚠️ 不支持response_format，将忽略: {str(e)}"
            print(message)
            logger.warning(message)
    
    # message = f"使用模型: {request_params['model']}"
    # print(message)
    # logger.info(message)
    # message = f"消息数量: {len(request_params['messages'])}"
    # print(message)
    # logger.info(message)
    # message = f"包含response_format: {'response_format' in request_params}"
    # print(message)
    # logger.info(message)
    
    # 调试：打印完整的request_params
    message = f"🔍 完整request_params keys: {list(request_params.keys())}"
    print(message)
    logger.info(f"🔍 完整request_params: {json.dumps(request_params, ensure_ascii=False, indent=2)}")
    # if 'response_format' in request_params:
    #     message = f"🔍 response_format内容: {json.dumps(request_params['response_format'], ensure_ascii=False, indent=2)[:200]}..."
    #     print(message)
    #     logger.info(message)
    
    try:
        message = "发起structured output请求..."
        print(message)
        logger.info(message)
        
        # 发起异步聊天请求
        response = await async_client.chat.completions.create(**request_params)
        
        print("✅ structured output请求成功")
        print(f"response: {json.dumps(response.model_dump(), ensure_ascii=False, indent=2)}")
        
        # 使用平台工具模块处理函数调用响应
        # function_call = response.choices[0].message.function_call
        # function_args = process_function_call(function_call, logger)
        
        return True
        
    except Exception as e:
        error_msg = f"structured output请求失败: {str(e)}"
        print(f"❌ {error_msg}")
        return False

def test_openai_stream_client(logger=None):
    """
    测试流式OpenAI客户端调用LiteLLM
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始测试流式OpenAI客户端 ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置OpenAI客户端
    client = openai.OpenAI(
        base_url=base_url,
        api_key="dummy-key"  # LiteLLM代理不需要真实API密钥
    )
    
    # 从环境变量获取模型名称
    default_model = get_env("DEFAULT_MODEL", "my-custom-model")
    model_name = default_model
    message = f"使用模型: {model_name}"
    print(message)
    logger.info(message)
    
    try:
        message = "发起流式聊天请求..."
        print(message)
        logger.info(message)
        
        print("\n=== 流式OpenAI客户端测试结果 ===")
        print("流式响应内容:")
        
        # 发起流式聊天请求
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个创意写作助手，请用中文创作。"},
                {"role": "user", "content": "请写一首关于春天的短诗，4行即可。"}
            ],
            temperature=0.8,
            max_tokens=200,
            stream=True
        )
        
        collected_content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                collected_content += content
                print(content, end="", flush=True)
        
        print("\n")  # 换行
        message = "✅ 流式请求成功"
        print(message)
        logger.info(message)
        
        return True
        
    except Exception as e:
        error_msg = f"流式请求失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False

def test_openai_models_list(logger=None):
    """
    测试OpenAI客户端获取模型列表功能
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始测试模型列表获取 ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    # 同时打印和记录到日志
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置OpenAI客户端
    client = openai.OpenAI(
        base_url=base_url,
        api_key="dummy-key"  # LiteLLM代理不需要真实API密钥
    )
    
    try:
        message = "获取模型列表..."
        print(message)
        logger.info(message)
        
        # 获取模型列表
        models = client.models.list()
        
        message = "✅ 模型列表获取成功"
        print(message)
        logger.info(message)
        
        # 打印详细模型信息
        print("\n=== 可用模型列表 ===")
        print(f"模型总数: {len(models.data)}")
        
        for i, model in enumerate(models.data, 1):
            print(f"{i}. 模型ID: {model.id}")
            print(f"   类型: {model.object}")
            print(f"   拥有者: {model.owned_by}")
            print(f"   创建时间: {model.created}")
            if hasattr(model, 'root'):
                print(f"   根模型: {model.root}")
            print()
        
        # 验证是否包含预期的模型
        model_ids = [model.id for model in models.data]
        expected_models = ["my-custom-model", "business-presentation-model"]
        
        for expected in expected_models:
            if expected in model_ids:
                print(f"✅ 发现预期模型: {expected}")
            else:
                print(f"⚠️ 未发现预期模型: {expected}")
        
        return True
        
    except Exception as e:
        error_msg = f"模型列表获取失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False

def test_openai_multiple_models(logger=None):
    """
    测试多个模型调用
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始测试多个模型调用 ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 配置OpenAI客户端
    client = openai.OpenAI(
        base_url=base_url,
        api_key="dummy-key"
    )
    
    # 测试不同的模型名称
    models_to_test = [
        "my-custom-model",
        get_env("DEFAULT_MODEL", "my-custom-model")
    ]
    
    print("\n=== 多模型测试结果 ===")
    successful_models = []
    failed_models = []
    
    for model in models_to_test:
        try:
            message = f"测试模型: {model}"
            print(message)
            logger.info(message)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "请说 '你好'"}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            content = response.choices[0].message.content
            message = f"✅ 模型 '{model}': {content}"
            print(message)
            logger.info(message)
            successful_models.append(model)
            
        except Exception as e:
            error_msg = f"模型 '{model}' 失败: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            failed_models.append(model)
    
    message = f"成功的模型: {successful_models}"
    print(message)
    logger.info(message)
    message = f"失败的模型: {failed_models}"
    print(message)
    logger.info(message)
    
    return len(successful_models) > 0

async def run_all_tests(logger=None):
    """
    运行所有测试
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("🚀 开始运行OpenAI客户端测试套件")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 记录环境变量信息
    print(f"环境变量: LITELLM_PROXY_HOST={get_env('LITELLM_PROXY_HOST', '未设置')}, "
               f"LITELLM_PROXY_PORT={get_env('LITELLM_PROXY_PORT', '未设置')}, "
               f"DEFAULT_MODEL={get_env('DEFAULT_MODEL', '未设置')}")
    
    results = {}
    
    # 测试1: 同步客户端
    results['sync'] = test_openai_sync_client(logger=logger)
    
    # 测试2: 异步客户端
    results['async'] = await test_openai_async_client(logger=logger)
    
    # 测试3: 流式客户端
    results['stream'] = test_openai_stream_client(logger=logger)
    
    # 测试4: 模型列表测试
    results['models_list'] = test_openai_models_list(logger=logger)
    
    # 测试5: 多模型测试
    results['multiple_models'] = test_openai_multiple_models(logger=logger)
    
    # 测试6: Structured Output测试
    results['structured'] = await test_openai_structured_output(logger=logger)
    
    # 打印总结
    print("\n" + "="*50)
    print("🏁 测试总结")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name.ljust(20)}: {status}")
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    return passed_tests == total_tests

async def test_openai_sync_vs_async_comparison(logger=None):
    """
    对比测试AsyncOpenAI和OpenAI的区别
    
    Args:
        logger: 日志记录器，如果为None则创建新的
    """
    print("=== 开始对比测试AsyncOpenAI vs OpenAI ===")
    
    # 如果没有传入logger，则创建新的
    if logger is None:
        logger, _ = get_test_logger()
    
    # 从环境变量获取LiteLLM代理的主机和端口
    host = get_env("LITELLM_PROXY_HOST", "localhost")
    port = get_env_int("LITELLM_PROXY_PORT", 8080)
    base_url = f"http://{host}:{port}"
    
    message = f"LiteLLM代理地址: {base_url}"
    print(message)
    logger.info(message)
    
    # 测试参数
    model_name = get_env("DEFAULT_MODEL", "my-custom-model")
    test_messages = [
        {"role": "user", "content": "请简单介绍一下LiteLLM"}
    ]
    
    """ print("\n=== 测试1: 使用OpenAI（同步）===")
    try:
        # 配置同步OpenAI客户端
        sync_client = openai.OpenAI(
            base_url=base_url,
            api_key="dummy-key"
        )
        
        # 同步流式调用
        stream = sync_client.chat.completions.create(
            model=model_name,
            messages=test_messages,
            stream=True
        )
        
        print("同步流式响应内容:")
        collected_content = ""
        chunk_count = 0
        for chunk in stream:
            chunk_count += 1
            print(f"\n[客户端] 📦 收到第{chunk_count}个流式块")
            print(f"[客户端] 完整chunk对象: {chunk}")
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                collected_content += content
                print(f"[客户端] 📝 内容: {content[:100]}...")  # 直接打印内容，不用repr
                print(content, end="", flush=True)
            else:
                print(f"[客户端] ⚠️  chunk.choices[0].delta.content 为 None")
        
        print(f"\n✅ 同步流式请求成功，内容长度: {len(collected_content)}")
        
    except Exception as e:
        print(f"❌ 同步流式请求失败: {str(e)}") """
    
    print("\n=== 测试2: 使用AsyncOpenAI（异步）===")
    try:
        # 配置异步OpenAI客户端
        async_client = openai.AsyncOpenAI(
            base_url=base_url,
            api_key="dummy-key"
        )
        
        # 异步流式调用
        stream = await async_client.chat.completions.create(
            model=model_name,
            messages=test_messages,
            stream=True
        )
        
        print("异步流式响应内容:")
        collected_content = ""
        parsed_text_content = ""  # 用于存储解析后的纯文本内容
        chunk_count = 0
        async for chunk in stream:
            chunk_count += 1
            print(f"\n[客户端] 📦 收到第{chunk_count}个流式块")
            print(f"[客户端] 完整chunk对象: {chunk}")
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                collected_content += content
                print(f"[客户端]======原始内容: {content[:100]}...")
                
                # 解析SSE数据，提取实际文本内容
                try:
                    # 检查是否为SSE格式
                    if content.startswith('data: '):
                        # 移除 "data: " 前缀
                        json_str = content[6:].strip()
                        if json_str and json_str != '[DONE]':
                            try:
                                sse_data = json.loads(json_str)
                                # 只处理text_chunk事件，提取增量文本
                                if sse_data.get("event") == "text_chunk":
                                    text_part = sse_data.get("data", {}).get("text", "")
                                    if text_part:
                                        # 在这里就解码Unicode转义字符
                                        try:
                                            decoded_text_part = json.loads(f'"{text_part}"')
                                        except json.JSONDecodeError:
                                            decoded_text_part = text_part  # 如果解码失败，使用原文本
                                        
                                        parsed_text_content += decoded_text_part
                                        print(f"[客户端] 📝 解析出文本: {decoded_text_part}")
                                        print(decoded_text_part, end="", flush=True)
                                # 处理workflow_finished事件，但不重复添加文本
                                elif sse_data.get("event") == "workflow_finished":
                                    final_text = sse_data.get("data", {}).get("outputs", {}).get("text", "")
                                    print(f"[客户端] 🏁 工作流完成，最终文本长度: {len(final_text)}")
                                    # 如果通过text_chunk没有收集到任何文本，才使用最终文本
                                    if not parsed_text_content and final_text:
                                        # 同样解码Unicode转义字符
                                        try:
                                            decoded_final_text = json.loads(f'"{final_text}"')
                                        except json.JSONDecodeError:
                                            decoded_final_text = final_text
                                        
                                        parsed_text_content = decoded_final_text
                                        print(f"[客户端] 📝 使用最终文本作为结果")
                                # 忽略其他事件类型
                                else:
                                    print(f"[客户端] ℹ️  忽略事件: {sse_data.get('event', 'unknown')}")
                            except json.JSONDecodeError:
                                # JSON解析失败，可能是不完整的数据，跳过
                                print(f"[客户端] ⚠️ JSON解析失败，跳过: {json_str[:50]}...")
                    else:
                        # 非SSE格式，严格过滤，只保留纯文本
                        # 跳过包含JSON字段的内容
                        if any(keyword in content for keyword in ['":', '{"', '"}', 'created_at', 'finished_at', 'parallel_id']):
                            print(f"[客户端] ⚠️ 跳过JSON片段: {content[:50]}...")
                        elif content.strip() and len(content.strip()) > 3:  # 只保留有意义的文本
                            # 进一步检查是否为纯文本（包含中文字符或常见英文单词）
                            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content)
                            has_meaningful_english = any(word in content.lower() for word in ['litellm', 'api', 'model', 'text'])
                            
                            if has_chinese or has_meaningful_english:
                                parsed_text_content += content
                                print(f"[客户端] 📝 添加纯文本: {content[:30]}...")
                                print(content, end="", flush=True)
                            else:
                                print(f"[客户端] ⚠️ 跳过无意义内容: {content[:30]}...")
                        else:
                            print(f"[客户端] ⚠️ 跳过短内容: {content}")
                except Exception as e:
                    print(f"[客户端] ⚠️ 解析异常: {str(e)}")
                    # 解析失败时，不添加到解析内容中，避免污染结果
            else:
                print(f"[客户端] ⚠️  chunk.choices[0].delta.content 为 None")
        
        print(f"\n✅ 异步流式请求成功，原始内容长度: {len(collected_content)}")
        print(f"📝 解析后的纯文本内容长度: {len(parsed_text_content)}")
        print(f"📖 完整解析文本（已解码）: {parsed_text_content}")
        
    except Exception as e:
        print(f"❌ 异步流式请求失败: {str(e)}")
    
    print("\n=== 对比总结 ===")
    print("1. AsyncOpenAI 会调用 custom_handler.py 中的 astreaming 方法")
    print("2. OpenAI 会调用 custom_handler.py 中的 streaming 方法")
    print("3. 两者都应该逐个返回SSE数据，而不是一次性返回")
    
    return True

def parse_arguments():
    """
    解析命令行参数
    """
    import argparse
    parser = argparse.ArgumentParser(description="使用OpenAI客户端测试LiteLLM接口")
    parser.add_argument("--test", type=str, choices=['sync', 'async', 'stream', 'models_list', 'models', 'structured', 'sync_vs_async', 'all'],
                        default='async', help="指定要运行的测试类型")
    
    return parser.parse_args()

async def main():
    """
    主函数
    """
    # 设置日志记录
    logger, log_file = get_test_logger()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 使用config目录下的.env文件
    config_env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env")
    if os.path.exists(config_env_file):
        message = f"✅ 使用配置文件: {config_env_file}"
        print(message)
        logger.info(message)
    else:
        message = f"⚠️ 配置文件不存在: {config_env_file}"
        print(message)
        logger.warning(message)
    
    # 根据参数运行指定测试
    if args.test == 'sync':
        success = test_openai_sync_client(logger=logger)
    elif args.test == 'async':
        success = await test_openai_async_client(logger=logger)
    elif args.test == 'stream':
        success = test_openai_stream_client(logger=logger)
    elif args.test == 'models_list':
        success = test_openai_models_list(logger=logger)
    elif args.test == 'models':
        success = test_openai_multiple_models(logger=logger)
    elif args.test == 'structured':
        success = await test_openai_structured_output(logger=logger)
    elif args.test == 'sync_vs_async':
        success = await test_openai_sync_vs_async_comparison(logger=logger)
    else:  # all
        success = await run_all_tests(logger=logger)
    
    # 记录测试会话结束
    logger.info("-" * 50)
    status = "✅ 成功" if success else "❌ 失败"
    logger.info(f"🏁 测试会话结束 - {status} - {datetime.now().strftime('%H:%M:%S')}")
    logger.info("-" * 50)
    logger.info("")  # 空行分隔
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())