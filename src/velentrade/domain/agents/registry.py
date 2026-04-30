from __future__ import annotations

from collections import OrderedDict

from velentrade.domain.agents.models import (
    AuthorityPolicy,
    CapabilityProfile,
    ContextPolicy,
    EscalationPolicy,
    EvaluationPolicy,
    FailurePolicy,
    OutputContract,
    ToolPolicy,
    WritePolicy,
)


OFFICIAL_AGENT_IDS = (
    "cio",
    "cfo",
    "macro_analyst",
    "fundamental_analyst",
    "quant_analyst",
    "event_analyst",
    "risk_officer",
    "investment_researcher",
    "devops_engineer",
)

FORBIDDEN_ROLES = (
    "strategy_manager",
    "rules_path",
    "performance_analyst",
    "performance_analyst_agent",
)

OFFICIAL_SERVICES = (
    "data_collection_quality",
    "market_state_evaluation",
    "factor_engine",
    "valuation_engine",
    "portfolio_optimization",
    "risk_engine",
    "trade_execution",
    "performance_attribution_evaluation",
)


def _profile(
    agent_id: str,
    display_name: str,
    role: str,
    mission: str,
    semantic_domains: list[str],
    artifacts: list[str],
    commands: list[str],
    skills: list[str],
    payload_schema: str = "generic_payload",
    can_read_finance_raw: bool = False,
) -> CapabilityProfile:
    denied = ["direct_business_db_write", "hot_patch_context_snapshot"]
    context_denied = ["direct_business_db_write"]
    if not can_read_finance_raw:
        context_denied.append("finance_sensitive_raw")
    return CapabilityProfile(
        agent_id=agent_id,
        display_name=display_name,
        role=role,
        profile_version="1.0.0",
        status="active",
        mission=mission,
        authority=AuthorityPolicy(
            proposal_rights=["append_comment", "submit_artifact", "submit_command"],
            semantic_lead_domains=semantic_domains,
            forbidden_actions=denied
            + [
                "override_risk_rejected",
                "create_agent_run_without_admission",
                "use_memory_as_business_fact",
            ],
        ),
        default_context_policy=ContextPolicy(
            always_include=["task_brief", "context_snapshot"],
            stage_scoped=["current_stage_artifacts"],
            on_demand_retrieval=["knowledge", "memory", "process_archive"],
            denied=context_denied,
        ),
        tool_policy=ToolPolicy(
            db_read_views=["readonly_business_view", "artifact_read_model"],
            file_scopes=["business_materials", "active_skill_packages"],
            network_policy=["approved_public_sources"],
            terminal_policy=["readonly_diagnostics"],
            service_result_read=["data_readiness", "market_state", "risk", "attribution"],
            skill_packages=skills,
        ),
        write_policy=WritePolicy(
            artifact_types=artifacts,
            command_types=commands,
            comment_types=["view_update", "evidence_comment"],
            proposal_types=["knowledge", "prompt", "skill", "config"],
        ),
        output_contracts=[OutputContract(artifacts[0], f"{artifacts[0]}_schema", payload_schema)],
        sop=[
            "读取 ContextSlice 中的正式 artifact 和 fenced background。",
            "明确证据、反证、开放问题和角色边界。",
            "通过 Authority Gateway 提交 typed 输出，不直接改业务状态。",
        ],
        failure_policy=[
            FailurePolicy("insufficient_context", "提交 request_evidence 或 request_data。"),
            FailurePolicy("permission_denied", "停止写入并记录 guard_failed event。"),
        ],
        escalation_policy=[
            EscalationPolicy("无法在当前阶段修复", "request_reopen"),
            EscalationPolicy("需要人工裁决", "request_owner_input"),
        ],
        evaluation_policy=EvaluationPolicy(
            metrics=["schema_pass_rate", "evidence_quality", "role_boundary_pass"],
            feedback_sources=["attribution_service", "risk_review", "owner_feedback"],
        ),
        default_model_profile="balanced",
        default_tool_profile_id="readonly-basic",
        default_skill_packages=skills,
    )


