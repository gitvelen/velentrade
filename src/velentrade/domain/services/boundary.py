from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import GuardDecision


FORBIDDEN_AUTHORITY_FIELDS = {
    "approval",
    "owner_approval",
    "risk_verdict",
    "final_investment_decision",
    "real_trade_action",
    "trade_order",
    "workflow_state",
}


@dataclass(frozen=True)
class ServiceOutput:
    service_name: str
    payload: dict[str, Any]
    output_quality_score: float = 1.0
    limitations: list[str] = field(default_factory=list)


class ServiceBoundaryChecker:
    def check(self, output: ServiceOutput) -> GuardDecision:
        forbidden = sorted(field for field in output.payload if field in FORBIDDEN_AUTHORITY_FIELDS)
        if forbidden:
            return GuardDecision(
                False,
                "COMMAND_NOT_ALLOWED",
                "service_forbidden_authority",
                "Service output cannot approve, veto, decide, trade, or advance workflow state.",
                {"service_name": output.service_name, "forbidden_fields": forbidden},
            )
        return GuardDecision(
            True,
            "OK",
            "service_output_boundary_pass",
            "Service output is limited to deterministic result, constraint, recommendation, or receipt.",
            {"service_name": output.service_name},
        )
