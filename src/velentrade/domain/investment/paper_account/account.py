from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id, utc_now


@dataclass(frozen=True)
class PaperAccount:
    paper_account_id: str
    cash: dict[str, Any]
    positions: dict[str, Any]
    total_value: dict[str, Any]
    cost_basis: dict[str, Any]
    return_value: float
    drawdown: float
    risk_budget: dict[str, Any]
    benchmark_ref: str
    created_at: str
    updated_at: str


class PaperAccountService:
    def initialize(self) -> PaperAccount:
        now = utc_now()
        return PaperAccount(
            paper_account_id=new_id("paper-account"),
            cash={"amount": 1_000_000, "currency": "CNY"},
            positions={},
            total_value={"amount": 1_000_000, "currency": "CNY"},
            cost_basis={},
            return_value=0,
            drawdown=0,
            risk_budget={"cash_ratio": 1.0, "risk_budget_used": 0, "single_name_limit": 0.15},
            benchmark_ref="baseline-cash",
            created_at=now,
            updated_at=now,
        )
