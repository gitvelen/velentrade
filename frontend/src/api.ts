import {
  AgentProfileReadModel,
  ApprovalRecordReadModel,
  CapabilityConfigReadModel,
  DevOpsHealthReadModel,
  FinanceOverviewReadModel,
  GovernanceReadModel,
  InvestmentDossierReadModel,
  KnowledgeReadModel,
  TeamReadModel,
  TraceDebugReadModel,
  buildDevOpsHealthReadModel,
  buildFinanceOverviewReadModel,
  buildGovernanceReadModel,
  buildApprovalRecordReadModel,
  buildTeamReadModel,
  buildUnavailableTraceDebugReadModel,
  buildUnifiedTodoItems,
} from "./workbench";

type ApiEnvelope<T> = {
  data: T;
};

type ApiErrorEnvelope = {
  error?: {
    code?: string;
    reason_code?: string;
    trace_id?: string;
    message?: string;
  };
};

type ApiTeamReadModel = {
  team_health?: {
    healthy_agent_count?: number;
    active_agent_run_count?: number;
    pending_draft_count?: number;
    failed_or_denied_count?: number;
  };
  agent_cards?: Array<{
    agent_id?: string;
    display_name?: string;
    role?: string;
    profile_version?: string;
    skill_package_version?: string;
    prompt_version?: string;
    context_snapshot_version?: string;
    recent_quality_score?: number;
    failure_count?: number;
    denied_action_count?: number;
    config_draft_entry?: string;
    weakness_tags?: string[];
  }>;
};

type ApiPermissionFieldValue = string | string[] | null | undefined;
type ApiPermissionMap = Record<string, ApiPermissionFieldValue>;
type ApiPermissionInput = string[] | ApiPermissionMap | undefined;

type ApiAgentProfileReadModel = {
  agent_id?: string;
  display_name?: string;
  capability_summary?: string;
  can_do?: string[];
  cannot_do?: string[];
  profile_version?: string;
  skill_package_version?: string;
  prompt_version?: string;
  context_snapshot_version?: string;
  read_permissions?: ApiPermissionMap;
  write_permissions?: ApiPermissionMap;
  service_permissions?: string[];
  tool_permissions?: ApiPermissionInput;
  collaboration_commands?: string[];
  weakness_tags?: string[];
  cfo_attribution_refs?: string[];
  quality_metrics?: {
    schema_pass_rate?: number;
    evidence_quality?: number;
  };
  denied_actions?: Array<{ reason_code?: string }>;
  failure_records?: Array<string | { reason_code?: string }>;
};

type ApiCapabilityConfigReadModel = {
  agent_id?: string;
  editable_fields?: Array<string | { field?: string }>;
  forbidden_direct_update_reason?: string;
  effective_scope_options?: string[];
};

type ApiMemoryReadModel = {
  memory_id?: string;
  memory_type?: string;
  status?: string;
  title?: string;
  summary?: string;
  tags?: string[];
  source_refs?: string[];
  artifact_refs?: string[];
  why_included?: string;
  current_version_id?: string;
  sensitivity?: string;
  promotion_state?: string;
  extraction_status?: string;
  relations?: Array<{
    target_ref?: string;
    relation_type?: string;
    reason?: string;
  }>;
};

type ApiAgentRunReadModel = {
  agent_run_id?: string;
  parent_run_id?: string | null;
  agent_id?: string;
  stage?: string;
  profile_version?: string;
  context_snapshot_id?: string;
  context_slice_id?: string;
  run_goal?: string;
  status?: string;
};

type ApiCollaborationEventReadModel = {
  event_type?: string;
  summary?: string;
  payload?: Record<string, unknown>;
};

type ApiHandoffReadModel = {
  from_stage?: string;
  to_stage_or_agent?: string;
  blockers?: string[];
  open_questions?: string[];
};

type ApiFinanceOverviewReadModel = {
  asset_profile?: Array<{
    asset_type?: string;
    valuation?: { amount?: number; currency?: string };
    boundary_label?: string;
  }>;
  finance_health?: {
    liquidity?: number;
    risk_budget?: { budget_ref?: string };
    stress_test_summary?: string;
  };
  manual_todo?: Array<{ risk_hint?: string }>;
};

type ApiDevOpsHealthReadModel = {
  routine_checks?: Array<{ check_id?: string; status?: string; last_success_at?: string; next_check_at?: string }>;
  incidents?: Array<{ incident_id?: string; status?: string; incident_type?: string }>;
  recovery?: Array<{ plan_id?: string; technical_recovery_status?: string; investment_resume_allowed?: boolean }>;
};

type ApiTaskCenterReadModel = {
  task_center?: Array<{
    task_id?: string;
    task_type?: string;
    current_state?: string;
    reason_code?: string;
    due_date?: string;
    risk_hint?: string;
    blocked_reason?: string;
  }>;
};

type ApiApprovalCenterReadModel = {
  approval_center?: Array<{
    approval_id?: string;
    approval_type?: string;
    subject?: string;
    trigger_reason?: string;
    effective_scope?: string;
    deadline?: string;
    recommended_decision?: string;
    decision?: string;
    alternatives?: unknown[];
    comparison_options?: unknown[];
    risk_and_impact?: unknown[] | Record<string, unknown>;
    timeout_disposition?: string;
    timeout_policy?: string;
    rollback_ref?: string;
    evidence_refs?: string[];
    trace_route?: string;
    allowed_actions?: string[];
  }>;
};

type ApiGovernanceChangeReadModel = {
  change_id?: string;
  change_type?: string;
  impact_level?: string;
  state?: string;
  effective_scope?: string;
};

let cachedApprovalCenter: NonNullable<ApiApprovalCenterReadModel["approval_center"]> = [];

