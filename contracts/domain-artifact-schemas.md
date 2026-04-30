contract_id: CONTRACT-DOMAIN-ARTIFACT-SCHEMAS
status: frozen
frozen_at: 2026-04-29
freeze_review_ref: reviews/contract-freeze-domain-artifact-schemas-design-fix-2026-04-30.yaml
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
requirement_refs:
  - REQ-003
  - REQ-004
  - REQ-005
  - REQ-006
  - REQ-007
  - REQ-008
  - REQ-009
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

reading_contract:
  - "Design 阶段 frozen contract；实现 domain、artifact ledger、collaboration、memory/knowledge、report fixture 时必须读取。"
  - "业务状态、artifact 字段、Memory/Knowledge 边界、stage guard reason code 以本文件为跨 WI 共享边界。"
  - "本文件不新增正式需求；冲突时以 spec.md 为准并回写 Design/Requirement。"

schema_notation:
  id_type: "string, stable opaque id"
  timestamp_type: "ISO-8601 UTC string"
  required_rule: "schema.required 中字段必须非空；未列字段默认可省略但不能改变业务语义"
  score_range: "number 0..1 unless field name says -5..+5 or _pp"
  evidence_ref_type: "string id or URI pointing to artifact/data/source ref"
  payload_rule: "Artifact.payload 必须符合 artifact_type 对应 schema，且写入时记录 schema_version"
  enum_rule: "枚举字段未知值视为 schema validation failed"

artifact_envelope:
  fields: ["artifact_id", "artifact_type", "workflow_id", "attempt_no", "trace_id", "producer", "producer_type", "source_refs", "created_at", "status", "summary", "evidence_refs", "decision_refs", "schema_version", "payload"]
  required: ["artifact_id", "artifact_type", "workflow_id", "attempt_no", "trace_id", "producer", "producer_type", "created_at", "status", "schema_version", "payload"]
  status_values: ["draft", "submitted", "accepted", "superseded", "rejected", "failed"]
  invariant: "旧 artifact 不删除；重开或修正只能生成新版本并标记旧版本 superseded。"
  field_types:
    artifact_id: id
    artifact_type: string
    workflow_id: id
    attempt_no: integer
    trace_id: id
    producer: string
    producer_type: "agent | service | workflow | owner"
    source_refs: "array<evidence_ref>"
    created_at: timestamp
    evidence_refs: "array<evidence_ref>"
    decision_refs: "array<evidence_ref>"
    schema_version: string
    payload: object

task_workflow:
  TaskEnvelope:
    fields: ["task_id", "task_type", "priority", "owner_role", "current_state", "blocked_reason", "reason_code", "artifact_refs", "created_at", "updated_at", "closed_at"]
    task_type_values: ["investment_workflow", "research_task", "finance_task", "governance_task", "agent_capability_change", "system_task", "manual_todo"]
  WorkflowStage:
    fields: ["workflow_id", "attempt_no", "stage", "node_status", "responsible_role", "input_artifact_refs", "output_artifact_refs", "reason_code", "started_at", "completed_at", "stage_version"]
    node_status_values: ["not_started", "running", "waiting", "blocked", "completed", "skipped", "failed"]
    invariant: "degraded、rejected、owner_timeout、unfilled、reopened 不作为 node_status。"
  ReopenEvent:
    fields: ["reopen_event_id", "workflow_id", "from_stage", "target_stage", "reason_code", "requested_by", "approved_by_or_guard", "invalidated_artifacts", "preserved_artifacts", "attempt_no", "created_at"]

