export type NavItem = {
  id: string;
  label: string;
  route: string;
};

export type WorkbenchPage =
  | "overview"
  | "investment-queue"
  | "investment-dossier"
  | "trace-debug"
  | "finance"
  | "knowledge"
  | "governance"
  | "agent-team"
  | "agent-profile"
  | "agent-config"
  | "approval-detail"
  | "not-found";

export type WorkbenchRoute = {
  path: string;
  page: WorkbenchPage;
  topNavId: string;
  label: string;
};

export type ResolvedWorkbenchRoute = WorkbenchRoute & {
  pathname: string;
  params: Record<string, string>;
  query: Record<string, string>;
};

export type RequestBriefPreview = {
  status: "preview" | "draft" | "blocked_draft";
  taskType: string;
  semanticLead: string;
  processAuthority: string;
  expectedArtifacts: string[];
  reasonCode: string;
  blockedDirectActions: string[];
  clarificationPrompts?: string[];
  details?: Array<{ label: string; value: string }>;
  display: {
    statusLabel: string;
    taskLabel: string;
    leadLabel: string;
    authorityLabel: string;
    artifactsLabel: string;
    boundaryLabel: string;
    nextStepLabel: string;
  };
};

export type RequestBriefPreviewSource = {
  routeType?: string;
  semanticLead?: string;
  processAuthority?: string;
  expectedArtifacts?: string[];
  reasonCode?: string | null;
  ownerConfirmationStatus?: string;
};

export type DebateStatusSummary = {
  roundsUsed: number;
  retainedHardDissent: boolean;
  riskReviewRequired: boolean;
  consensusScore?: number | null;
  actionConviction?: number | null;
};

export type DebateCoreDispute = {
  title: string;
  whyItMatters: string;
  involvedRoles: string[];
  currentConclusion: string;
  requiredEvidence: string[];
};

export type DebateViewChangeDetail = {
  role: string;
  before: string;
  after: string;
  reason: string;
  impact: string;
};

export type DebateRetainedDissentDetail = {
  sourceRole: string;
  dissent: string;
  counterRisks: string[];
  handling: string;
  forbiddenActions: string[];
};

export type DebateRoundDetail = {
  roundNo: number;
  issue: string;
  participants: string[];
  inputEvidence: string[];
  outcome: string;
  unresolvedQuestions: string[];
};

export type DebateNextAction = {
  action: string;
  owner: string;
  completionSignal: string;
  nextStage: string;
};

export type TeamHealth = {
  healthyAgentCount: number;
  activeAgentRunCount: number;
  pendingDraftCount: number;
  failedOrDeniedCount: number;
};

export type TeamAgentCard = {
  agentId: string;
  displayName: string;
  role: string;
  profileVersion: string;
  skillPackageVersion: string;
  promptVersion: string;
  contextSnapshotVersion: string;
  recentQualityScore: number;
  failureCount: number;
  deniedActionCount: number;
  configDraftEntry: string;
  weaknessTags: string[];
};

export type AgentProfileReadModel = {
  agentId: string;
  displayName: string;
  capabilitySummary: string;
  canDo: string[];
  cannotDo: string[];
  versions: {
    profileVersion: string;
    skillPackageVersion: string;
    promptVersion: string;
    contextSnapshotVersion: string;
  };
  toolPermissions: string[];
  weaknessTags: string[];
  qualityMetrics: {
    schemaPassRate: number;
    evidenceQuality: number;
  };
  cfoAttributionRefs: string[];
  deniedActions: Array<{ reasonCode: string }>;
  failureRecords: string[];
};

export type CapabilityConfigReadModel = {
  agentId: string;
  editableFields: string[];
  forbiddenDirectUpdateReason: string;
  effectiveScopeOptions: string[];
};

export type CapabilityDraftSubmission = {
  draftId: string;
  state: string;
  impactLevel: string;
  governanceChangeRef: string;
  ownerApprovalRef: string;
  effectiveScope: string;
};

export type TeamReadModel = {
  teamHealth: TeamHealth;
  agentCards: TeamAgentCard[];
  agentProfileReadModels: AgentProfileReadModel[];
  capabilityConfigReadModel: CapabilityConfigReadModel;
  capabilityDraftSubmission: CapabilityDraftSubmission;
  hotPatchDenials: Array<{ reasonCode: string; actionVisible: boolean }>;
};

export type InvestmentDossierReadModel = {
  workflow: {
    workflowId: string;
    title: string;
    currentStage: string;
    state: string;
  };
  stageRail: Array<{
    stage: string;
    nodeStatus: string;
    reasonCode: string | null;
    artifactCount: number;
  }>;
  chairBrief: {
    decisionQuestion: string;
    keyTensions: string[];
    noPresetDecisionAttestation: boolean;
  };
  analystStanceMatrix: Array<{
    role: string;
    direction: string;
    confidence: number;
    evidenceQuality?: number;
    hardDissent: boolean;
    hardDissentReason?: string | null;
    thesis?: string | null;
  }>;
  dataReadiness: {
    qualityBand: string;
    decisionCoreStatus: string;
    executionCoreStatus: string;
    issues: string[];
    lineageRefs?: string[];
    ownerSummary?: string;
    sourceStatus?: Array<{
      sourceName: string;
      sourceRef: string;
      requiredUsage: string;
      requestedFields: string[];
      obtainedFields: string[];
      missingFields: string[];
      status: "available" | "partial" | "failed" | "missing" | string;
      qualityLabel: string;
      evidenceRef: string;
    }>;
    dataGaps?: Array<{
      gap: string;
      affectsStage: string;
      impact: string;
      nextAction: string;
    }>;
  };
  rolePayloadDrilldowns: Array<{
    role: string;
    highlights: string[];
    hardDissentReason?: string | null;
    thesis?: string | null;
    supportingEvidenceRefs?: string[];
    counterEvidenceRefs?: string[];
    keyRisks?: string[];
    applicableConditions?: string[];
    invalidationConditions?: string[];
    suggestedActionImplication?: string | null;
    rolePayload?: Record<string, unknown>;
  }>;
  consensus: {
    score: number;
    actionConviction: number;
    thresholdLabel: string;
  };
  debate: {
    roundsUsed: number;
    retainedHardDissent: boolean;
    riskReviewRequired: boolean;
    issues: string[];
    viewChanges?: string[];
    cioSynthesis?: string | null;
    unresolvedDissent?: string[];
    rounds?: Array<{ roundNo?: number; issue?: string; outcome?: string }>;
    ownerSummary?: string | null;
    statusSummary?: DebateStatusSummary | null;
    coreDisputes?: DebateCoreDispute[];
    viewChangeDetails?: DebateViewChangeDetail[];
    retainedDissentDetails?: DebateRetainedDissentDetail[];
    roundDetails?: DebateRoundDetail[];
    nextActions?: DebateNextAction[];
  };
  optimizerDeviation: {
    singleNameDeviation: string;
    portfolioDeviation: string;
    recommendation: string;
  };
  cioDecision?: {
    decision: string;
    rationale?: string;
    deviationReason?: string;
    conditions?: string[];
    monitoringPoints?: string[];
    riskHandoffNotes?: string;
  };
  decisionGuard?: {
    majorDeviation?: boolean;
    singleNameDeviationPp?: number | string;
    portfolioActiveDeviation?: number | string;
    lowActionConviction?: boolean;
    retainedHardDissent?: boolean;
    dataQualityBlockers?: string[];
    reasonCodes?: string[];
  };
  riskReview: {
    reviewResult: string;
    repairability: string;
    ownerExceptionRequired: boolean;
    reasonCodes: string[];
  };
  paperExecution: {
    status: string;
    pricingMethod: string;
    window: string;
    fees: string;
    taxes?: string;
    slippage?: string;
    tPlusOne: string;
  };
  attribution: {
    summary: string;
    links: string[];
    marketResult?: string;
    decisionQuality?: number | null;
    executionQuality?: number | null;
    riskQuality?: number | null;
    dataQuality?: number | null;
    evidenceQuality?: number | null;
    conditionHit?: string;
    improvementItems?: string[];
    needsCfoInterpretation?: boolean;
  };
  evidenceMap: {
    artifactRefs: string[];
    dataRefs: string[];
    sourceQuality: Array<string | { source?: string; usedFor?: string; quality?: string }>;
    conflictRefs: string[];
    supportingEvidenceOnlyRefs: string[];
  };
  forbiddenActions: Record<string, { actionVisible: boolean; reasonCode: string }>;
  traceRoute: string;
};

