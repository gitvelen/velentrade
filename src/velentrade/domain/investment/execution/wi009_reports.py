from __future__ import annotations

from typing import Any

from velentrade.domain.investment.execution.paper_execution import ExecutionCoreSnapshot, MinuteBar, PaperExecutionService, PaperOrder
from velentrade.domain.investment.paper_account.wi009_reports import _envelope


def build_paper_execution_report() -> dict[str, Any]:
    service = PaperExecutionService()
    bars = [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 10000),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 15000),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 12000),
    ]
    filled_order = PaperOrder("order-filled", "wf-1", "memo-1", "600000.SH", "buy", 10000, {"max_price": 10.5}, "normal", "exec-core-1")
    blocked_order = PaperOrder("order-blocked", "wf-1", "memo-1", "600000.SH", "buy", 10000, {"max_price": 10.5}, "urgent", "exec-core-blocked")
    miss_order = PaperOrder("order-miss", "wf-1", "memo-1", "600000.SH", "buy", 10000, {"max_price": 9.0}, "urgent", "exec-core-1")
    cache_order = PaperOrder("order-cache", "wf-1", "memo-1", "600000.SH", "buy", 10000, {"max_price": 10.5}, "normal", "exec-core-cache")
    partial_order = PaperOrder("order-partial", "wf-1", "memo-1", "600000.SH", "buy", 10000, {"max_price": 10.5}, "normal", "exec-core-1")
    twap_sell_order = PaperOrder("order-twap-sell", "wf-1", "memo-1", "600000.SH", "sell", 2000, {"min_price": 9.5}, "low", "exec-core-twap")
    invalid_price_order = PaperOrder("order-invalid-price", "wf-1", "memo-1", "600000.SH", "buy", 1000, {"max_price": 10.5}, "normal", "exec-core-invalid-price")
    invalid_quantity_order = PaperOrder("order-invalid-quantity", "wf-1", "memo-1", "600000.SH", "buy", 0, {"max_price": 10.5}, "normal", "exec-core-invalid-quantity")
    fake_a_share_order = PaperOrder("order-fake-a", "wf-1", "memo-1", "AAPL.SH", "buy", 1000, {"max_price": 10.5}, "normal", "exec-core-fake-a")
    twap_bars = [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 0),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 0),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 0),
    ]
    invalid_price_bars = [
        MinuteBar("2026-04-30T09:31:00+08:00", 0, 0, 0, 0, 0),
        MinuteBar("2026-04-30T09:32:00+08:00", 0, 0, 0, 0, 1000),
    ]
    filled = service.execute(filled_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    blocked = service.execute(blocked_order, ExecutionCoreSnapshot.blocked("minute_bar_stale"))
    missed = service.execute(miss_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    cache_blocked = service.execute(cache_order, ExecutionCoreSnapshot.pass_with_bars(bars, may_create_execution_authorization=False))
    partial = service.execute(partial_order, ExecutionCoreSnapshot.pass_with_bars(bars), available_cash=25_000)
    twap_sell = service.execute(twap_sell_order, ExecutionCoreSnapshot.pass_with_bars(twap_bars))
    invalid_price = service.execute(invalid_price_order, ExecutionCoreSnapshot.pass_with_bars(invalid_price_bars))
    invalid_quantity = service.execute(invalid_quantity_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    fake_a_share = service.execute(fake_a_share_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    payload = {
        "order_windows": {"urgent": "30m", "normal": "2h", "low": "full_day"},
        "selected_window_bar_counts": {"urgent": len(bars[:30]), "normal": len(bars[:120]), "low": len(twap_bars)},
        "minute_bar_fixture": [bar.__dict__ for bar in bars],
        "pricing_method": {"filled": filled.pricing_method, "twap_sell": twap_sell.pricing_method},
        "vwap_or_twap_calculation": {"filled_price": filled.fill_price, "twap_sell_price": twap_sell.fill_price, "fallback": "twap_when_zero_volume"},
        "price_range_check": {"filled": "hit", "missed": missed.reason_code, "twap_sell": "hit"},
        "invalid_price_check": {"fill_status": invalid_price.fill_status, "reason_code": invalid_price.reason_code},
        "invalid_order_checks": {"invalid_quantity": invalid_quantity.reason_code, "fake_a_share_symbol": fake_a_share.reason_code},
        "fill_status": {"filled": filled.fill_status, "partial": partial.fill_status, "blocked": blocked.fill_status, "missed": missed.fill_status, "twap_sell": twap_sell.fill_status},
        "fees": filled.fees,
        "taxes": {"buy": filled.taxes, "sell": twap_sell.taxes},
        "slippage": filled.slippage,
        "execution_core_freshness_block": blocked.reason_code,
        "cache_execution_authorization_block": cache_blocked.reason_code,
        "t_plus_one_state": {"buy": filled.t_plus_one_state, "sell": twap_sell.t_plus_one_state},
    }
    return _envelope("paper_execution_report.json", "TC-ACC-021-01", "ACC-021", "REQ-021", payload)
