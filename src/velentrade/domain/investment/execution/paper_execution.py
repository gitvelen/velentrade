from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class MinuteBar:
    minute_ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3


@dataclass(frozen=True)
class ExecutionCoreSnapshot:
    status: str
    reason_code: str | None
    bars: list[MinuteBar]
    fee_config: dict[str, float]

    @classmethod
    def pass_with_bars(cls, bars: list[MinuteBar]) -> "ExecutionCoreSnapshot":
        return cls("pass", None, bars, {"commission_bps": 2.5, "min_commission": 5, "stamp_tax_sell_bps": 10, "transfer_bps": 0.1})

    @classmethod
    def blocked(cls, reason_code: str) -> "ExecutionCoreSnapshot":
        return cls("blocked", reason_code, [], {"commission_bps": 2.5, "min_commission": 5, "stamp_tax_sell_bps": 10, "transfer_bps": 0.1})


@dataclass(frozen=True)
class PaperOrder:
    paper_order_id: str
    workflow_id: str
    decision_memo_ref: str
    symbol: str
    side: str
    target_quantity_or_weight: float
    price_range: dict[str, float]
    urgency: str
    execution_core_snapshot_ref: str
    status: str = "pending"


@dataclass(frozen=True)
class PaperExecutionReceipt:
    paper_order_id: str
    decision_memo_ref: str
    execution_window: str
    pricing_method: str
    market_data_refs: list[str]
    fill_status: str
    fill_price: float | None
    fill_quantity: float
    fees: dict[str, float]
    taxes: dict[str, float]
    slippage: dict[str, float]
    t_plus_one_state: str
    attribution_ref: str | None
    reason_code: str | None = None


class PaperExecutionService:
    def execute(self, order: PaperOrder, snapshot: ExecutionCoreSnapshot) -> PaperExecutionReceipt:
        window = {"urgent": "30m", "normal": "2h", "low": "full_day"}[order.urgency]
        if snapshot.status != "pass" or not snapshot.bars:
            return self._receipt(order, window, "blocked", None, 0, "execution_core_blocked", snapshot)
        price, method = _vwap_or_twap(snapshot.bars)
        if not _price_hits(order, price, snapshot.bars):
            return self._receipt(order, window, "expired" if order.urgency == "urgent" else "unfilled", None, 0, "price_range_not_hit", snapshot, method)
        slipped = _apply_slippage(order, price, snapshot.bars)
        quantity = order.target_quantity_or_weight
        return self._receipt(order, window, "filled", slipped, quantity, None, snapshot, method)

    def _receipt(
        self,
        order: PaperOrder,
        window: str,
        fill_status: str,
        fill_price: float | None,
        quantity: float,
        reason_code: str | None,
        snapshot: ExecutionCoreSnapshot,
        pricing_method: str = "minute_vwap",
    ) -> PaperExecutionReceipt:
        gross = (fill_price or 0) * quantity
        commission = max(5.0, gross * snapshot.fee_config["commission_bps"] / 10000) if fill_status == "filled" else 0
        transfer = gross * snapshot.fee_config["transfer_bps"] / 10000 if fill_status == "filled" else 0
        stamp = gross * snapshot.fee_config["stamp_tax_sell_bps"] / 10000 if fill_status == "filled" and order.side == "sell" else 0
        policy_bps = {"urgent": 8, "normal": 5, "low": 3}[order.urgency]
        return PaperExecutionReceipt(
            paper_order_id=order.paper_order_id,
            decision_memo_ref=order.decision_memo_ref,
            execution_window=window,
            pricing_method=pricing_method,
            market_data_refs=[order.execution_core_snapshot_ref],
            fill_status=fill_status,
            fill_price=fill_price,
            fill_quantity=quantity,
            fees={"commission": round(commission, 3), "transfer": round(transfer, 3)},
            taxes={"stamp_tax": round(stamp, 3)},
            slippage={"policy_bps": policy_bps},
            t_plus_one_state="locked_until_next_trading_day" if fill_status == "filled" and order.side == "buy" else "not_applicable",
            attribution_ref=new_id("attribution") if fill_status == "filled" else None,
            reason_code=reason_code,
        )


def _vwap_or_twap(bars: list[MinuteBar]) -> tuple[float, str]:
    total_volume = sum(bar.volume for bar in bars)
    if total_volume:
        return sum(bar.typical_price * bar.volume for bar in bars) / total_volume, "minute_vwap"
    return sum(bar.typical_price for bar in bars) / len(bars), "minute_twap"


def _price_hits(order: PaperOrder, price: float, bars: list[MinuteBar]) -> bool:
    if order.side == "buy":
        max_price = order.price_range.get("max_price") or order.price_range.get("max")
        return max_price is not None and min(bar.low for bar in bars) <= max_price and price <= max_price
    min_price = order.price_range.get("min_price") or order.price_range.get("min")
    return min_price is not None and max(bar.high for bar in bars) >= min_price and price >= min_price


def _apply_slippage(order: PaperOrder, price: float, bars: list[MinuteBar]) -> float:
    bps = {"urgent": 8, "normal": 5, "low": 3}[order.urgency]
    amplitude = (max(bar.high for bar in bars) - min(bar.low for bar in bars)) / bars[0].open
    if amplitude > 0.03:
        bps += 2
    multiplier = 1 + bps / 10000 if order.side == "buy" else 1 - bps / 10000
    return round(price * multiplier, 4)
