contract_id: CONTRACT-API-READ-MODELS
status: frozen
frozen_at: 2026-04-29
freeze_review_ref: reviews/contract-freeze-api-read-models-team-decision-2026-04-29.yaml
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
  - "Design 阶段 frozen contract；实现 API、frontend、read model 或 E2E 时必须读取。"
  - "本契约只承接 spec.md/testing.md/design.md；若冲突，以 spec.md 为准并回写 Design/Requirement。"
  - "Implementation 后修改本契约需按 contract-boundary 规则处理。"

common_api:
  base_path: "/api"
  format: "REST + JSON"
  write_rule: "所有写操作进入 domain command handler；前端不得直接推进业务状态。"
  auth: "V1 单 Owner session；未来多用户必须重开安全需求。"
  success_envelope:
    data: "object | array"
    meta: ["trace_id", "generated_at"]
  error_envelope:
    error_fields: ["code", "message", "trace_id", "retryable", "reason_code", "details"]
    details_shape:
      field_errors: "array<{field: string, code: string, message: string}>"
      guard_context: "object | null"
      expected_version: "integer | string | null"
      actual_version: "integer | string | null"
      retry_after_seconds: "integer | null"
  error_codes:
    - VALIDATION_ERROR
    - PERMISSION_DENIED
    - STAGE_GUARD_FAILED
    - COMMAND_NOT_ALLOWED
    - SENSITIVE_DATA_RESTRICTED
    - DIRECT_WRITE_DENIED
    - SNAPSHOT_MISMATCH
    - CONFLICT
    - SERVICE_UNAVAILABLE
    - NOT_FOUND
  http_status_mapping:
    VALIDATION_ERROR: 422
    PERMISSION_DENIED: 403
    STAGE_GUARD_FAILED: 409
    COMMAND_NOT_ALLOWED: 403
    SENSITIVE_DATA_RESTRICTED: 403
    DIRECT_WRITE_DENIED: 403
    SNAPSHOT_MISMATCH: 409
    CONFLICT: 409
    SERVICE_UNAVAILABLE: 503
    NOT_FOUND: 404
  pagination:
    query_params:
      limit: {type: integer, default: 50, minimum: 1, maximum: 200}
      cursor: {type: string, required: false, nullable: true}
    response_meta_fields: ["trace_id", "generated_at", "next_cursor", "has_more"]
    applies_to:
      - "/tasks"
      - "/approvals"
      - "/governance/changes"
      - "/devops/incidents"
      - "/workflows/{id}/agent-runs"
      - "/workflows/{id}/collaboration-events"
      - "/workflows/{id}/handoffs"
      - "/knowledge/search"
      - "/knowledge/memory-items"
      - "/team"

schema_notation:
  scalar_types: ["string", "integer", "number", "boolean", "timestamp", "date", "object", "array"]
  id_type: "string, stable opaque id; never infer business meaning from prefix"
  timestamp_type: "ISO-8601 UTC string"
  enum_rule: "unknown enum value is validation error unless field explicitly says future_extensible=true"
  money_shape: "{amount: number, currency: CNY}"
  percent_shape: "number; 0.01 means 1 percent unless field name ends with _pp"
  nullable_rule: "fields are non-null unless marked nullable: true"
  version_rule: "client_seen_version/client_seen_stage_version are optimistic concurrency guards"

