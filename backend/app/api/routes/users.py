from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, status

from backend.app.api.dependencies import app_repository
from backend.app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> UserRead:
    try:
        return app_repository().create_user(payload)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int) -> UserRead:
    try:
        return app_repository().get_user(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
