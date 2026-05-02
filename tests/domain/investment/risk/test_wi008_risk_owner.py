from velentrade.domain.investment.owner_exception.approval import ApprovalRecord, OwnerExceptionService
from velentrade.domain.investment.risk.runtime import RiskReviewRuntime
from velentrade.domain.investment.risk.wi008_reports import build_wi008_risk_reports


def test_risk_review_three_states_and_rejected_cannot_be_bypassed():
    runtime = RiskReviewRuntime()

    approved = runtime.review("decision-1", blockers=[], conditional_requirements=[], retained_hard_dissent=False)
    conditional = runtime.review("decision-2", blockers=[], conditional_requirements=["position_limit_exception"], retained_hard_dissent=True)
    rejected = runtime.review("decision-3", blockers=["risk_budget_breach"], conditional_requirements=[], retained_hard_dissent=True)

    assert approved.review_result == "approved"
    assert conditional.review_result == "conditional_pass"
    assert conditional.owner_exception_required is True
    assert rejected.review_result == "rejected"
    assert rejected.repairability == "repairable"
    assert runtime.bypass_attempt(rejected, actor="owner") == "denied:risk_rejected_no_override"
    assert runtime.reopen_or_close(rejected)["target"] == "S4"


def test_owner_exception_packet_and_timeout_never_execute():
    service = OwnerExceptionService()
    packet = service.create_packet("candidate-1", trigger_reason="major_deviation")
    pending = service.submit_for_approval(packet)
    expired = service.apply_timeout(pending)

    assert packet.comparison_options
    assert packet.risk_and_impact
    assert pending.decision == "pending"
    assert expired.decision == "expired"
    assert service.timeout_disposition(expired) == "no_execution"


def test_owner_timeout_disposition_is_specific_to_approval_type():
    service = OwnerExceptionService()

    records = {
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
        for approval_type in [
            "request_brief_confirmation",
            "risk_conditional_pass",
            "s6_investment_exception",
            "cio_major_deviation",
            "high_impact_governance",
            "prompt_knowledge_promotion",
            "finance_risk_budget",
            "manual_todo",
        ]
    }

    assert service.timeout_disposition(records["request_brief_confirmation"]) == "request_brief_expired_no_workflow"
    assert service.timeout_disposition(records["risk_conditional_pass"]) == "s6_blocked_no_execution"
    assert service.timeout_disposition(records["s6_investment_exception"]) == "s6_blocked_no_execution"
    assert service.timeout_disposition(records["cio_major_deviation"]) == "reopen_s4_or_close_no_execution"
    assert service.timeout_disposition(records["high_impact_governance"]) == "governance_expired_no_effect"
    assert service.timeout_disposition(records["prompt_knowledge_promotion"]) == "governance_expired_no_effect"
    assert service.timeout_disposition(records["finance_risk_budget"]) == "governance_expired_no_effect"
    assert service.timeout_disposition(records["manual_todo"]) == "manual_todo_expired_only"


def test_wi008_risk_report_has_contract_payloads():
    report = build_wi008_risk_reports()["risk_owner_exception_report.json"]

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-008"]
    assert set(report) >= {
        "risk_states",
        "approval_packet",
        "repairability",
        "reopen_target",
        "owner_timeout",
        "timeout_disposition_by_type",
        "blocked_execution",
        "reopen_required_for_repair",
        "unrepairable_attempt_closed",
        "bypass_attempt_denied",
    }
    assert report["timeout_disposition_by_type"] == {
        "risk_conditional_pass": "s6_blocked_no_execution",
        "cio_major_deviation": "reopen_s4_or_close_no_execution",
        "high_impact_governance": "governance_expired_no_effect",
        "manual_todo": "manual_todo_expired_only",
    }
