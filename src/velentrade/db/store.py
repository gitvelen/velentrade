from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine

from velentrade.db.base import Base
from velentrade.domain.collaboration.models import CollaborationCommand, CollaborationEvent, HandoffPacket
from velentrade.domain.memory.models import MemoryExtractionResult, MemoryItem, MemoryRelation, MemoryVersion


def _as_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _as_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


class SqlAlchemyGatewayMirror:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.tables = Base.metadata.tables

    def mirror_artifact(
        self,
        artifact_row: dict[str, Any],
        *,
        audit_event_id: str,
        outbox_event_id: str,
        idempotency_key: str,
    ) -> None:
        payload = dict(artifact_row)
        payload["created_at"] = _as_datetime(payload["created_at"])
        with self.engine.begin() as connection:
            connection.execute(self.tables["artifact"].insert(), [payload])
            self._write_audit_and_outbox(
                connection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
                object_type="artifact",
                object_id=str(payload["artifact_id"]),
                actor=str(payload["producer"]),
                event_type="artifact_submitted",
                payload={"artifact_type": payload["artifact_type"]},
                idempotency_key=idempotency_key,
            )

    def mirror_command(
        self,
        command: CollaborationCommand,
        *,
        audit_event_id: str,
        outbox_event_id: str,
        idempotency_key: str,
    ) -> None:
        payload = {
            "command_id": command.command_id,
            "command_type": command.command_type,
            "workflow_id": command.workflow_id,
            "attempt_no": command.attempt_no,
            "stage": command.stage,
            "session_id": command.session_id,
            "source_agent_run_id": command.source_agent_run_id,
            "source_agent_id": command.source_agent_id,
            "target_agent_id_or_service": command.target_agent_id_or_service,
            "payload": command.payload,
            "requested_admission_type": command.requested_admission_type,
            "admission_status": command.admission_status,
            "admission_reason": command.admission_reason,
            "result_ref": command.result_ref,
            "created_at": _as_datetime(command.created_at),
            "resolved_at": _as_datetime(command.resolved_at),
        }
        with self.engine.begin() as connection:
            connection.execute(self.tables["collaboration_command"].insert(), [payload])
            self._write_audit_and_outbox(
                connection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
                object_type="command",
                object_id=command.command_id,
                actor=command.source_agent_id,
                event_type="command_accepted",
                payload={"command_type": command.command_type},
                idempotency_key=idempotency_key,
            )

    def mirror_event(
        self,
        event: CollaborationEvent,
        *,
        audit_event_id: str,
        outbox_event_id: str,
        idempotency_key: str,
    ) -> None:
        payload = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "workflow_id": event.workflow_id,
            "attempt_no": event.attempt_no,
            "session_id": event.session_id,
            "agent_run_id": event.agent_run_id,
            "command_id": event.command_id,
            "artifact_id": event.artifact_id,
            "trace_id": event.trace_id,
            "payload": event.payload,
            "created_at": _as_datetime(event.created_at),
        }
        with self.engine.begin() as connection:
            connection.execute(self.tables["collaboration_event"].insert(), [payload])
            self._write_audit_and_outbox(
                connection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
                object_type="event",
                object_id=event.event_id,
                actor=event.agent_run_id or "system",
                event_type=event.event_type,
                payload=event.payload,
                idempotency_key=idempotency_key,
            )

    def mirror_handoff(
        self,
        handoff: HandoffPacket,
        *,
        audit_event_id: str,
        outbox_event_id: str,
        idempotency_key: str,
    ) -> None:
        payload = {
            "handoff_id": handoff.handoff_id,
            "workflow_id": handoff.workflow_id,
            "attempt_no": handoff.attempt_no,
            "from_stage": handoff.from_stage,
            "to_stage_or_agent": handoff.to_stage_or_agent,
            "producer_agent_id_or_service": handoff.producer_agent_id_or_service,
            "source_artifact_refs": handoff.source_artifact_refs,
            "summary": handoff.summary,
            "open_questions": handoff.open_questions,
            "blockers": handoff.blockers,
            "decisions_made": handoff.decisions_made,
            "invalidated_artifacts": handoff.invalidated_artifacts,
            "preserved_artifacts": handoff.preserved_artifacts,
            "created_at": _as_datetime(handoff.created_at),
        }
        with self.engine.begin() as connection:
            connection.execute(self.tables["handoff_packet"].insert(), [payload])
            self._write_audit_and_outbox(
                connection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
                object_type="handoff",
                object_id=handoff.handoff_id,
                actor=handoff.producer_agent_id_or_service,
                event_type="handoff_created",
                payload={"to_stage_or_agent": handoff.to_stage_or_agent},
                idempotency_key=idempotency_key,
            )

    def mirror_memory(
        self,
        item: MemoryItem,
        version: MemoryVersion,
        extraction: MemoryExtractionResult,
        *,
        audit_event_id: str,
        outbox_event_id: str,
        idempotency_key: str,
    ) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                self.tables["memory_item"].insert(),
                [
                    {
                        "memory_id": item.memory_id,
                        "memory_type": item.memory_type,
                        "owner_role": item.owner_role,
                        "producer_agent_id": item.producer_agent_id,
                        "status": item.status,
                        "current_version_id": item.current_version_id,
                        "source_refs": item.source_refs,
                        "sensitivity": item.sensitivity,
                        "pinned": item.pinned,
                        "created_at": _as_datetime(item.created_at),
                        "updated_at": _as_datetime(item.updated_at),
                    }
                ],
            )
            connection.execute(
                self.tables["memory_version"].insert(),
                [
                    {
                        "version_id": version.version_id,
                        "memory_id": version.memory_id,
                        "version_no": version.version_no,
                        "content_markdown": version.content_markdown,
                        "payload": version.payload,
                        "created_by": version.created_by,
                        "created_at": _as_datetime(version.created_at),
                        "content_hash": version.content_hash,
                        "superseded_by_version_id": version.superseded_by_version_id,
                    }
                ],
            )
            connection.execute(
                self.tables["memory_extraction_result"].insert(),
                [
                    {
                        "extraction_id": extraction.extraction_id,
                        "memory_version_id": extraction.memory_version_id,
                        "extractor_version": extraction.extractor_version,
                        "title": extraction.title,
                        "tags": extraction.tags,
                        "mentions": extraction.mentions,
                        "has_link": extraction.has_link,
                        "has_task_list": extraction.has_task_list,
                        "has_code": extraction.has_code,
                        "has_incomplete_tasks": extraction.has_incomplete_tasks,
                        "symbol_refs": extraction.symbol_refs,
                        "artifact_refs": extraction.artifact_refs,
                        "agent_refs": extraction.agent_refs,
                        "stage_refs": extraction.stage_refs,
                        "source_refs": extraction.source_refs,
                        "sensitivity": extraction.sensitivity,
                        "status": extraction.status,
                        "created_at": _as_datetime(extraction.created_at),
                    }
                ],
            )
            self._write_audit_and_outbox(
                connection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
                object_type="memory_item",
                object_id=item.memory_id,
                actor=item.producer_agent_id,
                event_type="memory_captured",
                payload={"memory_type": item.memory_type},
                idempotency_key=idempotency_key,
            )

    def mirror_memory_relation(self, relation: MemoryRelation) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                self.tables["memory_relation"].insert(),
                [
                    {
                        "relation_id": relation.relation_id,
                        "source_memory_id": relation.source_memory_id,
                        "target_ref": relation.target_ref,
                        "relation_type": relation.relation_type,
                        "reason": relation.reason,
                        "evidence_refs": relation.evidence_refs,
                        "created_by": relation.created_by,
                        "created_at": _as_datetime(relation.created_at),
                    }
                ],
            )

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                select(self.tables["artifact"]).where(self.tables["artifact"].c.artifact_id == artifact_id)
            ).mappings().one_or_none()
        if row is None:
            return None
        artifact = dict(row)
        artifact["created_at"] = _as_iso(artifact["created_at"])
        return artifact

    def list_events(self, workflow_id: str) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(self.tables["collaboration_event"])
                .where(self.tables["collaboration_event"].c.workflow_id == workflow_id)
                .order_by(self.tables["collaboration_event"].c.created_at.asc())
            ).mappings().all()
        events = []
        for row in rows:
            event = dict(row)
            event["created_at"] = _as_iso(event["created_at"])
            events.append(event)
        return events

    def list_handoffs(self, workflow_id: str) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(self.tables["handoff_packet"])
                .where(self.tables["handoff_packet"].c.workflow_id == workflow_id)
                .order_by(self.tables["handoff_packet"].c.created_at.asc())
            ).mappings().all()
        handoffs = []
        for row in rows:
            handoff = dict(row)
            handoff["created_at"] = _as_iso(handoff["created_at"])
            handoffs.append(handoff)
        return handoffs

    def list_memory_read_models(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(self.tables["memory_item"]).order_by(self.tables["memory_item"].c.created_at.asc())
            ).mappings().all()
        return [
            memory
            for memory_id in [row["memory_id"] for row in rows]
            if (memory := self.get_memory_read_model(memory_id)) is not None
        ]

    def get_memory_read_model(self, memory_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as connection:
            item = connection.execute(
                select(self.tables["memory_item"]).where(self.tables["memory_item"].c.memory_id == memory_id)
            ).mappings().one_or_none()
            if item is None:
                return None
            version = connection.execute(
                select(self.tables["memory_version"]).where(
                    self.tables["memory_version"].c.version_id == item["current_version_id"]
                )
            ).mappings().one_or_none()
            extraction = None
            if version is not None:
                extraction = connection.execute(
                    select(self.tables["memory_extraction_result"]).where(
                        self.tables["memory_extraction_result"].c.memory_version_id == version["version_id"]
                    )
                ).mappings().one_or_none()
            relation_rows = connection.execute(
                select(self.tables["memory_relation"])
                .where(self.tables["memory_relation"].c.source_memory_id == memory_id)
                .order_by(self.tables["memory_relation"].c.created_at.asc())
            ).mappings().all()

        return {
            "memory_id": item["memory_id"],
            "memory_type": item["memory_type"],
            "status": item["status"],
            "current_version_id": item["current_version_id"],
            "title": extraction["title"] if extraction else "Untitled Memory",
            "summary": (version["content_markdown"][:120].strip() if version else ""),
            "tags": list(extraction["tags"]) if extraction else [],
            "source_refs": list(item["source_refs"]),
            "artifact_refs": list(extraction["artifact_refs"]) if extraction else [],
            "symbol_refs": list(extraction["symbol_refs"]) if extraction else [],
            "agent_refs": list(extraction["agent_refs"]) if extraction else [],
            "stage_refs": list(extraction["stage_refs"]) if extraction else [],
            "relations": [
                {
                    "relation_id": row["relation_id"],
                    "target_ref": row["target_ref"],
                    "relation_type": row["relation_type"],
                    "reason": row["reason"],
                    "evidence_refs": list(row["evidence_refs"] or []),
                    "created_by": row["created_by"],
                    "created_at": _as_iso(row["created_at"]),
                }
                for row in relation_rows
            ],
            "collections": [],
            "sensitivity": item["sensitivity"],
            "promotion_state": item["status"],
            "why_included": "fenced_background_context_only",
            "created_at": _as_iso(item["created_at"]),
            "updated_at": _as_iso(item["updated_at"]),
        }

    def _write_audit_and_outbox(
        self,
        connection,
        *,
        audit_event_id: str,
        outbox_event_id: str,
        object_type: str,
        object_id: str,
        actor: str,
        event_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> None:
        now = datetime.utcnow()
        connection.execute(
            self.tables["audit_event"].insert(),
            [
                {
                    "audit_event_id": audit_event_id,
                    "event_type": event_type,
                    "object_type": object_type,
                    "object_id": object_id,
                    "actor": actor,
                    "payload": payload,
                    "created_at": now,
                }
            ],
        )
        connection.execute(
            self.tables["outbox_event"].insert(),
            [
                {
                    "outbox_event_id": outbox_event_id,
                    "topic": f"wi001.{object_type}",
                    "payload": payload,
                    "idempotency_key": idempotency_key,
                    "created_at": now,
                }
            ],
        )
