from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import utc_now


COMMAND_TYPES = {
    "ask_question",
    "request_view_update",
    "request_peer_review",
    "request_agent_run",
    "request_data",
    "request_evidence",
    "request_service_recompute",
    "request_source_health_check",
    "request_reopen",
    "request_pause_or_hold",
    "request_resume",
    "request_owner_input",
    "request_manual_todo",
    "request_reflection",
    "propose_knowledge_promotion",
    "propose_prompt_update",
    "propose_skill_update",
    "propose_config_change",
    "report_incident",
    "request_degradation",
    "request_recovery_validation",
    "request_risk_impact_review",
}


@dataclass(frozen=True)
class CollaborationSession:
    session_id: str
    workflow_id: str
    attempt_no: int
    stage: str
    mode: str
    semantic_lead_agent_id: str
    process_authority: str
    status: str
    context_snapshot_id: str
    participant_agent_ids: list[str]
    opened_by: str
    opened_at: str
    closed_at: str | None = None
    close_reason: str | None = None

    @classmethod
    def open_session(
        cls,
        session_id: str,
        workflow_id: str,
        stage: str,
        semantic_lead_agent_id: str,
        participant_agent_ids: list[str],
        attempt_no: int = 1,
        mode: str = "ad_hoc_support",
    ) -> "CollaborationSession":
        return cls(
            session_id=session_id,
            workflow_id=workflow_id,
            attempt_no=attempt_no,
            stage=stage,
            mode=mode,
            semantic_lead_agent_id=semantic_lead_agent_id,
            process_authority="workflow",
            status="open",
            context_snapshot_id="ctx-v1",
            participant_agent_ids=participant_agent_ids,
            opened_by=semantic_lead_agent_id,
            opened_at=utc_now(),
        )


@dataclass(frozen=True)
class AgentRun:
    agent_run_id: str
    workflow_id: str
    attempt_no: int
    stage: str
    agent_id: str
    profile_version: str
    run_goal: str
    admission_type: str
    context_snapshot_id: str
    context_slice_id: str
    tool_profile_id: str
    status: str
    output_artifact_schema: str
    allowed_command_types: list[str]
    session_id: str | None = None
    parent_run_id: str | None = None

    @classmethod
    def fake(
        cls,
        agent_run_id: str,
        agent_id: str,
        workflow_id: str,
        allowed_command_types: list[str] | None = None,
    ) -> "AgentRun":
        return cls(
            agent_run_id=agent_run_id,
            workflow_id=workflow_id,
            attempt_no=1,
            stage="S1",
            agent_id=agent_id,
            profile_version="1.0.0",
            run_goal="fixture run",
            admission_type="auto_accept",
            context_snapshot_id="ctx-v1",
            context_slice_id=f"slice-{agent_run_id}",
            tool_profile_id="readonly-basic",
            status="running",
            output_artifact_schema="ResearchPackage",
            allowed_command_types=allowed_command_types or ["ask_question"],
        )


@dataclass(frozen=True)
class CollaborationEvent:
    event_id: str
    event_type: str
    workflow_id: str
    attempt_no: int
    trace_id: str
    payload: dict[str, Any]
    created_at: str
    session_id: str | None = None
    agent_run_id: str | None = None
    command_id: str | None = None
    artifact_id: str | None = None


@dataclass(frozen=True)
class CollaborationCommand:
    command_id: str
    command_type: str
    workflow_id: str
    attempt_no: int
    stage: str
    source_agent_run_id: str
    source_agent_id: str
    target_agent_id_or_service: str
    payload: dict[str, Any]
    requested_admission_type: str
    admission_status: str
    created_at: str
    session_id: str | None = None
    admission_reason: str | None = None
    result_ref: str | None = None
    resolved_at: str | None = None

    @classmethod
    def request(
        cls,
        command_id: str,
        command_type: str,
        workflow_id: str,
        attempt_no: int,
        stage: str,
        source_agent_run_id: str,
        source_agent_id: str,
        target_agent_id_or_service: str,
        payload: dict[str, Any],
        requested_admission_type: str = "auto_accept",
    ) -> "CollaborationCommand":
        if command_type not in COMMAND_TYPES:
            raise ValueError(f"Unknown collaboration command_type: {command_type}")
        return cls(
            command_id=command_id,
            command_type=command_type,
            workflow_id=workflow_id,
            attempt_no=attempt_no,
            stage=stage,
            source_agent_run_id=source_agent_run_id,
            source_agent_id=source_agent_id,
            target_agent_id_or_service=target_agent_id_or_service,
            payload=payload,
            requested_admission_type=requested_admission_type,
            admission_status="pending",
            created_at=utc_now(),
        )

    def to_event(self, event_id: str, trace_id: str) -> CollaborationEvent:
        return CollaborationEvent(
            event_id=event_id,
            event_type="command_requested",
            workflow_id=self.workflow_id,
            attempt_no=self.attempt_no,
            trace_id=trace_id,
            payload={"command_type": self.command_type, "target": self.target_agent_id_or_service},
            created_at=utc_now(),
            session_id=self.session_id,
            agent_run_id=self.source_agent_run_id,
            command_id=self.command_id,
        )


@dataclass(frozen=True)
class HandoffPacket:
    handoff_id: str
    workflow_id: str
    attempt_no: int
    from_stage: str
    to_stage_or_agent: str
    producer_agent_id_or_service: str
    source_artifact_refs: list[str]
    summary: str
    created_at: str
    open_questions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    invalidated_artifacts: list[str] = field(default_factory=list)
    preserved_artifacts: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        handoff_id: str,
        workflow_id: str,
        from_stage: str,
        to_stage_or_agent: str,
        producer_agent_id_or_service: str,
        source_artifact_refs: list[str],
        summary: str,
        attempt_no: int = 1,
    ) -> "HandoffPacket":
        return cls(
            handoff_id=handoff_id,
            workflow_id=workflow_id,
            attempt_no=attempt_no,
            from_stage=from_stage,
            to_stage_or_agent=to_stage_or_agent,
            producer_agent_id_or_service=producer_agent_id_or_service,
            source_artifact_refs=source_artifact_refs,
            summary=summary,
            created_at=utc_now(),
        )
