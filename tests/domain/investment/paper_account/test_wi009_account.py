from velentrade.domain.investment.paper_account.account import PaperAccountService
from velentrade.domain.investment.paper_account.wi009_reports import build_paper_account_report
from velentrade.domain.investment.execution.paper_execution import ExecutionCoreSnapshot, MinuteBar, PaperExecutionService, PaperOrder


def test_paper_account_initializes_one_million_cny_empty_portfolio():
    account = PaperAccountService().initialize()

    assert account.cash == {"amount": 1_000_000, "currency": "CNY"}
    assert account.positions == {}
    assert account.total_value == {"amount": 1_000_000, "currency": "CNY"}
    assert account.return_value == 0
    assert account.drawdown == 0
    assert account.risk_budget["cash_ratio"] == 1.0


def test_paper_account_applies_buy_receipt_with_t_plus_one_locked_position():
    account_service = PaperAccountService()
    account = account_service.initialize()
    order = PaperOrder("order-account-buy", "wf-1", "memo-1", "600000.SH", "buy", 1_000, {"max_price": 10.5}, "normal", "exec-core-1")
    receipt = PaperExecutionService().execute(order, ExecutionCoreSnapshot.pass_with_bars(_bars()))

    updated = account_service.apply_execution(account, order, receipt)

    assert updated.cash["amount"] < account.cash["amount"]
    assert updated.positions["600000.SH"]["quantity"] == receipt.fill_quantity
    assert updated.positions["600000.SH"]["available_quantity"] == 0
    assert updated.positions["600000.SH"]["t_plus_one_state"] == "locked_until_next_trading_day"
    assert updated.cost_basis["600000.SH"]["gross_cost"] > 0


def test_paper_account_applies_sell_receipt_after_t_plus_one_availability():
    account_service = PaperAccountService()
    account = account_service.initialize()
    held_account = account.__class__(
        **{
            **account.__dict__,
            "positions": {
                "600000.SH": {
                    "quantity": 2_000,
                    "available_quantity": 2_000,
                    "t_plus_one_state": "available",
                    "last_fill_price": 10.0,
                }
            },
            "total_value": {"amount": 1_020_000, "currency": "CNY"},
        }
    )
    order = PaperOrder("order-account-sell", "wf-1", "memo-1", "600000.SH", "sell", 1_000, {"min_price": 9.5}, "low", "exec-core-1")
    receipt = PaperExecutionService().execute(order, ExecutionCoreSnapshot.pass_with_bars(_bars()), available_position=held_account.positions["600000.SH"]["available_quantity"])

    updated = account_service.apply_execution(held_account, order, receipt)

    assert receipt.taxes["stamp_tax"] > 0
    assert updated.cash["amount"] > held_account.cash["amount"]
    assert updated.positions["600000.SH"]["quantity"] == 1_000
    assert updated.positions["600000.SH"]["available_quantity"] == 1_000
    assert updated.positions["600000.SH"]["t_plus_one_state"] == "not_applicable"


def test_paper_account_report_has_contract_payload():
    report = build_paper_account_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-009"]
    assert set(report) >= {
        "initial_cash",
        "positions",
        "post_execution_cash",
        "post_execution_position",
        "post_sell_cash",
        "post_sell_position",
        "cost_basis",
        "baseline_returns",
        "risk_budget_baseline",
        "t_plus_one_position_lock",
    }
    assert report["post_execution_cash"]["amount"] < report["initial_cash"]["amount"]
    assert report["t_plus_one_position_lock"] == "locked_until_next_trading_day"
    assert report["post_sell_cash"]["amount"] > report["post_execution_cash"]["amount"]
    assert report["post_sell_position"]["quantity"] < report["post_execution_position"]["quantity"]


def _bars():
    return [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 10000),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 15000),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 12000),
    ]