data_service:
  RequestBrief:
    fields: ["goal", "scope", "asset_scope", "priority", "authorization_boundary", "time_budget", "success_standard", "block_conditions", "owner_confirmation_status"]
    owner_confirmation_status_values: ["draft", "confirmed", "edited", "canceled", "expired"]
  DataRequest:
    fields: ["request_id", "trace_id", "data_domain", "symbol_or_scope", "time_range", "required_usage", "freshness_requirement", "required_fields", "requesting_stage", "requesting_agent_or_service"]
    required_usage_values: ["display", "research", "decision_core", "execution_core", "finance_planning"]
  DataReadinessReport:
    fields: ["data_requests", "quality_score", "quality_band", "critical_field_results", "fallback_attempts", "cache_usage", "conflict_report_refs", "decision_core_status", "execution_core_status", "lineage_refs", "risk_constraints"]
    quality_band_values: ["normal", "degraded", "blocked"]
    execution_core_status_values: ["pass", "blocked"]
  ServiceResult:
    fields: ["input_artifact_refs", "data_quality_refs", "calculation_version", "output_quality_score", "limitations"]
  DecisionPacket:
    fields: ["packet_id", "workflow_id", "attempt_no", "context_snapshot_id", "decision_question", "input_artifact_refs", "analyst_stance_summary", "consensus_score", "action_conviction", "hard_dissent_state", "data_quality_summary", "market_state_ref", "valuation_refs", "optimizer_result_ref", "portfolio_context_ref", "risk_constraint_refs", "execution_feasibility", "reflection_hit_refs", "allowed_cio_actions", "evidence_refs", "packet_hash"]
    required: ["packet_id", "workflow_id", "attempt_no", "context_snapshot_id", "decision_question", "input_artifact_refs", "analyst_stance_summary", "consensus_score", "action_conviction", "data_quality_summary", "optimizer_result_ref", "risk_constraint_refs", "allowed_cio_actions", "evidence_refs", "packet_hash"]
    invariant: "DecisionPacket 是 CIO S4 消费的正式决策包；不得包含审批结论、Risk verdict 或执行释放指令。"
  DecisionGuardResult:
    fields: ["guard_id", "workflow_id", "attempt_no", "decision_packet_ref", "cio_decision_memo_ref", "input_completeness", "single_name_deviation_pp", "portfolio_active_deviation", "major_deviation", "low_action_conviction", "retained_hard_dissent", "data_quality_blockers", "optimizer_available", "owner_exception_candidate_ref", "reopen_recommendation_ref", "reason_codes", "created_at"]
    required: ["guard_id", "workflow_id", "attempt_no", "decision_packet_ref", "input_completeness", "major_deviation", "reason_codes", "created_at"]
    invariant: "DecisionGuardResult 只供 workflow guard、Dossier 和验证报告使用；不直接推进 workflow 状态。"
  DecisionExceptionCandidate:
    fields: ["candidate_id", "workflow_id", "attempt_no", "trigger_reason", "decision_packet_ref", "cio_decision_memo_ref", "deviation_summary", "comparison_options", "recommended_disposition", "risk_and_impact", "evidence_refs", "effective_scope", "owner_approval_ref"]
    required: ["candidate_id", "workflow_id", "attempt_no", "trigger_reason", "decision_packet_ref", "deviation_summary", "comparison_options", "risk_and_impact", "evidence_refs", "effective_scope"]
    invariant: "只是 Owner 审批材料候选；未进入 ApprovalRecord 前没有审批效力。"
  ReopenRecommendation:
    fields: ["recommendation_id", "workflow_id", "attempt_no", "from_stage", "target_stage", "reason_code", "invalidated_artifact_candidates", "preserved_artifact_candidates", "evidence_refs", "created_at"]
    required: ["recommendation_id", "workflow_id", "attempt_no", "from_stage", "target_stage", "reason_code", "evidence_refs", "created_at"]
    invariant: "只建议 Workflow 创建 ReopenEvent；不得自行重开。"