type ApiInvestmentDossierReadModel = {
  workflow?: {
    workflow_id?: string;
    title?: string;
    current_stage?: string;
    state?: string;
  };
  stage_rail?: Array<{
    stage?: string;
    node_status?: string;
    reason_code?: string | null;
    artifact_count?: number;
  }>;
  chair_brief?: {
    decision_question?: string;
    key_tensions?: string[];
    no_preset_decision_attestation?: boolean;
  };
  analyst_stance_matrix?: Array<{
    role?: string;
    direction?: string;
    direction_score?: number;
    confidence?: number;
    evidence_quality?: number;
    hard_dissent?: boolean;
    hard_dissent_reason?: string | null;
    thesis?: string | null;
  }>;
  forbidden_actions?: Record<string, {
    action_visible?: boolean;
    actionVisible?: boolean;
    reason_code?: string;
    reasonCode?: string;
  }>;
  data_readiness?: {
    quality_band?: string;
    decision_core_status?: string;
    execution_core_status?: string;
    issues?: string[];
    lineage_refs?: string[];
    owner_summary?: string;
    source_status?: Array<{
      source_name?: string;
      source_ref?: string;
      required_usage?: string;
      requested_fields?: string[];
      obtained_fields?: string[];
      missing_fields?: string[];
      status?: string;
      quality_label?: string;
      evidence_ref?: string;
    }>;
    data_gaps?: Array<{
      gap?: string;
      affects_stage?: string;
      impact?: string;
      next_action?: string;
    }>;
  };
  role_payload_drilldowns?: Array<{
    role?: string;
    highlights?: string[];
    hard_dissent_reason?: string | null;
    thesis?: string | null;
    supporting_evidence_refs?: string[];
    counter_evidence_refs?: string[];
    key_risks?: string[];
    applicable_conditions?: string[];
    invalidation_conditions?: string[];
    suggested_action_implication?: string | null;
    role_payload?: Record<string, unknown>;
  }>;
  consensus?: {
    score?: number;
    consensus_score?: number;
    action_conviction?: number;
    threshold_label?: string;
  };
  debate?: {
    rounds_used?: number;
    retained_hard_dissent?: boolean;
    risk_review_required?: boolean;
    issues?: string[];
    view_changes?: string[];
    cio_synthesis?: string | null;
    unresolved_dissent?: string[];
    rounds?: Array<{ round_no?: number; issue?: string; outcome?: string }>;
    owner_summary?: string | null;
    status_summary?: {
      rounds_used?: number;
      retained_hard_dissent?: boolean;
      risk_review_required?: boolean;
      consensus_score?: number | null;
      action_conviction?: number | null;
    };
    core_disputes?: Array<{
      title?: string;
      why_it_matters?: string;
      involved_roles?: string[];
      current_conclusion?: string;
      required_evidence?: string[];
    }>;
    view_change_details?: Array<{
      role?: string;
      before?: string;
      after?: string;
      reason?: string;
      impact?: string;
    }>;
    retained_dissent_details?: Array<{
      source_role?: string;
      dissent?: string;
      counter_risks?: string[];
      handling?: string;
      forbidden_actions?: string[];
    }>;
    round_details?: Array<{
      round_no?: number;
      issue?: string;
      participants?: string[];
      input_evidence?: string[];
      outcome?: string;
      unresolved_questions?: string[];
    }>;
    next_actions?: Array<{
      action?: string;
      owner?: string;
      completion_signal?: string;
      next_stage?: string;
    }>;
  };
  optimizer_deviation?: {
    single_name_deviation?: string;
    portfolio_deviation?: string;
    recommendation?: string;
  };
  cio_decision?: {
    decision?: string;
    decision_rationale?: string;
    deviation_reason?: string;
    conditions?: string[];
    monitoring_points?: string[];
    risk_handoff_notes?: string;
  };
  decision_guard?: {
    major_deviation?: boolean;
    single_name_deviation_pp?: number | string;
    portfolio_active_deviation?: number | string;
    low_action_conviction?: boolean;
    retained_hard_dissent?: boolean;
    data_quality_blockers?: string[];
    reason_codes?: string[];
  };
  risk_review?: {
    review_result?: string;
    repairability?: string;
    owner_exception_required?: boolean;
    reason_codes?: string[];
  };
  paper_execution?: {
    status?: string;
    pricing_method?: string;
    window?: string;
    fees?: unknown;
    taxes?: unknown;
    slippage?: unknown;
    t_plus_one?: string;
  };
  attribution?: {
    summary?: string;
    links?: string[];
    market_result?: string;
    decision_quality?: number | null;
    execution_quality?: number | null;
    risk_quality?: number | null;
    data_quality?: number | null;
    evidence_quality?: number | null;
    condition_hit?: string;
    improvement_items?: string[];
    needs_cfo_interpretation?: boolean;
  };
  evidence_map?: {
    artifact_refs?: string[];
    data_refs?: string[];
    source_quality?: Array<string | { source?: string; used_for?: string; usedFor?: string; quality?: string }>;
    conflict_refs?: string[];
    supporting_evidence_only_refs?: string[];
  };
};

export type RequestBriefApiReadModel = {
  briefId: string;
  routeType: string;
  semanticLead?: string;
  processAuthority?: string;
  expectedArtifacts?: string[];
  reasonCode?: string | null;
  ownerConfirmationStatus?: string;
  version: number;
};

export type TaskCardApiReadModel = {
  taskId: string;
  taskType: string;
  currentState: string;
  reasonCode: string;
  workflowId?: string;
};

export type CapabilityDraftApiReadModel = {
  draftId: string;
  governanceChangeRef: string;
  impactLevel: string;
  effectiveScope: string;
};

export type ApprovalDecisionApiReadModel = {
  approvalId: string;
  decision: string;
  effectiveScope: string;
};

export type MemoryWriteApiReadModel = {
  memoryId: string;
  currentVersionId: string;
};

export type MemoryRelationApiReadModel = {
  relationId: string;
  sourceMemoryId: string;
  targetRef: string;
  relationType: string;
};

export type FinanceAssetUpdateApiReadModel = {
  assetId: string;
  assetType: string;
};

export type FinanceAssetUpdateInput = {
  assetId?: string;
  assetType?: "a_share" | "fund" | "gold" | "real_estate" | "cash" | "liability" | "other";
  amount?: number;
  valuationDate?: string;
  source?: string;
};

export class ApiRequestError extends Error {
  statusCode: number;
  code: string;
  reasonCode: string;
  traceId: string;

  constructor(path: string, statusCode: number, code: string, reasonCode: string, traceId: string) {
    super(`request failed: ${path}`);
    this.statusCode = statusCode;
    this.code = code;
    this.reasonCode = reasonCode;
    this.traceId = traceId;
  }
}

async function fetchEnvelope<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    let errorEnvelope: ApiErrorEnvelope = {};
    try {
      errorEnvelope = await response.json() as ApiErrorEnvelope;
    } catch {
      errorEnvelope = {};
    }
    throw new ApiRequestError(
      path,
      response.status,
      errorEnvelope.error?.code ?? "REQUEST_FAILED",
      errorEnvelope.error?.reason_code ?? "unknown",
      errorEnvelope.error?.trace_id ?? "trace-unavailable",
    );
  }
  const payload = await response.json() as ApiEnvelope<T>;
  return payload.data;
}

export function buildEmptyKnowledgeReadModel(): KnowledgeReadModel {
  return {
    dailyBrief: [],
    researchPackages: [],
    memoryCollections: [],
    memoryResults: [],
    relationGraph: [],
    organizeSuggestions: [],
    contextInjectionInspector: [],
    proposals: [],
    defaultContextProposalPath: "/governance?panel=changes",
  };
}

