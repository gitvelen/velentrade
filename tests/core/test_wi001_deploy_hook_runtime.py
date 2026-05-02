from __future__ import annotations

from pathlib import Path


def test_deploy_hook_supports_runtime_compose_release_mode():
    script = Path("scripts/codespec-deploy").read_text(encoding="utf-8")

    assert "release_mode" in script
    assert "runtime" in script
    assert "docker compose up -d" in script
    assert "docker compose down -v --remove-orphans" in script
    assert "deployment_method: docker-compose-runtime" in script
    assert "runtime_ready: pass" in script
