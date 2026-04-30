from velentrade.domain.investment.paper_account.account import PaperAccountService
from velentrade.domain.investment.paper_account.wi009_reports import build_paper_account_report


def test_paper_account_initializes_one_million_cny_empty_portfolio():
    account = PaperAccountService().initialize()

    assert account.cash == {"amount": 1_000_000, "currency": "CNY"}
    assert account.positions == {}
    assert account.total_value == {"amount": 1_000_000, "currency": "CNY"}
    assert account.return_value == 0
    assert account.drawdown == 0
    assert account.risk_budget["cash_ratio"] == 1.0


def test_paper_account_report_has_contract_payload():
    report = build_paper_account_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-009"]
    assert set(report) >= {"initial_cash", "positions", "cost_basis", "baseline_returns", "risk_budget_baseline"}
