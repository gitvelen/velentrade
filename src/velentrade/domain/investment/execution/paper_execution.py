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
    may_create_execution_authorization: bool = True

    @classmethod
    def pass_with_bars(cls, bars: list[MinuteBar], may_create_execution_authorization: bool = True) -> "ExecutionCoreSnapshot":
        return cls(
            "pass",
            None,
            bars,
            {"commission_bps": 2.5, "min_commission": 5, "stamp_tax_sell_bps": 10, "transfer_bps": 0.1},
            may_create_execution_authorization,
        )

    @classmethod
    def blocked(cls, reason_code: str) -> "ExecutionCoreSnapshot":
        return cls("blocked", reason_code, [], {"commission_bps": 2.5, "min_commission": 5, "stamp_tax_sell_bps": 10, "transfer_bps": 0.1}, False)


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
    def execute(
        self,
        order: PaperOrder,
        snapshot: ExecutionCoreSnapshot,
        available_cash: float | None = None,
        available_position: float | None = None,
    ) -> PaperExecutionReceipt:
        window_by_urgency = {"urgent": "30m", "normal": "2h", "low": "full_day"}
        if order.urgency not in window_by_urgency:
            return self._receipt(order, "invalid", "blocked", None, 0, "invalid_order_urgency", snapshot, "not_applicable")
        window = window_by_urgency[order.urgency]
        if order.side not in {"buy", "sell"}:
            return self._receipt(order, window, "blocked", None, 0, "invalid_order_side", snapshot, "not_applicable")
        if not _is_a_share_symbol(order.symbol):
            return self._receipt(order, window, "blocked", None, 0, "non_a_asset_no_paper_execution", snapshot)
        if snapshot.status != "pass" or not snapshot.bars:
            return self._receipt(order, window, "blocked", None, 0, "execution_core_blocked", snapshot)
        if not snapshot.may_create_execution_authorization:
            return self._receipt(order, window, "blocked", None, 0, "cache_execution_authorization_denied", snapshot)
        window_bars = _select_window_bars(order, snapshot.bars)
        if not window_bars:
            return self._receipt(order, window, "expired" if order.urgency == "urgent" else "unfilled", None, 0, "execution_window_empty", snapshot)
        valid_bars = _valid_minute_bars(window_bars)
        if not valid_bars:
            return self._receipt(order, window, "expired" if order.urgency == "urgent" else "unfilled", None, 0, "no_valid_minute_price", snapshot)
        price, method = _vwap_or_twap(valid_bars)
        if not _price_hits(order, price, valid_bars):
            return self._receipt(order, window, "expired" if order.urgency == "urgent" else "unfilled", None, 0, "price_range_not_hit", snapshot, method)
        slipped = _apply_slippage(order, price, valid_bars)
        quantity = order.target_quantity_or_weight
        fill_status = "filled"
        reason_code = None
        if order.side == "buy" and available_cash is not None:
            affordable_quantity = _affordable_buy_quantity(slipped, available_cash, snapshot.fee_config)
            if affordable_quantity <= 0:
                return self._receipt(order, window, "blocked", None, 0, "insufficient_cash_blocked", snapshot, method)
            if affordable_quantity < quantity:
                quantity = affordable_quantity
                fill_status = "partial"
                reason_code = "insufficient_cash_partial"
        if order.side == "sell" and available_position is not None:
            if available_position <= 0:
                return self._receipt(order, window, "blocked", None, 0, "insufficient_position_blocked", snapshot, method)
            if available_position < quantity:
                quantity = available_position
                fill_status = "partial"
                reason_code = "insufficient_position_partial"
        return self._receipt(order, window, fill_status, slipped, quantity, reason_code, snapshot, method)

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
        is_executed = fill_status in {"filled", "partial"}
        commission = max(5.0, gross * snapshot.fee_config["commission_bps"] / 10000) if is_executed else 0
        transfer = gross * snapshot.fee_config["transfer_bps"] / 10000 if is_executed else 0
        stamp = gross * snapshot.fee_config["stamp_tax_sell_bps"] / 10000 if is_executed and order.side == "sell" else 0
        policy_bps = {"urgent": 8, "normal": 5, "low": 3}.get(order.urgency, 0)
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
            t_plus_one_state="locked_until_next_trading_day" if is_executed and order.side == "buy" else "not_applicable",
            attribution_ref=new_id("attribution") if is_executed else None,
            reason_code=reason_code,
        )


def _vwap_or_twap(bars: list[MinuteBar]) -> tuple[float, str]:
    total_volume = sum(bar.volume for bar in bars)
    if total_volume:
        return sum(bar.typical_price * bar.volume for bar in bars) / total_volume, "minute_vwap"
    return sum(bar.typical_price for bar in bars) / len(bars), "minute_twap"


def _select_window_bars(order: PaperOrder, bars: list[MinuteBar]) -> list[MinuteBar]:
    window_size = {"urgent": 30, "normal": 120, "low": len(bars)}[order.urgency]
    return bars[:window_size]


def _valid_minute_bars(bars: list[MinuteBar]) -> list[MinuteBar]:
    return [bar for bar in bars if bar.open > 0 and bar.high > 0 and bar.low > 0 and bar.close > 0 and bar.high >= bar.low and bar.volume >= 0]


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


def _affordable_buy_quantity(fill_price: float, available_cash: float, fee_config: dict[str, float]) -> float:
    if available_cash <= 0 or fill_price <= 0:
        return 0.0
    commission_rate = fee_config["commission_bps"] / 10000
    transfer_rate = fee_config["transfer_bps"] / 10000
    min_commission = fee_config["min_commission"]
    if available_cash <= min_commission:
        return 0.0

    quantity_with_min_commission = (available_cash - min_commission) / (fill_price * (1 + transfer_rate))
    gross_with_min_commission = quantity_with_min_commission * fill_price
    if gross_with_min_commission * commission_rate <= min_commission:
        quantity = _floor_quantity(quantity_with_min_commission)
    else:
        quantity = _floor_quantity(available_cash / (fill_price * (1 + commission_rate + transfer_rate)))

    while quantity > 0 and _buy_cash_required(quantity, fill_price, fee_config) > available_cash:
        quantity = _floor_quantity(quantity - 0.001)
    return quantity


def _buy_cash_required(quantity: float, fill_price: float, fee_config: dict[str, float]) -> float:
    gross = fill_price * quantity
    commission = round(max(fee_config["min_commission"], gross * fee_config["commission_bps"] / 10000), 3)
    transfer = round(gross * fee_config["transfer_bps"] / 10000, 3)
    return gross + commission + transfer


def _floor_quantity(quantity: float) -> float:
    return max(0.0, int(quantity * 1000) / 1000)


def _is_a_share_symbol(symbol: str) -> bool:
    return symbol.endswith((".SH", ".SZ", ".BJ"))
