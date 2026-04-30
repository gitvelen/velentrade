from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from hashlib import sha256
from typing import Any

from velentrade.domain.common import new_id, utc_now


AUTO_VALIDATION_REQUIRED = {"schema", "fixture", "scope", "rollback", "snapshot"}


@dataclass(frozen=True)
class ContextSnapshot:
    context_snapshot_id: str
    snapshot_version: str
    created_at: str
    created_by: str
    effective_from: str
    effective_scope: str
    source_change_ref: str
    threshold_versions: list[str]
    risk_parameter_versions: list[str]
    approval_rule_versions: list[str]
    prompt_versions: dict[str, str]
    skill_package_versions: dict[str, str]
    knowledge_item_versions: list[str]
    memory_collection_versions: list[str]
    default_context_versions: list[str]
    agent_capability_versions: dict[str, str]
    model_route_version: str
    tool_permission_versions: list[str]
    data_policy_version: str
    registry_versions: list[str]
    service_degradation_policy_version: str
    execution_parameter_version: str
    content_hash: str
    frozen: bool = True


@dataclass(frozen=True)
class GovernanceChange:
    change_id: str
    change_type: str
    impact_level: str
    state: str
    proposal_ref: str
    target_version_refs: dict[str, Any]
    effective_scope: str
    rollback_plan_ref: str
    created_at: str
    updated_at: str
    comparison_analysis_ref: str | None = None
    auto_validation_refs: list[str] = field(default_factory=list)
    owner_approval_ref: str | None = None
    context_snapshot_id: str | None = None
    state_reason: str | None = None
    decided_at: str | None = None
    effective_at: str | None = None


