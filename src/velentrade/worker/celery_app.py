from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Callable

from celery import Celery

from velentrade.core.settings import Settings
from velentrade.db.session import build_engine
from velentrade.db.store import SqlAlchemyGatewayMirror
from velentrade.domain.agents.registry import build_agent_capability_profiles
from velentrade.domain.collaboration.models import AgentRun
from velentrade.domain.data.persistence import SqlAlchemyDataCollectionStore, build_source_registry_from_db
from velentrade.domain.data.quality import DataRequest, RequiredField
from velentrade.domain.data.sources import DataCollectionService
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


def _data_request_from_payload(payload: dict[str, Any]) -> DataRequest:
    return DataRequest(
        request_id=payload["request_id"],
        trace_id=payload["trace_id"],
        data_domain=payload["data_domain"],
        symbol_or_scope=payload["symbol_or_scope"],
        required_usage=payload["required_usage"],
        freshness_requirement=payload["freshness_requirement"],
        required_fields=[RequiredField(**field) for field in payload["required_fields"]],
        requesting_stage=payload["requesting_stage"],
        requesting_agent_or_service=payload["requesting_agent_or_service"],
        time_range=payload.get("time_range"),
    )


def _register_collect_data_request_task(
    app: Celery,
    *,
    database_url: str | None,
    data_fetch_text: Callable[[str], str] | None,
) -> None:
    task_name = "velentrade.worker.collect_data_request"
    if task_name in app.tasks:
        app.tasks.unregister(task_name)

    @app.task(name=task_name)
    def collect_data_request(request_payload: dict[str, Any]) -> dict[str, Any]:
        if not database_url:
            raise RuntimeError("Database URL is required for scheduled data collection.")
        request = _data_request_from_payload(request_payload)
        engine = build_engine(database_url)
        store = SqlAlchemyDataCollectionStore(engine)
        registry = build_source_registry_from_db(engine, fetch_text=data_fetch_text)
        service = DataCollectionService(registry)
        cached = store.latest_dataset(
            data_domain=request.data_domain,
            symbol_or_scope=request.symbol_or_scope,
            required_usage=request.required_usage,
        )
        if cached is not None:
            service.cache_result(request, cached)
        result = service.collect(request, require_real=True, allow_cache=True)
        persisted = store.persist_result(request, result)
        return {
            **persisted,
            "selected_source_id": result.selected_source_id,
            "from_cache": result.from_cache,
            "quality_band": result.report.quality_band,
            "decision_core_status": result.report.decision_core_status,
            "execution_core_status": result.report.execution_core_status,
        }


def _install_scheduled_data_requests(
    app: Celery,
    scheduled_data_requests: list[dict[str, Any]] | None,
    data_collection_interval_seconds: int,
) -> None:
    if not scheduled_data_requests:
        return
    schedule = dict(app.conf.beat_schedule or {})
    for request_payload in scheduled_data_requests:
        request_id = request_payload["request_id"]
        schedule[f"velentrade.worker.collect_data_request:{request_id}"] = {
            "task": "velentrade.worker.collect_data_request",
            "schedule": data_collection_interval_seconds,
            "kwargs": {"request_payload": request_payload},
        }
    app.conf.beat_schedule = schedule


def build_celery_app(
    *,
    broker_url: str | None = None,
    result_backend: str | None = None,
    database_url: str | None = None,
    runner_url: str | None = None,
    data_fetch_text: Callable[[str], str] | None = None,
    scheduled_data_requests: list[dict[str, Any]] | None = None,
    data_collection_interval_seconds: int = 900,
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
    _register_collect_data_request_task(app, database_url=database_url, data_fetch_text=data_fetch_text)
    _install_scheduled_data_requests(app, scheduled_data_requests, data_collection_interval_seconds)
    return app
