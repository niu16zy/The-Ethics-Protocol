# Logic Fortress MVP Implementation Status

Last updated: 2026-06-30

This document records the current implementation stage so future coding agents can quickly understand what has been built, what has been verified, and what must remain architecturally protected.

## Current Stage

Backend MVP closed loop is implemented and test-verified. A configurable Gemini LLM provider path has been added, with rule-based fallback preserved for local development and provider failures.

The current implementation is intentionally minimal. It is not a complete product and does not include a frontend, embeddings, vector databases, authentication, or production deployment configuration.

## Architecture Rules Currently Preserved

- Dual-layer LLM boundary is represented in code:
  - `EvaluationService` produces schema-validated evaluator results.
  - `PersonaService` only consumes evaluator output and meter state.
  - Persona does not access the knowledge database.
- Knowledge DB and application DB are separate:
  - Knowledge DB: `course_content.db`
  - Application DB: `logic_fortress_app.db`
- Retrieval baseline is SQLite FTS5/BM25.
- No embedding layer is implemented.
- No vector database is implemented.
- User/session flow is explicit-user-first, not anonymous-first.
- Frontend-to-LLM calls are not implemented or exposed.
- No secrets or provider credentials are hardcoded.
- Gemini API keys are loaded from environment variables only.
- Local `.env` is supported for development and remains ignored by git.

## Completed Coding Tasks

### Backend Scaffold

Added:

- `backend/__init__.py`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/db.py`

Current behavior:

- FastAPI app is created by `create_app()`.
- App DB is initialized during FastAPI lifespan startup.
- Settings resolve paths for:
  - `course_content.db`
  - `logic_fortress_app.db`
- Optional environment overrides:
  - `LOGIC_FORTRESS_KNOWLEDGE_DB`
  - `LOGIC_FORTRESS_APP_DB`
  - `LOGIC_FORTRESS_LLM_PROVIDER`
  - `GEMINI_MODEL`
  - `GEMINI_API_KEY`
  - `GOOGLE_API_KEY`
  - `GOOGLE_GENERATIVE_AI_API_KEY`
  - `GEMINI_TIMEOUT_SECONDS`
  - `LOGIC_FORTRESS_LLM_MAX_ATTEMPTS`

### Application Database

Implemented in:

- `backend/app/core/db.py`
- `backend/app/repositories/app_repository.py`

Tables initialized:

- `users`
- `game_sessions`
- `turns`
- `progress_saves`
- `achievements`
- `final_reports`

Implemented persistence:

- create user
- get user
- create session
- get session
- compute next turn index
- persist turn with retrieved refs, evaluator JSON, NPC response, meter before/after
- create progress save
- fetch turns for verification/tests

### Knowledge Database Access

Implemented in:

- `backend/app/repositories/knowledge_repository.py`
- `backend/app/services/retrieval_service.py`

Current behavior:

- Verifies required knowledge tables:
  - `documents`
  - `documents_fts`
- Searches `documents_fts` with SQLite FTS5/BM25.
- Joins retrieved FTS rows back to `documents`.
- Returns traceable `EvidenceRef` values containing:
  - `document_id`
  - `course`
  - `lesson`
  - `topic`
  - `seq_order`
  - `excerpt`
  - optional `score`
- Cleans full-sentence player input before FTS search:
  - strips punctuation
  - removes short/common stopwords
  - deduplicates terms

Fallback:

- If an FTS query raises a SQLite operational error, repository falls back to a conservative SQL `LIKE` search.
- If `score` is `null` in returned evidence, that generally means the fallback `LIKE` path was used instead of FTS/BM25.

### Evaluator Layer

Implemented in:

- `backend/app/schemas/evaluator.py`
- `backend/app/services/evaluation_service.py`

Current behavior:

- Uses Gemini LLM evaluation when `LOGIC_FORTRESS_LLM_PROVIDER=gemini` and `GEMINI_API_KEY` are configured.
- Uses a rule-based MVP evaluator when no LLM client is configured, so the backend can run without a real LLM provider or secrets.
- Returns validated `EvaluatorResult`.
- Supports required fields:
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
- Enforces that `strong` and `partial` verdicts include evidence refs.
- Provides `parse_or_fallback()` for invalid JSON/schema fallback.
- Strips optional Markdown JSON fences before schema validation.

Important limitation:

- The Gemini integration currently uses the `generateContent` REST endpoint to match the provided manual API style. It is wrapped behind a provider abstraction so it can later move to a newer Google API surface if needed.
- If the Evaluator LLM call fails or returns invalid JSON, the system returns a low-confidence unsupported result rather than fabricating a judgment.
- Gemini request/read timeouts are wrapped as `LLMClientError`, so Evaluator can safely fall back instead of crashing streaming responses.
- Evaluator LLM calls retry up to `LOGIC_FORTRESS_LLM_MAX_ATTEMPTS` before falling back.
- Runtime source is exposed in `DebateTurnResponse.evaluator_source`:
  - `llm`
  - `rules`
  - `fallback`

### Persona Layer

Implemented in:

- `backend/app/services/persona_service.py`

Current behavior:

- Consumes `EvaluatorResult` and `meter_after`.
- Produces `PersonaResponse`.
- Does not query the knowledge DB.
- Does not re-score or re-judge facts.
- Uses Gemini when a provider client is configured.
- Falls back to rule-based NPC text if Persona LLM output is invalid or the provider call fails.
- Streamed Persona responses now use regular Gemini JSON generation first, then locally chunk the resulting NPC text for the frontend. This avoids relying on the less stable provider streaming endpoint during the MVP.
- Streaming Persona calls fall back to rule-based chunks when the provider fails.
- Runtime source is exposed in `DebateTurnResponse.persona_source`:
  - `llm`
  - `rules`
  - `fallback`

### LLM Provider Client

Implemented in:

- `backend/app/services/llm_client.py`

Current behavior:

- Defines a provider-neutral `LLMClient` protocol.
- Implements `GeminiGenerateContentClient`.
- Sends API key through the `X-goog-api-key` header from `GEMINI_API_KEY`.
- Also accepts `GOOGLE_API_KEY` and `GOOGLE_GENERATIVE_AI_API_KEY`.
- Auto-selects `gemini` provider when a Gemini/Google API key is configured and `LOGIC_FORTRESS_LLM_PROVIDER` is unset.
- Does not log or persist secrets.
- Returns generated text to Evaluator/Persona services.
- Wraps HTTP, URL, and timeout failures in `LLMClientError`.
- Uses configurable timeout via `GEMINI_TIMEOUT_SECONDS`.

Prompt files:

- `backend/app/prompts/evaluator.md`
- `backend/app/prompts/persona.md`

### Meter Logic

Implemented in:

- `backend/app/services/meter_service.py`

Current behavior:

- Applies evaluator `score_delta`.
- Clamps fortress meter to `0..100`.

### Debate Orchestration

Implemented in:

- `backend/app/services/orchestrator_service.py`

Current turn flow:

1. Load session from app DB.
2. Retrieve evidence from knowledge DB.
3. Evaluate player input using retrieved evidence.
4. Apply meter update.
5. Generate persona response from evaluator output.
6. Persist turn in app DB.
7. Return `DebateTurnResponse`.

### API Surface

Implemented routes:

- `POST /api/users`
- `GET /api/users/{user_id}`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/turns`
- `POST /api/sessions/{session_id}/turns/stream`
- `POST /api/sessions/{session_id}/saves`
- `POST /api/sessions/{session_id}/resume`
- `GET /api/search`
- `GET /api/llm/status`

