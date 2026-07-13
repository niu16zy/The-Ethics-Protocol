# Next Stage Development Prompt

Use this prompt to start the next implementation conversation for Logic Fortress.

## Current Completion Summary

The backend MVP closed loop is already implemented and test-verified.

Completed backend capabilities:

- FastAPI backend scaffold
- Separate knowledge DB and app DB
- Knowledge DB retrieval with SQLite FTS5/BM25
- App DB tables:
  - `users`
  - `game_sessions`
  - `turns`
  - `progress_saves`
  - `achievements`
  - `final_reports`
- User creation
- Session creation
- Debate turn persistence
- Progress save/resume baseline
- Retriever service
- Evaluator service with schema validation
- Rule-based evaluator fallback
- Gemini evaluator path
- Persona service
- Rule-based persona fallback
- Gemini persona path
- LLM status endpoint
- Meter update service
- Debate orchestrator
- Tests covering API, app DB, retrieval, evaluator, persona, LLM status, and turn flow

Last known verification:

```powershell
python -m compileall backend tests
python -m pytest
```

Last known result:

```text
17 passed
```

## Next Stage Goal

The next stage should build the first complete frontend level UI.

Primary goal:

Create a polished, minimal, dark visual experience for one playable level:

1. a cinematic entry scene
2. a typed narrative intro
3. a transition into the formal debate level
4. an NPC visual area
5. an NPC dialogue panel
6. a player input area
7. backend-connected debate turn feedback

This stage is frontend-first, but it must respect the existing FastAPI backend contract. Do not redesign the backend unless a tiny compatibility fix is absolutely required.

## Level-1 UI Concept

The first level should feel like a quiet, dark, pixel-noir / visual-novel inspired debate scene.

Reference direction:

- black page background
- one large atmospheric scene image or generated/static visual panel near the top
- narrative text beneath the scene
- typewriter effect that gradually reveals preset intro text
- after the intro, transition into the active level interface
- formal level screen contains:
  - NPC image/avatar/portrait area
  - NPC dialogue box
  - player argument input box
  - Logic Fortress meter
  - evidence/verdict diagnostics

The result should not look like a dashboard, SaaS panel, generic chatbot, or marketing landing page.

## Extensibility Requirement

Design the frontend so Level 2 and Level 3 can be added later without rewriting the main UI.

Use a level configuration pattern such as:

- `levelId`
- `title`
- `introText`
- `sceneImage`
- `npcName`
- `npcAvatar`
- `npcInitialDialogue`
- `theme`
- optional `scenarioPrompt`

Keep Level 1 content in a config object/file rather than hardcoding all copy inside components.

## Next Stage Scope

Implement these tasks in order:

1. Inspect the repository.
   - Read `AGENTS.md`.
   - Read `AI_CODING_CONSTRAINTS.md`.
   - Read `architecture-design.md`.
   - Read `MVP_IMPLEMENTATION_STATUS.md`.
   - Inspect backend schemas and routes before writing frontend types.

2. Scaffold the frontend if it does not exist.
   - Use React + TypeScript + Vite.
   - Use Tailwind CSS for styling.
   - Use TanStack Query for API calls.
   - Use Zustand only for local level/session UI state where useful.
   - Use React Router only if multiple route screens are implemented in this stage.

3. Implement the Level 1 entry scene.
   - Full black/dark background.
   - Large centered scene image or generated/static visual panel.
   - Preset intro text shown below the image.
   - Typewriter effect that reveals text gradually.
   - Continue/enter action appears after text finishes.
   - Include skip/continue behavior so testing is not slow.

4. Implement the active Level 1 debate screen.
   Required UI areas:
   - NPC visual area
   - NPC name/status
   - NPC dialogue box
   - player argument input
   - submit button
   - Logic Fortress meter
   - evidence panel with traceable document ids/topics
   - current verdict/confidence display
   - evaluator/persona source diagnostics
   - loading state
   - error state

5. Implement API integration.
   Required backend endpoints to consume:
   - `POST /api/users`
   - `GET /api/users/{user_id}`
   - `POST /api/sessions`
   - `GET /api/sessions/{session_id}`
   - `POST /api/sessions/{session_id}/turns`
   - `POST /api/sessions/{session_id}/saves`
   - `POST /api/sessions/{session_id}/resume`
   - `GET /api/search`
   - `GET /api/llm/status`