context_governance:
  ContextSnapshot:
    fields: ["context_snapshot_id", "snapshot_version", "created_at", "created_by", "effective_from", "effective_scope", "source_change_ref", "threshold_versions", "risk_parameter_versions", "approval_rule_versions", "prompt_versions", "skill_package_versions", "knowledge_item_versions", "memory_collection_versions", "default_context_versions", "model_route_version", "tool_permission_versions", "data_policy_version", "registry_versions", "service_degradation_policy_version", "execution_parameter_version", "content_hash", "frozen"]
    required: ["context_snapshot_id", "snapshot_version", "created_at", "effective_scope", "threshold_versions", "risk_parameter_versions", "approval_rule_versions", "prompt_versions", "skill_package_versions", "knowledge_item_versions", "memory_collection_versions", "default_context_versions", "model_route_version", "tool_permission_versions", "data_policy_version", "registry_versions", "service_degradation_policy_version", "execution_parameter_version", "content_hash", "frozen"]
    effective_scope_values: ["new_task", "new_attempt", "test_fixture"]
    invariant: "frozen=true 后不可更新；配置、Prompt、Skill、Knowledge、MemoryCollection 或 DefaultContext 变更只能生成新 ContextSnapshot，in-flight workflow/AgentRun 继续引用旧 id。"
  GovernanceChange:
    fields: ["change_id", "change_type", "impact_level", "state", "proposal_ref", "comparison_analysis_ref", "auto_validation_refs", "owner_approval_ref", "target_version_refs", "context_snapshot_id", "effective_scope", "rollback_plan_ref", "state_reason", "created_at", "updated_at", "decided_at", "effective_at"]
    required: ["change_id", "change_type", "impact_level", "state", "proposal_ref", "effective_scope", "created_at", "updated_at"]
    change_type_values: ["threshold", "risk_parameter", "approval_rule", "prompt", "skill_package", "default_context", "agent_capability", "tool_permission", "model_route", "knowledge_policy", "service_degradation_policy", "data_source_routing", "execution_parameter", "governance_impact_policy"]
    impact_level_values: ["low", "medium", "high"]
    state_values: ["draft", "triage", "assessment", "owner_pending", "approved", "effective", "rejected", "expired", "canceled", "activation_failed"]
    no_effect_terminal_values: ["rejected", "expired", "canceled", "activation_failed"]
  AgentCapabilityChangeDraft:
    fields: ["draft_id", "agent_id", "profile_version", "context_snapshot_id", "change_set", "diff_summary", "impact_level", "forced_high_reasons", "validation_plan_refs", "auto_validation_refs", "governance_change_ref", "owner_approval_ref", "effective_scope", "rollback_plan_ref", "state", "created_at", "updated_at"]
    required: ["draft_id", "agent_id", "profile_version", "context_snapshot_id", "change_set", "diff_summary", "impact_level", "effective_scope", "state", "created_at", "updated_at"]
    impact_level_values: ["low", "medium", "high"]
    effective_scope_values: ["new_task", "new_attempt"]
    state_values: ["draft", "triage", "assessment", "owner_pending", "approved", "effective", "rejected", "expired", "canceled", "activation_failed"]
    invariant: "团队页保存只能生成草案和 GovernanceChange；不得直接修改有效 Prompt、SkillPackage、工具权限、模型路由、默认上下文或在途 AgentRun。"

