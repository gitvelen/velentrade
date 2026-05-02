"""wi001 foundation schema

Revision ID: 20260502_0001
Revises: None
Create Date: 2026-05-02 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260502_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifact",
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("producer", sa.String(), nullable=False),
        sa.Column("producer_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decision_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("artifact_id"),
    )
    op.create_table(
        "collaboration_session",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("semantic_lead_agent_id", sa.String(), nullable=False),
        sa.Column("process_authority", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("participant_agent_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("opened_by", sa.String(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_table(
        "agent_run",
        sa.Column("agent_run_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("parent_run_id", sa.String(), nullable=True),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("profile_version", sa.String(), nullable=False),
        sa.Column("run_goal", sa.Text(), nullable=False),
        sa.Column("admission_type", sa.String(), nullable=False),
        sa.Column("admission_decision_ref", sa.String(), nullable=True),
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("context_slice_id", sa.String(), nullable=False),
        sa.Column("tool_profile_id", sa.String(), nullable=False),
        sa.Column("skill_package_versions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_profile_id", sa.String(), nullable=True),
        sa.Column("budget_tokens", sa.Integer(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("output_artifact_schema", sa.String(), nullable=False),
        sa.Column("allowed_command_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cost_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("agent_run_id"),
    )
    op.create_table(
        "collaboration_command",
        sa.Column("command_id", sa.String(), nullable=False),
        sa.Column("command_type", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("source_agent_run_id", sa.String(), nullable=False),
        sa.Column("source_agent_id", sa.String(), nullable=False),
        sa.Column("target_agent_id_or_service", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_admission_type", sa.String(), nullable=False),
        sa.Column("admission_status", sa.String(), nullable=False),
        sa.Column("admission_reason", sa.Text(), nullable=True),
        sa.Column("result_ref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("command_id"),
    )
    op.create_table(
        "collaboration_event",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("agent_run_id", sa.String(), nullable=True),
        sa.Column("command_id", sa.String(), nullable=True),
        sa.Column("artifact_id", sa.String(), nullable=True),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_table(
        "handoff_packet",
        sa.Column("handoff_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("from_stage", sa.String(), nullable=False),
        sa.Column("to_stage_or_agent", sa.String(), nullable=False),
        sa.Column("producer_agent_id_or_service", sa.String(), nullable=False),
        sa.Column("source_artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("open_questions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decisions_made", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("invalidated_artifacts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preserved_artifacts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("handoff_id"),
    )
    op.create_table(
        "context_snapshot",
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("snapshot_version", sa.String(), nullable=False),
        sa.Column("effective_scope", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("frozen", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("context_snapshot_id"),
    )
    op.create_table(
        "memory_item",
        sa.Column("memory_id", sa.String(), nullable=False),
        sa.Column("memory_type", sa.String(), nullable=False),
        sa.Column("owner_role", sa.String(), nullable=False),
        sa.Column("producer_agent_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_version_id", sa.String(), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sensitivity", sa.String(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("memory_id"),
    )
    op.create_table(
        "memory_version",
        sa.Column("version_id", sa.String(), nullable=False),
        sa.Column("memory_id", sa.String(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("superseded_by_version_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("version_id"),
        sa.UniqueConstraint("memory_id", "version_no", name="uq_memory_version"),
    )
    op.create_table(
        "memory_extraction_result",
        sa.Column("extraction_id", sa.String(), nullable=False),
        sa.Column("memory_version_id", sa.String(), nullable=False),
        sa.Column("extractor_version", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mentions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("has_link", sa.Boolean(), nullable=True),
        sa.Column("has_task_list", sa.Boolean(), nullable=True),
        sa.Column("has_code", sa.Boolean(), nullable=True),
        sa.Column("has_incomplete_tasks", sa.Boolean(), nullable=True),
        sa.Column("symbol_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("agent_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("stage_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sensitivity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("extraction_id"),
    )
    op.create_table(
        "memory_relation",
        sa.Column("relation_id", sa.String(), nullable=False),
        sa.Column("source_memory_id", sa.String(), nullable=False),
        sa.Column("target_ref", sa.String(), nullable=False),
        sa.Column("relation_type", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("relation_id"),
    )
    op.create_table(
        "memory_collection",
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("filter_expression", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("owner_agent_id", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("collection_id"),
    )
    op.create_table(
        "knowledge_item",
        sa.Column("knowledge_id", sa.String(), nullable=False),
        sa.Column("knowledge_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_memory_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation_result_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("effective_scope", sa.String(), nullable=False),
        sa.Column("governance_change_ref", sa.String(), nullable=True),
        sa.Column("current_version_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("knowledge_id"),
    )
    op.create_table(
        "model_profile",
        sa.Column("model_profile_id", sa.String(), nullable=False),
        sa.Column("provider_profile_id", sa.String(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("model_profile_id"),
    )
    op.create_table(
        "tool_profile",
        sa.Column("tool_profile_id", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tool_profile_id"),
    )
    op.create_table(
        "skill_package",
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("package_id"),
    )
    op.create_table(
        "skill_package_version",
        sa.Column("package_version_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("manifest_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("package_version_id"),
        sa.UniqueConstraint("package_id", "version", name="uq_skill_package_version"),
    )
    op.create_table(
        "default_context_binding",
        sa.Column("binding_id", sa.String(), nullable=False),
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("binding_type", sa.String(), nullable=False),
        sa.Column("effective_scope", sa.String(), nullable=False),
        sa.Column("impact_level", sa.String(), nullable=False),
        sa.Column("governance_change_ref", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("binding_id"),
    )
    op.create_table(
        "process_archive",
        sa.Column("archive_id", sa.String(), nullable=False),
        sa.Column("source_object_type", sa.String(), nullable=False),
        sa.Column("source_object_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_policy", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("archive_id"),
    )
    op.create_table(
        "audit_event",
        sa.Column("audit_event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("object_id", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_event_id"),
    )
    op.create_table(
        "outbox_event",
        sa.Column("outbox_event_id", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("outbox_event_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_outbox_event_idempotency_key"),
    )
    op.create_table(
        "runner_write_denial",
        sa.Column("denial_id", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("denial_id"),
    )


def downgrade() -> None:
    op.drop_table("runner_write_denial")
    op.drop_table("outbox_event")
    op.drop_table("audit_event")
    op.drop_table("process_archive")
    op.drop_table("default_context_binding")
    op.drop_table("skill_package_version")
    op.drop_table("skill_package")
    op.drop_table("tool_profile")
    op.drop_table("model_profile")
    op.drop_table("knowledge_item")
    op.drop_table("memory_collection")
    op.drop_table("memory_relation")
    op.drop_table("memory_extraction_result")
    op.drop_table("memory_version")
    op.drop_table("memory_item")
    op.drop_table("context_snapshot")
    op.drop_table("handoff_packet")
    op.drop_table("collaboration_event")
    op.drop_table("collaboration_command")
    op.drop_table("agent_run")
    op.drop_table("collaboration_session")
    op.drop_table("artifact")
