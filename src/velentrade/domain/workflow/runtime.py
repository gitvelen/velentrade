from __future__ import annotations

from dataclasses import dataclass, field, replace

from velentrade.domain.common import new_id, utc_now


NODE_STATUSES = {"not_started", "running", "waiting", "blocked", "completed", "skipped", "failed"}
INVESTMENT_STAGES = tuple(f"S{i}" for i in range(8))
RESPONSIBLE_ROLES = {
    "S0": "workflow_scheduling_center",
    "S1": "data_collection_quality_service",
    "S2": "analyst_team",
    "S3": "cio_debate_manager",
    "S4": "decision_service_and_cio",
    "S5": "risk_officer",
    "S6": "owner_and_paper_execution",
    "S7": "attribution_and_reflection",
}


@dataclass(frozen=True)
class RequestBrief:
    brief_id: str
    raw_input_ref: str
    route_type: str
    route_confidence: float
    asset_scope: str
    authorization_boundary: str
    owner_confirmation_status: str
    route_reason: str
    created_at: str
    suggested_semantic_lead: str = "owner_confirmation_required"
    process_authority: str = "request_distribution_center"
    predicted_outputs: list[str] = field(default_factory=list)
    creates_agent_run: bool = False
    forbidden_action_reason_code: str | None = None

    @classmethod
    def create(
        cls,
        brief_id: str,
        raw_input_ref: str,
        route_type: str,
        route_confidence: float,
        asset_scope: str,
        authorization_boundary: str,
    ) -> "RequestBrief":
        status = "draft"
        reason = "ready_for_owner_confirmation"
        if route_confidence >= 0.8 and asset_scope == "a_share_common_stock":
            status = "draft"
        return cls(
            brief_id=brief_id,
            raw_input_ref=raw_input_ref,
            route_type=route_type,
            route_confidence=route_confidence,
            asset_scope=asset_scope,
            authorization_boundary=authorization_boundary,
            owner_confirmation_status=status,
            route_reason=reason,
            created_at=utc_now(),
        )

    @classmethod
    def route_owner_request(
        cls,
        brief_id: str,
        raw_input_ref: str,
        intent: str,
        asset_scope: str,
        target_action: str,
        route_confidence: float,
        authorization_boundary: str,
    ) -> "RequestBrief":
        route_type = "research_task"
        route_reason = "route_research_default"
        semantic_lead = "investment_researcher"
        process_authority = "workflow_scheduling_center"
        predicted_outputs = ["ResearchPackage", "MemoryCapture", "TopicProposalCandidate"]
        creates_agent_run = True
        forbidden_action_reason_code = None

        if intent in {"formal_investment_decision", "position_disposal", "paper_trade"} and asset_scope == "a_share_common_stock":
            route_type = "investment_workflow"
            route_reason = "route_a_share_formal_workflow"
            semantic_lead = "cio"
            predicted_outputs = ["ICChairBrief", "AnalystMemo", "DecisionPacket", "RiskReviewReport"]
        elif intent in {"learn_hot_event", "research_material", "supporting_evidence_only"}:
            route_type = "research_task"
            route_reason = "route_research_task"
            semantic_lead = "investment_researcher"
            predicted_outputs = ["ResearchPackage", "MemoryCapture", "TopicProposalCandidate"]
        elif intent in {"finance_planning", "family_budget", "tax_review"}:
            route_type = "finance_task"
            route_reason = "route_finance_task"
            semantic_lead = "cfo"
            predicted_outputs = ["FinancePlanningSummary", "ManualTodo"]
        elif intent in {"prompt_change", "skill_change", "config_change"}:
            route_type = "governance_task"
            route_reason = "route_governance_task"
            semantic_lead = "responsible_agent"
            process_authority = "governance_runtime"
            predicted_outputs = ["GovernanceChangeDraft", "ValidationPlan"]
        elif intent in {"change_agent_capability", "agent_capability_change"}:
            route_type = "agent_capability_change"
            route_reason = "route_agent_capability_change"
            semantic_lead = "responsible_agent"
            process_authority = "governance_runtime"
            predicted_outputs = ["AgentCapabilityChangeDraft", "GovernanceChangeDraft"]
        elif intent in {"system_incident", "data_source_issue", "security_issue"}:
            route_type = "system_task"
            route_reason = "route_system_task"
            semantic_lead = "devops_engineer"
            predicted_outputs = ["IncidentReport", "RecoveryValidation"]
        elif asset_scope != "a_share_common_stock" and target_action in {"trade", "execute", "approve_trade"}:
            route_type = "manual_todo"
            route_reason = "route_non_a_manual_todo"
            semantic_lead = "owner_manual_follow_up"
            process_authority = "task_center"
            predicted_outputs = ["ManualTodo", "RiskReminder"]
            creates_agent_run = False
            forbidden_action_reason_code = "non_a_asset_no_trade"
        elif intent == "ambiguous_request":
            route_reason = "route_low_confidence_draft"
            semantic_lead = "owner_confirmation_required"
            predicted_outputs = ["RequestBriefDraft"]
            creates_agent_run = False

        brief = cls.create(
            brief_id=brief_id,
            raw_input_ref=raw_input_ref,
            route_type=route_type,
            route_confidence=route_confidence,
            asset_scope=asset_scope,
            authorization_boundary=authorization_boundary,
        )
        return replace(
            brief,
            route_reason=route_reason,
            suggested_semantic_lead=semantic_lead,
            process_authority=process_authority,
            predicted_outputs=predicted_outputs,
            creates_agent_run=creates_agent_run,
            forbidden_action_reason_code=forbidden_action_reason_code,
        )


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    task_type: str
    priority: str
    owner_role: str
    current_state: str
    reason_code: str
    artifact_refs: list[str]
    created_at: str
    updated_at: str
    blocked_reason: str | None = None
    closed_at: str | None = None


