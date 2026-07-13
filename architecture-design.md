# Architecture Design

Project: `Logic Fortress`

## 1. System Goal

The project is an educational debate game grounded in IBM SkillsBuild AI ethics course content.

The system has two separate responsibilities:

1. Knowledge grounding and evaluation
2. User/game-state persistence

These responsibilities must not share one database.

## 2. Core Architecture Decision

Use two SQLite databases:

- `course_content.db`
  - RAG knowledge base
  - imported from structured Markdown
  - queried with SQLite FTS5/BM25

- `logic_fortress_app.db`
  - application database
  - stores users, sessions, turns, progress, achievements, reports

This gives a clean boundary between course evidence and game state.

## 3. No-Embedding Baseline

Current retrieval baseline:

1. Structured Markdown ingestion
2. SQLite knowledge tables
3. FTS5/BM25 retrieval
4. Retriever evidence assembly
5. Evaluator JSON generation
6. Persona dialogue generation

Do not treat embedding or vector databases as part of the baseline architecture.

## 4. Knowledge Database

### 4.1 Purpose

The knowledge database stores all course material used for grounding player evaluation.

### 4.2 Schema

#### `documents`

```sql
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT,
    lesson TEXT,
    topic TEXT,
    content TEXT,
    seq_order INTEGER
);
```

#### `documents_fts`

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
USING fts5(
    id UNINDEXED,
    search_content
);
```

### 4.3 Ingestion contract

- Parse Markdown line by line with a state machine.
- Update `current_course`, `current_lesson`, `current_topic` from `[Course]`, `[LessonX]`, and `[topic]`.
- Insert one `documents` row per `[content]`.
- Build `search_content` in the form:

```text
Course: {course} | Lesson: {lesson} | Topic: {topic} | Content: {content}
```

## 5. Application Database

### 5.1 Purpose

The application database stores the playable product state.

### 5.2 Recommended schema

#### `users`

- `id`
- `username`
- `display_name`
- `email` or `external_id` if needed later
- `created_at`
- `updated_at`

#### `game_sessions`

- `id`
- `user_id`
- `current_level`
- `fortress_meter`
- `session_status`
- `started_at`
- `ended_at`
- `updated_at`

#### `turns`

- `id`
- `session_id`
- `turn_index`
- `player_input`
- `retrieved_refs`
- `evaluator_json`
- `npc_response`
- `meter_before`
- `meter_after`
- `created_at`

#### `progress_saves`

- `id`
- `session_id`
- `save_name`
- `save_payload`
- `created_at`

#### `achievements`

- `id`
- `user_id`
- `session_id`
- `badge_name`
- `unlocked_at`

#### `final_reports`

- `id`
- `session_id`
- `strengths`
- `misconceptions`
- `recommended_topics`
- `generated_at`

### 5.3 Design note

The app DB is not the knowledge DB. It must never become the source of truth for course content.

## 6. Retrieval and Evaluation Flow

1. Player submits an argument.
2. Backend loads the user session from the app DB.
3. Retriever queries the knowledge DB with FTS5/BM25.
4. Retriever returns traceable evidence rows.
5. Evaluator receives the evidence and returns structured JSON.
6. Persona converts the evaluator result into NPC dialogue.
7. Backend persists the turn in the app DB.
8. Frontend renders NPC reply, meter change, and evidence.

## 7. User Model

Do not design the system around anonymous-first behavior.

The initial model should assume an explicit user identity exists, even if the implementation is lightweight.

Future guest mode can be added later as an enhancement, but it is not the baseline.

## 8. Backend Service Boundaries

Suggested backend modules:

- `ingestion`
- `retrieval`
- `evaluation`
- `persona`
- `orchestration`
- `session_service`
- `progress_service`
- `report_service`

Boundary rules:

- API routes should not contain core business logic.
- Persona must not access the knowledge DB directly.
- Evaluator must not fabricate evidence.
- Frontend must not call any LLM provider directly.

## 9. API Surface

Recommended endpoints:

- `POST /api/users`
- `GET /api/users/{user_id}`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/turns`
- `POST /api/sessions/{session_id}/saves`
- `POST /api/sessions/{session_id}/resume`
- `GET /api/reports/{session_id}`
- `GET /api/search`

## 10. Testing Strategy

### 10.1 Knowledge DB

- imported content count matches source content count
- `documents_fts` count matches `documents`
- `seq_order` is continuous and unique
- FTS queries return expected course evidence

### 10.2 Application DB

- user creation works
- session creation works
- turn persistence works
- save and resume work
- final report persistence works

### 10.3 End-to-end

- user -> session -> turn -> evidence -> evaluator -> persona -> persistence -> report

## 11. Recommended Repository Layout

```text
project-root/
  scripts/
    import_markdown_to_sqlite.py
  data/
    course_content.db
    logic_fortress_app.db
  backend/
    app/
      api/
      services/
      repositories/
      models/
      schemas/
  docs/
  AI_CODING_CONSTRAINTS.md
  architecture-design.md
  DEVELOPMENT_GANTT.md
```

## 12. Summary

The project should remain a clean two-database system:

- knowledge DB for grounded course retrieval
- application DB for user and progress state

No embedding layer is part of the current baseline, and anonymous-first behavior is intentionally not the starting model.
