# The Ethics Protocol

一个以 AI 伦理为主题的互动辩论游戏。玩家扮演“算法审计局”的高级审计员，在三段赛博朋克剧情中引用证据、构建论点，并说服不同立场的角色暂停不安全的生成式 AI 部署。

## 功能

- 三个可独立进入的剧情关卡：招聘公平、城市数据隐私与医疗 AI 安全。
- 基于本地知识库的证据检索，帮助玩家围绕偏见、透明度、隐私、人类监督和安全保障进行论证。
- LLM 驱动的论点评估与 NPC 人格化回复；未配置模型服务时可使用规则回退。
- 对话上下文、回合记录、进度与堡垒值持久化到 SQLite。
- 流式回合接口，前端可依次展示检索、评估和 NPC 回复状态。
- 内置单元测试与检索、进度、延迟、降级评估脚本。

## 技术栈

- 前端：React 18、TypeScript、Vite、Tailwind CSS、Zustand、TanStack Query
- 后端：Python、FastAPI、Pydantic、SQLite
- 模型服务：Groq Chat Completions 或兼容 OpenAI Responses API 的 Fox 网关

## 项目结构

```text
.
├── backend/                 # FastAPI 服务、业务逻辑、提示词与关卡配置
├── frontend/                # React/Vite 游戏界面与场景资源
├── tests/                   # 后端单元与 API 测试
├── evaluation/              # 检索、进度、延迟、降级评估脚本及结果
├── course_content.db        # 已提交的伦理知识库
└── logic_fortress_app.db    # 本地运行时产生的游戏数据（已忽略）
```

## 快速开始

### 1. 准备环境

- Python 3.11 或更高版本
- Node.js 18 或更高版本

在项目根目录创建并激活虚拟环境，然后安装后端依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi "uvicorn[standard]" pydantic pytest httpx
```

安装前端依赖：

```powershell
cd frontend
npm install
cd ..
```

### 2. 配置模型服务

在根目录创建 `.env`。没有可用密钥时，设置 `LOGIC_FORTRESS_LLM_PROVIDER=rules` 即可使用内置规则回退。

```dotenv
# 使用 Groq
LOGIC_FORTRESS_LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# 或使用兼容 OpenAI Responses API 的 Fox 网关
# LOGIC_FORTRESS_LLM_PROVIDER=fox
# FOX_API_KEY=your_api_key
# FOX_MODEL=gpt-5.5
# FOX_BASE_URL=https://code.newcli.com/codex/v1

# 不配置模型服务时使用规则回退
# LOGIC_FORTRESS_LLM_PROVIDER=rules
```

其他可选配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GROQ_TIMEOUT_SECONDS` | `90` | Groq 请求超时秒数 |
| `GROQ_MAX_OUTPUT_TOKENS` | `700` | 单次模型输出上限 |
| `LOGIC_FORTRESS_LLM_MAX_ATTEMPTS` | `2` | 模型调用最大尝试次数 |
| `FOX_REASONING_EFFORT` | `high` | Fox 模型推理强度 |
| `LOGIC_FORTRESS_KNOWLEDGE_DB` | `course_content.db` | 知识库 SQLite 文件路径 |
| `LOGIC_FORTRESS_APP_DB` | `logic_fortress_app.db` | 游戏数据 SQLite 文件路径 |

请勿提交 `.env` 或任何 API 密钥。

### 3. 启动应用

在项目根目录启动后端：

```powershell
python -m uvicorn backend.app.main:app --reload
```

另开一个终端启动前端：

```powershell
cd frontend
npm run dev
```

打开 Vite 命令输出的本地地址（通常为 `http://localhost:5173`）。前端默认请求 `http://127.0.0.1:8000`；若后端地址不同，可在 `frontend/.env.local` 中设置：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

关卡也可通过查询参数或路径直接进入：

```text
http://localhost:5173/?level=2
http://localhost:5173/level-3
```

## 游戏关卡

| 关卡 | 场景 | 核心伦理议题 |
| --- | --- | --- |
| Level 1 — The Hiring Gate | 招聘筛选 AI `Aegis-Recruit v4` | 偏见、公平性、可解释性、问责 |
| Level 2 — The Memory Vault | 城市画像系统 `CivicPulse` | 数据最小化、隐私、敏感数据与治理 |
| Level 3 — The Clinical Singularity | 医疗应急系统 `ASCLEPIUS-03` | 事实核验、人类监督、有害输出、知识产权与监控 |

玩家每轮提交论点后，后端会检索相关证据、评估论证质量、更新“Logic Fortress”数值，再由 NPC 作出回应。将堡垒值降至零即可完成当前关卡。

## API 概览

启动后端后，可在 `http://127.0.0.1:8000/docs` 查看自动生成的 OpenAPI 文档。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/users` | 创建玩家 |
| `POST` | `/api/sessions` | 创建游戏会话 |
| `GET` | `/api/sessions/{session_id}` | 获取会话和进度 |
| `POST` | `/api/sessions/{session_id}/turns` | 提交完整辩论回合 |
| `POST` | `/api/sessions/{session_id}/turns/stream` | 以 NDJSON 流式返回回合事件 |
| `GET` | `/api/search?q=...` | 搜索知识库证据 |
| `GET` | `/api/llm/status` | 检查当前模型服务状态 |

## 测试与评估

运行后端测试：

```powershell
python -m pytest
```

构建并检查前端类型：

```powershell
cd frontend
npm run build
```

评估脚本位于 `evaluation/`：

```powershell
python -m evaluation.run_retrieval_eval
python -m evaluation.simulate_progression
python -m evaluation.run_latency
python -m evaluation.run_degradation
```

结果会写入 `evaluation/results/`。

## 开发说明

- `course_content.db` 是项目随仓库提供的只读知识库；不要在本地调试时覆盖它。
- `logic_fortress_app.db` 保存本地玩家和回合数据，可在需要重置进度时手动删除；它已被 Git 忽略。
- 后端 CORS 默认只允许本机 `localhost` 和 `127.0.0.1` 的任意端口访问。
