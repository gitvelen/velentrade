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

    def mirror_task(self, task) -> None:
        payload = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "priority": task.priority,
            "owner_role": task.owner_role,
            "current_state": task.current_state,
            "blocked_reason": task.blocked_reason,
            "reason_code": task.reason_code,
            "artifact_refs": list(task.artifact_refs),
            "created_at": _as_datetime(task.created_at),
            "updated_at": _as_datetime(task.updated_at),
            "closed_at": _as_datetime(task.closed_at),
        }
        table = self.tables["task_envelope"]
        with self.engine.begin() as connection:
            connection.execute(table.delete().where(table.c.task_id == task.task_id))
            connection.execute(table.insert(), [payload])

    def mirror_workflow(self, workflow) -> None:
        workflow_table = self.tables["workflow"]
        attempt_table = self.tables["workflow_attempt"]
        stage_table = self.tables["workflow_stage"]
        with self.engine.begin() as connection:
            connection.execute(stage_table.delete().where(stage_table.c.workflow_id == workflow.workflow_id))
            connection.execute(attempt_table.delete().where(attempt_table.c.workflow_id == workflow.workflow_id))
            connection.execute(workflow_table.delete().where(workflow_table.c.workflow_id == workflow.workflow_id))
            connection.execute(
                workflow_table.insert(),
                [
                    {
                        "workflow_id": workflow.workflow_id,
                        "task_id": workflow.task_id,
                        "workflow_type": workflow.workflow_type,
                        "current_stage": workflow.current_stage,
                        "current_attempt_no": workflow.current_attempt_no,
                        "status": workflow.status,
                        "context_snapshot_id": workflow.context_snapshot_id,
                        "created_at": _as_datetime(workflow.created_at),
                        "updated_at": _as_datetime(workflow.updated_at),
                    }
                ],
            )
            connection.execute(
                attempt_table.insert(),
                [
                    {
                        "workflow_id": workflow.workflow_id,
                        "attempt_no": workflow.current_attempt_no,
                        "context_snapshot_id": workflow.context_snapshot_id,
                        "started_at": _as_datetime(workflow.created_at),
                        "ended_at": None,
                        "status": workflow.status,
                        "superseded_by_attempt_no": None,
                    }
                ],
            )
            connection.execute(
                stage_table.insert(),
                [
                    {
                        "workflow_id": stage.workflow_id,
                        "attempt_no": stage.attempt_no,
                        "stage": stage.stage,
                        "node_status": stage.node_status,
                        "responsible_role": stage.responsible_role,
                        "input_artifact_refs": list(stage.input_artifact_refs),
                        "output_artifact_refs": list(stage.output_artifact_refs),
                        "reason_code": stage.reason_code,
                        "started_at": _as_datetime(stage.started_at),
                        "completed_at": _as_datetime(stage.completed_at),
                        "stage_version": stage.stage_version,
                    }
                    for stage in workflow.stages
                ],
            )

    def mirror_reopen_event(self, event) -> None:
        payload = {
            "reopen_event_id": event.reopen_event_id,
            "workflow_id": event.workflow_id,
            "from_stage": event.from_stage,
            "target_stage": event.target_stage,
            "reason_code": event.reason_code,
            "requested_by": event.requested_by,
            "approved_by_or_guard": event.approved_by_or_guard,
            "invalidated_artifacts": list(event.invalidated_artifacts),
            "preserved_artifacts": list(event.preserved_artifacts),
            "attempt_no": event.attempt_no,
            "created_at": _as_datetime(event.created_at),
        }
        table = self.tables["reopen_event"]
        with self.engine.begin() as connection:
            connection.execute(table.delete().where(table.c.reopen_event_id == event.reopen_event_id))
            connection.execute(table.insert(), [payload])

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

    def list_task_read_models(self) -> list[dict[str, Any]]:
        table = self.tables["task_envelope"]
        with self.engine.connect() as connection:
            rows = connection.execute(select(table).order_by(table.c.created_at.asc())).mappings().all()
        return [self._task_row_to_read_model(row) for row in rows]

    def get_task_read_model(self, task_id: str) -> dict[str, Any] | None:
        table = self.tables["task_envelope"]
        with self.engine.connect() as connection:
            row = connection.execute(select(table).where(table.c.task_id == task_id)).mappings().one_or_none()
        return self._task_row_to_read_model(row) if row is not None else None

    def get_workflow_read_model(self, workflow_id: str) -> dict[str, Any] | None:
        workflow_table = self.tables["workflow"]
        stage_table = self.tables["workflow_stage"]
        with self.engine.connect() as connection:
            workflow = connection.execute(
                select(workflow_table).where(workflow_table.c.workflow_id == workflow_id)
            ).mappings().one_or_none()
            if workflow is None:
                return None
            stages = connection.execute(
                select(stage_table)
                .where(stage_table.c.workflow_id == workflow_id)
                .order_by(stage_table.c.attempt_no.asc(), stage_table.c.stage.asc())
            ).mappings().all()
        return {
            "workflow_id": workflow["workflow_id"],
            "task_id": workflow["task_id"],
            "workflow_type": workflow["workflow_type"],
            "current_stage": workflow["current_stage"],
            "current_attempt_no": workflow["current_attempt_no"],
            "status": workflow["status"],
            "context_snapshot_id": workflow["context_snapshot_id"],
            "created_at": _as_iso(workflow["created_at"]),
            "updated_at": _as_iso(workflow["updated_at"]),
            "stages": [self._stage_row_to_read_model(stage) for stage in stages],
        }

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

    def _task_row_to_read_model(self, row) -> dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "task_type": row["task_type"],
            "priority": row["priority"],
            "owner_role": row["owner_role"],
            "current_state": row["current_state"],
            "reason_code": row["reason_code"],
            "artifact_refs": list(row["artifact_refs"] or []),
            "created_at": _as_iso(row["created_at"]),
            "updated_at": _as_iso(row["updated_at"]),
            "blocked_reason": row["blocked_reason"],
            "closed_at": _as_iso(row["closed_at"]),
        }

    def _stage_row_to_read_model(self, row) -> dict[str, Any]:
        return {
            "workflow_id": row["workflow_id"],
            "attempt_no": row["attempt_no"],
            "stage": row["stage"],
            "node_status": row["node_status"],
            "responsible_role": row["responsible_role"],
            "input_artifact_refs": list(row["input_artifact_refs"] or []),
            "output_artifact_refs": list(row["output_artifact_refs"] or []),
            "reason_code": row["reason_code"],
            "started_at": _as_iso(row["started_at"]),
            "completed_at": _as_iso(row["completed_at"]),
            "stage_version": row["stage_version"],
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
