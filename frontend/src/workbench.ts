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
  qualityMetrics: {
    schemaPassRate: number;
    evidenceQuality: number;
  };
  cfoAttributionRefs: string[];
  deniedActions: Array<{ reasonCode: string }>;
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
    hardDissent: boolean;
  }>;
  forbiddenActions: Record<string, { actionVisible: boolean; reasonCode: string }>;
  traceRoute: string;
};

export type TraceDebugReadModel = {
  workflowId: string;
  agentRunTree: Array<{ runId: string; parentRunId: string | null; stage: string; profileVersion: string; contextSlice: string }>;
  commands: Array<{ commandType: string; admission: string; receiver: string; reasonCode: string }>;
  events: Array<{ eventType: string; summary: string }>;
  handoffs: Array<{ from: string; to: string; blockers: string[]; openQuestions: string[] }>;
  contextInjectionRecords: Array<{ contextSnapshotId: string; whyIncluded: string; redactionStatus: string }>;
  rawTranscriptDefaultCollapsed: boolean;
};

export type KnowledgeReadModel = {
  memoryCollections: Array<{ collectionId: string; title: string; resultCount: number }>;
  memoryResults: Array<{ memoryId: string; title: string; relationSummary: string; sensitivity: string }>;
  relationGraph: Array<{ sourceMemoryId: string; targetRef: string; relationType: string }>;
  contextInjectionInspector: Array<{ contextSnapshotId: string; whyIncluded: string; redactionStatus: string }>;
  defaultContextProposalPath: string;
};

export type FinanceOverviewReadModel = {
  assets: Array<{ label: string; value: string; status: string }>;
  health: { liquidity: string; debtRatio: string; riskBudget: string; stress: string };
  reminders: string[];
  nonAAssetBoundary: { actionVisible: boolean; reasonCode: string };
};

export type GovernanceReadModel = {
  modules: string[];
  taskCenter: Array<{ taskId: string; taskType: string; currentState: string; reasonCode: string }>;
  approvalCenter: Array<{
    approvalId: string;
    kind: string;
    triggerReason: string;
    packet: { comparisonAnalysis: boolean; impactScope: string; alternatives: string[]; recommendation: string };
  }>;
  governanceChanges: Array<{ changeId: string; changeType: string; impactLevel: string; state: string; effectiveScope: string }>;
  manualTodoIsolation: { connectedToS5S6: boolean; state: string };
  governanceStateMachine: string[];
  agentCapabilityDraftStates: string[];
  uiGuardResponses: Record<string, { actionVisible: boolean; reasonCode: string }>;
  inFlightSnapshotUnchanged: boolean;
  financeSensitiveRedactionUi: { dossier: string; trace: string; financeOwnerView: string };
};

export type DevOpsHealthReadModel = {
  routineChecks: Array<{ checkId: string; status: string }>;
  incidents: Array<{ incidentId: string; status: string; incidentType: string }>;
  recovery: Array<{ planId: string; investmentResumeAllowed: boolean }>;
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
    { path: "/governance/team", page: "agent-team", topNavId: "governance", label: "Agent 团队" },
    { path: "/governance/team/:agentId", page: "agent-profile", topNavId: "governance", label: "Agent 画像" },
    { path: "/governance/team/:agentId/config", page: "agent-config", topNavId: "governance", label: "能力配置草案" },
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
    [/^\/governance\/team$/, "agent-team", "governance", "/governance/team", [], "Agent 团队"],
    [/^\/governance\/team\/([^/]+)\/config$/, "agent-config", "governance", "/governance/team/:agentId/config", ["agentId"], "能力配置草案"],
    [/^\/governance\/team\/([^/]+)$/, "agent-profile", "governance", "/governance/team/:agentId", ["agentId"], "Agent 画像"],
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
    governanceModules: ["任务", "审批", "Agent 团队", "变更", "健康", "审计"],
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
        artifactsLabel: "能力配置草案 / 治理变更草案",
        boundaryLabel: "不能热改运行中的 Agent",
        nextStepLabel: "改为治理变更草案后再评估",
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
        authorityLabel: "任务中心",
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
        statusLabel: "草案",
        taskLabel: "能力改进",
        leadLabel: "治理运行时",
        authorityLabel: "治理流程",
        artifactsLabel: "能力配置草案 / 治理变更草案",
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
      { label: "待审批", count: 2, route: "/governance/approvals/ap-001", severity: "pending" },
      { label: "人工待办", count: 3, route: "/governance?task=manual", severity: "notice" },
    ],
    paperAccount: { totalValue: "1,000,000 CNY", cash: "100%", positionValue: "0", return: "0.00%" },
    riskSummary: { concentration: "低", riskBudgetUsed: "12%", blockers: ["Risk rejected 待重开"] },
    approvalSummary: { pending: 2, nearestDeadline: "今日 18:00", impactScope: "新任务" },
    manualTodoSummary: { open: 3, stale: 0 },
    dailyBriefSummary: [{ title: "半导体链关注度上升", priority: "P1" }],
    systemHealth: { data: "degraded", service: "normal", incident: "数据源延迟已交接 Risk" },
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
      { role: "Macro", direction: "谨慎", confidence: 0.7, hardDissent: false },
      { role: "Fundamental", direction: "正向", confidence: 0.76, hardDissent: false },
      { role: "Quant", direction: "中性", confidence: 0.61, hardDissent: false },
      { role: "Event", direction: "反向", confidence: 0.82, hardDissent: true },
    ],
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
      { runId: "run-cio-001", parentRunId: null, stage: "S3", profileVersion: "cio@1.0.0", contextSlice: "ctx-s3-cio" },
      { runId: "run-event-001", parentRunId: "run-cio-001", stage: "S3", profileVersion: "event@1.0.0", contextSlice: "ctx-s3-event" },
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

