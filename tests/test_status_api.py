from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api import dependencies
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.llm_client import FoxResponsesClient, GroqChatCompletionsClient


def test_llm_status_reports_configured_client(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=tmp_path / "logic_fortress_app.db",
            llm_provider="groq",
            groq_api_key="fake-key",
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
            groq_max_output_tokens=700,
        )

    dependencies.settings = test_settings
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/llm/status")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "groq"
    assert body["model"] == "llama-3.3-70b-versatile"
    assert body["timeout_seconds"] == 90
    assert body["max_attempts"] == 2
    assert body["max_output_tokens"] == 700
    assert body["api_key_configured"] is True
    assert body["client_configured"] is True
    assert body["using_rules_fallback"] is False


def test_llm_client_accepts_persona_specific_output_budget(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=tmp_path / "logic_fortress_app.db",
            llm_provider="groq",
            groq_api_key="fake-key",
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
            groq_max_output_tokens=700,
        )

    dependencies.settings = test_settings

    client = dependencies.llm_client(max_output_tokens=300)

    assert isinstance(client, GroqChatCompletionsClient)
    assert client.max_output_tokens == 300


def test_llm_status_reports_fox_client(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=tmp_path / "logic_fortress_app.db",
            llm_provider="fox",
            groq_api_key=None,
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
            groq_max_output_tokens=700,
            fox_api_key="fox-key",
            fox_model="gpt-5.5",
            fox_base_url="https://code.newcli.com/codex/v1",
            fox_reasoning_effort="high",
            fox_disable_response_storage=True,
        )

    dependencies.settings = test_settings
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/llm/status")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "fox"
    assert body["model"] == "gpt-5.5"
    assert body["api_key_configured"] is True
    assert body["client_configured"] is True
    assert body["using_rules_fallback"] is False


def test_llm_client_builds_fox_client_with_persona_budget(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    def test_settings() -> Settings:
        return Settings(
            project_root=project_root,
            knowledge_db_path=project_root / "course_content.db",
            app_db_path=tmp_path / "logic_fortress_app.db",
            llm_provider="fox",
            groq_api_key=None,
            groq_model="llama-3.3-70b-versatile",
            groq_timeout_seconds=90,
            llm_max_attempts=2,
            groq_max_output_tokens=700,
            fox_api_key="fox-key",
            fox_model="gpt-5.5",
            fox_base_url="https://code.newcli.com/codex/v1",
            fox_reasoning_effort="medium",
            fox_disable_response_storage=True,
        )

    dependencies.settings = test_settings

    client = dependencies.llm_client(max_output_tokens=300)

    assert isinstance(client, FoxResponsesClient)
    assert client.model == "gpt-5.5"
    assert client.max_output_tokens == 300
    assert client.reasoning_effort == "medium"
