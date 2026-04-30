from velentrade.domain.investment.position.monitor import PositionMonitor
from velentrade.domain.investment.position.wi009_reports import build_position_disposal_report


def test_position_monitor_creates_disposal_task_without_skipping_risk():
    monitor = PositionMonitor()
    task = monitor.handle_triggers("600000.SH", ["abnormal_volatility", "major_announcement", "risk_threshold_breach"])

    assert task.priority == "P0"
    assert task.risk_gate_present is True
    assert task.execution_core_guard_present is True
    assert task.direct_execution_allowed is False
    assert task.audit_trace


def test_position_disposal_report_has_contract_payload():
    report = build_position_disposal_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-009"]
    assert set(report) >= {"triggers", "trigger_events", "position_disposal_tasks", "priority_changes", "risk_review_guard", "execution_core_guard", "risk_gate_present", "audit_trace"}