memory_knowledge:
  ProcessArchiveEntry:
    fields: ["archive_id", "source_object_type", "source_object_id", "workflow_id", "attempt_no", "stage", "summary", "source_refs", "created_at", "retention_policy"]
    required: ["archive_id", "source_object_type", "source_object_id", "summary", "source_refs", "created_at"]
    source_object_type_values: ["collaboration_event", "handoff_packet", "artifact", "agent_run", "verification_report"]
    invariant: "ProcessArchive 只用于追溯和摘要召回，不能直接进入 DefaultContext 或替代原始 source object。"
  MemoryItem:
    fields: ["memory_id", "memory_type", "owner_role", "producer_agent_id", "status", "current_version_id", "source_refs", "sensitivity", "pinned", "created_at", "updated_at"]
    required: ["memory_id", "memory_type", "status", "current_version_id", "source_refs", "sensitivity", "created_at"]
    memory_type_values: ["owner_observation", "research_note", "process_summary", "reflection_draft", "method_note", "external_excerpt"]
    status_values: ["draft", "validated_context", "archived", "superseded", "rejected"]
    sensitivity_values: ["public_internal", "finance_sensitive_summary", "finance_sensitive_raw", "security_sensitive"]
    invariant: "MemoryItem 是上下文/证据/可复用经验，不是业务事实源；与正式 artifact 冲突时 artifact 和 stage guard 优先。"
  MemoryVersion:
    fields: ["version_id", "memory_id", "version_no", "content_markdown", "payload", "created_by", "created_at", "superseded_by_version_id", "content_hash"]
    required: ["version_id", "memory_id", "version_no", "content_markdown", "payload", "created_by", "created_at", "content_hash"]
    invariant: "MemoryVersion append-only；修订必须新建版本并保留旧版本，禁止原地覆盖正文或 payload。"
  MemoryExtractionResult:
    fields: ["extraction_id", "memory_version_id", "extractor_version", "title", "tags", "mentions", "has_link", "has_task_list", "has_code", "has_incomplete_tasks", "symbol_refs", "artifact_refs", "agent_refs", "stage_refs", "source_refs", "sensitivity", "status", "created_at"]
    required: ["extraction_id", "memory_version_id", "extractor_version", "title", "tags", "mentions", "sensitivity", "status", "created_at"]
    status_values: ["pending", "succeeded", "failed", "not_required"]
    invariant: "抽取结果只能辅助筛选、路由和 ContextSlice 注入解释，不得自动生成业务状态或正式结论。"
  MemoryRelation:
    fields: ["relation_id", "source_memory_id", "target_ref", "relation_type", "reason", "evidence_refs", "created_by", "created_at"]
    required: ["relation_id", "source_memory_id", "target_ref", "relation_type", "reason", "created_by", "created_at"]
    relation_type_values: ["supports", "contradicts", "duplicates", "supersedes", "derived_from", "related_to", "promotes_to_knowledge", "used_by_context"]
    invariant: "Relation 是可追溯边，不删除历史边；归类错误通过新 relation 或 supersedes 表达。"
  MemoryCollection:
    fields: ["collection_id", "title", "filter_expression", "scope", "owner_agent_id", "purpose", "created_at", "updated_at"]
    required: ["collection_id", "title", "filter_expression", "scope", "purpose", "created_at"]
    scope_values: ["knowledge_page", "researcher_digest", "context_policy", "trace_debug", "test_fixture"]
    invariant: "filter_expression 只能引用 MemoryExtractionResult 白名单字段；Collection 只定义筛选视图，本身不提升事实权威。"
  KnowledgeItem:
    fields: ["knowledge_id", "knowledge_type", "status", "source_memory_refs", "source_artifact_refs", "validation_result_refs", "effective_scope", "governance_change_ref", "current_version_id", "created_at", "updated_at"]
    required: ["knowledge_id", "knowledge_type", "status", "source_memory_refs", "source_artifact_refs", "validation_result_refs", "effective_scope", "current_version_id", "created_at"]
    knowledge_type_values: ["methodology", "research_pattern", "prompt_background", "risk_checklist", "service_policy_note", "factor_note"]
    status_values: ["candidate", "validated", "effective_default_context", "superseded", "rejected"]
    invariant: "KnowledgeItem 必须从 Memory/Artifact/验证证据晋升；生效只通过 GovernanceChange 和新 ContextSnapshot。"
  DefaultContextBinding:
    fields: ["binding_id", "context_snapshot_id", "source_ref", "binding_type", "effective_scope", "impact_level", "governance_change_ref", "created_at"]
    required: ["binding_id", "context_snapshot_id", "source_ref", "binding_type", "effective_scope", "impact_level", "governance_change_ref", "created_at"]
    binding_type_values: ["knowledge_item", "memory_collection", "prompt_background", "skill_package", "checklist"]
    effective_scope_values: ["new_task", "new_attempt", "test_fixture"]
    invariant: "DefaultContextBinding 只能绑定已批准/已验证来源，且不得改变已在途 ContextSnapshot。"
  MemoryCapture:
    fields: ["capture_id", "source_type", "source_refs", "content_markdown", "payload", "suggested_memory_type", "sensitivity", "producer_agent_id", "created_at"]
    required: ["capture_id", "source_type", "source_refs", "content_markdown", "suggested_memory_type", "sensitivity", "producer_agent_id", "created_at"]
    source_type_values: ["owner_note", "agent_observation", "research_material", "reflection_output", "process_archive", "external_excerpt"]
    invariant: "Capture 是写入请求，不等于 validated memory；Authority Gateway 校验后才生成 MemoryItem/MemoryVersion。"
  MemoryOrganizeSuggestion:
    fields: ["suggestion_id", "target_memory_refs", "suggested_tags", "suggested_relations", "suggested_collections", "merge_or_duplicate_candidates", "reason", "risk_if_applied", "requires_gateway_write"]
    required: ["suggestion_id", "target_memory_refs", "reason", "requires_gateway_write"]
    invariant: "组织建议必须经 Gateway 产生 relation/collection/version 变更，不能直接改写原 MemoryVersion。"