6. Implement TypeScript API types.
   - Mirror backend Pydantic response shapes closely.
   - Avoid `any`.
   - Keep API client code centralized.
   - Keep DTO/types in a dedicated frontend types location.

7. Implement one full Level 1 user path.
   - Create explicit user.
   - Create session.
   - Show entry scene.
   - Enter formal debate screen.
   - Submit one debate turn.
   - Render NPC response.
   - Render meter before/after.
   - Render retrieved evidence.
   - Render evaluator verdict/confidence.
   - Render whether the response came from `llm`, `rules`, or `fallback`.

8. Add minimal frontend verification.
   - Run type check/build.
   - Add component or API-client tests only if the scaffold already includes a test setup or adding one is low-risk.
   - At minimum, verify the app builds and can call the backend manually.

## Hard Constraints

- Do not call LLM providers from the frontend.
- Do not expose API keys or provider endpoints to frontend code.
- Do not add embeddings.
- Do not add a vector DB.
- Do not make anonymous sessions the default.
- Do not merge Evaluator and Persona concepts in the UI copy or state model.
- Do not redesign backend schemas unless a small compatibility fix is required.
- Do not turn the app into a generic chatbot or quiz.
- Do not create a marketing landing page as the main screen.
- Do not build Level 2 or Level 3 yet; only design the structure so they can be added.

## UI Design Guidance

The UI should feel like a focused dark educational game, with visual-novel pacing and a minimal debate interface.

Entry scene:

- black background
- large image/visual panel
- narrative text below the image
- typewriter animation
- minimal continue affordance

Active level screen:

- dark background
- restrained color palette
- NPC visual left/top depending on viewport
- dialogue and input should be primary
- evidence/verdict diagnostics should be visible but secondary
- avoid clutter and bright dashboard styling

Design rules:

- Use the playable experience as the first screen.
- Keep controls efficient and readable.
- Use clear states for idle, intro typing, loading, success, and error.
- Evidence should be visible and traceable, not hidden in raw JSON.
- The UI may be game-like, but should remain usable for repeated testing.
- Text must not overlap or overflow controls.
- Layout must work on desktop and mobile.

## Asset Guidance

If no final art assets exist yet:

- Use a local placeholder visual panel or CSS-generated dark scene only as a temporary development asset.
- Keep asset references centralized in level config.
- Do not hardcode remote asset URLs that may disappear.
- Do not block the UI implementation waiting for final art.

Recommended future asset paths:

```text
frontend/src/assets/levels/level-1/intro-scene.png
frontend/src/assets/levels/level-1/npc-avatar.png
```

## Expected File Direction

If no frontend exists, create a small frontend root such as:

```text
frontend/
  package.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    api/
      client.ts
      logicFortressApi.ts
    assets/
      levels/
        level-1/
    components/
      DebateInput.tsx
      DialogueBox.tsx
      EvidencePanel.tsx
      FortressMeter.tsx
      IntroScene.tsx
      LevelShell.tsx
      LlmStatusBadge.tsx
      NpcPanel.tsx
      TurnDiagnostics.tsx
    config/
      levels.ts
    pages/
      LevelOnePage.tsx
    stores/
      gameStore.ts
    types/
      api.ts
      level.ts
    styles/
      index.css
```

Only create the files actually needed for the first usable level.

## High Quality Prompt To Paste Into A New Conversation