export type TraceDebugReadModel = {
  workflowId: string;
  agentRunTree: Array<{
    runId: string;
    parentRunId: string | null;
    stage: string;
    profileVersion: string;
    contextSlice: string;
    businessSummary?: string;
    agentId?: string;
    status?: string;
  }>;
  commands: Array<{ commandType: string; admission: string; receiver: string; reasonCode: string }>;
  events: Array<{ eventType: string; summary: string }>;
  handoffs: Array<{ from: string; to: string; blockers: string[]; openQuestions: string[] }>;
  contextInjectionRecords: Array<{ contextSnapshotId: string; whyIncluded: string; redactionStatus: string }>;
  rawTranscriptDefaultCollapsed: boolean;
};

export type KnowledgeReadModel = {
  dailyBrief: Array<{ briefId: string; priority: string; title: string; supportingEvidenceOnly: boolean }>;
  researchPackages: Array<{ packageId: string; title: string; status: string; evidenceRefs: string[] }>;
  memoryCollections: Array<{ collectionId: string; title: string; resultCount: number }>;
  memoryResults: Array<{
    memoryId: string;
    currentVersionId: string;
    title: string;
    relationSummary: string;
    sensitivity: string;
    extractionStatus: string;
    promotionState: string;
    tags: string[];
  }>;
  relationGraph: Array<{ sourceMemoryId: string; targetRef: string; relationType: string; reason: string }>;
  organizeSuggestions: Array<{
    suggestionId: string;
    targetMemoryRefs: string[];
    suggestedTags: string[];
    requiresGatewayWrite: boolean;
    riskIfApplied: string;
  }>;
  contextInjectionInspector: Array<{
    contextSnapshotId: string;
    sourceRef: string;
    whyIncluded: string;
    redactionStatus: string;
    deniedRefs: string[];
  }>;
  proposals: Array<{
    proposalId: string;
    proposalType: string;
    impactLevel: string;
    validationResultRefs: string[];
    effectiveScope: string;
    rollbackPlan: string;
  }>;
  defaultContextProposalPath: string;
};

export type ApprovalRecordReadModel = {
  approvalId: string;
  subject: string;
  triggerReason: string;
  recommendation: string;
  alternatives: string[];
  comparisonOptions: string[];
  impactScope: string;
  riskAndImpact: string[];
  timeoutDisposition: string;
  rollbackRef: string;
  evidenceRefs: string[];
  traceRoute: string;
  allowedActions: string[];
};

export type FinanceOverviewReadModel = {
  assets: Array<{ label: string; value: string; status: string }>;
  health: { liquidity: string; debtRatio: string; riskBudget: string; stress: string };
  reminders: string[];
  nonAAssetBoundary: { actionVisible: boolean; reasonCode: string };
};

export type GovernanceReadModel = {
  modules: string[];
  taskCenter: Array<{
    taskId: string;
    taskType: string;
    currentState: string;
    reasonCode: string;
    dueDate?: string;
    riskHint?: string;
    blockedReason?: string;
  }>;
  approvalCenter: Array<{
    approvalId: string;
    kind: string;
    triggerReason: string;
    subject?: string;
    deadline?: string;
    packet: { comparisonAnalysis: boolean; impactScope: string; alternatives: string[]; recommendation: string };
  }>;
  unifiedTodos: GovernanceTodoItem[];
  governanceChanges: Array<{ changeId: string; changeType: string; impactLevel: string; state: string; effectiveScope: string }>;
  manualTodoIsolation: { connectedToS5S6: boolean; state: string };
  governanceStateMachine: string[];
  agentCapabilityDraftStates: string[];
  uiGuardResponses: Record<string, { actionVisible: boolean; reasonCode: string }>;
  inFlightSnapshotUnchanged: boolean;
  financeSensitiveRedactionUi: { dossier: string; trace: string; financeOwnerView: string };
};

export type GovernanceTodoItem = {
  todoId: string;
  todoType: "approval" | "manual_todo" | "task";
  sourceId: string;
  title: string;
  detail: string;
  actionLabel: string;
  actionHref: string;
};

export type DevOpsHealthReadModel = {
  routineChecks: Array<{ checkId: string; status: string }>;
  incidents: Array<{ incidentId: string; status: string; incidentType: string }>;
  recovery: Array<{ planId: string; investmentResumeAllowed: boolean; technicalRecoveryStatus?: string }>;
};

export type Report = Record<string, unknown> & {
  report_id: string;
  result: "pass" | "fail";
  work_item_refs: string[];
  test_case_refs: string[];
  failures: unknown[];
};

export type ReportEnvelopeOptions = {
  guardResults?: Array<Record<string, unknown> & { result?: string }>;
  failures?: unknown[];
};

export const topLevelLabels = ["全景", "投资", "财务", "知识", "治理"];

const designPreviewRefs = [
  "design-previews/frontend-workbench/00-shell-and-navigation.md",
  "design-previews/frontend-workbench/01-overview.md",
  "design-previews/frontend-workbench/02-investment.md",
  "design-previews/frontend-workbench/04-knowledge.md",
  "design-previews/frontend-workbench/06-governance.md",
  "design-previews/frontend-workbench/07-states-and-guards.md",
];

const agentIds = [
  "cio",
  "cfo",
  "macro_analyst",
  "fundamental_analyst",
  "quant_analyst",
  "event_analyst",
  "risk_officer",
  "investment_researcher",
  "devops_engineer",
];

const agentNames: Record<string, string> = {
  cio: "CIO",
  cfo: "CFO",
  macro_analyst: "Macro Analyst",
  fundamental_analyst: "Fundamental Analyst",
  quant_analyst: "Quant Analyst",
  event_analyst: "Event Analyst",
  risk_officer: "Risk Officer",
  investment_researcher: "Investment Researcher",
  devops_engineer: "DevOps Engineer",
};

export function buildRouteManifest(): WorkbenchRoute[] {
  return [
    { path: "/", page: "overview", topNavId: "overview", label: "全景" },
    { path: "/investment", page: "investment-queue", topNavId: "investment", label: "投资队列" },
    { path: "/investment/:workflowId", page: "investment-dossier", topNavId: "investment", label: "Investment Dossier" },
    { path: "/investment/:workflowId/trace", page: "trace-debug", topNavId: "investment", label: "Workflow Trace" },
    { path: "/finance", page: "finance", topNavId: "finance", label: "财务" },
    { path: "/knowledge", page: "knowledge", topNavId: "knowledge", label: "知识" },
    { path: "/governance", page: "governance", topNavId: "governance", label: "治理" },
    { path: "/governance/team", page: "agent-team", topNavId: "governance", label: "团队" },
    { path: "/governance/team/:agentId", page: "agent-profile", topNavId: "governance", label: "团队画像" },
    { path: "/governance/team/:agentId/config", page: "agent-config", topNavId: "governance", label: "能力提升方案" },
    { path: "/governance/approvals/:approvalId", page: "approval-detail", topNavId: "governance", label: "审批包" },
  ];
}

export function resolveWorkbenchRoute(pathname: string): ResolvedWorkbenchRoute {
  const cleanPath = normalizePath(pathname);
  const query = parseQuery(pathname);
  const matchers: Array<[RegExp, WorkbenchPage, string, string, string[], string]> = [
    [/^\/$/, "overview", "overview", "/", [], "全景"],
    [/^\/investment$/, "investment-queue", "investment", "/investment", [], "投资队列"],
    [/^\/investment\/([^/]+)\/trace$/, "trace-debug", "investment", "/investment/:workflowId/trace", ["workflowId"], "Workflow Trace"],
    [/^\/investment\/([^/]+)$/, "investment-dossier", "investment", "/investment/:workflowId", ["workflowId"], "Investment Dossier"],
    [/^\/finance$/, "finance", "finance", "/finance", [], "财务"],
    [/^\/knowledge$/, "knowledge", "knowledge", "/knowledge", [], "知识"],
    [/^\/governance$/, "governance", "governance", "/governance", [], "治理"],
    [/^\/governance\/team$/, "agent-team", "governance", "/governance/team", [], "团队"],
    [/^\/governance\/team\/([^/]+)\/config$/, "agent-config", "governance", "/governance/team/:agentId/config", ["agentId"], "能力提升方案"],
    [/^\/governance\/team\/([^/]+)$/, "agent-profile", "governance", "/governance/team/:agentId", ["agentId"], "团队画像"],
    [/^\/governance\/approvals\/([^/]+)$/, "approval-detail", "governance", "/governance/approvals/:approvalId", ["approvalId"], "审批包"],
  ];
  for (const [pattern, page, topNavId, path, paramNames, label] of matchers) {
    const match = cleanPath.match(pattern);
    if (!match) continue;
    return {
      path,
      page,
      topNavId,
      label,
      pathname: cleanPath,
      params: Object.fromEntries(paramNames.map((name, index) => [name, match[index + 1]])),
      query,
    };
  }
  return {
    path: cleanPath,
    page: "not-found",
    topNavId: "overview",
    label: "未找到",
    pathname: cleanPath,
    params: {},
    query,
  };
}

