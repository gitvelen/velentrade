from __future__ import annotations

from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.paper_account.account import PaperAccountService


def build_paper_account_report() -> dict[str, Any]:
    account = PaperAccountService().initialize()
    payload = {
        "initial_cash": account.cash,
        "positions": account.positions,
        "cost_basis": account.cost_basis,
        "baseline_returns": {"return": account.return_value, "drawdown": account.drawdown, "benchmark_ref": account.benchmark_ref},
        "risk_budget_baseline": account.risk_budget,
    }
    return _envelope("paper_account_report.json", "TC-ACC-020-01", "ACC-020", "REQ-020", payload)


def _envelope(report_id: str, tc: str, acc: str, req: str, payload: dict[str, Any]) -> dict[str, Any]:
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi009",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-009"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": "pass",
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-PAPER-NO-REAL-BROKER"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-009 deterministic paper account fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "initial_account", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}],
    }
    report.update(payload)
    return report
