from velentrade.domain.investment.execution.paper_execution import ExecutionCoreSnapshot, MinuteBar, PaperExecutionService, PaperOrder
from velentrade.domain.investment.execution.wi009_reports import build_paper_execution_report


def test_paper_execution_uses_vwap_fees_slippage_and_t_plus_one():
    service = PaperExecutionService()
    order = PaperOrder("order-1", "wf-1", "memo-1", "600000.SH", "buy", 10_000, {"max_price": 10.5}, "normal", "exec-core-1")
    receipt = service.execute(order, ExecutionCoreSnapshot.pass_with_bars(_bars()))

    assert receipt.fill_status == "filled"
    assert receipt.pricing_method == "minute_vwap"
    assert receipt.fill_price > 0
    assert receipt.fees["commission"] >= 5
    assert receipt.taxes["stamp_tax"] == 0
    assert receipt.slippage["policy_bps"] == 5
    assert receipt.t_plus_one_state == "locked_until_next_trading_day"


def test_execution_core_block_and_price_miss_are_explicit():
    service = PaperExecutionService()
    order = PaperOrder("order-2", "wf-1", "memo-1", "600000.SH", "buy", 10_000, {"max_price": 9.0}, "urgent", "exec-core-2")

    blocked = service.execute(order, ExecutionCoreSnapshot.blocked("minute_bar_stale"))
    unfilled = service.execute(order, ExecutionCoreSnapshot.pass_with_bars(_bars()))

    assert blocked.fill_status == "blocked"
    assert blocked.reason_code == "execution_core_blocked"
    assert unfilled.fill_status in {"unfilled", "expired"}
    assert unfilled.reason_code == "price_range_not_hit"


def test_cache_hit_cannot_create_new_paper_execution_authorization():
    service = PaperExecutionService()
    order = PaperOrder("order-cache", "wf-1", "memo-1", "600000.SH", "buy", 10_000, {"max_price": 10.5}, "normal", "exec-core-cache")
    snapshot = ExecutionCoreSnapshot.pass_with_bars(_bars(), may_create_execution_authorization=False)

    receipt = service.execute(order, snapshot)

    assert receipt.fill_status == "blocked"
    assert receipt.reason_code == "cache_execution_authorization_denied"


def test_zero_volume_falls_back_to_twap_and_sell_applies_stamp_tax():
    service = PaperExecutionService()
    order = PaperOrder("order-sell", "wf-1", "memo-1", "600000.SH", "sell", 2_000, {"min_price": 9.5}, "low", "exec-core-sell")
    snapshot = ExecutionCoreSnapshot.pass_with_bars(_zero_volume_bars())

    receipt = service.execute(order, snapshot)

    assert receipt.fill_status == "filled"
    assert receipt.pricing_method == "minute_twap"
    assert receipt.taxes["stamp_tax"] > 0
    assert receipt.t_plus_one_state == "not_applicable"


def test_insufficient_cash_or_position_returns_partial_or_blocked():
    service = PaperExecutionService()
    buy_order = PaperOrder("order-partial-buy", "wf-1", "memo-1", "600000.SH", "buy", 10_000, {"max_price": 10.5}, "normal", "exec-core-buy")
    sell_order = PaperOrder("order-blocked-sell", "wf-1", "memo-1", "600000.SH", "sell", 5_000, {"min_price": 9.5}, "normal", "exec-core-sell")
    snapshot = ExecutionCoreSnapshot.pass_with_bars(_bars())

    partial_buy = service.execute(buy_order, snapshot, available_cash=25_000)
    blocked_sell = service.execute(sell_order, snapshot, available_position=0)

    assert partial_buy.fill_status == "partial"
    assert 0 < partial_buy.fill_quantity < buy_order.target_quantity_or_weight
    assert partial_buy.reason_code == "insufficient_cash_partial"
    assert blocked_sell.fill_status == "blocked"
    assert blocked_sell.reason_code == "insufficient_position_blocked"


def test_paper_execution_report_has_contract_payload():
    report = build_paper_execution_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-009"]
    assert set(report) >= {
        "order_windows",
        "minute_bar_fixture",
        "pricing_method",
        "vwap_or_twap_calculation",
        "price_range_check",
        "fill_status",
        "fees",
        "taxes",
        "slippage",
        "execution_core_freshness_block",
        "cache_execution_authorization_block",
        "t_plus_one_state",
    }
    assert report["cache_execution_authorization_block"] == "cache_execution_authorization_denied"


def _bars():
    return [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 10000),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 15000),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 12000),
    ]


def _zero_volume_bars():
    return [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 0),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 0),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 0),
    ]
