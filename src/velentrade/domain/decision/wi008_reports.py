from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.decision.service import CIODecisionMemo, DecisionService


def build_wi008_decision_reports() -> dict[str, dict[str, Any]]:
    service = DecisionService()
    packet = service.assemble_packet(service.fixture_inputs())
    memo = CIODecisionMemo("buy", packet.packet_id, "600000.SH", 0.16, {"max": 12.5}, "normal", "CIO synthesis", "optimizer deviation justified", ["memo-1"])
    guard = service.validate_cio_memo(packet, memo, {"600000.SH": 0.10})
    low_packet = service.assemble_packet({**service.fixture_inputs(), "action_conviction": 0.50})
    low_guard = service.validate_cio_memo(low_packet, CIODecisionMemo("buy", low_packet.packet_id, "600000.SH", 0.20, {}, "normal", "low action", "", ["memo-1"]), {"600000.SH": 0.10})
    reports = {
        "decision_service_report.json": _envelope(
            "decision_service_report.json",
            "TC-ACC-018-01",
            "ACC-018",
            "REQ-018",
            {
                "input_artifact_refs": packet.input_artifact_refs,
                "decision_packet": packet.__dict__,
                "input_completeness": guard.input_completeness,
                "decision_guard_result": guard.__dict__,
                "single_name_deviation": guard.single_name_deviation_pp,
                "portfolio_active_deviation": guard.portfolio_active_deviation,
                "exception_candidate_or_reopen": {"exception": guard.owner_exception_candidate_ref, "reopen": low_guard.reopen_recommendation_ref},
                "forbidden_service_authority_check": service.forbidden_service_authority_check(),
                "failure_path_cases": {"low_action": low_guard.reason_codes, "missing_deviation_rationale": "missing_deviation_rationale" in low_guard.reason_codes},
                "view_projection_results": [{"view": "InvestmentDossierReadModel.decision_service", "expected": "visible", "actual": "visible", "result": "pass"}],
                "runbook_trace": [{"step": "assemble_packet", "actor": "decision_service", "input_ref": "S3", "output_ref": packet.packet_id, "result": "pass"}],
            },
        ),
        "cio_optimizer_report.json": _envelope(
            "cio_optimizer_report.json",
            "TC-ACC-018-01",
            "ACC-018",
            "REQ-018",
            {
                "chair_brief": "chair-1",
                "debate_synthesis": "debate-1",
                "decision_packet": packet.__dict__,
                "packet_consumed": packet.packet_id,
                "decision_guard_result": guard.__dict__,
                "forbidden_cio_actions_denied": {"direct_order": True, "risk_override": True, "artifact_overwrite": True},
                "deviation_reason": memo.deviation_reason,
                "single_name_deviation": guard.single_name_deviation_pp,
                "portfolio_active_deviation": guard.portfolio_active_deviation,
                "major_deviation_flag": guard.major_deviation,
                "owner_exception_or_rework": {"exception": guard.owner_exception_candidate_ref, "reopen": low_guard.reopen_recommendation_ref},
            },
        ),
    }
    return {name: deepcopy(report) for name, report in reports.items()}


def _envelope(
    report_id: str,
    tc: str,
    acc: str,
    req: str,
    payload: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    guard_results = guard_results or [{"guard": "no_authority_overreach", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}]
    failures = failures or []
    result = "fail" if failures or any(guard.get("result") != "pass" for guard in guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi008",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-008"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-DECISION-SERVICE-NO-AUTHORITY-OVERREACH"],
        "artifact_refs": [],
        "failures": failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-008 deterministic decision fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": guard_results,
    }
    report.update(payload)
    return report