endpoints:
  - path: "/requests/briefs"
    method: POST
    request: CreateRequestBriefRequest
    response: RequestBriefReadModel
    boundary: "只创建草稿 Request Brief；不启动 workflow"
  - path: "/requests/briefs/{id}/confirmation"
    method: POST
    request: RequestBriefConfirmationRequest
    response: TaskCardReadModel
    boundary: "confirmation，不是 approval"
  - path: "/workflows/{id}"
    method: GET
    response: WorkflowReadModel
    boundary: "只读"
  - path: "/workflows/{id}/commands"
    method: POST
    request: WorkflowCommandRequest
    response: WorkflowCommandResult
    boundary: "经 stage guard"
  - path: "/workflows/{id}/dossier"
    method: GET
    response: InvestmentDossierReadModel
    boundary: "只读聚合"
  - path: "/workflows/{id}/agent-runs"
    method: GET
    response: "AgentRunReadModel[]"
    boundary: "只读"
  - path: "/workflows/{id}/collaboration-events"
    method: GET
    response: "CollaborationEventReadModel[]"
    boundary: "只读"
  - path: "/workflows/{id}/handoffs"
    method: GET
    response: "HandoffPacketReadModel[]"
    boundary: "只读"
  - path: "/collaboration/commands"
    method: POST
    request: CollaborationCommandRequest
    response: CollaborationCommandReadModel
    boundary: "经 Authority Gateway"
  - path: "/gateway/artifacts"
    method: POST
    request: GatewayArtifactWriteRequest
    response: GatewayWriteResult
    boundary: "内部 runner/service API；经 Authority Gateway append-only 写 artifact"
  - path: "/gateway/events"
    method: POST
    request: GatewayEventWriteRequest
    response: GatewayWriteResult
    boundary: "内部 runner/service API；经 Authority Gateway 写 collaboration/audit event"
  - path: "/gateway/handoffs"
    method: POST
    request: GatewayHandoffWriteRequest
    response: GatewayWriteResult
    boundary: "内部 runner/service API；经 Authority Gateway 写 handoff packet"
  - path: "/gateway/memory-items"
    method: POST
    request: GatewayMemoryWriteRequest
    response: GatewayWriteResult
    boundary: "内部 runner/service API；经 Authority Gateway append-only 写 MemoryItem/MemoryVersion/MemoryRelation；不能写业务事实"
  - path: "/artifacts/{id}"
    method: GET
    response: ArtifactReadModel
    boundary: "只读"
  - path: "/tasks"
    method: GET
    response: TaskCenterReadModel
    boundary: "只读"
  - path: "/approvals"
    method: GET
    response: ApprovalCenterReadModel
    boundary: "只读"
  - path: "/approvals/{id}/decision"
    method: POST
    request: ApprovalDecisionRequest
    response: ApprovalRecordReadModel
    boundary: "Owner approval；不能覆盖 Risk rejected"
  - path: "/finance/overview"
    method: GET
    response: FinanceOverviewReadModel
    boundary: "只读"
  - path: "/finance/assets"
    method: POST
    request: FinanceAssetUpdateRequest
    response: FinanceAssetReadModel
    boundary: "财务受控写；非 A 股不触发交易"
  - path: "/knowledge/search"
    method: GET
    response: KnowledgeSearchReadModel
    boundary: "只读检索"
  - path: "/knowledge/memory-items"
    method: GET
    response: "MemoryItemReadModel[]"
    boundary: "只读检索 MemoryItem；Memory 不作为正式业务事实源"
  - path: "/knowledge/memory-items"
    method: POST
    request: CreateMemoryItemRequest
    response: MemoryItemReadModel
    boundary: "Owner/Researcher capture；经 domain command 和 Authority Gateway 形成 append-only MemoryVersion"
  - path: "/knowledge/memory-items/{id}"
    method: GET
    response: MemoryItemReadModel
    boundary: "只读详情；正文、抽取结果、关系和注入记录必须可追溯"
  - path: "/knowledge/memory-items/{id}/relations"
    method: POST
    request: MemoryRelationWriteRequest
    response: MemoryRelationReadModel
    boundary: "经 domain command 和 Authority Gateway 追加 relation；不得删除或覆盖历史 relation"
  - path: "/team"
    method: GET
    response: TeamReadModel
    boundary: "只读九个正式 Agent 画像、健康、版本和能力草案聚合"
  - path: "/team/{agentId}"
    method: GET
    response: AgentProfileReadModel
    boundary: "只读 Agent 画像、能力、版本、运行质量和越权/失败记录"
  - path: "/team/{agentId}/capability-config"
    method: GET
    response: AgentCapabilityConfigReadModel
    boundary: "只读能力配置表单 read model；有效版本来自 ContextSnapshot/registry"
  - path: "/team/{agentId}/capability-drafts"
    method: POST
    request: AgentCapabilityDraftRequest
    response: AgentCapabilityDraftReadModel
    boundary: "只创建 AgentCapabilityChangeDraft 和 Governance Change；不得直接修改有效版本或在途 AgentRun"
  - path: "/governance/changes"
    method: GET
    response: "GovernanceChangeReadModel[]"
    boundary: "只读"
  - path: "/governance/changes/{id}/decision"
    method: POST
    request: ApprovalDecisionRequest
    response: GovernanceChangeReadModel
    boundary: "高影响 Owner approval"
  - path: "/devops/health"
    method: GET
    response: DevOpsHealthReadModel
    boundary: "只读"
  - path: "/devops/incidents"
    method: GET
    response: "IncidentReadModel[]"
    boundary: "只读"

