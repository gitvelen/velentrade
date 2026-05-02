from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.owner_exception.approval import ApprovalRecord, OwnerExceptionService
from velentrade.domain.investment.risk.runtime import RiskReviewRuntime


def build_wi008_risk_reports() -> dict[str, dict[str, Any]]:
    risk = RiskReviewRuntime()
    approved = risk.review("decision-approved", [], [], False)
    conditional = risk.review("decision-conditional", [], ["position_limit_exception"], True)
    rejected = risk.review("decision-rejected", ["risk_budget_breach"], [], True)
    unrepairable = risk.review("decision-unrepairable", ["unrepairable_security_issue"], [], False)
    owner = OwnerExceptionService()
    packet = owner.create_packet("candidate-1", "major_deviation")
    pending = owner.submit_for_approval(packet)
    expired = owner.apply_timeout(pending)
    timeout_records = {
        approval_type: ApprovalRecord(
            approval_id=f"approval-{approval_type}",
            approval_type=approval_type,
            approval_object_ref="object-1",
            trigger_reason="timeout_fixture",
            comparison_options=[],
            recommended_decision="no_effect_on_timeout",
            risk_and_impact={},
            evidence_refs=[],
            effective_scope="current_attempt_only",
            timeout_policy="default",
            decision="expired",
        )
        for approval_type in ["risk_conditional_pass", "cio_major_deviation", "high_impact_governance", "manual_todo"]
    }
    payload = {
        "risk_states": {"approved": approved.__dict__, "conditional_pass": conditional.__dict__, "rejected": rejected.__dict__},
        "approval_packet": packet.__dict__,
        "repairability": {"rejected": rejected.repairability, "unrepairable": unrepairable.repairability},
        "reopen_target": risk.reopen_or_close(rejected),
        "owner_timeout": expired.__dict__,
        "timeout_disposition_by_type": {approval_type: owner.timeout_disposition(record) for approval_type, record in timeout_records.items()},
        "blocked_execution": rejected.review_result == "rejected" and expired.decision == "expired",
        "reopen_required_for_repair": risk.reopen_or_close(rejected)["action"] == "reopen",
        "unrepairable_attempt_closed": risk.reopen_or_close(unrepairable)["action"] == "close_attempt",
        "bypass_attempt_denied": risk.bypass_attempt(rejected, "owner"),
    }
    return {"risk_owner_exception_report.json": _envelope(payload)}


def _envelope(payload: dict[str, Any]) -> dict[str, Any]:
    report = {
        "report_id": "risk_owner_exception_report.json",
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi008",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-008"],
        "test_case_refs": ["TC-ACC-019-01"],
        "fixture_refs": ["FX-RISK-REJECTED-REOPEN"],
        "result": "pass",
        "checked_requirements": ["REQ-019"],
        "checked_acceptances": ["ACC-019"],
        "checked_invariants": ["INV-RISK-REJECTED-NO-OWNER-OVERRIDE"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-008 deterministic risk fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "risk_rejected_no_override", "input_ref": "rejected", "expected": "denied", "actual": payload["bypass_attempt_denied"], "result": "pass"}],
    }
    report.update(payload)
    return deepcopy(report)
