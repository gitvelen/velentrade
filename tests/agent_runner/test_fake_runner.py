from velentrade.agent_runner.fake_runner import FakeAgentRunner
from velentrade.agent_runner.models import AgentRunStartRequest


def test_fake_runner_is_deterministic_and_does_not_create_business_facts():
    runner = FakeAgentRunner()
    request = AgentRunStartRequest(
        agent_run_id="run-1",
        workflow_id="wf-1",
        attempt_no=1,
        stage="S1",
        agent_id="investment_researcher",
        profile_version="1.0.0",
        context_snapshot_id="ctx-1",
        context_slice_id="slice-1",
        tool_profile_id="readonly-basic",
        skill_package_versions=["research-pack@1.0.0"],
        model_profile_id="fake_test",
        run_goal="produce deterministic proposal",
        output_artifact_schema="ResearchPackage",
        allowed_command_types=["request_evidence"],
        budget_tokens=1000,
        timeout_seconds=30,
    )

    first = runner.start(request)
    second = runner.start(request)

    assert first == second
    assert first.status == "completed"
    assert first.artifact_payloads[0]["artifact_type"] == "ResearchPackage"
    assert first.business_fact_created is False
    assert first.diagnostics["write_boundary"] == "authority_gateway_required"
