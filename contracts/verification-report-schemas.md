contract_id: CONTRACT-VERIFICATION-REPORT-SCHEMAS
status: frozen
frozen_at: 2026-04-29
freeze_review_ref: reviews/contract-freeze-verification-report-schemas-design-fix-2026-04-30.yaml
consumers:
  - WI-001
  - WI-002
  - WI-003
  - WI-004
  - WI-005
  - WI-006
  - WI-007
  - WI-008
  - WI-009
  - WI-010
requirement_refs:
  - REQ-001
  - REQ-002
  - REQ-003
  - REQ-004
  - REQ-005
  - REQ-006
  - REQ-007
  - REQ-008
  - REQ-009
  - REQ-010
  - REQ-011
  - REQ-012
  - REQ-013
  - REQ-014
  - REQ-015
  - REQ-016
  - REQ-017
  - REQ-018
  - REQ-019
  - REQ-020
  - REQ-021
  - REQ-022
  - REQ-023
  - REQ-024
  - REQ-025
  - REQ-026
  - REQ-027
  - REQ-028
  - REQ-029
  - REQ-030
  - REQ-031
  - REQ-032

reading_contract:
  - "Design 阶段 frozen contract；实现测试、report writer、CI artifact 或 review 证据时必须读取。"
  - "本契约只定义每个 report 最少要证明什么；不改变 TC 场景和验收义务。"

report_envelope:
  fields: ["report_id", "generated_at", "generated_by", "git_revision", "work_item_refs", "test_case_refs", "fixture_refs", "result", "checked_requirements", "checked_acceptances", "checked_invariants", "artifact_refs", "failures", "residual_risk"]
  required: ["report_id", "generated_at", "generated_by", "git_revision", "work_item_refs", "test_case_refs", "fixture_refs", "result", "checked_requirements", "checked_acceptances", "checked_invariants", "artifact_refs", "failures", "residual_risk", "schema_version", "checked_fields", "fixture_inputs", "actual_outputs", "guard_results"]
  result_values: ["pass", "fail"]
  invariant: "result pass 必须代表所有 P0 断言通过；若 failures 非空，结果必须为 fail。"
  common_payload:
    schema_version: string
    checked_fields: "array<string>; every field asserted by this report"
    fixture_inputs: "object; exact fixture ids and relevant input values"
    actual_outputs: "object; observed state/artifact/read model/report writer output"
    guard_results: "array<{guard: string, input_ref: string, expected: string, actual: string, result: pass|fail}>"
    runbook_trace: "array<{step: string, actor: string, input_ref: string, output_ref: string, result: pass|fail}>"
    view_projection_results: "array<{view: string, expected: string, actual: string, result: pass|fail}>"
    failures: "array<{code: string, message: string, evidence_ref: string}>"
    residual_risk: "array<string>"

