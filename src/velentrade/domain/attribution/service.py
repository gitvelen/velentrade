from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class AttributionInput:
    period: str
    market_result: dict[str, Any]
    thesis_outcome_fit: float | None = None
    decision_rationale_completeness: float | None = None
    dissent_handling: float | None = None
    invalidation_condition_quality: float | None = None
    fill_policy_fit: float | None = None
    slippage_bps: float | None = None
    policy_slippage_bps: float | None = None
    fee_tax_correctness: float | None = None
    execution_core_guard_compliance: float | None = None
    hard_constraint_compliance: float | None = None
    conditional_requirement_followthrough: float | None = None
    drawdown_or_exposure_control: float | None = None
    hard_dissent_assessment_quality: float | None = None
    data_quality_score: float | None = None
    source_reliability: float | None = None
    evidence_ref_completeness: float | None = None
    counter_evidence_coverage: float | None = None
    stale_or_conflict_penalty_adjusted: float | None = None
    conditions: list[tuple[str, str]] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    repeated_degradation: bool = False
    rolling_drop: float = 0.0
    hard_blocker_hit: bool = False
    periodic_window: bool = False


@dataclass(frozen=True)
class AttributionReport:
    report_id: str
    period: str
    market_result: dict[str, Any]
    decision_quality: float | None
    execution_quality: float | None
    risk_quality: float | None
    data_quality: float | None
    evidence_quality: float | None
    condition_hit: dict[str, Any]
    improvement_items: list[str]
    needs_cfo_interpretation: bool
    trigger_candidates: list[str]


class PerformanceAttributionService:
    def evaluate(self, inputs: AttributionInput) -> AttributionReport:
        missing = set(inputs.missing_inputs)
        improvement_items = [f"missing_input:{name}" for name in inputs.missing_inputs]
        decision_quality = None if "CIODecisionMemo" in missing else _weighted(
            [
                (inputs.thesis_outcome_fit, 0.35),
                (inputs.decision_rationale_completeness, 0.25),
                (inputs.dissent_handling, 0.20),
                (inputs.invalidation_condition_quality, 0.20),
            ]
        )
        execution_quality = None if "PaperExecutionReceipt" in missing else _weighted(
            [
                (inputs.fill_policy_fit, 0.35),
                (_slippage_score(inputs.slippage_bps, inputs.policy_slippage_bps), 0.25),
                (inputs.fee_tax_correctness, 0.20),
                (inputs.execution_core_guard_compliance, 0.20),
            ]
        )
        risk_quality = None if "RiskReviewReport" in missing else _weighted(
            [
                (inputs.hard_constraint_compliance, 0.35),
                (inputs.conditional_requirement_followthrough, 0.25),
                (inputs.drawdown_or_exposure_control, 0.20),
                (inputs.hard_dissent_assessment_quality, 0.20),
            ]
        )
        evidence_quality = _weighted(
            [
                (inputs.source_reliability, 0.30),
                (inputs.evidence_ref_completeness, 0.25),
                (inputs.counter_evidence_coverage, 0.25),
                (inputs.stale_or_conflict_penalty_adjusted, 0.20),
            ]
        )
        condition_hit = _condition_hit(inputs.conditions)
        trigger_candidates = _trigger_candidates(
            [decision_quality, execution_quality, risk_quality, inputs.data_quality_score, evidence_quality],
            inputs,
            condition_hit,
        )
        return AttributionReport(
            report_id=new_id("attribution"),
            period=inputs.period,
            market_result=inputs.market_result,
            decision_quality=decision_quality,
            execution_quality=execution_quality,
            risk_quality=risk_quality,
            data_quality=inputs.data_quality_score,
            evidence_quality=evidence_quality,
            condition_hit=condition_hit,
            improvement_items=improvement_items,
            needs_cfo_interpretation=bool(trigger_candidates),
            trigger_candidates=trigger_candidates,
        )


def _weighted(items: list[tuple[float | None, float]]) -> float | None:
    if any(value is None for value, _ in items):
        return None
    return round(sum(float(value) * weight for value, weight in items), 3)


def _slippage_score(actual: float | None, policy: float | None) -> float | None:
    if actual is None or policy is None:
        return None
    return max(0.0, 1 - abs(actual - policy) / 20)


def _condition_hit(conditions: list[tuple[str, str]]) -> dict[str, Any]:
    observable = [status for _, status in conditions if status != "not_observable"]
    hits = sum(1 for status in observable if status == "hit")
    return {
        "conditions": [{"condition": name, "status": status} for name, status in conditions],
        "score": None if not observable else round(hits / len(observable), 3),
    }


def _trigger_candidates(scores: list[float | None], inputs: AttributionInput, condition_hit: dict[str, Any]) -> list[str]:
    triggers: list[str] = []
    if inputs.hard_blocker_hit:
        triggers.append("hard_blocker_hit")
    if any(score is not None and score < 0.60 for score in scores):
        triggers.append("single_dimension_low")
    if inputs.rolling_drop >= 0.25:
        triggers.append("rolling_drop")
    if inputs.repeated_degradation:
        triggers.append("repeated_degradation")
    if any(status == "hit" for _, status in inputs.conditions) or condition_hit.get("score") == 0.0:
        triggers.append("condition_failure")
    if inputs.periodic_window or inputs.period in {"weekly", "monthly", "quarterly"}:
        triggers.append("periodic_window")
    return triggers