export function buildUnavailableInvestmentDossierReadModel(workflowId: string): InvestmentDossierReadModel {
  return {
    workflow: { workflowId, title: "投资档案不可用", currentStage: "S0", state: "unavailable" },
    stageRail: ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"].map((stage) => ({
      stage,
      nodeStatus: "not_started",
      reasonCode: null,
      artifactCount: 0,
    })),
    chairBrief: { decisionQuestion: "未读取到后端投资档案。", keyTensions: [], noPresetDecisionAttestation: true },
    analystStanceMatrix: [],
    dataReadiness: {
      qualityBand: "unknown",
      decisionCoreStatus: "unknown",
      executionCoreStatus: "unknown",
      issues: [],
      lineageRefs: [],
      ownerSummary: "未读取到后端 S1 数据准备结果。",
      sourceStatus: [],
      dataGaps: [],
    },
    rolePayloadDrilldowns: [],
    consensus: { score: 0, actionConviction: 0, thresholdLabel: "不可用" },
    debate: { roundsUsed: 0, retainedHardDissent: false, riskReviewRequired: false, issues: [] },
    optimizerDeviation: { singleNameDeviation: "不可用", portfolioDeviation: "不可用", recommendation: "等待后端档案" },
    riskReview: { reviewResult: "unknown", repairability: "unknown", ownerExceptionRequired: false, reasonCodes: [] },
    paperExecution: { status: "not_started", pricingMethod: "not_released", window: "不可用", fees: "不可用", tPlusOne: "不可用" },
    attribution: { summary: "暂无归因。", links: [] },
    evidenceMap: { artifactRefs: [], dataRefs: [], sourceQuality: [], conflictRefs: [], supportingEvidenceOnlyRefs: [] },
    forbiddenActions: {},
    traceRoute: `/investment/${workflowId}/trace`,
  };
}

export async function loadTeamReadModel(): Promise<TeamReadModel> {
  const fallback = buildTeamReadModel();
  const payload = await fetchEnvelope<ApiTeamReadModel>("/api/team");

  return {
    ...fallback,
    teamHealth: {
      healthyAgentCount: payload.team_health?.healthy_agent_count ?? fallback.teamHealth.healthyAgentCount,
      activeAgentRunCount: payload.team_health?.active_agent_run_count ?? fallback.teamHealth.activeAgentRunCount,
      pendingDraftCount: payload.team_health?.pending_draft_count ?? fallback.teamHealth.pendingDraftCount,
      failedOrDeniedCount: payload.team_health?.failed_or_denied_count ?? fallback.teamHealth.failedOrDeniedCount,
    },
    agentCards: mergeAgentCards(fallback.agentCards, payload.agent_cards ?? []),
  };
}

function mergeAgentCards(
  fallbackCards: TeamReadModel["agentCards"],
  apiCards: NonNullable<ApiTeamReadModel["agent_cards"]>,
): TeamReadModel["agentCards"] {
  const normalizedApiCards = new Map(
    apiCards.map((card) => [
      card.agent_id ?? "unknown",
      {
        agentId: card.agent_id ?? "unknown",
        displayName: card.display_name ?? "未知 Agent",
        role: card.role ?? card.agent_id ?? "unknown",
        profileVersion: card.profile_version ?? "unknown",
        skillPackageVersion: card.skill_package_version ?? "unknown",
        promptVersion: card.prompt_version ?? "unknown",
        contextSnapshotVersion: card.context_snapshot_version ?? "unknown",
        recentQualityScore: card.recent_quality_score ?? 0,
        failureCount: card.failure_count ?? 0,
        deniedActionCount: card.denied_action_count ?? 0,
        configDraftEntry: card.config_draft_entry ?? "governance_draft_only",
        weaknessTags: card.weakness_tags ?? [],
      },
    ]),
  );
  const merged = fallbackCards.map((fallbackCard) => {
    const apiCard = normalizedApiCards.get(fallbackCard.agentId);
    if (!apiCard) {
      return fallbackCard;
    }
    return {
      ...fallbackCard,
      ...apiCard,
      weaknessTags: apiCard.weaknessTags.length ? apiCard.weaknessTags : fallbackCard.weaknessTags,
    };
  });
  const fallbackIds = new Set(fallbackCards.map((card) => card.agentId));
  return [
    ...merged,
    ...Array.from(normalizedApiCards.values()).filter((card) => !fallbackIds.has(card.agentId)),
  ];
}

export async function loadAgentProfileReadModel(agentId: string): Promise<AgentProfileReadModel> {
  const fallback = buildTeamReadModel().agentProfileReadModels.find((item) => item.agentId === agentId);
  const payload = await fetchEnvelope<ApiAgentProfileReadModel>(`/api/team/${agentId}`);
  const fallbackPermissions = fallback?.toolPermissions ?? [];
  const deniedActions = Array.isArray(payload.denied_actions)
    ? payload.denied_actions.map((item) => ({ reasonCode: item.reason_code ?? "unknown" }))
    : fallback?.deniedActions ?? [];
  const failureRecords = Array.isArray(payload.failure_records)
    ? payload.failure_records.map((item) => typeof item === "string" ? item : item.reason_code ?? "unknown")
    : fallback?.failureRecords ?? [];

  return {
    agentId: payload.agent_id ?? fallback?.agentId ?? agentId,
    displayName: payload.display_name ?? fallback?.displayName ?? agentId,
    capabilitySummary: payload.capability_summary ?? fallback?.capabilitySummary ?? "",
    canDo: payload.can_do ?? fallback?.canDo ?? [],
    cannotDo: payload.cannot_do ?? fallback?.cannotDo ?? [],
    versions: {
      profileVersion: payload.profile_version ?? fallback?.versions.profileVersion ?? "unknown",
      skillPackageVersion: formatPermissionValue(payload.skill_package_version ?? fallback?.versions.skillPackageVersion ?? "unknown"),
      promptVersion: payload.prompt_version ?? fallback?.versions.promptVersion ?? "unknown",
      contextSnapshotVersion: formatContextSnapshotVersion(payload.context_snapshot_version ?? fallback?.versions.contextSnapshotVersion ?? "unknown"),
    },
    toolPermissions: normalizeAgentPermissionSummaries(payload, fallbackPermissions),
    weaknessTags: payload.weakness_tags ?? fallback?.weaknessTags ?? [],
    qualityMetrics: {
      schemaPassRate: payload.quality_metrics?.schema_pass_rate ?? fallback?.qualityMetrics.schemaPassRate ?? 0,
      evidenceQuality: payload.quality_metrics?.evidence_quality ?? fallback?.qualityMetrics.evidenceQuality ?? 0,
    },
    cfoAttributionRefs: payload.cfo_attribution_refs ?? fallback?.cfoAttributionRefs ?? [],
    deniedActions,
    failureRecords,
  };
}

function normalizeAgentPermissionSummaries(payload: ApiAgentProfileReadModel, fallback: string[]): string[] {
  const permissionRows = [
    ...formatPermissionInput("可读资料", payload.read_permissions),
    ...formatPermissionInput("可写权限", payload.write_permissions),
    ...formatPermissionInput("工具权限", payload.tool_permissions),
    ...formatPermissionInput("可请求服务", payload.service_permissions),
    ...formatPermissionInput("可提交协作命令", payload.collaboration_commands),
  ];
  return permissionRows.length ? permissionRows : fallback;
}

