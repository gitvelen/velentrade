from __future__ import annotations

import contextlib
import importlib
import socket
import subprocess
import threading
import time
from dataclasses import asdict
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from velentrade.domain.collaboration.models import AgentRun


def _require_module(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        raise AssertionError(f"missing runtime module: {name}") from exc


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def _postgres_container():
    port = _find_free_port()
    name = f"velentrade-worker-pg-{port}"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_USER=velentrade",
            "-e",
            "POSTGRES_PASSWORD=velentrade",
            "-e",
            "POSTGRES_DB=velentrade",
            "-p",
            f"127.0.0.1:{port}:5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        url = f"postgresql+psycopg://velentrade:velentrade@127.0.0.1:{port}/velentrade"
        deadline = time.time() + 40
        while time.time() < deadline:
            try:
                with psycopg.connect(
                    f"host=127.0.0.1 port={port} dbname=velentrade user=velentrade password=velentrade"
                ) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("select 1")
                        cursor.fetchone()
                    break
            except psycopg.Error:
                time.sleep(1)
        else:
            raise RuntimeError("PostgreSQL container did not become ready in time.")
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


@contextlib.contextmanager
def _redis_container():
    redis_module = _require_module("redis")
    port = _find_free_port()
    name = f"velentrade-worker-redis-{port}"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-p",
            f"127.0.0.1:{port}:6379",
            "redis:7-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        client = redis_module.Redis(host="127.0.0.1", port=port, decode_responses=True)
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                if client.ping():
                    break
            except redis_module.RedisError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Redis container did not become ready in time.")
        yield f"redis://127.0.0.1:{port}/0"
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


@contextlib.contextmanager
def _agent_runner_server():
    uvicorn = _require_module("uvicorn")
    service = _require_module("velentrade.agent_runner.service")
    port = _find_free_port()
    app = service.build_agent_runner_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.25)
        else:
            raise RuntimeError("agent-runner did not become ready in time.")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def test_celery_dispatch_persists_runner_artifact_via_postgres_and_redis():
    celery_worker = _require_module("celery.contrib.testing.worker")
    seed = _require_module("velentrade.db.seed")
    celery_runtime = _require_module("velentrade.worker.celery_app")

    with _postgres_container() as database_url, _redis_container() as redis_url, _agent_runner_server() as runner_url:
        config = Config(str(Path("alembic.ini")))
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        seed.apply_wi001_seed(engine)

        app = celery_runtime.build_celery_app(
            broker_url=redis_url,
            result_backend=redis_url,
            database_url=database_url,
            runner_url=runner_url,
        )

        run = AgentRun.fake(
            agent_run_id="run-celery-001",
            agent_id="investment_researcher",
            workflow_id="wf-celery-001",
            allowed_command_types=["request_evidence"],
        )

        with celery_worker.start_worker(app, perform_ping_check=False):
            result = app.send_task(
                "velentrade.worker.start_agent_run",
                kwargs={
                    "run_payload": asdict(run),
                    "model_profile_id": "fake_test",
                },
            ).get(timeout=60)

        assert result["status"] == "completed"
        assert result["agent_run_id"] == run.agent_run_id

        with engine.connect() as connection:
            artifact_count = connection.execute(text("select count(*) from artifact")).scalar_one()
            audit_count = connection.execute(text("select count(*) from audit_event")).scalar_one()
            outbox_count = connection.execute(text("select count(*) from outbox_event")).scalar_one()
            artifact_payload = connection.execute(text("select payload from artifact")).scalar_one()

        assert artifact_count == 1
        assert audit_count == 1
        assert outbox_count == 1
        assert artifact_payload["summary"].startswith("fake_test output")