Route files:

- `backend/app/api/dependencies.py`
- `backend/app/api/routes/users.py`
- `backend/app/api/routes/sessions.py`
- `backend/app/api/routes/search.py`
- `backend/app/api/routes/status.py`

## Implemented Schemas

Schema files:

- `backend/app/schemas/user.py`
- `backend/app/schemas/session.py`
- `backend/app/schemas/turn.py`
- `backend/app/schemas/progress.py`
- `backend/app/schemas/evaluator.py`
- `backend/app/schemas/status.py`

Key DTOs:

- `UserCreate`
- `UserRead`
- `SessionCreate`
- `SessionRead`
- `DebateTurnCreate`
- `DebateTurnResponse`
- `ProgressSaveCreate`
- `ProgressSaveRead`
- `EvidenceRef`
- `EvaluatorResult`
- `PersonaResponse`
- `LLMStatus`

## Tests Added

Test files:

- `tests/test_api.py`
- `tests/test_app_db.py`
- `tests/test_evaluator.py`
- `tests/test_config.py`
- `tests/test_llm_integration.py`
- `tests/test_llm_client.py`
- `tests/test_persona.py`
- `tests/test_retrieval.py`
- `tests/test_status_api.py`
- `tests/test_turn_flow.py`

Coverage intent:

