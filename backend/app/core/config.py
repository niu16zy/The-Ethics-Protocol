from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    knowledge_db_path: Path
    app_db_path: Path
    llm_provider: str
    groq_api_key: str | None
    groq_model: str
    groq_timeout_seconds: int
    llm_max_attempts: int
    groq_max_output_tokens: int = 700
    default_top_k: int = 3
    initial_fortress_meter: int = 100


def load_dotenv_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv_file(project_root / ".env")
    knowledge_db_path = Path(
        os.getenv("LOGIC_FORTRESS_KNOWLEDGE_DB", project_root / "course_content.db")
    )
    app_db_path = Path(
        os.getenv("LOGIC_FORTRESS_APP_DB", project_root / "logic_fortress_app.db")
    )
    groq_api_key = os.getenv("GROQ_API_KEY")
    configured_provider = os.getenv("LOGIC_FORTRESS_LLM_PROVIDER")
    llm_provider = (configured_provider or ("groq" if groq_api_key else "rules")).lower()
    return Settings(
        project_root=project_root,
        knowledge_db_path=knowledge_db_path,
        app_db_path=app_db_path,
        llm_provider=llm_provider,
        groq_api_key=groq_api_key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_timeout_seconds=_int_env("GROQ_TIMEOUT_SECONDS", 90),
        llm_max_attempts=_int_env("LOGIC_FORTRESS_LLM_MAX_ATTEMPTS", 2),
        groq_max_output_tokens=_int_env("GROQ_MAX_OUTPUT_TOKENS", 700),
    )


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return max(1, value)
