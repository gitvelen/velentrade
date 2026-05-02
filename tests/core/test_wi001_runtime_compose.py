from __future__ import annotations

import subprocess
from pathlib import Path


def test_runtime_compose_wires_required_services_and_entrypoints():
    compose_file = Path("docker-compose.yml")
    dockerfile = Path("Dockerfile")
    pyproject = Path("pyproject.toml")

    assert compose_file.exists(), "docker-compose.yml must exist for local runtime deployment."
    assert dockerfile.exists(), "runtime compose must build or reuse a prebuilt application image."
    assert pyproject.exists()

    services = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "config", "--services"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert {
        "postgres",
        "redis",
        "migrate",
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

    dockerfile_text = dockerfile.read_text(encoding="utf-8")
    assert "wheelhouse" in dockerfile_text
    assert "pip install" in dockerfile_text
    assert "PYTHONPATH=/app/src" in dockerfile_text
    assert "PIP_INDEX_URL" in dockerfile_text
    assert "mirrors.cloud.aliyuncs.com" in dockerfile_text
    assert "/tmp/requirements.txt" in dockerfile_text
    assert "-e ." not in dockerfile_text
    assert "frontend/dist" in dockerfile_text
    assert "apt-get" not in dockerfile_text
    assert "psycopg[binary]" in pyproject.read_text(encoding="utf-8")
    assert dockerfile_text.index("COPY wheelhouse") < dockerfile_text.index("COPY src")
    assert dockerfile_text.index("pip install") < dockerfile_text.index("COPY src")

    assert "build:" in rendered
    assert "dockerfile: Dockerfile" in rendered
    assert "image: velentrade-runtime:local" in rendered
    assert "condition: service_completed_successfully" in rendered
    assert "VELENTRADE_DATABASE_URL" in rendered
    assert "VELENTRADE_REDIS_URL" in rendered
    assert "pip install -e ." not in rendered
    assert "pip-cache" not in rendered
    assert "/root/.cache/pip" not in rendered
    assert "alembic upgrade head" in rendered
    assert "uvicorn --factory velentrade.api.app:build_app" in rendered
    assert "uvicorn --factory velentrade.agent_runner.service:build_agent_runner_app" in rendered
    assert "velentrade.worker.celery_runtime:celery_app" in rendered
    assert "worker --loglevel=INFO" in rendered
    assert "beat --loglevel=INFO" in rendered
