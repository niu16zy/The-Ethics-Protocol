from __future__ import annotations

from backend.app.repositories.app_repository import AppRepository
from backend.app.schemas.user import UserCreate


def test_create_user_and_session(tmp_path):
    repository = AppRepository(tmp_path / "logic_fortress_app.db")
    repository.initialize()

    user = repository.create_user(
        UserCreate(username="auditor1", display_name="Ethical Auditor")
    )
    session = repository.create_session(user.id, current_level=1, initial_meter=100)

    assert user.id > 0
    assert session.user_id == user.id
    assert session.fortress_meter == 100
    assert session.session_status == "active"
