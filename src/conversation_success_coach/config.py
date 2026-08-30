"""Runtime configuration with safe local-demo defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings.

    The product intentionally has no provider credentials or outbound-network
    configuration. All analysis is local and deterministic.
    """

    database_path: str = "data/conversation_success_coach.db"
    host: str = "127.0.0.1"
    port: int = 8103
    demo_seed: bool = True
    docs_enabled: bool = True
    static_dir: Path = Path(__file__).parent / "web"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_path=os.getenv(
                "CSC_DATABASE_PATH",
                "data/conversation_success_coach.db",
            ),
            host=os.getenv("CSC_HOST", "127.0.0.1"),
            port=int(os.getenv("CSC_PORT", "8103")),
            demo_seed=_env_bool("CSC_DEMO_SEED", True),
            docs_enabled=_env_bool("CSC_DOCS_ENABLED", True),
        )
