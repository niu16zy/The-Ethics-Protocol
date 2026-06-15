# AI 编码约束文档

适用项目：Logic Fortress: An LLM-powered Ethics Debate Game

本文件用于约束 Codex、Cursor、Claude Code 或其他 AI 编码助手在本项目中的代码生成行为。任何 AI 在生成、修改或重构代码前，都必须优先遵守本文件，并与 `architecture-design.md` 保持一致。

## 1. 项目核心定位

本项目是一个基于 IBM SkillsBuild 课程内容和 LLM 的教育游戏。玩家通过与 NPC 辩论，逐步击破 NPC 的 Logic Fortress。

项目核心不是：

- 普通聊天机器人
- 普通问答系统
- 多项选择测验应用
- 纯展示型 demo

项目核心必须同时包含：

- 游戏化交互
- RAG grounding
- 可解释的 Argument Validation System
- 双层 LLM 架构

## 2. 不可违反的架构约束

### 2.1 双层 LLM 必须分离

系统必须保留两个职责不同的 AI 模块：

- Evaluator Agent：负责基于检索到的课程内容判断玩家论证质量，并输出结构化 JSON
- Persona Agent：只负责将 Evaluator 结果转化为自然语言 NPC 回复

禁止：

- 将两个 Agent 合并成一个通用 Agent
- 让 Persona Agent 重新判断事实或课程内容
- 让 Persona Agent 直接访问知识库并自由解释课程内容
- 让前端直接调用 LLM

### 2.2 前端不得直连大模型

前端只能调用后端 API。所有 LLM provider、prompt、embedding、检索、校验逻辑都必须留在后端。

禁止在前端代码中出现：

- LLM API key
- provider credentials
- direct LLM endpoint
- embedding endpoint
- 检索库直连逻辑

### 2.3 RAG 必须优先于判断

Evaluator Agent 在做判断之前，必须先拿到检索到的课程证据。

如果检索不到足够证据，系统应返回：

- clarification
- low-confidence verdict
- off-topic / unsupported

禁止在缺乏证据时编造评分理由。

### 2.4 结构化输出必须强制

Evaluator Agent 输出必须是 JSON，并经过 schema 校验。

禁止：

- 直接返回自由文本评分
- 用字符串匹配解析模型输出
- 允许缺失关键字段却继续进入业务流程

### 2.5 证据引用必须可追溯

任何 strong 或 partial verdict 必须包含 `evidence_refs`。

最终反馈报告必须能追溯到知识库中的 `topic`、`chunk` 或 `document id`。

### 2.6 密钥与配置安全

任何 API key、LLM provider credential、数据库密码都不得硬编码，也不得提交到仓库。

禁止：

- 在代码中写死 secret
- 将 `.env` 提交到仓库
- 将真实凭证写入 prompt 文件

## 3. 固定技术栈

除非用户明确要求，否则不要随意替换以下主技术栈。

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Zustand
- TanStack Query
- React Router
- Framer Motion

### Backend

- Python 3.12
- FastAPI
- Pydantic v2
- SQLite
- SQLite FTS5
- Pluggable LLM provider client
- pytest

### Evaluation

- gold standard cases
- pytest-based backend checks
- optional RAGAS / evaluation scripts

### RAG 默认实现

- Markdown knowledge base
- 结构化导入
- SQLite FTS5 / BM25 检索
- query expansion 可选
- embedding / vector DB 仅作为增强层

## 4. 检索层约束

### 4.1 默认不用独立向量数据库

当前项目数据量较小，默认不使用 ChromaDB、Qdrant、Milvus 等独立向量数据库。

优先使用：

- 结构化 Markdown
- SQLite FTS5
- BM25
- 轻量 rerank

只有在知识库显著增大、需要复杂混合检索或高并发时，才考虑向量数据库。

### 4.2 Markdown 必须结构化导入

知识库内容必须先解析为结构化字段，再入库。

推荐字段：

- course
- lesson
- topic
- content
- seq_order

禁止把整个 Markdown 文件直接当作一个不可解释的大块文本硬塞给模型。

### 4.3 检索优先策略

检索链路建议为：

1. 结构化导入
2. FTS5/BM25 初筛
3. query expansion
4. top-k 去重与补全
5. 交给 Evaluator

不要一开始就上复杂 multi-stage retrieval 或重型向量系统。

## 5. 数据模型约束

### 5.1 Evaluator 输出必须用类型表达

必须使用 DTO / schema 表达结构化结果。

建议字段：

- match_score
- score_delta
- verdict
- identified_principles
- misconceptions_addressed
- missing_points
- evidence_refs
- reasoning_summary
- persona_instruction
- confidence

### 5.2 Session / Turn 必须可追踪

每轮对话至少保存：

- player_input
- retrieved_refs
- evaluator_json
- npc_response
- meter_before
- meter_after
- timestamp

### 5.3 日志必须脱敏

日志中不得输出：

- API key
- provider token
- 数据库密码
- 原始敏感配置

## 6. 编码风格约束

- 使用明确类型
- 避免大面积 `any` / `object`
- 避免把业务逻辑堆在 controller / route 里
- 复杂逻辑应放在 `service` 层
- Prompt 必须外置，不得散落在业务代码中
- 所有与 LLM 相关的逻辑必须通过统一 client 接口隔离

## 7. 测试要求

以下内容必须有测试或可验证说明：

- DTO / schema 校验
- meter 更新逻辑
- retriever 返回格式
- invalid JSON fallback
- debate turn happy path
- low-confidence path

若引入检索优化、prompt 修改或结构化输出变更，必须同步更新测试用例。

## 8. 禁止事项

AI 编码助手不得：

- 把项目做成普通 chatbot
- 把项目做成普通 quiz app
- 合并 Evaluator Agent 与 Persona Agent
- 让前端直连 LLM
- 硬编码 secret
- 用脆弱字符串匹配替代 schema validation
- 引入不必要的重型基础设施
- 删除或弱化 Argument Validation System
- 绕过 RAG grounding

## 9. 代码生成工作流

AI 每次生成代码前应遵守：

1. 先确认任务属于 frontend、backend、RAG、evaluation 还是 docs
2. 先查看相关目录和已有代码风格
3. 只修改与任务直接相关的文件
4. 新增代码必须符合本约束和架构文档
5. 涉及 API schema、Agent、RAG 的修改必须同步测试
6. 完成后说明修改内容、文件范围和验证结果

## 10. Definition of Done

一次开发任务完成时必须满足：

- 符合固定技术栈
- 不破坏双层 LLM 架构
- 后端 schema 清晰，前端类型明确
- 没有硬编码 secret
- 核心逻辑具备测试或明确的测试计划
- 用户能清楚知道如何运行与验证

## 11. 推荐给 AI 的短提示词

```text
You are coding the Logic Fortress project. Follow AI_CODING_CONSTRAINTS.md and architecture-design.md strictly. Use Python and FastAPI for the backend. Preserve the dual-layer LLM architecture: Evaluator Agent performs RAG-grounded argument validation and returns structured JSON; Persona Agent only turns the evaluator result into NPC dialogue. The default retrieval stack is structured Markdown + SQLite FTS5/BM25, not a standalone vector database. The frontend must never call an LLM directly. Do not hardcode secrets. Keep code scoped, typed, testable, and aligned with the existing project structure.
```