write_dtos:
  CreateRequestBriefRequest:
    fields: ["raw_text", "source", "requested_scope", "priority_hint", "authorization_boundary", "time_budget"]
    required: ["raw_text", "source"]
    schema:
      raw_text: {type: string, min_length: 1, max_length: 12000}
      source: {type: string, enum: ["owner_command", "page_action", "system_import"]}
      requested_scope: {type: object, required: false, nullable: true}
      priority_hint: {type: string, enum: ["P0", "P1", "P2"], required: false, nullable: true}
      authorization_boundary: {type: string, required: false, nullable: true}
      time_budget: {type: string, required: false, nullable: true}
  RequestBriefConfirmationRequest:
    fields: ["decision", "edited_brief", "client_seen_version"]
    required: ["decision", "client_seen_version"]
    allowed_decisions: ["confirm", "edit", "cancel"]
    schema:
      decision: {type: string, enum: ["confirm", "edit", "cancel"]}
      edited_brief: {type: object, required: false, nullable: true}
      client_seen_version: {type: integer, minimum: 1}
  WorkflowCommandRequest:
    fields: ["command_type", "reason_code", "payload", "client_seen_stage_version"]
    required: ["command_type", "payload", "client_seen_stage_version"]
    schema:
      command_type: {type: string}
      reason_code: {type: string, required: false, nullable: true}
      payload: {type: object}
      client_seen_stage_version: {type: integer, minimum: 1}
  CollaborationCommandRequest:
    fields: ["command_type", "workflow_id", "attempt_no", "stage", "source_agent_run_id", "target_agent_id_or_service", "payload", "requested_admission_type"]
    required: ["command_type", "workflow_id", "attempt_no", "stage", "source_agent_run_id", "target_agent_id_or_service", "payload", "requested_admission_type"]
    schema:
      command_type: {type: string}
      workflow_id: {type: string}
      attempt_no: {type: integer, minimum: 1}
      stage: {type: string}
      source_agent_run_id: {type: string}
      target_agent_id_or_service: {type: string}
      payload: {type: object}
      requested_admission_type: {type: string, enum: ["auto_accept", "semantic_accept", "domain_accept", "owner_approval"]}
  ApprovalDecisionRequest:
    fields: ["decision", "comment", "accepted_risks", "requested_changes", "client_seen_version"]
    required: ["decision", "client_seen_version"]
    allowed_decisions: ["approved", "rejected", "request_changes"]
    schema:
      decision: {type: string, enum: ["approved", "rejected", "request_changes"]}
      comment: {type: string, required: false, nullable: true, max_length: 4000}
      accepted_risks: {type: array, required: false, items: string}
      requested_changes: {type: array, required: false, items: string}
      client_seen_version: {type: integer, minimum: 1}
  GatewayArtifactWriteRequest:
    fields: ["workflow_id", "attempt_no", "stage", "source_agent_run_id", "context_snapshot_id", "artifact_type", "schema_version", "payload", "source_refs", "idempotency_key"]
    required: ["workflow_id", "attempt_no", "stage", "source_agent_run_id", "context_snapshot_id", "artifact_type", "schema_version", "payload", "idempotency_key"]
    schema:
      workflow_id: {type: string}
      attempt_no: {type: integer, minimum: 1}
      stage: {type: string}
      source_agent_run_id: {type: string}
      context_snapshot_id: {type: string}
      artifact_type: {type: string}
      schema_version: {type: string}
      payload: {type: object}
      source_refs: {type: array, required: false, items: string}
      idempotency_key: {type: string}
  GatewayEventWriteRequest:
    fields: ["workflow_id", "attempt_no", "stage", "source_agent_run_id", "event_type", "payload", "idempotency_key"]
    required: ["workflow_id", "attempt_no", "stage", "source_agent_run_id", "event_type", "payload", "idempotency_key"]
  GatewayHandoffWriteRequest:
    fields: ["workflow_id", "attempt_no", "from_stage", "to_stage_or_agent", "producer_agent_id_or_service", "source_artifact_refs", "summary", "open_questions", "blockers", "decisions_made", "invalidated_artifacts", "preserved_artifacts", "idempotency_key"]
    required: ["workflow_id", "attempt_no", "from_stage", "to_stage_or_agent", "producer_agent_id_or_service", "source_artifact_refs", "summary", "idempotency_key"]
  GatewayMemoryWriteRequest:
    fields: ["source_agent_run_id", "context_snapshot_id", "operation", "memory_id", "content_markdown", "payload", "source_refs", "relation_updates", "collection_updates", "sensitivity", "idempotency_key"]
    required: ["source_agent_run_id", "context_snapshot_id", "operation", "content_markdown", "source_refs", "sensitivity", "idempotency_key"]
    schema:
      operation: {type: string, enum: ["capture", "revise", "add_relation", "organize"]}
      source_agent_run_id: {type: string}
      context_snapshot_id: {type: string}
      memory_id: {type: string, required: false, nullable: true}
      content_markdown: {type: string, min_length: 1, max_length: 40000}
      payload: {type: object, required: false, nullable: true}
      source_refs: {type: array, items: string}
      relation_updates: {type: array, required: false, items: object}
      collection_updates: {type: array, required: false, items: object}
      sensitivity: {type: string, enum: ["public_internal", "finance_sensitive_summary", "finance_sensitive_raw", "security_sensitive"]}
      idempotency_key: {type: string}
  CreateMemoryItemRequest:
    fields: ["source_type", "source_refs", "content_markdown", "suggested_memory_type", "tags", "sensitivity", "client_seen_context_snapshot_id"]
    required: ["source_type", "source_refs", "content_markdown", "suggested_memory_type", "sensitivity", "client_seen_context_snapshot_id"]
    schema:
      source_type: {type: string, enum: ["owner_note", "agent_observation", "research_material", "reflection_output", "process_archive", "external_excerpt"]}
      source_refs: {type: array, items: string}
      content_markdown: {type: string, min_length: 1, max_length: 40000}
      suggested_memory_type: {type: string}
      tags: {type: array, required: false, items: string}
      sensitivity: {type: string, enum: ["public_internal", "finance_sensitive_summary", "finance_sensitive_raw", "security_sensitive"]}
      client_seen_context_snapshot_id: {type: string}
  MemoryRelationWriteRequest:
    fields: ["target_ref", "relation_type", "reason", "evidence_refs", "client_seen_version_id"]
    required: ["target_ref", "relation_type", "reason", "client_seen_version_id"]
    schema:
      target_ref: {type: string}
      relation_type: {type: string, enum: ["supports", "contradicts", "duplicates", "supersedes", "derived_from", "related_to", "promotes_to_knowledge", "used_by_context"]}
      reason: {type: string, min_length: 1, max_length: 4000}
      evidence_refs: {type: array, required: false, items: string}
      client_seen_version_id: {type: string}
  AgentCapabilityDraftRequest:
    fields: ["agent_id", "draft_title", "change_set", "impact_level_hint", "validation_plan_refs", "rollback_plan_ref", "effective_scope", "client_seen_profile_version", "client_seen_context_snapshot_id"]
    required: ["agent_id", "draft_title", "change_set", "effective_scope", "client_seen_profile_version", "client_seen_context_snapshot_id"]
    schema:
      agent_id: {type: string}
      draft_title: {type: string, min_length: 1, max_length: 200}
      change_set: {type: object, allowed_fields: ["tools_enabled", "service_permissions", "collaboration_commands", "skill_package_version", "prompt_version", "default_context_bindings", "model_route", "budget_tokens", "timeout_seconds", "sop_ref", "rubric_ref", "escalation_rules", "allowed_artifact_types"]}
      impact_level_hint: {type: string, enum: ["low", "medium", "high"], required: false, nullable: true}
      validation_plan_refs: {type: array, required: false, items: string}
      rollback_plan_ref: {type: string, required: false, nullable: true}
      effective_scope: {type: string, enum: ["new_task", "new_attempt"]}
      client_seen_profile_version: {type: string}
      client_seen_context_snapshot_id: {type: string}
  FinanceAssetUpdateRequest:
    fields: ["asset_id", "asset_type", "valuation", "valuation_date", "source", "client_seen_version"]
    required: ["asset_type", "valuation", "valuation_date", "source", "client_seen_version"]
    schema:
      asset_type: {type: string, enum: ["a_share", "fund", "gold", "real_estate", "cash", "liability", "other"]}
      valuation: {type: object, shape: money_shape}
      valuation_date: {type: date}
      source: {type: string}
      client_seen_version: {type: integer, minimum: 1}

