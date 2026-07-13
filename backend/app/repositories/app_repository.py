from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from backend.app.core.db import connect_sqlite, initialize_app_db
from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.schemas.routing import DialogueBrief
from backend.app.schemas.session import SessionRead
from backend.app.schemas.user import UserCreate, UserRead


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class AppRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        with connect_sqlite(self.db_path) as connection:
            initialize_app_db(connection)

    def create_user(self, payload: UserCreate) -> UserRead:
        now = utc_now()
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, display_name, email, external_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.username,
                    payload.display_name,
                    payload.email,
                    payload.external_id,
                    now,
                    now,
                ),
            )
            connection.commit()
            return self.get_user(cursor.lastrowid)

    def get_user(self, user_id: int) -> UserRead:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise LookupError(f"User not found: {user_id}")
        return UserRead(**dict(row))

    def create_session(self, user_id: int, current_level: int, initial_meter: int) -> SessionRead:
        self.get_user(user_id)
        now = utc_now()
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO game_sessions
                    (user_id, current_level, fortress_meter, session_status, started_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                (user_id, current_level, initial_meter, now, now),
            )
            connection.commit()
            return self.get_session(cursor.lastrowid)

    def get_session(self, session_id: int) -> SessionRead:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM game_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise LookupError(f"Session not found: {session_id}")
        return SessionRead(**dict(row))

    def next_turn_index(self, session_id: int) -> int:
        with connect_sqlite(self.db_path) as connection:
            value = connection.execute(
                "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
        return int(value)

    def persist_turn(
        self,
        *,
        session_id: int,
        turn_index: int,
        player_input: str,
        retrieved_refs: list[EvidenceRef],
        evaluator: EvaluatorResult | None,
        npc_response: str,
        meter_before: int,
        meter_after: int,
        turn_type: str = "debate_argument",
        is_scored: bool = True,
        dialogue_brief: DialogueBrief | None = None,
    ) -> None:
        now = utc_now()
        score_delta = evaluator.score_delta if evaluator is not None else 0
        evaluator_json = evaluator.model_dump_json() if evaluator is not None else "{}"
        dialogue_brief_json = (
            dialogue_brief.model_dump_json()
            if dialogue_brief is not None
            else None
        )
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO turns (
                    session_id, turn_index, player_input, turn_type, is_scored,
                    retrieved_refs, evaluator_json, dialogue_brief_json,
                    npc_response, score_delta, meter_before, meter_after, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    turn_index,
                    player_input,
                    turn_type,
                    1 if is_scored else 0,
                    json.dumps([ref.model_dump() for ref in retrieved_refs]),
                    evaluator_json,
                    dialogue_brief_json,
                    npc_response,
                    score_delta,
                    meter_before,
                    meter_after,
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE game_sessions
                SET fortress_meter = ?, updated_at = ?
                WHERE id = ?
                """,
                (meter_after, now, session_id),
            )
            connection.commit()

    def fetch_turns(self, session_id: int) -> list[sqlite3.Row]:
        with connect_sqlite(self.db_path) as connection:
            return connection.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_index",
                (session_id,),
            ).fetchall()

    def fetch_recent_turns(self, session_id: int, limit: int) -> list[sqlite3.Row]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM turns
                WHERE session_id = ?
                ORDER BY turn_index DESC
                LIMIT ?
                """,
                (session_id, max(1, limit)),
            ).fetchall()
        return list(reversed(rows))
