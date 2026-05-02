from __future__ import annotations

from fastapi.testclient import TestClient

from velentrade.agent_runner.service import build_agent_runner_app


def test_runner_service_exposes_internal_start_endpoint():
    client = TestClient(build_agent_runner_app())

    response = client.post(
        "/internal/agent-runner/runs/run-1/start",
        json={
            "agent_run_id": "run-1",
            "workflow_id": "wf-1",
            "attempt_no": 1,
            "stage": "S1",
            "agent_id": "investment_researcher",
            "profile_version": "1.0.0",
            "context_snapshot_id": "ctx-1",
            "context_slice_id": "slice-1",
            "tool_profile_id": "readonly-basic",
            "skill_package_versions": ["research-pack@1.0.0"],
            "model_profile_id": "fake_test",
            "run_goal": "produce deterministic proposal",
            "output_artifact_schema": "ResearchPackage",
            "allowed_command_types": ["request_evidence"],
            "budget_tokens": 1000,
            "timeout_seconds": 30,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["agent_run_id"] == "run-1"
    assert payload["status"] == "completed"
    assert payload["business_fact_created"] is False
    assert payload["artifact_payloads"][0]["artifact_type"] == "ResearchPackage"
