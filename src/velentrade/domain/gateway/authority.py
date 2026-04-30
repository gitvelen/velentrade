from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from velentrade.domain.agents.models import CapabilityProfile
from velentrade.domain.collaboration.models import AgentRun, CollaborationCommand
from velentrade.domain.common import GuardDecision, new_id, utc_now
from velentrade.domain.memory.models import ContextSlice, MemoryCapture, MemoryItem, MemoryVersion


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


@dataclass
class AuthorityGateway:
    profiles: dict[str, CapabilityProfile]
    artifact_ledger: list[dict[str, Any]] = field(default_factory=list)
    command_ledger: list[CollaborationCommand] = field(default_factory=list)
    memory_items: list[MemoryItem] = field(default_factory=list)
    memory_versions: list[MemoryVersion] = field(default_factory=list)
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
    ) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            profile = self.profiles[run.agent_id]
            if artifact_type not in profile.write_policy.artifact_types:
                return GatewayWriteResult(False, "artifact", "", "", "", "permission_denied")
            artifact_id = new_id("artifact")
            self.artifact_ledger.append(
                {
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "workflow_id": run.workflow_id,
                    "attempt_no": run.attempt_no,
                    "producer": run.agent_id,
                    "status": "accepted",
                    "payload": payload,
                    "created_at": utc_now(),
                }
            )
            return GatewayWriteResult(True, "artifact", artifact_id, new_id("audit"), new_id("outbox"))

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
            return GatewayWriteResult(True, "command", command.command_id, new_id("audit"), new_id("outbox"))

        return self._idempotent(idempotency_key, write)

    def capture_memory(self, capture: MemoryCapture, idempotency_key: str) -> GatewayWriteResult:
        def write() -> GatewayWriteResult:
            memory_id = new_id("memory")
            version_id = new_id("memory-version")
            now = utc_now()
            item = MemoryItem(
                memory_id=memory_id,
                memory_type=capture.suggested_memory_type,
                owner_role="owner",
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
            self.memory_items.append(item)
            self.memory_versions.append(version)
            return GatewayWriteResult(True, "memory_item", memory_id, new_id("audit"), new_id("outbox"))

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