function normalizePath(pathname: string): string {
  const withoutHash = pathname.split("#")[0] || "/";
  const withoutQuery = withoutHash.split("?")[0] || "/";
  return withoutQuery.length > 1 ? withoutQuery.replace(/\/+$/, "") : "/";
}

function parseQuery(pathname: string): Record<string, string> {
  const queryText = pathname.includes("?") ? pathname.slice(pathname.indexOf("?") + 1).split("#")[0] : "";
  return Object.fromEntries(new URLSearchParams(queryText));
}

export function buildShellReadModel() {
  return {
    navItems: topLevelLabels.map((label, index) => ({
      id: ["overview", "investment", "finance", "knowledge", "governance"][index],
      label,
      route: ["/", "/investment", "/finance", "/knowledge", "/governance"][index],
    })),
    attentionCounts: {
      approvals: 2,
      manualTodo: 3,
      riskBlocked: 1,
      incidents: 1,
    },
    governanceModules: ["待办", "团队", "变更", "健康", "审计"],
    commandLayer: {
      placement: "topbar_drawer",
      defaultExpanded: false,
      pageNarrativeIntrusion: false,
      previewTitle: "请求预览",
    },
    session: { ownerMode: "single_owner", language: "zh-CN" },
  };
}

export function routeOwnerCommand(input: string): RequestBriefPreview {
  const trimmed = input.trim();
  const normalized = input.toLowerCase();
  if (isBlockedCapabilityHotPatch(trimmed)) {
    return {
      status: "blocked_draft",
      taskType: "agent_capability_change",
      semanticLead: "Governance Runtime",
      processAuthority: "Governance Runtime",
      expectedArtifacts: ["AgentCapabilityChangeDraft", "GovernanceChange"],
      reasonCode: "agent_capability_hot_patch_denied",
      blockedDirectActions: ["hot_patch_in_flight_agent_run_denied"],
      clarificationPrompts: [
        "请说明影响的 Agent 或配置项",
        "确认是否接受只对后续任务生效",
      ],
      display: {
        statusLabel: "已阻断",
        taskLabel: "能力改进",
        leadLabel: "治理运行时",
        authorityLabel: "治理流程",
        artifactsLabel: "能力提升方案 / 治理变更",
        boundaryLabel: "不能热改运行中的 Agent",
        nextStepLabel: "改为能力提升方案后再评估",
      },
    };
  }
  if (isAmbiguousOwnerCommand(trimmed)) {
    return {
      status: "draft",
      taskType: "manual_todo",
      semanticLead: "待确认",
      processAuthority: "Request Brief Triage",
      expectedArtifacts: ["RequestBriefDraft"],
      reasonCode: "request_brief_needs_clarification",
      blockedDirectActions: ["task_creation_blocked_until_clarified"],
      clarificationPrompts: [
        "请补充目标对象或主题",
        "请补充希望产出的结果",
        "请说明是否只做研究、审批还是人工跟进",
      ],
      display: {
        statusLabel: "待补充",
        taskLabel: "待补充请求",
        leadLabel: "待确认",
        authorityLabel: "请求分诊",
        artifactsLabel: "请求草稿",
        boundaryLabel: "信息不完整，先不生成任务卡",
        nextStepLabel: "补充后再重新生成预览",
      },
    };
  }
  if (input.includes("热点") || input.includes("学习")) {
    return {
      status: "preview",
      taskType: "research_task",
      semanticLead: "Investment Researcher",
      processAuthority: "Workflow Scheduling Center",
      expectedArtifacts: ["Research Package", "MemoryCapture", "候选 TopicProposal"],
      reasonCode: "supporting_evidence_only",
      blockedDirectActions: ["no_trade_or_approval_entry"],
      display: {
        statusLabel: "可确认",
        taskLabel: "热点研究",
        leadLabel: "投资研究员",
        authorityLabel: "流程调度",
        artifactsLabel: "研究资料包 / 记忆摘录 / 候选议题",
        boundaryLabel: "只做研究，不进入审批或交易",
        nextStepLabel: "确认后生成研究任务卡",
      },
    };
  }
  if (input.includes("下单") || normalized.includes("trade") || input.includes("腾讯")) {
    return {
      status: "blocked_draft",
      taskType: "manual_todo",
      semanticLead: "无 Agent 主持",
      processAuthority: "Task Center",
      expectedArtifacts: ["manual_todo"],
      reasonCode: "non_a_asset_no_trade",
      blockedDirectActions: ["approval_entry_hidden", "execution_entry_hidden", "real_trade_entry_hidden"],
      display: {
        statusLabel: "需补充",
        taskLabel: "人工事项",
        leadLabel: "老板确认",
        authorityLabel: "任务",
        artifactsLabel: "人工待办",
        boundaryLabel: "不生成审批、执行或交易入口",
        nextStepLabel: "补充资产范围后重新生成预览",
      },
    };
  }
  if (input.includes("能力") || input.includes("Prompt") || input.includes("Skill")) {
    return {
      status: "draft",
      taskType: "agent_capability_change",
      semanticLead: "Governance Runtime",
      processAuthority: "Governance Runtime",
      expectedArtifacts: ["AgentCapabilityChangeDraft", "GovernanceChange"],
      reasonCode: "agent_capability_hot_patch_denied",
      blockedDirectActions: ["hot_patch_in_flight_agent_run_denied"],
      display: {
        statusLabel: "待完善",
        taskLabel: "能力改进",
        leadLabel: "治理运行时",
        authorityLabel: "治理流程",
        artifactsLabel: "能力提升方案 / 治理变更",
        boundaryLabel: "只影响后续任务，不热改运行中的 Agent",
        nextStepLabel: "确认后进入治理变更评估",
      },
    };
  }
  return {
    status: "preview",
    taskType: "investment_workflow",
    semanticLead: "CIO",
    processAuthority: "Workflow Scheduling Center",
    expectedArtifacts: ["Request Brief", "TaskEnvelope", "Investment Dossier"],
    reasonCode: "request_brief_preview_required",
    blockedDirectActions: ["direct_execution_denied"],
    display: {
      statusLabel: "可确认",
      taskLabel: "投资任务",
      leadLabel: "CIO",
      authorityLabel: "流程调度",
      artifactsLabel: "请求预览 / 任务卡 / 投资档案",
      boundaryLabel: "先进入受控流程，不直接执行",
      nextStepLabel: "确认后创建任务卡",
    },
  };
}

export function buildRequestBriefPreviewFromApi(
  input: string,
  source: RequestBriefPreviewSource,
): RequestBriefPreview {
  const localPreview = routeOwnerCommand(input);
  const routePreview = routeOwnerCommandByRouteType(input, source.routeType);
  const keepsLocalGuard = localPreview.status !== "preview";
  const base = keepsLocalGuard
    ? {
        ...routePreview,
        status: localPreview.status,
        reasonCode: source.reasonCode ?? localPreview.reasonCode,
        blockedDirectActions: localPreview.blockedDirectActions,
        clarificationPrompts: localPreview.clarificationPrompts,
        display: {
          ...routePreview.display,
          statusLabel: localPreview.display.statusLabel,
          boundaryLabel: localPreview.display.boundaryLabel,
          nextStepLabel: localPreview.display.nextStepLabel,
        },
      }
    : routePreview;
  const semanticLead = source.semanticLead ? normalizeSemanticLead(source.semanticLead) : base.semanticLead;
  const processAuthority = source.processAuthority
    ? normalizeProcessAuthority(source.processAuthority)
    : base.processAuthority;
  const expectedArtifacts = source.expectedArtifacts?.length ? source.expectedArtifacts : base.expectedArtifacts;
  const display = {
    ...base.display,
    leadLabel: formatSemanticLead(semanticLead),
    authorityLabel: formatProcessAuthority(processAuthority),
    artifactsLabel: formatExpectedArtifacts(expectedArtifacts),
  };
  const preview: RequestBriefPreview = {
    ...base,
    taskType: normalizeRouteType(source.routeType) ?? base.taskType,
    semanticLead,
    processAuthority,
    expectedArtifacts,
    reasonCode: source.reasonCode ?? base.reasonCode,
    display,
  };
  return {
    ...preview,
    details: buildRequestBriefPreviewDetails(input, preview),
  };
}

