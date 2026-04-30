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
    filled = service.execute(filled_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    blocked = service.execute(blocked_order, ExecutionCoreSnapshot.blocked("minute_bar_stale"))
    missed = service.execute(miss_order, ExecutionCoreSnapshot.pass_with_bars(bars))
    payload = {
        "order_windows": {"urgent": "30m", "normal": "2h", "low": "full_day"},
        "minute_bar_fixture": [bar.__dict__ for bar in bars],
        "pricing_method": filled.pricing_method,
        "vwap_or_twap_calculation": {"filled_price": filled.fill_price, "fallback": "twap_when_zero_volume"},
        "price_range_check": {"filled": "hit", "missed": missed.reason_code},
        "fill_status": {"filled": filled.fill_status, "blocked": blocked.fill_status, "missed": missed.fill_status},
        "fees": filled.fees,
        "taxes": filled.taxes,
        "slippage": filled.slippage,
        "execution_core_freshness_block": blocked.reason_code,
        "t_plus_one_state": filled.t_plus_one_state,
    }
    return _envelope("paper_execution_report.json", "TC-ACC-021-01", "ACC-021", "REQ-021", payload)