@dataclass(frozen=True)
class WorkflowStage:
    workflow_id: str
    attempt_no: int
    stage: str
    node_status: str
    responsible_role: str
    input_artifact_refs: list[str] = field(default_factory=list)
    output_artifact_refs: list[str] = field(default_factory=list)
    reason_code: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    stage_version: int = 1

    def with_status(self, node_status: str, reason_code: str | None = None, outputs: list[str] | None = None) -> "WorkflowStage":
        if node_status not in NODE_STATUSES:
            raise ValueError(f"Invalid workflow node_status: {node_status}")
        now = utc_now()
        return replace(
            self,
            node_status=node_status,
            reason_code=reason_code,
            output_artifact_refs=outputs if outputs is not None else self.output_artifact_refs,
            started_at=now if node_status == "running" and not self.started_at else self.started_at,
            completed_at=now if node_status == "completed" else self.completed_at,
            stage_version=self.stage_version + 1,
        )


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    task_id: str
    workflow_type: str
    current_stage: str
    current_attempt_no: int
    status: str
    context_snapshot_id: str
    stages: list[WorkflowStage]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ReopenEvent:
    reopen_event_id: str
    workflow_id: str
    from_stage: str
    target_stage: str
    reason_code: str
    requested_by: str
    approved_by_or_guard: str
    invalidated_artifacts: list[str]
    preserved_artifacts: list[str]
    attempt_no: int
    created_at: str


