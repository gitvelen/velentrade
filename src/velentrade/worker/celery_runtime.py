from __future__ import annotations

from .celery_app import build_celery_app


celery_app = build_celery_app()