@dataclass
class GovernanceRuntime:
    context_snapshots: dict[str, ContextSnapshot] = field(default_factory=dict)
    changes: dict[str, GovernanceChange] = field(default_factory=dict)
    current_context_snapshot_id: str | None = None

    def _content_hash(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()

    def create_context_snapshot(
        self,
        snapshot_version: str,
        source_change_ref: str,
        prompt_versions: dict[str, str],
        skill_package_versions: dict[str, str],
        knowledge_item_versions: list[str],
        memory_collection_versions: list[str],
        default_context_versions: list[str],
        agent_capability_versions: dict[str, str],
        effective_scope: str,
    ) -> ContextSnapshot:
        payload = {
            "snapshot_version": snapshot_version,
            "source_change_ref": source_change_ref,
            "prompt_versions": prompt_versions,
            "skill_package_versions": skill_package_versions,
            "knowledge_item_versions": knowledge_item_versions,
            "memory_collection_versions": memory_collection_versions,
            "default_context_versions": default_context_versions,
            "agent_capability_versions": agent_capability_versions,
            "effective_scope": effective_scope,
        }
        now = utc_now()
        snapshot = ContextSnapshot(
            context_snapshot_id=new_id("ctx"),
            snapshot_version=snapshot_version,
            created_at=now,
            created_by="governance_runtime",
            effective_from=now,
            effective_scope=effective_scope,
            source_change_ref=source_change_ref,
            threshold_versions=["threshold-v1"],
            risk_parameter_versions=["risk-v1"],
            approval_rule_versions=["approval-v1"],
            prompt_versions=dict(prompt_versions),
            skill_package_versions=dict(skill_package_versions),
            knowledge_item_versions=list(knowledge_item_versions),
            memory_collection_versions=list(memory_collection_versions),
            default_context_versions=list(default_context_versions),
            agent_capability_versions=dict(agent_capability_versions),
            model_route_version="model-route-v1",
            tool_permission_versions=["tool-v1"],
            data_policy_version="data-policy-v1",
            registry_versions=["registry-v1"],
            service_degradation_policy_version="degradation-v1",
            execution_parameter_version="execution-v1",
            content_hash=self._content_hash(payload),
        )
        self.context_snapshots[snapshot.context_snapshot_id] = snapshot
        self.current_context_snapshot_id = snapshot.context_snapshot_id
        return snapshot

    def submit_change(
        self,
        change_id: str,
        change_type: str,
        impact_level: str,
        proposal_ref: str,
        target_version_refs: dict[str, Any],
        effective_scope: str,
        rollback_plan_ref: str,
    ) -> GovernanceChange:
        now = utc_now()
        change = GovernanceChange(
            change_id=change_id,
            change_type=change_type,
            impact_level=impact_level,
            state="draft",
            proposal_ref=proposal_ref,
            target_version_refs=target_version_refs,
            effective_scope=effective_scope,
            rollback_plan_ref=rollback_plan_ref,
            created_at=now,
            updated_at=now,
        )
        self.changes[change_id] = change
        return change

    def triage(self, change_id: str) -> GovernanceChange:
        change = self.changes[change_id]
        triaged = replace(change, state="triage", updated_at=utc_now(), state_reason="impact_policy_applied")
        self.changes[change_id] = triaged
        return triaged

    def assess(self, change_id: str, validation_refs: list[str]) -> GovernanceChange:
        change = self.changes[change_id]
        missing = AUTO_VALIDATION_REQUIRED - set(validation_refs)
        if missing:
            assessed = replace(change, state="activation_failed", state_reason=f"missing_validation:{','.join(sorted(missing))}", updated_at=utc_now())
        elif change.impact_level in {"low", "medium"}:
            assessed = replace(
                change,
                state="approved",
                auto_validation_refs=list(validation_refs),
                comparison_analysis_ref=f"comparison-{change.change_id}",
                updated_at=utc_now(),
            )
        else:
            assessed = replace(
                change,
                state="owner_pending",
                auto_validation_refs=list(validation_refs),
                comparison_analysis_ref=f"comparison-{change.change_id}",
                updated_at=utc_now(),
            )
        self.changes[change_id] = assessed
        return assessed

    def owner_decide(self, change_id: str, approved: bool, approval_ref: str) -> GovernanceChange:
        change = self.changes[change_id]
        state = "approved" if approved else "rejected"
        decided = replace(
            change,
            state=state,
            owner_approval_ref=approval_ref,
            decided_at=utc_now(),
            updated_at=utc_now(),
            state_reason="owner_approved" if approved else "owner_rejected",
        )
        self.changes[change_id] = decided
        return decided

    def activate(self, change_id: str) -> GovernanceChange:
        change = self.changes[change_id]
        if change.state not in {"approved"}:
            failed = replace(change, state="activation_failed", state_reason="change_not_approved", updated_at=utc_now())
            self.changes[change_id] = failed
            return failed
        base = self.context_snapshots[self.current_context_snapshot_id] if self.current_context_snapshot_id else None
        if base is None:
            failed = replace(change, state="activation_failed", state_reason="missing_base_context_snapshot", updated_at=utc_now())
            self.changes[change_id] = failed
            return failed
        snapshot = self.create_context_snapshot(
            snapshot_version=f"{base.snapshot_version}+{change.change_id}",
            source_change_ref=change.change_id,
            prompt_versions=change.target_version_refs.get("prompt_versions", base.prompt_versions),
            skill_package_versions=change.target_version_refs.get("skill_package_versions", base.skill_package_versions),
            knowledge_item_versions=change.target_version_refs.get("knowledge_item_versions", base.knowledge_item_versions),
            memory_collection_versions=change.target_version_refs.get("memory_collection_versions", base.memory_collection_versions),
            default_context_versions=change.target_version_refs.get("default_context_versions", base.default_context_versions),
            agent_capability_versions=change.target_version_refs.get("agent_capability_versions", base.agent_capability_versions),
            effective_scope=change.effective_scope,
        )
        effective = replace(
            change,
            state="effective",
            context_snapshot_id=snapshot.context_snapshot_id,
            effective_at=utc_now(),
            updated_at=utc_now(),
            state_reason="new_task_or_attempt_only",
        )
        self.changes[change_id] = effective
        return effective
