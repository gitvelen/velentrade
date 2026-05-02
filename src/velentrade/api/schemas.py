from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateRequestBriefRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=12000)
    source: str
    requested_scope: dict[str, Any] | None = None
    priority_hint: str | None = None
    authorization_boundary: str | None = None
    time_budget: str | None = None


class RequestBriefConfirmationRequest(BaseModel):
    decision: str
    edited_brief: dict[str, Any] | None = None
    client_seen_version: int = Field(ge=1)


class ApprovalDecisionRequest(BaseModel):
    decision: str
    comment: str | None = None
    accepted_risks: list[str] = Field(default_factory=list)
    requested_changes: list[str] = Field(default_factory=list)
    client_seen_version: int = Field(ge=1)


class AgentCapabilityDraftRequest(BaseModel):
    agent_id: str
    draft_title: str = Field(min_length=1, max_length=200)
    change_set: dict[str, Any]
    impact_level_hint: str | None = None
    validation_plan_refs: list[str] = Field(default_factory=list)
    rollback_plan_ref: str | None = None
    effective_scope: str
    client_seen_profile_version: str
    client_seen_context_snapshot_id: str


class FinanceAssetUpdateRequest(BaseModel):
    asset_id: str | None = None
    asset_type: str
    valuation: dict[str, Any]
    valuation_date: str
    source: str
    client_seen_version: int = Field(ge=1)


class CollaborationCommandRequest(BaseModel):
    command_type: str
    workflow_id: str
    attempt_no: int = Field(ge=1)
    stage: str
    source_agent_run_id: str
    target_agent_id_or_service: str
    payload: dict[str, Any]
    requested_admission_type: str


class GatewayArtifactWriteRequest(BaseModel):
    workflow_id: str
    attempt_no: int = Field(ge=1)
    stage: str
    source_agent_run_id: str
    context_snapshot_id: str
    artifact_type: str
    schema_version: str
    payload: dict[str, Any]
    source_refs: list[str] = Field(default_factory=list)
    idempotency_key: str


class GatewayEventWriteRequest(BaseModel):
    workflow_id: str
    attempt_no: int = Field(ge=1)
    stage: str
    source_agent_run_id: str
    event_type: str
    payload: dict[str, Any]
    idempotency_key: str


class GatewayHandoffWriteRequest(BaseModel):
    workflow_id: str
    attempt_no: int = Field(ge=1)
    from_stage: str
    to_stage_or_agent: str
    producer_agent_id_or_service: str
    source_artifact_refs: list[str]
    summary: str
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    decisions_made: list[str] = Field(default_factory=list)
    invalidated_artifacts: list[str] = Field(default_factory=list)
    preserved_artifacts: list[str] = Field(default_factory=list)
    idempotency_key: str


class GatewayMemoryWriteRequest(BaseModel):
    source_agent_run_id: str
    context_snapshot_id: str
    operation: str
    memory_id: str | None = None
    content_markdown: str
    payload: dict[str, Any] | None = None
    source_refs: list[str]
    relation_updates: list[dict[str, Any]] = Field(default_factory=list)
    collection_updates: list[dict[str, Any]] = Field(default_factory=list)
    sensitivity: str
    idempotency_key: str


class MemoryRelationWriteRequest(BaseModel):
    target_ref: str
    relation_type: str
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    client_seen_version_id: str


class CreateMemoryItemRequest(BaseModel):
    source_type: str
    source_refs: list[str]
    content_markdown: str
    suggested_memory_type: str
    tags: list[str] = Field(default_factory=list)
    sensitivity: str
    client_seen_context_snapshot_id: str