collaboration_objects:
  CollaborationSession:
    fields: ["session_id", "workflow_id", "attempt_no", "stage", "mode", "semantic_lead_agent_id", "process_authority", "status", "context_snapshot_id", "participant_agent_ids", "opened_by", "opened_at", "closed_at", "close_reason"]
    required: ["session_id", "workflow_id", "attempt_no", "stage", "mode", "semantic_lead_agent_id", "process_authority", "status", "context_snapshot_id", "participant_agent_ids", "opened_by", "opened_at"]
    mode_values: ["ic_debate", "cross_agent_evidence", "research", "finance_reflection", "incident", "governance", "ad_hoc_support"]
    status_values: ["open", "active", "waiting", "synthesizing", "closed", "failed", "canceled", "expired"]
    invariant: "Session status does not express business outcomes such as Risk rejected, low consensus, data degraded, owner_timeout, or execution blocked."
  AgentRun:
    fields: ["agent_run_id", "workflow_id", "attempt_no", "stage", "session_id", "parent_run_id", "agent_id", "profile_version", "run_goal", "admission_type", "admission_decision_ref", "context_snapshot_id", "context_slice_id", "tool_profile_id", "skill_package_versions", "model_profile_id", "budget_tokens", "timeout_seconds", "status", "output_artifact_schema", "allowed_command_types", "started_at", "ended_at", "cost_tokens", "cost_estimate"]
    required: ["agent_run_id", "workflow_id", "attempt_no", "stage", "agent_id", "profile_version", "run_goal", "admission_type", "context_snapshot_id", "context_slice_id", "tool_profile_id", "status", "output_artifact_schema", "allowed_command_types"]
    admission_type_values: ["auto_accept", "semantic_accept", "domain_accept", "owner_approval"]
    status_values: ["queued", "running", "waiting", "completed", "failed", "canceled", "timed_out"]
    invariant: "AgentRun never owns workflow state transition permission; retry creates a new AgentRun."
  CollaborationCommand:
    fields: ["command_id", "command_type", "workflow_id", "attempt_no", "stage", "session_id", "source_agent_run_id", "source_agent_id", "target_agent_id_or_service", "payload", "requested_admission_type", "admission_status", "admission_reason", "result_ref", "created_at", "resolved_at"]
    required: ["command_id", "command_type", "workflow_id", "attempt_no", "stage", "source_agent_run_id", "source_agent_id", "target_agent_id_or_service", "payload", "requested_admission_type", "admission_status", "created_at"]
    command_type_values: ["ask_question", "request_view_update", "request_peer_review", "request_agent_run", "request_data", "request_evidence", "request_service_recompute", "request_source_health_check", "request_reopen", "request_pause_or_hold", "request_resume", "request_owner_input", "request_manual_todo", "request_reflection", "propose_knowledge_promotion", "propose_prompt_update", "propose_skill_update", "propose_config_change", "report_incident", "request_degradation", "request_recovery_validation", "request_risk_impact_review"]
    admission_status_values: ["pending", "accepted", "rejected", "owner_pending", "expired"]
  CollaborationEvent:
    fields: ["event_id", "event_type", "workflow_id", "attempt_no", "session_id", "agent_run_id", "command_id", "artifact_id", "trace_id", "payload", "created_at"]
    required: ["event_id", "event_type", "workflow_id", "attempt_no", "trace_id", "payload", "created_at"]
    event_type_values: ["session_opened", "agent_run_created", "agent_run_started", "tool_progress", "command_requested", "command_accepted", "command_rejected", "command_expired", "artifact_submitted", "handoff_created", "guard_failed", "sensitive_access_denied", "direct_write_denied", "session_closed"]
  HandoffPacket:
    fields: ["handoff_id", "workflow_id", "attempt_no", "from_stage", "to_stage_or_agent", "producer_agent_id_or_service", "source_artifact_refs", "summary", "open_questions", "blockers", "decisions_made", "invalidated_artifacts", "preserved_artifacts", "created_at"]
    required: ["handoff_id", "workflow_id", "attempt_no", "from_stage", "to_stage_or_agent", "producer_agent_id_or_service", "source_artifact_refs", "summary", "created_at"]
    invariant: "Handoff summarizes and links accepted artifacts; it never replaces original evidence or formal conclusions."
  ViewUpdate:
    fields: ["view_update_id", "source_artifact_ref", "producer_agent_id", "changed_fields", "reason", "evidence_refs", "supersedes_view_update_ref", "created_at"]
    invariant: "ViewUpdate can update an Agent's own current view but cannot overwrite the original artifact version."

