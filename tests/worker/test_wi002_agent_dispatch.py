from velentrade.agent_runner.models import AgentRunResult
from velentrade.domain.agents.registry import build_agent_capability_profiles
from velentrade.domain.collaboration.models import AgentRun
from velentrade.domain.gateway.authority import AuthorityGateway
from velentrade.worker.agent_dispatch import AgentRunDispatcher


class FailingRunner:
    def start(self, request):
        return AgentRunResult(
            agent_run_id=request.agent_run_id,
            status="failed",
            artifact_payloads=[{"artifact_type": "ResearchPackage", "summary": "must not persist"}],
            command_proposals=[],
            diagnostics={"error": "runner_unavailable"},
            process_archive_ref="process-fail",
            tool_trace_summary_ref="trace-fail",
            cost_tokens=0,
            failure_code="service_unavailable",
            failure_reason="runner unavailable",
        )


def test_worker_dispatches_agent_run_through_runner_and_does_not_fabricate_on_failure():
    profiles = build_agent_capability_profiles()
    gateway = AuthorityGateway(profiles)
    run = AgentRun.fake(
        agent_run_id="run-fail",
        agent_id="investment_researcher",
        workflow_id="wf-1",
        allowed_command_types=["request_evidence"],
    )
    dispatcher = AgentRunDispatcher(gateway=gateway, runner=FailingRunner())

    result = dispatcher.start_agent_run(run, model_profile_id="fake_test")

    assert result.status == "failed"
    assert gateway.artifact_ledger == []
    assert dispatcher.dispatch_events[0]["reason_code"] == "runner_unavailable_no_artifact"