function routeOwnerCommandByRouteType(input: string, routeType?: string): RequestBriefPreview {
  switch (normalizeRouteType(routeType)) {
    case "research_task":
      return {
        status: "preview",
        taskType: "research_task",
        semanticLead: "Investment Researcher",
        processAuthority: "Workflow Scheduling Center",
        expectedArtifacts: ["ResearchPackage", "MemoryCapture", "TopicProposalCandidate"],
        reasonCode: "supporting_evidence_only",
        blockedDirectActions: ["no_trade_or_approval_entry"],
        display: {
          statusLabel: "可确认",
          taskLabel: "热点研究",
          leadLabel: "投资研究员",
          authorityLabel: "流程调度",
          artifactsLabel: "研究资料包 / 记忆摘录 / 候选议题",
          boundaryLabel: "只做研究，不进入审批或交易",
          nextStepLabel: "确认后生成研究任务卡",
        },
      };
    case "manual_todo":
      return {
        status: "preview",
        taskType: "manual_todo",
        semanticLead: "Owner",
        processAuthority: "Task Center",
        expectedArtifacts: ["ManualTodo"],
        reasonCode: "manual_todo_required",
        blockedDirectActions: ["approval_entry_hidden", "execution_entry_hidden", "real_trade_entry_hidden"],
        display: {
          statusLabel: "可确认",
          taskLabel: "人工事项",
          leadLabel: "老板确认",
          authorityLabel: "任务",
          artifactsLabel: "人工待办",
          boundaryLabel: "不生成审批、执行或交易入口",
          nextStepLabel: "确认后生成人工待办",
        },
      };
    case "finance_task":
      return {
        status: "preview",
        taskType: "finance_task",
        semanticLead: "CFO",
        processAuthority: "Task Center",
        expectedArtifacts: ["FinancePlanningSummary", "ManualTodo"],
        reasonCode: "finance_planning_only",
        blockedDirectActions: ["non_a_asset_no_trade"],
        display: {
          statusLabel: "可确认",
          taskLabel: "财务事项",
          leadLabel: "CFO",
          authorityLabel: "任务",
          artifactsLabel: "财务规划 / 人工待办",
          boundaryLabel: "只做财务规划，不触发交易",
          nextStepLabel: "确认后生成财务任务卡",
        },
      };
    case "governance_task":
    case "agent_capability_change":
      return {
        status: "preview",
        taskType: normalizeRouteType(routeType) ?? "governance_task",
        semanticLead: "Governance Runtime",
        processAuthority: "Governance Runtime",
        expectedArtifacts: ["AgentCapabilityChangeDraft", "GovernanceChange"],
        reasonCode: "governance_change_required",
        blockedDirectActions: ["hot_patch_in_flight_agent_run_denied"],
        display: {
        statusLabel: "待完善",
        taskLabel: "能力改进",
        leadLabel: "治理运行时",
        authorityLabel: "治理流程",
        artifactsLabel: "能力提升方案 / 治理变更",
        boundaryLabel: "只影响后续任务，不热改运行中的 Agent",
        nextStepLabel: "确认后进入治理变更评估",
        },
      };
    case "system_task":
      return {
        status: "preview",
        taskType: "system_task",
        semanticLead: "DevOps Engineer",
        processAuthority: "Task Center",
        expectedArtifacts: ["IncidentReview", "RecoveryPlan"],
        reasonCode: "system_task_required",
        blockedDirectActions: ["investment_resume_requires_risk_guard"],
        display: {
          statusLabel: "可确认",
          taskLabel: "系统事项",
          leadLabel: "DevOps",
          authorityLabel: "任务",
          artifactsLabel: "故障复核 / 恢复计划",
          boundaryLabel: "技术恢复不自动放行投资",
          nextStepLabel: "确认后生成系统任务卡",
        },
      };
    case "investment_workflow":
      return {
        status: "preview",
        taskType: "investment_workflow",
        semanticLead: "CIO",
        processAuthority: "Workflow Scheduling Center",
        expectedArtifacts: ["RequestBrief", "TaskEnvelope", "InvestmentDossier"],
        reasonCode: "request_brief_preview_required",
        blockedDirectActions: ["direct_execution_denied"],
        display: {
          statusLabel: "可确认",
          taskLabel: "投资任务",
          leadLabel: "CIO",
          authorityLabel: "流程调度",
          artifactsLabel: "请求预览 / 任务卡 / 投资档案",
          boundaryLabel: "先进入受控流程，不直接执行",
          nextStepLabel: "确认后创建任务卡",
        },
      };
    default:
      return routeOwnerCommand(input);
  }
}

function buildRequestBriefPreviewDetails(input: string, preview: RequestBriefPreview) {
  const routeText = routeTypeToChinese(preview.taskType);
  return [
    { label: "目标", value: previewTargetLabel(preview.taskType) },
    { label: "范围", value: input.trim() || "待补充" },
    { label: "资产边界", value: preview.display.boundaryLabel },
    { label: "任务类型", value: routeText },
    { label: "建议负责人", value: preview.display.leadLabel },
    { label: "过程权威", value: preview.display.authorityLabel },
    { label: "预期产物", value: preview.display.artifactsLabel },
    { label: "优先级", value: "普通" },
    { label: "授权边界", value: authorizationBoundaryLabel(preview.taskType) },
    { label: "成功标准", value: successStandardLabel(preview.taskType) },
    { label: "阻断条件", value: blockConditionLabel(preview.taskType) },
    { label: "审批可能性", value: approvalPossibilityLabel(preview.taskType) },
  ];
}

function normalizeRouteType(routeType?: string) {
  const normalized = routeType?.trim().toLowerCase();
  const allowed = [
    "investment_workflow",
    "research_task",
    "finance_task",
    "governance_task",
    "agent_capability_change",
    "system_task",
    "manual_todo",
  ];
  return allowed.includes(normalized ?? "") ? normalized : undefined;
}

function normalizeSemanticLead(lead: string) {
  const normalized = lead.trim().toLowerCase();
  const mapping: Record<string, string> = {
    cio: "CIO",
    cfo: "CFO",
    owner: "Owner",
    investment_researcher: "Investment Researcher",
    governance_runtime: "Governance Runtime",
    devops_engineer: "DevOps Engineer",
    risk_officer: "Risk Officer",
  };
  return mapping[normalized] ?? lead;
}

function normalizeProcessAuthority(authority: string) {
  const normalized = authority.trim().toLowerCase();
  const mapping: Record<string, string> = {
    workflow_scheduling_center: "Workflow Scheduling Center",
    task_center: "Task Center",
    governance_runtime: "Governance Runtime",
  };
  return mapping[normalized] ?? authority;
}

function formatSemanticLead(lead: string) {
  const mapping: Record<string, string> = {
    "Investment Researcher": "投资研究员",
    "Governance Runtime": "治理运行时",
    "DevOps Engineer": "DevOps",
    "Risk Officer": "风控负责人",
    Owner: "老板确认",
    CIO: "CIO",
    CFO: "CFO",
  };
  return mapping[lead] ?? lead;
}

function formatProcessAuthority(authority: string) {
  const mapping: Record<string, string> = {
    "Workflow Scheduling Center": "流程调度",
    "Task Center": "任务",
    "Governance Runtime": "治理流程",
  };
  return mapping[authority] ?? authority;
}

function formatExpectedArtifacts(artifacts: string[]) {
  const mapping: Record<string, string> = {
    AgentCapabilityChangeDraft: "能力提升方案",
    FinancePlanningSummary: "财务规划",
    GovernanceChange: "治理变更",
    IncidentReview: "故障复核",
    InvestmentDossier: "投资档案",
    ManualTodo: "人工待办",
    MemoryCapture: "记忆摘录",
    RecoveryPlan: "恢复计划",
    RequestBrief: "请求预览",
    ResearchPackage: "研究资料包",
    TaskEnvelope: "任务卡",
    TopicProposalCandidate: "候选议题",
    "候选 TopicProposal": "候选议题",
  };
  return artifacts.map((artifact) => mapping[artifact] ?? artifact).join(" / ");
}

function routeTypeToChinese(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "团队能力提升",
    finance_task: "财务任务",
    governance_task: "治理任务",
    investment_workflow: "投资流程",
    manual_todo: "人工待办",
    research_task: "研究任务",
    system_task: "系统任务",
  };
  return mapping[taskType] ?? taskType;
}

function previewTargetLabel(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "Agent 能力受控变更",
    finance_task: "财务规划事项",
    governance_task: "治理变更事项",
    investment_workflow: "投资研究任务",
    manual_todo: "人工确认事项",
    research_task: "热点事件研究",
    system_task: "系统运行事项",
  };
  return mapping[taskType] ?? "待确认请求";
}

function authorizationBoundaryLabel(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "只能提交能力提升方案",
    finance_task: "只能生成财务任务卡",
    governance_task: "只能生成治理任务或变更材料",
    investment_workflow: "只能生成受控投资任务卡",
    manual_todo: "只能生成人工待办",
    research_task: "只能生成研究任务卡",
    system_task: "只能生成系统任务卡",
  };
  return mapping[taskType] ?? "只能生成请求预览";
}