investment_artifacts:
  TopicQueueEntry:
    fields: ["topic_id", "source_type", "symbol", "hard_gate_results", "priority_scores", "formal_ic_status", "rejected_reason"]
    required: ["topic_id", "source_type", "symbol", "hard_gate_results", "priority_scores", "formal_ic_status"]
    priority_score_fields: ["opportunity_strength", "data_completeness", "risk_urgency", "portfolio_relevance", "weighted_total"]
    priority_score_range: "0..5 for each dimension; weighted_total 0..5"
    formal_ic_status_values: ["candidate", "queued", "active", "rejected", "deferred"]
  ICContextPackage:
    fields: ["request_brief_ref", "data_readiness_ref", "market_state_ref", "service_result_refs", "portfolio_context_ref", "risk_constraint_refs", "research_package_refs", "reflection_hit_refs", "role_attachment_refs", "context_snapshot_id"]
    required: ["request_brief_ref", "data_readiness_ref", "market_state_ref", "service_result_refs", "portfolio_context_ref", "risk_constraint_refs", "research_package_refs", "role_attachment_refs", "context_snapshot_id"]
  AnalystMemo:
    source_contract: "spec.md memo_contract + analyst_role_payload_contract"
    required_envelope_fields: ["memo_id", "workflow_id", "attempt_no", "analyst_id", "role", "context_snapshot_id", "decision_question", "direction_score", "confidence", "evidence_quality", "hard_dissent", "thesis", "supporting_evidence_refs", "counter_evidence_refs", "key_risks", "applicable_conditions", "invalidation_conditions", "suggested_action_implication", "role_payload"]
    field_constraints:
      role: ["macro", "fundamental", "quant", "event"]
      direction_score: "integer -5..5"
      confidence: "number 0..1"
      evidence_quality: "number 0..1"
      hard_dissent: boolean
  DebateSummary:
    source_contract: "spec.md debate_contract"
    required_process_fields: ["rounds_used", "participants", "issues", "new_evidence_refs", "view_changes", "hard_dissent_present", "retained_hard_dissent", "risk_review_required", "recomputed_consensus_score", "recomputed_action_conviction", "stop_reason", "next_stage_decision"]
    required_cio_fields: ["agenda", "questions_asked", "synthesis", "resolved_issues", "unresolved_dissent", "chair_recommendation_for_next_stage", "semantic_lead_signature"]
    stop_reason_values: ["skipped_high_consensus", "max_rounds_reached", "no_new_evidence", "converged", "retained_hard_dissent", "hard_dissent_risk_handoff", "low_consensus_blocked", "low_action_conviction_blocked"]
  CIODecisionMemo:
    fields: ["decision", "decision_packet_ref", "target_symbol", "target_weight", "price_range", "urgency", "decision_rationale", "analyst_view_comparison", "consensus_action_summary", "optimizer_comparison", "deviation_reason", "risk_handoff_notes", "conditions", "invalidation_triggers", "monitoring_points", "evidence_refs", "reopen_target_if_any"]
    decision_values: ["buy", "sell", "hold", "observe", "no_action", "reopen"]
  RiskReviewReport:
    fields: ["review_result", "repairability", "risk_summary", "hard_blockers", "conditional_requirements", "data_quality_assessment", "portfolio_risk_assessment", "liquidity_execution_assessment", "cio_deviation_assessment", "hard_dissent_assessment", "owner_exception_required", "reopen_target_if_any", "reason_codes", "evidence_refs"]
    review_result_values: ["approved", "conditional_pass", "rejected"]
  ApprovalRecord:
    fields: ["approval_id", "approval_type", "approval_object_ref", "trigger_reason", "comparison_options", "recommended_decision", "risk_and_impact", "evidence_refs", "effective_scope", "timeout_policy", "decision", "decided_at"]
    decision_values: ["pending", "approved", "rejected", "request_changes", "expired"]
  PaperExecutionReceipt:
    fields: ["paper_order_id", "decision_memo_ref", "execution_window", "pricing_method", "market_data_refs", "fill_status", "fill_price", "fill_quantity", "fees", "taxes", "slippage", "t_plus_one_state", "attribution_ref"]
    required: ["paper_order_id", "decision_memo_ref", "execution_window", "pricing_method", "market_data_refs", "fill_status", "fees", "taxes", "slippage", "t_plus_one_state"]
    pricing_method_values: ["minute_vwap", "minute_twap"]
    fill_status_values: ["filled", "partial", "unfilled", "expired", "blocked"]
    t_plus_one_state_values: ["not_applicable", "locked_until_next_trading_day", "available_next_trading_day"]
  PaperAccount:
    fields: ["paper_account_id", "cash", "positions", "total_value", "cost_basis", "return", "drawdown", "risk_budget", "benchmark_ref", "created_at", "updated_at"]
    required: ["paper_account_id", "cash", "positions", "total_value", "cost_basis", "return", "drawdown", "risk_budget", "created_at", "updated_at"]
  PaperOrder:
    fields: ["paper_order_id", "workflow_id", "decision_memo_ref", "symbol", "side", "target_quantity_or_weight", "price_range", "urgency", "execution_core_snapshot_ref", "status", "created_at", "released_at"]
    required: ["paper_order_id", "workflow_id", "decision_memo_ref", "symbol", "side", "target_quantity_or_weight", "price_range", "urgency", "execution_core_snapshot_ref", "status", "created_at"]
    side_values: ["buy", "sell"]
    urgency_values: ["urgent", "normal", "low"]
    status_values: ["pending", "released", "filled", "partial", "unfilled", "expired", "blocked"]

