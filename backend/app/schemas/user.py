from __future__ import annotations

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=120)
    email: str | None = None
    external_id: str | None = None


class UserRead(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None = None
    external_id: str | None = None
    created_at: str
    updated_at: str