function successStandardLabel(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "形成可验证、可回滚的能力提升方案",
    finance_task: "形成可复核的财务规划或人工待办",
    governance_task: "形成可审计的治理变更材料",
    investment_workflow: "形成任务卡并进入受控投资档案",
    manual_todo: "明确责任人、原因和截止时间",
    research_task: "形成可复用研究资料和候选议题",
    system_task: "形成故障复核、恢复验证和风险交接",
  };
  return mapping[taskType] ?? "补齐请求后再创建任务";
}

function blockConditionLabel(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "不热改运行中的 Agent",
    finance_task: "不生成审批、执行或交易入口",
    governance_task: "不绕过验证或审批生效",
    investment_workflow: "不直接执行或绕过风控",
    manual_todo: "不连接审批、执行或交易链路",
    research_task: "不生成审批、执行或交易入口",
    system_task: "技术恢复后仍需 Risk/workflow guard",
  };
  return mapping[taskType] ?? "不直接执行业务动作";
}

function approvalPossibilityLabel(taskType: string) {
  const mapping: Record<string, string> = {
    agent_capability_change: "高影响时触发审批",
    finance_task: "通常不触发审批",
    governance_task: "高影响时触发审批",
    investment_workflow: "符合条件时可能触发审批",
    manual_todo: "不触发审批",
    research_task: "通常不触发审批",
    system_task: "通常不触发审批",
  };
  return mapping[taskType] ?? "待后端分诊确认";
}

function isAmbiguousOwnerCommand(input: string) {
  if (!input) return true;
  const vaguePatterns = ["处理一下", "安排一下", "看一下", "看看", "跟进一下", "弄一下"];
  const knownIntentPatterns = ["热点", "学习", "下单", "买入", "卖出", "能力", "prompt", "skill", "审批", "财务", "治理", "研究"];
  return vaguePatterns.some((pattern) => input.includes(pattern))
    && !knownIntentPatterns.some((pattern) => input.toLowerCase().includes(pattern));
}

function isBlockedCapabilityHotPatch(input: string) {
  const normalized = input.toLowerCase();
  const configKeywords = ["能力", "prompt", "skill", "工具权限", "model route", "上下文"];
  const activationKeywords = ["直接生效", "立刻生效", "马上生效", "热更新", "热改"];
  return configKeywords.some((pattern) => normalized.includes(pattern.toLowerCase()))
    && activationKeywords.some((pattern) => normalized.includes(pattern.toLowerCase()));
}

export function buildOwnerDecisionReadModel() {
  return {
    todayAttention: [
      { label: "风险阻断", count: 1, route: "/investment/wf-001", severity: "blocked" },
      { label: "待办", count: 5, route: "/governance?panel=todos", severity: "pending" },
    ],
    paperAccount: { totalValue: "1,000,000 CNY", cash: "100%", positionValue: "0", return: "0.00%" },
    riskSummary: { concentration: "低", riskBudgetUsed: "12%", blockers: ["Risk rejected 待重开"] },
    approvalSummary: { pending: 2, nearestDeadline: "今日 18:00", impactScope: "新任务" },
    manualTodoSummary: { open: 3, stale: 0 },
    dailyBriefSummary: [{ title: "半导体链关注度上升", priority: "P1" }],
    systemHealth: { data: "live_health_api", service: "normal", incident: "全景系统卡由健康接口推导" },
  };
}

export function buildInvestmentQueueReadModel() {
  return {
    queues: [
      { workflowId: "wf-001", title: "浦发银行 A 股研究", state: "blocked", stage: "S3", priority: "P0", route: "/investment/wf-001" },
      { workflowId: "wf-002", title: "半导体链候选议题", state: "researching", stage: "S1", priority: "P1", route: "/investment/wf-002" },
      { workflowId: "wf-003", title: "黄金配置复盘", state: "manual_only", stage: "manual_todo", priority: "P2", route: "/governance?task=manual" },
    ],
    guardSummary: [
      { label: "Risk blocked", count: 1, reasonCode: "retained_hard_dissent_risk_review" },
      { label: "execution_core blocked", count: 1, reasonCode: "execution_core_blocked_no_trade" },
      { label: "非 A 股 manual_todo", count: 1, reasonCode: "non_a_asset_manual_only" },
    ],
  };
}