```text
You are now the frontend implementation agent for Logic Fortress.

First, read these files before changing anything:
- AGENTS.md
- AI_CODING_CONSTRAINTS.md
- architecture-design.md
- DEVELOPMENT_GANTT.md
- MVP_IMPLEMENTATION_STATUS.md
- NEXT_STAGE_DEVELOPMENT_PROMPT.md

Current state:
- The backend MVP closed loop is implemented and test-verified.
- Tests previously passed with 17 passed.
- The system already has FastAPI, separate knowledge/app SQLite databases, FTS5 retrieval, user/session/turn persistence, Evaluator, Persona, Gemini provider integration, rule-based fallbacks, and LLM status diagnostics.
- There is no frontend yet.
- There is no embedding layer and there must not be one for this stage.
- There is no vector DB and there must not be one for this stage.
- There is no anonymous-first flow and there must not be one for this stage.

Next stage objective:
Build the first complete frontend level UI: a dark, minimal, visual-novel inspired Level 1 that includes an entry scene with typewriter intro text and a formal debate screen connected to the existing FastAPI backend.

Required frontend stack:
- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Zustand only for local level/session UI state where useful
- React Router only if multiple route screens are needed

Level 1 UX requirements:
1. First screen is an entry scene, not a marketing landing page.
2. Entry scene has a black/dark background.
3. Entry scene has a large atmospheric image or temporary visual panel near the top.
4. Preset narrative text appears below the image with a typewriter effect.
5. After the text finishes, show a clear continue/enter action.
6. Include a skip/continue mechanism for faster testing.
7. Formal level screen includes:
   - NPC visual/avatar area
   - NPC name/status
   - NPC dialogue box
   - player argument input
   - submit action
   - Logic Fortress meter
   - evidence panel
   - verdict/confidence display
   - evaluator/persona source diagnostics
   - LLM status indicator
   - loading state
   - error state

Style requirements:
- Minimal and dark.
- Pixel-noir / visual-novel inspired, but not visually noisy.
- The UI should not look like a SaaS dashboard, generic chatbot, quiz app, or marketing page.
- Text must not overlap or overflow.
- Layout must be responsive on desktop and mobile.
- Evidence should be readable and traceable without dumping raw JSON.

Extensibility requirements:
- Do not hardcode Level 1 copy and assets directly inside UI components.
- Create a level config pattern that can support Level 2 and Level 3 later.
- Level config should support at least:
  - levelId
  - title
  - introText
  - sceneImage
  - npcName
  - npcAvatar
  - npcInitialDialogue
  - theme
  - optional scenarioPrompt
- Only implement Level 1 now.

Required user flow:
1. Create a lightweight explicit user using POST /api/users.
2. Create a game session using POST /api/sessions.
3. Show Level 1 entry scene.
4. Enter the formal debate screen.
5. Submit a player argument using POST /api/sessions/{session_id}/turns.
6. Render NPC response.
7. Render Logic Fortress meter before/after.
8. Render retrieved evidence with document ids, topic, lesson, excerpt, and score when present.
9. Render evaluator verdict, confidence, and evidence refs.
10. Render evaluator_source and persona_source so the user can see whether output came from llm, rules, or fallback.
11. Show loading and error states.
12. Optionally show GET /api/llm/status in a small status badge.

Important backend endpoints:
- POST /api/users
- GET /api/users/{user_id}
- POST /api/sessions
- GET /api/sessions/{session_id}
- POST /api/sessions/{session_id}/turns
- POST /api/sessions/{session_id}/saves
- POST /api/sessions/{session_id}/resume
- GET /api/search
- GET /api/llm/status

Implementation requirements:
- Inspect backend Pydantic schemas and route files before defining frontend TypeScript types.
- Keep API calls centralized in a frontend api module.
- Keep shared TypeScript DTOs in a frontend types module.
- Avoid any.
- Use VITE_API_BASE_URL for the backend base URL, defaulting to http://127.0.0.1:8000 if appropriate.
- Frontend must never call LLM providers directly.
- Frontend must never expose API keys or model endpoints.
- Do not add embeddings, vector DB, auth, production deployment, or unrelated backend refactors.
- Do not redesign backend schemas unless a tiny compatibility fix is required.

Suggested file layout if no frontend exists:
frontend/
  package.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    api/
      client.ts
      logicFortressApi.ts
    assets/
      levels/
        level-1/
    components/
      DebateInput.tsx
      DialogueBox.tsx
      EvidencePanel.tsx
      FortressMeter.tsx
      IntroScene.tsx
      LevelShell.tsx
      LlmStatusBadge.tsx
      NpcPanel.tsx
      TurnDiagnostics.tsx
    config/
      levels.ts
    pages/
      LevelOnePage.tsx
    stores/
      gameStore.ts
    types/
      api.ts
      level.ts
    styles/
      index.css

Before editing:
- Briefly summarize what is already implemented.
- Give a concrete frontend implementation plan.

After editing:
- Summarize changed files.
- Explain how to run the backend and frontend together.
- Run the available frontend build/type-check command.
- If dependencies cannot be installed or commands cannot run, say exactly why and what remains to verify.
```