gateway_write_result:
  fields: ["accepted", "object_id", "object_type", "schema_version", "audit_event_id", "outbox_event_id", "trace_id"]
  required: ["accepted", "object_id", "object_type", "schema_version", "audit_event_id", "trace_id"]
  guard_failures:
    schema_validation_failed: VALIDATION_ERROR
    command_not_allowed: COMMAND_NOT_ALLOWED
    stage_guard_failed: STAGE_GUARD_FAILED
    snapshot_mismatch: SNAPSHOT_MISMATCH
    direct_write_denied: DIRECT_WRITE_DENIED
    memory_not_fact_source: STAGE_GUARD_FAILED
    memory_sensitive_denied: SENSITIVE_DATA_RESTRICTED
    agent_capability_hot_patch_denied: SNAPSHOT_MISMATCH

read_models:
  ShellReadModel:
    fields: ["nav_items", "attention_counts", "session"]
    nav_items: ["overview", "investment", "finance", "knowledge", "team", "governance"]
  OwnerDecisionReadModel:
    fields: ["today_attention", "paper_account", "risk_summary", "approval_summary", "manual_todo_summary", "daily_brief_summary", "system_health"]
  InvestmentDossierReadModel:
    fields:
      - workflow
      - stage_rail
      - request_brief
      - data_readiness
      - ic_context
      - chair_brief
      - analyst_stance_matrix
      - role_payload_drilldowns
      - consensus
      - debate
      - decision_service
      - cio_decision
      - decision_packet
      - decision_guard
      - optimizer_deviation
      - risk_review
      - approval
      - paper_execution
      - position_disposal
      - attribution
      - handoffs
      - evidence_map
      - forbidden_actions
  ArtifactReadModel:
    fields: ["artifact_id", "artifact_type", "workflow_id", "attempt_no", "trace_id", "producer", "producer_type", "status", "summary", "source_refs", "evidence_refs", "decision_refs", "schema_version", "payload", "created_at"]
    invariant: "ArtifactReadModel 是 artifact ledger 的只读投影；payload 必须遵守 artifact_type 对应 domain artifact schema。"
  GovernanceReadModel:
    fields: ["task_center", "approval_center", "governance_changes", "agent_capability_changes", "data_service_health", "audit_trail"]
  TeamReadModel:
    fields: ["team_health", "agent_cards", "capability_drafts", "quality_alerts", "governance_links"]
    invariant: "必须覆盖九个正式 Agent；不显示任何直接热改在途 AgentRun 的入口。"
  AgentProfileReadModel:
    fields: ["agent_id", "display_name", "role", "status", "capability_summary", "can_do", "cannot_do", "read_permissions", "write_permissions", "service_permissions", "tool_permissions", "collaboration_commands", "sop_refs", "rubric_refs", "escalation_rules", "failure_policy", "profile_version", "skill_package_version", "prompt_version", "context_snapshot_version", "model_route", "budget_tokens", "timeout_seconds", "recent_artifacts", "quality_metrics", "failure_records", "denied_actions", "active_agent_runs", "config_draft_entry"]
  AgentCapabilityConfigReadModel:
    fields: ["agent_id", "editable_fields", "current_effective_versions", "draft_schema", "impact_policy_preview", "validation_plan_options", "rollback_refs", "effective_scope_options", "forbidden_direct_update_reason"]
    invariant: "read model 只提供草案表单；提交后必须进入 AgentCapabilityDraftReadModel/GovernanceChange。"
  AgentCapabilityDraftReadModel:
    fields: ["draft_id", "agent_id", "change_set", "diff_summary", "impact_level", "state", "validation_status", "governance_change_ref", "owner_approval_ref", "effective_scope", "rollback_plan_ref", "created_at", "updated_at"]
  TraceDebugReadModel:
    fields: ["agent_run_tree", "context_slices", "context_injection_records", "denied_memory_refs", "collaboration_commands", "collaboration_events", "handoff_packets", "gateway_write_records", "denied_direct_writes", "sensitive_access_denials", "service_calls", "latency_token_cost"]
    visibility: "默认不出现在 Owner 首屏；从治理、Dossier 详情或 DevOps 入口进入。"
  MemoryItemReadModel:
    fields: ["memory_id", "memory_type", "status", "current_version_id", "title", "summary", "tags", "source_refs", "artifact_refs", "symbol_refs", "agent_refs", "stage_refs", "relations", "collections", "sensitivity", "promotion_state", "why_included", "created_at", "updated_at"]
    invariant: "展示时必须标注 Memory/Knowledge 不是正式业务事实源；与 artifact 冲突时 read model 应显示冲突和 artifact 优先。"
  MemoryRelationReadModel:
    fields: ["relation_id", "source_memory_id", "target_ref", "relation_type", "reason", "evidence_refs", "created_by", "created_at"]

