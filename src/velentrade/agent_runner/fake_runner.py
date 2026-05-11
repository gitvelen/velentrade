from __future__ import annotations

from velentrade.agent_runner.models import AgentRunResult, AgentRunStartRequest
from velentrade.model_gateway.profiles import route_model_profile


class FakeAgentRunner:
    def start(self, request: AgentRunStartRequest) -> AgentRunResult:
        profile = route_model_profile(request.model_profile_id)
        if profile.purpose != "fake_test":
            return AgentRunResult(
                agent_run_id=request.agent_run_id,
                status="failed",
                artifact_payloads=[],
                command_proposals=[],
                diagnostics={"error": "live_llm_disabled_for_p0"},
                process_archive_ref=f"process-{request.agent_run_id}",
                tool_trace_summary_ref=f"trace-{request.agent_run_id}",
                cost_tokens=0,
                failure_code="service_unavailable",
                failure_reason="Only fake_test is enabled in WI-001 automation.",
            )
        return AgentRunResult(
            agent_run_id=request.agent_run_id,
            status="completed",
            artifact_payloads=[
                {
                    "artifact_type": request.output_artifact_schema,
                    "producer": request.agent_id,
                    "summary": f"fake_test output for {request.run_goal}",
                    "context_snapshot_id": request.context_snapshot_id,
                }
            ],
            command_proposals=[
                {"command_type": command, "status": "proposed"}
                for command in sorted(request.allowed_command_types)
            ],
            diagnostics={"model_profile": profile.model_profile_id, "write_boundary": "authority_gateway_required"},
            process_archive_ref=f"process-{request.agent_run_id}",
            tool_trace_summary_ref=f"trace-{request.agent_run_id}",
            cost_tokens=0,
            business_fact_created=False,
            tool_usage_summary={"readonly_db": 0, "network": 0, "files": 0},
        )
