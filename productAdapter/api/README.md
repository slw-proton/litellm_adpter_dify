# API模块说明

## 概述

`productAdapter/api` 模块包含业务API实现和Dify工作流客户端。

## 文件结构

```
productAdapter/api/
├── __init__.py                 # 模块初始化文件
├── business_api_example.py     # 业务API示例实现
├── dify_workflow_client.py     # Dify工作流客户端
├── test_dify_client.py         # Dify客户端测试脚本
└── README.md                   # 本说明文档
```

## 模块说明

### 1. business_api_example.py

业务API示例实现，提供以下功能：

- **POST /api/process**: 处理业务请求，集成Dify工作流
- **GET /models**: 获取可用模型列表
- **GET /health**: 健康检查

**主要特性**：
- 支持Dify工作流集成
- 完整的错误处理
- 详细的日志记录
- 环境变量配置

### 2. dify_workflow_client.py

Dify工作流客户端模块，提供以下功能：

- **run_workflow()**: 运行指定的工作流
- **get_workflow_status()**: 获取工作流执行状态
- **stop_workflow_execution()**: 停止工作流执行
- **health_check()**: 检查Dify API连接状态
- **process_query()**: 处理查询的便捷方法
- **process_query_with_config()**: 带配置检查的查询处理方法（推荐使用）

**主要特性**：
- 完整的错误处理
- 超时控制
- 详细的日志记录
- 类型注解支持
- 便捷的查询处理方法
- 自动配置检查和环境变量支持

## 使用方法

### 导入DifyWorkflowClient

```python
# 相对导入（推荐）
from .dify_workflow_client import DifyWorkflowClient

# 绝对导入
from productAdapter.api.dify_workflow_client import DifyWorkflowClient
```

### 使用示例

```python
# 方法1: 使用带配置检查的便捷方法（推荐）
result = DifyWorkflowClient.process_query_with_config(
    query="用户查询内容"
)

if result["success"]:
    print(f"处理成功: {result['content']}")
    print(f"处理时间: {result['processing_time']:.2f}秒")
else:
    print(f"处理失败: {result['error']}")

# 方法2: 使用便捷方法（需要手动配置）
client = DifyWorkflowClient(
    api_key="your_dify_api_key",
    base_url="https://api.dify.ai/v1"
)

result = client.process_query(
    query="用户查询内容",
    workflow_id="your_workflow_id",
    response_mode="blocking"
)

# 方法3: 分步调用
workflow_result = client.run_workflow(
    workflow_id="your_workflow_id",
    input_data={"querydata": "用户查询"},
    response_mode="blocking"
)

status_result = client.get_workflow_status(
    workflow_run_id=workflow_result["workflow_run_id"]
)
```

## 测试

### 运行Dify客户端测试

```bash
cd productAdapter/api
python test_dify_client.py
```

### 测试内容

1. **模块导入测试**: 验证DifyWorkflowClient模块可以正确导入
2. **初始化测试**: 验证客户端可以正确初始化
3. **方法测试**: 验证所有必需方法都存在

## 配置要求

### 环境变量

确保在 `productAdapter/config/.env` 中设置以下变量：

```bash
# Dify 平台配置
DIFY_API_KEY=your_actual_dify_api_key
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_WORKFLOW_ID=your_actual_workflow_id
```

## 错误处理

### 常见错误

1. **导入错误**: 检查模块路径和依赖
2. **配置错误**: 检查环境变量设置
3. **网络错误**: 检查网络连接和API地址
4. **权限错误**: 检查API密钥权限

### 调试方法

1. 设置日志级别为DEBUG
2. 查看详细错误信息
3. 使用测试脚本验证功能

## 依赖项

- `requests`: HTTP请求库
- `json`: JSON数据处理
- `logging`: 日志记录
- `typing`: 类型注解

## 注意事项

1. **模块导入**: 优先使用相对导入，失败时使用绝对导入
2. **错误处理**: 所有API调用都有完整的错误处理
3. **日志记录**: 详细的操作日志记录
4. **类型安全**: 使用类型注解提高代码质量 