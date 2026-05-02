from velentrade.domain.attribution.cfo import CFOGovernanceService
from velentrade.domain.attribution.factor_research import FactorResearchService
from velentrade.domain.attribution.service import AttributionInput, PerformanceAttributionService
from velentrade.domain.attribution.wi005_reports import build_wi005_attribution_reports


def test_performance_attribution_scores_missing_inputs_and_cfo_triggers():
    service = PerformanceAttributionService()
    report = service.evaluate(
        AttributionInput(
            period="2026-04-30",
            market_result={"return": -0.02},
            thesis_outcome_fit=0.5,
            decision_rationale_completeness=0.6,
            dissent_handling=0.0,
            invalidation_condition_quality=0.5,
            fill_policy_fit=0.8,
            slippage_bps=18,
            policy_slippage_bps=5,
            fee_tax_correctness=1.0,
            execution_core_guard_compliance=1.0,
            missing_inputs=["RiskReviewReport"],
            source_reliability=0.9,
            evidence_ref_completeness=0.8,
            counter_evidence_coverage=0.4,
            stale_or_conflict_penalty_adjusted=0.8,
            conditions=[("valuation rerate", "miss"), ("policy shock", "not_observable")],
        )
    )

    assert report.decision_quality == 0.425
    assert report.execution_quality == 0.767
    assert report.risk_quality is None
    assert "missing_input:RiskReviewReport" in report.improvement_items
    assert report.needs_cfo_interpretation is True
    assert report.condition_hit["score"] == 0.0


def test_normal_daily_attribution_auto_publishes_without_cfo_trigger():
    report = PerformanceAttributionService().evaluate(
        AttributionInput(
            period="daily",
            market_result={"return": 0.012, "benchmark": 0.01},
            thesis_outcome_fit=0.85,
            decision_rationale_completeness=0.8,
            dissent_handling=0.8,
            invalidation_condition_quality=0.8,
            fill_policy_fit=0.85,
            slippage_bps=5,
            policy_slippage_bps=5,
            fee_tax_correctness=1.0,
            execution_core_guard_compliance=1.0,
            hard_constraint_compliance=0.9,
            conditional_requirement_followthrough=0.9,
            drawdown_or_exposure_control=0.85,
            hard_dissent_assessment_quality=0.8,
            data_quality_score=0.95,
            source_reliability=0.9,
            evidence_ref_completeness=0.9,
            counter_evidence_coverage=0.85,
            stale_or_conflict_penalty_adjusted=0.95,
            conditions=[("growth", "hit"), ("risk", "hit")],
        )
    )

    assert report.needs_cfo_interpretation is False
    assert report.trigger_candidates == []


def test_cfo_maps_trigger_priority_to_reflection_and_high_impact_governance():
    attribution = PerformanceAttributionService().evaluate(
        AttributionInput(
            period="weekly",
            market_result={"return": -0.03},
            decision_rationale_completeness=0.2,
            dissent_handling=0.0,
            invalidation_condition_quality=0.4,
            hard_blocker_hit=True,
            repeated_degradation=True,
            rolling_drop=0.30,
            conditions=[("invalidation", "hit")],
        )
    )

    service = CFOGovernanceService()
    result = service.interpret(attribution, governance_subtype="risk_budget", impact_level="high")

    assert result.trigger == "hard_blocker_hit"
    assert result.interpretation.finance_context_used == "authorized_or_redacted"
    assert result.assignment.classification == "data_quality_problem"
    assert result.assignment.responsible_agent_id == "devops_engineer"
    assert len(result.assignment.questions_to_answer) >= 3
    assert result.governance_proposal.proposal_type == "risk_budget"
    assert result.governance_change.state == "owner_pending"
    assert result.owner_approval_required is True


def test_factor_research_governance_does_not_require_backtest_and_monitors_drift():
    service = FactorResearchService()
    result = service.admit_factor(
        factor_id="low-vol",
        hypothesis="低波动因子在震荡市降低组合回撤",
        sample_scope={"period": "2024-2026", "universe": "CSI300", "applicable_market_state": ["range_bound"]},
        independent_validation={"validator": "quant_peer", "leakage_check": "pass", "direction_consistency": "pass"},
        monitoring={"coverage": 0.75, "data_quality": 0.9, "direction_failures": 1},
        affects_default_weight=True,
    )

    assert result.registry_entry["status"] == "validated"
    assert result.no_backtest_dependency is True
    assert result.monitoring_alerts == ["coverage_below_threshold"]
    assert result.governance_proposal["impact_level"] == "high"


def test_wi005_attribution_reports_have_contract_payloads():
    reports = build_wi005_attribution_reports()

    assert set(reports) == {
        "performance_attribution_report.json",
        "cfo_governance_report.json",
        "factor_research_report.json",
    }
    for report in reports.values():
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-005"]
        assert report["failures"] == []
    assert reports["cfo_governance_report.json"]["auto_published_daily"] is True
