from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from velentrade.db.base import Base


Table(
    "artifact",
    Base.metadata,
    Column("artifact_id", String, primary_key=True),
    Column("artifact_type", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("trace_id", String, nullable=False),
    Column("producer", String, nullable=False),
    Column("producer_type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("schema_version", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("source_refs", JSONB, nullable=True),
    Column("summary", Text, nullable=True),
    Column("evidence_refs", JSONB, nullable=True),
    Column("decision_refs", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "collaboration_session",
    Base.metadata,
    Column("session_id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("stage", String, nullable=False),
    Column("mode", String, nullable=False),
    Column("semantic_lead_agent_id", String, nullable=False),
    Column("process_authority", String, nullable=False),
    Column("status", String, nullable=False),
    Column("context_snapshot_id", String, nullable=False),
    Column("participant_agent_ids", JSONB, nullable=False),
    Column("opened_by", String, nullable=False),
    Column("opened_at", DateTime(timezone=True), nullable=False),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("close_reason", Text, nullable=True),
)

Table(
    "agent_run",
    Base.metadata,
    Column("agent_run_id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("stage", String, nullable=False),
    Column("session_id", String, nullable=True),
    Column("parent_run_id", String, nullable=True),
    Column("agent_id", String, nullable=False),
    Column("profile_version", String, nullable=False),
    Column("run_goal", Text, nullable=False),
    Column("admission_type", String, nullable=False),
    Column("admission_decision_ref", String, nullable=True),
    Column("context_snapshot_id", String, nullable=False),
    Column("context_slice_id", String, nullable=False),
    Column("tool_profile_id", String, nullable=False),
    Column("skill_package_versions", JSONB, nullable=True),
    Column("model_profile_id", String, nullable=True),
    Column("budget_tokens", Integer, nullable=True),
    Column("timeout_seconds", Integer, nullable=True),
    Column("status", String, nullable=False),
    Column("output_artifact_schema", String, nullable=False),
    Column("allowed_command_types", JSONB, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("ended_at", DateTime(timezone=True), nullable=True),
    Column("cost_tokens", Integer, nullable=True),
    Column("cost_estimate", Float, nullable=True),
)

Table(
    "collaboration_command",
    Base.metadata,
    Column("command_id", String, primary_key=True),
    Column("command_type", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("stage", String, nullable=False),
    Column("session_id", String, nullable=True),
    Column("source_agent_run_id", String, nullable=False),
    Column("source_agent_id", String, nullable=False),
    Column("target_agent_id_or_service", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("requested_admission_type", String, nullable=False),
    Column("admission_status", String, nullable=False),
    Column("admission_reason", Text, nullable=True),
    Column("result_ref", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
)

Table(
    "collaboration_event",
    Base.metadata,
    Column("event_id", String, primary_key=True),
    Column("event_type", String, nullable=False),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("session_id", String, nullable=True),
    Column("agent_run_id", String, nullable=True),
    Column("command_id", String, nullable=True),
    Column("artifact_id", String, nullable=True),
    Column("trace_id", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "handoff_packet",
    Base.metadata,
    Column("handoff_id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("from_stage", String, nullable=False),
    Column("to_stage_or_agent", String, nullable=False),
    Column("producer_agent_id_or_service", String, nullable=False),
    Column("source_artifact_refs", JSONB, nullable=False),
    Column("summary", Text, nullable=False),
    Column("open_questions", JSONB, nullable=True),
    Column("blockers", JSONB, nullable=True),
    Column("decisions_made", JSONB, nullable=True),
    Column("invalidated_artifacts", JSONB, nullable=True),
    Column("preserved_artifacts", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "context_snapshot",
    Base.metadata,
    Column("context_snapshot_id", String, primary_key=True),
    Column("snapshot_version", String, nullable=False),
    Column("effective_scope", String, nullable=False),
    Column("content_hash", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("frozen", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("effective_from", DateTime(timezone=True), nullable=False),
)

Table(
    "memory_item",
    Base.metadata,
    Column("memory_id", String, primary_key=True),
    Column("memory_type", String, nullable=False),
    Column("owner_role", String, nullable=False),
    Column("producer_agent_id", String, nullable=True),
    Column("status", String, nullable=False),
    Column("current_version_id", String, nullable=False),
    Column("source_refs", JSONB, nullable=False),
    Column("sensitivity", String, nullable=False),
    Column("pinned", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

Table(
    "memory_version",
    Base.metadata,
    Column("version_id", String, primary_key=True),
    Column("memory_id", String, nullable=False),
    Column("version_no", Integer, nullable=False),
    Column("content_markdown", Text, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_by", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("content_hash", String, nullable=False),
    Column("superseded_by_version_id", String, nullable=True),
    UniqueConstraint("memory_id", "version_no", name="uq_memory_version"),
)

Table(
    "memory_extraction_result",
    Base.metadata,
    Column("extraction_id", String, primary_key=True),
    Column("memory_version_id", String, nullable=False),
    Column("extractor_version", String, nullable=False),
    Column("title", String, nullable=False),
    Column("tags", JSONB, nullable=False),
    Column("mentions", JSONB, nullable=False),
    Column("has_link", Boolean, nullable=True),
    Column("has_task_list", Boolean, nullable=True),
    Column("has_code", Boolean, nullable=True),
    Column("has_incomplete_tasks", Boolean, nullable=True),
    Column("symbol_refs", JSONB, nullable=True),
    Column("artifact_refs", JSONB, nullable=True),
    Column("agent_refs", JSONB, nullable=True),
    Column("stage_refs", JSONB, nullable=True),
    Column("source_refs", JSONB, nullable=True),
    Column("sensitivity", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "memory_relation",
    Base.metadata,
    Column("relation_id", String, primary_key=True),
    Column("source_memory_id", String, nullable=False),
    Column("target_ref", String, nullable=False),
    Column("relation_type", String, nullable=False),
    Column("reason", Text, nullable=False),
    Column("evidence_refs", JSONB, nullable=True),
    Column("created_by", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "memory_collection",
    Base.metadata,
    Column("collection_id", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("filter_expression", Text, nullable=False),
    Column("scope", String, nullable=False),
    Column("owner_agent_id", String, nullable=True),
    Column("purpose", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

Table(
    "knowledge_item",
    Base.metadata,
    Column("knowledge_id", String, primary_key=True),
    Column("knowledge_type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("source_memory_refs", JSONB, nullable=False),
    Column("source_artifact_refs", JSONB, nullable=False),
    Column("validation_result_refs", JSONB, nullable=False),
    Column("effective_scope", String, nullable=False),
    Column("governance_change_ref", String, nullable=True),
    Column("current_version_id", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

Table(
    "model_profile",
    Base.metadata,
    Column("model_profile_id", String, primary_key=True),
    Column("provider_profile_id", String, nullable=False),
    Column("purpose", String, nullable=False),
    Column("model_name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "tool_profile",
    Base.metadata,
    Column("tool_profile_id", String, primary_key=True),
    Column("description", Text, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "skill_package",
    Base.metadata,
    Column("package_id", String, primary_key=True),
    Column("display_name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "skill_package_version",
    Base.metadata,
    Column("package_version_id", String, primary_key=True),
    Column("package_id", String, nullable=False),
    Column("version", String, nullable=False),
    Column("manifest_hash", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("package_id", "version", name="uq_skill_package_version"),
)

Table(
    "default_context_binding",
    Base.metadata,
    Column("binding_id", String, primary_key=True),
    Column("context_snapshot_id", String, nullable=False),
    Column("source_ref", String, nullable=False),
    Column("binding_type", String, nullable=False),
    Column("effective_scope", String, nullable=False),
    Column("impact_level", String, nullable=False),
    Column("governance_change_ref", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "process_archive",
    Base.metadata,
    Column("archive_id", String, primary_key=True),
    Column("source_object_type", String, nullable=False),
    Column("source_object_id", String, nullable=False),
    Column("workflow_id", String, nullable=True),
    Column("attempt_no", Integer, nullable=True),
    Column("stage", String, nullable=True),
    Column("summary", Text, nullable=False),
    Column("source_refs", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("retention_policy", String, nullable=True),
)

Table(
    "audit_event",
    Base.metadata,
    Column("audit_event_id", String, primary_key=True),
    Column("event_type", String, nullable=False),
    Column("object_type", String, nullable=False),
    Column("object_id", String, nullable=False),
    Column("actor", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "outbox_event",
    Base.metadata,
    Column("outbox_event_id", String, primary_key=True),
    Column("topic", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("idempotency_key", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("idempotency_key", name="uq_outbox_event_idempotency_key"),
)

Table(
    "runner_write_denial",
    Base.metadata,
    Column("denial_id", String, primary_key=True),
    Column("actor", String, nullable=False),
    Column("table_name", String, nullable=False),
    Column("reason_code", String, nullable=False),
    Column("details", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
