# Dify 工作流集成配置

## 概述

本系统已集成Dify工作流API，可以通过环境变量配置来使用Dify平台的工作流功能。

## 配置步骤

### 1. 创建环境配置文件

复制示例配置文件：
```bash
cp productAdapter/config/env.example productAdapter/config/.env
```

### 2. 配置Dify参数

编辑 `productAdapter/config/.env` 文件，设置以下参数：

```bash
# Dify 平台配置
DIFY_API_KEY=your_actual_dify_api_key
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_WORKFLOW_ID=your_actual_workflow_id
```

### 3. 获取Dify配置信息

#### API密钥 (DIFY_API_KEY)
1. 登录Dify平台
2. 进入应用设置
3. 在API密钥部分获取或创建新的API密钥

#### 工作流ID (DIFY_WORKFLOW_ID)
1. 在Dify平台创建工作流
2. 复制工作流的ID（通常在URL中可以看到）

## 工作流程

### 1. 请求处理流程
```
用户请求 → /api/process → Dify工作流API → 获取执行状态 → 返回结果
```

### 2. 数据流
1. **输入**: 用户查询通过 `querydata` 字段传递给Dify工作流
2. **处理**: Dify工作流执行并生成结果
3. **输出**: 从 `data.outputs` 中提取 `querydata` 字段作为响应内容

### 3. 错误处理
- 配置不完整：返回配置错误信息
- 工作流执行失败：返回错误详情
- 网络问题：返回网络错误信息

## API接口说明

### POST /api/process

**请求格式**:
```json
{
  "query": "用户查询内容",
  "model_info": {"name": "model-name"},
  "response_type": "text",
  "stream": false
}
```

**响应格式**:
```json
{
  "response_id": "resp-xxx",
  "content": "Dify工作流返回的内容",
  "timestamp": 1234567890,
  "processing_time": 0.123
}
```

## 日志记录

系统会记录以下关键信息：
- Dify API调用日志
- 工作流执行状态
- 错误信息和异常处理
- 响应内容摘要

## 故障排除

### 常见问题

1. **配置错误**
   - 检查API密钥是否正确
   - 确认工作流ID是否存在
   - 验证API基础URL

2. **网络问题**
   - 检查网络连接
   - 确认防火墙设置
   - 验证DNS解析

3. **权限问题**
   - 确认API密钥有足够权限
   - 检查工作流访问权限

### 调试模式

设置日志级别为DEBUG以获取详细信息：
```bash
LOG_LEVEL=DEBUG
```

## 测试和验证

### 运行Dify集成测试
```bash
# 启动服务并运行Dify集成测试
./start_with_logging.sh --test-dify

# 或者只启动服务
./start_with_logging.sh
```

### 手动测试
```bash
# 测试业务API
curl -X POST http://localhost:8002/api/process \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "你好，请介绍一下Dify平台",
    "model_info": {"name": "dify-workflow-model"},
    "response_type": "text"
  }'

# 测试LiteLLM代理
curl -X POST http://localhost:8080/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "my-custom-model",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 示例配置

完整的 `.env` 文件示例：
```bash
# Dify 平台配置
DIFY_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_WORKFLOW_ID=5EZwtE7Wu86mBpTo

# 业务 API 配置
BUSINESS_API_URL=http://localhost:8002/api/process
BUSINESS_API_KEY=
DEFAULT_MODEL=dify-workflow-model

# LiteLLM 代理服务器配置
LITELLM_PROXY_HOST=0.0.0.0
LITELLM_PROXY_PORT=8080

# 日志级别配置
LOG_LEVEL=INFO
``` 