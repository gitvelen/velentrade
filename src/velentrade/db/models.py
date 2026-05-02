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
    "task_envelope",
    Base.metadata,
    Column("task_id", String, primary_key=True),
    Column("task_type", String, nullable=False),
    Column("priority", String, nullable=False),
    Column("owner_role", String, nullable=False),
    Column("current_state", String, nullable=False),
    Column("blocked_reason", Text, nullable=True),
    Column("reason_code", String, nullable=False),
    Column("artifact_refs", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("closed_at", DateTime(timezone=True), nullable=True),
)

Table(
    "workflow",
    Base.metadata,
    Column("workflow_id", String, primary_key=True),
    Column("task_id", String, nullable=False),
    Column("workflow_type", String, nullable=False),
    Column("current_stage", String, nullable=False),
    Column("current_attempt_no", Integer, nullable=False),
    Column("status", String, nullable=False),
    Column("context_snapshot_id", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

Table(
    "workflow_attempt",
    Base.metadata,
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("context_snapshot_id", String, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("ended_at", DateTime(timezone=True), nullable=True),
    Column("status", String, nullable=False),
    Column("superseded_by_attempt_no", Integer, nullable=True),
    UniqueConstraint("workflow_id", "attempt_no", name="uq_workflow_attempt"),
)

Table(
    "workflow_stage",
    Base.metadata,
    Column("workflow_id", String, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("stage", String, nullable=False),
    Column("node_status", String, nullable=False),
    Column("responsible_role", String, nullable=False),
    Column("input_artifact_refs", JSONB, nullable=False),
    Column("output_artifact_refs", JSONB, nullable=False),
    Column("reason_code", String, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("stage_version", Integer, nullable=False),
    UniqueConstraint("workflow_id", "attempt_no", "stage", name="uq_workflow_stage"),
)

Table(
    "reopen_event",
    Base.metadata,
    Column("reopen_event_id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("from_stage", String, nullable=False),
    Column("target_stage", String, nullable=False),
    Column("reason_code", String, nullable=False),
    Column("requested_by", String, nullable=False),
    Column("approved_by_or_guard", String, nullable=False),
    Column("invalidated_artifacts", JSONB, nullable=False),
    Column("preserved_artifacts", JSONB, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "approval_record",
    Base.metadata,
    Column("approval_id", String, primary_key=True),
    Column("approval_type", String, nullable=False),
    Column("approval_object_ref", String, nullable=False),
    Column("trigger_reason", String, nullable=False),
    Column("recommended_decision", String, nullable=False),
    Column("decision", String, nullable=False),
    Column("effective_scope", String, nullable=False),
    Column("evidence_refs", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("decided_at", DateTime(timezone=True), nullable=True),
)

Table(
    "manual_todo",
    Base.metadata,
    Column("manual_todo_id", String, primary_key=True),
    Column("task_id", String, nullable=False),
    Column("reason_code", String, nullable=False),
    Column("risk_hint", Text, nullable=True),
    Column("due_at", DateTime(timezone=True), nullable=True),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("closed_at", DateTime(timezone=True), nullable=True),
)

Table(
    "governance_change",
    Base.metadata,
    Column("change_id", String, primary_key=True),
    Column("change_type", String, nullable=False),
    Column("impact_level", String, nullable=False),
    Column("state", String, nullable=False),
    Column("proposal_ref", String, nullable=False),
    Column("context_snapshot_id", String, nullable=True),
    Column("effective_scope", String, nullable=False),
    Column("state_reason", Text, nullable=True),
    Column("target_version_refs", JSONB, nullable=True),
    Column("rollback_plan_ref", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("decided_at", DateTime(timezone=True), nullable=True),
    Column("effective_at", DateTime(timezone=True), nullable=True),
)

Table(
    "data_domain_registry",
    Base.metadata,
    Column("domain_id", String, primary_key=True),
    Column("display_name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "data_source_registry",
    Base.metadata,
    Column("source_id", String, primary_key=True),
    Column("data_domain", String, nullable=False),
    Column("usage_scope", String, nullable=False),
    Column("priority", String, nullable=False),
    Column("status", String, nullable=False),
    Column("license_summary", Text, nullable=False),
    Column("rate_limit", JSONB, nullable=False),
    Column("adapter_kind", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "data_request",
    Base.metadata,
    Column("request_id", String, primary_key=True),
    Column("trace_id", String, nullable=False),
    Column("data_domain", String, nullable=False),
    Column("symbol_or_scope", String, nullable=False),
    Column("time_range", JSONB, nullable=True),
    Column("required_usage", String, nullable=False),
    Column("freshness_requirement", String, nullable=False),
    Column("required_fields", JSONB, nullable=False),
    Column("requesting_stage", String, nullable=False),
    Column("requesting_agent_or_service", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "data_lineage",
    Base.metadata,
    Column("lineage_id", String, primary_key=True),
    Column("request_id", String, nullable=False),
    Column("source_id", String, nullable=False),
    Column("source_ref", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "data_quality_report",
    Base.metadata,
    Column("report_id", String, primary_key=True),
    Column("request_id", String, nullable=False),
    Column("quality_score", Float, nullable=False),
    Column("quality_band", String, nullable=False),
    Column("critical_field_results", JSONB, nullable=False),
    Column("decision_core_status", String, nullable=False),
    Column("execution_core_status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "data_conflict_report",
    Base.metadata,
    Column("conflict_id", String, primary_key=True),
    Column("request_id", String, nullable=False),
    Column("severity", String, nullable=False),
    Column("field_results", JSONB, nullable=False),
    Column("resolution", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "market_state",
    Base.metadata,
    Column("market_state_id", String, primary_key=True),
    Column("effective_date", String, nullable=False),
    Column("state", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

for result_table_name in ("factor_result", "valuation_result", "portfolio_optimization_result", "risk_engine_result"):
    Table(
        result_table_name,
        Base.metadata,
        Column("result_id", String, primary_key=True),
        Column("workflow_id", String, nullable=True),
        Column("input_artifact_refs", JSONB, nullable=False),
        Column("payload", JSONB, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )

Table(
    "paper_account",
    Base.metadata,
    Column("account_id", String, primary_key=True),
    Column("base_currency", String, nullable=False),
    Column("cash", Float, nullable=False),
    Column("total_value", Float, nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "paper_order",
    Base.metadata,
    Column("paper_order_id", String, primary_key=True),
    Column("workflow_id", String, nullable=False),
    Column("decision_memo_ref", String, nullable=False),
    Column("symbol", String, nullable=False),
    Column("side", String, nullable=False),
    Column("target_quantity_or_weight", Float, nullable=False),
    Column("price_range", JSONB, nullable=False),
    Column("urgency", String, nullable=False),
    Column("execution_core_snapshot_ref", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "paper_execution_receipt",
    Base.metadata,
    Column("receipt_id", String, primary_key=True),
    Column("paper_order_id", String, nullable=False),
    Column("pricing_method", String, nullable=False),
    Column("execution_window", JSONB, nullable=False),
    Column("fill_status", String, nullable=False),
    Column("fill_price", Float, nullable=True),
    Column("fill_quantity", Float, nullable=True),
    Column("fees", JSONB, nullable=False),
    Column("taxes", JSONB, nullable=False),
    Column("slippage", JSONB, nullable=False),
    Column("t_plus_one_state", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "session",
    Base.metadata,
    Column("session_id", String, primary_key=True),
    Column("owner_role", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
)

Table(
    "user_auth",
    Base.metadata,
    Column("user_id", String, primary_key=True),
    Column("owner_role", String, nullable=False),
    Column("auth_provider", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "sensitive_field_access_event",
    Base.metadata,
    Column("event_id", String, primary_key=True),
    Column("actor", String, nullable=False),
    Column("field_ref", String, nullable=False),
    Column("access_decision", String, nullable=False),
    Column("reason_code", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Table(
    "security_finding",
    Base.metadata,
    Column("finding_id", String, primary_key=True),
    Column("severity", String, nullable=False),
    Column("finding_type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("payload", JSONB, nullable=False),
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
