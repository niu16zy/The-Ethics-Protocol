from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import app_repository, orchestrator, settings
from backend.app.schemas.session import SessionCreate, SessionRead
from backend.app.schemas.turn import DebateTurnCreate, DebateTurnResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate) -> SessionRead:
    try:
        return app_repository().create_session(
            user_id=payload.user_id,
            current_level=payload.current_level,
            initial_meter=settings().initial_fortress_meter,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int) -> SessionRead:
    try:
        return app_repository().get_session(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/turns", response_model=DebateTurnResponse)
def submit_turn(session_id: int, payload: DebateTurnCreate) -> DebateTurnResponse:
    try:
        return orchestrator().submit_turn(session_id, payload.player_input)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{session_id}/turns/stream")
def stream_turn(session_id: int, payload: DebateTurnCreate) -> StreamingResponse:
    def encode_events() -> Iterator[str]:
        try:
            for event in orchestrator().stream_turn_events(session_id, payload.player_input):
                yield f"{json.dumps(event, ensure_ascii=False)}\n"
        except LookupError as exc:
            yield f"{json.dumps({'event': 'error', 'message': str(exc)}, ensure_ascii=False)}\n"
        except RuntimeError as exc:
            yield f"{json.dumps({'event': 'error', 'message': str(exc)}, ensure_ascii=False)}\n"
        except Exception:
            yield f"{json.dumps({'event': 'error', 'message': 'Unexpected stream failure.'}, ensure_ascii=False)}\n"

    return StreamingResponse(
        encode_events(),
        media_type="application/x-ndjson",
    )