function formatPermissionInput(groupLabel: string, value: ApiPermissionInput): string[] {
  if (Array.isArray(value)) {
    return value
      .filter((item) => item.trim().length > 0)
      .map((item) => `${groupLabel}: ${formatPermissionValue(item)}`);
  }
  if (!isPermissionMap(value)) {
    return [];
  }
  return Object.entries(value).flatMap(([field, fieldValue]) => {
    const values = Array.isArray(fieldValue)
      ? fieldValue
      : typeof fieldValue === "string"
        ? [fieldValue]
        : [];
    const formattedValues = values
      .filter((item) => item.trim().length > 0)
      .map(formatPermissionValue);
    if (!formattedValues.length) {
      return [];
    }
    return `${formatPermissionField(field)}: ${formattedValues.join(" / ")}`;
  });
}

function isPermissionMap(value: ApiPermissionInput): value is ApiPermissionMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatPermissionField(field: string): string {
  const labels: Record<string, string> = {
    artifact_types: "可写产物",
    command_types: "可提交命令",
    comment_types: "可写评论",
    db_read_views: "可读业务视图",
    file_scopes: "可读资料范围",
    network_policy: "授权网络来源",
    proposal_types: "可提方案",
    skill_packages: "能力包",
    terminal_policy: "诊断权限",
  };
  return labels[field] ?? field.replace(/_/g, " ");
}

function formatPermissionValue(value: string): string {
  const labels: Record<string, string> = {
    active_skill_packages: "生效能力包",
    approved_public_sources: "授权公开来源",
    artifact_read_model: "产物只读视图",
    ask_question: "发起追问",
    business_materials: "业务资料",
    cio_decision_memo: "CIO 决策备忘",
    "cio-decision-synthesis": "CIO 决策综合能力包",
    "cfo-governance": "CFO 财务治理能力包",
    data_readiness: "数据就绪服务",
    "devops-incident-diagnostics": "系统事件诊断能力包",
    "event-catalyst-assessment": "事件催化评估能力包",
    "fundamental-quality-review": "基本面质量复核能力包",
    ICChairBrief: "IC 主席摘要",
    CIODecisionMemo: "CIO 决策备忘",
    "macro-regime-analysis": "宏观环境分析能力包",
    market_state: "市场状态服务",
    "quant-signal-review": "量化信号复核能力包",
    readonly_business_view: "只读业务视图",
    readonly_diagnostics: "只读诊断",
    "research-package-builder": "研究资料包构建能力包",
    request_reopen: "建议重开",
    request_view_update: "要求更新观点",
    risk: "风控服务",
    "risk-gate-review": "独立风控复核能力包",
  };
  return labels[value] ?? value.replace(/_/g, " ");
}

function formatContextSnapshotVersion(value: string): string {
  const match = value.match(/^ctx-v(\d+)$/);
  if (match) {
    return `配置快照 v${match[1]}`;
  }
  return value.replace(/_/g, " ");
}

export async function loadAgentCapabilityConfigReadModel(agentId: string): Promise<CapabilityConfigReadModel> {
  const fallback = buildTeamReadModel().capabilityConfigReadModel;
  const payload = await fetchEnvelope<ApiCapabilityConfigReadModel>(`/api/team/${agentId}/capability-config`);

  return {
    agentId: payload.agent_id ?? fallback.agentId,
    editableFields: (payload.editable_fields ?? []).map((item) => typeof item === "string" ? item : item.field ?? "unknown"),
    forbiddenDirectUpdateReason: payload.forbidden_direct_update_reason ?? fallback.forbiddenDirectUpdateReason,
    effectiveScopeOptions: payload.effective_scope_options ?? fallback.effectiveScopeOptions,
  };
}

export async function loadKnowledgeReadModel(): Promise<KnowledgeReadModel> {
  const payload = await fetchEnvelope<ApiMemoryReadModel[]>("/api/knowledge/memory-items");
  const memoryResults = payload.map((item) => ({
    memoryId: item.memory_id ?? "memory",
    currentVersionId: item.current_version_id ?? "memory-version",
    title: item.title ?? "未命名经验",
    relationSummary: item.relations?.[0]
      ? `${item.relations[0].relation_type ?? "related_to"} ${item.relations[0].target_ref ?? "unknown"}`
      : "无关联",
    sensitivity: item.sensitivity ?? "public_internal",
    extractionStatus: item.extraction_status ?? item.status ?? "unknown",
    promotionState: item.promotion_state ?? "candidate",
    tags: item.tags ?? [],
  }));

  return {
    ...buildEmptyKnowledgeReadModel(),
    memoryCollections: payload.map((item) => ({
      collectionId: item.memory_id ?? "memory",
      title: item.title ?? "未命名经验",
      resultCount: Math.max(item.relations?.length ?? 0, 1),
    })),
    memoryResults,
    relationGraph: payload.flatMap((item) =>
      (item.relations ?? []).map((relation) => ({
        sourceMemoryId: item.memory_id ?? "memory",
        targetRef: relation.target_ref ?? "unknown",
        relationType: relation.relation_type ?? "related_to",
        reason: relation.reason ?? "API relation",
      })),
    ),
    contextInjectionInspector: payload.length
      ? payload.map((item) => ({
          contextSnapshotId: item.current_version_id ?? "ctx-api",
          sourceRef: item.memory_id ?? "memory",
          whyIncluded: item.why_included ?? "fenced_background_context_only",
          redactionStatus: "applied",
          deniedRefs: [],
        }))
      : [],
  };
}

export async function createMemoryItem(contentMarkdown: string): Promise<MemoryWriteApiReadModel> {
  const payload = await fetchEnvelope<ApiMemoryReadModel>("/api/knowledge/memory-items", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_type: "owner_note",
      source_refs: ["knowledge-ui"],
      content_markdown: contentMarkdown,
      suggested_memory_type: "research_note",
      tags: ["owner_capture", "research"],
      sensitivity: "public_internal",
      client_seen_context_snapshot_id: "ctx-v1",
    }),
  });

  return {
    memoryId: payload.memory_id ?? "memory",
    currentVersionId: payload.current_version_id ?? "memory-version",
  };
}

