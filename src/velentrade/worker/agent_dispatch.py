from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from velentrade.agent_runner.models import AgentRunResult, AgentRunStartRequest
from velentrade.domain.collaboration.models import AgentRun
from velentrade.domain.gateway.authority import AuthorityGateway
from velentrade.domain.common import utc_now


class Runner(Protocol):
    def start(self, request: AgentRunStartRequest) -> AgentRunResult:
        ...


@dataclass
class AgentRunDispatcher:
    gateway: AuthorityGateway
    runner: Runner
    dispatch_events: list[dict] = field(default_factory=list)
    completed_runs: set[str] = field(default_factory=set)

    def start_agent_run(self, run: AgentRun, model_profile_id: str) -> AgentRunResult:
        if run.agent_run_id in self.completed_runs:
            request = AgentRunStartRequest(
                agent_run_id=run.agent_run_id,
                workflow_id=run.workflow_id,
                attempt_no=run.attempt_no,
                stage=run.stage,
                agent_id=run.agent_id,
                profile_version=run.profile_version,
                context_snapshot_id=run.context_snapshot_id,
                context_slice_id=run.context_slice_id,
                tool_profile_id=run.tool_profile_id,
                skill_package_versions=["fixture-skill@1.0.0"],
                model_profile_id=model_profile_id,
                run_goal=run.run_goal,
                output_artifact_schema=run.output_artifact_schema,
                allowed_command_types=run.allowed_command_types,
                budget_tokens=1000,
                timeout_seconds=30,
            )
            result = self.runner.start(request)
            self.dispatch_events.append(
                {
                    "agent_run_id": run.agent_run_id,
                    "status": result.status,
                    "reason_code": "agent_run_already_dispatched",
                    "created_at": utc_now(),
                }
            )
            return result

        request = AgentRunStartRequest(
            agent_run_id=run.agent_run_id,
            workflow_id=run.workflow_id,
            attempt_no=run.attempt_no,
            stage=run.stage,
            agent_id=run.agent_id,
            profile_version=run.profile_version,
            context_snapshot_id=run.context_snapshot_id,
            context_slice_id=run.context_slice_id,
            tool_profile_id=run.tool_profile_id,
            skill_package_versions=["fixture-skill@1.0.0"],
            model_profile_id=model_profile_id,
            run_goal=run.run_goal,
            output_artifact_schema=run.output_artifact_schema,
            allowed_command_types=run.allowed_command_types,
            budget_tokens=1000,
            timeout_seconds=30,
        )
        result = self.runner.start(request)
        if result.status != "completed":
            reason_code = "runner_timeout_no_artifact" if result.status == "timed_out" else "runner_unavailable_no_artifact"
            self.dispatch_events.append(
                {
                    "agent_run_id": run.agent_run_id,
                    "status": result.status,
                    "reason_code": reason_code,
                    "created_at": utc_now(),
                }
            )
            return result
        for index, artifact in enumerate(result.artifact_payloads):
            self.gateway.append_artifact(
                run,
                artifact_type=artifact["artifact_type"],
                payload=artifact,
                idempotency_key=f"{run.agent_run_id}:artifact:{index}",
            )
        self.completed_runs.add(run.agent_run_id)
        self.dispatch_events.append(
            {
                "agent_run_id": run.agent_run_id,
                "status": "completed",
                "reason_code": "authority_gateway_persisted_runner_artifacts",
                "created_at": utc_now(),
            }
        )
        return result
