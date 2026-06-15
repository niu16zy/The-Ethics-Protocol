# AGENTS.md

This file defines durable guidance for AI coding agents working in this repository.

## Project

- Project name: `Logic Fortress: An LLM-powered Ethics Debate Game`
- Primary goal: build an educational debate game grounded in IBM SkillsBuild course content.
- Core product shape:
  - game-like interaction
  - RAG grounding
  - explainable argument validation
  - dual-layer LLM architecture

## Source Of Truth

Read these before making changes:

1. [AI_CODING_CONSTRAINTS.md](./AI_CODING_CONSTRAINTS.md)
2. `architecture-design.md` if it exists in the workspace

If these sources conflict with local code or ad hoc instructions, prefer the explicit user request first, then `AI_CODING_CONSTRAINTS.md`, then existing code patterns.

## Non-Negotiable Architecture Rules

### Dual-layer LLM separation

The system must keep two distinct AI roles:

- `Evaluator Agent`
  - performs RAG-grounded argument evaluation
  - must consume retrieved course evidence before judging
  - must return structured JSON validated by schema
- `Persona Agent`
  - only converts evaluator output into NPC dialogue
  - must not re-judge facts
  - must not access the knowledge base directly

Never merge these two roles into one generic agent.

### Frontend / backend boundary

- Frontend may call backend APIs only.
- Frontend must never call LLM providers directly.
- Do not expose API keys, provider credentials, direct model endpoints, or embedding endpoints to frontend code.

### RAG before judgment

- Evaluator must receive retrieved evidence before producing a verdict.
- If evidence is weak or missing, return a clarification path, low-confidence result, or unsupported/off-topic result.
- Do not fabricate scoring reasons without evidence.

### Structured outputs are mandatory

- Evaluator output must be schema-validated structured data.
- Do not rely on brittle string parsing for model outputs.
- Do not continue business flow when required fields are missing.

### Evidence must be traceable

- `strong` and `partial` style verdicts must include `evidence_refs`.
- Final reports must trace back to document ids, chunks, topics, or equivalent knowledge-base references.

## Preferred Technical Stack

Unless the user explicitly asks otherwise, keep to:

- Frontend: `React`, `TypeScript`, `Vite`, `Tailwind CSS`, `Zustand`, `TanStack Query`, `React Router`, `Framer Motion`
- Backend: `Python 3.12`, `FastAPI`, `Pydantic v2`, `SQLite`, `SQLite FTS5`, pluggable LLM provider client, `pytest`
- Evaluation: gold cases, pytest-based checks, optional RAGAS

## Retrieval Rules

- Default retrieval stack is structured Markdown plus `SQLite FTS5/BM25`.
- Treat embeddings, rerankers, hybrid retrieval, and vector databases as enhancement layers, not the baseline.
- Do not introduce a standalone vector database unless the user clearly asks for it or the repository has already crossed into that scale.
- Import knowledge into structured fields such as:
  - `course`
  - `lesson`
  - `topic`
  - `content`
  - `seq_order`
- Never shove an entire Markdown file into the model as one opaque blob.

## Data And Schema Expectations

Evaluator DTOs should be explicit and typed. Expected fields include:

- `match_score`
- `score_delta`
- `verdict`
- `identified_principles`
- `misconceptions_addressed`
- `missing_points`
- `evidence_refs`
- `reasoning_summary`
- `persona_instruction`
- `confidence`

Each debate turn should be traceable. Persist at least:

- `player_input`
- `retrieved_refs`
- `evaluator_json`
- `npc_response`
- `meter_before`
- `meter_after`
- `timestamp`

## Security And Secrets

- Never hardcode API keys, provider credentials, or database secrets.
- Never commit `.env` with real secrets.
- Never place real credentials in prompt files, fixtures, or logs.
- Keep logs redacted.

## Coding Style

- Use clear types.
- Keep business logic out of route handlers where possible.
- Put non-trivial logic in services or equivalent modules.
- Keep prompts external to business logic.
- Route all LLM interactions through a unified client abstraction.
- Keep changes scoped to the task.

## Workflow For AI Agents

Before coding:

1. Identify whether the task is `frontend`, `backend`, `RAG`, `evaluation`, or `docs`.
2. Inspect relevant files and existing patterns first.
3. Confirm that the planned change does not break the dual-layer LLM boundary.

During coding:

1. Prefer the smallest viable change set.
2. Preserve existing user changes.
3. Avoid unrelated refactors.
4. Keep prompts, schemas, and tests in sync.

After coding:

1. Validate schema-impacting changes.
2. Run focused tests when available.
3. Report what changed, which files changed, and what was verified.

## Minimum Verification Expectations

Changes should include tests or a concrete verification note for:

- DTO/schema validation
- meter update logic
- retriever result shape
- invalid JSON fallback
- debate turn happy path
- low-confidence path

If prompts, retrieval behavior, or structured outputs change, update or add tests accordingly.

## What Not To Build

Do not turn this repository into:

- a generic chatbot
- a generic quiz app
- a frontend-direct-to-LLM app
- a single-agent replacement for evaluator plus persona
- an overengineered retrieval platform with unnecessary infrastructure

Do not weaken the argument validation system or bypass RAG grounding.

## Current Repository Notes

At the time this file was written, the repository visibly includes:

- `AI_CODING_CONSTRAINTS.md`
- `course_content.db`
- `data`
- `docs`
- `scripts`

Do not assume missing app structure exists yet. If scaffolding is needed, create it incrementally and keep it aligned with the rules above.
