from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any
from urllib import error, request

from velentrade.agent_runner.models import AgentRunResult, AgentRunStartRequest


class RunnerHttpClient:
    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def start(self, runtime_request: AgentRunStartRequest) -> AgentRunResult:
        payload = json.dumps(asdict(runtime_request)).encode("utf-8")
        http_request = request.Request(
            url=f"{self.base_url}/internal/agent-runner/runs/{runtime_request.agent_run_id}/start",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return AgentRunResult(
                agent_run_id=runtime_request.agent_run_id,
                status="failed",
                artifact_payloads=[],
                command_proposals=[],
                diagnostics={"error": "runner_http_error", "detail": detail},
                process_archive_ref=f"process-{runtime_request.agent_run_id}",
                tool_trace_summary_ref=f"trace-{runtime_request.agent_run_id}",
                cost_tokens=0,
                failure_code="service_unavailable",
                failure_reason=f"agent_runner_http_{exc.code}",
            )
        except error.URLError as exc:
            return AgentRunResult(
                agent_run_id=runtime_request.agent_run_id,
                status="failed",
                artifact_payloads=[],
                command_proposals=[],
                diagnostics={"error": "runner_unreachable", "detail": str(exc.reason)},
                process_archive_ref=f"process-{runtime_request.agent_run_id}",
                tool_trace_summary_ref=f"trace-{runtime_request.agent_run_id}",
                cost_tokens=0,
                failure_code="service_unavailable",
                failure_reason="agent_runner_unreachable",
            )

        result_payload: dict[str, Any] = body["data"]
        return AgentRunResult(**result_payload)