r8_read_model_shapes:
  OwnerDecisionReadModel:
    purpose: "Owner 首屏只回答今天是否需要处理、风险在哪里、哪些事项被阻断。"
    sections:
      today_attention:
        fields: ["risk_items", "approval_items", "manual_todo_items", "data_quality_items", "incident_items"]
        guard: "只展示需要 Owner 注意的摘要，不展示 raw trace。"
      paper_account:
        fields: ["total_value", "cash", "position_value", "return", "drawdown", "risk_budget_used"]
      risk_summary:
        fields: ["concentration", "risk_budget_used", "blockers", "risk_rejected_count", "conditional_pass_count"]
      approval_summary:
        fields: ["pending_count", "next_deadline", "high_impact_count", "risk_exception_count"]
      manual_todo_summary:
        fields: ["open_count", "expired_count", "next_due", "non_a_asset_count"]
      system_health:
        fields: ["health_state", "active_incidents", "risk_handoff_count", "last_success_at"]
  InvestmentDossierReadModel:
    purpose: "Dossier 解释 S0-S7 业务链路、Agent 协作、Risk/Execution/Attribution，不展示长聊天。"
    sections:
      stage_rail:
        item_fields: ["stage", "node_status", "responsible_role", "reason_code", "artifact_count", "reopen_marker"]
      analyst_stance_matrix:
        item_fields: ["role", "direction_score", "confidence", "evidence_quality", "hard_dissent", "view_update_refs"]
      debate:
        fields: ["debate_required", "rounds", "issues", "view_changes", "cio_synthesis", "retained_hard_dissent", "risk_review_required"]
      decision_service:
        fields: ["service_call_id", "input_artifact_refs", "decision_packet_ref", "input_completeness", "guard_result_ref", "major_deviation", "exception_candidate_ref", "reopen_recommendation_ref", "reason_codes"]
      decision_packet:
        fields: ["packet_id", "decision_question", "analyst_stance_summary", "consensus_score", "action_conviction", "data_quality", "market_state", "optimizer_baseline", "risk_constraints", "evidence_refs"]
      decision_guard:
        fields: ["single_name_deviation_pp", "portfolio_active_deviation", "major_deviation", "low_action_conviction", "retained_hard_dissent", "data_quality_blockers", "owner_exception_or_reopen"]
      ic_context:
        fields: ["topic_id", "request_brief_ref", "data_readiness_ref", "market_state_ref", "service_result_refs", "portfolio_context_ref", "risk_constraint_refs", "research_package_refs", "role_attachment_refs", "context_snapshot_id", "artifact_ref"]
      chair_brief:
        fields: ["decision_question", "scope_boundary", "key_tensions", "must_answer_questions", "time_budget", "action_standard", "risk_constraints_to_respect", "forbidden_assumptions", "no_preset_decision_attestation", "artifact_ref"]
      position_disposal:
        fields: ["task_id", "symbol", "triggers", "priority", "risk_gate_present", "execution_core_guard_present", "direct_execution_allowed", "workflow_route", "reason_code", "artifact_ref"]
        invariant: "Dossier 只能展示处置任务和风控回路，不提供直接执行入口。"
      forbidden_actions:
        fields: ["risk_rejected_no_override", "execution_core_blocked_no_trade", "non_a_asset_no_trade", "low_action_no_execution"]
      evidence_map:
        fields: ["artifact_refs", "data_refs", "source_quality", "conflict_refs", "supporting_evidence_only_refs"]
  TraceDebugReadModel:
    purpose: "审计协作与排障；raw transcript 默认折叠且非正式事实源。"
    sections:
      agent_run_tree:
        item_fields: ["agent_run_id", "parent_run_id", "agent_id", "stage", "attempt_no", "profile_version", "status", "context_slice_id"]
      collaboration_commands:
        item_fields: ["command_id", "command_type", "source_agent_id", "target_agent_id_or_service", "admission_status", "admission_reason", "result_ref"]
      collaboration_events:
        item_fields: ["event_id", "event_type", "agent_run_id", "command_id", "artifact_id", "payload_summary", "created_at"]
      handoff_packets:
        item_fields: ["handoff_id", "from_stage", "to_stage_or_agent", "source_artifact_refs", "open_questions", "blockers"]
      gateway_write_records:
        item_fields: ["object_type", "object_id", "schema_version", "audit_event_id", "outbox_event_id", "accepted"]
  GovernanceReadModel:
    purpose: "治理页分离 Task、Approval、Governance Change、Health 和 Audit。"
    sections:
      task_center:
        item_fields: ["task_id", "task_type", "priority", "current_state", "blocked_reason", "reason_code"]
      approval_center:
        item_fields: ["approval_id", "approval_type", "trigger_reason", "recommended_decision", "deadline", "decision"]
        guard: "不包含 confirmation 和 manual_todo；Risk rejected 不生成 approval。"
      governance_changes:
        item_fields: ["change_id", "change_type", "impact_level", "state", "effective_scope", "rollback_plan_ref"]
      agent_capability_changes:
        item_fields: ["draft_id", "agent_id", "impact_level", "state", "validation_status", "governance_change_ref", "owner_approval_ref", "effective_scope"]
      data_service_health:
        item_fields: ["incident_id", "severity", "incident_type", "status", "risk_handoff_status"]
  TeamReadModel:
    purpose: "团队页用中文卡面展示九个正式 Agent 的画像、能力、版本、质量和能力配置草案入口。"
    sections:
      team_health:
        fields: ["healthy_agent_count", "active_agent_run_count", "pending_draft_count", "failed_or_denied_count", "last_quality_window"]
      agent_cards:
        item_fields: ["agent_id", "display_name", "role", "status", "profile_version", "skill_package_version", "prompt_version", "context_snapshot_version", "recent_quality_score", "active_run_count", "failure_count", "denied_action_count"]
      capability_drafts:
        item_fields: ["draft_id", "agent_id", "impact_level", "state", "validation_status", "governance_change_ref", "effective_scope"]
      quality_alerts:
        item_fields: ["agent_id", "alert_type", "severity", "reason_code", "artifact_ref", "trace_id"]
  AgentProfileReadModel:
    purpose: "单 Agent 画像页解释该 Agent 是否胜任岗位以及配置边界。"
    sections:
      identity:
        fields: ["agent_id", "display_name", "role", "status", "profile_version"]
      capability:
        fields: ["capability_summary", "can_do", "cannot_do", "read_permissions", "write_permissions", "tool_permissions", "service_permissions", "collaboration_commands"]
      quality:
        fields: ["recent_artifacts", "quality_metrics", "schema_pass_rate", "evidence_quality", "failure_records", "denied_actions"]
      versions:
        fields: ["skill_package_version", "prompt_version", "context_snapshot_version", "model_route", "budget_tokens", "timeout_seconds"]
  AgentCapabilityConfigReadModel:
    purpose: "能力配置表单只创建草案，不能直接修改有效版本。"
    sections:
      editable_fields:
        item_fields: ["field", "current_value_ref", "allowed_values", "requires_high_impact_if_changed", "validation_required"]
      impact_preview:
        fields: ["impact_level_preview", "affected_workflows", "affected_agent_runs", "new_task_or_attempt_only", "forced_high_reasons"]
      submit_guard:
        fields: ["forbidden_direct_update_reason", "client_seen_profile_version", "client_seen_context_snapshot_id"]
  AgentCapabilityDraftReadModel:
    purpose: "团队页保存草案后的回执；Owner 后续在治理页查看状态和审批。"
    sections:
      draft:
        fields: ["draft_id", "agent_id", "change_set", "diff_summary", "impact_level", "state", "validation_status"]
      governance:
        fields: ["governance_change_ref", "owner_approval_ref", "effective_scope", "rollback_plan_ref", "created_at", "updated_at"]
  FinanceOverviewReadModel:
    purpose: "展示全资产与规划边界，非 A 股不进入审批/执行/交易。"
    sections:
      asset_profile:
        item_fields: ["asset_type", "valuation", "valuation_date", "source", "boundary_label"]
      finance_health:
        fields: ["liquidity", "leverage", "risk_budget", "stress_test_summary", "future_cash_need"]
      manual_todo:
        item_fields: ["todo_id", "asset_type", "due_date", "risk_hint", "state"]
      sensitive_data_notice:
        fields: ["redaction_applied", "allowed_cleartext_roles", "denied_agent_count"]
  KnowledgeSearchReadModel:
    purpose: "展示研究、经验、反思、MemoryCollection、关系图和 Prompt/Skill/Knowledge proposal；不直接生效，不作为业务事实源。"
    sections:
      daily_brief:
        item_fields: ["brief_id", "priority", "title", "supporting_evidence_only"]
      memory_collections:
        item_fields: ["collection_id", "title", "scope", "purpose", "filter_expression", "result_count"]
      memory_results:
        item_fields: ["memory_id", "memory_type", "status", "current_version_id", "title", "tags", "source_refs", "relation_summary", "sensitivity", "promotion_state", "why_included"]
      relation_graph:
        item_fields: ["source_memory_id", "target_ref", "relation_type", "reason", "evidence_refs"]
      context_injection_preview:
        item_fields: ["context_snapshot_id", "source_ref", "binding_type", "effective_scope", "redaction_status", "why_included"]
      organize_suggestions:
        item_fields: ["suggestion_id", "target_memory_refs", "suggested_tags", "suggested_relations", "requires_gateway_write", "risk_if_applied"]
      proposals:
        item_fields: ["proposal_id", "proposal_type", "impact_level", "validation_result_refs", "effective_scope", "rollback_plan"]
      reflection_library:
        item_fields: ["reflection_id", "classification", "responsible_agent_id", "memory_refs", "promotion_proposal_refs"]
  DevOpsHealthReadModel:
    purpose: "展示日常巡检、incident、degradation、recovery 和 Risk handoff。"
    sections:
      routine_checks:
        item_fields: ["check_id", "window", "status", "last_success_at", "next_check_at"]
      incidents:
        item_fields: ["incident_id", "severity", "incident_type", "affected_workflows", "status", "risk_notification_ref"]
      recovery:
        item_fields: ["plan_id", "technical_recovery_status", "risk_review_required", "investment_resume_allowed"]

