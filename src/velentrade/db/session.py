from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from velentrade.core.settings import Settings


def resolve_database_url(database_url: str | None = None, settings: Settings | None = None) -> str:
    if database_url:
        return database_url
    runtime_settings = settings or Settings()
    resolved = os.getenv(runtime_settings.database_url_env)
    if not resolved:
        raise RuntimeError(
            f"Database URL is not configured. Set {runtime_settings.database_url_env} before creating an engine."
        )
    return resolved


def build_engine(database_url: str | None = None, *, echo: bool = False) -> Engine:
    return create_engine(resolve_database_url(database_url), echo=echo, future=True)


def build_session_factory(database_url: str | None = None):
    return sessionmaker(bind=build_engine(database_url), autoflush=False, autocommit=False, future=True)
