from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: int
    current_level: int = Field(default=1, ge=1)


class SessionRead(BaseModel):
    id: int
    user_id: int
    current_level: int
    fortress_meter: int
    session_status: str
    started_at: str
    ended_at: str | None = None
    updated_at: str
