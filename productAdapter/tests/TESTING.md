## 测试说明（Tests Guide）

本说明文档介绍如何在本项目中运行各类测试，尤其是图片生成功能的测试。所有命令均在项目根目录执行。

### 准备工作

- 可选：配置 `productAdapter/config/.env`（推荐），或使用环境变量覆盖。
- 启动业务 API（用于 HTTP 模式联调）：

```bash
python -m productAdapter.api.business_api_example --host 0.0.0.0 --port 8002
```

### 一、图片接口直连测试（不依赖 LiteLLM）

脚本：`productAdapter/tests/test_image_api.py`

1) 本地直接调用（使用 FastAPI TestClient，无需启动服务）
```bash
python -m productAdapter.tests.test_image_api --prompt "a cute cat" --n 1 --size 1024x1024
```

2) HTTP 调用（需先启动业务 API）
```bash
python -m productAdapter.tests.test_image_api --http --base-url http://localhost:8002 \
  --prompt "a cute cat" --n 1 --size 1024x1024
```

可选参数：`--model`、`--response-format (url|b64_json)`、`--out <file>`。

### 二、通过 OpenAI 客户端测试（经由 LiteLLM 接口）

脚本：`productAdapter/tests/test_openai_client.py`

- 同步图片测试
```bash
python -m productAdapter.tests.test_openai_client --test image_sync
```

- 异步图片测试
```bash
python -m productAdapter.tests.test_openai_client --test image_async
```

- 同步 + 异步
```bash
python -m productAdapter.tests.test_openai_client --test image_all
```

该脚本会读取下述环境变量并覆盖默认值：

- 业务 API：
  - `BUSINESS_API_BASE_URL`（默认 `http://localhost:8002`）
  - `IMAGE_MODEL`（默认 `business-api-image`）
  - `IMAGE_PROMPT`（默认 `a cute cat sitting on a chair`）
  - `IMAGE_N`（默认 `1`）
  - `IMAGE_SIZE`（默认 `1024x1024`）
  - `IMAGE_FORMAT`（`url` 或 `b64_json`，默认 `url`）

- LiteLLM 网关（仅当你需要经 LiteLLM 代理时）：
  - `LITELLM_PROXY_HOST`、`LITELLM_PROXY_PORT`

### 三、服务端图片生成配置（Dify / LLM）

- Dify 工作流（用于图片生成）：
  - `DIFY_BASE_URL`
  - `DIFY_PPT_IMAGE_API_KEY`
  - `DIFY_PPT_IMAGE__WORKFLOW_ID`

- 直连 LLM 图片生成（可选）：
  - `ENABLE_LITELLM_IMAGE`（`true|false`）
  - `LITELLM_IMAGE_MODEL`（如 `openai/gpt-image-1`）

### 四、生产/联调环境回退策略

- 生产默认禁用图片占位回退：
  - `ENVIRONMENT=production`（或 `prod`）下强制禁用回退
  - 失败将直接抛错，由 API 层返回 5xx/业务错误码

- 非生产或联调可启用占位回退：
  - `IMAGE_MOCK_FALLBACK_ENABLED=true`
  - `MOCK_IMAGE_BASE_URL`（URL 占位域名，默认 `https://picsum.photos`）

示例（联调 b64_json 占位回退）：
```bash
ENVIRONMENT=dev IMAGE_MOCK_FALLBACK_ENABLED=true IMAGE_FORMAT=b64_json \
python -m productAdapter.tests.test_openai_client --test image_sync
```

### 五、其他测试项（示例）

- 聊天/流式/模型列表等：
```bash
python -m productAdapter.tests.test_openai_client --test sync
python -m productAdapter.tests.test_openai_client --test async
python -m productAdapter.tests.test_openai_client --test stream
python -m productAdapter.tests.test_openai_client --test models_list
```

### 六、日志与排查

- 日志默认输出在 `logs/YYYY/MM/DD/*.log`。
- 关注：`business_api.log`、`image_generation_service.log`、`test_openai_client.log`。

若需要将测试响应保存到文件，使用 shell 重定向：
```bash
python -m productAdapter.tests.test_openai_client --test image_sync > /tmp/image_test.log
```