reports:
  scope_boundary_report.json:
    wi: WI-001
    tc: TC-ACC-001-01
    assertions: ["Web-only", "个人使用", "A 股闭环", "禁用入口扫描"]
  registry_validation_report.json:
    wi: WI-001
    tc: TC-ACC-002-01
    assertions: ["9 个 Agent", "8 个服务", "禁用角色不可调度"]
  agent_capability_contract_report.json:
    wi: WI-001
    tc: TC-ACC-003-01
    assertions: ["profile 字段", "SOP", "rubric", "失败处理", "评价", "团队页九个 Agent 卡面", "版本/质量/越权记录"]
  memory_boundary_report.json:
    wi: WI-001
    tc: TC-ACC-004-01
    assertions: ["透明读", "Gateway 写", "runner 无写凭证", "财务敏感例外", "Memory 元数据抽取", "Memory 不是事实源", "ContextSlice 注入/拒绝留痕"]
  collaboration_trace_report.json:
    wi: WI-001
    tc: TC-ACC-005-01
    assertions: ["session", "run", "command", "event", "handoff", "artifact trace"]
  security_privacy_report.json:
    wi: WI-001
    tc: TC-ACC-031-01
    assertions: ["加密", "日志脱敏", "只读 DB", "敏感字段 allow/deny"]
  requirement_structure_report.json:
    wi: WI-001
    tc: TC-ACC-032-01
    assertions: ["REQ/ACC/VO 正文定义", "TC 覆盖", "appendix 无正式 ID"]
  s0_s7_workflow_report.json:
    wi: WI-002
    tc: TC-ACC-008-01
    assertions: ["S0-S7", "责任", "输入输出", "节点状态", "Reopen Event"]
  data_quality_degradation_report.json:
    wi: WI-002
    tc: TC-ACC-009-01
    assertions: ["三档质量", "关键字段最低有效分", "fallback", "cache", "conflict", "execution_core 阻断"]
  service_boundary_report.json:
    wi: WI-002
    tc: TC-ACC-010-01
    assertions: ["服务无审批权", "服务无否决权", "服务无最终投资判断", "服务无真实交易权"]
  market_state_report.json:
    wi: WI-002
    tc: TC-ACC-011-01
    assertions: ["Market State 默认生效", "因子建议", "Macro override 留痕"]
  config_governance_report.json:
    wi: WI-002
    tc: TC-ACC-030-01
    assertions: ["低中影响自动验证", "高影响审批", "新任务/新 attempt 生效", "DefaultContextBinding/MemoryCollection/AgentCapability 版本快照"]
  decision_service_report.json:
    wi: WI-008
    tc: TC-ACC-018-01
    assertions: ["DecisionPacket 装配", "S4 输入完整性", "DecisionGuardResult", "偏离守卫", "Owner 例外候选或重开建议", "服务无越权"]
  topic_registration_report.json:
    wi: WI-003
    tc: TC-ACC-012-01
    assertions: ["开放来源注册", "supporting evidence 不直入正式 IC"]
  topic_queue_report.json:
    wi: WI-003
    tc: TC-ACC-013-01
    assertions: ["硬门槛", "四维评分", "IC 并发 3", "全局并发 5", "P0 抢占"]
  ic_context_package_report.json:
    wi: WI-003
    tc: TC-ACC-014-01
    assertions: ["ICContextPackage 一等 artifact", "ICChairBrief 一等 artifact", "Dossier 投影", "Chair Brief 不预设结论", "证据可解析"]
  analyst_memo_report.json:
    wi: WI-007
    tc: TC-ACC-015-01
    assertions: ["四 Analyst 独立 profile", "Memo 外壳", "role_payload"]
  consensus_action_report.json:
    wi: WI-007
    tc: TC-ACC-016-01
    assertions: ["consensus 公式", "action_conviction 公式", "阈值", "低行动强度不执行"]
  debate_dissent_report.json:
    wi: WI-007
    tc: TC-ACC-017-01
    assertions: ["debate skipped", "有界辩论", "hard dissent", "中等共识保留异议进入风控", "低共识阻断"]
  cio_optimizer_report.json:
    wi: WI-008
    tc: TC-ACC-018-01
    assertions: ["Chair", "Synthesis", "Decision", "偏离计算", "CIO 禁止越权"]
  risk_owner_exception_report.json:
    wi: WI-008
    tc: TC-ACC-019-01
    assertions: ["Risk 三状态", "rejected 阻断", "conditional_pass 审批", "超时"]
  paper_account_report.json:
    wi: WI-009
    tc: TC-ACC-020-01
    assertions: ["100 万 CNY 空仓初始化", "基线"]
  paper_execution_report.json:
    wi: WI-009
    tc: TC-ACC-021-01
    assertions: ["VWAP/TWAP", "窗口", "费用", "T+1", "未成交/过期"]
  position_disposal_report.json:
    wi: WI-009
    tc: TC-ACC-022-01
    assertions: ["PositionDisposalTask 一等 artifact", "Dossier 投影", "持仓异常触发处置", "不跳过风控", "不直接执行"]
  web_command_routing_report.json:
    wi: WI-004
    tc: TC-ACC-006-01
    assertions: ["五个一级主导航且不含团队", "简体中文高端浅色卡面", "治理下 Agent 团队工作区", "三层视图", "Request Brief", "阻断直达动作"]
  governance_task_report.json:
    wi: WI-004
    tc: TC-ACC-007-01
    assertions: ["Task/Approval/manual_todo 分离", "审批材料完整", "Agent 能力草案治理", "禁用入口"]
  team_capability_config_report.json:
    wi: WI-004
    tc: TC-ACC-007-01
    assertions: ["TeamReadModel", "AgentProfileReadModel", "AgentCapabilityConfigReadModel", "草案转 Governance Change", "低中自动验证", "高影响 Owner 审批", "in-flight AgentRun 不热改"]
  finance_asset_boundary_report.json:
    wi: WI-005
    tc: TC-ACC-023-01
    assertions: ["全资产档案", "基金/黄金行情", "房产估值", "非 A 股隔离"]
  performance_attribution_report.json:
    wi: WI-005
    tc: TC-ACC-024-01
    assertions: ["收益", "风险", "成本", "滑点", "因子", "IC/证据质量"]
  cfo_governance_report.json:
    wi: WI-005
    tc: TC-ACC-025-01
    assertions: ["CFO Interpretation", "Governance Proposal", "Reflection Assignment"]
  factor_research_report.json:
    wi: WI-005
    tc: TC-ACC-026-01
    assertions: ["因子准入", "独立验证", "登记", "监控", "无回测依赖"]
  researcher_workflow_report.json:
    wi: WI-005
    tc: TC-ACC-027-01
    assertions: ["每日简报", "Research Package", "Topic/Knowledge/Prompt/Skill Proposal", "Memory capture/review/digest/organize"]
  reflection_learning_report.json:
    wi: WI-005
    tc: TC-ACC-028-01
    assertions: ["归因触发", "CFO 范围", "Agent 一稿", "Memory/Knowledge 晋升", "Researcher 晋升", "无热改"]
  devops_incident_report.json:
    wi: WI-006
    tc: TC-ACC-029-01
    assertions: ["incident", "degradation", "recovery", "Risk handoff", "成本观测非硬验收"]

