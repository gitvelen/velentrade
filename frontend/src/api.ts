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
  buildInvestmentDossierReadModel,
  buildKnowledgeReadModel,
  buildApprovalRecordReadModel,
  buildTeamReadModel,
  buildTraceDebugReadModel,
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
  tool_permissions?: string[];
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
  tags?: string[];
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
  stage?: string;
  profile_version?: string;
  context_snapshot_id?: string;
};

type ApiCollaborationEventReadModel = {
  event_type?: string;
  summary?: string;
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
  routine_checks?: Array<{ check_id?: string; status?: string }>;
  incidents?: Array<{ incident_id?: string; status?: string; incident_type?: string }>;
  recovery?: Array<{ plan_id?: string; investment_resume_allowed?: boolean }>;
};

type ApiTaskCenterReadModel = {
  task_center?: Array<{
    task_id?: string;
    task_type?: string;
    current_state?: string;
    reason_code?: string;
  }>;
};

type ApiApprovalCenterReadModel = {
  approval_center?: Array<{
    approval_id?: string;
    approval_type?: string;
    subject?: string;
    trigger_reason?: string;
    effective_scope?: string;
    recommended_decision?: string;
    decision?: string;
    alternatives?: string[];
    comparison_options?: string[];
    risk_and_impact?: string[];
    timeout_disposition?: string;
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
    hard_dissent?: boolean;
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
  };
  role_payload_drilldowns?: Array<{
    role?: string;
    highlights?: string[];
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
  };
  optimizer_deviation?: {
    single_name_deviation?: string;
    portfolio_deviation?: string;
    recommendation?: string;
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
    fees?: string;
    t_plus_one?: string;
  };
  attribution?: {
    summary?: string;
    links?: string[];
  };
};