finance_knowledge_artifacts:
  FinanceProfile:
    fields: ["profile_id", "assets", "liabilities", "cash_flow_summary", "tax_reminder_summary", "risk_budget", "liquidity_constraints", "sensitive_fields_encrypted", "derived_summary_refs"]
  AttributionReport:
    fields: ["report_id", "period", "market_result", "decision_quality", "execution_quality", "risk_quality", "data_quality", "evidence_quality", "condition_hit", "improvement_items", "needs_cfo_interpretation"]
  GovernanceProposal:
    fields: ["proposal_id", "proposal_type", "impact_level", "problem_statement", "proposed_change", "comparison_analysis", "validation_result_refs", "effective_scope", "rollback_plan", "owner_approval_ref"]
    impact_level_values: ["low", "medium", "high"]
  KnowledgePromptSkillProposal:
    fields: ["proposal_id", "proposal_type", "diff_or_manifest_ref", "affected_roles", "affected_workflows", "source_memory_refs", "source_knowledge_refs", "validation_result_refs", "impact_level", "rollback_plan", "effective_scope"]
  ReflectionRecord:
    fields: ["reflection_id", "trigger_source", "classification", "responsible_agent_id", "original_judgment_refs", "memory_refs", "knowledge_candidate_refs", "evidence_gap", "improvement_recommendation", "promotion_proposal_refs"]
  CFOInterpretation:
    fields: ["interpretation_id", "attribution_ref", "period", "summary_for_owner", "market_vs_decision_vs_execution", "finance_context_used", "sensitive_data_redaction_summary", "recommended_followups", "governance_proposal_refs", "reflection_assignment_refs"]
    required: ["interpretation_id", "attribution_ref", "period", "summary_for_owner", "market_vs_decision_vs_execution", "finance_context_used", "sensitive_data_redaction_summary", "recommended_followups"]
  ReflectionAssignment:
    fields: ["assignment_id", "trigger_ref", "responsible_agent_id", "classification", "questions_to_answer", "due_policy", "semantic_lead_agent_id", "process_authority", "status"]
    required: ["assignment_id", "trigger_ref", "responsible_agent_id", "classification", "questions_to_answer", "due_policy", "semantic_lead_agent_id", "process_authority", "status"]
    classification_values: ["decision_error", "market_shift", "unexpected_event", "execution_problem", "data_quality_problem", "methodology_decay"]
    status_values: ["assigned", "in_progress", "draft_submitted", "researcher_review", "proposal_created", "closed", "expired"]

