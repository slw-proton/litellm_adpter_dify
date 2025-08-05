# LiteLLM适配器

这个适配器用于将自定义业务API封装为符合OpenAI API规范的接口，通过LiteLLM代理提供服务。

## 功能特点

- 将业务API的请求和响应转换为OpenAI格式
- 支持自定义模型处理器集成到LiteLLM中
- 提供配置管理功能
- 包含启动LiteLLM代理服务器的脚本

## 目录结构

```
liteLLMAdapter/
├── __init__.py          # 包初始化文件
├── adapter.py           # 适配器核心模块
├── config.py            # 配置管理模块
├── custom_model.py      # 自定义模型处理器
├── example.py           # 示例脚本
├── litellm_integration.py # LiteLLM集成模块
├── start_proxy.py       # 代理启动脚本
└── README.md            # 说明文档
```

## 安装依赖

```bash
# 方法1：直接安装依赖包
pip install litellm openai requests fastapi uvicorn pydantic

# 方法2：从源代码安装（推荐，解决路径问题）
cd /home/slw/dev/trae-litellm/src/liteLLMAdapter
pip install -e .

# 方法3：使用requirements.txt安装
pip install -r requirements.txt
```

## 安装路径问题解决

如果遇到类似 "Location: /home/slw/anaconda3/lib/python3.12/site-packages导致我安装的litellm找不到" 的问题，可以尝试以下解决方案：

1. **使用虚拟环境**：创建并激活一个虚拟环境，然后在虚拟环境中安装依赖
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   pip install -e .
   ```

2. **指定安装路径**：使用`--target`参数指定安装路径
   ```bash
   pip install litellm --target=/path/to/your/project/lib
   ```
   然后在代码中添加路径：
   ```python
   import sys
   sys.path.insert(0, '/path/to/your/project/lib')
   ```

3. **使用`PYTHONPATH`环境变量**：设置`PYTHONPATH`环境变量指向项目目录
   ```bash
   export PYTHONPATH=$PYTHONPATH:/home/slw/dev/trae-litellm/src
   ```

## 使用方法

### 1. 启动LiteLLM代理服务器

```bash
python -m liteLLMAdapter.start_proxy --host 0.0.0.0 --port 8080 --api-base http://localhost:8001/api/process
```

参数说明：
- `--host`: 服务器绑定的主机地址，默认为0.0.0.0
- `--port`: 服务器绑定的端口，默认为8080
- `--config`: LiteLLM配置文件路径（可选）
- `--api-base`: 业务API的基础URL
- `--api-key`: 业务API的认证密钥（可选）

### 2. 使用OpenAI客户端调用

```python
from openai import OpenAI

# 创建OpenAI客户端
client = OpenAI(
    api_key="dummy-key",  # 使用任意值，因为我们的适配器不检查API密钥
    base_url="http://localhost:8080/v1"  # LiteLLM代理的URL
)

# 发送请求
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "请用一句话介绍人工智能。"}
    ]
)

# 打印响应
print(response)
```

### 3. 直接使用适配器

```python
from liteLLMAdapter.adapter import LiteLLMAdapter

# 创建适配器
api_base_url = "http://localhost:8001/api/process"
adapter = LiteLLMAdapter(api_base_url)

# 构建OpenAI格式的请求
openai_request = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "你好，请介绍一下自己。"}
    ]
}

# 处理请求
response = adapter.handle_chat_completion(openai_request)

# 打印响应
print(response)
```

## 环境变量

- `BUSINESS_API_URL`: 业务API的基础URL，默认为http://localhost:8001/api/process
- `BUSINESS_API_KEY`: 业务API的认证密钥（可选）
- `DEFAULT_MODEL`: 默认模型名称，默认为gpt-3.5-turbo

## 示例

运行示例脚本：

```bash
python -m liteLLMAdapter.example
```

## 业务API格式

### 请求格式

```json
{
  "query": "用户输入的文本",
  "response_type": "text",
  "stream": false,
  "model_info": {
    "name": "gpt-3.5-turbo"
  }
}
```

### 响应格式

```json
{
  "response_id": "unique-id",
  "content": "响应内容",
  "timestamp": 1234567890,
  "processing_time": 0.5
}
```

## 注意事项

1. 确保业务API已经启动并可访问
2. 适配器目前支持非流式响应，流式响应需要进一步实现
3. 适配器会模拟token使用量，实际应用中可能需要从业务API获取准确的token使用量
4. 如果遇到模块导入或路径问题，请参考[安装路径问题解决](#安装路径问题解决)部分
5. 建议使用虚拟环境进行开发和部署，避免包冲突和路径问题