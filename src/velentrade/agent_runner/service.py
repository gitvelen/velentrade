from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from velentrade.agent_runner.fake_runner import FakeAgentRunner
from velentrade.agent_runner.models import AgentRunStartRequest
from velentrade.domain.common import new_id, utc_now


def _success(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "data": payload,
        "meta": {"trace_id": new_id("trace"), "generated_at": utc_now()},
    }


def build_agent_runner_app(runner: FakeAgentRunner | None = None) -> FastAPI:
    app = FastAPI(title="velentrade-agent-runner", version="0.1.0")
    runtime_runner = runner or FakeAgentRunner()

    @app.post("/internal/agent-runner/runs/{agent_run_id}/start")
    def start_agent_run(agent_run_id: str, request: AgentRunStartRequest):
        if agent_run_id != request.agent_run_id:
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "CONFLICT",
                        "message": "Path agent_run_id does not match request body.",
                        "trace_id": new_id("trace"),
                        "retryable": False,
                        "reason_code": "agent_run_id_mismatch",
                        "details": None,
                    }
                },
            )
        result = runtime_runner.start(request)
        return _success(asdict(result))

    return app
