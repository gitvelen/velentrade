from __future__ import annotations

import subprocess
from pathlib import Path


def test_runtime_compose_wires_required_services_and_entrypoints():
    compose_file = Path("docker-compose.yml")

    assert compose_file.exists(), "docker-compose.yml must exist for local runtime deployment."

    services = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "config", "--services"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert {
        "postgres",
        "redis",
        "api",
        "worker",
        "beat",
        "agent-runner",
    }.issubset(set(services))

    rendered = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "config"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert "VELENTRADE_DATABASE_URL" in rendered
    assert "VELENTRADE_REDIS_URL" in rendered
    assert "PIP_DEFAULT_TIMEOUT" in rendered
    assert "PIP_RETRIES" in rendered
    assert "pip-cache" in rendered
    assert "/root/.cache/pip" in rendered
    assert "uvicorn --factory velentrade.api.app:build_app" in rendered
    assert "uvicorn --factory velentrade.agent_runner.service:build_agent_runner_app" in rendered
    assert "velentrade.worker.celery_runtime:celery_app" in rendered
    assert "worker --loglevel=INFO" in rendered
    assert "beat --loglevel=INFO" in rendered
