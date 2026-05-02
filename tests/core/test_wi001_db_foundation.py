from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from velentrade.db.base import Base


def test_sqlalchemy_metadata_contains_wi001_foundation_tables_and_columns():
    table_names = set(Base.metadata.tables)
    assert {
        "artifact",
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


def test_alembic_is_configured_with_a_wi001_foundation_revision():
    config = Config(str(Path("alembic.ini")))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()

    assert len(heads) == 1

    revision = script.get_revision(heads[0])
    assert revision is not None
    text = Path(revision.path).read_text(encoding="utf-8")
    assert "artifact" in text
    assert "collaboration_session" in text
    assert "memory_item" in text
