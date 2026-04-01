from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    bot_token: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    proxy_public_host: str
    proxy_public_port: int
    proxy_mode: str
    proxy_tls_domain: str
    export_file_path: Path
    export_interval_seconds: int

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    proxy_mode = os.getenv("PROXY_MODE", "tls").strip().lower() or "tls"
    if proxy_mode not in {"classic", "secure", "tls"}:
        raise RuntimeError("PROXY_MODE must be one of: classic, secure, tls")

    return Settings(
        bot_token=_get_required_env("BOT_TOKEN"),
        db_host=os.getenv("DB_HOST", "db"),
        db_port=_get_int_env("DB_PORT", 5432),
        db_name=os.getenv("POSTGRES_DB", "mtproxy"),
        db_user=os.getenv("POSTGRES_USER", "mtproxy"),
        db_password=_get_required_env("POSTGRES_PASSWORD"),
        proxy_public_host=_get_required_env("PROXY_PUBLIC_HOST"),
        proxy_public_port=_get_int_env("PROXY_PORT", 443),
        proxy_mode=proxy_mode,
        proxy_tls_domain=os.getenv("PROXY_TLS_DOMAIN", "www.google.com"),
        export_file_path=Path(os.getenv("PROXY_ACTIVE_USERS_FILE", "/runtime/active_users.json")),
        export_interval_seconds=_get_int_env("EXPORT_INTERVAL_SECONDS", 60),
    )
