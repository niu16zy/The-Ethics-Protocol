from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api import dependencies
from backend.app.core.config import Settings
from backend.app.main import create_app


def test_api_create_user_session_and_turn(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=tmp_path / "logic_fortress_app.db",
            llm_provider="rules",
            groq_api_key=None,
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
        )

    dependencies.settings = test_settings
    app = create_app()
    client = TestClient(app)

    user_response = client.post(
        "/api/users",
        json={"username": "apiuser", "display_name": "API User"},
    )
    assert user_response.status_code == 201

    session_response = client.post(
        "/api/sessions",
        json={"user_id": user_response.json()["id"]},
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    saves_response = client.post(
        f"/api/sessions/{session_id}/saves",
        json={"save_name": "manual checkpoint", "save_payload": {}},
    )
    assert saves_response.status_code == 404

    resume_response = client.post(f"/api/sessions/{session_id}/resume")
    assert resume_response.status_code == 404

    turn_response = client.post(
        f"/api/sessions/{session_id}/turns",
        json={
            "player_input": "Transparency matters because users need to understand AI recommendations."
        },
    )
    assert turn_response.status_code == 200
    body = turn_response.json()
    assert body["retrieved_refs"]
    assert body["evaluator"]["verdict"] in {
        "strong",
        "partial",
        "weak",
        "unsupported",
        "off_topic",
    }
    assert body["evaluator_source"] in {"rules", "llm", "fallback"}
    assert body["persona_source"] in {"rules", "llm", "fallback"}

    dialogue_response = client.post(
        f"/api/sessions/{session_id}/turns",
        json={"player_input": "你是谁？你的AI系统是什么？"},
    )
    assert dialogue_response.status_code == 200
    dialogue_body = dialogue_response.json()
    assert dialogue_body["turn_type"] == "in_world_question"
    assert dialogue_body["is_scored"] is False
    assert dialogue_body["evaluator"] is None
    assert dialogue_body["retrieved_refs"] == []
    assert dialogue_body["score_delta"] == 0