devops_artifacts:
  IncidentReport:
    fields: ["incident_id", "incident_type", "severity", "affected_workflows", "affected_stages", "affected_artifacts", "affected_data_domains", "affected_agent_runs", "detected_by", "technical_summary", "evidence_refs", "business_impact_unknown_or_known", "risk_notification_ref", "status"]
    incident_type_values: ["system", "data_source", "service", "execution_environment", "security", "cost_token"]
    severity_values: ["P0", "P1", "P2", "P3"]
    status_values: ["detected", "triaged", "mitigating", "monitoring", "closed", "unresolved", "escalated"]
  DegradationPlan:
    fields: ["plan_id", "incident_ref", "fallback_option", "affected_usage", "data_quality_effect", "decision_or_execution_blocking_effect", "business_risk_requires_risk_review", "auto_allowed", "owner_or_governance_required", "rollback_or_recovery_steps"]
  RecoveryPlan:
    fields: ["plan_id", "incident_ref", "preconditions", "recovery_steps", "validation_steps", "technical_recovery_status", "residual_risks", "risk_review_required", "risk_release_request_ref", "investment_resume_allowed"]
    invariant: "DevOps 技术恢复不等于投资业务放行；investment_resume_allowed 固定 false。"
  RiskNotification:
    fields: ["notification_id", "incident_ref", "affected_workflows", "affected_stage_or_artifact_refs", "technical_status", "business_question_for_risk", "recommended_hold_or_reopen", "evidence_refs"]
    required: ["notification_id", "incident_ref", "affected_workflows", "technical_status", "business_question_for_risk", "recommended_hold_or_reopen", "evidence_refs"]

stage_guard_errors:
  request_brief_not_confirmed: VALIDATION_ERROR
  decision_core_blocked: STAGE_GUARD_FAILED
  execution_core_blocked: STAGE_GUARD_FAILED
  memo_schema_failed: VALIDATION_ERROR
  low_consensus_no_execution: STAGE_GUARD_FAILED
  low_action_conviction_no_execution: STAGE_GUARD_FAILED
  retained_hard_dissent_risk_review: STAGE_GUARD_FAILED
  risk_rejected_no_override: STAGE_GUARD_FAILED
  non_a_asset_no_trade: COMMAND_NOT_ALLOWED
  in_flight_snapshot_locked: SNAPSHOT_MISMATCH
  governance_auto_validation_failed: VALIDATION_ERROR
  governance_activation_failed: STAGE_GUARD_FAILED
  agent_capability_hot_patch_denied: SNAPSHOT_MISMATCH
  decision_packet_missing_input: STAGE_GUARD_FAILED
  decision_service_timeout: SERVICE_UNAVAILABLE
  decision_major_deviation_requires_exception_or_reopen: STAGE_GUARD_FAILED
  missing_deviation_rationale: VALIDATION_ERROR
  memory_not_fact_source: STAGE_GUARD_FAILED
  memory_sensitive_denied: SENSITIVE_DATA_RESTRICTED
  memory_snapshot_mismatch: SNAPSHOT_MISMATCH
  topic_hard_gate_failed: STAGE_GUARD_FAILED
  topic_concurrency_full: STAGE_GUARD_FAILED
  price_range_not_hit: STAGE_GUARD_FAILED
  execution_freshness_failed: STAGE_GUARD_FAILED

schema_catalog:
  version: "2026-04-29-team-decision-refreeze"
  pydantic_generation_rule: "每个 schema 条目可直接生成 Pydantic v2 model；字段约束不足时实现者不得自行放宽，需回写 contract。"
  jsonb_storage_rule: "artifact payload 可存 JSONB，但 domain guard 必须先按 schema 校验。"
  db_column_rule: "核心表列按 runtime-storage-architecture；artifact payload 内嵌结构按本文件。"

verification_rule: "每个 report fixture 必须引用 schema 名称、schema_version 和 checked_fields；缺 schema 的 report 不能作为 P0 pass 证据。"
