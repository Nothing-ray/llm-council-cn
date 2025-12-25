# CLAUDE.md - LLM Council的技术说明

该文件包含了技术细节、架构决策以及未来开发会议的重要实施注意事项。

## 项目概述

LLM Council是一个分三个阶段的审议系统，多个大型语言模型（LLMs）通过该系统协作回答用户的问题。关键的创新在于第二阶段的匿名同行评审机制，这可以防止模型偏袒某些答案。

## 架构

### 后端结构（`backend/`）

**`config.py`**
- 包含`COUNCIL_MODELS`（OpenRouter模型标识符列表）
- 包含`CHAIRMAN_MODEL`（合成最终答案的模型）
- 使用来自`.env`文件的环境变量`OPENROUTER_API_KEY`
- 后端运行在**端口8001**上（而不是8000，因为用户已经在8000端口上运行了另一个应用程序）

**`openrouter.py`
- `query_model()`：单个异步模型查询
- `query_models_parallel()`：使用`asyncio.gather()`进行并行查询
- 返回包含“content”和可选“reasoning_details”的字典
- 优雅的降级处理：失败时返回None，继续处理成功的响应

**`council.py`** - 核心逻辑
- `stage1_collect_responses()`：向所有模型并行发送查询
- `stage2_collect_rankings()`：
  - 将响应匿名化为“Response A, B, C等”
  - 创建`label_to_model`映射以便后续去匿名化
  - 提示模型进行评估和排名（有严格的格式要求）
  - 返回元组：(rankings_list, label_to_model_dict)
  - 每个排名包含原始文本和`parsed_ranking`列表
- `stage3_synthesize_final()`：主席模型根据所有响应和排名结果合成最终答案
- `parse_ranking_from_text()`：提取“FINAL RANKING:”部分，支持数字列表和纯文本格式
- `calculate_aggregate_rankings()`：计算所有模型评估的平均排名位置

**`storage.py`
- 基于JSON的对话存储在`data/conversations/`目录下
- 每个对话的结构为：`{id, created_at, messages[]}`
- 助手模型的消息包含：`{role, stage1, stage2, stage3}`
- 注意：元数据（label_to_model, aggregate_rankings）不会持久化到存储中，仅通过API返回

**`main.py`
- 快速API应用，启用CORS，支持本地地址localhost:5173和localhost:3000
- POST `/api/conversations/{id}/message`接口除了返回对话阶段信息外，还返回元数据
- 元数据包括：label_to_model映射和aggregate_rankings

### 前端结构（`frontend/src/`）

**`App.jsx`
- 主要协调功能：管理对话列表和当前对话
- 处理消息发送和元数据存储
- 重要提示：元数据存储在UI状态中以供显示，但不会持久化到后端JSON中

**`components/ChatInterface.jsx`
- 多行文本区域（3行，可调整大小）
- 按Enter键发送消息，按Shift+Enter键换行
- 用户消息使用markdown-content类进行格式化

**`components/Stage1.jsx`
- 以标签页形式显示每个模型的响应
- 使用ReactMarkdown渲染，并带有markdown-content包装器

**`components/Stage2.jsx**
- **关键功能**：以标签页形式显示每个模型的原始评估文本
- 去匿名化操作在客户端完成（模型接收匿名标签）
- 在每个评估结果下方显示“Extracted Ranking”以便用户验证解析结果
- 显示总体排名、平均位置和投票数
- 说明性文本指出加粗的模型名称仅用于提高可读性

**`components/Stage3.jsx**
- 主席模型合成的最终答案
- 背景颜色为绿色（#f0fff0）以突出显示结论

**样式（`.css`）
- 使用浅色模式（非深色模式）
- 主要颜色：#4a90e2（蓝色）
- 在`index.css`中使用`.markdown-content`类进行全局markdown样式设置
- 所有markdown内容周围有12px的间距，以避免显示混乱

## 关键设计决策

### 第二阶段提示格式
第二阶段的提示格式非常具体，以确保输出可以被正确解析：
```
1. 首先分别评估每个响应
2. 添加“FINAL RANKING:”标题
3. 使用数字列表格式：“1. Response C”，“2. Response A”等
4. 排名部分之后没有额外的文本
```
这种严格的格式既保证了解析的可靠性，又能获得有深度的评估结果。

### 去匿名化策略
- 模型接收的标签为：“Response A”，“Response B”等
- 后端创建映射：`{"Response A": "openai/gpt-5.1", ...}`）
- 前端以**粗体**显示模型名称以便阅读
- 用户会看到说明，知道原始评估使用了匿名标签
- 这种方式可以在保持透明度的同时防止偏见

### 错误处理原则
- 如果某些模型失败，继续处理成功的响应（优雅降级）
- 单个模型失败不会导致整个请求失败
- 记录错误，但除非所有模型都失败，否则不会向用户显示错误信息

### UI/UX透明度
- 所有原始输出都可以通过标签页查看
- 解析后的排名结果显示在原始文本下方以供验证
- 用户可以验证系统对模型输出的解释
- 这有助于建立信任并便于调试边缘情况

## 重要实施细节

### 相对导入
所有后端模块都使用相对导入（例如，`from .config import ...`），而不是绝对导入。这对于在`python -m backend.main`模式下正确运行Python的模块系统至关重要。

### 端口配置
- 后端：8001（从8000更改为8001以避免冲突）
- 前端：5173（Vite的默认端口）
- 如果需要更改，请更新`backend/main.py`和`frontend/src/api.js`

### Markdown渲染
所有ReactMarkdown组件都必须使用`<div className="markdown-content">`进行包裹，以确保正确的间距。这个类在`index.css`中全局定义。

### 模型配置
模型在`backend/config.py`中进行了硬编码。主席模型可以与其他模型相同或不同。目前的默认设置是根据用户偏好选择Gemini模型作为主席模型。

## 常见问题

1. **模块导入错误**：始终从项目根目录运行`python -m backend.main`，而不是从backend目录运行
2. **CORS问题**：前端必须在`main.py`的CORS中间件中设置允许的来源地址
3. **排名解析失败**：如果模型不遵循格式，备用正则表达式会按顺序提取任何“Response X”模式
4. **缺少元数据**：元数据是临时性的（不会持久化），仅在API响应中提供

## 未来改进计划

- 通过UI而不是配置文件来配置委员会成员/主席模型
- 实现响应的流式传输而不是批量加载
- 将对话导出为markdown/PDF格式
- 随时间分析模型性能
- 定义自定义的排名标准（不仅仅是准确性/洞察力）
- 支持需要特殊处理的推理模型（如o1等）

## 测试说明

在将模型添加到委员会之前，使用`test_openrouter.py`来验证API连接性和测试不同的模型标识符。该脚本可以测试流式和非流式传输模式。

## 数据流概览

```
用户查询
    ↓
第一阶段：并行查询 → [单个模型响应]
    ↓
第二阶段：匿名化 → 并行排名查询 → [评估结果 + 解析后的排名]
    ↓
计算总体排名 → [按平均位置排序]
    ↓
第三阶段：主席模型根据完整上下文合成最终答案
    ↓
返回：{stage1, stage2, stage3, metadata}
    ↓
前端：通过标签页显示结果 + 提供验证UI
```

整个流程尽可能采用异步/并行方式，以最小化延迟。