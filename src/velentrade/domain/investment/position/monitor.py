from __future__ import annotations

from dataclasses import dataclass

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class PositionDisposalTask:
    task_id: str
    symbol: str
    triggers: list[str]
    priority: str
    risk_gate_present: bool
    execution_core_guard_present: bool
    direct_execution_allowed: bool
    workflow_route: str
    reason_code: str
    audit_trace: list[str]


class PositionMonitor:
    def handle_triggers(self, symbol: str, triggers: list[str]) -> PositionDisposalTask:
        priority = "P0" if {"major_announcement", "risk_threshold_breach", "execution_failure"} & set(triggers) else "P1"
        return PositionDisposalTask(
            task_id=new_id("position-disposal"),
            symbol=symbol,
            triggers=triggers,
            priority=priority,
            risk_gate_present=True,
            execution_core_guard_present=True,
            direct_execution_allowed=False,
            workflow_route="S5_risk_review",
            reason_code="position_disposal_requires_risk_review",
            audit_trace=[new_id("audit") for _ in triggers],
        )
