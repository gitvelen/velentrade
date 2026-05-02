from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from celery import Celery

from velentrade.core.settings import Settings
from velentrade.db.session import build_engine
from velentrade.db.store import SqlAlchemyGatewayMirror
from velentrade.domain.agents.registry import build_agent_capability_profiles
from velentrade.domain.collaboration.models import AgentRun
from velentrade.domain.gateway.authority import AuthorityGateway

from .agent_dispatch import AgentRunDispatcher
from .http_runner import RunnerHttpClient


def resolve_redis_url(redis_url: str | None = None, settings: Settings | None = None) -> str:
    if redis_url:
        return redis_url
    runtime_settings = settings or Settings()
    resolved = os.getenv(runtime_settings.redis_url_env)
    if not resolved:
        raise RuntimeError(f"Redis URL is not configured. Set {runtime_settings.redis_url_env} before creating Celery.")
    return resolved


def resolve_agent_runner_url(agent_runner_url: str | None = None, settings: Settings | None = None) -> str:
    if agent_runner_url:
        return agent_runner_url.rstrip("/")
    runtime_settings = settings or Settings()
    resolved = os.getenv(runtime_settings.agent_runner_url_env)
    if not resolved:
        raise RuntimeError(
            f"Agent runner URL is not configured. Set {runtime_settings.agent_runner_url_env} before dispatching runs."
        )
    return resolved.rstrip("/")


def _register_start_agent_run_task(
    app: Celery,
    *,
    database_url: str | None,
    runner_url: str,
) -> None:
    if "velentrade.worker.start_agent_run" in app.tasks:
        return

    @app.task(name="velentrade.worker.start_agent_run")
    def start_agent_run(run_payload: dict[str, Any], model_profile_id: str) -> dict[str, Any]:
        run = AgentRun(**run_payload)
        gateway = AuthorityGateway(
            build_agent_capability_profiles(),
            store=SqlAlchemyGatewayMirror(build_engine(database_url)) if database_url else None,
        )
        dispatcher = AgentRunDispatcher(gateway=gateway, runner=RunnerHttpClient(runner_url))
        result = dispatcher.start_agent_run(run, model_profile_id=model_profile_id)
        return asdict(result)


def build_celery_app(
    *,
    broker_url: str | None = None,
    result_backend: str | None = None,
    database_url: str | None = None,
    runner_url: str | None = None,
) -> Celery:
    resolved_broker_url = resolve_redis_url(broker_url)
    resolved_backend = result_backend or resolved_broker_url
    resolved_runner_url = resolve_agent_runner_url(runner_url)

    app = Celery("velentrade")
    app.conf.update(
        broker_url=resolved_broker_url,
        result_backend=resolved_backend,
        task_default_queue="agent-runs",
        task_ignore_result=False,
        broker_connection_retry_on_startup=True,
        result_expires=3600,
        timezone="Asia/Shanghai",
    )
    _register_start_agent_run_task(app, database_url=database_url, runner_url=resolved_runner_url)
    return app
