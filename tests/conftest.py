from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conversation_success_coach.app import create_app
from conversation_success_coach.config import Settings


@pytest.fixture
def app(tmp_path: Path):
    static_dir = Path(__file__).resolve().parents[1] / "src" / "conversation_success_coach" / "web"
    return create_app(
        Settings(
            database_path=str(tmp_path / "coach.db"),
            host="127.0.0.1",
            port=8103,
            demo_seed=True,
            docs_enabled=True,
            static_dir=static_dir,
        )
    )


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
