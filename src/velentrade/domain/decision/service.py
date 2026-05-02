from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from velentrade.domain.common import new_id, utc_now


@dataclass(frozen=True)
class DecisionPacket:
    packet_id: str
    workflow_id: str
    attempt_no: int
    context_snapshot_id: str
    decision_question: str
    input_artifact_refs: list[str]
    analyst_stance_summary: dict[str, Any]
    consensus_score: float
    action_conviction: float
    hard_dissent_state: str
    data_quality_summary: dict[str, Any]
    market_state_ref: str
    valuation_refs: list[str]
    optimizer_result_ref: str
    portfolio_context_ref: str
    risk_constraint_refs: list[str]
    execution_feasibility: dict[str, Any]
    reflection_hit_refs: list[str]
    allowed_cio_actions: list[str]
    evidence_refs: list[str]
    packet_hash: str


@dataclass(frozen=True)
class CIODecisionMemo:
    decision: str
    decision_packet_ref: str
    target_symbol: str
    target_weight: float
    price_range: dict[str, Any]
    urgency: str
    decision_rationale: str
    deviation_reason: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class DecisionGuardResult:
    guard_id: str
    workflow_id: str
    attempt_no: int
    decision_packet_ref: str
    cio_decision_memo_ref: str | None
    input_completeness: dict[str, bool]
    single_name_deviation_pp: float
    portfolio_active_deviation: float
    major_deviation: bool
    low_action_conviction: bool
    retained_hard_dissent: bool
    data_quality_blockers: list[str]
    optimizer_available: bool
    owner_exception_candidate_ref: str | None
    reopen_recommendation_ref: str | None
    reason_codes: list[str]
    created_at: str


@dataclass(frozen=True)
class DecisionExceptionCandidate:
    candidate_id: str
    workflow_id: str
    attempt_no: int
    trigger_reason: str
    decision_packet_ref: str
    cio_decision_memo_ref: str
    deviation_summary: dict[str, Any]
    comparison_options: list[dict[str, Any]]
    recommended_disposition: str
    risk_and_impact: dict[str, Any]
    evidence_refs: list[str]
    effective_scope: str
    owner_approval_ref: str | None = None


@dataclass(frozen=True)
class ReopenRecommendation:
    recommendation_id: str
    workflow_id: str
    attempt_no: int
    from_stage: str
    target_stage: str
    reason_code: str
    invalidated_artifact_candidates: list[str]
    preserved_artifact_candidates: list[str]
    evidence_refs: list[str]
    created_at: str


