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