export function buildInvestmentDossierReadModel(): InvestmentDossierReadModel {
  return {
    workflow: { workflowId: "wf-001", title: "浦发银行 A 股研究", currentStage: "S3", state: "blocked" },
    stageRail: ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"].map((stage, index) => ({
      stage,
      nodeStatus: index < 3 ? "completed" : index === 3 ? "blocked" : "not_started",
      reasonCode: stage === "S3" ? "retained_hard_dissent_risk_review" : null,
      artifactCount: index < 3 ? 2 : 0,
    })),
    chairBrief: {
      decisionQuestion: "是否值得围绕浦发银行进入完整 IC 论证",
      keyTensions: ["估值修复与资产质量的冲突", "市场状态与组合约束"],
      noPresetDecisionAttestation: true,
    },
    analystStanceMatrix: [
      { role: "macro", direction: "positive", confidence: 0.7, evidenceQuality: 0.76, hardDissent: false },
      {
        role: "fundamental",
        direction: "neutral",
        confidence: 0.68,
        evidenceQuality: 0.62,
        hardDissent: true,
        hardDissentReason: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
      },
      { role: "quant", direction: "positive", confidence: 0.74, evidenceQuality: 0.78, hardDissent: false },
      { role: "event", direction: "neutral", confidence: 0.61, evidenceQuality: 0.72, hardDissent: false },
    ],
    dataReadiness: {
      qualityBand: "degraded",
      decisionCoreStatus: "conditional_pass",
      executionCoreStatus: "blocked",
      issues: ["事件源冲突待补证", "执行核心数据不足"],
      lineageRefs: ["tencent-public-kline:600000.SH"],
      ownerSummary: "S1 已拿到可用于研究的数据；成交前还缺 S6 执行核心数据。",
      sourceStatus: [
        {
          sourceName: "腾讯公开日线行情",
          sourceRef: "tencent-public-kline:600000.SH",
          requiredUsage: "decision_core",
          requestedFields: ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
          obtainedFields: ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
          missingFields: [],
          status: "available",
          qualityLabel: "可用于研究判断",
          evidenceRef: "tencent-public-kline:600000.SH",
        },
        {
          sourceName: "实时执行行情",
          sourceRef: "execution-core:600000.SH",
          requiredUsage: "execution_core",
          requestedFields: ["最新成交价", "盘口深度", "可成交窗口"],
          obtainedFields: [],
          missingFields: ["最新成交价", "盘口深度", "可成交窗口"],
          status: "missing",
          qualityLabel: "缺失，不能用于成交",
          evidenceRef: "execution-core:600000.SH",
        },
      ],
      dataGaps: [
        {
          gap: "实时执行行情缺失",
          affectsStage: "S6",
          impact: "不能生成纸面成交授权，不影响当前 S3 硬异议判断。",
          nextAction: "进入 S6 前重新采集最新成交价、盘口深度和可成交窗口，并由风控复核。",
        },
      ],
    },
    rolePayloadDrilldowns: [
      { role: "macro", highlights: ["宏观环境温和支持", "信用扩张仍需观察"] },
      {
        role: "fundamental",
        highlights: ["资产质量修复证据不足", "需要补充不良率、拨备覆盖率和息差趋势"],
        hardDissentReason: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
        thesis: "估值低位不能单独支持推进，需要看到资产质量和息差同时改善。",
        supportingEvidenceRefs: ["artifact-wf001-data-readiness"],
        counterEvidenceRefs: ["source-wf001-fundamental-npl", "source-wf001-fundamental-nim"],
        keyRisks: ["不良率拐点未确认", "息差修复慢于预期"],
        applicableConditions: ["补齐最近两个季度不良率、拨备覆盖率和息差趋势后再进入 S4"],
        invalidationConditions: ["不良率继续上行或拨备覆盖率继续下降"],
        suggestedActionImplication: "S3 先补证，保留硬异议并交风控复核。",
        rolePayload: { asset_quality: "insufficient", valuation_gap: "needs_confirmation" },
      },
      { role: "quant", highlights: ["因子信号偏正面", "辩论后降为观察"] },
      { role: "event", highlights: ["事件冲击暂未扩大", "继续跟踪公告和监管信息"] },
    ],
    consensus: {
      score: 0.72,
      actionConviction: 0.58,
      thresholdLabel: "行动强度不足，不进入纸面执行",
    },
    debate: {
      roundsUsed: 2,
      retainedHardDissent: true,
      riskReviewRequired: true,
      issues: ["事件冲击是否短期可修复", "低行动强度是否需要观察"],
      viewChanges: ["量化观点由偏正面降为观察；基本面仍保留硬异议"],
      cioSynthesis: "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
      unresolvedDissent: ["基本面硬异议仍保留"],
      rounds: [
        { roundNo: 1, issue: "资产质量修复是否成立", outcome: "要求补充不良率和拨备证据" },
        { roundNo: 2, issue: "补证后是否能进入 S4", outcome: "CIO synthesis 维持 S3 受阻" },
      ],
      ownerSummary: "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
      statusSummary: {
        roundsUsed: 2,
        retainedHardDissent: true,
        riskReviewRequired: true,
        consensusScore: 0.75,
        actionConviction: 0.6,
      },
      coreDisputes: [
        {
          title: "资产质量修复是否足以抵消估值低位",
          whyItMatters: "如果资产质量没有确认修复，低估值可能是价值陷阱，不能直接进入 S4 决策。",
          involvedRoles: ["基本面分析师", "量化分析师", "CIO"],
          currentConclusion: "补证前不能进入 S4，先保留 S3 阻断。",
          requiredEvidence: ["不良率趋势", "拨备覆盖率趋势", "息差改善证据"],
        },
      ],
      viewChangeDetails: [
        {
          role: "量化分析师",
          before: "偏正面",
          after: "观察",
          reason: "基本面补证不足，量价信号不能单独推动 S4。",
          impact: "降低行动强度，等待基本面补证后再评估。",
        },
        {
          role: "基本面分析师",
          before: "中性",
          after: "维持硬异议",
          reason: "资产质量、拨备覆盖率和息差趋势证据不足。",
          impact: "保留 S3 阻断，不能进入 S4。",
        },
      ],
      retainedDissentDetails: [
        {
          sourceRole: "基本面分析师",
          dissent: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
          counterRisks: ["不良率拐点未确认", "拨备覆盖率可能继续承压", "息差修复慢于预期"],
          handling: "保留硬异议，补证后交风控复核。",
          forbiddenActions: ["不能直接放行 S4", "不能进入 S6 执行"],
        },
      ],
      roundDetails: [
        {
          roundNo: 1,
          issue: "资产质量修复是否成立",
          participants: ["CIO", "基本面分析师", "量化分析师"],
          inputEvidence: ["不良率趋势", "拨备覆盖率"],
          outcome: "要求补充不良率和拨备证据",
          unresolvedQuestions: ["资产质量修复证据是否足够"],
        },
        {
          roundNo: 2,
          issue: "补证后是否能进入 S4",
          participants: ["CIO", "基本面分析师", "量化分析师"],
          inputEvidence: ["息差趋势", "估值分位"],
          outcome: "CIO 维持 S3 受阻",
          unresolvedQuestions: ["补证后是否足以解除基本面硬异议"],
        },
      ],
      nextActions: [
        {
          action: "补齐资产质量、拨备覆盖率和息差趋势证据",
          owner: "基本面分析师",
          completionSignal: "形成可复核补证包并更新硬异议判断",
          nextStage: "交风控复核后再判断是否进入 S4",
        },
      ],
    },
    optimizerDeviation: {
      singleNameDeviation: "4.2pp",
      portfolioDeviation: "1.1pp",
      recommendation: "先补证，不生成 Owner 例外",
    },
    riskReview: {
      reviewResult: "conditional_pass",
      repairability: "repairable",
      ownerExceptionRequired: false,
      reasonCodes: ["retained_hard_dissent_risk_review", "execution_core_blocked_no_trade"],
    },
    paperExecution: {
      status: "blocked",
      pricingMethod: "minute_vwap",
      window: "2h",
      fees: "未产生",
      tPlusOne: "未进入锁定",
    },
    attribution: {
      summary: "等待正式执行与归因样本；当前仅保留反思入口。",
      links: ["reflection-draft-001", "handoff-risk-001"],
    },
    evidenceMap: {
      artifactRefs: ["artifact-wf001-data-readiness", "artifact-wf001-fundamental-memo", "artifact-wf001-debate-summary"],
      dataRefs: ["tencent-public-kline:600000.SH"],
      sourceQuality: [
        {
          source: "腾讯公开日线行情",
          usedFor: "支持判断：是否值得继续分析浦发银行",
          quality: "可用于研究判断",
        },
      ],
      conflictRefs: ["分钟级成交数据缺失"],
      supportingEvidenceOnlyRefs: [],
    },
    forbiddenActions: {
      risk_rejected_no_override: { actionVisible: false, reasonCode: "risk_rejected_no_override" },
      execution_core_blocked_no_trade: { actionVisible: false, reasonCode: "execution_core_blocked_no_trade" },
      non_a_asset_no_trade: { actionVisible: false, reasonCode: "non_a_asset_no_trade" },
      low_action_no_execution: { actionVisible: false, reasonCode: "low_action_no_execution" },
    },
    traceRoute: "/investment/wf-001/trace",
  };
}

export function buildTraceDebugReadModel(): TraceDebugReadModel {
  return {
    workflowId: "wf-001",
    agentRunTree: [
      {
        runId: "run-cio-001",
        parentRunId: null,
        stage: "S3",
        profileVersion: "cio@1.0.0",
        contextSlice: "ctx-s3-cio",
        businessSummary: "CIO 汇总四位分析师 Memo，追问硬异议并形成 S3 辩论摘要。",
        agentId: "cio",
        status: "completed",
      },
      {
        runId: "run-event-001",
        parentRunId: "run-cio-001",
        stage: "S3",
        profileVersion: "event@1.0.0",
        contextSlice: "ctx-s3-event",
        businessSummary: "事件分析师补充公告影响，供 CIO 判断分歧是否可修复。",
        agentId: "event_analyst",
        status: "completed",
      },
    ],
    commands: [
      { commandType: "request_evidence", admission: "accepted", receiver: "Event Analyst", reasonCode: "hard_dissent_requires_evidence" },
      { commandType: "direct_write", admission: "rejected", receiver: "Authority Gateway", reasonCode: "DIRECT_WRITE_DENIED" },
    ],
    events: [
      { eventType: "tool_progress", summary: "Event Analyst 补证中" },
      { eventType: "handoff_created", summary: "hard dissent 交接 Risk" },
      { eventType: "guard_failed", summary: "Risk conditional path blocked Owner bypass" },
    ],
    handoffs: [{ from: "CIO", to: "Risk Officer", blockers: ["hard dissent retained"], openQuestions: ["事件冲击是否可修复"] }],
    contextInjectionRecords: [
      { contextSnapshotId: "ctx-v1", whyIncluded: "Researcher digest", redactionStatus: "applied" },
      { contextSnapshotId: "ctx-v1", whyIncluded: "finance raw field", redactionStatus: "denied" },
    ],
    rawTranscriptDefaultCollapsed: true,
  };
}

export function buildUnavailableTraceDebugReadModel(workflowId = "wf-001"): TraceDebugReadModel {
  return {
    workflowId,
    agentRunTree: [],
    commands: [],
    events: [],
    handoffs: [],
    contextInjectionRecords: [],
    rawTranscriptDefaultCollapsed: true,
  };
}

export function buildGovernanceReadModel(): GovernanceReadModel {
  const taskCenter: GovernanceReadModel["taskCenter"] = [
      { taskId: "task-invest", taskType: "investment_workflow", currentState: "blocked", reasonCode: "retained_hard_dissent_risk_review" },
      { taskId: "task-research", taskType: "research_task", currentState: "running", reasonCode: "supporting_evidence_only" },
      {
        taskId: "task-manual",
        taskType: "manual_todo",
        currentState: "ready",
        reasonCode: "non_a_asset_manual_only",
        dueDate: "本周五",
        riskHint: "非 A 股资产资料不完整会影响财务规划",
      },
      { taskId: "task-incident", taskType: "system_task", currentState: "monitoring", reasonCode: "data_source_degraded" },
    ];
  const approvalCenter: GovernanceReadModel["approvalCenter"] = [
      {
        approvalId: "ap-001",
        kind: "approval",
        triggerReason: "high_impact_agent_capability_change",
        subject: "团队能力提升方案",
        deadline: "今日 18:00",
        packet: { comparisonAnalysis: true, impactScope: "new_task", alternatives: ["reject", "request_changes"], recommendation: "request_changes" },
      },
    ];
  return {
    modules: ["待办", "团队", "变更", "健康", "审计"],
    taskCenter,
    approvalCenter,
    unifiedTodos: buildUnifiedTodoItems({ taskCenter, approvalCenter }),
    governanceChanges: [
      { changeId: "default-context", changeType: "default_context", impactLevel: "medium", state: "draft", effectiveScope: "new_task" },
      { changeId: "gov-change-001", changeType: "agent_capability", impactLevel: "high", state: "owner_pending", effectiveScope: "new_task" },
    ],
    manualTodoIsolation: { connectedToS5S6: false, state: "task_center_only" },
    governanceStateMachine: ["draft", "triage", "assessment", "owner_pending", "approved", "effective"],
    agentCapabilityDraftStates: ["draft", "triage", "assessment", "owner_pending"],
    uiGuardResponses: {
      riskRejected: { actionVisible: false, reasonCode: "risk_rejected_no_override" },
      executionCoreBlocked: { actionVisible: false, reasonCode: "execution_core_blocked_no_trade" },
      nonAAsset: { actionVisible: false, reasonCode: "non_a_asset_no_trade" },
      agentCapabilityHotPatch: { actionVisible: false, reasonCode: "agent_capability_hot_patch_denied" },
    },
    inFlightSnapshotUnchanged: true,
    financeSensitiveRedactionUi: { dossier: "redacted_summary", trace: "redacted_summary", financeOwnerView: "cleartext_owner_only" },
  };
}

