from __future__ import annotations

from dataclasses import dataclass, replace
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

    def apply_execution(self, account: PaperAccount, order: Any, receipt: Any) -> PaperAccount:
        if receipt.fill_status not in {"filled", "partial"} or receipt.fill_price is None or receipt.fill_quantity <= 0:
            return account

        positions = {symbol: dict(position) for symbol, position in account.positions.items()}
        cost_basis = {symbol: dict(basis) for symbol, basis in account.cost_basis.items()}
        cash_amount = float(account.cash["amount"])
        gross = float(receipt.fill_price) * float(receipt.fill_quantity)
        fees = sum(float(value) for value in receipt.fees.values())
        taxes = sum(float(value) for value in receipt.taxes.values())

        if order.side == "buy":
            cash_amount -= gross + fees + taxes
            existing = positions.get(order.symbol, {"quantity": 0.0, "available_quantity": 0.0})
            existing_quantity = float(existing.get("quantity", 0))
            existing_available = float(existing.get("available_quantity", 0))
            locked = receipt.t_plus_one_state == "locked_until_next_trading_day"
            positions[order.symbol] = {
                "quantity": round(existing_quantity + receipt.fill_quantity, 3),
                "available_quantity": round(existing_available if locked else existing_available + receipt.fill_quantity, 3),
                "t_plus_one_state": receipt.t_plus_one_state,
                "last_fill_price": receipt.fill_price,
            }
            existing_basis = cost_basis.get(order.symbol, {"gross_cost": 0.0, "fees": 0.0, "taxes": 0.0})
            cost_basis[order.symbol] = {
                "gross_cost": round(float(existing_basis.get("gross_cost", 0)) + gross, 3),
                "fees": round(float(existing_basis.get("fees", 0)) + fees, 3),
                "taxes": round(float(existing_basis.get("taxes", 0)) + taxes, 3),
            }
        else:
            cash_amount += gross - fees - taxes
            existing = positions.get(order.symbol, {"quantity": 0.0, "available_quantity": 0.0})
            positions[order.symbol] = {
                **existing,
                "quantity": round(max(0.0, float(existing.get("quantity", 0)) - receipt.fill_quantity), 3),
                "available_quantity": round(max(0.0, float(existing.get("available_quantity", 0)) - receipt.fill_quantity), 3),
                "t_plus_one_state": receipt.t_plus_one_state,
                "last_fill_price": receipt.fill_price,
            }

        marked_positions_value = sum(float(position.get("quantity", 0)) * float(position.get("last_fill_price", 0)) for position in positions.values())
        total_value = round(cash_amount + marked_positions_value, 3)
        return replace(
            account,
            cash={"amount": round(cash_amount, 3), "currency": "CNY"},
            positions=positions,
            total_value={"amount": total_value, "currency": "CNY"},
            cost_basis=cost_basis,
            return_value=round(total_value - 1_000_000, 3),
            risk_budget={**account.risk_budget, "cash_ratio": round(cash_amount / total_value, 6) if total_value else 0},
            updated_at=utc_now(),
        )
