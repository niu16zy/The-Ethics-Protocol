# AI Coding Constraints

Applicable project: `Logic Fortress`

This document constrains how Codex, Cursor, Claude Code, or any other AI coding assistant may change this repository. Any code, schema, prompt, architecture, or documentation change must follow this file and `architecture-design.md`.

## 1. Project Baseline

The project currently has two distinct data domains:

- Knowledge domain: course Markdown -> SQLite FTS5/BM25 retrieval
- Application domain: user accounts, game sessions, turns, progress, reports

These domains must stay separate.

## 2. Required Architecture Rules

### 2.1 Dual-layer LLM separation

The system must keep two different AI roles:

- `Evaluator Agent`
  - consumes retrieved course evidence
  - validates player arguments
  - returns structured JSON only
- `Persona Agent`
  - consumes evaluator output only
  - turns the verdict into NPC dialogue
  - must not re-judge facts
  - must not access the knowledge base directly

Never merge these agents into one generic model call.

### 2.2 Frontend boundary

- Frontend may call backend APIs only.
- Frontend must never call LLM providers directly.
- Do not expose API keys, provider credentials, direct model endpoints, or retrieval internals to frontend code.

### 2.3 Retrieval before judgment

- Evaluator must receive retrieved evidence before producing a verdict.
- If evidence is weak or missing, return clarification, low-confidence, or unsupported/off-topic.
- Do not fabricate scoring reasons without evidence.

### 2.4 Structured outputs are mandatory

- Evaluator output must be schema-validated structured data.
- Do not rely on brittle string parsing for model outputs.
- Do not continue business flow when required fields are missing.

### 2.5 Traceability is mandatory

- Strong and partial verdicts must include `evidence_refs`.
- Final reports must be traceable to document ids, topics, or other knowledge-base references.

## 3. Fixed Technical Stack

Unless the user explicitly asks otherwise, keep to:

- Frontend: React, TypeScript, Vite, Tailwind CSS, Zustand, TanStack Query, React Router, Framer Motion
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLite, SQLite FTS5, pluggable LLM provider client, pytest
- Application DB: SQLite initially
- Evaluation: gold cases, pytest-based checks, optional RAGAS scripts

## 4. Retrieval Rules

- Default retrieval stack is structured Markdown plus SQLite FTS5/BM25.
- Treat query expansion, reranking, and any future semantic retrieval as optional enhancements only.
- Do not introduce a standalone vector database unless the user explicitly asks for it.
- Import knowledge into structured fields such as:
  - `course`
  - `lesson`
  - `topic`
  - `content`
  - `seq_order`
- Never shove an entire Markdown file into the model as one opaque blob.

## 5. Data And Schema Expectations

### 5.1 Knowledge DB

The RAG knowledge base must remain in a separate SQLite database from user/game state.

Required knowledge tables:

- `documents`
- `documents_fts`

### 5.2 Application DB

The user and game-state database must store at least:

- `users`
- `game_sessions`
- `turns`
- `progress_saves`
- `achievements`
- `final_reports`

### 5.3 Traceable turn storage

Each debate turn should persist at least:

- `player_input`
- `retrieved_refs`
- `evaluator_json`
- `npc_response`
- `meter_before`
- `meter_after`
- `timestamp`

## 6. User Model Rules

- Do not design the system around an anonymous-first flow.
- Model users explicitly.
- If future guest mode is needed, add it as a separate enhancement later.
- Do not assume every session is anonymous by default.

## 7. Security And Secrets

- Never hardcode API keys, provider credentials, or database secrets.
- Never commit `.env` with real secrets.
- Never place real credentials in prompt files, fixtures, or logs.
- Keep logs redacted.

## 8. Coding Style

- Use clear types.
- Keep business logic out of route handlers where possible.
- Put non-trivial logic in services or equivalent modules.
- Keep prompts external to business logic.
- Route all LLM interactions through a unified client abstraction.
- Keep changes scoped to the task.

## 9. Workflow For AI Agents

Before coding:

1. Identify whether the task is frontend, backend, RAG, evaluation, or docs.
2. Inspect relevant files and existing patterns first.
3. Confirm that the planned change does not break dual-layer LLM separation.

During coding:

1. Prefer the smallest viable change set.
2. Preserve existing user changes.
3. Avoid unrelated refactors.
4. Keep prompts, schemas, and tests in sync.

After coding:

1. Validate schema-impacting changes.
2. Run focused tests when available.
3. Report what changed, which files changed, and what was verified.

## 10. Minimum Verification Expectations

Changes should include tests or a concrete verification note for:

- DTO/schema validation
- meter update logic
- retriever result shape
- invalid JSON fallback
- debate turn happy path
- low-confidence path

If prompts, retrieval behavior, or structured outputs change, update or add tests accordingly.

## 11. What Not To Build

Do not turn this repository into:

- a generic chatbot
- a generic quiz app
- a frontend-direct-to-LLM app
- a single-agent replacement for evaluator plus persona
- an overengineered retrieval platform with unnecessary infrastructure

Do not weaken the argument validation system or bypass RAG grounding.

## 12. Short Prompt For Future AI Help

```text
You are coding the Logic Fortress project. Follow AI_CODING_CONSTRAINTS.md and architecture-design.md strictly. Use Python and FastAPI for the backend. Preserve the dual-layer LLM architecture: Evaluator Agent performs RAG-grounded argument validation and returns structured JSON; Persona Agent only turns the evaluator result into NPC dialogue. The default retrieval stack is structured Markdown + SQLite FTS5/BM25, not a standalone vector database. The application database for users and game progress is separate from the RAG knowledge database. The frontend must never call an LLM directly. Do not hardcode secrets. Keep code scoped, typed, testable, and aligned with the existing project structure.
```
