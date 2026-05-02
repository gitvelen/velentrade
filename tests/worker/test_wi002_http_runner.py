from __future__ import annotations

from velentrade.agent_runner.models import AgentRunStartRequest
from velentrade.worker.http_runner import RunnerHttpClient


def _start_request() -> AgentRunStartRequest:
    return AgentRunStartRequest(
        agent_run_id="run-http-timeout",
        workflow_id="wf-http-timeout",
        attempt_no=1,
        stage="S1",
        agent_id="investment_researcher",
        profile_version="v1",
        context_snapshot_id="ctx-v1",
        context_slice_id="slice-v1",
        tool_profile_id="tool-v1",
        skill_package_versions=["skill-v1"],
        model_profile_id="fake_test",
        run_goal="collect evidence",
        output_artifact_schema="ResearchPackage",
        allowed_command_types=["request_evidence"],
        budget_tokens=1000,
        timeout_seconds=30,
    )


def test_runner_http_client_maps_socket_timeout_to_timed_out_without_artifacts(monkeypatch):
    def raise_timeout(*_args, **_kwargs):
        raise TimeoutError("agent runner timed out")

    monkeypatch.setattr("velentrade.worker.http_runner.request.urlopen", raise_timeout)

    result = RunnerHttpClient("http://agent-runner.local", timeout_seconds=1).start(_start_request())

    assert result.status == "timed_out"
    assert result.artifact_payloads == []
    assert result.failure_code == "budget_timeout"
    assert result.failure_reason == "agent_runner_timeout"