- User creation and session creation.
- Knowledge retrieval returns traceable document refs.
- Full-sentence retrieval uses cleaned FTS query and should return BM25 scores when FTS succeeds.
- Evaluator returns schema-valid structured output.
- Invalid evaluator JSON fallback returns low-confidence unsupported result.
- Low-confidence path when no evidence is available.
- Persona consumes evaluator output only.
- Configured Evaluator LLM client returns schema-valid JSON.
- Invalid LLM JSON output falls back safely.
- Gemini request and stream timeout errors are wrapped and handled.
- Configured Persona LLM client does not require knowledge DB access.
- Stream turn endpoint emits progress events and persists exactly one turn.
- Debate turn response exposes evaluator/persona source diagnostics.
- LLM status endpoint reports provider/client configuration without exposing secrets.
- Gemini provider auto-enables when only a supported API key environment variable is present.
- Debate turn happy path persists traceable turn data.
- API can create user, create session, and submit turn.

Last verified commands:

```powershell
python -m compileall backend tests
python -m pytest
```

Last known result:

```text
23 passed
```

## LLM Configuration

Never place real provider keys in committed files.

Use environment variables:

```powershell
$env:LOGIC_FORTRESS_LLM_PROVIDER="gemini"
$env:GEMINI_MODEL="gemini-flash-latest"
$env:GEMINI_TIMEOUT_SECONDS="90"
$env:LOGIC_FORTRESS_LLM_MAX_ATTEMPTS="2"
$env:GEMINI_API_KEY="your-rotated-key"
```

Equivalent supported key variable names:

```powershell
$env:GOOGLE_API_KEY="your-rotated-key"
$env:GOOGLE_GENERATIVE_AI_API_KEY="your-rotated-key"
```

For local development, a root `.env` file is also supported:

```text
LOGIC_FORTRESS_LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-flash-latest
GEMINI_TIMEOUT_SECONDS=90
LOGIC_FORTRESS_LLM_MAX_ATTEMPTS=2
GEMINI_API_KEY=your-rotated-key
```

Then start the API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

If `LOGIC_FORTRESS_LLM_PROVIDER` is unset or `GEMINI_API_KEY` is missing, the backend stays runnable using the rule-based MVP evaluator/persona fallback.

Check LLM runtime configuration without exposing the key:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/llm/status
```

Expected Gemini-ready result:

```json
{
  "provider": "gemini",
  "model": "gemini-flash-latest",
  "api_key_configured": true,
  "client_configured": true,
  "using_rules_fallback": false
}
```

## Manual Verification Entry Points

Start API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Create user:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/users `
  -ContentType "application/json" `
  -Body '{"username":"manual_auditor","display_name":"Manual Auditor"}'
```

Create session:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/sessions `
  -ContentType "application/json" `
  -Body '{"user_id":1}'
```

Search evidence:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/search?q=fairness%20bias%20hiring&top_k=3"
```

Submit debate turn:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/sessions/1/turns `
  -ContentType "application/json" `
  -Body '{"player_input":"A hiring AI can be unfair if biased training data discriminates against applicants, so fairness and transparency matter."}'
```

Important outputs to inspect:

- `retrieved_refs[*].document_id`
- `retrieved_refs[*].score`
- `evaluator.verdict`
- `evaluator.evidence_refs`
- `evaluator.confidence`
- `evaluator_source`
- `persona_source`
- `npc_response`
- `meter_before`
- `meter_after`

## Known Gaps / Not Yet Implemented

- No authentication or password management.
- No frontend.
- No final report generation logic beyond schema/table support.
- No achievement unlock logic.
- No migration framework.
- No packaging files such as `pyproject.toml` or `requirements.txt`.
- No production logging configuration.
- No Docker/deployment setup.
- No provider-backed retry strategy for invalid model JSON beyond safe fallback.
- No streaming model responses.

## Recommended Next Development Tasks

1. Add project dependency metadata:
   - `pyproject.toml` or `requirements.txt`
   - pin FastAPI, Starlette, Pydantic, pytest, httpx, uvicorn
2. Move the existing root `scripts`, `data`, and `docs` files into a clearer structure only if the user approves, because they are currently files rather than directories.
3. Improve turn retrieval ranking:
   - prioritize course principle keywords
   - consider topic boosts
   - consider neighboring chunks where useful
4. Add provider retry/repair behavior for invalid Evaluator JSON while preserving schema validation.
5. Add final report generation using persisted turns and evidence refs.
6. Add focused tests for report traceability.
7. Add a minimal frontend only after the backend contract remains stable.

## Do Not Accidentally Change

- Do not merge Evaluator and Persona into one generic agent.
- Do not let Persona query `course_content.db`.
- Do not put user/session/turn data into `course_content.db`.
- Do not put course documents into `logic_fortress_app.db`.
- Do not add embeddings or a vector DB for the baseline MVP.
- Do not make anonymous sessions the default user model.
- Do not expose provider secrets or direct model endpoints to frontend code.
