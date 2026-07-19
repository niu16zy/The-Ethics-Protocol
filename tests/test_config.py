from __future__ import annotations

from backend.app.core.config import get_settings, load_dotenv_file


def test_load_dotenv_file_does_not_override_existing_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=from-file\nGROQ_MODEL=llama-3.3-70b-versatile\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GROQ_API_KEY", "from-shell")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    load_dotenv_file(env_file)

    settings = get_settings()
    assert settings.groq_api_key == "from-shell"
    assert settings.groq_model == "llama-3.3-70b-versatile"


def test_get_settings_auto_enables_groq_when_key_is_configured(monkeypatch):
    monkeypatch.delenv("LOGIC_FORTRESS_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")

    settings = get_settings()

    assert settings.llm_provider == "groq"
    assert settings.groq_api_key == "fake-key"
    assert settings.groq_timeout_seconds == 90
    assert settings.groq_max_output_tokens == 700
    assert settings.llm_max_attempts == 2


def test_get_settings_reads_timeout_and_attempts(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("GROQ_MAX_OUTPUT_TOKENS", "512")
    monkeypatch.setenv("LOGIC_FORTRESS_LLM_MAX_ATTEMPTS", "3")

    settings = get_settings()

    assert settings.groq_timeout_seconds == 120
    assert settings.groq_max_output_tokens == 512
    assert settings.llm_max_attempts == 3


def test_get_settings_reads_fox_provider(monkeypatch):
    monkeypatch.setenv("LOGIC_FORTRESS_LLM_PROVIDER", "fox")
    monkeypatch.setenv("FOX_API_KEY", "fox-key")
    monkeypatch.setenv("FOX_MODEL", "gpt-5.5")
    monkeypatch.setenv("FOX_BASE_URL", "https://code.newcli.com/codex/v1")
    monkeypatch.setenv("FOX_REASONING_EFFORT", "medium")
    monkeypatch.setenv("FOX_DISABLE_RESPONSE_STORAGE", "true")

    settings = get_settings()

    assert settings.llm_provider == "fox"
    assert settings.fox_api_key == "fox-key"
    assert settings.fox_model == "gpt-5.5"
    assert settings.fox_base_url == "https://code.newcli.com/codex/v1"
    assert settings.fox_reasoning_effort == "medium"
    assert settings.fox_disable_response_storage is True
