from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
