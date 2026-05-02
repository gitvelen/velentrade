from velentrade.domain.decision.service import CIODecisionMemo, DecisionService
from velentrade.domain.decision.wi008_reports import _envelope, build_wi008_decision_reports


def test_decision_service_assembles_packet_and_major_deviation_candidate():
    service = DecisionService()
    packet = service.assemble_packet(service.fixture_inputs())
    memo = CIODecisionMemo(
        decision="buy",
        decision_packet_ref=packet.packet_id,
        target_symbol="600000.SH",
        target_weight=0.16,
        price_range={"max": 12.5},
        urgency="normal",
        decision_rationale="CIO 认可多数意见，但因风险预算选择偏离优化器。",
        deviation_reason="估值安全边际更高，保留 hard dissent 到 Risk。",
        evidence_refs=["memo-1", "optimizer-1"],
    )
    guard = service.validate_cio_memo(packet, memo, optimizer_target_weights={"600000.SH": 0.10})

    assert packet.allowed_cio_actions == ["buy", "sell", "hold", "observe", "no_action", "reopen"]
    assert guard.major_deviation is True
    assert guard.single_name_deviation_pp == 6.0
    assert guard.owner_exception_candidate_ref is not None
    assert guard.reopen_recommendation_ref is None
    assert service.forbidden_service_authority_check()["service_can_approve"] is False


def test_decision_service_reopen_recommendation_for_missing_rationale_and_low_action():
    service = DecisionService()
    packet = service.assemble_packet({**service.fixture_inputs(), "action_conviction": 0.51})
    memo = CIODecisionMemo(
        decision="buy",
        decision_packet_ref=packet.packet_id,
        target_symbol="600000.SH",
        target_weight=0.20,
        price_range={"max": 12.5},
        urgency="normal",
        decision_rationale="行动强度不足仍尝试买入。",
        deviation_reason="",
        evidence_refs=["memo-1"],
    )

    guard = service.validate_cio_memo(packet, memo, optimizer_target_weights={"600000.SH": 0.10})

    assert guard.low_action_conviction is True
    assert guard.major_deviation is True
    assert guard.reopen_recommendation_ref is not None
    assert "missing_deviation_rationale" in guard.reason_codes


def test_decision_service_data_quality_blocker_recommends_reopen():
    service = DecisionService()
    packet = service.assemble_packet(
        {
            **service.fixture_inputs(),
            "data_quality_summary": {
                "decision_core_status": "blocked",
                "execution_core_status": "blocked",
                "blockers": ["execution_core_critical_field_missing"],
            },
        }
    )
    memo = CIODecisionMemo(
        decision="observe",
        decision_packet_ref=packet.packet_id,
        target_symbol="600000.SH",
        target_weight=0.10,
        price_range={},
        urgency="normal",
        decision_rationale="等待数据质量修复。",
        deviation_reason="",
        evidence_refs=["data-readiness-1"],
    )

    guard = service.validate_cio_memo(packet, memo, optimizer_target_weights={"600000.SH": 0.10})

    assert guard.data_quality_blockers == ["execution_core_critical_field_missing"]
    assert "data_quality_guard" in guard.reason_codes
    assert guard.reopen_recommendation_ref is not None
    assert guard.owner_exception_candidate_ref is None


def test_decision_service_rejects_memo_bound_to_other_packet():
    service = DecisionService()
    packet = service.assemble_packet(service.fixture_inputs())
    memo = CIODecisionMemo(
        decision="buy",
        decision_packet_ref="decision-packet-other",
        target_symbol="600000.SH",
        target_weight=0.10,
        price_range={"max": 12.5},
        urgency="normal",
        decision_rationale="wrong packet ref",
        deviation_reason="",
        evidence_refs=["memo-1"],
    )

    try:
        service.validate_cio_memo(packet, memo, optimizer_target_weights={"600000.SH": 0.10})
    except ValueError as exc:
        assert str(exc) == "decision_packet_ref_mismatch"
    else:
        raise AssertionError("expected decision_packet_ref_mismatch")


def test_portfolio_active_deviation_uses_target_symbol_and_zero_for_other_symbols():
    service = DecisionService()
    packet = service.assemble_packet(service.fixture_inputs())
    memo = CIODecisionMemo(
        decision="buy",
        decision_packet_ref=packet.packet_id,
        target_symbol="600000.SH",
        target_weight=0.35,
        price_range={"max": 12.5},
        urgency="normal",
        decision_rationale="集中提高目标持仓。",
        deviation_reason="组合主动偏离用于风险预算再分配。",
        evidence_refs=["memo-1", "optimizer-1"],
    )

    guard = service.validate_cio_memo(
        packet,
        memo,
        optimizer_target_weights={"600000.SH": 0.10, "601398.SH": 0.15},
    )

    assert guard.single_name_deviation_pp == 25.0
    assert guard.portfolio_active_deviation == 0.2
    assert guard.major_deviation is True
    assert guard.owner_exception_candidate_ref is not None


def test_wi008_decision_reports_have_contract_payloads():
    reports = build_wi008_decision_reports()

    assert set(reports) == {"decision_service_report.json", "cio_optimizer_report.json"}
    for report in reports.values():
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-008"]
        assert report["failures"] == []
    assert reports["decision_service_report.json"]["forbidden_service_authority_check"]["service_can_transition_workflow"] is False


def test_decision_report_fails_when_guard_or_failure_fails():
    report = _envelope(
        "decision_service_report.json",
        "TC-ACC-018-01",
        "ACC-018",
        "REQ-018",
        {"probe": "negative"},
        guard_results=[
            {
                "guard": "no_authority_overreach",
                "input_ref": "decision-service",
                "expected": "no_workflow_transition",
                "actual": "transitioned_workflow",
                "result": "fail",
            }
        ],
        failures=[{"code": "service_overreach", "message": "Decision Service transitioned workflow state"}],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "service_overreach"
