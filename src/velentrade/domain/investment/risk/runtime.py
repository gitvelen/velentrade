from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class RiskReviewReport:
    review_result: str
    repairability: str | None
    risk_summary: str
    hard_blockers: list[str]
    conditional_requirements: list[str]
    data_quality_assessment: str
    portfolio_risk_assessment: str
    liquidity_execution_assessment: str
    cio_deviation_assessment: str
    hard_dissent_assessment: str
    owner_exception_required: bool
    reopen_target_if_any: str | None
    reason_codes: list[str]
    evidence_refs: list[str]


class RiskReviewRuntime:
    def review(self, decision_ref: str, blockers: list[str], conditional_requirements: list[str], retained_hard_dissent: bool) -> RiskReviewReport:
        if blockers:
            return RiskReviewReport(
                review_result="rejected",
                repairability="repairable" if "risk_budget_breach" in blockers else "unrepairable",
                risk_summary="hard blocker present",
                hard_blockers=blockers,
                conditional_requirements=[],
                data_quality_assessment="pass",
                portfolio_risk_assessment="blocked",
                liquidity_execution_assessment="not_released",
                cio_deviation_assessment="requires_rework",
                hard_dissent_assessment="must_be_explicitly_assessed" if retained_hard_dissent else "none",
                owner_exception_required=False,
                reopen_target_if_any="S4" if "risk_budget_breach" in blockers else None,
                reason_codes=["risk_rejected_no_override"],
                evidence_refs=[decision_ref],
            )
        if conditional_requirements or retained_hard_dissent:
            return RiskReviewReport(
                review_result="conditional_pass",
                repairability=None,
                risk_summary="owner exception required",
                hard_blockers=[],
                conditional_requirements=conditional_requirements or ["retained_hard_dissent_owner_awareness"],
                data_quality_assessment="pass",
                portfolio_risk_assessment="conditional",
                liquidity_execution_assessment="conditional",
                cio_deviation_assessment="owner_exception_required",
                hard_dissent_assessment="retained_hard_dissent" if retained_hard_dissent else "none",
                owner_exception_required=True,
                reopen_target_if_any=None,
                reason_codes=["conditional_pass_owner_exception"],
                evidence_refs=[decision_ref],
            )
        return RiskReviewReport(
            review_result="approved",
            repairability=None,
            risk_summary="risk accepted",
            hard_blockers=[],
            conditional_requirements=[],
            data_quality_assessment="pass",
            portfolio_risk_assessment="pass",
            liquidity_execution_assessment="pass",
            cio_deviation_assessment="within_guard",
            hard_dissent_assessment="none",
            owner_exception_required=False,
            reopen_target_if_any=None,
            reason_codes=[],
            evidence_refs=[decision_ref],
        )

    def bypass_attempt(self, report: RiskReviewReport, actor: str) -> str:
        if report.review_result == "rejected":
            return "denied:risk_rejected_no_override"
        return f"allowed:{actor}"

    def reopen_or_close(self, report: RiskReviewReport) -> dict[str, Any]:
        if report.review_result != "rejected":
            return {"action": "none"}
        if report.repairability == "repairable":
            return {"action": "reopen", "target": report.reopen_target_if_any or "S4", "reopen_event_ref": new_id("reopen")}
        return {"action": "close_attempt", "target": None}
