from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id


ROLE_PAYLOAD_FIELDS = {
    "macro": {"market_state", "policy_transmission", "liquidity", "credit_cycle", "style_tailwind", "macro_risks"},
    "fundamental": {"business_model", "moat", "financial_quality", "earnings_scenario", "valuation_method", "fair_value", "accounting_red_flags"},
    "quant": {"signal_hypothesis", "trend", "factor_exposure", "sample_context", "stability", "regime_fit", "crowding_risk"},
    "event": {"event_type", "timeline", "source_reliability", "verification_status", "catalyst_strength", "event_window", "reversal_risk"},
}

ROLE_SKILLS = {
    "macro": "macro-regime-policy-v1",
    "fundamental": "fundamental-valuation-v1",
    "quant": "quant-factor-signal-v1",
    "event": "event-catalyst-v1",
}


@dataclass(frozen=True)
class AnalystMemo:
    memo_id: str
    workflow_id: str
    attempt_no: int
    analyst_id: str
    role: str
    context_snapshot_id: str
    decision_question: str
    direction_score: int
    confidence: float
    evidence_quality: float
    hard_dissent: bool
    hard_dissent_reason: str
    thesis: str
    supporting_evidence_refs: list[str]
    counter_evidence_refs: list[str]
    key_risks: list[str]
    applicable_conditions: list[str]
    invalidation_conditions: list[str]
    suggested_action_implication: str
    role_payload: dict[str, Any]
    skill_package_ref: str
    rubric_ref: str
    profile_version: str


class AnalystMemoFactory:
    def fixture_memos(
        self,
        direction_scores: list[int] | None = None,
        confidences: list[float] | None = None,
        evidence_qualities: list[float] | None = None,
    ) -> list[AnalystMemo]:
        scores = direction_scores or [4, 3, 3, -4]
        confidence_values = confidences or [0.82, 0.78, 0.74, 0.76]
        evidence_values = evidence_qualities or [0.85, 0.80, 0.78, 0.82]
        roles = ["macro", "fundamental", "quant", "event"]
        majority = _majority_sign(scores)
        memos = []
        for index, role in enumerate(roles):
            score = scores[index]
            hard_dissent = majority != 0 and _sign(score) == -majority and (abs(score) >= 4 or confidence_values[index] >= 0.7)
            memos.append(
                AnalystMemo(
                    memo_id=new_id("memo"),
                    workflow_id="wf-analysis",
                    attempt_no=1,
                    analyst_id=f"{role}_analyst",
                    role=role,
                    context_snapshot_id="ctx-v1",
                    decision_question="是否进入下一步 A 股 IC 决策？",
                    direction_score=score,
                    confidence=confidence_values[index],
                    evidence_quality=evidence_values[index],
                    hard_dissent=hard_dissent,
                    hard_dissent_reason="opposes majority with strong evidence" if hard_dissent else "",
                    thesis=f"{role} thesis",
                    supporting_evidence_refs=[f"{role}-support-1"],
                    counter_evidence_refs=[f"{role}-counter-1"],
                    key_risks=[f"{role}-risk"],
                    applicable_conditions=[f"{role}-condition"],
                    invalidation_conditions=[f"{role}-invalidation"],
                    suggested_action_implication="role_view_only_no_order",
                    role_payload=_role_payload(role),
                    skill_package_ref=ROLE_SKILLS[role],
                    rubric_ref=f"{role}-rubric-v1",
                    profile_version=f"{role}-profile-v1",
                )
            )
        return memos


class AnalystMemoValidator:
    def validate_all(self, memos: list[AnalystMemo]) -> dict[str, Any]:
        role_payload_pass = {
            memo.role: ROLE_PAYLOAD_FIELDS[memo.role].issubset(set(memo.role_payload))
            for memo in memos
        }
        return {
            "schema_pass": all(_schema_pass(memo) for memo in memos),
            "role_payload_pass": role_payload_pass,
            "profile_independence_pass": len({memo.profile_version for memo in memos}) == 4 and len({memo.skill_package_ref for memo in memos}) == 4,
            "skill_package_refs": {memo.role: memo.skill_package_ref for memo in memos},
            "rubric_refs": {memo.role: memo.rubric_ref for memo in memos},
            "score_range_pass": all(-5 <= memo.direction_score <= 5 for memo in memos),
            "evidence_quality_range_pass": all(0 <= memo.evidence_quality <= 1 for memo in memos),
            "hard_dissent_field": {memo.role: memo.hard_dissent for memo in memos},
            "evidence_refs": {memo.role: memo.supporting_evidence_refs for memo in memos},
            "counter_evidence": {memo.role: memo.counter_evidence_refs for memo in memos},
        }


def _schema_pass(memo: AnalystMemo) -> bool:
    return (
        memo.role in ROLE_PAYLOAD_FIELDS
        and -5 <= memo.direction_score <= 5
        and 0 <= memo.confidence <= 1
        and 0 <= memo.evidence_quality <= 1
        and bool(memo.supporting_evidence_refs)
        and bool(memo.counter_evidence_refs)
        and ROLE_PAYLOAD_FIELDS[memo.role].issubset(set(memo.role_payload))
    )


def _role_payload(role: str) -> dict[str, Any]:
    return {field: f"{role}:{field}:fixture" for field in sorted(ROLE_PAYLOAD_FIELDS[role])}


def _sign(score: int) -> int:
    if score > 0:
        return 1
    if score < 0:
        return -1
    return 0


def _majority_sign(scores: list[int]) -> int:
    signs = [_sign(score) for score in scores if _sign(score) != 0]
    if not signs:
        return 0
    positive = signs.count(1)
    negative = signs.count(-1)
    if positive == negative:
        return 0
    return 1 if positive > negative else -1