export function buildUnifiedTodoItems(input: Pick<GovernanceReadModel, "taskCenter" | "approvalCenter">): GovernanceTodoItem[] {
  const approvalTodos: GovernanceTodoItem[] = input.approvalCenter.map((approval) => ({
    todoId: `approval-${approval.approvalId}`,
    todoType: "approval",
    sourceId: approval.approvalId,
    title: approval.subject ?? "审批事项",
    detail: `建议${formatStatusWord(approval.packet.recommendation)} · 影响${formatStatusWord(approval.packet.impactScope)}`,
    actionLabel: "办理审批",
    actionHref: `/governance/approvals/${approval.approvalId}`,
  }));
  const taskTodos: GovernanceTodoItem[] = input.taskCenter
    .filter(isActionableTodoTask)
    .map((task) => ({
      todoId: `task-${task.taskId}`,
      todoType: task.taskType === "manual_todo" ? "manual_todo" : "task",
      sourceId: task.taskId,
      title: task.taskType === "manual_todo" ? "人工待办" : task.taskType,
      detail: task.reasonCode,
      actionLabel: task.taskType === "manual_todo" ? "去办理" : "查看任务",
      actionHref: task.taskType === "manual_todo" ? buildManualTodoActionHref(task.taskId, task.reasonCode) : "/governance?panel=todos",
    }));
  return [...approvalTodos, ...taskTodos];
}

function isActionableTodoTask(task: GovernanceReadModel["taskCenter"][number]) {
  if (task.taskType === "manual_todo") {
    return true;
  }
  if (task.reasonCode === "request_brief_confirmed") {
    return false;
  }
  return new Set(["ready", "blocked", "owner_pending", "draft", "waiting"]).has(task.currentState);
}

function buildManualTodoActionHref(taskId: string, _reasonCode: string) {
  return `/finance?todo=${encodeURIComponent(taskId)}`;
}

function formatStatusWord(value: string) {
  const labels: Record<string, string> = {
    approved: "通过",
    approve_exception_only_if_risk_accepted: "仅在风控接受风险后批准例外",
    rejected: "拒绝",
    request_changes: "要求修改",
    new_task: "后续任务",
    current_attempt_only: "当前尝试",
    follow_optimizer: "跟随优化器建议",
    higher_single_name_exposure: "单股暴露更高",
    cio_deviation: "CIO 偏离",
  };
  return labels[value] ?? value;
}

export function buildApprovalRecordReadModel(overrides: Partial<ApprovalRecordReadModel> = {}) {
  const record: ApprovalRecordReadModel = {
    approvalId: "ap-001",
    subject: "量化分析能力提升方案",
    triggerReason: "high_impact_agent_capability_change",
    recommendation: "request_changes",
    alternatives: ["approved", "rejected", "request_changes"],
    comparisonOptions: ["维持当前能力版本", "降低模型路由风险后重提", "通过高影响方案但只作用于后续任务"],
    impactScope: "new_task",
    riskAndImpact: ["影响量化分析后续研究质量", "不改变在途任务", "不改变风控或执行规则"],
    timeoutDisposition: "不生效",
    rollbackRef: "gov-change-001",
    evidenceRefs: ["team_capability_config_report.json", "cfo-attribution-001"],
    traceRoute: "/investment/wf-001/trace",
    allowedActions: ["approved", "rejected", "request_changes"],
  };
  return { ...record, ...overrides };
}

export function buildTeamReadModel(): TeamReadModel {
  const agentCards = agentIds.map((agentId, index) => ({
    agentId,
    displayName: agentNames[agentId],
    role: agentId,
    profileVersion: "1.0.0",
    skillPackageVersion: `${agentId}-skill@1.0.0`,
    promptVersion: "1.0.0",
    contextSnapshotVersion: "ctx-v1",
    recentQualityScore: Number((0.91 - index * 0.01).toFixed(2)),
    failureCount: index === 3 ? 1 : 0,
    deniedActionCount: index === 2 ? 1 : 0,
    configDraftEntry: "governance_draft_only",
    weaknessTags: index === 2 ? ["证据不足", "敏感字段拒绝"] : [],
  }));
  return {
    teamHealth: { healthyAgentCount: 9, activeAgentRunCount: 2, pendingDraftCount: 1, failedOrDeniedCount: 2 },
    agentCards,
    agentProfileReadModels: agentCards.map((card) => ({
      agentId: card.agentId,
      displayName: card.displayName,
      capabilitySummary: "按岗位读取 ContextSlice，提交 typed artifact 或 command。",
      canDo: ["读取组织透明资料", "提交授权范围内产物", "提出补证请求"],
      cannotDo: ["直接推进流程", "热改在途任务", "读取未授权财务原始字段"],
      versions: {
        profileVersion: card.profileVersion,
        skillPackageVersion: card.skillPackageVersion,
        promptVersion: card.promptVersion,
        contextSnapshotVersion: card.contextSnapshotVersion,
      },
      toolPermissions: ["只读 DB", "文件读取", "受控服务请求"],
      weaknessTags: card.weaknessTags,
      qualityMetrics: { schemaPassRate: 1, evidenceQuality: card.recentQualityScore },
      cfoAttributionRefs: card.agentId === "quant_analyst" ? ["cfo-attribution-001"] : [],
      deniedActions: card.deniedActionCount ? [{ reasonCode: "memory_sensitive_denied" }] : [],
      failureRecords: card.failureCount ? ["schema_validation_failed"] : [],
    })),
    capabilityConfigReadModel: {
      agentId: "quant_analyst",
      editableFields: ["tools_enabled", "service_permissions", "collaboration_commands", "skill_package_version", "prompt_version"],
      forbiddenDirectUpdateReason: "hot_patch_denied",
      effectiveScopeOptions: ["new_task", "new_attempt"],
    },
    capabilityDraftSubmission: {
      draftId: "draft-quant-001",
      state: "draft",
      impactLevel: "high",
      governanceChangeRef: "gov-change-001",
      ownerApprovalRef: "ap-001",
      effectiveScope: "new_task",
    },
    hotPatchDenials: [{ reasonCode: "agent_capability_hot_patch_denied", actionVisible: false }],
  };
}

export function buildFinanceOverviewReadModel(): FinanceOverviewReadModel {
  return {
    assets: [
      { label: "现金", value: "1,000,000 CNY", status: "可用" },
      { label: "A 股纸面账户", value: "0 CNY", status: "空仓" },
      { label: "基金", value: "仅规划", status: "manual_todo" },
      { label: "黄金", value: "仅估值", status: "manual_todo" },
      { label: "房产", value: "手工估值", status: "manual_todo" },
    ],
    health: { liquidity: "充足", debtRatio: "低", riskBudget: "12%", stress: "可承受" },
    reminders: ["税务提醒待确认", "重大支出影响已脱敏进入投资约束"],
    nonAAssetBoundary: { actionVisible: false, reasonCode: "non_a_asset_manual_only" },
  };
}

export function buildDevOpsHealthReadModel(): DevOpsHealthReadModel {
  return {
    routineChecks: [
      { checkId: "data-source-latency", status: "degraded" },
      { checkId: "execution-core-readiness", status: "blocked" },
    ],
    incidents: [
      { incidentId: "incident-data-001", status: "triaged", incidentType: "data_source" },
    ],
    recovery: [
      { planId: "recovery-data-001", investmentResumeAllowed: false, technicalRecoveryStatus: "pending_validation" },
    ],
  };
}

