from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from velentrade.domain.agents.models import CapabilityProfile
from velentrade.domain.agents.registry import OFFICIAL_SERVICES
from velentrade.domain.collaboration.models import AgentRun, CollaborationCommand, CollaborationEvent, HandoffPacket
from velentrade.domain.common import GuardDecision, new_id, utc_now
from velentrade.domain.memory.models import (
    ContextSlice,
    MemoryCapture,
    MemoryExtractionResult,
    MemoryItem,
    MemoryRelation,
    MemoryVersion,
)


@dataclass(frozen=True)
class DirectBusinessWrite:
    actor: str
    table: str


@dataclass(frozen=True)
class GatewayWriteResult:
    accepted: bool
    object_type: str
    object_id: str
    audit_event_id: str
    outbox_event_id: str
    reason_code: str | None = None


SERVICE_ARTIFACT_TYPES = {
    "data_collection_quality": {"DataReadinessReport", "DataLineage", "DataQualityReport"},
    "market_state_evaluation": {"MarketStateReport", "ServiceResult"},
    "factor_engine": {"FactorAttributionReport", "ServiceResult"},
    "valuation_engine": {"ValuationResult", "ServiceResult"},
    "portfolio_optimization": {"DecisionPacket", "DecisionGuardResult", "PortfolioOptimizationResult"},
    "risk_engine": {"DecisionGuardResult", "RiskReviewReport"},
    "trade_execution": {"PaperExecutionReceipt", "PaperOrder", "PaperAccount", "PositionDisposalTask"},
    "performance_attribution_evaluation": {"AttributionReport", "ReflectionRecord"},
}


def _artifact_payload_rejection_reason(artifact_type: str, payload: dict[str, Any]) -> str | None:
    if artifact_type == "ICContextPackage":
        required = {
            "topic_id",
            "request_brief_ref",
            "data_readiness_ref",
            "market_state_ref",
            "service_result_refs",
            "portfolio_context_ref",
            "risk_constraint_refs",
            "research_package_refs",
            "role_attachment_refs",
            "context_snapshot_id",
        }
        if any(payload.get(field) in (None, "", []) for field in required):
            return "schema_validation_failed"
        return None
    if artifact_type == "ICChairBrief":
        required = {
            "decision_question",
            "scope_boundary",
            "key_tensions",
            "must_answer_questions",
            "time_budget",
            "action_standard",
            "risk_constraints_to_respect",
            "forbidden_assumptions",
            "no_preset_decision_attestation",
        }
        if any(field not in payload or payload.get(field) in (None, "") for field in required):
            return "schema_validation_failed"
        if payload.get("no_preset_decision_attestation") is not True:
            return "schema_validation_failed"
        return None
    if artifact_type != "PositionDisposalTask":
        return None
    required = {
        "task_id",
        "symbol",
        "triggers",
        "priority",
        "risk_gate_present",
        "execution_core_guard_present",
        "direct_execution_allowed",
        "workflow_route",
        "reason_code",
    }
    if any(field not in payload or payload.get(field) in (None, "", []) for field in required):
        return "schema_validation_failed"
    if payload.get("direct_execution_allowed") is not False:
        return "position_disposal_requires_risk_review"
    if payload.get("risk_gate_present") is not True:
        return "position_disposal_requires_risk_review"
    if payload.get("execution_core_guard_present") is not True:
        return "position_disposal_requires_risk_review"
    if "risk_review" not in str(payload.get("workflow_route", "")):
        return "position_disposal_requires_risk_review"
    return None


