from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from velentrade.db.base import Base


def test_sqlalchemy_metadata_contains_wi001_foundation_tables_and_columns():
    table_names = set(Base.metadata.tables)
    assert {
        "artifact",
        "task_envelope",
        "workflow",
        "workflow_attempt",
        "workflow_stage",
        "reopen_event",
        "approval_record",
        "manual_todo",
        "governance_change",
        "data_domain_registry",
        "data_source_registry",
        "data_request",
        "data_lineage",
        "data_quality_report",
        "data_conflict_report",
        "market_state",
        "factor_result",
        "valuation_result",
        "portfolio_optimization_result",
        "risk_engine_result",
        "paper_account",
        "paper_order",
        "paper_execution_receipt",
        "session",
        "user_auth",
        "sensitive_field_access_event",
        "security_finding",
        "collaboration_session",
        "agent_run",
        "collaboration_command",
        "collaboration_event",
        "handoff_packet",
        "context_snapshot",
        "memory_item",
        "memory_version",
        "memory_extraction_result",
        "memory_relation",
        "memory_collection",
        "knowledge_item",
        "default_context_binding",
        "process_archive",
        "audit_event",
        "outbox_event",
        "runner_write_denial",
    }.issubset(table_names)

    artifact_columns = set(Base.metadata.tables["artifact"].columns.keys())
    assert {
        "artifact_id",
        "artifact_type",
        "workflow_id",
        "attempt_no",
        "trace_id",
        "producer",
        "producer_type",
        "status",
        "schema_version",
        "payload",
        "created_at",
    }.issubset(artifact_columns)

    memory_columns = set(Base.metadata.tables["memory_item"].columns.keys())
    assert {
        "memory_id",
        "memory_type",
        "owner_role",
        "producer_agent_id",
        "status",
        "current_version_id",
        "source_refs",
        "sensitivity",
        "pinned",
        "created_at",
        "updated_at",
    }.issubset(memory_columns)

    workflow_stage_columns = set(Base.metadata.tables["workflow_stage"].columns.keys())
    assert {
        "workflow_id",
        "attempt_no",
        "stage",
        "node_status",
        "responsible_role",
        "input_artifact_refs",
        "output_artifact_refs",
        "reason_code",
        "stage_version",
    }.issubset(workflow_stage_columns)

    data_request_columns = set(Base.metadata.tables["data_request"].columns.keys())
    assert {
        "request_id",
        "trace_id",
        "data_domain",
        "symbol_or_scope",
        "required_usage",
        "freshness_requirement",
        "required_fields",
        "requesting_stage",
        "requesting_agent_or_service",
        "created_at",
    }.issubset(data_request_columns)

    governance_change_columns = set(Base.metadata.tables["governance_change"].columns.keys())
    assert {
        "change_id",
        "change_type",
        "impact_level",
        "state",
        "proposal_ref",
        "context_snapshot_id",
        "effective_scope",
        "state_reason",
        "created_at",
        "updated_at",
    }.issubset(governance_change_columns)


def test_alembic_is_configured_with_a_wi001_foundation_revision():
    config = Config(str(Path("alembic.ini")))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()

    assert len(heads) == 1

    required_foundation_tables = {
        "artifact",
        "task_envelope",
        "workflow_stage",
        "data_request",
        "governance_change",
        "paper_order",
        "collaboration_session",
        "memory_item",
    }

    revision = script.get_revision(heads[0])
    assert revision is not None
    found_foundation_revision = False
    while revision is not None:
        text = Path(revision.path).read_text(encoding="utf-8")
        if required_foundation_tables.issubset(set(text.split('"'))):
            found_foundation_revision = True
            break

        down_revision = revision.down_revision
        assert not isinstance(down_revision, tuple)
        revision = script.get_revision(down_revision) if down_revision else None

    assert found_foundation_revision


def test_alembic_env_prefers_runtime_database_url_env():
    text = Path("migrations/env.py").read_text(encoding="utf-8")

    assert "VELENTRADE_DATABASE_URL" in text
    assert "os.getenv" in text
    assert "config.set_main_option(\"sqlalchemy.url\"" in text