@dataclass
class WorkflowRuntime:
    tasks: dict[str, TaskEnvelope] = field(default_factory=dict)
    workflows: dict[str, Workflow] = field(default_factory=dict)
    reopen_events: list[ReopenEvent] = field(default_factory=list)
    artifact_status: dict[str, str] = field(default_factory=dict)

    def expire_request_brief(self, brief: RequestBrief) -> TaskEnvelope:
        now = utc_now()
        task = TaskEnvelope(
            task_id=new_id("task"),
            task_type=brief.route_type,
            priority="P1",
            owner_role="owner",
            current_state="expired",
            reason_code="owner_timeout_request_brief_expired",
            artifact_refs=[],
            created_at=now,
            updated_at=now,
            closed_at=now,
        )
        self.tasks[task.task_id] = task
        return task

    def confirm_request_brief(self, brief: RequestBrief, owner_decision: str) -> TaskEnvelope:
        if owner_decision != "confirmed":
            state = "canceled" if owner_decision == "canceled" else "draft"
            reason = "request_brief_not_confirmed"
        elif brief.route_confidence < 0.8:
            state = "draft"
            reason = "request_brief_not_confirmed"
        elif brief.route_type == "investment_workflow" and brief.asset_scope != "a_share_common_stock":
            state = "draft"
            reason = "request_brief_not_confirmed"
        else:
            state = "ready"
            reason = "request_brief_confirmed"
        now = utc_now()
        task = TaskEnvelope(
            task_id=new_id("task"),
            task_type=brief.route_type,
            priority="P1",
            owner_role="owner",
            current_state=state,
            reason_code=reason,
            artifact_refs=[],
            created_at=now,
            updated_at=now,
        )
        self.tasks[task.task_id] = task
        return task

    def create_investment_workflow(self, task: TaskEnvelope, context_snapshot_id: str) -> Workflow:
        if task.current_state != "ready" or task.task_type != "investment_workflow":
            raise ValueError("RequestBrief must be confirmed before workflow creation.")
        workflow_id = new_id("workflow")
        stages = [
            WorkflowStage(
                workflow_id=workflow_id,
                attempt_no=1,
                stage=stage,
                node_status="not_started",
                responsible_role=RESPONSIBLE_ROLES[stage],
            )
            for stage in INVESTMENT_STAGES
        ]
        now = utc_now()
        workflow = Workflow(
            workflow_id=workflow_id,
            task_id=task.task_id,
            workflow_type="investment_workflow",
            current_stage="S0",
            current_attempt_no=1,
            status="running",
            context_snapshot_id=context_snapshot_id,
            stages=stages,
            created_at=now,
            updated_at=now,
        )
        self.workflows[workflow_id] = workflow
        return workflow

    def _stage_index(self, workflow: Workflow, stage: str) -> int:
        for index, candidate in enumerate(workflow.stages):
            if candidate.stage == stage:
                return index
        raise ValueError(f"Unknown stage: {stage}")

    def start_stage(self, workflow_id: str, stage: str) -> WorkflowStage:
        workflow = self.workflows[workflow_id]
        index = self._stage_index(workflow, stage)
        if index > 0 and workflow.stages[index - 1].node_status not in {"completed", "skipped"}:
            blocked = workflow.stages[index].with_status("blocked", "upstream_stage_not_completed")
            workflow.stages[index] = blocked
            return blocked
        started = workflow.stages[index].with_status("running")
        workflow.stages[index] = started
        self.workflows[workflow_id] = replace(workflow, current_stage=stage, updated_at=utc_now())
        return started

    def complete_stage(self, workflow_id: str, stage: str, artifact_refs: list[str]) -> WorkflowStage:
        workflow = self.workflows[workflow_id]
        index = self._stage_index(workflow, stage)
        if not artifact_refs:
            blocked = workflow.stages[index].with_status("blocked", "missing_required_artifact")
            workflow.stages[index] = blocked
            return blocked
        if any(_is_memory_ref(ref) for ref in artifact_refs):
            blocked = workflow.stages[index].with_status("blocked", "memory_not_fact_source")
            workflow.stages[index] = blocked
            return blocked
        completed = workflow.stages[index].with_status("completed", outputs=artifact_refs)
        for ref in artifact_refs:
            self.artifact_status.setdefault(ref, "accepted")
        workflow.stages[index] = completed
        self.workflows[workflow_id] = replace(workflow, updated_at=utc_now())
        return completed

    def request_reopen(
        self,
        workflow_id: str,
        from_stage: str,
        target_stage: str,
        reason_code: str,
        requested_by: str,
        invalidated_artifacts: list[str],
        preserved_artifacts: list[str],
    ) -> ReopenEvent:
        workflow = self.workflows[workflow_id]
        if target_stage not in INVESTMENT_STAGES or from_stage not in INVESTMENT_STAGES:
            raise ValueError("Reopen stages must be valid S0-S7 stages.")
        for ref in invalidated_artifacts:
            self.artifact_status[ref] = "superseded"
        event = ReopenEvent(
            reopen_event_id=new_id("reopen"),
            workflow_id=workflow_id,
            from_stage=from_stage,
            target_stage=target_stage,
            reason_code=reason_code,
            requested_by=requested_by,
            approved_by_or_guard="workflow_guard",
            invalidated_artifacts=invalidated_artifacts,
            preserved_artifacts=preserved_artifacts,
            attempt_no=workflow.current_attempt_no + 1,
            created_at=utc_now(),
        )
        self.reopen_events.append(event)
        return event


def _is_memory_ref(ref: str) -> bool:
    return ref.startswith("memory-") or ref.startswith("memory:")
