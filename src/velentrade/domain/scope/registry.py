from __future__ import annotations

from velentrade.domain.agents.registry import FORBIDDEN_ROLES, OFFICIAL_SERVICES

EXCLUDED_CAPABILITIES = (
    "feishu",
    "mobile_app",
    "real_broker_api",
    "real_order",
    "backtest",
    "non_a_share_auto_trade",
    "strategy_manager",
    "rules_path",
    "performance_analyst_agent",
)


def build_scope_boundary_report(
    forbidden_found: list[str] | None = None,
    ui_forbidden_found: list[str] | None = None,
    api_forbidden_found: list[str] | None = None,
) -> dict:
    forbidden_found = forbidden_found or []
    ui_forbidden_found = ui_forbidden_found or []
    api_forbidden_found = api_forbidden_found or []
    return {
        "result": "fail" if forbidden_found or ui_forbidden_found or api_forbidden_found else "pass",
        "scope_registry": {
            "owner_model": "single_owner",
            "interaction_surface": "web_only",
            "formal_investment_scope": "a_share_common_stock",
            "compliance_statement": "personal_non_public_advisory; real money actions remain human-owned",
        },
        "included_capabilities": ["web_workbench", "a_share_ic", "paper_execution", "finance_planning"],
        "forbidden_entry_scan": {
            "excluded_capabilities": list(EXCLUDED_CAPABILITIES),
            "forbidden_found": forbidden_found,
        },
        "ui_entry_scan": {"forbidden_found": ui_forbidden_found},
        "api_entry_scan": {"forbidden_found": api_forbidden_found},
    }


def validate_service_registry(
    forbidden_found: list[str] | None = None,
    workflow_forbidden_found: list[str] | None = None,
) -> dict:
    forbidden_found = forbidden_found or []
    workflow_forbidden_found = workflow_forbidden_found or []
    return {
        "result": "fail" if forbidden_found or workflow_forbidden_found else "pass",
        "allowed_services": list(OFFICIAL_SERVICES),
        "service_registry": [{"service_id": service, "status": "active"} for service in OFFICIAL_SERVICES],
        "forbidden_role_scan": {"blocked_roles": list(FORBIDDEN_ROLES), "forbidden_found": forbidden_found},
        "workflow_node_scan": {"blocked_roles": list(FORBIDDEN_ROLES), "forbidden_found": workflow_forbidden_found},
    }