def build_agent_capability_profiles() -> "OrderedDict[str, CapabilityProfile]":
    rows = [
        ("cio", "CIO", "cio", "IC 语义主席和投资收口者。", ["investment_ic"], ["CIODecisionMemo"], ["ask_question", "request_view_update", "request_reopen"], ["cio-decision-synthesis"], "cio_payload", False),
        ("cfo", "CFO", "cfo", "财务规划、归因解释、治理签发和反思分派者。", ["finance", "reflection"], ["CFOInterpretation"], ["request_reflection", "propose_config_change"], ["cfo-governance"], "cfo_payload", True),
        ("macro_analyst", "Macro Analyst", "macro_analyst", "宏观、政策、流动性和市场状态解释。", ["macro_analysis"], ["AnalystMemo"], ["request_data", "request_evidence"], ["macro-regime-analysis"], "macro_payload", False),
        ("fundamental_analyst", "Fundamental Analyst", "fundamental_analyst", "公司质量、财务质量、盈利和估值分析。", ["fundamental_analysis"], ["AnalystMemo"], ["request_data", "request_evidence"], ["fundamental-quality-review"], "fundamental_payload", False),
        ("quant_analyst", "Quant Analyst", "quant_analyst", "量价、趋势、择时和因子解释。", ["quant_analysis"], ["AnalystMemo"], ["request_data", "request_service_recompute"], ["quant-signal-review"], "quant_payload", False),
        ("event_analyst", "Event Analyst", "event_analyst", "公告、新闻、资金流和催化窗口分析。", ["event_analysis"], ["AnalystMemo"], ["request_evidence", "request_source_health_check"], ["event-catalyst-assessment"], "event_payload", False),
        ("risk_officer", "Risk Officer", "risk_officer", "独立风险关口和业务风险裁决者。", ["risk_review"], ["RiskReviewReport"], ["request_reopen", "request_risk_impact_review"], ["risk-gate-review"], "risk_payload", False),
        ("investment_researcher", "Investment Researcher", "investment_researcher", "研究资料、知识资产和 Prompt/Skill 提案准备者。", ["research", "knowledge"], ["ResearchPackage"], ["request_evidence", "propose_knowledge_promotion", "propose_prompt_update", "propose_skill_update"], ["research-package-builder"], "research_payload", False),
        ("devops_engineer", "DevOps Engineer", "devops_engineer", "系统、数据源、执行环境和成本观测诊断者。", ["incident", "service_health"], ["IncidentReport"], ["report_incident", "request_degradation", "request_recovery_validation"], ["devops-incident-diagnostics"], "devops_payload", False),
    ]
    return OrderedDict(
        (agent_id, _profile(agent_id, display_name, role, mission, domains, artifacts, commands, skills, payload, can_read_finance_raw))
        for agent_id, display_name, role, mission, domains, artifacts, commands, skills, payload, can_read_finance_raw in rows
    )


def validate_agent_registry() -> dict:
    profiles = build_agent_capability_profiles()
    forbidden_found = [role for role in FORBIDDEN_ROLES if role in profiles]
    return {
        "result": "pass" if not forbidden_found and tuple(profiles) == OFFICIAL_AGENT_IDS else "fail",
        "allowed_agents": list(profiles),
        "blocked_roles": list(FORBIDDEN_ROLES),
        "forbidden_role_scan": {"forbidden_found": forbidden_found, "blocked_roles": list(FORBIDDEN_ROLES)},
        "workflow_node_scan": {"agent_nodes": list(profiles), "forbidden_found": forbidden_found},
    }


def build_team_read_model() -> dict:
    profiles = build_agent_capability_profiles()
    cards = []
    for profile in profiles.values():
        cards.append(
            {
                "agent_id": profile.agent_id,
                "display_name": profile.display_name,
                "role": profile.role,
                "status": profile.status,
                "profile_version": profile.profile_version,
                "skill_package_version": profile.default_skill_packages[0],
                "prompt_version": "1.0.0",
                "context_snapshot_version": "ctx-v1",
                "recent_quality_score": 1.0,
                "active_run_count": 0,
                "failure_count": 0,
                "denied_action_count": 0,
                "config_draft_entry": "governance_draft_only",
            }
        )
    return {
        "team_health": {
            "healthy_agent_count": len(cards),
            "active_agent_run_count": 0,
            "pending_draft_count": 0,
            "failed_or_denied_count": 0,
            "last_quality_window": "fixture",
        },
        "agent_cards": cards,
        "capability_drafts": [],
        "quality_alerts": [],
        "governance_links": ["/api/governance/changes"],
    }
