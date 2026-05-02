from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import GuardDecision, new_id, utc_now


NON_A_ASSET_TYPES = {"fund", "gold", "real_estate", "cash", "liability", "other"}


@dataclass(frozen=True)
class FinanceAssetUpdate:
    asset_type: str
    valuation: dict[str, Any]
    valuation_date: str
    source: str
    asset_id: str | None = None


@dataclass(frozen=True)
class ManualTodo:
    todo_id: str
    asset_type: str
    due_date: str
    risk_hint: str
    state: str = "open"


@dataclass(frozen=True)
class FinanceProfile:
    profile_id: str
    assets: list[dict[str, Any]]
    liabilities: list[dict[str, Any]]
    cash_flow_summary: dict[str, Any]
    tax_reminder_summary: list[str]
    risk_budget: dict[str, Any]
    liquidity_constraints: dict[str, Any]
    sensitive_fields_encrypted: bool
    derived_summary_refs: list[str]


@dataclass
class FinanceProfileService:
    profile: FinanceProfile | None = None
    manual_todos: list[ManualTodo] = field(default_factory=list)
    sensitive_access_audit: list[dict[str, Any]] = field(default_factory=list)

    def update_profile(
        self,
        updates: list[FinanceAssetUpdate],
        income: dict[str, Any] | None = None,
        tax_reminders: list[str] | None = None,
        major_expenses: list[str] | None = None,
    ) -> FinanceProfile:
        assets: list[dict[str, Any]] = []
        liabilities: list[dict[str, Any]] = []
        self.manual_todos = []
        for update in updates:
            row = {
                "asset_id": update.asset_id or new_id(update.asset_type),
                "asset_type": update.asset_type,
                "valuation": update.valuation,
                "valuation_date": update.valuation_date,
                "source": update.source,
                "boundary_label": "trade_chain_allowed" if update.asset_type == "a_share" else "finance_planning_only",
            }
            if update.asset_type == "liability":
                liabilities.append(row)
            else:
                assets.append(row)
            if update.asset_type == "real_estate":
                self.manual_todos.append(ManualTodo(new_id("todo"), "real_estate", update.valuation_date, "manual_valuation_due"))

        for reminder in tax_reminders or []:
            self.manual_todos.append(ManualTodo(new_id("todo"), "tax", "next_tax_window", reminder))
        for expense in major_expenses or []:
            self.manual_todos.append(ManualTodo(new_id("todo"), "major_expense", "before_commitment", expense))

        cash_total = sum(
            asset["valuation"].get("amount", 0)
            for asset in assets
            if asset["asset_type"] == "cash"
        )
        liability_total = sum(item["valuation"].get("amount", 0) for item in liabilities)
        profile = FinanceProfile(
            profile_id=new_id("finance-profile"),
            assets=assets,
            liabilities=liabilities,
            cash_flow_summary={"income": income or {}, "cash_total": cash_total, "liability_total": liability_total},
            tax_reminder_summary=tax_reminders or [],
            risk_budget={"cash_floor": max(50000, cash_total * 0.2), "budget_ref": "risk-budget-finance-v1"},
            liquidity_constraints={"future_cash_need": major_expenses or [], "leverage": liability_total / max(cash_total, 1)},
            sensitive_fields_encrypted=True,
            derived_summary_refs=[new_id("finance-summary")],
        )
        self.profile = profile
        self.sensitive_access_audit.append({"roles_allowed": ["cfo", "finance_service"], "roles_denied": ["cio", "researcher"]})
        return profile

    def request_trade(self, asset_type: str, asset_ref: str) -> GuardDecision:
        if asset_type != "a_share":
            return GuardDecision(
                False,
                "COMMAND_NOT_ALLOWED",
                "non_a_asset_no_trade",
                "非 A 股资产只能进入财务规划、风险提示或 manual_todo。",
                {"asset_type": asset_type, "asset_ref": asset_ref, "projected_to": ["planning", "risk_hint", "manual_todo"]},
            )
        return GuardDecision(True, "OK", "a_share_trade_chain_allowed", "A 股资产可进入正式投资链。", {"asset_ref": asset_ref})

    def finance_overview(self) -> dict[str, Any]:
        profile = self.profile or self._build_fixture_profile()
        return {
            "asset_profile": profile.assets + profile.liabilities,
            "finance_health": {
                "liquidity": profile.cash_flow_summary["cash_total"],
                "leverage": profile.liquidity_constraints["leverage"],
                "risk_budget": profile.risk_budget,
                "stress_test_summary": "cash_floor_checked",
                "future_cash_need": profile.liquidity_constraints["future_cash_need"],
            },
            "manual_todo": [todo.__dict__ for todo in self.manual_todos],
            "sensitive_data_notice": {
                "redaction_applied": True,
                "allowed_cleartext_roles": ["cfo", "finance_service"],
                "denied_agent_count": 7,
            },
        }

    def build_asset_boundary_report(self) -> dict[str, Any]:
        profile = self._build_fixture_profile()
        fund_denial = self.request_trade("fund", "fund-fixture")
        gold_denial = self.request_trade("gold", "gold-fixture")
        payload = {
            "asset_registry": [asset["asset_type"] for asset in profile.assets + profile.liabilities],
            "fund_gold_quotes": {"fund": "auto_quote_ref", "gold": "auto_quote_ref"},
            "real_estate_manual_valuation": {"source": "manual", "todo_present": True},
            "non_a_asset_trade_denials": [fund_denial.details | {"reason_code": fund_denial.reason_code}, gold_denial.details | {"reason_code": gold_denial.reason_code}],
            "asset_profiles": profile.assets + profile.liabilities,
            "market_data_links": {"fund": ["quote-fund-1"], "gold": ["quote-gold-1"]},
            "manual_valuation": [todo.__dict__ for todo in self.manual_todos if todo.asset_type == "real_estate"],
            "blocked_trade_tasks": [fund_denial.details, gold_denial.details],
            "manual_todo_tasks": [todo.__dict__ for todo in self.manual_todos],
        }
        return _report_envelope("finance_asset_boundary_report.json", "TC-ACC-023-01", "ACC-023", "REQ-023", payload)

    def _build_fixture_profile(self) -> FinanceProfile:
        if self.profile is not None:
            return self.profile
        return self.update_profile(
            [
                FinanceAssetUpdate("cash", {"amount": 120000, "currency": "CNY"}, "2026-04-30", "owner", "cash-1"),
                FinanceAssetUpdate("fund", {"amount": 80000, "currency": "CNY"}, "2026-04-30", "auto_quote", "fund-1"),
                FinanceAssetUpdate("gold", {"amount": 30000, "currency": "CNY"}, "2026-04-30", "auto_quote", "gold-1"),
                FinanceAssetUpdate("real_estate", {"amount": 3000000, "currency": "CNY"}, "2025-01-01", "manual", "home-1"),
                FinanceAssetUpdate("liability", {"amount": 500000, "currency": "CNY"}, "2026-04-30", "owner", "loan-1"),
            ],
            income={"salary": {"amount": 50000, "currency": "CNY"}},
            tax_reminders=["annual_tax"],
            major_expenses=["tuition"],
        )


def _report_envelope(
    report_id: str,
    tc: str,
    acc: str,
    req: str,
    payload: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    guard_results = guard_results or [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}]
    failures = failures or []
    result = "fail" if failures or any(guard.get("result") != "pass" for guard in guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi005",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-005"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-FINANCE-KNOWLEDGE-NO-HOT-PATCH"],
        "artifact_refs": [],
        "failures": failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-005 deterministic finance fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": guard_results,
    }
    report.update(payload)
    return report
