from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from velentrade.db.session import build_engine
from velentrade.db.store import SqlAlchemyGatewayMirror
from velentrade.domain.agents.registry import (
    build_agent_capability_profiles,
    build_agent_capability_config_read_model,
    build_agent_profile_read_model,
    build_team_read_model,
)
from velentrade.domain.collaboration.models import AgentRun, CollaborationCommand, HandoffPacket
from velentrade.domain.common import new_id, utc_now
from velentrade.domain.finance.boundary import FinanceProfileService
from velentrade.domain.gateway.authority import AuthorityGateway
from velentrade.domain.memory.models import MemoryCapture
from velentrade.domain.observability.health import ObservabilityCollector
from velentrade.domain.workflow.runtime import RequestBrief, WorkflowRuntime

from .schemas import (
    CollaborationCommandRequest,
    CreateRequestBriefRequest,
    CreateMemoryItemRequest,
    GatewayArtifactWriteRequest,
    GatewayEventWriteRequest,
    GatewayHandoffWriteRequest,
    GatewayMemoryWriteRequest,
    MemoryRelationWriteRequest,
    RequestBriefConfirmationRequest,
)


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _success(payload: Any) -> dict[str, Any]:
    return {
        "data": _serialize(payload),
        "meta": {"trace_id": new_id("trace"), "generated_at": utc_now()},
    }


def _error(status_code: int, code: str, message: str, *, reason_code: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "trace_id": new_id("trace"),
                "retryable": False,
                "reason_code": reason_code,
                "details": None,
            }
        },
    )


class ApiRuntime:
    def __init__(self, database_url: str | None = None) -> None:
        self.profiles = build_agent_capability_profiles()
        store = SqlAlchemyGatewayMirror(build_engine(database_url)) if database_url else None
        self.gateway = AuthorityGateway(self.profiles, store=store)
        self.finance = FinanceProfileService()
        self.observability = ObservabilityCollector()
        self.workflow = WorkflowRuntime()
        self.request_briefs: dict[str, RequestBrief] = {}
        self.confirmed_brief_ids: set[str] = set()
        self.agent_runs = {
            f"run-{agent_id}": AgentRun.fake(
                agent_run_id=f"run-{agent_id}",
                agent_id=agent_id,
                workflow_id="wf-1",
                allowed_command_types=profile.write_policy.command_types,
                output_artifact_schema=profile.output_contracts[0].artifact_type,
            )
            for agent_id, profile in self.profiles.items()
        }
        self.owner_memory_counter = 0

    def require_run(self, run_id: str) -> AgentRun | None:
        return self.agent_runs.get(run_id)

    def next_owner_capture_run(self) -> AgentRun:
        self.owner_memory_counter += 1
        run_id = f"run-owner-memory-{self.owner_memory_counter}"
        run = AgentRun.fake(
            agent_run_id=run_id,
            agent_id="investment_researcher",
            workflow_id="wf-owner-memory",
            allowed_command_types=["propose_knowledge_promotion"],
            output_artifact_schema="ResearchPackage",
            stage="capture",
        )
        self.agent_runs[run_id] = run
        return run


def _request_brief_read_model(brief: RequestBrief) -> dict[str, Any]:
    return {
        "brief_id": brief.brief_id,
        "raw_input_ref": brief.raw_input_ref,
        "route_type": brief.route_type,
        "route_confidence": brief.route_confidence,
        "asset_scope": brief.asset_scope,
        "authorization_boundary": brief.authorization_boundary,
        "owner_confirmation_status": brief.owner_confirmation_status,
        "route_reason": brief.route_reason,
        "created_at": brief.created_at,
        "suggested_semantic_lead": brief.suggested_semantic_lead,
        "process_authority": brief.process_authority,
        "predicted_outputs": list(brief.predicted_outputs),
        "creates_agent_run": brief.creates_agent_run,
        "forbidden_action_reason_code": brief.forbidden_action_reason_code,
        "version": 1,
    }