export async function applyMemoryOrganizeSuggestion(
  memoryId: string,
  currentVersionId: string,
  tags: string[],
): Promise<MemoryRelationApiReadModel> {
  const payload = await fetchEnvelope<{
    relation_id?: string;
    source_memory_id?: string;
    memory_id?: string;
    target_ref?: string;
    relation_type?: string;
  }>(`/api/knowledge/memory-items/${memoryId}/relations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_ref: `memory-tag:${tags.join("/") || "owner-confirmed"}`,
      relation_type: "supports",
      reason: `Owner confirmed tags: ${tags.join("/") || "owner-confirmed"}`,
      evidence_refs: [memoryId],
      client_seen_version_id: currentVersionId,
    }),
  });

  return {
    relationId: payload.relation_id ?? "relation",
    sourceMemoryId: payload.source_memory_id ?? payload.memory_id ?? memoryId,
    targetRef: payload.target_ref ?? "knowledge-method-1",
    relationType: payload.relation_type ?? "supports",
  };
}

export async function loadTraceDebugReadModel(workflowId: string): Promise<TraceDebugReadModel> {
  const emptyTrace = buildUnavailableTraceDebugReadModel(workflowId);
  const [agentRuns, events, handoffs] = await Promise.all([
    fetchEnvelope<ApiAgentRunReadModel[]>(`/api/workflows/${workflowId}/agent-runs`),
    fetchEnvelope<ApiCollaborationEventReadModel[]>(`/api/workflows/${workflowId}/collaboration-events`),
    fetchEnvelope<ApiHandoffReadModel[]>(`/api/workflows/${workflowId}/handoffs`),
  ]);

  return {
    ...emptyTrace,
    workflowId,
    agentRunTree: agentRuns.map((item) => ({
      runId: item.agent_run_id ?? "run",
      parentRunId: item.parent_run_id ?? null,
      stage: item.stage ?? "unknown",
      profileVersion: item.profile_version ?? "unknown",
      contextSlice: item.context_slice_id ?? item.context_snapshot_id ?? "ctx-api",
      businessSummary: item.run_goal ?? undefined,
      agentId: item.agent_id ?? undefined,
      status: item.status ?? undefined,
    })),
    events: events.map((item) => ({
      eventType: item.event_type ?? "event",
      summary: String(item.payload?.business_summary ?? item.summary ?? "无摘要"),
    })),
    handoffs: handoffs.map((item) => ({
      from: item.from_stage ?? "unknown",
      to: item.to_stage_or_agent ?? "unknown",
      blockers: item.blockers ?? [],
      openQuestions: item.open_questions ?? [],
    })),
  };
}

export async function loadInvestmentDossierReadModel(workflowId: string): Promise<InvestmentDossierReadModel> {
  const fallback = buildUnavailableInvestmentDossierReadModel(workflowId);
  const payload = await fetchEnvelope<ApiInvestmentDossierReadModel>(`/api/workflows/${workflowId}/dossier`);
  const forbiddenActions = Object.fromEntries(
    Object.entries(payload.forbidden_actions ?? fallback.forbiddenActions).map(([key, value]) => [
      key,
      {
        actionVisible: value.action_visible ?? value.actionVisible ?? false,
        reasonCode: value.reason_code ?? value.reasonCode ?? key,
      },
    ]),
  );

  return {
    workflow: {
      workflowId: payload.workflow?.workflow_id ?? workflowId,
      title: payload.workflow?.title ?? fallback.workflow.title,
      currentStage: payload.workflow?.current_stage ?? fallback.workflow.currentStage,
      state: payload.workflow?.state ?? fallback.workflow.state,
    },
    stageRail: (payload.stage_rail ?? []).length
      ? (payload.stage_rail ?? []).map((stage) => ({
          stage: stage.stage ?? "S0",
          nodeStatus: stage.node_status ?? "not_started",
          reasonCode: stage.reason_code ?? null,
          artifactCount: stage.artifact_count ?? 0,
        }))
      : fallback.stageRail,
    chairBrief: {
      decisionQuestion: payload.chair_brief?.decision_question ?? fallback.chairBrief.decisionQuestion,
      keyTensions: payload.chair_brief?.key_tensions ?? fallback.chairBrief.keyTensions,
      noPresetDecisionAttestation: payload.chair_brief?.no_preset_decision_attestation ?? fallback.chairBrief.noPresetDecisionAttestation,
    },
    analystStanceMatrix: (payload.analyst_stance_matrix ?? []).length
      ? (payload.analyst_stance_matrix ?? []).map((row) => ({
          role: row.role ?? "Analyst",
          direction: row.direction ?? String(row.direction_score ?? "待定"),
          confidence: row.confidence ?? 0,
          evidenceQuality: row.evidence_quality ?? undefined,
          hardDissent: row.hard_dissent ?? false,
          hardDissentReason: row.hard_dissent_reason ?? undefined,
          thesis: row.thesis ?? undefined,
        }))
      : fallback.analystStanceMatrix,
    dataReadiness: {
      qualityBand: payload.data_readiness?.quality_band ?? fallback.dataReadiness.qualityBand,
      decisionCoreStatus: payload.data_readiness?.decision_core_status ?? fallback.dataReadiness.decisionCoreStatus,
      executionCoreStatus: payload.data_readiness?.execution_core_status ?? fallback.dataReadiness.executionCoreStatus,
      issues: payload.data_readiness?.issues ?? fallback.dataReadiness.issues,
      lineageRefs: payload.data_readiness?.lineage_refs ?? fallback.dataReadiness.lineageRefs,
      ownerSummary: payload.data_readiness?.owner_summary ?? fallback.dataReadiness.ownerSummary,
      sourceStatus: payload.data_readiness?.source_status?.map((item) => ({
        sourceName: item.source_name ?? "未返回数据来源",
        sourceRef: item.source_ref ?? "",
        requiredUsage: item.required_usage ?? "research",
        requestedFields: item.requested_fields ?? [],
        obtainedFields: item.obtained_fields ?? [],
        missingFields: item.missing_fields ?? [],
        status: item.status ?? "missing",
        qualityLabel: item.quality_label ?? "未返回状态",
        evidenceRef: item.evidence_ref ?? item.source_ref ?? "",
      })) ?? fallback.dataReadiness.sourceStatus,
      dataGaps: payload.data_readiness?.data_gaps?.map((item) => ({
        gap: item.gap ?? "未返回数据缺口",
        affectsStage: item.affects_stage ?? "S1",
        impact: item.impact ?? "无法判断影响",
        nextAction: item.next_action ?? "重试数据采集并复核",
      })) ?? fallback.dataReadiness.dataGaps,
    },
    rolePayloadDrilldowns: (payload.role_payload_drilldowns ?? []).length
      ? (payload.role_payload_drilldowns ?? []).map((item) => ({
          role: item.role ?? "Analyst",
          highlights: item.highlights ?? [],
          hardDissentReason: item.hard_dissent_reason ?? undefined,
          thesis: item.thesis ?? undefined,
          supportingEvidenceRefs: item.supporting_evidence_refs ?? [],
          counterEvidenceRefs: item.counter_evidence_refs ?? [],
          keyRisks: item.key_risks ?? [],
          applicableConditions: item.applicable_conditions ?? [],
          invalidationConditions: item.invalidation_conditions ?? [],
          suggestedActionImplication: item.suggested_action_implication ?? undefined,
          rolePayload: item.role_payload ?? {},
        }))
      : fallback.rolePayloadDrilldowns,
    consensus: {
      score: payload.consensus?.score ?? payload.consensus?.consensus_score ?? fallback.consensus.score,
      actionConviction: payload.consensus?.action_conviction ?? fallback.consensus.actionConviction,
      thresholdLabel: payload.consensus?.threshold_label ?? fallback.consensus.thresholdLabel,
    },
    debate: {
      roundsUsed: payload.debate?.rounds_used ?? fallback.debate.roundsUsed,
      retainedHardDissent: payload.debate?.retained_hard_dissent ?? fallback.debate.retainedHardDissent,
      riskReviewRequired: payload.debate?.risk_review_required ?? fallback.debate.riskReviewRequired,
      issues: payload.debate?.issues ?? fallback.debate.issues,
      viewChanges: payload.debate?.view_changes ?? fallback.debate.viewChanges,
      cioSynthesis: payload.debate?.cio_synthesis ?? fallback.debate.cioSynthesis,
      unresolvedDissent: payload.debate?.unresolved_dissent ?? fallback.debate.unresolvedDissent,
      rounds: payload.debate?.rounds?.map((round) => ({
        roundNo: round.round_no,
        issue: round.issue,
        outcome: round.outcome,
      })) ?? fallback.debate.rounds,
      ownerSummary: payload.debate?.owner_summary ?? fallback.debate.ownerSummary,
      statusSummary: payload.debate?.status_summary
        ? {
            roundsUsed: payload.debate.status_summary.rounds_used ?? payload.debate.rounds_used ?? fallback.debate.roundsUsed,
            retainedHardDissent: payload.debate.status_summary.retained_hard_dissent ?? payload.debate.retained_hard_dissent ?? fallback.debate.retainedHardDissent,
            riskReviewRequired: payload.debate.status_summary.risk_review_required ?? payload.debate.risk_review_required ?? fallback.debate.riskReviewRequired,
            consensusScore: payload.debate.status_summary.consensus_score,
            actionConviction: payload.debate.status_summary.action_conviction,
          }
        : fallback.debate.statusSummary,
      coreDisputes: payload.debate?.core_disputes?.map((item) => ({
        title: item.title ?? "后端未返回分歧标题",
        whyItMatters: item.why_it_matters ?? "后端未返回辩论详情",
        involvedRoles: item.involved_roles ?? [],
        currentConclusion: item.current_conclusion ?? "后端未返回辩论详情",
        requiredEvidence: item.required_evidence ?? [],
      })) ?? fallback.debate.coreDisputes,
      viewChangeDetails: payload.debate?.view_change_details?.map((item) => ({
        role: item.role ?? "未标明岗位",
        before: item.before ?? "后端未返回辩论详情",
        after: item.after ?? "后端未返回辩论详情",
        reason: item.reason ?? "后端未返回辩论详情",
        impact: item.impact ?? "后端未返回辩论详情",
      })) ?? fallback.debate.viewChangeDetails,
      retainedDissentDetails: payload.debate?.retained_dissent_details?.map((item) => ({
        sourceRole: item.source_role ?? "未标明岗位",
        dissent: item.dissent ?? "后端未返回辩论详情",
        counterRisks: item.counter_risks ?? [],
        handling: item.handling ?? "后端未返回辩论详情",
        forbiddenActions: item.forbidden_actions ?? [],
      })) ?? fallback.debate.retainedDissentDetails,
      roundDetails: payload.debate?.round_details?.map((item) => ({
        roundNo: item.round_no ?? 0,
        issue: item.issue ?? "后端未返回辩论详情",
        participants: item.participants ?? [],
        inputEvidence: item.input_evidence ?? [],
        outcome: item.outcome ?? "后端未返回辩论详情",
        unresolvedQuestions: item.unresolved_questions ?? [],
      })) ?? fallback.debate.roundDetails,
      nextActions: payload.debate?.next_actions?.map((item) => ({
        action: item.action ?? "后端未返回辩论详情",
        owner: item.owner ?? "未标明负责人",
        completionSignal: item.completion_signal ?? "后端未返回辩论详情",
        nextStage: item.next_stage ?? "后端未返回辩论详情",
      })) ?? fallback.debate.nextActions,
    },
    optimizerDeviation: {
      singleNameDeviation: payload.optimizer_deviation?.single_name_deviation ?? fallback.optimizerDeviation.singleNameDeviation,
      portfolioDeviation: payload.optimizer_deviation?.portfolio_deviation ?? fallback.optimizerDeviation.portfolioDeviation,
      recommendation: payload.optimizer_deviation?.recommendation ?? fallback.optimizerDeviation.recommendation,
    },
    cioDecision: payload.cio_decision ? {
      decision: payload.cio_decision.decision ?? "observe",
      rationale: payload.cio_decision.decision_rationale,
      deviationReason: payload.cio_decision.deviation_reason,
      conditions: payload.cio_decision.conditions ?? [],
      monitoringPoints: payload.cio_decision.monitoring_points ?? [],
      riskHandoffNotes: payload.cio_decision.risk_handoff_notes,
    } : fallback.cioDecision,
    decisionGuard: payload.decision_guard ? {
      majorDeviation: payload.decision_guard.major_deviation,
      singleNameDeviationPp: payload.decision_guard.single_name_deviation_pp,
      portfolioActiveDeviation: payload.decision_guard.portfolio_active_deviation,
      lowActionConviction: payload.decision_guard.low_action_conviction,
      retainedHardDissent: payload.decision_guard.retained_hard_dissent,
      dataQualityBlockers: payload.decision_guard.data_quality_blockers ?? [],
      reasonCodes: payload.decision_guard.reason_codes ?? [],
    } : fallback.decisionGuard,
    riskReview: {
      reviewResult: payload.risk_review?.review_result ?? fallback.riskReview.reviewResult,
      repairability: payload.risk_review?.repairability ?? fallback.riskReview.repairability,
      ownerExceptionRequired: payload.risk_review?.owner_exception_required ?? fallback.riskReview.ownerExceptionRequired,
      reasonCodes: payload.risk_review?.reason_codes ?? fallback.riskReview.reasonCodes,
    },
    paperExecution: {
      status: payload.paper_execution?.status ?? fallback.paperExecution.status,
      pricingMethod: payload.paper_execution?.pricing_method ?? fallback.paperExecution.pricingMethod,
      window: payload.paper_execution?.window ?? fallback.paperExecution.window,
      fees: formatApiFees(payload.paper_execution?.fees, fallback.paperExecution.fees),
      taxes: formatApiFees(payload.paper_execution?.taxes, fallback.paperExecution.taxes ?? ""),
      slippage: formatApiFees(payload.paper_execution?.slippage, fallback.paperExecution.slippage ?? ""),
      tPlusOne: payload.paper_execution?.t_plus_one ?? fallback.paperExecution.tPlusOne,
    },
    attribution: {
      summary: payload.attribution?.summary ?? fallback.attribution.summary,
      links: payload.attribution?.links ?? fallback.attribution.links,
      marketResult: payload.attribution?.market_result ?? fallback.attribution.marketResult,
      decisionQuality: payload.attribution?.decision_quality ?? fallback.attribution.decisionQuality,
      executionQuality: payload.attribution?.execution_quality ?? fallback.attribution.executionQuality,
      riskQuality: payload.attribution?.risk_quality ?? fallback.attribution.riskQuality,
      dataQuality: payload.attribution?.data_quality ?? fallback.attribution.dataQuality,
      evidenceQuality: payload.attribution?.evidence_quality ?? fallback.attribution.evidenceQuality,
      conditionHit: payload.attribution?.condition_hit ?? fallback.attribution.conditionHit,
      improvementItems: payload.attribution?.improvement_items ?? fallback.attribution.improvementItems,
      needsCfoInterpretation: payload.attribution?.needs_cfo_interpretation ?? fallback.attribution.needsCfoInterpretation,
    },
    evidenceMap: {
      artifactRefs: payload.evidence_map?.artifact_refs ?? fallback.evidenceMap.artifactRefs,
      dataRefs: payload.evidence_map?.data_refs ?? fallback.evidenceMap.dataRefs,
      sourceQuality: payload.evidence_map?.source_quality?.map((item) => typeof item === "string" ? item : ({
        source: item.source,
        usedFor: item.used_for ?? item.usedFor,
        quality: item.quality,
      })) ?? fallback.evidenceMap.sourceQuality,
      conflictRefs: payload.evidence_map?.conflict_refs ?? fallback.evidenceMap.conflictRefs,
      supportingEvidenceOnlyRefs: payload.evidence_map?.supporting_evidence_only_refs ?? fallback.evidenceMap.supportingEvidenceOnlyRefs,
    },
    forbiddenActions,
    traceRoute: `/investment/${workflowId}/trace`,
  };
}

export async function loadGovernanceReadModel(): Promise<GovernanceReadModel> {
  const fallback = buildGovernanceReadModel();
  const [tasks, approvals, changes] = await Promise.all([
    fetchEnvelope<ApiTaskCenterReadModel>("/api/tasks"),
    fetchEnvelope<ApiApprovalCenterReadModel>("/api/approvals"),
    fetchEnvelope<ApiGovernanceChangeReadModel[]>("/api/governance/changes"),
  ]);
  const taskCenter = Array.isArray(tasks.task_center)
    ? tasks.task_center.map((task) => ({
        taskId: task.task_id ?? "task",
        taskType: task.task_type ?? "system_task",
        currentState: task.current_state ?? "ready",
        reasonCode: task.reason_code ?? "unknown",
        dueDate: task.due_date,
        riskHint: task.risk_hint,
        blockedReason: task.blocked_reason,
      }))
    : fallback.taskCenter;
  const approvalCenter = Array.isArray(approvals.approval_center)
    ? (cachedApprovalCenter = approvals.approval_center ?? [], cachedApprovalCenter).map((approval) => ({
        approvalId: approval.approval_id ?? "approval",
        kind: approval.approval_type ?? "approval",
        triggerReason: approval.trigger_reason ?? "unknown",
        subject: approval.subject,
        deadline: approval.deadline,
        packet: {
          comparisonAnalysis: true,
          impactScope: approval.effective_scope ?? "new_task",
          alternatives: ["approved", "rejected", "request_changes"],
          recommendation: approval.recommended_decision ?? approval.decision ?? "request_changes",
        },
      }))
    : fallback.approvalCenter;

  return {
    ...fallback,
    taskCenter,
    approvalCenter,
    unifiedTodos: buildUnifiedTodoItems({ taskCenter, approvalCenter }),
    governanceChanges: changes.map((change) => ({
          changeId: change.change_id ?? "change",
          changeType: change.change_type ?? "unknown",
          impactLevel: change.impact_level ?? "medium",
          state: change.state ?? "draft",
          effectiveScope: change.effective_scope ?? "new_task",
        })),
  };
}

export async function loadApprovalRecordReadModel(approvalId: string): Promise<ApprovalRecordReadModel> {
  const fallback = buildApprovalRecordReadModel({ approvalId });
  const cachedApproval = cachedApprovalCenter.find((item) => item.approval_id === approvalId);
  if (cachedApproval) {
    return buildApprovalRecordFromApi(cachedApproval, fallback);
  }
  const payload = await fetchEnvelope<ApiApprovalCenterReadModel>("/api/approvals");
  cachedApprovalCenter = payload.approval_center ?? cachedApprovalCenter;
  const approval = (payload.approval_center ?? []).find((item) => item.approval_id === approvalId);

  if (!approval) {
    return buildApprovalRecordReadModel({
      approvalId,
      subject: `审批包 ${approvalId}`,
      triggerReason: "approval_not_found",
      recommendation: "request_changes",
      comparisonOptions: ["等待服务端返回完整审批材料"],
      riskAndImpact: ["当前审批记录未出现在审批列表"],
      evidenceRefs: [],
      allowedActions: [],
    });
  }

  return buildApprovalRecordFromApi(approval, fallback);
}

function buildApprovalRecordFromApi(
  approval: NonNullable<ApiApprovalCenterReadModel["approval_center"]>[number],
  fallback: ApprovalRecordReadModel,
) {
  return buildApprovalRecordReadModel({
    approvalId: approval.approval_id ?? fallback.approvalId,
    subject: approval.subject ?? fallback.subject,
    triggerReason: approval.trigger_reason ?? fallback.triggerReason,
    recommendation: approval.recommended_decision ?? approval.decision ?? fallback.recommendation,
    alternatives: normalizeApiTextList(approval.alternatives, fallback.alternatives),
    comparisonOptions: normalizeApiTextList(approval.comparison_options, fallback.comparisonOptions),
    impactScope: approval.effective_scope ?? fallback.impactScope,
    riskAndImpact: normalizeApiTextList(approval.risk_and_impact, fallback.riskAndImpact),
    timeoutDisposition: approval.timeout_disposition ?? approval.timeout_policy ?? fallback.timeoutDisposition,
    rollbackRef: approval.rollback_ref ?? fallback.rollbackRef,
    evidenceRefs: approval.evidence_refs ?? fallback.evidenceRefs,
    traceRoute: approval.trace_route ?? fallback.traceRoute,
    allowedActions: approval.allowed_actions ?? fallback.allowedActions,
  });
}

function normalizeApiTextList(value: unknown, fallback: string[]) {
  if (Array.isArray(value)) {
    const normalized = value.map(formatApiTextValue).filter(Boolean);
    return normalized.length ? normalized : fallback;
  }
  if (value && typeof value === "object") {
    const normalized = Object.entries(value as Record<string, unknown>).map(([key, item]) => `${formatApiFieldName(key)} ${formatApiTextValue(item)}`);
    return normalized.length ? normalized : fallback;
  }
  if (typeof value === "string" && value.trim()) {
    return [value];
  }
  return fallback;
}

function formatApiFees(value: unknown, fallback: string): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return value === 0 ? "未产生" : String(value);
  }
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, item]) => item !== null && item !== undefined);
    if (!entries.length) {
      return "未产生";
    }
    return entries.map(([key, item]) => `${formatApiFieldName(key)} ${formatApiTextValue(item)}`).join(" · ");
  }
  return fallback;
}

function formatApiTextValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value !== "object") {
    return String(value);
  }
  return Object.entries(value as Record<string, unknown>)
    .map(([key, item]) => `${formatApiFieldName(key)} ${formatApiTextValue(item)}`)
    .join(" · ");
}

function formatApiFieldName(value: string) {
  const labels: Record<string, string> = {
    option: "方案",
    target_weight: "目标权重",
    risk: "风险",
    single_name_deviation_pp: "单股偏离",
    portfolio_active_deviation: "组合主动偏离",
    scope: "适用范围",
  };
  return labels[value] ?? value;
}

export async function loadFinanceOverviewReadModel(): Promise<FinanceOverviewReadModel> {
  const fallback = buildFinanceOverviewReadModel();
  const payload = await fetchEnvelope<ApiFinanceOverviewReadModel>("/api/finance/overview");

  return {
    ...fallback,
    assets: (payload.asset_profile ?? []).map((item) => ({
      label: item.asset_type ?? "asset",
      value: `${item.valuation?.amount ?? 0} ${item.valuation?.currency ?? "CNY"}`,
      status: item.boundary_label ?? "finance_planning_only",
    })),
    health: {
      liquidity: String(payload.finance_health?.liquidity ?? fallback.health.liquidity),
      debtRatio: fallback.health.debtRatio,
      riskBudget: payload.finance_health?.risk_budget?.budget_ref ?? fallback.health.riskBudget,
      stress: payload.finance_health?.stress_test_summary ?? fallback.health.stress,
    },
    reminders: (payload.manual_todo ?? []).map((item) => item.risk_hint ?? "manual_todo"),
  };
}

export async function updateFinanceAsset(input: FinanceAssetUpdateInput = {}): Promise<FinanceAssetUpdateApiReadModel> {
  const assetType = input.assetType ?? "cash";
  const amount = Number.isFinite(input.amount) ? Number(input.amount) : 1000000;
  const payload = await fetchEnvelope<{
    asset_id?: string;
    asset_type?: string;
  }>("/api/finance/assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_id: input.assetId ?? "cash-owner-ui",
      asset_type: assetType,
      valuation: { amount, currency: "CNY" },
      valuation_date: input.valuationDate ?? "2026-05-06",
      source: input.source ?? "owner_ui",
      client_seen_version: 1,
    }),
  });

  return {
    assetId: payload.asset_id ?? "asset",
    assetType: payload.asset_type ?? assetType,
  };
}

export async function loadDevOpsHealthReadModel(): Promise<DevOpsHealthReadModel> {
  const fallback = buildDevOpsHealthReadModel();
  const payload = await fetchEnvelope<ApiDevOpsHealthReadModel>("/api/devops/health");

  return {
    routineChecks: (payload.routine_checks ?? []).map((item) => ({
      checkId: item.check_id ?? "check",
      status: item.status ?? "unknown",
    })),
    incidents: (payload.incidents ?? []).map((item) => ({
      incidentId: item.incident_id ?? "incident",
      status: item.status ?? "unknown",
      incidentType: item.incident_type ?? "unknown",
    })),
    recovery: (payload.recovery ?? []).map((item) => ({
      planId: item.plan_id ?? "recovery",
      technicalRecoveryStatus: item.technical_recovery_status ?? "unknown",
      investmentResumeAllowed: item.investment_resume_allowed ?? false,
    })),
  };
}

export async function createRequestBrief(rawText: string): Promise<RequestBriefApiReadModel> {
  const payload = await fetchEnvelope<{
    brief_id?: string;
    route_type?: string;
    suggested_semantic_lead?: string;
    process_authority?: string;
    predicted_outputs?: string[];
    forbidden_action_reason_code?: string | null;
    owner_confirmation_status?: string;
    version?: number;
  }>("/api/requests/briefs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_text: rawText,
      source: "owner_command",
      requested_scope: inferRequestedScope(rawText),
      authorization_boundary: "request_brief_only",
    }),
  });

  return {
    briefId: payload.brief_id ?? "",
    routeType: payload.route_type ?? "manual_todo",
    semanticLead: payload.suggested_semantic_lead,
    processAuthority: payload.process_authority,
    expectedArtifacts: payload.predicted_outputs,
    reasonCode: payload.forbidden_action_reason_code,
    ownerConfirmationStatus: payload.owner_confirmation_status,
    version: payload.version ?? 1,
  };
}

export async function confirmRequestBrief(briefId: string, version: number): Promise<TaskCardApiReadModel> {
  const payload = await fetchEnvelope<{
    task_id?: string;
    task_type?: string;
    current_state?: string;
    reason_code?: string;
    workflow_id?: string | null;
  }>(`/api/requests/briefs/${briefId}/confirmation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision: "confirm", client_seen_version: version }),
  });

  return {
    taskId: payload.task_id ?? "task",
    taskType: payload.task_type ?? "manual_todo",
    currentState: payload.current_state ?? "draft",
    reasonCode: payload.reason_code ?? "unknown",
    workflowId: payload.workflow_id ?? undefined,
  };
}