class DecisionService:
    def fixture_inputs(self) -> dict[str, Any]:
        return {
            "workflow_id": "wf-decision",
            "attempt_no": 1,
            "context_snapshot_id": "ctx-v1",
            "decision_question": "600000.SH 是否进入买入决策？",
            "input_artifact_refs": ["ic-context-1", "chair-1", "memo-macro", "memo-fundamental", "memo-quant", "memo-event", "debate-1", "optimizer-1"],
            "analyst_stance_summary": {"macro": 2, "fundamental": 2, "quant": 2, "event": -1},
            "consensus_score": 0.744,
            "action_conviction": 0.69,
            "hard_dissent_state": "retained",
            "data_quality_summary": {"decision_core_status": "pass", "execution_core_status": "pass", "blockers": []},
            "market_state_ref": "market-risk-on",
            "valuation_refs": ["valuation-1"],
            "optimizer_result_ref": "optimizer-1",
            "portfolio_context_ref": "portfolio-1",
            "risk_constraint_refs": ["risk-budget-1"],
            "execution_feasibility": {"execution_core_status": "pass"},
            "reflection_hit_refs": ["reflection-1"],
            "evidence_refs": ["memo-macro", "optimizer-1", "risk-budget-1"],
        }

    def assemble_packet(self, inputs: dict[str, Any]) -> DecisionPacket:
        required = ["workflow_id", "context_snapshot_id", "input_artifact_refs", "optimizer_result_ref", "risk_constraint_refs", "evidence_refs"]
        missing = [field for field in required if not inputs.get(field)]
        if missing:
            raise ValueError(f"missing_required_artifact:{','.join(missing)}")
        payload = repr(sorted(inputs.items())).encode("utf-8")
        return DecisionPacket(
            packet_id=new_id("decision-packet"),
            workflow_id=inputs["workflow_id"],
            attempt_no=inputs.get("attempt_no", 1),
            context_snapshot_id=inputs["context_snapshot_id"],
            decision_question=inputs["decision_question"],
            input_artifact_refs=list(inputs["input_artifact_refs"]),
            analyst_stance_summary=dict(inputs["analyst_stance_summary"]),
            consensus_score=inputs["consensus_score"],
            action_conviction=inputs["action_conviction"],
            hard_dissent_state=inputs["hard_dissent_state"],
            data_quality_summary=dict(inputs["data_quality_summary"]),
            market_state_ref=inputs["market_state_ref"],
            valuation_refs=list(inputs["valuation_refs"]),
            optimizer_result_ref=inputs["optimizer_result_ref"],
            portfolio_context_ref=inputs["portfolio_context_ref"],
            risk_constraint_refs=list(inputs["risk_constraint_refs"]),
            execution_feasibility=dict(inputs["execution_feasibility"]),
            reflection_hit_refs=list(inputs["reflection_hit_refs"]),
            allowed_cio_actions=["buy", "sell", "hold", "observe", "no_action", "reopen"],
            evidence_refs=list(inputs["evidence_refs"]),
            packet_hash=sha256(payload).hexdigest(),
        )

    def validate_cio_memo(self, packet: DecisionPacket, memo: CIODecisionMemo, optimizer_target_weights: dict[str, float]) -> DecisionGuardResult:
        if memo.decision_packet_ref != packet.packet_id:
            raise ValueError("decision_packet_ref_mismatch")
        if memo.decision not in packet.allowed_cio_actions:
            raise ValueError("cio_action_not_allowed")
        optimizer_weight = optimizer_target_weights.get(memo.target_symbol)
        optimizer_available = optimizer_weight is not None
        single_pp = round(abs(memo.target_weight - (optimizer_weight or 0)) * 100, 3) if optimizer_available else 0.0
        portfolio_active = (
            round(
                0.5
                * sum(
                    abs((memo.target_weight if symbol == memo.target_symbol else 0.0) - weight)
                    for symbol, weight in optimizer_target_weights.items()
                ),
                3,
            )
            if optimizer_available
            else 0.0
        )
        major = optimizer_available and (single_pp >= 5.0 or portfolio_active >= 0.20)
        low_action = packet.action_conviction < 0.65
        reason_codes: list[str] = []
        if low_action:
            reason_codes.append("low_action_conviction_no_execution")
        if major:
            reason_codes.append("decision_major_deviation_requires_exception_or_reopen")
        if major and not memo.deviation_reason:
            reason_codes.append("missing_deviation_rationale")
        if packet.hard_dissent_state == "retained":
            reason_codes.append("retained_hard_dissent_risk_review")
        candidate_ref = new_id("decision-exception") if major and memo.deviation_reason and not low_action else None
        reopen_ref = new_id("reopen-recommendation") if low_action or (major and not memo.deviation_reason) else None
        return DecisionGuardResult(
            guard_id=new_id("decision-guard"),
            workflow_id=packet.workflow_id,
            attempt_no=packet.attempt_no,
            decision_packet_ref=packet.packet_id,
            cio_decision_memo_ref=new_id("cio-memo"),
            input_completeness={field: True for field in ["ic_context", "chair_brief", "memos", "debate", "optimizer", "data_readiness"]},
            single_name_deviation_pp=single_pp,
            portfolio_active_deviation=portfolio_active,
            major_deviation=major,
            low_action_conviction=low_action,
            retained_hard_dissent=packet.hard_dissent_state == "retained",
            data_quality_blockers=packet.data_quality_summary.get("blockers", []),
            optimizer_available=optimizer_available,
            owner_exception_candidate_ref=candidate_ref,
            reopen_recommendation_ref=reopen_ref,
            reason_codes=reason_codes,
            created_at=utc_now(),
        )

    def forbidden_service_authority_check(self) -> dict[str, bool]:
        return {
            "service_can_write_cio_decision": False,
            "service_can_risk_verdict": False,
            "service_can_owner_approve": False,
            "service_can_transition_workflow": False,
            "service_can_release_paper_execution": False,
            "service_can_approve": False,
        }