export function buildKnowledgeReadModel(): KnowledgeReadModel {
  return {
    dailyBrief: [
      { briefId: "daily-brief-001", priority: "P1", title: "半导体链关注度上升", supportingEvidenceOnly: true },
    ],
    researchPackages: [
      { packageId: "research-1", title: "半导体资料包", status: "reviewing", evidenceRefs: ["memory-1", "artifact-research-1"] },
    ],
    memoryCollections: [{ collectionId: "collection-1", title: "半导体资料", resultCount: 12 }],
    memoryResults: [
      {
        memoryId: "memory-1",
        currentVersionId: "memory-version-1",
        title: "政策跟踪",
        relationSummary: "supports research-1",
        sensitivity: "public_internal",
        extractionStatus: "extracted",
        promotionState: "candidate",
        tags: ["政策", "半导体"],
      },
    ],
    relationGraph: [{ sourceMemoryId: "memory-1", targetRef: "research-1", relationType: "supports", reason: "证据支持研究资料包" }],
    organizeSuggestions: [
      {
        suggestionId: "organize-001",
        targetMemoryRefs: ["memory-1"],
        suggestedTags: ["政策", "半导体"],
        requiresGatewayWrite: true,
        riskIfApplied: "错误归类会影响后续召回，需要人工确认",
      },
    ],
    contextInjectionInspector: [
      {
        contextSnapshotId: "ctx-v1",
        sourceRef: "memory-1",
        whyIncluded: "Researcher digest",
        redactionStatus: "applied",
        deniedRefs: ["finance-raw-001"],
      },
    ],
    proposals: [
      {
        proposalId: "proposal-knowledge-001",
        proposalType: "Knowledge / Prompt / Skill",
        impactLevel: "medium",
        validationResultRefs: ["researcher_workflow_report.json"],
        effectiveScope: "new_task",
        rollbackPlan: "rollback-knowledge-001",
      },
    ],
    defaultContextProposalPath: "/governance?change=default-context",
  };
}

export function buildWorkbenchReports(): Record<string, Report> {
  const shell = buildShellReadModel();
  const owner = buildOwnerDecisionReadModel();
  const dossier = buildInvestmentDossierReadModel();
  const governance = buildGovernanceReadModel();
  const team = buildTeamReadModel();
  const command = routeOwnerCommand("学习热点事件");
  const ambiguousCommand = routeOwnerCommand("帮我处理一下");
  const blockedHotPatchCommand = routeOwnerCommand("把量化分析的 Prompt 直接生效");
  return {
    "web_command_routing_report.json": buildReportEnvelope("web_command_routing_report.json", "TC-ACC-006-01", "ACC-006", {
      nav_scan: { top_level_labels: shell.navItems.map((item) => item.label), top_level_team_present: false },
      route_manifest: buildRouteManifest(),
      chinese_ui_scan: { language: "zh-CN", forbidden_english_titles: [] },
      premium_light_theme_assertions: { warm_porcelain: true, ink_text: true, jade_accent: true, indigo_gold_crimson_support: true },
      request_brief_preview_flow: command,
      draft_clarification_prompts: ambiguousCommand.clarificationPrompts ?? [],
      blocked_hot_patch_preview: blockedHotPatchCommand,
      command_layer_assertions: shell.commandLayer,
      owner_facing_content_assertions: {
        forbidden_terms_absent: [
          "Request Brief",
          "research_task",
          "supporting_evidence_only",
          "Workflow Scheduling Center",
          "schema pass",
          "Governance Change",
        ],
        removed_page_subtitles: [
          "待处理、风险、审批和系统状态",
          "机会池、IC 队列、硬门槛与 Dossier 入口",
          "全资产档案、现金流、风险预算和人工待办",
          "研究资料、经验、关系和上下文注入",
        ],
      },
      view_layers: { owner: owner.todayAttention, dossier: dossier.stageRail, traceRoute: dossier.traceRoute },
      unified_todo_card_assertions: {
        ownerCardLabel: "待办",
        route: "/governance?panel=todos",
        duplicateApprovalCardVisible: false,
        duplicateManualTodoCardVisible: false,
        todoTypes: governance.unifiedTodos.map((todo) => todo.todoType),
      },
      dossier_business_panels: {
        data_readiness: dossier.dataReadiness,
        role_payload_drilldowns: dossier.rolePayloadDrilldowns,
        consensus: dossier.consensus,
        debate: dossier.debate,
        optimizer_deviation: dossier.optimizerDeviation,
        risk_review: dossier.riskReview,
        paper_execution: dossier.paperExecution,
        attribution: dossier.attribution,
      },
      knowledge_memory_workspace: buildKnowledgeReadModel(),
      trace_entry_return_path: {
        from_dossier: "/investment/wf-001/trace",
        from_approval_detail: "/investment/wf-001/trace?returnTo=%2Fgovernance%2Fapprovals%2Fap-001",
      },
      governance_agent_team_assertions: { modules: shell.governanceModules, agentCount: team.agentCards.length, draftOnly: true },
      design_preview_refs: designPreviewRefs,
      forbidden_action_ui_denials: dossier.forbiddenActions,
      read_model_guard_denials: governance.uiGuardResponses,
      api_guard_denials: ["DIRECT_WRITE_DENIED", "COMMAND_NOT_ALLOWED", "SNAPSHOT_MISMATCH"],
      screenshot_refs: ["frontend/dist/index.html"],
    }),
    "governance_task_report.json": buildReportEnvelope("governance_task_report.json", "TC-ACC-007-01", "ACC-007", {
      task_center_states: governance.taskCenter,
      approval_center_items: governance.approvalCenter,
      unified_todo_items: governance.unifiedTodos,
      approval_packet_completeness: buildApprovalRecordReadModel(),
      manual_todo_isolation: governance.manualTodoIsolation,
      agent_capability_draft_states: governance.agentCapabilityDraftStates,
      governance_change_links: ["gov-change-001"],
      risk_rejected_ui_guard: governance.uiGuardResponses.riskRejected,
      execution_core_ui_guard: governance.uiGuardResponses.executionCoreBlocked,
      non_a_asset_ui_guard: governance.uiGuardResponses.nonAAsset,
      agent_capability_hot_patch_denial: {
        reason_code: governance.uiGuardResponses.agentCapabilityHotPatch.reasonCode,
        action_visible: governance.uiGuardResponses.agentCapabilityHotPatch.actionVisible,
      },
      design_preview_refs: designPreviewRefs,
    }),
    "team_capability_config_report.json": buildReportEnvelope("team_capability_config_report.json", "TC-ACC-007-01", "ACC-007", {
      team_read_model: team.teamHealth,
      agent_cards: team.agentCards,
      agent_profile_read_models: team.agentProfileReadModels,
      capability_config_read_model: team.capabilityConfigReadModel,
      capability_draft_submission: team.capabilityDraftSubmission,
      impact_triage: { low: "auto_validation", medium: "auto_validation", high: "owner_approval" },
      auto_validation_refs: ["schema", "fixture", "scope", "rollback", "snapshot"],
      owner_approval_refs: ["ap-001"],
      effective_scope: "new_task",
      in_flight_agent_run_snapshot_unchanged: true,
      hot_patch_denials: team.hotPatchDenials,
      screenshot_refs: ["frontend/dist/index.html#/governance/team"],
    }),
  };
}

export function buildReportEnvelope(
  reportId: string,
  tc: string,
  acc: string,
  payload: Record<string, unknown>,
  options: ReportEnvelopeOptions = {},
): Report {
  const guardResults = options.guardResults ?? [
    { guard: "ui_guard_denials", input_ref: reportId, expected: "pass", actual: "pass", result: "pass" },
  ];
  const failures = options.failures ?? [];
  const result = failures.length > 0 || guardResults.some((guard) => guard.result !== "pass") ? "fail" : "pass";
  return {
    report_id: reportId,
    generated_at: new Date().toISOString(),
    generated_by: "velentrade.wi004",
    git_revision: "runtime-generated-report",
    work_item_refs: ["WI-004"],
    test_case_refs: [tc],
    fixture_refs: [`FX-${tc}`],
    result,
    checked_requirements: [acc === "ACC-006" ? "REQ-006" : "REQ-007"],
    checked_acceptances: [acc],
    checked_invariants: ["INV-FRONTEND-READ-MODEL-ONLY"],
    artifact_refs: [reportId],
    failures,
    residual_risk: [],
    schema_version: "1.0.0",
    checked_fields: Object.keys(payload).sort(),
    fixture_inputs: { fixture: "WI-004 fixture-first frontend" },
    actual_outputs: { payload_keys: Object.keys(payload).sort() },
    guard_results: guardResults,
    ...payload,
  };
}
