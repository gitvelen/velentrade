from velentrade.domain.investment.analysis.consensus import ConsensusCalculator
from velentrade.domain.investment.analysis.memo import ROLE_PAYLOAD_FIELDS, AnalystMemoFactory, AnalystMemoValidator
from velentrade.domain.investment.analysis.wi007_reports import _envelope, build_wi007_analysis_reports


EXPECTED_ROLE_PAYLOAD_FIELDS = {
    "macro": {
        "engine_market_state",
        "analyst_market_state_view",
        "market_state_conflict",
        "policy_stance",
        "liquidity_condition",
        "credit_cycle",
        "industry_policy_alignment",
        "style_bias",
        "macro_tailwinds",
        "macro_headwinds",
        "transmission_path",
        "macro_risk_triggers",
    },
    "fundamental": {
        "business_model_quality_score",
        "moat_assessment",
        "financial_quality",
        "earnings_scenarios",
        "valuation_methods_used",
        "fair_value_range",
        "valuation_percentile",
        "safety_margin",
        "sensitivity_factors",
        "accounting_red_flags",
        "key_kpi_watchlist",
        "fundamental_catalysts",
        "valuation_conclusion",
    },
    "quant": {
        "signal_hypothesis",
        "trend_state",
        "momentum_score",
        "volume_price_confirmation",
        "factor_exposures",
        "factor_signal_scores",
        "sample_context",
        "signal_stability_score",
        "regime_fit",
        "timing_implication",
        "overheat_or_crowding_risk",
        "invalidating_price_or_signal_levels",
    },
    "event": {
        "event_type",
        "event_timeline",
        "source_reliability",
        "verification_status",
        "catalyst_strength_score",
        "time_window_assessment",
        "affected_fundamental_assumptions",
        "sentiment_and_fund_flow",
        "historical_analogues",
        "reversal_risk",
        "supporting_evidence_only",
    },
}


def test_four_analyst_memos_have_independent_payloads_and_valid_ranges():
    memos = AnalystMemoFactory().fixture_memos()
    validation = AnalystMemoValidator().validate_all(memos)

    assert validation["schema_pass"] is True
    assert validation["role_payload_pass"] == {"macro": True, "fundamental": True, "quant": True, "event": True}
    assert validation["profile_independence_pass"] is True
    assert validation["score_range_pass"] is True
    assert validation["evidence_quality_range_pass"] is True
    assert {memo.role for memo in memos} == {"macro", "fundamental", "quant", "event"}
    assert len({tuple(sorted(memo.role_payload)) for memo in memos}) == 4


def test_analyst_memo_matches_spec_shell_and_role_payload_contracts():
    memos = AnalystMemoFactory().fixture_memos()

    assert ROLE_PAYLOAD_FIELDS == EXPECTED_ROLE_PAYLOAD_FIELDS
    for memo in memos:
        assert isinstance(memo.data_quality_notes, str)
        assert isinstance(memo.needs_reopen_or_escalation, bool)
        assert isinstance(memo.collaboration_command_refs, list)
        assert set(memo.role_payload) == EXPECTED_ROLE_PAYLOAD_FIELDS[memo.role]


def test_consensus_and_action_conviction_follow_formula_and_thresholds():
    calculator = ConsensusCalculator()
    memos = AnalystMemoFactory().fixture_memos(
        direction_scores=[2, 2, 2, -1],
        confidences=[1.0, 1.0, 1.0, 1.0],
        evidence_qualities=[1.0, 1.0, 1.0, 1.0],
    )
    result = calculator.calculate(memos)

    assert result.dominant_direction_share == 0.75
    assert result.hard_dissent_present is True
    assert result.execution_authorized is False
    assert result.reason_code == "hard_dissent_requires_debate"

    low_action = calculator.calculate(AnalystMemoFactory().fixture_memos(direction_scores=[1, 1, 1, 1], confidences=[0.4, 0.4, 0.4, 0.4]))
    assert low_action.consensus_score >= 0.8
    assert low_action.action_conviction < 0.65
    assert low_action.execution_authorized is False
    assert low_action.reason_code == "low_action_conviction_no_execution"


def test_consensus_counts_neutral_direction_as_its_own_direction():
    result = ConsensusCalculator().calculate(
        AnalystMemoFactory().fixture_memos(
            direction_scores=[0, 0, 1, -1],
            confidences=[1.0, 1.0, 1.0, 1.0],
            evidence_qualities=[1.0, 1.0, 1.0, 1.0],
        )
    )

    assert result.dominant_direction_share == 0.5


def test_consensus_requires_all_four_official_analyst_roles():
    calculator = ConsensusCalculator()
    memos = AnalystMemoFactory().fixture_memos()

    try:
        calculator.calculate(memos[:3])
    except ValueError as exc:
        assert str(exc) == "requires_four_official_analyst_memos"
    else:
        raise AssertionError("expected requires_four_official_analyst_memos")

    duplicate_macro = [memos[0], memos[0], memos[2], memos[3]]
    try:
        calculator.calculate(duplicate_macro)
    except ValueError as exc:
        assert str(exc) == "requires_four_official_analyst_memos"
    else:
        raise AssertionError("expected requires_four_official_analyst_memos")


def test_wi007_analysis_reports_have_contract_payloads():
    reports = build_wi007_analysis_reports()

    assert set(reports) == {"analyst_memo_report.json", "consensus_action_report.json"}
    for report in reports.values():
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-007"]
        assert report["failures"] == []
    assert reports["consensus_action_report.json"]["no_execution_when_low_action_conviction"] is True
    assert reports["consensus_action_report.json"]["four_official_roles_required"] is True


def test_analysis_report_fails_when_guard_or_failure_fails():
    report = _envelope(
        "consensus_action_report.json",
        {"probe": "negative"},
        guard_results=[
            {
                "guard": "hard_dissent_requires_debate",
                "input_ref": "consensus-result",
                "expected": "execution_authorized_false",
                "actual": "execution_authorized_true",
                "result": "fail",
            }
        ],
        failures=[{"code": "hard_dissent_authorized_execution", "message": "hard dissent was marked execution-authorized"}],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "hard_dissent_authorized_execution"
