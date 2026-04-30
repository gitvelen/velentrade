from __future__ import annotations

from typing import Any

from velentrade.domain.investment.paper_account.wi009_reports import _envelope
from velentrade.domain.investment.position.monitor import PositionMonitor


def build_position_disposal_report() -> dict[str, Any]:
    task = PositionMonitor().handle_triggers("600000.SH", ["abnormal_volatility", "major_announcement", "risk_threshold_breach"])
    payload = {
        "triggers": task.triggers,
        "trigger_events": [{"trigger": trigger, "symbol": task.symbol} for trigger in task.triggers],
        "position_disposal_tasks": [task.__dict__],
        "priority_changes": {"from": "P1", "to": task.priority},
        "risk_review_guard": task.risk_gate_present,
        "execution_core_guard": task.execution_core_guard_present,
        "risk_gate_present": task.risk_gate_present,
        "audit_trace": task.audit_trace,
    }
    return _envelope("position_disposal_report.json", "TC-ACC-022-01", "ACC-022", "REQ-022", payload)
