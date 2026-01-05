# LLM Council

![llmcouncil](header.jpg)

---

[English](README.md) | [中文](README.zh.md)

---

这个项目的想法是，与其向你最喜欢的大语言模型提供商（如 OpenAI GPT-5.1、Google Gemini 3.0 Pro、Anthropic Claude Sonnet 4.5、xAI Grok 4 等）提问，不如将它们组织成你的"LLM 议会"。这是一个简单的本地 Web 应用，看起来基本上像 ChatGPT，不同的是它使用多个 LLM 提供商将你的查询发送给多个 LLM，然后让它们相互评审和排名，最后由主席 LLM 生成最终回答。

详细来说，当你提交查询时会发生以下情况：

1. **阶段 1：初步意见**。将用户查询分别发送给所有 LLM，收集各自的响应。单个响应以"标签页视图"显示，方便用户逐一查看。
2. **阶段 2：评审**。每个单独的 LLM 会收到其他 LLM 的响应。在底层，LLM 身份被匿名化，以便 LLM 在评判输出时不会偏袒。要求 LLM 按准确性和洞察力进行排名。
3. **阶段 3：最终响应**。LLM 议会的指定主席综合所有模型的响应，编译成呈现给用户的单一最终答案。

## Vibe Code 警告

这个项目 99% 是 vibe code 出来的，作为一个有趣的周六黑客项目，因为我想在[与 LLM 一起阅读书籍](https://x.com/karpathy/status/1990577951671509438)的过程中并排探索和评估多个 LLM。并排查看多个响应以及所有 LLM 对彼此输出的交叉意见是很好的，也是有用的。我不会以任何方式支持它，这里按原样提供，供其他人启发，我不打算改进它。代码现在是暂时的，库已经结束了，让你的 LLM 以任何你喜欢的方式改变它。

## 设置

### 1. 安装依赖

项目使用 [uv](https://docs.astral.sh/uv/) 进行项目管理。

**后端：**
```bash
uv sync
```

**前端：**
```bash
cd frontend
npm install
cd ..
```

### 2. 配置 API 密钥

在项目根目录创建 `.env` 文件：

```bash
# OpenRouter API 密钥
OPENROUTER_API_KEY=your-api-key-here

# SiliconFlow API 密钥（可选，用于使用 SiliconFlow 提供商）
SILICONFLOW_API_KEY=your-api-key-here
```

获取你的 API 密钥：
- [OpenRouter](https://openrouter.ai/) - 确保购买你需要的额度，或注册自动充值
- [SiliconFlow](https://siliconflow.cn/) - 注册并获取你的 API 密钥

### 3. 配置模型（可选）

编辑 `config/config.json` 来自定义议会并选择你的活动提供商：

```json
{
  "active_provider": "openrouter",
  "providers": {
    "openrouter": {
      "enabled": true,
      "api_url": "https://openrouter.ai/api/v1/chat/completions",
      "api_key_env": "OPENROUTER_API_KEY",
      "models": {
        "council": [
          "openai/gpt-4o",
          "google/gemini-2.5-pro-preview-03-25",
          "anthropic/claude-3-5-sonnet-20241022"
        ],
        "chairman": "google/gemini-2.5-pro-preview-03-25",
        "title_generator": "google/gemini-2.5-flash"
      }
    },
    "siliconflow": {
      "enabled": true,
      "api_url": "https://api.siliconflow.cn/v1/chat/completions",
      "api_key_env": "SILICONFLOW_API_KEY",
      "models": {
        "council": [
          "Qwen/Qwen2.5-72B-Instruct",
          "deepseek-ai/DeepSeek-V3"
        ],
        "chairman": "Qwen/Qwen2.5-72B-Instruct",
        "title_generator": "Qwen/Qwen2.5-7B-Instruct"
      }
    }
  }
}
```

**配置选项：**
- `active_provider`：使用的提供商（例如 `openrouter`、`siliconflow`）
- `council`：议会中的模型列表
- `chairman`：综合最终答案的模型
- `title_generator`：用于生成对话标题的模型

## 运行应用

**方式 1：使用启动脚本**
```bash
./start.sh
```

**方式 2：手动运行**

终端 1（后端）：
```bash
uv run python -m backend.main
```

终端 2（前端）：
```bash
cd frontend
npm run dev
```

然后在浏览器中打开 http://localhost:5173。

## 技术栈

- **后端：** FastAPI (Python 3.10+)、异步 httpx、OpenRouter/SiliconFlow API
- **前端：** React + Vite、react-markdown 用于渲染
- **存储：** `data/conversations/` 中的 JSON 文件
- **包管理：** uv 用于 Python，npm 用于 JavaScript