report_payload_contracts:
  scope_boundary_report.json:
    required_payload_fields: ["scope_registry", "forbidden_entry_scan", "ui_entry_scan", "api_entry_scan"]
  registry_validation_report.json:
    required_payload_fields: ["agent_registry", "service_registry", "forbidden_role_scan"]
  agent_capability_contract_report.json:
    required_payload_fields: ["capability_profiles", "team_read_model", "agent_profile_read_models", "skill_package_manifests", "prompt_versions", "context_snapshot_versions", "sop_checks", "rubric_checks", "failure_policy_checks", "quality_metrics", "denied_action_records"]
  memory_boundary_report.json:
    required_payload_fields: ["transparent_read_paths", "gateway_write_paths", "runner_write_denials", "finance_sensitive_allow_deny", "memory_items", "memory_versions", "memory_relations", "memory_collections", "memory_extraction_results", "context_injection_decisions", "denied_memory_refs", "memory_not_fact_source_guards"]
  collaboration_trace_report.json:
    required_payload_fields: ["sessions", "agent_runs", "commands", "events", "handoffs", "artifact_lineage", "gateway_write_records", "runbook_trace", "view_projection_results"]
  security_privacy_report.json:
    required_payload_fields: ["encrypted_fields_check", "plaintext_log_scan", "readonly_db_check", "sensitive_access_events"]
  requirement_structure_report.json:
    required_payload_fields: ["req_acc_vo_scan", "tc_coverage", "appendix_formal_id_scan"]
  s0_s7_workflow_report.json:
    required_payload_fields: ["stage_outputs", "responsible_roles", "node_statuses", "reopen_events", "superseded_artifacts", "stop_conditions"]
  data_quality_degradation_report.json:
    required_payload_fields: ["data_request_schema", "component_scores", "quality_band_actions", "critical_field_minimums", "fallback_attempts", "cache_decision_policy", "conflict_resolution_report", "execution_core_freshness_gate", "blocked_decisions"]
  service_boundary_report.json:
    required_payload_fields: ["service_outputs", "forbidden_authority_check", "governance_owner_check"]
  market_state_report.json:
    required_payload_fields: ["default_effective_state", "ic_context_binding", "factor_weight_effect", "collaboration_mode", "macro_override_audit"]
  config_governance_report.json:
    required_payload_fields: ["impact_levels", "auto_validation", "transition_guards", "governance_states", "context_snapshot_binding", "default_context_bindings", "memory_collection_versions", "agent_capability_change_versions", "effective_scope", "in_flight_snapshot_unchanged"]
  topic_registration_report.json:
    required_payload_fields: ["registered_sources", "supporting_evidence_only_actions", "candidate_states", "formal_ic_states", "rejected_reasons"]
  topic_queue_report.json:
    required_payload_fields: ["hard_gate_results", "priority_score_components", "priority_weighted_totals", "active_ic_slots", "global_workflows", "preemption_events", "gate_checks"]
  ic_context_package_report.json:
    required_payload_fields: ["ic_context_artifact", "chair_brief_artifact", "shared_context", "market_state_ref", "service_result_refs", "role_attachments", "chair_brief", "chair_brief_no_preset_decision", "dossier_projection", "evidence_resolution"]
  analyst_memo_report.json:
    required_payload_fields: ["profile_versions", "memo_envelopes", "role_payloads", "schema_validation", "independence_checks"]
  consensus_action_report.json:
    required_payload_fields: ["formula_inputs", "population_std_outputs", "dominant_direction_share", "expected_outputs", "actual_outputs", "threshold_decisions"]
  debate_dissent_report.json:
    required_payload_fields: ["debate_skipped", "debate_round_inputs", "debate_round_outputs", "debate_manager_process_fields", "cio_agenda_synthesis", "collaboration_commands", "view_updates", "handoff_packets", "retained_hard_dissent", "risk_review_required", "recomputed_consensus", "recomputed_action_conviction", "execution_blocked", "runbook_trace"]
  decision_service_report.json:
    required_payload_fields: ["input_artifact_refs", "decision_packet", "input_completeness", "decision_guard_result", "single_name_deviation", "portfolio_active_deviation", "exception_candidate_or_reopen", "forbidden_service_authority_check", "failure_path_cases", "view_projection_results", "runbook_trace"]
  cio_optimizer_report.json:
    required_payload_fields: ["chair_brief", "debate_synthesis", "decision_packet", "decision_guard_result", "forbidden_cio_actions_denied", "deviation_reason", "single_name_deviation", "portfolio_active_deviation", "owner_exception_or_rework"]
  risk_owner_exception_report.json:
    required_payload_fields: ["risk_states", "approval_packet", "repairability", "reopen_target", "owner_timeout", "timeout_disposition_by_type", "blocked_execution", "bypass_attempt_denied"]
  paper_account_report.json:
    required_payload_fields: ["initial_cash", "positions", "cost_basis", "baseline_returns", "risk_budget_baseline"]
  paper_execution_report.json:
    required_payload_fields: ["order_windows", "minute_bar_fixture", "pricing_method", "vwap_or_twap_calculation", "price_range_check", "fill_status", "fees", "taxes", "slippage", "t_plus_one_state"]
  position_disposal_report.json:
    required_payload_fields: ["trigger_events", "position_disposal_task_artifact", "position_disposal_tasks", "dossier_projection", "priority_escalation", "risk_review_guard", "execution_core_guard", "direct_execution_denied"]
  web_command_routing_report.json:
    required_payload_fields: ["nav_scan", "chinese_ui_scan", "premium_light_theme_assertions", "request_brief_preview_flow", "view_layers", "governance_agent_team_assertions", "design_preview_refs", "forbidden_action_ui_denials", "read_model_guard_denials", "api_guard_denials", "screenshot_refs"]
  governance_task_report.json:
    required_payload_fields: ["task_center_states", "approval_center_items", "manual_todo_isolation", "agent_capability_draft_states", "governance_change_links", "risk_rejected_ui_guard", "execution_core_ui_guard", "non_a_asset_ui_guard", "agent_capability_hot_patch_denial", "design_preview_refs"]
  team_capability_config_report.json:
    required_payload_fields: ["team_read_model", "agent_cards", "agent_profile_read_models", "capability_config_read_model", "capability_draft_submission", "impact_triage", "auto_validation_refs", "owner_approval_refs", "effective_scope", "in_flight_agent_run_snapshot_unchanged", "hot_patch_denials", "screenshot_refs"]
  finance_asset_boundary_report.json:
    required_payload_fields: ["asset_registry", "fund_gold_quotes", "real_estate_manual_valuation", "non_a_asset_trade_denials"]
  performance_attribution_report.json:
    required_payload_fields: ["return_attribution", "risk_attribution", "cost_slippage", "factor_contribution", "ic_quality", "evidence_quality"]
  cfo_governance_report.json:
    required_payload_fields: ["cfo_interpretation", "governance_proposal", "reflection_assignment", "attribution_trigger", "high_impact_owner_approval", "new_task_or_attempt_effective_scope"]
  factor_research_report.json:
    required_payload_fields: ["research_admission", "sample_context", "independent_validation", "factor_registry", "monitoring", "no_backtest_dependency"]
  researcher_workflow_report.json:
    required_payload_fields: ["daily_brief", "research_package", "topic_proposal", "memory_capture", "memory_review_digest", "memory_organize_suggestions", "memory_relation_applications", "knowledge_proposal", "prompt_skill_proposal", "impact_validation"]
  reflection_learning_report.json:
    required_payload_fields: ["attribution_trigger", "cfo_scope_confirmation", "responsible_agent_draft", "memory_item_refs", "knowledge_promotion_refs", "researcher_promotion", "impact_triage", "auto_validation_or_owner_approval", "new_task_or_attempt_only_effect", "no_hot_patch_guard"]
  devops_incident_report.json:
    required_payload_fields: ["routine_checks", "incidents", "health_signals", "severity_classification", "degradation_actions", "recovery_plan", "risk_reports", "investment_resume_denied_until_guard", "cost_observability_only"]

