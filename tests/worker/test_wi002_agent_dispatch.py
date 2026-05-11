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


class TimedOutRunner:
    def start(self, request):
        return AgentRunResult(
            agent_run_id=request.agent_run_id,
            status="timed_out",
            artifact_payloads=[{"artifact_type": "ResearchPackage", "summary": "must not persist"}],
            command_proposals=[],
            diagnostics={"error": "timeout"},
            process_archive_ref="process-timeout",
            tool_trace_summary_ref="trace-timeout",
            cost_tokens=0,
            failure_code="budget_timeout",
            failure_reason="runner timed out",
        )


class SuccessfulRunner:
    def __init__(self):
        self.calls = 0

    def start(self, request):
        self.calls += 1
        return AgentRunResult(
            agent_run_id=request.agent_run_id,
            status="completed",
            artifact_payloads=[{"artifact_type": "ResearchPackage", "summary": "persist once"}],
            command_proposals=[],
            diagnostics={},
            process_archive_ref="process-ok",
            tool_trace_summary_ref="trace-ok",
            cost_tokens=0,
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


def test_worker_timeout_does_not_fabricate_artifact_and_records_timeout_reason():
    profiles = build_agent_capability_profiles()
    gateway = AuthorityGateway(profiles)
    run = AgentRun.fake(
        agent_run_id="run-timeout",
        agent_id="investment_researcher",
        workflow_id="wf-1",
        allowed_command_types=["request_evidence"],
    )
    dispatcher = AgentRunDispatcher(gateway=gateway, runner=TimedOutRunner())

    result = dispatcher.start_agent_run(run, model_profile_id="fake_test")

    assert result.status == "timed_out"
    assert gateway.artifact_ledger == []
    assert dispatcher.dispatch_events[0]["reason_code"] == "runner_timeout_no_artifact"


def test_worker_dispatch_is_idempotent_for_same_agent_run():
    profiles = build_agent_capability_profiles()
    gateway = AuthorityGateway(profiles)
    run = AgentRun.fake(
        agent_run_id="run-duplicate",
        agent_id="investment_researcher",
        workflow_id="wf-1",
        allowed_command_types=["request_evidence"],
    )
    runner = SuccessfulRunner()
    dispatcher = AgentRunDispatcher(gateway=gateway, runner=runner)

    first = dispatcher.start_agent_run(run, model_profile_id="fake_test")
    second = dispatcher.start_agent_run(run, model_profile_id="fake_test")

    assert first.status == "completed"
    assert second.status == "completed"
    assert runner.calls == 1
    assert len(gateway.artifact_ledger) == 1
    assert dispatcher.dispatch_events[-1]["reason_code"] == "agent_run_already_dispatched"