function inferRequestedScope(rawText: string) {
  if (rawText.includes("热点") || rawText.includes("学习")) {
    return { intent: "learn_hot_event", asset_scope: "a_share_common_stock", target_action: "research" };
  }
  if (rawText.includes("下单") || rawText.toLowerCase().includes("trade") || rawText.includes("腾讯")) {
    return { intent: "formal_investment_decision", asset_scope: "non_a_asset", target_action: "trade" };
  }
  if (rawText.includes("能力") || rawText.includes("Prompt") || rawText.includes("Skill")) {
    return { intent: "agent_capability_change", asset_scope: "system_config", target_action: "governance_change" };
  }
  return { intent: "formal_investment_decision", asset_scope: "a_share_common_stock", target_action: "approve_trade" };
}

export async function createCapabilityDraft(agentId: string): Promise<CapabilityDraftApiReadModel> {
  const payload = await fetchEnvelope<{
    draft_id?: string;
    governance_change_ref?: string;
    impact_level?: string;
    effective_scope?: string;
  }>(`/api/team/${agentId}/capability-drafts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      agent_id: agentId,
      draft_title: "能力提升方案",
      change_set: { model_route: "balanced" },
      impact_level_hint: "high",
      validation_plan_refs: ["schema"],
      rollback_plan_ref: "rollback-ui",
      effective_scope: "new_task",
      client_seen_profile_version: "1.0.0",
      client_seen_context_snapshot_id: "ctx-v1",
    }),
  });

  return {
    draftId: payload.draft_id ?? "draft",
    governanceChangeRef: payload.governance_change_ref ?? "gov-change",
    impactLevel: payload.impact_level ?? "high",
    effectiveScope: payload.effective_scope ?? "new_task",
  };
}

export async function submitApprovalDecision(approvalId: string, decision: string): Promise<ApprovalDecisionApiReadModel> {
  const payload = await fetchEnvelope<{
    approval_id?: string;
    decision?: string;
    effective_scope?: string;
  }>(`/api/approvals/${approvalId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, client_seen_version: 1 }),
  });

  return {
    approvalId: payload.approval_id ?? approvalId,
    decision: payload.decision ?? decision,
    effectiveScope: payload.effective_scope ?? "new_task",
  };
}
