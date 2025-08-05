#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试check_yaml.py的功能
"""

import os
import sys
import subprocess
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_check_yaml")

# 导入check_yaml模块
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import check_yaml

def test_valid_yaml():
    """
    测试有效的YAML文件
    """
    logger.info("=== 测试有效的YAML文件 ===")
    
    # 测试文件路径
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
    
    # 测试作为模块导入
    logger.info("测试作为模块导入 - validate_yaml函数")
    try:
        data = check_yaml.validate_yaml(yaml_path, log=True)
        logger.info(f"验证成功，数据: {data}")
    except ValueError as e:
        logger.error(f"验证失败: {e}")
        return False
    
    # 测试check_yaml_file函数
    logger.info("测试check_yaml_file函数")
    success, data, error = check_yaml.check_yaml_file(yaml_path, verbose=False)
    if success:
        logger.info(f"检查成功，数据: {data}")
    else:
        logger.error(f"检查失败: {error}")
        return False
    
    # 测试命令行调用
    logger.info("测试命令行调用")
    check_yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "check_yaml.py"))
    result = subprocess.run([sys.executable, check_yaml_path, yaml_path], 
                           capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("命令行调用成功")
    else:
        logger.error(f"命令行调用失败: {result.stderr}")
        return False
    
    return True

def test_invalid_yaml():
    """
    测试无效的YAML文件
    """
    logger.info("=== 测试无效的YAML文件 ===")
    
    # 创建一个临时的无效YAML文件
    invalid_yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "invalid_test.yaml"))
    with open(invalid_yaml_path, 'w') as f:
        f.write("invalid: - yaml: content")
    
    # 测试作为模块导入
    logger.info("测试作为模块导入 - validate_yaml函数")
    try:
        data = check_yaml.validate_yaml(invalid_yaml_path, log=True)
        logger.error("验证应该失败但成功了")
        os.remove(invalid_yaml_path)  # 清理
        return False
    except ValueError as e:
        logger.info(f"验证正确失败: {e}")
    
    # 测试check_yaml_file函数
    logger.info("测试check_yaml_file函数")
    success, data, error = check_yaml.check_yaml_file(invalid_yaml_path, verbose=False)
    if not success:
        logger.info(f"检查正确失败: {error}")
    else:
        logger.error("检查应该失败但成功了")
        os.remove(invalid_yaml_path)  # 清理
        return False
    
    # 测试命令行调用
    logger.info("测试命令行调用")
    check_yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "check_yaml.py"))
    result = subprocess.run([sys.executable, check_yaml_path, invalid_yaml_path], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.info("命令行调用正确失败")
    else:
        logger.error("命令行调用应该失败但成功了")
        os.remove(invalid_yaml_path)  # 清理
        return False
    
    # 清理临时文件
    os.remove(invalid_yaml_path)
    return True

def main():
    """
    主函数
    """
    logger.info("开始测试check_yaml.py功能")
    
    # 测试有效YAML
    valid_result = test_valid_yaml()
    
    # 测试无效YAML
    invalid_result = test_invalid_yaml()
    
    # 输出总结果
    if valid_result and invalid_result:
        logger.info("所有测试通过！")
        return 0
    else:
        logger.error("测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())