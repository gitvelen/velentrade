from velentrade.domain.finance.boundary import FinanceAssetUpdate, FinanceProfileService, _report_envelope


def test_finance_profile_blocks_non_a_assets_from_trade_and_projects_manual_todo():
    service = FinanceProfileService()

    profile = service.update_profile(
        [
            FinanceAssetUpdate("cash", {"amount": 120000, "currency": "CNY"}, "2026-04-30", "owner"),
            FinanceAssetUpdate("fund", {"amount": 80000, "currency": "CNY"}, "2026-04-30", "quote"),
            FinanceAssetUpdate("gold", {"amount": 30000, "currency": "CNY"}, "2026-04-30", "quote"),
            FinanceAssetUpdate("real_estate", {"amount": 3000000, "currency": "CNY"}, "2025-01-01", "manual"),
            FinanceAssetUpdate("liability", {"amount": 500000, "currency": "CNY"}, "2026-04-30", "owner"),
        ],
        income={"salary": {"amount": 50000, "currency": "CNY"}},
        tax_reminders=["annual_tax"],
        major_expenses=["tuition"],
    )

    assert profile.sensitive_fields_encrypted is True
    assert service.request_trade("fund", "fund-001").allowed is False
    assert service.request_trade("gold", "gold-001").reason_code == "non_a_asset_no_trade"
    assert service.request_trade("a_share", "600000.SH").allowed is True
    assert service.request_trade("a_share", "AAPL.SH").allowed is False
    assert service.request_trade("a_share", "AAPL.SH").reason_code == "non_a_asset_no_trade"
    assert {todo.asset_type for todo in service.manual_todos} == {"real_estate", "tax", "major_expense"}
    assert service.finance_overview()["sensitive_data_notice"]["allowed_cleartext_roles"] == ["cfo", "finance_service"]


def test_finance_asset_boundary_report_has_required_evidence_fields():
    report = FinanceProfileService().build_asset_boundary_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-005"]
    assert report["test_case_refs"] == ["TC-ACC-023-01"]
    assert set(report) >= {
        "asset_registry",
        "fund_gold_quotes",
        "real_estate_manual_valuation",
        "non_a_asset_trade_denials",
        "asset_profiles",
        "market_data_links",
        "manual_valuation",
        "blocked_trade_tasks",
        "manual_todo_tasks",
    }
    assert report["non_a_asset_trade_denials"][0]["reason_code"] == "non_a_asset_no_trade"


def test_finance_report_fails_when_guard_or_failure_fails():
    report = _report_envelope(
        "finance_asset_boundary_report.json",
        "TC-ACC-023-01",
        "ACC-023",
        "REQ-023",
        {"probe": "negative"},
        guard_results=[
            {
                "guard": "non_a_asset_no_trade",
                "input_ref": "fund-trade",
                "expected": "denied",
                "actual": "allowed",
                "result": "fail",
            }
        ],
        failures=[{"code": "non_a_trade_allowed", "message": "fund trade entered approval chain"}],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "non_a_trade_allowed"
