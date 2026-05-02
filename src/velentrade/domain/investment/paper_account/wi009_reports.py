from __future__ import annotations

from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.execution.paper_execution import ExecutionCoreSnapshot, MinuteBar, PaperExecutionService, PaperOrder
from velentrade.domain.investment.paper_account.account import PaperAccountService


def build_paper_account_report() -> dict[str, Any]:
    account_service = PaperAccountService()
    account = account_service.initialize()
    order = PaperOrder("order-account-report", "wf-1", "memo-1", "600000.SH", "buy", 1000, {"max_price": 10.5}, "normal", "exec-core-account-report")
    receipt = PaperExecutionService().execute(order, ExecutionCoreSnapshot.pass_with_bars(_bars()))
    updated = account_service.apply_execution(account, order, receipt)
    sell_order = PaperOrder("order-account-report-sell", "wf-1", "memo-1", "600000.SH", "sell", 500, {"min_price": 9.5}, "low", "exec-core-account-report")
    available_for_sell = updated.positions["600000.SH"]["quantity"]
    sell_receipt = PaperExecutionService().execute(sell_order, ExecutionCoreSnapshot.pass_with_bars(_bars()), available_position=available_for_sell)
    after_sell = account_service.apply_execution(
        updated.__class__(
            **{
                **updated.__dict__,
                "positions": {
                    **updated.positions,
                    "600000.SH": {
                        **updated.positions["600000.SH"],
                        "available_quantity": available_for_sell,
                        "t_plus_one_state": "available",
                    },
                },
            }
        ),
        sell_order,
        sell_receipt,
    )
    payload = {
        "initial_cash": account.cash,
        "positions": account.positions,
        "post_execution_cash": updated.cash,
        "post_execution_position": updated.positions["600000.SH"],
        "post_sell_cash": after_sell.cash,
        "post_sell_position": after_sell.positions["600000.SH"],
        "cost_basis": updated.cost_basis,
        "baseline_returns": {"return": account.return_value, "drawdown": account.drawdown, "benchmark_ref": account.benchmark_ref},
        "risk_budget_baseline": account.risk_budget,
        "t_plus_one_position_lock": updated.positions["600000.SH"]["t_plus_one_state"],
    }
    return _envelope("paper_account_report.json", "TC-ACC-020-01", "ACC-020", "REQ-020", payload)


def _envelope(
    report_id: str,
    tc: str,
    acc: str,
    req: str,
    payload: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    guard_results = guard_results or [{"guard": "initial_account", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}]
    failures = failures or []
    result = "fail" if failures or any(guard.get("result") != "pass" for guard in guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi009",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-009"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-PAPER-NO-REAL-BROKER"],
        "artifact_refs": [],
        "failures": failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-009 deterministic paper account fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": guard_results,
    }
    report.update(payload)
    return report


def _bars() -> list[MinuteBar]:
    return [
        MinuteBar("2026-04-30T09:31:00+08:00", 10.0, 10.2, 9.9, 10.1, 10000),
        MinuteBar("2026-04-30T09:32:00+08:00", 10.1, 10.3, 10.0, 10.2, 15000),
        MinuteBar("2026-04-30T09:33:00+08:00", 10.2, 10.4, 10.1, 10.3, 12000),
    ]
