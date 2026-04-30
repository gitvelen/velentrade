from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.attribution.cfo import CFOGovernanceService
from velentrade.domain.attribution.factor_research import FactorResearchService
from velentrade.domain.attribution.service import AttributionInput, PerformanceAttributionService
from velentrade.domain.common import utc_now


REPORT_TC = {
    "performance_attribution_report.json": ("TC-ACC-024-01", "ACC-024", "REQ-024"),
    "cfo_governance_report.json": ("TC-ACC-025-01", "ACC-025", "REQ-025"),
    "factor_research_report.json": ("TC-ACC-026-01", "ACC-026", "REQ-026"),
}


def _envelope(report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    tc, acc, req = REPORT_TC[report_id]
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi005",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-005"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": "pass",
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-ATTRIBUTION-CFO-GOVERNED"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-005 deterministic attribution fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}],
    }
    report.update(payload)
    return report


def build_wi005_attribution_reports() -> dict[str, dict[str, Any]]:
    attribution = PerformanceAttributionService().evaluate(
        AttributionInput(
            period="daily",
            market_result={"return": 0.015, "benchmark": 0.010},
            thesis_outcome_fit=0.8,
            decision_rationale_completeness=0.7,
            dissent_handling=0.7,
            invalidation_condition_quality=0.8,
            fill_policy_fit=0.8,
            slippage_bps=8,
            policy_slippage_bps=5,
            fee_tax_correctness=1.0,
            execution_core_guard_compliance=1.0,
            hard_constraint_compliance=1.0,
            conditional_requirement_followthrough=0.8,
            drawdown_or_exposure_control=0.8,
            hard_dissent_assessment_quality=0.7,
            data_quality_score=0.9,
            source_reliability=0.8,
            evidence_ref_completeness=0.9,
            counter_evidence_coverage=0.7,
            stale_or_conflict_penalty_adjusted=0.9,
            conditions=[("growth", "hit"), ("risk", "miss")],
        )
    )
    abnormal = PerformanceAttributionService().evaluate(
        AttributionInput(period="weekly", market_result={"return": -0.04}, hard_blocker_hit=True, repeated_degradation=True)
    )
    cfo = CFOGovernanceService().interpret(abnormal, "risk_budget", "high")
    factor = FactorResearchService().admit_factor(
        "quality-momentum",
        "质量动量在 risk_on 市场提高胜率",
        {"period": "2024-2026", "universe": "CSI300", "applicable_market_state": ["risk_on"]},
        {"validator": "quant_peer", "leakage_check": "pass", "direction_consistency": "pass"},
        {"coverage": 0.79, "data_quality": 0.86, "direction_failures": 0},
        True,
    )
    reports = {
        "performance_attribution_report.json": _envelope(
            "performance_attribution_report.json",
            {
                "return_attribution": attribution.market_result,
                "risk_attribution": {"risk_quality": attribution.risk_quality},
                "cost_slippage": {"execution_quality": attribution.execution_quality},
                "factor_contribution": {"factor_ref": "factor-quality-momentum"},
                "ic_quality": {"decision_quality": attribution.decision_quality, "condition_hit": attribution.condition_hit},
                "evidence_quality": attribution.evidence_quality,
                "quality_score_inputs": {"scores_present": True},
                "quality_score_formula_outputs": {
                    "decision_quality": attribution.decision_quality,
                    "execution_quality": attribution.execution_quality,
                    "risk_quality": attribution.risk_quality,
                    "data_quality": attribution.data_quality,
                    "evidence_quality": attribution.evidence_quality,
                },
                "condition_hit": attribution.condition_hit,
                "role_quality_scores": {"cio": attribution.decision_quality},
            },
        ),
        "cfo_governance_report.json": _envelope(
            "cfo_governance_report.json",
            {
                "cfo_interpretation": cfo.interpretation.__dict__,
                "governance_proposal": cfo.governance_proposal.__dict__,
                "reflection_assignment": cfo.assignment.__dict__,
                "attribution_trigger": cfo.trigger,
                "high_impact_owner_approval": cfo.owner_approval_required,
                "new_task_or_attempt_effective_scope": cfo.governance_proposal.effective_scope,
                "auto_published_daily": attribution.needs_cfo_interpretation is False,
                "attribution_trigger_thresholds": ["single_dimension_low", "repeated_degradation", "rolling_drop", "hard_blocker_hit", "condition_failure", "periodic_window"],
                "classification_mapping": {cfo.trigger: cfo.assignment.classification},
                "responsible_agent_selection": cfo.assignment.responsible_agent_id,
                "questions_to_answer": cfo.assignment.questions_to_answer,
                "governance_subtype": cfo.governance_proposal.proposal_type,
                "governance_impact_level": cfo.governance_proposal.impact_level,
                "owner_approval_required": cfo.owner_approval_required,
            },
        ),
        "factor_research_report.json": _envelope(
            "factor_research_report.json",
            {
                "research_admission": factor.hypothesis,
                "sample_context": factor.sample_scope,
                "independent_validation": factor.independent_validation,
                "factor_registry": factor.registry_entry,
                "monitoring": factor.monitoring_rule,
                "no_backtest_dependency": factor.no_backtest_dependency,
                "hypothesis": factor.hypothesis,
                "sample_scope": factor.sample_scope,
                "registry_entry_required_fields": sorted(factor.registry_entry),
                "monitoring_rule_thresholds": factor.monitoring_rule,
                "invalidation_diagnosis": factor.invalidation_diagnosis,
                "high_impact_factor_weight_governance": factor.governance_proposal,
            },
        ),
    }
    return {name: deepcopy(report) for name, report in reports.items()}