def _task_read_model(task, workflow_id: str | None = None) -> dict[str, Any]:
    payload = {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "priority": task.priority,
        "owner_role": task.owner_role,
        "current_state": task.current_state,
        "reason_code": task.reason_code,
        "artifact_refs": list(task.artifact_refs),
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "blocked_reason": task.blocked_reason,
        "closed_at": task.closed_at,
    }
    if workflow_id is not None:
        payload["workflow_id"] = workflow_id
    return payload


def _workflow_read_model(workflow) -> dict[str, Any]:
    return {
        "workflow_id": workflow.workflow_id,
        "task_id": workflow.task_id,
        "workflow_type": workflow.workflow_type,
        "current_stage": workflow.current_stage,
        "current_attempt_no": workflow.current_attempt_no,
        "status": workflow.status,
        "context_snapshot_id": workflow.context_snapshot_id,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "stages": [
            {
                "workflow_id": stage.workflow_id,
                "attempt_no": stage.attempt_no,
                "stage": stage.stage,
                "node_status": stage.node_status,
                "responsible_role": stage.responsible_role,
                "input_artifact_refs": list(stage.input_artifact_refs),
                "output_artifact_refs": list(stage.output_artifact_refs),
                "reason_code": stage.reason_code,
                "started_at": stage.started_at,
                "completed_at": stage.completed_at,
                "stage_version": stage.stage_version,
            }
            for stage in workflow.stages
        ],
    }