ui_guard_responses:
  - scenario: "Risk rejected 后 Owner 尝试批准执行"
    api_error: STAGE_GUARD_FAILED
    reason_code: risk_rejected_no_override
    frontend_rule: "不显示批准继续按钮；显示阻断原因和 reopen/终止路径"
  - scenario: "非 A 股资产请求交易"
    api_error: COMMAND_NOT_ALLOWED
    reason_code: non_a_asset_no_trade
    frontend_rule: "转为 finance planning 或 manual_todo"
  - scenario: "execution_core 不达标请求成交"
    api_error: STAGE_GUARD_FAILED
    reason_code: execution_core_blocked
    frontend_rule: "执行按钮禁用，展示 Data Readiness 缺口"
  - scenario: "直接热改 Prompt/Skill/配置"
    api_error: SNAPSHOT_MISMATCH
    reason_code: in_flight_snapshot_locked
    frontend_rule: "跳转 Governance Proposal"
  - scenario: "团队页直接热改 Agent 能力、工具权限、Prompt、SkillPackage 或默认上下文"
    api_error: SNAPSHOT_MISMATCH
    reason_code: agent_capability_hot_patch_denied
    frontend_rule: "只能创建 AgentCapabilityChangeDraft 并进入 Governance Change；在途 AgentRun 继续旧 ContextSnapshot"
  - scenario: "非 CFO 读取财务敏感明文"
    api_error: SENSITIVE_DATA_RESTRICTED
    reason_code: sensitive_data_restricted
    frontend_rule: "展示脱敏摘要和审计提示"
  - scenario: "Memory/Knowledge 被用作正式 artifact 事实源或直接推进业务状态"
    api_error: STAGE_GUARD_FAILED
    reason_code: memory_not_fact_source
    frontend_rule: "展示冲突说明和正式 artifact 链接；只允许生成补证、反思或治理提案"

