from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


try:
    import velentrade.db.models  # noqa: F401
except ImportError:
    pass
