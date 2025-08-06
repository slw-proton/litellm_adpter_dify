#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
演示Python中的几种日志记录方式
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any

def demo_method_1_basic_logging():
    """方案1: 基础日志配置 - 同时输出到控制台和文件"""
    print("\n=== 方案1: 基础日志配置 ===")
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 配置日志
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/demo_basic_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # 控制台
            logging.FileHandler(log_file, encoding='utf-8')  # 文件
        ],
        force=True  # 强制重新配置
    )
    
    logger = logging.getLogger('demo1')
    
    # 测试日志输出
    base_url = "http://localhost:8080"
    logger.info(f"LiteLLM代理地址: {base_url}")
    logger.info("开始测试模型列表...")
    logger.info("✅ 测试成功完成")
    
    print(f"📄 日志已保存到: {log_file}")
    return log_file

def demo_method_2_custom_logger():
    """方案2: 自定义日志器 - 支持不同级别和格式"""
    print("\n=== 方案2: 自定义日志器 ===")
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 创建自定义日志器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/demo_custom_{timestamp}.log"
    
    # 创建日志器
    logger = logging.getLogger('test_openai_client')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 测试不同级别的日志
    base_url = "http://localhost:8080"
    logger.debug(f"调试信息: 准备连接到 {base_url}")
    logger.info(f"LiteLLM代理地址: {base_url}")
    logger.warning("这是一个警告信息")
    logger.error("这是一个错误信息")
    
    print(f"📄 日志已保存到: {log_file}")
    return log_file

def demo_method_3_json_logging():
    """方案3: JSON格式日志记录"""
    print("\n=== 方案3: JSON格式日志 ===")
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/demo_json_{timestamp}.log"
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            return json.dumps(log_entry, ensure_ascii=False)
    
    # 创建日志器
    logger = logging.getLogger('json_logger')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # 文件处理器 (JSON格式)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # 控制台处理器 (普通格式)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # 测试日志输出
    base_url = "http://localhost:8080"
    logger.info(f"LiteLLM代理地址: {base_url}")
    logger.info("JSON格式日志测试")
    
    print(f"📄 JSON日志已保存到: {log_file}")
    return log_file

def demo_method_4_context_manager():
    """方案4: 使用上下文管理器的日志记录"""
    print("\n=== 方案4: 上下文管理器日志 ===")
    
    class LogContext:
        def __init__(self, log_file):
            self.log_file = log_file
            self.logger = None
            
        def __enter__(self):
            # 创建日志器
            self.logger = logging.getLogger('context_logger')
            self.logger.setLevel(logging.INFO)
            self.logger.handlers.clear()
            
            # 配置处理器
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # 文件处理器
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            self.logger.info("=== 开始日志记录会话 ===")
            return self.logger
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.logger:
                self.logger.info("=== 结束日志记录会话 ===")
                # 清理处理器
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
    
    # 使用上下文管理器
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/demo_context_{timestamp}.log"
    
    with LogContext(log_file) as logger:
        base_url = "http://localhost:8080"
        logger.info(f"LiteLLM代理地址: {base_url}")
        logger.info("使用上下文管理器记录日志")
        logger.info("自动管理日志器生命周期")
    
    print(f"📄 上下文日志已保存到: {log_file}")
    return log_file

def demo_method_5_print_and_log():
    """方案5: print + 文件写入的简单组合"""
    print("\n=== 方案5: print + 文件写入 ===")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/demo_simple_{timestamp}.log"
    
    def log_print(message, level="INFO"):
        """同时打印到控制台和写入文件"""
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp_str} - {level} - {message}"
        
        # 打印到控制台
        print(message)
        
        # 写入文件
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    # 使用示例
    base_url = "http://localhost:8080"
    log_print(f"LiteLLM代理地址: {base_url}")
    log_print("这是一个简单的日志方案")
    log_print("⚠️ 这是警告信息", "WARNING")
    log_print("❌ 这是错误信息", "ERROR")
    
    print(f"📄 简单日志已保存到: {log_file}")
    return log_file

def demo_method_6_daily_append():
    """方案6: 按日期追加日志 - 当日所有测试记录在同一文件"""
    print("\n=== 方案6: 按日期追加日志 ===")
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 按日期命名文件
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = f"logs/daily_test_{date_str}.log"
    
    # 检查是否为当日首次运行
    is_new_file = not os.path.exists(log_file)
    
    # 配置日志器
    logger = logging.getLogger('daily_logger')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # 文件处理器（追加模式）
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)
    
    # 添加会话分隔符
    if is_new_file:
        logger.info("=" * 60)
        logger.info(f"📅 {datetime.now().strftime('%Y年%m月%d日')} 测试日志开始")
        logger.info("=" * 60)
    else:
        logger.info("-" * 40)
        logger.info(f"🔄 新测试会话 - {datetime.now().strftime('%H:%M:%S')}")
        logger.info("-" * 40)
    
    # 记录测试内容
    base_url = "http://localhost:8080"
    logger.info(f"LiteLLM代理地址: {base_url}")
    logger.info("演示按日期追加的日志记录")
    
    # 会话结束
    logger.info("-" * 40)
    logger.info(f"✅ 会话结束 - {datetime.now().strftime('%H:%M:%S')}")
    logger.info("-" * 40)
    logger.info("")  # 空行分隔下次运行
    
    print(f"📄 当日日志文件: {log_file}")
    print(f"📊 文件模式: {'新建' if is_new_file else '追加'}")
    return log_file

def main():
    """演示所有日志记录方案"""
    print("🚀 Python日志记录方案演示")
    
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 演示各种方案
    files = []
    
    try:
        files.append(demo_method_1_basic_logging())
        files.append(demo_method_2_custom_logger()) 
        files.append(demo_method_3_json_logging())
        files.append(demo_method_4_context_manager())
        files.append(demo_method_5_print_and_log())
        files.append(demo_method_6_daily_append())  # 新增
        
        print(f"\n✅ 演示完成！生成了 {len(files)} 个日志文件：")
        for i, file in enumerate(files, 1):
            print(f"  {i}. {file}")
            
        print(f"\n💡 提示：方案6支持当日追加，多次运行会追加到同一文件")
        print(f"   今天的日志文件: logs/daily_test_{datetime.now().strftime('%Y%m%d')}.log")
            
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")

if __name__ == "__main__":
    main()