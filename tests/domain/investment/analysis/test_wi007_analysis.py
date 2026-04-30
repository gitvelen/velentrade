from velentrade.domain.investment.analysis.consensus import ConsensusCalculator
from velentrade.domain.investment.analysis.memo import AnalystMemoFactory, AnalystMemoValidator
from velentrade.domain.investment.analysis.wi007_reports import build_wi007_analysis_reports


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
    assert result.execution_authorized is True

    low_action = calculator.calculate(AnalystMemoFactory().fixture_memos(direction_scores=[1, 1, 1, 1], confidences=[0.4, 0.4, 0.4, 0.4]))
    assert low_action.consensus_score >= 0.8
    assert low_action.action_conviction < 0.65
    assert low_action.execution_authorized is False
    assert low_action.reason_code == "low_action_conviction_no_execution"


def test_wi007_analysis_reports_have_contract_payloads():
    reports = build_wi007_analysis_reports()

    assert set(reports) == {"analyst_memo_report.json", "consensus_action_report.json"}
    for report in reports.values():
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-007"]
        assert report["failures"] == []
    assert reports["consensus_action_report.json"]["no_execution_when_low_action_conviction"] is True
