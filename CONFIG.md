# LLM Council 配置说明

本文档详细说明 LLM Council 项目的配置文件结构和各配置项的含义。

---

## 快速开始

1. **复制示例配置**
   ```bash
   cp config.example.json config.json
   ```

2. **设置 API Key**
   在 `.env` 文件中添加：
   ```
   OPENROUTER_API_KEY=sk-or-your-key-here
   ```

3. **启动服务**
   ```bash
   python -m backend.main
   ```

---

## 配置文件优先级

系统按以下优先级加载配置（高到低）：

1. **环境变量** `LLM_COUNCIL_CONFIG_PATH` - 指定的配置文件路径
2. **config.local.json** - 本地开发配置（不会被git跟踪）
3. **config.json** - 默认配置文件
4. **内置默认值** - 代码中的 `DEFAULT_CONFIG`

---

## 配置文件结构

```json
{
  "version": "1.0.0",
  "providers": { ... },
  "storage": { ... },
  "server": { ... }
}
```

---

## 配置项详解

### version

配置版本号，用于未来的迁移和兼容性检查。

```json
"version": "1.0.0"
```

---

### providers

LLM服务提供商配置。可以配置多个提供商（如 openrouter、openai、anthropic），每个提供商可以独立启用/禁用。

#### providers.*.enabled

是否启用该提供商。

```json
"enabled": true   // 启用
"enabled": false  // 禁用
```

#### providers.*.api_url

API 端点 URL。不同提供商有不同的地址：

- OpenRouter: `https://openrouter.ai/api/v1/chat/completions`
- OpenAI: `https://api.openai.com/v1/chat/completions`
- Anthropic: `https://api.anthropic.com/v1/messages`

#### providers.*.api_key_env

存储 API Key 的环境变量名称。实际密钥值应存储在 `.env` 文件中，不要直接写入 JSON。

```json
"api_key_env": "OPENROUTER_API_KEY"
```

对应的 `.env` 文件：
```
OPENROUTER_API_KEY=sk-or-xxx
```

#### providers.*.models

该提供商下可用的模型配置。

##### providers.*.models.council

委员会成员模型列表。这些模型会在：
- **第一阶段**：独立回答用户问题
- **第二阶段**：对其他模型的答案进行评估和排名

```json
"council": [
  "openai/gpt-5.1",
  "google/gemini-3-pro-preview",
  "anthropic/claude-sonnet-4.5",
  "x-ai/grok-4"
]
```

##### providers.*.models.chairman

主席模型，负责在**第三阶段**综合所有答案和排名，给出最终结论。

```json
"chairman": "google/gemini-3-pro-preview"
```

##### providers.*.models.title_generator

标题生成模型，用于为新对话生成简短标题。建议使用快速、便宜的模型。

```json
"title_generator": "google/gemini-2.5-flash"
```

---

### storage

数据存储配置。

#### storage.type

存储类型：
- `"json"` - 文件存储（当前支持）
- `"database"` - 数据库存储（未来计划）

```json
"type": "json"
```

#### storage.data_dir

对话数据存储目录路径。

```json
"data_dir": "data/conversations"
```

---

### server

后端服务器配置。

#### server.host

服务器监听地址。

- `"0.0.0.0"` - 监听所有网络接口（生产环境）
- `"127.0.0.1"` - 仅本地访问（开发环境）

```json
"host": "0.0.0.0"
```

#### server.port

服务器端口号。注意：前端 `api.js` 中的端口需要与此保持一致。

```json
"port": 8001
```

#### server.cors_origins

允许跨域访问的前端地址列表。

```json
"cors_origins": [
  "http://localhost:5173",
  "http://localhost:3000"
]
```

---

## 完整配置示例

```json
{
  "version": "1.0.0",
  "providers": {
    "openrouter": {
      "enabled": true,
      "api_url": "https://openrouter.ai/api/v1/chat/completions",
      "api_key_env": "OPENROUTER_API_KEY",
      "models": {
        "council": [
          "openai/gpt-5.1",
          "google/gemini-3-pro-preview",
          "anthropic/claude-sonnet-4.5",
          "x-ai/grok-4"
        ],
        "chairman": "google/gemini-3-pro-preview",
        "title_generator": "google/gemini-2.5-flash"
      }
    }
  },
  "storage": {
    "type": "json",
    "data_dir": "data/conversations"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8001,
    "cors_origins": [
      "http://localhost:5173",
      "http://localhost:3000"
    ]
  }
}
```

---

## 多提供商支持

配置支持同时启用多个提供商。只需在 `providers` 中添加新的提供商条目并设置 `enabled: true`：

```json
{
  "providers": {
    "openrouter": {
      "enabled": true,
      ...
    },
    "openai": {
      "enabled": true,
      "api_url": "https://api.openai.com/v1/chat/completions",
      "api_key_env": "OPENAI_API_KEY",
      ...
    }
  }
}
```

注意：目前系统默认使用第一个启用的提供商。多提供商混合使用功能正在开发中。

---

## 本地开发配置

对于本地开发，可以创建 `config.local.json` 覆盖默认配置：

```json
{
  "version": "1.0.0",
  "providers": {
    "openrouter": {
      "enabled": true,
      "api_url": "http://localhost:8080/api/v1/chat/completions",
      "api_key_env": "OPENROUTER_API_KEY",
      ...
    }
  },
  "server": {
    "port": 8002
  }
}
```

`config.local.json` 已被添加到 `.gitignore`，不会被提交到版本控制。

---

## 常见问题

### Q: 修改配置后需要重启服务吗？

A: 是的，配置在服务启动时加载，修改后需要重启才能生效。

### Q: 如何验证配置文件格式是否正确？

A: 可以使用 JSON 验证工具或命令：
```bash
python -m json.tool config.json
```

### Q: API Key 存在哪里安全？

A: API Key 应该存储在 `.env` 文件中（已加入 `.gitignore`），配置文件中只引用环境变量名。

### Q: 如何添加新的模型提供商？

A: 在 `providers` 中添加新的提供商条目，参考 `config.example.json` 中的示例。