@dataclass
class AuthorityGateway:
    profiles: dict[str, CapabilityProfile]
    store: Any | None = None
    artifact_ledger: list[dict[str, Any]] = field(default_factory=list)
    command_ledger: list[CollaborationCommand] = field(default_factory=list)
    event_ledger: list[CollaborationEvent] = field(default_factory=list)
    handoff_ledger: list[HandoffPacket] = field(default_factory=list)
    memory_items: list[MemoryItem] = field(default_factory=list)
    memory_versions: list[MemoryVersion] = field(default_factory=list)
    memory_extraction_results: list[MemoryExtractionResult] = field(default_factory=list)
    memory_relations: list[MemoryRelation] = field(default_factory=list)
    denied_direct_writes: list[dict[str, Any]] = field(default_factory=list)
    _idempotency: dict[str, GatewayWriteResult] = field(default_factory=dict)

    def _idempotent(self, key: str, result_factory) -> GatewayWriteResult:
        if key in self._idempotency:
            return self._idempotency[key]
        result = result_factory()
        self._idempotency[key] = result
        return result

    def append_artifact(
        self,
        run: AgentRun,
        artifact_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
        schema_version: str = "1.0.0",
        source_refs: list[str] | None = None,
    ) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            profile = self.profiles[run.agent_id]
            if artifact_type not in profile.write_policy.artifact_types:
                return GatewayWriteResult(False, "artifact", "", "", "", "permission_denied")
            rejection_reason = _artifact_payload_rejection_reason(artifact_type, payload)
            if rejection_reason is not None:
                return GatewayWriteResult(False, "artifact", "", "", "", rejection_reason)
            artifact_id = new_id("artifact")
            artifact_row = {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "workflow_id": run.workflow_id,
                "attempt_no": run.attempt_no,
                "trace_id": new_id("trace"),
                "producer": run.agent_id,
                "producer_type": "agent",
                "status": "accepted",
                "schema_version": schema_version,
                "payload": payload,
                "source_refs": source_refs or [],
                "summary": str(payload.get("summary", "")) if isinstance(payload, dict) else "",
                "evidence_refs": [],
                "decision_refs": [],
                "created_at": utc_now(),
            }
            self.artifact_ledger.append(artifact_row)
            result = GatewayWriteResult(True, "artifact", artifact_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_artifact(
                    artifact_row,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def append_service_artifact(
        self,
        *,
        workflow_id: str,
        attempt_no: int,
        producer_service: str,
        artifact_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
        schema_version: str = "1.0.0",
        source_refs: list[str] | None = None,
    ) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            if producer_service not in OFFICIAL_SERVICES:
                return GatewayWriteResult(False, "artifact", "", "", "", "unknown_service")
            if artifact_type not in SERVICE_ARTIFACT_TYPES.get(producer_service, set()):
                return GatewayWriteResult(False, "artifact", "", "", "", "permission_denied")
            rejection_reason = _artifact_payload_rejection_reason(artifact_type, payload)
            if rejection_reason is not None:
                return GatewayWriteResult(False, "artifact", "", "", "", rejection_reason)
            artifact_id = new_id("artifact")
            artifact_row = {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "workflow_id": workflow_id,
                "attempt_no": attempt_no,
                "trace_id": new_id("trace"),
                "producer": producer_service,
                "producer_type": "service",
                "status": "accepted",
                "schema_version": schema_version,
                "payload": payload,
                "source_refs": source_refs or [],
                "summary": str(payload.get("summary", "")) if isinstance(payload, dict) else "",
                "evidence_refs": [],
                "decision_refs": [],
                "created_at": utc_now(),
            }
            self.artifact_ledger.append(artifact_row)
            result = GatewayWriteResult(True, "artifact", artifact_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_artifact(
                    artifact_row,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def append_command(
        self,
        run: AgentRun,
        command: CollaborationCommand,
        idempotency_key: str,
    ) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            profile = self.profiles[run.agent_id]
            if command.command_type not in profile.write_policy.command_types:
                return GatewayWriteResult(False, "command", command.command_id, "", "", "permission_denied")
            accepted = CollaborationCommand(
                **{**command.__dict__, "admission_status": "accepted", "resolved_at": utc_now()}
            )
            self.command_ledger.append(accepted)
            result = GatewayWriteResult(True, "command", command.command_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_command(
                    accepted,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def capture_memory(self, capture: MemoryCapture, idempotency_key: str) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            memory_id = new_id("memory")
            version_id = new_id("memory-version")
            now = utc_now()
            producer_profile = self.profiles.get(capture.producer_agent_id)
            item = MemoryItem(
                memory_id=memory_id,
                memory_type=capture.suggested_memory_type,
                owner_role=producer_profile.role if producer_profile else "owner",
                producer_agent_id=capture.producer_agent_id,
                status="validated_context",
                current_version_id=version_id,
                source_refs=capture.source_refs,
                sensitivity=capture.sensitivity,
                pinned=False,
                created_at=now,
                updated_at=now,
            )
            version = MemoryVersion(
                version_id=version_id,
                memory_id=memory_id,
                version_no=1,
                content_markdown=capture.content_markdown,
                payload=capture.payload,
                created_by=capture.producer_agent_id,
                created_at=now,
                content_hash=sha256(capture.content_markdown.encode("utf-8")).hexdigest(),
            )
            title = next(
                (
                    line.lstrip("# ").strip()
                    for line in capture.content_markdown.splitlines()
                    if line.strip()
                ),
                "Untitled Memory",
            )
            extraction = MemoryExtractionResult(
                extraction_id=new_id("memory-extraction"),
                memory_version_id=version_id,
                extractor_version="wi001-fixture",
                title=title,
                tags=[],
                mentions=[],
                has_link="http://" in capture.content_markdown or "https://" in capture.content_markdown,
                has_task_list="- [ ]" in capture.content_markdown,
                has_code="```" in capture.content_markdown,
                has_incomplete_tasks="- [ ]" in capture.content_markdown,
                symbol_refs=list(capture.payload.get("symbol_refs", [])),
                artifact_refs=list(capture.payload.get("artifact_refs", [])),
                agent_refs=list(capture.payload.get("agent_refs", [])),
                stage_refs=list(capture.payload.get("stage_refs", [])),
                source_refs=list(capture.source_refs),
                sensitivity=capture.sensitivity,
                status="succeeded",
                created_at=now,
            )
            self.memory_items.append(item)
            self.memory_versions.append(version)
            self.memory_extraction_results.append(extraction)
            result = GatewayWriteResult(True, "memory_item", memory_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_memory(
                    item,
                    version,
                    extraction,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def append_event(
        self,
        run: AgentRun,
        event_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
        trace_id: str | None = None,
    ) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            event = CollaborationEvent(
                event_id=new_id("event"),
                event_type=event_type,
                workflow_id=run.workflow_id,
                attempt_no=run.attempt_no,
                trace_id=trace_id or new_id("trace"),
                payload=payload,
                created_at=utc_now(),
                session_id=run.session_id,
                agent_run_id=run.agent_run_id,
            )
            self.event_ledger.append(event)
            result = GatewayWriteResult(True, "event", event.event_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_event(
                    event,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def append_handoff(self, handoff: HandoffPacket, idempotency_key: str) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            self.handoff_ledger.append(handoff)
            result = GatewayWriteResult(True, "handoff", handoff.handoff_id, new_id("audit"), new_id("outbox"))
            if self.store is not None:
                self.store.mirror_handoff(
                    handoff,
                    audit_event_id=result.audit_event_id,
                    outbox_event_id=result.outbox_event_id,
                    idempotency_key=idempotency_key,
                )
            return result

        return self._idempotent(idempotency_key, write)

    def build_context_slice(
        self,
        agent_id: str,
        context_snapshot_id: str,
        memory_refs: list[str],
        artifact_refs: list[str],
    ) -> ContextSlice:
        profile = self.profiles[agent_id]
        denied = []
        injected = []
        for ref in memory_refs:
            item = next((memory for memory in self.memory_items if memory.memory_id == ref), None)
            if item and item.sensitivity == "finance_sensitive_raw" and "finance_sensitive_raw" in profile.default_context_policy.denied:
                denied.append(ref)
            elif item:
                injected.append(ref)
        return ContextSlice(
            context_slice_id=new_id("slice"),
            context_snapshot_id=context_snapshot_id,
            agent_id=agent_id,
            profile_version=profile.profile_version,
            artifact_refs_injected=artifact_refs,
            memory_refs_injected=injected,
            denied_memory_refs=denied,
            retrieval_query_summary="fixture memory recall; artifact priority preserved",
            redaction_policy_applied="finance_sensitive_raw denied for non-CFO agents",
        )

    def deny_direct_write(self, write: DirectBusinessWrite) -> GuardDecision:
        event = {"actor": write.actor, "table": write.table, "created_at": utc_now()}
        self.denied_direct_writes.append(event)
        return GuardDecision(
            allowed=False,
            code="DIRECT_WRITE_DENIED",
            reason_code="direct_write_denied",
            message="Runner and agents must write through Authority Gateway.",
            details=event,
        )

    def reject_memory_as_fact_source(self, memory_ref: str) -> GuardDecision:
        return GuardDecision(
            allowed=False,
            code="STAGE_GUARD_FAILED",
            reason_code="memory_not_fact_source",
            message="Memory may be context or evidence lead, never formal business fact source.",
            details={"memory_ref": memory_ref},
        )

    def append_memory_relation(
        self,
        memory_id: str,
        target_ref: str,
        relation_type: str,
        reason: str,
        evidence_refs: list[str],
        client_seen_version_id: str,
        created_by: str = "owner",
    ) -> MemoryRelation:
        item = next((memory for memory in self.memory_items if memory.memory_id == memory_id), None)
        if item is None:
            raise KeyError(memory_id)
        if item.current_version_id != client_seen_version_id:
            raise ValueError("client_seen_version_mismatch")
        relation = MemoryRelation(
            relation_id=new_id("memory-relation"),
            source_memory_id=memory_id,
            target_ref=target_ref,
            relation_type=relation_type,
            reason=reason,
            evidence_refs=evidence_refs,
            created_by=created_by,
            created_at=utc_now(),
        )
        self.memory_relations.append(relation)
        if self.store is not None:
            self.store.mirror_memory_relation(relation)
        return relation

    def list_memory_read_models(self) -> list[dict[str, Any]]:
        return [self.get_memory_read_model(item.memory_id) for item in self.memory_items]

    def get_memory_read_model(self, memory_id: str) -> dict[str, Any] | None:
        item = next((memory for memory in self.memory_items if memory.memory_id == memory_id), None)
        if item is None:
            return None
        version = next(
            (memory_version for memory_version in self.memory_versions if memory_version.version_id == item.current_version_id),
            None,
        )
        extraction = next(
            (
                result
                for result in self.memory_extraction_results
                if version is not None and result.memory_version_id == version.version_id
            ),
            None,
        )
        relations = [relation for relation in self.memory_relations if relation.source_memory_id == memory_id]
        return {
            "memory_id": item.memory_id,
            "memory_type": item.memory_type,
            "status": item.status,
            "current_version_id": item.current_version_id,
            "title": extraction.title if extraction else "Untitled Memory",
            "summary": (version.content_markdown[:120] if version else "").strip(),
            "tags": extraction.tags if extraction else [],
            "source_refs": list(item.source_refs),
            "artifact_refs": extraction.artifact_refs if extraction else [],
            "symbol_refs": extraction.symbol_refs if extraction else [],
            "agent_refs": extraction.agent_refs if extraction else [],
            "stage_refs": extraction.stage_refs if extraction else [],
            "relations": [
                {
                    "relation_id": relation.relation_id,
                    "target_ref": relation.target_ref,
                    "relation_type": relation.relation_type,
                    "reason": relation.reason,
                    "evidence_refs": list(relation.evidence_refs),
                    "created_by": relation.created_by,
                    "created_at": relation.created_at,
                }
                for relation in relations
            ],
            "collections": [],
            "sensitivity": item.sensitivity,
            "promotion_state": item.status,
            "why_included": "fenced_background_context_only",
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