pass_fail_rule:
  pass_requires:
    - "report_envelope.required 全部存在"
    - "report_payload_contracts 中 required_payload_fields 全部存在且非空，除非 fixture 明确不适用并记录 reason"
    - "所有 guard_results.result 均为 pass"
    - "failures 为空"
  fail_requires:
    - "任一 P0 guard、schema validation 或 forbidden action assertion 失败时 result 必须为 fail"

fixture_bindings:
  FX-HAPPY-PATH-BUY-A-SHARE: ["s0_s7_workflow_report.json", "ic_context_package_report.json", "decision_service_report.json", "paper_execution_report.json", "performance_attribution_report.json"]
  FX-HIGH-CONSENSUS-HARD-DISSENT: ["debate_dissent_report.json", "risk_owner_exception_report.json"]
  FX-MEDIUM-CONSENSUS-HARD-DISSENT: ["debate_dissent_report.json", "risk_owner_exception_report.json"]
  FX-RISK-REJECTED-REOPEN: ["risk_owner_exception_report.json", "s0_s7_workflow_report.json"]
  FX-EXECUTION-CORE-INVALID: ["data_quality_degradation_report.json", "paper_execution_report.json", "web_command_routing_report.json"]
  FX-HIGH-IMPACT-GOVERNANCE: ["config_governance_report.json", "governance_task_report.json", "team_capability_config_report.json"]
  FX-NON-A-ASSET-MANUAL-TASK: ["finance_asset_boundary_report.json", "governance_task_report.json"]
  FX-PROMPT-NEW-TASKS-ONLY: ["config_governance_report.json", "researcher_workflow_report.json", "reflection_learning_report.json", "team_capability_config_report.json"]
  FX-AGENT-CAPABILITY-DRAFT: ["agent_capability_contract_report.json", "config_governance_report.json", "governance_task_report.json", "team_capability_config_report.json"]
  FX-AGENT-COLLABORATION-PROTOCOL: ["collaboration_trace_report.json", "agent_capability_contract_report.json", "team_capability_config_report.json"]
  FX-MEMORY-CAPTURE-ORGANIZE-PROMOTE: ["memory_boundary_report.json", "researcher_workflow_report.json", "reflection_learning_report.json", "config_governance_report.json"]
  FX-MEMORY-RECALL-NOT-AUTHORITY: ["memory_boundary_report.json", "collaboration_trace_report.json"]
  FX-MEMORY-FINANCE-RESTRICTED: ["memory_boundary_report.json", "security_privacy_report.json"]