export type RequestBriefApiReadModel = {
  briefId: string;
  routeType: string;
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

  return {
    agentId: payload.agent_id ?? fallback?.agentId ?? agentId,
    displayName: payload.display_name ?? fallback?.displayName ?? agentId,
    capabilitySummary: payload.capability_summary ?? fallback?.capabilitySummary ?? "",
    canDo: payload.can_do ?? fallback?.canDo ?? [],
    cannotDo: payload.cannot_do ?? fallback?.cannotDo ?? [],
    versions: {
      profileVersion: payload.profile_version ?? fallback?.versions.profileVersion ?? "unknown",
      skillPackageVersion: payload.skill_package_version ?? fallback?.versions.skillPackageVersion ?? "unknown",
      promptVersion: payload.prompt_version ?? fallback?.versions.promptVersion ?? "unknown",
      contextSnapshotVersion: payload.context_snapshot_version ?? fallback?.versions.contextSnapshotVersion ?? "unknown",
    },
    toolPermissions: payload.tool_permissions ?? fallback?.toolPermissions ?? [],
    weaknessTags: payload.weakness_tags ?? fallback?.weaknessTags ?? [],
    qualityMetrics: {
      schemaPassRate: payload.quality_metrics?.schema_pass_rate ?? fallback?.qualityMetrics.schemaPassRate ?? 0,
      evidenceQuality: payload.quality_metrics?.evidence_quality ?? fallback?.qualityMetrics.evidenceQuality ?? 0,
    },
    cfoAttributionRefs: payload.cfo_attribution_refs ?? fallback?.cfoAttributionRefs ?? [],
    deniedActions: (payload.denied_actions ?? []).map((item) => ({ reasonCode: item.reason_code ?? "unknown" })),
    failureRecords: (payload.failure_records ?? fallback?.failureRecords ?? []).map((item) =>
      typeof item === "string" ? item : item.reason_code ?? "unknown",
    ),
  };
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
  const fallback = buildKnowledgeReadModel();
  const payload = await fetchEnvelope<ApiMemoryReadModel[]>("/api/knowledge/memory-items");
  const firstMemoryId = payload[0]?.memory_id ?? fallback.memoryResults[0]?.memoryId ?? "memory";

  return {
    ...fallback,
    memoryCollections: payload.length
      ? payload.map((item) => ({
          collectionId: item.memory_id ?? "memory",
          title: item.title ?? "未命名记忆",
          resultCount: Math.max(item.relations?.length ?? 0, 1),
        }))
      : fallback.memoryCollections,
    memoryResults: payload.length
      ? payload.map((item) => ({
          memoryId: item.memory_id ?? "memory",
          currentVersionId: item.current_version_id ?? "memory-version",
          title: item.title ?? "未命名记忆",
          relationSummary: item.relations?.[0]
            ? `${item.relations[0].relation_type ?? "related_to"} ${item.relations[0].target_ref ?? "unknown"}`
            : "无关联",
          sensitivity: item.sensitivity ?? "public_internal",
          extractionStatus: item.extraction_status ?? item.status ?? "unknown",
          promotionState: item.promotion_state ?? "candidate",
          tags: item.tags ?? [],
        }))
      : fallback.memoryResults,
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
      : fallback.contextInjectionInspector,
    organizeSuggestions: fallback.organizeSuggestions.map((item) => ({
      ...item,
      targetMemoryRefs: [firstMemoryId],
    })),
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
  _tags: string[],
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
      target_ref: "knowledge-method-1",
      relation_type: "supports",
      reason: "Owner applied organize suggestion from Knowledge workspace",
      evidence_refs: ["knowledge_memory_workspace"],
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
  const fallback = buildTraceDebugReadModel();
  const [agentRuns, events, handoffs] = await Promise.all([
    fetchEnvelope<ApiAgentRunReadModel[]>(`/api/workflows/${workflowId}/agent-runs`),
    fetchEnvelope<ApiCollaborationEventReadModel[]>(`/api/workflows/${workflowId}/collaboration-events`),
    fetchEnvelope<ApiHandoffReadModel[]>(`/api/workflows/${workflowId}/handoffs`),
  ]);

  return {
    ...fallback,
    workflowId,
    agentRunTree: agentRuns.length
      ? agentRuns.map((item) => ({
          runId: item.agent_run_id ?? "run",
          parentRunId: item.parent_run_id ?? null,
          stage: item.stage ?? "unknown",
          profileVersion: item.profile_version ?? "unknown",
          contextSlice: item.context_snapshot_id ?? "ctx-api",
        }))
      : fallback.agentRunTree,
    events: events.length
      ? events.map((item) => ({
          eventType: item.event_type ?? "event",
          summary: item.summary ?? "无摘要",
        }))
      : fallback.events,
    handoffs: handoffs.length
      ? handoffs.map((item) => ({
          from: item.from_stage ?? "unknown",
          to: item.to_stage_or_agent ?? "unknown",
          blockers: item.blockers ?? [],
          openQuestions: item.open_questions ?? [],
        }))
      : fallback.handoffs,
  };
}

export async function loadInvestmentDossierReadModel(workflowId: string): Promise<InvestmentDossierReadModel> {
  const fallback = buildInvestmentDossierReadModel();
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
          hardDissent: row.hard_dissent ?? false,
        }))
      : fallback.analystStanceMatrix,
    dataReadiness: {
      qualityBand: payload.data_readiness?.quality_band ?? fallback.dataReadiness.qualityBand,
      decisionCoreStatus: payload.data_readiness?.decision_core_status ?? fallback.dataReadiness.decisionCoreStatus,
      executionCoreStatus: payload.data_readiness?.execution_core_status ?? fallback.dataReadiness.executionCoreStatus,
      issues: payload.data_readiness?.issues ?? fallback.dataReadiness.issues,
    },
    rolePayloadDrilldowns: (payload.role_payload_drilldowns ?? []).length
      ? (payload.role_payload_drilldowns ?? []).map((item) => ({
          role: item.role ?? "Analyst",
          highlights: item.highlights ?? [],
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
    },
    optimizerDeviation: {
      singleNameDeviation: payload.optimizer_deviation?.single_name_deviation ?? fallback.optimizerDeviation.singleNameDeviation,
      portfolioDeviation: payload.optimizer_deviation?.portfolio_deviation ?? fallback.optimizerDeviation.portfolioDeviation,
      recommendation: payload.optimizer_deviation?.recommendation ?? fallback.optimizerDeviation.recommendation,
    },
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
      fees: payload.paper_execution?.fees ?? fallback.paperExecution.fees,
      tPlusOne: payload.paper_execution?.t_plus_one ?? fallback.paperExecution.tPlusOne,
    },
    attribution: {
      summary: payload.attribution?.summary ?? fallback.attribution.summary,
      links: payload.attribution?.links ?? fallback.attribution.links,
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

  return {
    ...fallback,
    taskCenter: (tasks.task_center ?? []).length
      ? (tasks.task_center ?? []).map((task) => ({
          taskId: task.task_id ?? "task",
          taskType: task.task_type ?? "system_task",
          currentState: task.current_state ?? "ready",
          reasonCode: task.reason_code ?? "unknown",
        }))
      : fallback.taskCenter,
    approvalCenter: (approvals.approval_center ?? []).length
      ? (approvals.approval_center ?? []).map((approval) => ({
          approvalId: approval.approval_id ?? "approval",
          kind: approval.approval_type ?? "approval",
          triggerReason: approval.trigger_reason ?? "unknown",
          packet: {
            comparisonAnalysis: true,
            impactScope: approval.effective_scope ?? "new_task",
            alternatives: ["approved", "rejected", "request_changes"],
            recommendation: approval.recommended_decision ?? approval.decision ?? "request_changes",
          },
        }))
      : fallback.approvalCenter,
    governanceChanges: changes.length
      ? changes.map((change) => ({
          changeId: change.change_id ?? "change",
          changeType: change.change_type ?? "unknown",
          impactLevel: change.impact_level ?? "medium",
          state: change.state ?? "draft",
          effectiveScope: change.effective_scope ?? "new_task",
        }))
      : fallback.governanceChanges,
  };
}

export async function loadApprovalRecordReadModel(approvalId: string): Promise<ApprovalRecordReadModel> {
  const fallback = buildApprovalRecordReadModel({ approvalId });
  const payload = await fetchEnvelope<ApiApprovalCenterReadModel>("/api/approvals");
  const approval = (payload.approval_center ?? []).find((item) => item.approval_id === approvalId);

  if (!approval) {
    return buildApprovalRecordReadModel({
      approvalId,
      subject: `审批包 ${approvalId}`,
      triggerReason: "approval_not_found",
      recommendation: "request_changes",
      comparisonOptions: ["等待服务端返回完整审批材料"],
      riskAndImpact: ["当前审批记录未出现在审批中心 read model"],
      evidenceRefs: [],
      allowedActions: [],
    });
  }

  return buildApprovalRecordReadModel({
    approvalId: approval.approval_id ?? fallback.approvalId,
    subject: approval.subject ?? fallback.subject,
    triggerReason: approval.trigger_reason ?? fallback.triggerReason,
    recommendation: approval.recommended_decision ?? approval.decision ?? fallback.recommendation,
    alternatives: approval.alternatives ?? fallback.alternatives,
    comparisonOptions: approval.comparison_options ?? fallback.comparisonOptions,
    impactScope: approval.effective_scope ?? fallback.impactScope,
    riskAndImpact: approval.risk_and_impact ?? fallback.riskAndImpact,
    timeoutDisposition: approval.timeout_disposition ?? fallback.timeoutDisposition,
    rollbackRef: approval.rollback_ref ?? fallback.rollbackRef,
    evidenceRefs: approval.evidence_refs ?? fallback.evidenceRefs,
    traceRoute: approval.trace_route ?? fallback.traceRoute,
    allowedActions: approval.allowed_actions ?? fallback.allowedActions,
  });
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

export async function updateFinanceAsset(): Promise<FinanceAssetUpdateApiReadModel> {
  const payload = await fetchEnvelope<{
    asset_id?: string;
    asset_type?: string;
  }>("/api/finance/assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_type: "cash",
      valuation: { amount: 1000000, currency: "CNY" },
      valuation_date: "2026-05-04",
      source: "owner_ui",
      client_seen_version: 1,
    }),
  });

  return {
    assetId: payload.asset_id ?? "asset",
    assetType: payload.asset_type ?? "cash",
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
      investmentResumeAllowed: item.investment_resume_allowed ?? false,
    })),
  };
}

export async function createRequestBrief(rawText: string): Promise<RequestBriefApiReadModel> {
  const payload = await fetchEnvelope<{
    brief_id?: string;
    route_type?: string;
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
      draft_title: "能力配置草案",
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
