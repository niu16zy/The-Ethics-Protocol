from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_sqlite(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_app_db(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            email TEXT,
            external_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            current_level INTEGER NOT NULL DEFAULT 1,
            fortress_meter INTEGER NOT NULL DEFAULT 100,
            session_status TEXT NOT NULL DEFAULT 'active',
            started_at TEXT NOT NULL,
            ended_at TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            turn_index INTEGER NOT NULL,
            player_input TEXT NOT NULL,
            turn_type TEXT NOT NULL DEFAULT 'debate_argument',
            is_scored INTEGER NOT NULL DEFAULT 1,
            retrieved_refs TEXT NOT NULL,
            evaluator_json TEXT,
            dialogue_brief_json TEXT,
            npc_response TEXT NOT NULL,
            score_delta INTEGER NOT NULL,
            meter_before INTEGER NOT NULL,
            meter_after INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES game_sessions(id),
            UNIQUE (session_id, turn_index)
        )
        """
    )
    _ensure_column(
        connection,
        "turns",
        "turn_type",
        "TEXT NOT NULL DEFAULT 'debate_argument'",
    )
    _ensure_column(
        connection,
        "turns",
        "is_scored",
        "INTEGER NOT NULL DEFAULT 1",
    )
    _ensure_column(connection, "turns", "dialogue_brief_json", "TEXT")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            save_name TEXT NOT NULL,
            save_payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES game_sessions(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            badge_name TEXT NOT NULL,
            unlocked_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (session_id) REFERENCES game_sessions(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS final_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL UNIQUE,
            strengths TEXT NOT NULL,
            misconceptions TEXT NOT NULL,
            recommended_topics TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES game_sessions(id)
        )
        """
    )
    connection.commit()


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = set()
    for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall():
        columns.add(str(row["name"] if isinstance(row, sqlite3.Row) else row[1]))
    if column_name in columns:
        return
    connection.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
    )
