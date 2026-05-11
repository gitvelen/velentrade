from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class OwnerExceptionPacket:
    candidate_id: str
    trigger_reason: str
    comparison_options: list[dict[str, Any]]
    recommended_decision: str
    risk_and_impact: dict[str, Any]
    evidence_refs: list[str]
    effective_scope: str
    timeout_policy: str


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    approval_type: str
    approval_object_ref: str
    trigger_reason: str
    comparison_options: list[dict[str, Any]]
    recommended_decision: str
    risk_and_impact: dict[str, Any]
    evidence_refs: list[str]
    effective_scope: str
    timeout_policy: str
    decision: str
    decided_at: str | None = None


class OwnerExceptionService:
    def create_packet(self, candidate_id: str, trigger_reason: str) -> OwnerExceptionPacket:
        return OwnerExceptionPacket(
            candidate_id=candidate_id,
            trigger_reason=trigger_reason,
            comparison_options=[
                {"option": "follow_optimizer", "target_weight": 0.10, "risk": "baseline"},
                {"option": "cio_deviation", "target_weight": 0.16, "risk": "higher_single_name_exposure"},
            ],
            recommended_decision="approve_exception_only_if_risk_accepted",
            risk_and_impact={"single_name_deviation_pp": 6.0, "portfolio_active_deviation": 0.03, "scope": "current_attempt_only"},
            evidence_refs=["decision-guard-1", "cio-memo-1", "risk-review-1"],
            effective_scope="current_attempt_only",
            timeout_policy="timeout_means_no_execution",
        )

    def submit_for_approval(self, packet: OwnerExceptionPacket) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=new_id("approval"),
            approval_type="owner_exception",
            approval_object_ref=packet.candidate_id,
            trigger_reason=packet.trigger_reason,
            comparison_options=packet.comparison_options,
            recommended_decision=packet.recommended_decision,
            risk_and_impact=packet.risk_and_impact,
            evidence_refs=packet.evidence_refs,
            effective_scope=packet.effective_scope,
            timeout_policy=packet.timeout_policy,
            decision="pending",
        )

    def apply_timeout(self, approval: ApprovalRecord) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=approval.approval_id,
            approval_type=approval.approval_type,
            approval_object_ref=approval.approval_object_ref,
            trigger_reason=approval.trigger_reason,
            comparison_options=approval.comparison_options,
            recommended_decision=approval.recommended_decision,
            risk_and_impact=approval.risk_and_impact,
            evidence_refs=approval.evidence_refs,
            effective_scope=approval.effective_scope,
            timeout_policy=approval.timeout_policy,
            decision="expired",
            decided_at=None,
        )

    def timeout_disposition(self, approval: ApprovalRecord) -> str:
        if approval.decision != "expired":
            return "await_owner"
        if approval.approval_type == "request_brief_confirmation":
            return "request_brief_expired_no_workflow"
        if approval.approval_type in {"risk_conditional_pass", "s6_investment_exception"}:
            return "s6_blocked_no_execution"
        if approval.approval_type == "cio_major_deviation":
            return "reopen_s4_or_close_no_execution"
        if approval.approval_type in {"high_impact_governance", "prompt_knowledge_promotion", "finance_risk_budget"}:
            return "governance_expired_no_effect"
        if approval.approval_type == "manual_todo":
            return "manual_todo_expired_only"
        return "no_execution"