verification_mapping:
  TC-ACC-003-01: ["TeamReadModel", "AgentProfileReadModel", "AgentCapabilityConfigReadModel"]
  TC-ACC-004-01: ["MemoryItemReadModel", "TraceDebugReadModel.context_injection_records", "ui_guard_responses"]
  TC-ACC-006-01: ["ShellReadModel", "OwnerDecisionReadModel", "InvestmentDossierReadModel", "TeamReadModel"]
  TC-ACC-007-01: ["TaskCenterReadModel", "ApprovalCenterReadModel", "AgentCapabilityDraftReadModel", "GovernanceReadModel.agent_capability_changes", "ui_guard_responses"]
  TC-ACC-014-01: ["InvestmentDossierReadModel.ic_context", "InvestmentDossierReadModel.chair_brief", "ArtifactReadModel"]
  TC-ACC-017-01: ["InvestmentDossierReadModel.debate"]
  TC-ACC-018-01: ["InvestmentDossierReadModel.decision_service", "InvestmentDossierReadModel.decision_packet", "InvestmentDossierReadModel.decision_guard", "InvestmentDossierReadModel.optimizer_deviation"]
  TC-ACC-019-01: ["InvestmentDossierReadModel.risk_review", "ui_guard_responses"]
  TC-ACC-021-01: ["InvestmentDossierReadModel.paper_execution"]
  TC-ACC-022-01: ["InvestmentDossierReadModel.position_disposal", "ArtifactReadModel"]
  TC-ACC-027-01: ["KnowledgeSearchReadModel.memory_results", "KnowledgeSearchReadModel.organize_suggestions", "MemoryItemReadModel"]
  TC-ACC-028-01: ["KnowledgeSearchReadModel.relation_graph", "KnowledgeSearchReadModel.proposals", "ui_guard_responses"]
  TC-ACC-030-01: ["AgentCapabilityDraftReadModel", "KnowledgeSearchReadModel.context_injection_preview", "TraceDebugReadModel.context_injection_records"]