def build_app(runtime: ApiRuntime | None = None) -> FastAPI:
    app = FastAPI(title="velentrade-api", version="0.1.0")
    api_runtime = runtime or ApiRuntime()

    @app.get("/api/team")
    def get_team() -> dict[str, Any]:
        return _success(build_team_read_model())

    @app.get("/api/team/{agent_id}")
    def get_agent_profile(agent_id: str):
        try:
            return _success(build_agent_profile_read_model(agent_id))
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown agent: {agent_id}")

    @app.get("/api/team/{agent_id}/capability-config")
    def get_agent_capability_config(agent_id: str):
        try:
            return _success(build_agent_capability_config_read_model(agent_id))
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown agent: {agent_id}")

    @app.get("/api/finance/overview")
    def get_finance_overview():
        return _success(api_runtime.finance.finance_overview())

    @app.get("/api/devops/health")
    def get_devops_health():
        return _success(api_runtime.observability.devops_health_read_model())

    @app.post("/api/requests/briefs")
    def create_request_brief(request: CreateRequestBriefRequest):
        scope = request.requested_scope or {}
        brief = RequestBrief.route_owner_request(
            brief_id=new_id("brief"),
            raw_input_ref=request.raw_text,
            intent=str(scope.get("intent", "learn_hot_event")),
            asset_scope=str(scope.get("asset_scope", "a_share_common_stock")),
            target_action=str(scope.get("target_action", "research")),
            route_confidence=float(scope.get("route_confidence", 0.95)),
            authorization_boundary=request.authorization_boundary or "request_brief_only",
        )
        api_runtime.request_briefs[brief.brief_id] = brief
        return _success(_request_brief_read_model(brief))

    @app.post("/api/requests/briefs/{brief_id}/confirmation")
    def confirm_request_brief(brief_id: str, request: RequestBriefConfirmationRequest):
        brief = api_runtime.request_briefs.get(brief_id)
        if brief is None:
            return _error(404, "NOT_FOUND", f"Unknown request brief: {brief_id}")
        if brief_id in api_runtime.confirmed_brief_ids:
            return _error(409, "CONFLICT", "Request brief has already been decided.", reason_code="brief_already_decided")
        if request.decision not in {"confirm", "edit", "cancel"}:
            return _error(422, "VALIDATION_ERROR", "Unsupported confirmation decision.", reason_code="invalid_decision")

        owner_decision = {"confirm": "confirmed", "cancel": "canceled", "edit": "edited"}[request.decision]
        task = api_runtime.workflow.confirm_request_brief(brief, owner_decision=owner_decision)
        api_runtime.confirmed_brief_ids.add(brief_id)
        workflow_id = None
        if task.current_state == "ready" and task.task_type == "investment_workflow":
            workflow = api_runtime.workflow.create_investment_workflow(task, context_snapshot_id="ctx-v1")
            workflow_id = workflow.workflow_id
        return _success(_task_read_model(task, workflow_id=workflow_id))

    @app.get("/api/tasks")
    def get_tasks():
        return _success({
            "task_center": [_task_read_model(task) for task in api_runtime.workflow.tasks.values()],
        })

    @app.get("/api/workflows/{workflow_id}")
    def get_workflow(workflow_id: str):
        workflow = api_runtime.workflow.workflows.get(workflow_id)
        if workflow is None:
            return _error(404, "NOT_FOUND", f"Unknown workflow: {workflow_id}")
        return _success(_workflow_read_model(workflow))

    @app.post("/api/collaboration/commands")
    def create_collaboration_command(request: CollaborationCommandRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        command = CollaborationCommand.request(
            command_id=new_id("command"),
            command_type=request.command_type,
            workflow_id=request.workflow_id,
            attempt_no=request.attempt_no,
            stage=request.stage,
            source_agent_run_id=request.source_agent_run_id,
            source_agent_id=run.agent_id,
            target_agent_id_or_service=request.target_agent_id_or_service,
            payload=request.payload,
            requested_admission_type=request.requested_admission_type,
        )
        result = api_runtime.gateway.append_command(run, command, idempotency_key=command.command_id)
        if not result.accepted:
            return _error(403, "COMMAND_NOT_ALLOWED", "Command is not allowed for this AgentRun.", reason_code=result.reason_code)
        accepted = api_runtime.gateway.command_ledger[-1]
        return _success(accepted)

    @app.post("/api/gateway/artifacts")
    def write_artifact(request: GatewayArtifactWriteRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        result = api_runtime.gateway.append_artifact(
            run,
            artifact_type=request.artifact_type,
            payload=request.payload,
            idempotency_key=request.idempotency_key,
            schema_version=request.schema_version,
            source_refs=request.source_refs,
        )
        if not result.accepted:
            return _error(403, "PERMISSION_DENIED", "Artifact type is not allowed.", reason_code=result.reason_code)
        return _success(result)

    @app.post("/api/gateway/events")
    def write_event(request: GatewayEventWriteRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        result = api_runtime.gateway.append_event(
            run,
            event_type=request.event_type,
            payload=request.payload,
            idempotency_key=request.idempotency_key,
        )
        return _success(result)

    @app.post("/api/gateway/handoffs")
    def write_handoff(request: GatewayHandoffWriteRequest):
        handoff = HandoffPacket.create(
            handoff_id=new_id("handoff"),
            workflow_id=request.workflow_id,
            attempt_no=request.attempt_no,
            from_stage=request.from_stage,
            to_stage_or_agent=request.to_stage_or_agent,
            producer_agent_id_or_service=request.producer_agent_id_or_service,
            source_artifact_refs=request.source_artifact_refs,
            summary=request.summary,
        )
        if request.open_questions:
            handoff = HandoffPacket(
                **{
                    **handoff.__dict__,
                    "open_questions": request.open_questions,
                    "blockers": request.blockers,
                    "decisions_made": request.decisions_made,
                    "invalidated_artifacts": request.invalidated_artifacts,
                    "preserved_artifacts": request.preserved_artifacts,
                }
            )
        result = api_runtime.gateway.append_handoff(handoff, idempotency_key=request.idempotency_key)
        return _success(result)

    @app.post("/api/gateway/memory-items")
    def write_memory(request: GatewayMemoryWriteRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        capture = MemoryCapture(
            capture_id=new_id("capture"),
            source_type=request.operation,
            source_refs=request.source_refs,
            content_markdown=request.content_markdown,
            payload=request.payload or {},
            suggested_memory_type="research_note",
            sensitivity=request.sensitivity,
            producer_agent_id=run.agent_id,
        )
        result = api_runtime.gateway.capture_memory(capture, idempotency_key=request.idempotency_key)
        return _success(result)

    @app.post("/api/knowledge/memory-items")
    def create_memory_item(request: CreateMemoryItemRequest):
        run = api_runtime.next_owner_capture_run()
        capture = MemoryCapture(
            capture_id=new_id("capture"),
            source_type=request.source_type,
            source_refs=request.source_refs,
            content_markdown=request.content_markdown,
            payload={"tags": request.tags},
            suggested_memory_type=request.suggested_memory_type,
            sensitivity=request.sensitivity,
            producer_agent_id=run.agent_id,
        )
        api_runtime.gateway.capture_memory(capture, idempotency_key=f"owner-memory-{run.agent_run_id}")
        memory = api_runtime.gateway.get_memory_read_model(api_runtime.gateway.memory_items[-1].memory_id)
        return _success(memory)

    @app.get("/api/artifacts/{artifact_id}")
    def get_artifact(artifact_id: str):
        artifact = next(
            (item for item in api_runtime.gateway.artifact_ledger if item["artifact_id"] == artifact_id),
            None,
        )
        if artifact is None and api_runtime.gateway.store is not None:
            artifact = api_runtime.gateway.store.get_artifact(artifact_id)
        if artifact is None:
            return _error(404, "NOT_FOUND", f"Unknown artifact: {artifact_id}")
        return _success(artifact)

    @app.get("/api/workflows/{workflow_id}/agent-runs")
    def get_agent_runs(workflow_id: str):
        runs = [run for run in api_runtime.agent_runs.values() if run.workflow_id == workflow_id]
        return _success(runs)

    @app.get("/api/workflows/{workflow_id}/collaboration-events")
    def get_collaboration_events(workflow_id: str):
        events = [event for event in api_runtime.gateway.event_ledger if event.workflow_id == workflow_id]
        if not events and api_runtime.gateway.store is not None:
            events = api_runtime.gateway.store.list_events(workflow_id)
        return _success(events)

    @app.get("/api/workflows/{workflow_id}/handoffs")
    def get_handoffs(workflow_id: str):
        handoffs = [handoff for handoff in api_runtime.gateway.handoff_ledger if handoff.workflow_id == workflow_id]
        if not handoffs and api_runtime.gateway.store is not None:
            handoffs = api_runtime.gateway.store.list_handoffs(workflow_id)
        return _success(handoffs)

    @app.get("/api/knowledge/memory-items")
    def list_memory_items():
        memory_items = api_runtime.gateway.list_memory_read_models()
        if not memory_items and api_runtime.gateway.store is not None:
            memory_items = api_runtime.gateway.store.list_memory_read_models()
        return _success(memory_items)

    @app.get("/api/knowledge/memory-items/{memory_id}")
    def get_memory_item(memory_id: str):
        memory = api_runtime.gateway.get_memory_read_model(memory_id)
        if memory is None and api_runtime.gateway.store is not None:
            memory = api_runtime.gateway.store.get_memory_read_model(memory_id)
        if memory is None:
            return _error(404, "NOT_FOUND", f"Unknown memory item: {memory_id}")
        return _success(memory)

    @app.post("/api/knowledge/memory-items/{memory_id}/relations")
    def create_memory_relation(memory_id: str, request: MemoryRelationWriteRequest):
        try:
            relation = api_runtime.gateway.append_memory_relation(
                memory_id=memory_id,
                target_ref=request.target_ref,
                relation_type=request.relation_type,
                reason=request.reason,
                evidence_refs=request.evidence_refs,
                client_seen_version_id=request.client_seen_version_id,
            )
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown memory item: {memory_id}")
        except ValueError:
            return _error(409, "CONFLICT", "Memory version mismatch.", reason_code="client_seen_version_mismatch")
        return _success(relation)

    return app
