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
        "task_envelope",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("owner_role", sa.String(), nullable=False),
        sa.Column("current_state", sa.String(), nullable=False),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_table(
        "workflow",
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("workflow_type", sa.String(), nullable=False),
        sa.Column("current_stage", sa.String(), nullable=False),
        sa.Column("current_attempt_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("workflow_id"),
    )
    op.create_table(
        "workflow_attempt",
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("context_snapshot_id", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("superseded_by_attempt_no", sa.Integer(), nullable=True),
        sa.UniqueConstraint("workflow_id", "attempt_no", name="uq_workflow_attempt"),
    )
    op.create_table(
        "workflow_stage",
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("node_status", sa.String(), nullable=False),
        sa.Column("responsible_role", sa.String(), nullable=False),
        sa.Column("input_artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stage_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("workflow_id", "attempt_no", "stage", name="uq_workflow_stage"),
    )
    op.create_table(
        "reopen_event",
        sa.Column("reopen_event_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("from_stage", sa.String(), nullable=False),
        sa.Column("target_stage", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=False),
        sa.Column("approved_by_or_guard", sa.String(), nullable=False),
        sa.Column("invalidated_artifacts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preserved_artifacts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("reopen_event_id"),
    )
    op.create_table(
        "approval_record",
        sa.Column("approval_id", sa.String(), nullable=False),
        sa.Column("approval_type", sa.String(), nullable=False),
        sa.Column("approval_object_ref", sa.String(), nullable=False),
        sa.Column("trigger_reason", sa.String(), nullable=False),
        sa.Column("recommended_decision", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("effective_scope", sa.String(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("approval_id"),
    )
    op.create_table(
        "manual_todo",
        sa.Column("manual_todo_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("risk_hint", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("manual_todo_id"),
    )
    op.create_table(
        "governance_change",
        sa.Column("change_id", sa.String(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("impact_level", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("proposal_ref", sa.String(), nullable=False),
        sa.Column("context_snapshot_id", sa.String(), nullable=True),
        sa.Column("effective_scope", sa.String(), nullable=False),
        sa.Column("state_reason", sa.Text(), nullable=True),
        sa.Column("target_version_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rollback_plan_ref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("change_id"),
    )
    op.create_table(
        "data_domain_registry",
        sa.Column("domain_id", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("domain_id"),
    )
    op.create_table(
        "data_source_registry",
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("data_domain", sa.String(), nullable=False),
        sa.Column("usage_scope", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("license_summary", sa.Text(), nullable=False),
        sa.Column("rate_limit", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("adapter_kind", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.create_table(
        "data_request",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("data_domain", sa.String(), nullable=False),
        sa.Column("symbol_or_scope", sa.String(), nullable=False),
        sa.Column("time_range", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required_usage", sa.String(), nullable=False),
        sa.Column("freshness_requirement", sa.String(), nullable=False),
        sa.Column("required_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requesting_stage", sa.String(), nullable=False),
        sa.Column("requesting_agent_or_service", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_table(
        "data_lineage",
        sa.Column("lineage_id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("lineage_id"),
    )
    op.create_table(
        "data_quality_report",
        sa.Column("report_id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("quality_band", sa.String(), nullable=False),
        sa.Column("critical_field_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("decision_core_status", sa.String(), nullable=False),
        sa.Column("execution_core_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("report_id"),
    )
    op.create_table(
        "data_conflict_report",
        sa.Column("conflict_id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("field_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("conflict_id"),
    )
    op.create_table(
        "market_state",
        sa.Column("market_state_id", sa.String(), nullable=False),
        sa.Column("effective_date", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("market_state_id"),
    )
    for result_table_name in ("factor_result", "valuation_result", "portfolio_optimization_result", "risk_engine_result"):
        op.create_table(
            result_table_name,
            sa.Column("result_id", sa.String(), nullable=False),
            sa.Column("workflow_id", sa.String(), nullable=True),
            sa.Column("input_artifact_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("result_id"),
        )
    op.create_table(
        "paper_account",
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("base_currency", sa.String(), nullable=False),
        sa.Column("cash", sa.Float(), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "paper_order",
        sa.Column("paper_order_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("decision_memo_ref", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("target_quantity_or_weight", sa.Float(), nullable=False),
        sa.Column("price_range", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("urgency", sa.String(), nullable=False),
        sa.Column("execution_core_snapshot_ref", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("paper_order_id"),
    )
    op.create_table(
        "paper_execution_receipt",
        sa.Column("receipt_id", sa.String(), nullable=False),
        sa.Column("paper_order_id", sa.String(), nullable=False),
        sa.Column("pricing_method", sa.String(), nullable=False),
        sa.Column("execution_window", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("fill_status", sa.String(), nullable=False),
        sa.Column("fill_price", sa.Float(), nullable=True),
        sa.Column("fill_quantity", sa.Float(), nullable=True),
        sa.Column("fees", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("taxes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("slippage", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("t_plus_one_state", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("receipt_id"),
    )
    op.create_table(
        "session",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("owner_role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_table(
        "user_auth",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("owner_role", sa.String(), nullable=False),
        sa.Column("auth_provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "sensitive_field_access_event",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("field_ref", sa.String(), nullable=False),
        sa.Column("access_decision", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_table(
        "security_finding",
        sa.Column("finding_id", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("finding_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("finding_id"),
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
    op.drop_table("security_finding")
    op.drop_table("sensitive_field_access_event")
    op.drop_table("user_auth")
    op.drop_table("session")
    op.drop_table("paper_execution_receipt")
    op.drop_table("paper_order")
    op.drop_table("paper_account")
    op.drop_table("risk_engine_result")
    op.drop_table("portfolio_optimization_result")
    op.drop_table("valuation_result")
    op.drop_table("factor_result")
    op.drop_table("market_state")
    op.drop_table("data_conflict_report")
    op.drop_table("data_quality_report")
    op.drop_table("data_lineage")
    op.drop_table("data_request")
    op.drop_table("data_source_registry")
    op.drop_table("data_domain_registry")
    op.drop_table("governance_change")
    op.drop_table("manual_todo")
    op.drop_table("approval_record")
    op.drop_table("reopen_event")
    op.drop_table("workflow_stage")
    op.drop_table("workflow_attempt")
    op.drop_table("workflow")
    op.drop_table("task_envelope")
    op.drop_table("artifact")
