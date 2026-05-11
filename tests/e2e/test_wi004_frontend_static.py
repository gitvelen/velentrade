from pathlib import Path


def test_frontend_source_contains_required_nav_and_no_top_level_team():
    source = Path("frontend/src/workbench.ts").read_text(encoding="utf-8")
    assert '"全景", "投资", "财务", "知识", "治理"' in source
    assert "governanceModules: [\"待办\", \"团队\", \"变更\", \"健康\", \"审计\"]" in source
    assert "Agent 团队" not in source


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


def test_free_form_command_is_topbar_drawer_not_page_brief_block():
    app_source = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    assert "command-drawer" in app_source
    assert "command-panel" in app_source
    assert "aria-expanded={commandOpen}" in app_source
    assert "command-preview" not in app_source
    assert "Request Brief" not in app_source


def test_owner_default_view_removes_internal_terms_and_explanatory_subtitles():
    app_source = Path("frontend/src/main.tsx").read_text(encoding="utf-8")
    workbench_source = Path("frontend/src/workbench.ts").read_text(encoding="utf-8")

    for forbidden in [
        "待处理、风险、审批和系统状态",
        "机会池、IC 队列、硬门槛与 Dossier 入口",
        "全资产档案、现金流、风险预算和人工待办",
        "研究资料、经验、关系和上下文注入",
    ]:
        assert forbidden not in app_source

    for forbidden in ["Request Brief", "Workflow Scheduling Center", "supporting_evidence_only"]:
        assert forbidden not in app_source

    assert "display" in workbench_source
    assert "只做研究，不进入审批或交易" in workbench_source


def test_knowledge_and_investment_owner_copy_answers_validation_questions():
    app_source = Path("frontend/src/main.tsx").read_text(encoding="utf-8")
    frontend_source = app_source + Path("frontend/src/workbench.ts").read_text(encoding="utf-8")

    for required in [
        "健康接口未连接，不能判断真实降级原因。",
        "恢复待验证",
        "经验记录",
        "保存经验",
        "资料包来源：",
        "资料关系",
        "整理建议",
        "应用整理建议",
        "当前 S3：硬异议保留，需先补证并交风控复核",
        "执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因",
    ]:
        assert required in frontend_source

    for forbidden in ["记忆工作区", "捕获记忆", "应用组织建议", "今日影响：", "关系图", "数据获取"]:
        assert forbidden not in app_source


def test_frontend_theme_uses_approved_premium_light_tokens():
    styles = Path("frontend/src/styles.css").read_text(encoding="utf-8")

    for token in ["#f4f0e8", "#20262d", "#247564", "#2f5f9f", "#b08a3c", "#b84e61"]:
        assert token in styles

    assert "position: sticky" in styles
    assert "backdrop-filter: blur(16px)" in styles
    assert "command-panel" in styles
    assert ".compact-dossier-header" in styles
    assert "max-height: 44px" in styles


def test_vite_dev_server_proxies_api_calls_to_fastapi():
    config = Path("frontend/vite.config.ts").read_text(encoding="utf-8")

    assert "proxy" in config
    assert '"/api"' in config
    assert "VELENTRADE_API_PROXY_TARGET" in config
    assert '"http://127.0.0.1:8000"' in config