failure_evidence_rules:
  - "report writer 不得只输出字段存在性；必须写明 fixture 输入、guard 判断和实际状态转移。"
  - "禁止入口类测试必须同时证明 UI/read model 不展示入口、API/domain guard 拒绝请求。"
  - "安全类测试必须同时证明允许路径和拒绝路径。"
  - "治理生效类测试必须证明旧 in-flight ContextSnapshot 未改变。"
  - "Memory/Knowledge 召回必须证明以 fenced background/context 形式注入，不能作为正式 artifact 事实源或直接推进业务状态。"
  - "ProcessArchive 只能追溯来源，不能未经 Memory/Knowledge/Governance 晋升直接进入 DefaultContext。"
  - "Decision Service 证据必须证明服务只装配/校验/建议，不直接替 CIO、Risk、Owner 或 workflow 做最终裁决。"
  - "团队页能力配置证据必须证明保存动作只生成草案和 Governance Change，且旧 in-flight AgentRun 的 ContextSnapshot 未改变。"
  - "R8 runbook 类测试必须证明至少一个 trigger -> command/service/AgentRun -> artifact/event/handoff -> read model projection 的完整链路。"
  - "前端预览类证据必须引用 design-previews/frontend-workbench 路径；Design approved 前不得只用 placeholder screenshot。"