export function buildGovernanceReadModel(): GovernanceReadModel {
  return {
    modules: ["任务", "审批", "Agent 团队", "变更", "健康", "审计"],
    taskCenter: [
      { taskId: "task-invest", taskType: "investment_workflow", currentState: "blocked", reasonCode: "retained_hard_dissent_risk_review" },
      { taskId: "task-research", taskType: "research_task", currentState: "running", reasonCode: "supporting_evidence_only" },
      { taskId: "task-manual", taskType: "manual_todo", currentState: "ready", reasonCode: "non_a_asset_manual_only" },
      { taskId: "task-incident", taskType: "system_task", currentState: "monitoring", reasonCode: "data_source_degraded" },
    ],
    approvalCenter: [
      {
        approvalId: "ap-001",
        kind: "approval",
        triggerReason: "high_impact_agent_capability_change",
        packet: { comparisonAnalysis: true, impactScope: "new_task", alternatives: ["reject", "request_changes"], recommendation: "request_changes" },
      },
    ],
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

export function buildApprovalRecordReadModel() {
  return {
    approvalId: "ap-001",
    subject: "Quant Analyst 能力配置草案",
    triggerReason: "high_impact_agent_capability_change",
    recommendation: "request_changes",
    alternatives: ["approved", "rejected", "request_changes"],
    impactScope: "new_task",
    timeoutDisposition: "不生效",
    rollbackRef: "gov-change-001",
    evidenceRefs: ["team_capability_config_report.json", "cfo-attribution-001"],
    traceRoute: "/investment/wf-001/trace",
    allowedActions: ["approved", "rejected", "request_changes"],
  };
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
      cannotDo: ["直接推进 workflow", "热改在途 AgentRun", "读取未授权财务原始字段"],
      qualityMetrics: { schemaPassRate: 1, evidenceQuality: card.recentQualityScore },
      cfoAttributionRefs: card.agentId === "quant_analyst" ? ["cfo-attribution-001"] : [],
      deniedActions: card.deniedActionCount ? [{ reasonCode: "memory_sensitive_denied" }] : [],
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
      { planId: "recovery-data-001", investmentResumeAllowed: false },
    ],
  };
}

export function buildKnowledgeReadModel(): KnowledgeReadModel {
  return {
    memoryCollections: [{ collectionId: "collection-1", title: "半导体资料", resultCount: 12 }],
    memoryResults: [{ memoryId: "memory-1", title: "政策跟踪", relationSummary: "supports research-1", sensitivity: "public_internal" }],
    relationGraph: [{ sourceMemoryId: "memory-1", targetRef: "research-1", relationType: "supports" }],
    contextInjectionInspector: [{ contextSnapshotId: "ctx-v1", whyIncluded: "Researcher digest", redactionStatus: "applied" }],
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
    generated_at: "2026-04-30T00:00:00Z",
    generated_by: "velentrade.wi004",
    git_revision: "working-tree",
    work_item_refs: ["WI-004"],
    test_case_refs: [tc],
    fixture_refs: [`FX-${tc}`],
    result,
    checked_requirements: [acc === "ACC-006" ? "REQ-006" : "REQ-007"],
    checked_acceptances: [acc],
    checked_invariants: ["INV-FRONTEND-READ-MODEL-ONLY"],
    artifact_refs: [],
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
