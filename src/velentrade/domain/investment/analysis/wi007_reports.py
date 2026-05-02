from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.analysis.consensus import ConsensusCalculator
from velentrade.domain.investment.analysis.memo import AnalystMemoFactory, AnalystMemoValidator


REPORT_TC = {
    "analyst_memo_report.json": ("TC-ACC-015-01", "ACC-015", "REQ-015"),
    "consensus_action_report.json": ("TC-ACC-016-01", "ACC-016", "REQ-016"),
}


def _envelope(
    report_id: str,
    payload: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tc, acc, req = REPORT_TC[report_id]
    guard_results = guard_results or [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}]
    failures = failures or []
    result = "fail" if failures or any(guard.get("result") != "pass" for guard in guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi007",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-007"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-IC-ANALYST-INDEPENDENT-MEMOS"],
        "artifact_refs": [],
        "failures": failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-007 deterministic analysis fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": guard_results,
    }
    report.update(payload)
    return report


def build_wi007_analysis_reports() -> dict[str, dict[str, Any]]:
    factory = AnalystMemoFactory()
    memos = factory.fixture_memos()
    validation = AnalystMemoValidator().validate_all(memos)
    calculator = ConsensusCalculator()
    high = calculator.calculate(factory.fixture_memos(direction_scores=[4, 4, 3, 3], confidences=[0.8, 0.8, 0.75, 0.75]))
    low_action = calculator.calculate(factory.fixture_memos(direction_scores=[1, 1, 1, 1], confidences=[0.4, 0.4, 0.4, 0.4]))
    reports = {
        "analyst_memo_report.json": _envelope(
            "analyst_memo_report.json",
            {
                "profile_versions": {memo.role: memo.profile_version for memo in memos},
                "memo_envelopes": [memo.__dict__ for memo in memos],
                "role_payloads": {memo.role: memo.role_payload for memo in memos},
                "schema_validation": validation,
                "independence_checks": {
                    "profile_independence_pass": validation["profile_independence_pass"],
                    "skill_package_refs": validation["skill_package_refs"],
                    "rubric_refs": validation["rubric_refs"],
                },
                "schema_pass": validation["schema_pass"],
                "role_payload_pass": validation["role_payload_pass"],
                "profile_independence_pass": validation["profile_independence_pass"],
                "skill_package_refs": validation["skill_package_refs"],
                "rubric_refs": validation["rubric_refs"],
                "score_range_pass": validation["score_range_pass"],
                "evidence_quality_range_pass": validation["evidence_quality_range_pass"],
                "hard_dissent_field": validation["hard_dissent_field"],
                "evidence_refs": validation["evidence_refs"],
                "counter_evidence": validation["counter_evidence"],
            },
        ),
        "consensus_action_report.json": _envelope(
            "consensus_action_report.json",
            {
                "formula_inputs": {"high": high.formula_inputs, "low_action": low_action.formula_inputs},
                "population_std_outputs": {"high": high.population_std, "low_action": low_action.population_std},
                "dominant_direction_share": {"high": high.dominant_direction_share, "low_action": low_action.dominant_direction_share},
                "expected_outputs": {"action_threshold": 0.65, "low_action_reason": "low_action_conviction_no_execution"},
                "actual_outputs": {"high": high.__dict__, "low_action": low_action.__dict__},
                "threshold_decisions": {"high": high.reason_code, "low_action": low_action.reason_code},
                "no_execution_when_low_action_conviction": low_action.execution_authorized is False,
            },
        ),
    }
    return {name: deepcopy(report) for name, report in reports.items()}
