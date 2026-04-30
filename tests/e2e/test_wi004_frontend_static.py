from pathlib import Path


def test_frontend_source_contains_required_nav_and_no_top_level_team():
    source = Path("frontend/src/workbench.ts").read_text(encoding="utf-8")
    assert '"全景", "投资", "财务", "知识", "治理"' in source
    assert "Agent 团队" in source
    assert '"团队"' not in source


def test_frontend_reports_reference_design_previews_and_guard_denials():
    source = Path("frontend/src/workbench.ts").read_text(encoding="utf-8")
    assert "design-previews/frontend-workbench/00-shell-and-navigation.md" in source
    assert "risk_rejected_no_override" in source
    assert "execution_core_blocked_no_trade" in source
    assert "non_a_asset_no_trade" in source
    assert "agent_capability_hot_patch_denied" in source


def test_frontend_has_page_route_manifest_for_each_menu_and_drilldown():
    source = Path("frontend/src/workbench.ts").read_text(encoding="utf-8")
    app_source = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    for route in [
        '"/investment/:workflowId"',
        '"/investment/:workflowId/trace"',
        '"/finance"',
        '"/knowledge"',
        '"/governance/team"',
        '"/governance/team/:agentId"',
        '"/governance/team/:agentId/config"',
        '"/governance/approvals/:approvalId"',
    ]:
        assert route in source

    assert "resolveWorkbenchRoute" in app_source
    assert "renderWorkbenchPage" in app_source
