from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = "test"
    single_owner: bool = True
    database_url_env: str = "VELENTRADE_DATABASE_URL"
    redis_url_env: str = "VELENTRADE_REDIS_URL"
    secret_key_env: str = "VELENTRADE_SECRET_KEY"
    field_encryption_key_env: str = "VELENTRADE_FIELD_ENCRYPTION_KEY"
