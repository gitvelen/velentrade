import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  FileSearch,
  GitBranch,
  Landmark,
  Layers3,
  LockKeyhole,
  MessageSquareText,
  ShieldAlert,
  Sparkles,
  WalletCards,
} from "lucide-react";

import {
  AgentProfileReadModel,
  ApprovalDecisionApiReadModel,
  CapabilityConfigReadModel,
  DevOpsHealthReadModel,
  FinanceOverviewReadModel,
  GovernanceReadModel,
  GovernanceTodoItem,
  InvestmentDossierReadModel,
  KnowledgeReadModel,
  ApprovalRecordReadModel,
  RequestBriefPreview,
  ResolvedWorkbenchRoute,
  TeamReadModel,
  TraceDebugReadModel,
  buildApprovalRecordReadModel,
  buildDevOpsHealthReadModel,
  buildGovernanceReadModel,
  buildInvestmentQueueReadModel,
  buildRequestBriefPreviewFromApi,
  buildShellReadModel,
  buildTeamReadModel,
  buildUnavailableTraceDebugReadModel,
  resolveWorkbenchRoute,
} from "./workbench";
import {
  ApiRequestError,
  RequestBriefApiReadModel,
  TaskCardApiReadModel,
  applyMemoryOrganizeSuggestion,
  buildEmptyKnowledgeReadModel,
  buildUnavailableInvestmentDossierReadModel,
  confirmRequestBrief,
  createCapabilityDraft,
  createMemoryItem,
  createRequestBrief,
  loadApprovalRecordReadModel,
  loadAgentCapabilityConfigReadModel,
  loadAgentProfileReadModel,
  loadDevOpsHealthReadModel,
  loadFinanceOverviewReadModel,
  loadGovernanceReadModel,
  loadInvestmentDossierReadModel,
  loadKnowledgeReadModel,
  loadTeamReadModel,
  loadTraceDebugReadModel,
  submitApprovalDecision,
  updateFinanceAsset,
} from "./api";
import "./styles.css";

type Navigate = (href: string) => void;
type ConfirmedTaskFeedback = { label: string; href?: string; status: "success" | "error" };
type ReadModelStatus = "loading" | "ready" | "error";
type RemoteReadModel<T> = {
  data: T;
  status: ReadModelStatus;
  retry: () => void;
};

function App() {
  const shell = buildShellReadModel();
  const [currentLocation, setCurrentLocation] = useState(`${window.location.pathname}${window.location.search}`);
  const route = useMemo(() => resolveWorkbenchRoute(currentLocation), [currentLocation]);
  const [command, setCommand] = useState("学习热点事件");
  const [commandOpen, setCommandOpen] = useState(false);
  const [generatedPreview, setGeneratedPreview] = useState<RequestBriefPreview | null>(null);
  const [requestBrief, setRequestBrief] = useState<RequestBriefApiReadModel | null>(null);
  const [requestBriefStatus, setRequestBriefStatus] = useState<"idle" | "syncing" | "ready" | "failed">("idle");
  const [confirmedTask, setConfirmedTask] = useState<ConfirmedTaskFeedback | null>(null);

  useEffect(() => {
    const onPopState = () => setCurrentLocation(`${window.location.pathname}${window.location.search}`);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate: Navigate = (href) => {
    const url = new URL(href, window.location.origin);
    window.history.pushState({}, "", `${url.pathname}${url.search}`);
    setCurrentLocation(`${url.pathname}${url.search}`);
  };

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">Velentrade</div>
        <nav>
          {shell.navItems.map((item) => (
            <WorkbenchLink
              active={item.id === route.topNavId}
              href={item.route}
              key={item.id}
              onNavigate={navigate}
            >
              {item.label}
            </WorkbenchLink>
          ))}
        </nav>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div className="topbar-left" aria-label="今日状态">
            <strong>今日</strong>
            <span className="badge danger">风控 {shell.attentionCounts.riskBlocked}</span>
            <span className="badge warn">待办 {shell.attentionCounts.approvals + shell.attentionCounts.manualTodo}</span>
          </div>
          <div className="topbar-actions">
            <span className="badge">已同步</span>
            <button
              aria-controls="command-panel"
              aria-expanded={commandOpen}
              className="command-drawer"
              onClick={() => setCommandOpen((open) => !open)}
              type="button"
            >
              <MessageSquareText size={16} />
              自由对话
            </button>
            {commandOpen ? (
              <section className="command-panel" id="command-panel" aria-label="自由对话">
                <div className="command-input">
                  <input
                    value={command}
                    onChange={(event) => {
                      setCommand(event.target.value);
                      setGeneratedPreview(null);
                      setRequestBrief(null);
                      setRequestBriefStatus("idle");
                      setConfirmedTask(null);
                    }}
                    aria-label="自然语言请求"
                  />
                  <button
                    type="button"
                    disabled={requestBriefStatus === "syncing"}
                    onClick={() => {
                      setGeneratedPreview(null);
                      setRequestBrief(null);
                      setRequestBriefStatus("syncing");
                      setConfirmedTask(null);
                      createRequestBrief(command)
                        .then((brief) => {
                          setRequestBrief(brief);
                          setGeneratedPreview(buildRequestBriefPreviewFromApi(command, brief));
                          setRequestBriefStatus("ready");
                        })
                        .catch(() => {
                          setGeneratedPreview(null);
                          setRequestBriefStatus("failed");
                        });
                    }}
                  >
                    {requestBriefStatus === "syncing" ? "正在生成预览" : "生成请求预览"}
                  </button>
                </div>
                {generatedPreview ? (
                  <RequestPreviewCard
                    preview={generatedPreview}
                    confirmedTask={confirmedTask}
                    onCancel={() => {
                      setGeneratedPreview(null);
                      setRequestBrief(null);
                      setRequestBriefStatus("idle");
                      setConfirmedTask(null);
                    }}
                    onConfirm={() => {
                      if (!requestBrief?.briefId) {
                        return;
                      }
                      confirmRequestBrief(requestBrief.briefId, requestBrief.version)
                        .then((task: TaskCardApiReadModel) => {
                          setConfirmedTask({
                            label: `任务卡已生成：${task.taskId}`,
                            href: task.workflowId ? `/investment/${task.workflowId}` : undefined,
                            status: "success",
                          });
                        })
                        .catch(() => setConfirmedTask({ label: "任务卡生成失败，请重试", status: "error" }));
                    }}
                    onNavigate={navigate}
                    requestBriefStatus={requestBriefStatus}
                    canConfirm={Boolean(requestBrief?.briefId)}
                  />
                ) : (
                  <div className={`request-preview-empty ${requestBriefStatus === "failed" ? "danger" : ""}`.trim()}>
                    {requestBriefStatus === "syncing"
                      ? "正在向 API 生成请求预览..."
                      : requestBriefStatus === "failed"
                        ? "请求预览生成失败，请确认 API 已连接后重试。"
                        : "输入一句话后生成预览，系统只说明将做什么，不会直接执行。"}
                  </div>
                )}
              </section>
            ) : null}
          </div>
        </header>
        <div className="workspace-content">
          <WorkbenchRouteErrorBoundary key={currentLocation} route={route} onNavigate={navigate}>
            {renderWorkbenchPage(route, navigate)}
          </WorkbenchRouteErrorBoundary>
        </div>
      </main>
    </div>
  );
}

type WorkbenchRouteErrorBoundaryProps = {
  route: ResolvedWorkbenchRoute;
  onNavigate: Navigate;
  children: React.ReactNode;
};

type WorkbenchRouteErrorBoundaryState = {
  hasError: boolean;
  message: string;
};

class WorkbenchRouteErrorBoundary extends React.Component<WorkbenchRouteErrorBoundaryProps, WorkbenchRouteErrorBoundaryState> {
  state: WorkbenchRouteErrorBoundaryState = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): WorkbenchRouteErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Workbench route render failed", error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }
    const isTeamRoute = this.props.route.page === "agent-profile" || this.props.route.page === "agent-config";
    return (
      <section className="page-grid profile-grid">
        <div className="flat-panel">
          <h3><AlertTriangle size={16} />{isTeamRoute ? "团队画像暂不可用" : "页面暂不可用"}</h3>
          <p className="panel-note">真实数据暂时无法渲染，页面没有展示业务结论。可重试或返回上一层。</p>
          <div className="agent-actions">
            <button className="ghost-button" onClick={() => this.setState({ hasError: false, message: "" })} type="button">重试</button>
            <WorkbenchLink href="/governance?panel=team" onNavigate={this.props.onNavigate}>返回团队</WorkbenchLink>
          </div>
          <p className="panel-note danger">{this.state.message}</p>
        </div>
      </section>
    );
  }
}

export function renderWorkbenchPage(route: ResolvedWorkbenchRoute, navigate: Navigate) {
  switch (route.page) {
    case "overview":
      return <OverviewPage onNavigate={navigate} />;
    case "investment-queue":
      return <InvestmentQueuePage onNavigate={navigate} />;
    case "investment-dossier":
      return <InvestmentDossierPage route={route} onNavigate={navigate} />;
    case "trace-debug":
      return <TraceDebugPage route={route} onNavigate={navigate} />;
    case "finance":
      return <FinancePage route={route} />;
    case "knowledge":
      return <KnowledgePage onNavigate={navigate} />;
    case "governance":
      return <GovernancePage route={route} onNavigate={navigate} />;
    case "agent-team":
      return <AgentTeamPage onNavigate={navigate} />;
    case "agent-profile":
      return <AgentProfilePage agentId={route.params.agentId} onNavigate={navigate} />;
    case "agent-config":
      return <AgentConfigPage agentId={route.params.agentId} onNavigate={navigate} />;
    case "approval-detail":
      return <ApprovalDetailPage approvalId={route.params.approvalId} onNavigate={navigate} />;
    default:
      return <NotFoundPage onNavigate={navigate} />;
  }
}

function OverviewPage({ onNavigate }: { onNavigate: Navigate }) {
  const governance = useGovernanceReadModel().data;
  const financeState = useFinanceOverviewReadModel();
  const financeSummary = summarizeFinanceAssets(financeState.data.assets);
  const knowledgeState = useKnowledgeReadModel();
  const dossierState = useInvestmentDossierReadModel("wf-001");
  const dossier = dossierState.data;
  const healthState = useDevOpsHealthReadModel({ silentFallback: false });
  const systemHealth = buildOverviewSystemHealth(healthState.data, healthState.status);
  const todoCount = governance.unifiedTodos.length;
  const firstTodo = governance.unifiedTodos[0];
  const capabilityChange = governance.governanceChanges.find((change) => change.changeType === "agent_capability");
  const dossierReady = dossierState.status === "ready" && dossier.workflow.state !== "unavailable";
  const riskItems = dossierReady ? buildDossierRiskReviewItems(dossier) : [];
  const riskLinks = dossierReady ? buildOverviewRiskLinks(dossier, riskItems) : [];
  return (
    <section className="page-grid overview-grid" aria-labelledby="overview-title">
      <h1 className="sr-only" id="overview-title">全景</h1>
      <ReadModelStatusBanner status={healthState.status} onRetry={healthState.retry} />
      <AttentionCard
        label={dossierReady && dossier.workflow.state === "blocked" ? "风控阻断" : "投资档案"}
        title={dossierReady ? `${dossier.workflow.title}${dossier.workflow.state === "blocked" ? "当前不可继续" : "状态可读"}` : "投资档案不可用"}
        detail={dossierReady ? "已读取真实投资档案；当前阻断与执行门槛分开展示。" : "后端未返回真实 dossier，不展示预览结论。"}
        tone={dossierReady && dossier.workflow.state === "blocked" ? "danger" : "info"}
        href="/investment/wf-001"
        onNavigate={onNavigate}
      />
      <AttentionCard
        label="待办"
        title={firstTodo ? `${todoCount} 项待办` : "当前无待办"}
        detail={firstTodo ? `${formatOwnerCopy(firstTodo.title)} · ${formatDisplayText(firstTodo.detail)}` : "审批和人工事项会在这里合并展示。"}
        tone="warn"
        href="/governance?panel=todos"
        onNavigate={onNavigate}
      />
      <AttentionCard
        label="团队能力"
        title={capabilityChange ? `${formatChangeType(capabilityChange.changeType)}待验证` : "当前无能力变更"}
        detail={capabilityChange ? `只影响${formatEffectiveScope(capabilityChange.effectiveScope)}，当前状态 ${formatStatus(capabilityChange.state)}。` : "治理变更接口未返回待处理能力方案。"}
        tone="info"
        href="/governance?panel=team"
        onNavigate={onNavigate}
      />

      <MetricCard
        icon={<WalletCards />}
        title="纸面账户"
        value={financeState.status === "ready" ? financeSummary.totalLabel : "无法判断"}
        detail={financeState.status === "ready" ? `${financeSummary.categoryCount} 类资产 · ${financeSummary.manualCount} 项需人工确认` : "财务接口未返回真实资产摘要。"}
        tone="jade"
        href="/finance"
        onNavigate={onNavigate}
      />
      <div className="flat-panel">
        <div className="card-head"><strong>风险</strong><span className="badge danger">{riskItems.length || 0} 项</span></div>
        <ul className="business-list">
          {dossierReady ? riskLinks.map((item) => (
            <OverviewListLink detail={item.detail} href={item.href} key={item.title} onNavigate={onNavigate} title={item.title} />
          )) : (
            <OverviewListLink detail="后端未返回真实投资档案。" href="/investment/wf-001" onNavigate={onNavigate} title="投资档案不可用" />
          )}
        </ul>
      </div>
      <div className="flat-panel list-panel">
        <div className="card-head"><strong>每日简报</strong><span className="badge info">研究线索</span></div>
        <ul className="business-list">
          {knowledgeState.data.dailyBrief.length ? knowledgeState.data.dailyBrief.map((item) => (
            <OverviewListLink
              detail={`${item.priority} · 只作为研究线索，不跳过正式投研门槛。`}
              href="/knowledge"
              key={item.title}
              onNavigate={onNavigate}
              title={item.title}
            />
          )) : (
            <OverviewListLink detail="知识接口未返回真实简报。" href="/knowledge" onNavigate={onNavigate} title="暂无每日简报" />
          )}
        </ul>
      </div>
      <MetricCard icon={<AlertTriangle />} title="系统" value={systemHealth.value} detail={systemHealth.detail} tone="indigo" href="/governance?panel=health" onNavigate={onNavigate} />
    </section>
  );
}

function InvestmentQueuePage({ onNavigate }: { onNavigate: Navigate }) {
  const queue = buildInvestmentQueueReadModel();
  return (
    <section className="page-grid queue-grid">
      <h1 className="sr-only">投资</h1>
      <div className="flat-panel list-panel">
        <h3><Landmark size={16} />投研队列</h3>
        {queue.queues.map((item) => (
          <WorkbenchLink className="list-row link-row" href={item.route} key={item.workflowId} onNavigate={onNavigate}>
            <span>{item.title}</span>
            <strong>{item.stage}</strong>
            <em>{formatStatus(item.state)}</em>
          </WorkbenchLink>
        ))}
      </div>
      <MiniList icon={<ShieldAlert />} title="关口摘要" items={queue.guardSummary.map((item) => `${formatGuardLabel(item.label)} · ${formatReason(item.reasonCode)}`)} />
    </section>
  );
}

function InvestmentDossierPage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const dossierState = useInvestmentDossierReadModel(route.params.workflowId ?? "wf-001");
  const dossier = dossierState.data;
  const selectedStage = getSelectedStage(route.query.stage, dossier.workflow.currentStage);
  const [drawerDetail, setDrawerDetail] = useState<DossierDrawerDetail | null>(null);

  useEffect(() => {
    setDrawerDetail(null);
  }, [selectedStage, dossier.workflow.workflowId]);

  if (dossierState.status === "error") {
    return (
      <section className="page-grid dossier-grid">
        <div className="section-header with-actions compact-dossier-header" style={{ maxHeight: 44 }}>
          <h1 className="dossier-status-line">不可用 · IC：S0 接收不可用</h1>
        </div>
        <ReadModelStatusBanner status={dossierState.status} onRetry={dossierState.retry} />
        <div className="flat-panel">
          <h3><AlertTriangle size={16} />投资档案不可用</h3>
          <p className="panel-note">后端没有返回该 workflow 的真实 dossier，页面不展示预览结论或业务阻断原因。</p>
        </div>
      </section>
    );
  }
  return (
    <section
      className={`page-grid dossier-grid ${drawerDetail ? "drawer-open" : ""}`.trim()}
    >
      <div className="section-header with-actions compact-dossier-header" style={{ maxHeight: 44 }}>
        <h1 className="dossier-status-line">{buildDossierStatusLine(dossier)}</h1>
      </div>
      <ReadModelStatusBanner status={dossierState.status} onRetry={dossierState.retry} />
      <div className="stage-rail full-stage-rail">
        {dossier.stageRail.map((stage) => (
          <button
            aria-pressed={stage.stage === selectedStage}
            className={`stage-chip ${stage.nodeStatus} ${stage.stage === selectedStage ? "selected" : ""}`.trim()}
            key={stage.stage}
            onClick={() => {
              setDrawerDetail(null);
              onNavigate(`${route.pathname}?stage=${stage.stage}`);
            }}
            type="button"
          >
            <strong>{stage.stage} {getStageShortTitle(stage.stage)}</strong>
            <span>{formatStatus(stage.nodeStatus)}</span>
          </button>
        ))}
      </div>
      <StageSummaryBoard dossier={dossier} drawerDetail={drawerDetail} selectedStage={selectedStage} onOpenDetail={setDrawerDetail} />
      {drawerDetail ? <DossierDetailDrawer detail={drawerDetail} onClose={() => setDrawerDetail(null)} /> : null}
    </section>
  );
}

function StageSummaryBoard({ dossier, drawerDetail, selectedStage, onOpenDetail }: {
  dossier: InvestmentDossierReadModel;
  drawerDetail: DossierDrawerDetail | null;
  selectedStage: string;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  if (selectedStage !== "S2") {
    return (
      <div className="stage-summary-board stage-reading-frame">
        <StageDirectBoard dossier={dossier} onOpenDetail={onOpenDetail} selectedStage={selectedStage} />
      </div>
    );
  }
  const items = buildStageSummaryItems(dossier, selectedStage);
  if (drawerDetail) {
    return (
      <div className="stage-summary-board stage-reading-frame summary-focus-mode">
        <StageSummaryFocusList
          dossier={dossier}
          drawerDetail={drawerDetail}
          items={items}
          onOpenDetail={onOpenDetail}
          selectedStage={selectedStage}
        />
      </div>
    );
  }
  return (
    <div className="stage-summary-board stage-reading-frame">
      <div className="stage-summary-grid">
        {selectedStage === "S2" && dossier.analystStanceMatrix.length ? (
          <AnalystMatrixSummaryCard dossier={dossier} onOpenDetail={onOpenDetail} />
        ) : null}
        {items.map((item) => (
          <SummaryCard item={item} key={item.key} onOpenDetail={onOpenDetail} />
        ))}
      </div>
    </div>
  );
}

function StageDirectBoard({ dossier, selectedStage, onOpenDetail }: {
  dossier: InvestmentDossierReadModel;
  selectedStage: string;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  switch (selectedStage) {
    case "S0":
      return (
        <div className="direct-info-grid single">
          <StageUnifiedSummaryCard
            onOpenDetail={onOpenDetail}
            panels={[
              {
                title: "收到什么",
                lead: dossier.workflow.title,
                items: [
                  `标的：${formatDossierTarget(dossier.workflow.title)}`,
                  `目标：${dossier.chairBrief.decisionQuestion}`,
                  dossier.chairBrief.noPresetDecisionAttestation ? "边界：只做 A 股投研与纸面链路，不预设结论或买卖动作" : "边界：等待确认不预设结论",
                ],
                detailItems: [{ label: "接收详情", detail: buildStageDetail(dossier, "S0") }],
              },
              {
                title: "处理情况",
                items: [
                  "请求已标准化",
                  "任务边界已确认",
                  "等待 S1 数据准备结果",
                ],
              },
              {
                title: "准备做什么",
                items: [
                  "建立投资任务",
                  "拉取研究与决策核心数据",
                  "交给 CIO 形成会议问题和分析边界",
                ],
              },
            ]}
            title="任务接收"
          />
        </div>
      );
    case "S1": {
      const sourceRows = buildS1DataSourceRows(dossier);
      const statusCards = buildS1StatusCards(dossier, sourceRows);
      const gapRows = buildS1DataGapRows(dossier);
      return (
        <div className="direct-info-grid single s1-compact-grid">
          <DirectInfoPanel
            className="s1-data-readiness-card"
            title="数据准备"
            lead={dossier.dataReadiness.ownerSummary}
          >
            <div className="s1-readiness-dashboard">
              <div aria-label="S1关键判断" className="s1-status-grid">
                {statusCards.map((card) => (
                  <div className={`s1-status-block ${card.tone}`} key={card.label}>
                    <span className="s1-status-icon">
                      {card.tone === "ready" ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                    </span>
                    <div>
                      <span className="s1-status-label">{card.label}</span>
                      <strong>{card.title}</strong>
                      <p>{card.summary}</p>
                    </div>
                  </div>
                ))}
              </div>

              <section aria-label="S1数据来源矩阵" className="s1-source-matrix">
                <div className="s1-section-heading">
                  <h4>来源矩阵</h4>
                  <span>来源 / 用途 / 字段 / 结论</span>
                </div>
                {sourceRows.length ? (
                  <div className="s1-source-table" role="table">
                    <div className="s1-source-table-head" role="row">
                      <span>来源</span>
                      <span>用途</span>
                      <span>字段</span>
                      <span>结论</span>
                    </div>
                    {sourceRows.map((row) => (
                      <div className={`owner-data-source-row ${row.statusTone}`} key={`${row.sourceName}-${row.sourceRef}-${row.statusText}`} role="row">
                        <div className="s1-source-name">
                          <span className={`s1-source-dot ${row.statusTone}`} />
                          <strong>{row.sourceName}</strong>
                        </div>
                        <span className="s1-usage-pill">{row.usageLabel}</span>
                        <div className="s1-field-cell">
                          <span className="s1-field-label">{row.fieldLabel}</span>
                          <span className="s1-field-values">
                            {row.fields.length ? row.fields.map((field) => (
                              <span className="s1-field-chip" key={`${row.sourceName}-${field}`}>{field}</span>
                            )) : <span className="s1-field-empty">无</span>}
                          </span>
                        </div>
                        <em className="s1-status-pill">{row.statusText}</em>
                      </div>
                    ))}
                  </div>
                ) : <p className="s1-empty-note">暂无可展示数据来源。</p>}
              </section>

              <section aria-label="S1数据缺口与下一步" className="s1-impact-chain">
                <div className="s1-section-heading">
                  <h4>缺口影响链</h4>
                  <span>缺口 / 影响阶段 / 下一步</span>
                </div>
                {gapRows.length ? gapRows.map((row) => (
                  <div className="s1-impact-row" key={`${row.gap}-${row.affectsStage}`}>
                    <div>
                      <span>缺口</span>
                      <strong>{row.gap}</strong>
                    </div>
                    <div>
                      <span>影响阶段</span>
                      <strong>{row.affectsStage}</strong>
                      <p>{row.impact}</p>
                    </div>
                    <div>
                      <span>下一步</span>
                      <strong>{row.nextAction}</strong>
                    </div>
                  </div>
                )) : <p className="s1-empty-note">暂无明确数据缺口，下一步影响无需补充。</p>}
              </section>
            </div>
          </DirectInfoPanel>
        </div>
      );
    }
    case "S3":
      return (
        <div className="direct-info-grid s3-overview">
          <section className="direct-info-panel s3-debate-summary full">
            <h3>辩论摘要</h3>
            <p className="direct-lead">{dossier.debate.ownerSummary ?? dossier.debate.cioSynthesis ?? "后端未返回辩论详情"}</p>
            <div className="stage-summary-pair-list s3-debate-facts">
              <SummaryPair detail={buildS3RoundDetail(dossier)} label="轮次" onOpenDetail={onOpenDetail} value={formatS3StatusSummary(dossier)} />
              <SummaryPair detail={buildS3CoreDisputeDetail(dossier)} label="核心分歧" onOpenDetail={onOpenDetail} value={formatS3CoreDisputeSummary(dossier)} />
              <SummaryPair detail={buildS3ViewChangeDetail(dossier)} label="观点变化" onOpenDetail={onOpenDetail} value={formatS3ViewChangeSummary(dossier)} />
              <SummaryPair detail={buildS3RetainedDissentDetail(dossier)} label="保留异议" onOpenDetail={onOpenDetail} value={formatS3RetainedDissentSummary(dossier)} />
              <SummaryPair label="CIO 综合" value={dossier.debate.ownerSummary ?? dossier.debate.cioSynthesis ?? "后端未返回辩论详情"} />
              <SummaryPair label="下一步" value={formatS3NextActionSummary(dossier)} />
            </div>
          </section>
          <section className="direct-info-panel full">
            <h3>分析师要点</h3>
            <div className="s3-analyst-summary-list">
              {dossier.analystStanceMatrix.map((row) => {
                const confidence = Math.round(row.confidence * 100);
                const evidence = Math.round((row.evidenceQuality ?? row.confidence) * 100);
                return (
                  <DetailTriggerRow
                    className="s3-analyst-summary-row"
                    detail={buildS3AnalystDrawerDetail(dossier, row.role)}
                    key={row.role}
                    label={formatRoleName(row.role)}
                    onOpenDetail={onOpenDetail}
                  >
                    <span>{formatRoleName(row.role)}</span>
                    <strong>{formatAnalystDirection(row.direction)} · {confidence}%</strong>
                    <small>证据 {evidence}%</small>
                    <em>{row.hardDissent ? "硬异议保留" : "正常"}</em>
                  </DetailTriggerRow>
                );
              })}
            </div>
          </section>
        </div>
      );
    case "S4":
      return <DirectPanelGrid panels={buildS4DirectPanels(dossier)} summaryTitle="决策形成" onOpenDetail={onOpenDetail} />;
    case "S5":
      return <DirectPanelGrid panels={buildS5DirectPanels(dossier)} summaryTitle="风控复核" onOpenDetail={onOpenDetail} />;
    case "S6":
      return <DirectPanelGrid panels={buildS6DirectPanels(dossier)} summaryTitle="纸面执行" onOpenDetail={onOpenDetail} />;
    case "S7":
      return <DirectPanelGrid panels={buildS7DirectPanels(dossier)} summaryTitle="归因复盘" onOpenDetail={onOpenDetail} />;
    default:
      return (
        <div className="direct-info-grid single">
          <DirectInfoPanel title="阶段信息" lead="暂无可展示内容。" />
        </div>
      );
  }
}

function DirectPanelGrid({ panels, summaryTitle, onOpenDetail }: {
  panels: DirectPanelModel[];
  summaryTitle: string;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  return (
    <div className="direct-info-grid single">
      <StageUnifiedSummaryCard panels={panels} title={summaryTitle} onOpenDetail={onOpenDetail} />
    </div>
  );
}

function StageUnifiedSummaryCard({ title, panels, onOpenDetail }: {
  title: string;
  panels: DirectPanelModel[];
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  return (
    <section className="direct-info-panel stage-unified-summary-card">
      <h3>{title}</h3>
      <div className="stage-summary-section-list">
        {panels.map((panel) => (
          <div className="stage-summary-section stage-summary-section-card" key={panel.title}>
            <h4>{panel.title}</h4>
            {panel.lead ? <p className="direct-lead">{panel.lead}</p> : null}
            {panel.items?.length ? (
              <ul>
                {panel.items.filter(Boolean).map((item) => <li key={`${panel.title}-${item}`}>{item}</li>)}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function SummaryPair({ label, value, detail, onOpenDetail }: {
  label: string;
  value: string;
  detail?: DossierDrawerDetail;
  onOpenDetail?: (detail: DossierDrawerDetail) => void;
}) {
  const content = (
    <>
      <span>{label}：</span>
      <strong>{value}</strong>
    </>
  );
  if (detail && onOpenDetail) {
    return (
      <DetailTriggerRow className="stage-summary-pair" detail={detail} label={label} onOpenDetail={onOpenDetail}>
        {content}
      </DetailTriggerRow>
    );
  }
  return (
    <div className="stage-summary-pair">
      {content}
    </div>
  );
}

function DetailTriggerRow({ className = "", detail, label, onOpenDetail, children }: {
  className?: string;
  detail: DossierDrawerDetail;
  label: string;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
  children: React.ReactNode;
}) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onOpenDetail(detail);
  };
  return (
    <div
      aria-label={`${label}详情`}
      className={`stage-detail-row ${className}`.trim()}
      onClick={() => onOpenDetail(detail)}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
    >
      {children}
    </div>
  );
}

function DirectInfoPanel({ title, lead, items = [], children, className }: {
  title: string;
  lead?: string;
  items?: string[];
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`direct-info-panel ${className ?? ""}`.trim()}>
      <h3>{title}</h3>
      {lead ? <p className="direct-lead">{lead}</p> : null}
      {children}
      {items.length ? (
        <ul>
          {items.filter(Boolean).map((item) => <li key={`${title}-${item}`}>{item}</li>)}
        </ul>
      ) : null}
    </section>
  );
}

function buildS1DataSourceRows(dossier: InvestmentDossierReadModel) {
  const rows = dossier.dataReadiness.sourceStatus ?? [];
  if (!rows.length) {
    return [];
  }
  return rows.map((row) => ({
    sourceName: row.sourceName,
    sourceRef: row.sourceRef,
    requiredUsage: row.requiredUsage,
    usageLabel: formatRequiredUsage(row.requiredUsage),
    fieldLabel: row.obtainedFields.length ? "已取得字段" : "缺失字段",
    fields: row.obtainedFields.length ? row.obtainedFields : row.missingFields,
    statusText: formatS1SourceStatus(row.status, row.qualityLabel),
    statusTone: getS1StatusTone(row.status),
    hasObtainedFields: row.obtainedFields.length > 0,
  }));
}

function buildS1DataGapRows(dossier: InvestmentDossierReadModel) {
  const gaps = dossier.dataReadiness.dataGaps ?? [];
  if (!gaps.length) {
    return [];
  }
  return gaps.map((gap) => ({
    gap: gap.gap,
    affectsStage: gap.affectsStage,
    impact: gap.impact,
    nextAction: gap.nextAction,
  }));
}

function buildS1StatusCards(
  dossier: InvestmentDossierReadModel,
  sourceRows: ReturnType<typeof buildS1DataSourceRows>,
) {
  const decisionRows = sourceRows.filter((row) => row.requiredUsage !== "execution_core");
  const executionRows = sourceRows.filter((row) => row.requiredUsage === "execution_core");
  return [
    {
      label: "研究判断",
      title: formatS1CoreReadiness(dossier.dataReadiness.decisionCoreStatus, "decision"),
      summary: summarizeS1SourceFields(decisionRows, "研究数据来源未提供"),
      tone: getS1CoreTone(dossier.dataReadiness.decisionCoreStatus, decisionRows),
    },
    {
      label: "成交门槛",
      title: formatS1CoreReadiness(dossier.dataReadiness.executionCoreStatus, "execution"),
      summary: summarizeS1SourceFields(executionRows, "成交门槛来源未提供"),
      tone: getS1CoreTone(dossier.dataReadiness.executionCoreStatus, executionRows),
    },
  ];
}

function summarizeS1SourceFields(rows: ReturnType<typeof buildS1DataSourceRows>, emptyText: string) {
  if (!rows.length) {
    return emptyText;
  }
  const fields = Array.from(new Set(rows.flatMap((row) => row.fields))).filter(Boolean);
  const fieldSummary = fields.length ? fields.slice(0, 4).join("、") : "字段状态已返回";
  const suffix = fields.length > 4 ? `等 ${fields.length} 项` : "";
  if (rows.every((row) => row.hasObtainedFields)) {
    return `${fieldSummary}${suffix} 已齐`;
  }
  if (rows.some((row) => row.hasObtainedFields)) {
    return `${fieldSummary}${suffix} 仍需补齐`;
  }
  return `缺 ${fieldSummary}${suffix}`;
}

function formatS1CoreReadiness(status: string, kind: "decision" | "execution") {
  const tone = getS1StatusTone(status);
  if (kind === "execution") {
    if (tone === "ready") return "可进入成交检查";
    if (tone === "warning") return "需复核";
    return "未满足";
  }
  if (tone === "ready") return "可用于研究";
  if (tone === "warning") return "需复核";
  return "未满足";
}

function getS1CoreTone(status: string, rows: ReturnType<typeof buildS1DataSourceRows>) {
  if (rows.some((row) => row.statusTone === "blocked")) {
    return "blocked";
  }
  if (rows.some((row) => row.statusTone === "warning")) {
    return "warning";
  }
  return getS1StatusTone(status);
}

function getS1StatusTone(status: string) {
  if (["available", "pass", "ready", "completed", "ok"].includes(status)) {
    return "ready";
  }
  if (["partial", "conditional_pass", "degraded", "reviewing"].includes(status)) {
    return "warning";
  }
  return "blocked";
}

function formatS1SourceStatus(status: string, qualityLabel: string) {
  const statusText = formatSourceStatus(status) === "缺失" ? "未取得" : formatSourceStatus(status);
  const qualityText = formatDisplayText(qualityLabel).replace(/^缺失[，,、\s]*/, "").trim();
  if (status === "available") {
    return qualityText || "可用于研究判断";
  }
  if (status === "partial") {
    return qualityText ? `${statusText} · ${qualityText}` : statusText;
  }
  if (!qualityText || qualityText === statusText) {
    return statusText;
  }
  return `${statusText} · ${qualityText}`;
}

function formatDossierTarget(title: string) {
  return title.replace(/\s*研究$/, "").trim() || title;
}

function formatSummaryList(items: string[], fallback: string) {
  const visible = items.map(formatDisplayText).filter(Boolean);
  return visible.length ? visible.join("；") : fallback;
}

function buildS4DirectPanels(dossier: InvestmentDossierReadModel): DirectPanelModel[] {
  if (isMajorDecisionDeviation(dossier)) {
    return [
      {
        title: "重大偏离待处理",
        lead: "CIO 判断与组合优化建议差异较大",
        items: [
          `建议：${formatDecisionAction(dossier.cioDecision?.decision ?? "待定")}`,
          dossier.cioDecision?.deviationReason ? `偏离理由：${formatDisplayText(dossier.cioDecision.deviationReason)}` : "CIO 必须说明语义原因",
        ],
        detailItems: [{ label: "偏离说明", detail: buildStageDetail(dossier, "S4") }],
      },
      {
        title: "偏离在哪里",
        items: [
          "单股目标权重偏离 >= 5pp，或组合主动偏离 >= 20%",
          `单股偏离：${formatDecisionDeviation(dossier, "single")}`,
          `组合偏离：${formatDecisionDeviation(dossier, "portfolio")}`,
        ],
        detailItems: [{ label: "优化建议差异", detail: buildStageDetail(dossier, "S4") }],
      },
      {
        title: "下一步",
        items: ["进入老板例外候选，或重开论证"],
      },
    ];
  }

  if (dossier.cioDecision?.decision) {
    return [
      {
        title: "CIO 决策形成",
        lead: `建议：${formatDecisionAction(dossier.cioDecision.decision)}`,
        items: [
          `下一步：进入 S5 风控复核`,
        ],
      },
      {
        title: "为什么这样判断",
        items: [
          `共识：${Math.round(dossier.consensus.score * 100)}%，行动强度：${Math.round(dossier.consensus.actionConviction * 100)}%`,
          dossier.cioDecision.rationale ?? "CIO 已基于分析师观点、共识和风险约束形成收口判断。",
          ...(dossier.cioDecision.conditions?.length ? dossier.cioDecision.conditions.map((item) => `主要约束：${formatDisplayText(item)}`) : ["主要约束：风险预算、价格区间、执行窗口"]),
        ],
        detailItems: [{ label: "决策依据", detail: buildStageDetail(dossier, "S4") }],
      },
      {
        title: "和优化建议是否一致",
        items: [
          `单股偏离：${formatDecisionDeviation(dossier, "single")}，未触发重大偏离`,
          `组合偏离：${formatDecisionDeviation(dossier, "portfolio")}，可进入风控复核`,
        ],
        detailItems: [{ label: "偏离细节", detail: buildStageDetail(dossier, "S4") }],
      },
    ];
  }

  return [
    {
      title: "暂不能形成决策",
      lead: "基本面硬异议仍未解除",
      items: [
        "当前状态：基本面硬异议还没解除",
        `共识 ${Math.round(dossier.consensus.score * 100)}%，行动强度 ${Math.round(dossier.consensus.actionConviction * 100)}%。`,
      ],
    },
    {
      title: "卡点",
      items: [
        "资产质量和息差证据不足",
        "行动强度未达到执行阈值",
        "优化器基准可参考，但不能替代 CIO 结论",
      ],
      detailItems: [{ label: "卡点详情", detail: buildStageDetail(dossier, "S4") }],
    },
    {
      title: "可选去向",
      items: [
        "观察",
        "不行动",
        "重开 S2/S3 补证",
        "下一步：补齐证据后重新收口",
      ],
    },
  ];
}

function buildS5DirectPanels(dossier: InvestmentDossierReadModel): DirectPanelModel[] {
  const review = dossier.riskReview.reviewResult;
  if (review === "approved") {
    return [
      { title: "风控通过", lead: "可进入授权与纸面执行检查", items: ["下一步：进入 S6"] },
      {
        title: "通过依据",
        items: [
          "数据质量满足当前决策用途",
          "仓位、集中度和风险预算未越线",
          "流动性和执行约束可接受",
        ],
        detailItems: [{ label: "风控依据", detail: buildStageDetail(dossier, "S5") }],
      },
      {
        title: "后续影响",
        items: [
          "进入 S6",
          "仍需执行核心数据满足成交门槛",
        ],
      },
    ];
  }

  if (review === "conditional_pass" || dossier.riskReview.ownerExceptionRequired) {
    return [
      { title: "有条件通过", lead: "需要老板确认例外", items: ["下一步：进入审批包，而不是直接执行"] },
      {
        title: "为什么需要确认",
        items: [
          "风险可控但存在条件约束",
          "需要确认影响范围、替代方案和超时后不执行",
        ],
        detailItems: [{ label: "条件约束", detail: buildStageDetail(dossier, "S5") }],
      },
      {
        title: "老板要看的内容",
        items: [
          "推荐处理方式",
          "不同方案的风险与影响",
          "过期后如何处理",
        ],
      },
    ];
  }

  if (dossier.riskReview.repairability === "unrepairable") {
    return [
      { title: "风控拒绝，不可修复", lead: "当前尝试终止" },
      {
        title: "原因",
        items: [
          "关键风险无法通过补证消除",
          "不进入例外审批",
          "不生成执行路径",
        ],
        detailItems: [{ label: "拒绝原因", detail: buildStageDetail(dossier, "S5") }],
      },
      {
        title: "后续",
        items: [
          "关闭本轮尝试",
          "如需继续，只能重新发起新任务或新论证",
        ],
      },
    ];
  }

  return [
    { title: "风控拒绝，可修复", lead: "当前尝试暂停" },
    {
      title: "核心风险",
      items: [
        "硬异议仍未被证据消除",
        "数据质量或组合风险不能支撑放行",
        ...dossier.riskReview.reasonCodes.map(formatReason),
      ],
      detailItems: [{ label: "风险详情", detail: buildStageDetail(dossier, "S5") }],
    },
    {
      title: "修复方向",
      items: [
        "回到指定阶段补证或重开论证",
        "旧产物保留追溯，新产物覆盖后再复核",
      ],
    },
  ];
}

function buildS6DirectPanels(dossier: InvestmentDossierReadModel): DirectPanelModel[] {
  const status = dossier.paperExecution.status;
  if (status === "filled" || status === "partial") {
    return [
      { title: "纸面执行完成", lead: "已按规则模拟成交", items: ["下一步：进入 S7 归因反思"] },
      {
        title: "执行条件",
        items: [
          "风控已通过 / 例外已确认",
          "执行核心数据达标",
          "价格区间命中",
        ],
        detailItems: [{ label: "执行条件", detail: buildS6ExecutionGateDetail(dossier) }],
      },
      {
        title: "成交结果",
        items: [
          `方法：${formatPricingMethod(dossier.paperExecution.pricingMethod)}`,
          `成交：${status === "filled" ? "全部" : "部分"}`,
          `成本：${formatExecutionCost(dossier)}`,
          `T+1：${formatTPlusOneForOwner(dossier.paperExecution.tPlusOne)}`,
        ],
        detailItems: [{ label: "成交详情", detail: buildS6ExecutionGateDetail(dossier) }],
      },
    ];
  }

  if (status === "unfilled" || status === "expired") {
    return [
      { title: "未成交", lead: "条件满足，但价格窗口未命中" },
      {
        title: "发生了什么",
        items: [
          "订单已释放",
          "执行窗口内价格未到达设定区间",
          `结果为 ${formatStatus(status)}`,
        ],
        detailItems: [{ label: "未成交记录", detail: buildS6ExecutionGateDetail(dossier) }],
      },
      {
        title: "影响",
        items: [
          "不产生持仓变化",
          "保留执行记录供归因分析",
          "下一步：由后续监控或 CIO 再判断是否重开",
        ],
      },
    ];
  }

  return [
    { title: "不能执行", lead: "缺少成交所需的核心数据" },
    {
      title: "缺什么",
      items: [
        "分钟级价格 / 成交量",
        "交易日历、停复牌、涨跌停状态",
        "费用与滑点参数",
      ],
      detailItems: [{ label: "数据缺口", detail: buildS6ExecutionGateDetail(dossier) }],
    },
    {
      title: "影响与下一步",
      items: [
        "不生成纸面成交",
        "这是 S6 成交门槛，不是当前 S3 辩论受阻原因",
        "补齐执行核心数据后再判断",
      ],
    },
  ];
}

function buildS7DirectPanels(dossier: InvestmentDossierReadModel): DirectPanelModel[] {
  if (dossier.attribution.needsCfoInterpretation || (dossier.attribution.improvementItems?.length ?? 0) > 0) {
    return [
      { title: "需要反思", lead: "命中改进触发条件", items: ["生效边界：只对新任务或新尝试生效"] },
      {
        title: "触发原因",
        items: [
          "风控拒绝 / 执行核心阻断 / 数据冲突",
          "某一质量维度低于阈值",
          "关键条件命中或失效",
          ...(dossier.attribution.improvementItems ?? []).map(formatDisplayText),
        ],
        detailItems: [{ label: "触发证据", detail: buildStageDetail(dossier, "S7") }],
      },
      {
        title: "输出",
        items: [
          "CFO 解释",
          "责任角色反思",
          "知识、Prompt、Skill 或规则改进提案",
          "只对新任务或新尝试生效",
        ],
      },
    ];
  }

  if (hasAttributionSample(dossier)) {
    return [
      { title: "归因已生成", lead: "本轮结果已进入复盘", items: ["正常：自动发布归因", "异常：触发 CFO 解释或反思任务"] },
      {
        title: "看什么",
        items: [
          "收益、风险、成本、滑点",
          "决策质量、执行质量、风控质量",
          "数据质量、证据质量、条件是否命中",
        ],
        detailItems: [{ label: "归因维度", detail: buildStageDetail(dossier, "S7") }],
      },
      {
        title: "发现什么",
        items: [
          "哪些判断有效",
          "哪些条件失效",
          "哪些角色或服务需要改进",
          ...buildAttributionScoreItems(dossier),
        ],
      },
    ];
  }

  return [
    {
      title: "暂未归因",
      lead: "没有可复盘的执行结果",
      items: [
        "当前还没有纸面成交或持仓变化",
        "不能用未发生的执行倒推角色质量",
      ],
    },
    {
      title: "已保留",
      items: [
        "决策、分歧、风控和执行阻断记录",
        "后续若发生执行，会进入自动归因",
      ],
    },
    {
      title: "下一步",
      items: ["等待执行样本或周期复盘窗口"],
    },
  ];
}

function isMajorDecisionDeviation(dossier: InvestmentDossierReadModel) {
  return dossier.decisionGuard?.majorDeviation === true
    || parseDeviationNumber(dossier.decisionGuard?.singleNameDeviationPp ?? dossier.optimizerDeviation.singleNameDeviation) >= 5
    || parseDeviationNumber(dossier.decisionGuard?.portfolioActiveDeviation ?? dossier.optimizerDeviation.portfolioDeviation) >= 20;
}

function parseDeviationNumber(value: number | string | undefined) {
  if (typeof value === "number") {
    return value <= 1 ? value * 100 : value;
  }
  if (!value) return 0;
  const match = value.match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function formatDecisionAction(value: string) {
  const labels: Record<string, string> = {
    buy: "买入",
    sell: "卖出",
    hold: "持有",
    observe: "观察",
    no_action: "不行动",
    reopen: "重开论证",
    reduce: "降低仓位",
    increase: "提高仓位",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatDecisionDeviation(dossier: InvestmentDossierReadModel, kind: "single" | "portfolio") {
  const directValue = kind === "single"
    ? dossier.decisionGuard?.singleNameDeviationPp
    : dossier.decisionGuard?.portfolioActiveDeviation;
  if (directValue !== undefined) {
    return formatDeviationValue(directValue, kind);
  }
  return kind === "single" ? dossier.optimizerDeviation.singleNameDeviation : dossier.optimizerDeviation.portfolioDeviation;
}

function formatDeviationValue(value: number | string, kind: "single" | "portfolio") {
  if (typeof value === "string") {
    return formatDisplayText(value);
  }
  const normalized = value <= 1 ? value * 100 : value;
  const rounded = Number.isInteger(normalized) ? normalized.toFixed(0) : normalized.toFixed(1);
  return `${rounded}${kind === "single" ? "pp" : "%"}`;
}

function formatExecutionCost(dossier: InvestmentDossierReadModel) {
  return [
    dossier.paperExecution.fees ? dossier.paperExecution.fees : "",
    dossier.paperExecution.taxes ? dossier.paperExecution.taxes : "",
    dossier.paperExecution.slippage ? `滑点 ${dossier.paperExecution.slippage}` : "",
  ].filter(Boolean).join(" · ") || "未产生";
}

function formatTPlusOneForOwner(value: string) {
  if (value === "locked_until_next_trading_day" || value === "available_next_trading_day") {
    return "资金或持仓次日可用";
  }
  return formatStatus(value);
}

function hasAttributionSample(dossier: InvestmentDossierReadModel) {
  if (dossier.attribution.links.length > 0) return true;
  if (dossier.attribution.summary && !dossier.attribution.summary.includes("暂无归因")) return true;
  return [
    dossier.attribution.decisionQuality,
    dossier.attribution.executionQuality,
    dossier.attribution.riskQuality,
    dossier.attribution.dataQuality,
    dossier.attribution.evidenceQuality,
  ].some((value) => typeof value === "number");
}

function buildAttributionScoreItems(dossier: InvestmentDossierReadModel) {
  const scores = [
    ["决策质量", dossier.attribution.decisionQuality],
    ["执行质量", dossier.attribution.executionQuality],
    ["风控质量", dossier.attribution.riskQuality],
    ["数据质量", dossier.attribution.dataQuality],
    ["证据质量", dossier.attribution.evidenceQuality],
  ] as const;
  return scores
    .filter(([, value]) => typeof value === "number")
    .map(([label, value]) => `${label}：${Math.round((value ?? 0) * 100)}%`);
}

function formatRequiredUsage(usage: string) {
  const labels: Record<string, string> = {
    research: "研究",
    decision_core: "研究/决策核心",
    execution_core: "成交门槛",
    display: "展示",
    finance_planning: "财务规划",
  };
  return labels[usage] ?? formatDisplayText(usage);
}

function formatSourceStatus(status: string) {
  const labels: Record<string, string> = {
    available: "已获取",
    partial: "部分获取",
    failed: "采集失败",
    missing: "缺失",
  };
  return labels[status] ?? formatDisplayText(status);
}

function StageSummaryFocusList({ dossier, drawerDetail, items, selectedStage, onOpenDetail }: {
  dossier: InvestmentDossierReadModel;
  drawerDetail: DossierDrawerDetail;
  items: StageSummaryItem[];
  selectedStage: string;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  const matrixDetail = buildAnalystMatrixDrawerDetail(dossier);
  return (
    <div className="summary-focus-list">
      {selectedStage === "S2" && dossier.analystStanceMatrix.length ? (
        <div className="summary-focus-group">
          <DetailTriggerRow
            className={`summary-focus-item ${drawerDetail.title === matrixDetail.title ? "is-active" : ""}`.trim()}
            detail={matrixDetail}
            label="分析师立场矩阵"
            onOpenDetail={onOpenDetail}
          >
            <span>分析师立场矩阵</span>
            <strong>{buildAnalystMatrixBadge(dossier)}</strong>
            <small>方向、置信、证据、产物和异议状态</small>
          </DetailTriggerRow>
          <div className="summary-focus-analysts">
            {dossier.analystStanceMatrix.map((row) => {
              const title = formatRoleName(row.role);
              return (
                <DetailTriggerRow
                  className={`summary-focus-item summary-focus-analyst-row ${drawerDetail.title === title ? "is-active" : ""}`.trim()}
                  detail={buildAnalystDrawerDetail(dossier, row.role)}
                  key={row.role}
                  label={title}
                  onOpenDetail={onOpenDetail}
                >
                  <span>{title}</span>
                  <strong>{formatAnalystDirection(row.direction)} · {Math.round(row.confidence * 100)}%</strong>
                  <small>{Math.round((row.evidenceQuality ?? row.confidence) * 100)}% 证据 · {row.hardDissent ? "硬异议" : "正常"}</small>
                </DetailTriggerRow>
              );
            })}
          </div>
        </div>
      ) : null}
      {items.map((item) => (
        <React.Fragment key={item.key}>
          <DetailTriggerRow
            className={`summary-focus-item ${drawerDetail.title === item.detail.title ? "is-active" : ""}`.trim()}
            detail={item.detail}
            label={item.title}
            onOpenDetail={onOpenDetail}
          >
            <span>{item.title}</span>
            <strong>{item.value}</strong>
            {item.lines[0] ? <small>{item.lines[0]}</small> : null}
          </DetailTriggerRow>
          {item.detailItems?.length ? (
            <div className="summary-focus-detail-list">
              {item.detailItems.map((detailItem) => (
                <DetailTriggerRow
                  className={`summary-focus-item summary-focus-detail-row ${drawerDetail.title === detailItem.detail.title ? "is-active" : ""}`.trim()}
                  detail={detailItem.detail}
                  key={`${item.key}-${detailItem.label}`}
                  label={detailItem.label}
                  onOpenDetail={onOpenDetail}
                >
                  <span>{detailItem.label}</span>
                </DetailTriggerRow>
              ))}
            </div>
          ) : null}
        </React.Fragment>
      ))}
    </div>
  );
}

function AnalystMatrixSummaryCard({ dossier, onOpenDetail }: {
  dossier: InvestmentDossierReadModel;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  const rolesWithPayload = new Set(dossier.rolePayloadDrilldowns.map((item) => item.role));
  return (
    <div className="summary-card analyst-matrix-card quiet-matrix summary-span-12">
      <div className="summary-card-heading">
        <span>分析师立场矩阵</span>
        <strong>{buildAnalystMatrixBadge(dossier)}</strong>
      </div>
      <div className="analyst-stance-list compact-analyst-list">
        <div className="analyst-matrix-header">
          <span>角色</span>
          <span>方向</span>
          <span>置信</span>
          <span>证据</span>
          <span>产物</span>
          <span>状态</span>
        </div>
        {dossier.analystStanceMatrix.map((row) => (
          <DetailTriggerRow
            className="matrix-row analyst-row"
            detail={buildAnalystDrawerDetail(dossier, row.role)}
            key={row.role}
            label={formatRoleName(row.role)}
            onOpenDetail={onOpenDetail}
          >
            <span>{formatRoleName(row.role)}</span>
            <strong>{formatAnalystDirection(row.direction)}</strong>
            <small>{Math.round(row.confidence * 100)}%</small>
            <small>{Math.round((row.evidenceQuality ?? row.confidence) * 100)}%</small>
            <small>{rolesWithPayload.has(row.role) ? "已交" : "待补"}</small>
            {row.hardDissent ? <em>硬异议</em> : <i>正常</i>}
          </DetailTriggerRow>
        ))}
      </div>
    </div>
  );
}

function SummaryCard({ item, onOpenDetail }: {
  item: StageSummaryItem;
  onOpenDetail: (detail: DossierDrawerDetail) => void;
}) {
  if (item.detailItems?.length) {
    return (
      <section className={`summary-card summary-span-${item.span ?? 4}`}>
        <div className="summary-card-heading">
          <span>{item.title}</span>
          {item.badge ? <em>{item.badge}</em> : null}
        </div>
        <strong>{item.value}</strong>
        <ul className="s2-conclusion-list">
          {item.detailItems.map((detailItem) => (
            <li key={`${item.key}-${detailItem.label}`}>
              <DetailTriggerRow
                className="summary-line-row"
                detail={detailItem.detail}
                label={detailItem.label}
                onOpenDetail={onOpenDetail}
              >
                {detailItem.label}
              </DetailTriggerRow>
            </li>
          ))}
        </ul>
      </section>
    );
  }

  return (
    <DetailTriggerRow
      className={`summary-card summary-span-${item.span ?? 4}`}
      detail={item.detail}
      label={item.title}
      onOpenDetail={onOpenDetail}
    >
      <div className="summary-card-heading">
        <span>{item.title}</span>
        {item.badge ? <em>{item.badge}</em> : null}
      </div>
      <strong>{item.value}</strong>
      {item.facts?.length ? (
        <div className="summary-fact-list">
          {item.facts.map((fact) => (
            <div className="summary-fact-row" key={`${item.key}-${fact.label}`}>
              <span>{fact.label}</span>
              <strong>{fact.value}</strong>
            </div>
          ))}
        </div>
      ) : item.lines.length ? (
        <ul>
          {item.lines.map((line) => <li key={`${item.key}-${line}`}>{line}</li>)}
        </ul>
      ) : null}
    </DetailTriggerRow>
  );
}

function DossierDetailDrawer({ detail, onClose }: { detail: DossierDrawerDetail; onClose: () => void }) {
  return (
    <aside className="dossier-detail-drawer dossier-detail-sheet">
      <div className="drawer-header">
        <div>
          <span>详情</span>
          <h3>{detail.title}</h3>
          <p>{detail.subtitle}</p>
        </div>
        <button className="ghost-button drawer-close" onClick={onClose} type="button">关闭</button>
      </div>
      {detail.blocks.map((block) => (
        <DetailBlock key={block.title} title={block.title} items={block.items} />
      ))}
    </aside>
  );
}

function DossierBusinessPanels({ dossier }: { dossier: InvestmentDossierReadModel }) {
  return (
    <div className="dossier-side-panels">
      <MiniList
        icon={<ShieldAlert />}
        title="数据与证据"
        items={[
          `数据就绪：${formatStatus(dossier.dataReadiness.qualityBand)}`,
          `决策核心 ${formatStatus(dossier.dataReadiness.decisionCoreStatus)}`,
          `执行核心 ${formatStatus(dossier.dataReadiness.executionCoreStatus)}`,
          ...dossier.dataReadiness.issues,
        ]}
      />
      <MiniList
        icon={<ShieldAlert />}
        title="风控与禁用"
        items={buildDossierRiskReviewItems(dossier)}
      />
      <MiniList
        icon={<WalletCards />}
        title="执行门槛"
        items={buildExecutionGateItems(dossier)}
      />
      <MetricCard
        icon={<CheckCircle2 />}
        title="共识与行动强度"
        value={`${Math.round(dossier.consensus.score * 100)}% / ${Math.round(dossier.consensus.actionConviction * 100)}%`}
        detail={dossier.consensus.thresholdLabel}
        tone="jade"
      />
      <MiniList
        icon={<FileSearch />}
        title="优化偏离"
        items={[
          `单股偏离 ${dossier.optimizerDeviation.singleNameDeviation}`,
          `组合偏离 ${dossier.optimizerDeviation.portfolioDeviation}`,
          dossier.optimizerDeviation.recommendation,
        ]}
      />
      <MiniList
        icon={<Brain />}
        title="后续回链"
        items={[dossier.attribution.summary, ...dossier.attribution.links]}
      />
    </div>
  );
}

function IcStageCard({ dossier, selectedRole, showAnalystStance, onSelect }: {
  dossier: InvestmentDossierReadModel;
  selectedRole: string | null;
  showAnalystStance: boolean;
  onSelect: (role: string) => void;
}) {
  return (
    <div className="flat-panel ic-stage-card">
      <div className="ic-stage-card-header">
        <h3><GitBranch size={16} />IC 工作阶段</h3>
        <strong>IC 工作阶段：{dossier.workflow.currentStage} {getStageShortTitle(dossier.workflow.currentStage)} · {formatWorkflowStageState(dossier.workflow.state)}</strong>
      </div>
      <div className="ic-stage-card-body">
        <ul className="business-list compact-list ic-stage-signals">
          {buildCurrentIcStageItems(dossier).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {showAnalystStance ? (
          <div className="ic-analyst-block">
            <h4>分析师立场</h4>
            <div className="analyst-stance-list compact-analyst-list">
              {dossier.analystStanceMatrix.map((row) => {
                const pressed = selectedRole === row.role;
                return (
                  <button
                    aria-pressed={pressed}
                    className={`matrix-row analyst-row ${pressed ? "selected" : ""}`.trim()}
                    key={row.role}
                    onClick={() => onSelect(row.role)}
                    type="button"
                  >
                    <span>{formatRoleName(row.role)}</span>
                    <strong>{formatAnalystDirection(row.direction)}</strong>
                    <small>{Math.round(row.confidence * 100)}%</small>
                    {row.hardDissent ? <em>硬异议</em> : <i>正常</i>}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function CurrentDetailPanel({ dossier, selectedStage, selectedAnalystRole }: {
  dossier: InvestmentDossierReadModel;
  selectedStage: string;
  selectedAnalystRole: string | null;
}) {
  const analyst = selectedAnalystRole ? buildAnalystDetail(dossier, selectedAnalystRole) : null;
  if (analyst && isAnalystStage(selectedStage)) {
    return (
      <div className="flat-panel current-detail-panel">
        <h3><FileSearch size={16} />当前详情</h3>
        <div className="detail-kicker">
          <strong>{analyst.roleLabel}</strong>
          <span>{analyst.stanceLabel}</span>
        </div>
        <DetailBlock title="核心判断" items={[analyst.thesis]} />
        <DetailBlock title="主要依据" items={analyst.evidenceItems} />
        <DetailBlock title="反证与风险" items={analyst.riskItems} />
        <DetailBlock title="成立条件" items={analyst.applicableConditions} />
        <DetailBlock title="失效条件" items={analyst.invalidationConditions} />
        <DetailBlock title="建议动作" items={analyst.actionItems} />
      </div>
    );
  }

  const detail = buildStageDetail(dossier, selectedStage);
  return (
    <div className="flat-panel current-detail-panel">
      <h3><FileSearch size={16} />当前详情</h3>
      <div className="detail-kicker">
        <strong>{detail.title}</strong>
        <span>{detail.subtitle}</span>
      </div>
      {detail.blocks.map((block) => (
        <DetailBlock key={block.title} title={block.title} items={block.items} />
      ))}
    </div>
  );
}

function DetailBlock({ title, items }: { title: string; items: string[] }) {
  const visible = items.filter(Boolean);
  if (!visible.length) return null;
  return (
    <div className="detail-block">
      <span>{title}</span>
      <ul>
        {visible.map((item, index) => <li key={`${title}-${index}-${item}`}>{item}</li>)}
      </ul>
    </div>
  );
}

function TraceDebugPage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const traceState = useTraceDebugReadModel(route.params.workflowId ?? "wf-001");
  const trace = traceState.data;
  const returnHref = route.query.returnTo ?? "/investment/wf-001";
  const returnLabel = getTraceReturnLabel(returnHref);
  return (
    <section className="page-grid trace-grid">
      <div className="section-header with-actions">
        <div>
          <h1>流程审计</h1>
          <p>协作过程与证据追溯</p>
        </div>
        <WorkbenchLink className="inline-action" href={returnHref} onNavigate={onNavigate}>{returnLabel}</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={traceState.status} onRetry={traceState.retry} />
      <MiniList icon={<Bot />} title="协作过程" items={traceItemsOrEmpty(trace.agentRunTree.map(formatTraceRunSummary))} />
      <MiniList icon={<GitBranch />} title="协作命令" items={traceItemsOrEmpty(trace.commands.map((command) => `${formatCommandType(command.commandType)} · ${formatStatus(command.admission)} · ${formatReason(command.reasonCode)}`))} />
      <MiniList icon={<FileSearch />} title="协作事件" items={traceItemsOrEmpty(trace.events.map((event) => `${formatEventType(event.eventType)} · ${formatDisplayText(event.summary)}`))} />
      <MiniList icon={<LockKeyhole />} title="上下文使用" items={traceItemsOrEmpty(trace.contextInjectionRecords.map((record) => `${formatStatus(record.redactionStatus)} · ${formatContextReason(record.whyIncluded)}`))} />
      <MiniList icon={<Layers3 />} title="交接记录" items={traceItemsOrEmpty(trace.handoffs.map((handoff) => `${formatRoleName(handoff.from)} -> ${formatRoleName(handoff.to)} · ${handoff.blockers.map(formatDisplayText).join("/")}`))} />
    </section>
  );
}

function traceItemsOrEmpty(items: string[]) {
  return items.length ? items : ["暂无真实过程记录"];
}

function FinancePage({ route }: { route: ResolvedWorkbenchRoute }) {
  const financeState = useFinanceOverviewReadModel();
  const finance = financeState.data;
  const activeTodoId = route.query.todo;
  const assetSummary = summarizeFinanceAssets(finance.assets);
  const [assetType, setAssetType] = useState(activeTodoId ? "real_estate" : "cash");
  const [assetAmount, setAssetAmount] = useState(activeTodoId ? "3000000" : "1000000");
  const [valuationDate, setValuationDate] = useState("2026-05-06");
  const [source, setSource] = useState(activeTodoId ? "人工待办资料" : "owner_ui");
  const [assetUpdateStatus, setAssetUpdateStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const [updatedAssetId, setUpdatedAssetId] = useState<string | null>(null);
  return (
    <section className="page-grid finance-grid">
      <h1 className="sr-only">财务</h1>
      <ReadModelStatusBanner status={financeState.status} onRetry={financeState.retry} />
      <MetricCard
        icon={<WalletCards />}
        title="资产摘要"
        value={assetSummary.totalLabel}
        detail={`${assetSummary.categoryCount} 类资产 · ${assetSummary.manualCount} 项需人工确认`}
        tone="jade"
      />
      <MetricCard icon={<ShieldAlert />} title="风险预算" value={formatBudgetRef(finance.health.riskBudget)} detail={`流动性 ${finance.health.liquidity} · 压力 ${formatDisplayText(finance.health.stress)}`} tone="gold" />
      <MiniList icon={<WalletCards />} title="聚合资产" items={assetSummary.lines} />
      <MiniList icon={<AlertTriangle />} title="待确认事项" items={finance.reminders.map(formatReminder)} />
      <div className="flat-panel finance-form-panel">
        <h3><WalletCards size={16} />财务档案办理</h3>
        {activeTodoId ? <p className="panel-note">正在办理：{activeTodoId} · 提交走财务档案写入，不关闭通用任务状态</p> : null}
        <div className="finance-form">
          <label>
            <span>资产类型</span>
            <select
              aria-label="资产类型"
              value={assetType}
              onChange={(event) => setAssetType(event.target.value)}
            >
              <option value="cash">现金</option>
              <option value="fund">基金</option>
              <option value="gold">黄金</option>
              <option value="real_estate">房产</option>
              <option value="liability">负债</option>
              <option value="other">其他</option>
            </select>
          </label>
          <label>
            <span>估值金额</span>
            <input aria-label="估值金额" value={assetAmount} onChange={(event) => setAssetAmount(event.target.value)} />
          </label>
          <label>
            <span>估值日期</span>
            <input aria-label="估值日期" value={valuationDate} onChange={(event) => setValuationDate(event.target.value)} />
          </label>
          <label>
            <span>资料来源</span>
            <input aria-label="资料来源" value={source} onChange={(event) => setSource(event.target.value)} />
          </label>
        </div>
        <button
          className="inline-action"
          disabled={assetUpdateStatus === "submitting"}
          onClick={() => {
            setAssetUpdateStatus("submitting");
            updateFinanceAsset({
              assetId: activeTodoId ? `finance-${activeTodoId}` : `${assetType}-owner-ui`,
              assetType: assetType as "a_share" | "fund" | "gold" | "real_estate" | "cash" | "liability" | "other",
              amount: Number(assetAmount),
              valuationDate,
              source,
            })
              .then((payload) => {
                setUpdatedAssetId(payload.assetId);
                setAssetUpdateStatus("done");
              })
              .catch(() => setAssetUpdateStatus("failed"));
          }}
          type="button"
        >
          {assetUpdateStatus === "submitting" ? "正在提交..." : "提交财务档案"}
        </button>
        {assetUpdateStatus === "done" ? (
          <p className="panel-note">财务档案已更新 {updatedAssetId} · 不触发审批、执行或交易链路</p>
        ) : assetUpdateStatus === "failed" ? (
          <p className="panel-note danger">API 未连接，财务档案未写入；启动后端后可重试。</p>
        ) : (
          <p className="panel-note">提交只影响财务档案和财务规划，不触发审批、执行或交易链路。</p>
        )}
      </div>
    </section>
  );
}

function GovernanceHealthPanel() {
  const healthState = useDevOpsHealthReadModel();
  const health = healthState.data;
  return (
    <div className="flat-panel list-panel" data-panel="health">
      <h3><AlertTriangle size={16} />健康</h3>
      <ReadModelStatusBanner status={healthState.status} onRetry={healthState.retry} />
      <ul>
        {health.routineChecks.map((check) => (
          <li key={check.checkId}>{formatHealthCheck(check.checkId)} · {formatStatus(check.status)}</li>
        ))}
        {health.incidents.map((incident) => (
          <li key={incident.incidentId}>{formatIncidentType(incident.incidentType)}异常 · {formatStatus(incident.status)} · 需要确认影响范围</li>
        ))}
        {health.recovery.map((plan) => (
          <li key={plan.planId}>恢复计划 · {plan.investmentResumeAllowed ? "投资恢复已放行" : "投资恢复未放行"}</li>
        ))}
      </ul>
    </div>
  );
}

function KnowledgePage({ onNavigate }: { onNavigate: Navigate }) {
  const knowledgeState = useKnowledgeReadModel();
  const knowledge = knowledgeState.data;
  const [captureStatus, setCaptureStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const defaultMemoryDraft = "记录需要复核的研究经验、来源和适用边界。";
  const memoryDraftRef = useRef<HTMLTextAreaElement>(null);
  const [organizeStatus, setOrganizeStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const firstSuggestion = knowledge.organizeSuggestions[0];
  const suggestionMemoryId = firstSuggestion?.targetMemoryRefs[0] ?? knowledge.memoryResults[0]?.memoryId ?? "memory";
  const suggestionVersionId = knowledge.memoryResults.find((item) => item.memoryId === suggestionMemoryId)?.currentVersionId
    ?? knowledge.memoryResults[0]?.currentVersionId
    ?? "memory-version";
  const ownerVisibleMemories = getOwnerVisibleMemories(knowledge.memoryResults);
  return (
    <section className="page-grid knowledge-grid">
      <h1 className="sr-only">知识</h1>
      <ReadModelStatusBanner status={knowledgeState.status} onRetry={knowledgeState.retry} />
      <MiniList icon={<Brain />} title="每日简报" items={knowledge.dailyBrief.flatMap((item) => [
        `${item.title}，${item.supportingEvidenceOnly ? "先作为研究线索处理。" : "可进入正式资料复核。"}`,
        item.supportingEvidenceOnly ? "先复核来源质量，再决定是否进入候选议题。" : "进入正式复核后再提出候选议题。",
      ]).concat(knowledge.dailyBrief.length ? [] : ["暂无每日简报。"])} />
      <div className="flat-panel research-package-panel">
        <h3><FileSearch size={16} />研究资料包</h3>
        {knowledge.researchPackages.length ? knowledge.researchPackages.map((item) => (
          <div className="research-package-item" key={item.packageId}>
            <strong>{item.title} · {formatStatus(item.status)} · 证据 {item.evidenceRefs.length} 条</strong>
            <p>资料包来源：{formatEvidenceSourceList(item.evidenceRefs)}</p>
            <p>重点：先复核来源质量，再决定是否进入候选议题。</p>
          </div>
        )) : <p className="panel-note">暂无可复核资料包。资料包必须由后端研究产物提供来源和证据后才会显示。</p>}
      </div>
      <MiniList icon={<Brain />} title="经验库" items={buildExperienceLibrarySummary(knowledge)} />
      <div className="flat-panel">
        <h3><Layers3 size={16} />经验记录</h3>
        <p className="panel-note">保存一条可复核经验。保存后进入经验记录，不会直接改默认上下文。</p>
        <textarea
          aria-label="经验内容"
          className="knowledge-note-input"
          defaultValue={defaultMemoryDraft}
          ref={memoryDraftRef}
        />
        <button
          className="inline-action"
          disabled={captureStatus === "submitting"}
          onClick={() => {
            setCaptureStatus("submitting");
            createMemoryItem(memoryDraftRef.current?.value ?? defaultMemoryDraft)
              .then((payload) => {
                void payload;
                setCaptureStatus("done");
              })
              .catch(() => setCaptureStatus("failed"));
          }}
          type="button"
        >
          {captureStatus === "submitting" ? "正在保存..." : "保存经验"}
        </button>
        {captureStatus === "done" ? (
          <p className="panel-note">经验已保存，可在经验记录里复核。</p>
        ) : captureStatus === "failed" ? (
          <p className="panel-note danger">经验保存失败，请重试。</p>
        ) : null}
        <ul>
          {ownerVisibleMemories.length ? ownerVisibleMemories.map((item) => (
            <li key={item.memoryId}>
              {formatMemoryTitle(item.title)} · {formatStatus(item.promotionState)} · {item.tags.map(formatDisplayText).join(" / ") || "待补标签"}
            </li>
          )) : <li>待整理资料 · {knowledge.memoryResults.length} 条 · 已隐藏内部命名和测试材料</li>}
        </ul>
      </div>
      <MiniList
        icon={<GitBranch />}
        title="资料关系"
        items={summarizeKnowledgeRelations(knowledge.relationGraph)}
      />
      <div className="flat-panel organize-panel">
        <h3><ClipboardCheck size={16} />整理建议</h3>
        <p className="panel-note">把经验记录归类到资料包和标签，后续检索更准；不会改变业务事实或默认上下文。</p>
        <ul>
          {knowledge.organizeSuggestions.length ? knowledge.organizeSuggestions.map((item) => (
            <li key={item.suggestionId}>
              {formatOrganizeSuggestion(item)}
            </li>
          )) : <li>暂无可应用整理建议。需要后端给出明确目标、来源和理由后才允许应用。</li>}
        </ul>
        <button
          className="inline-action"
          disabled={!firstSuggestion || organizeStatus === "submitting"}
          onClick={() => {
            if (!firstSuggestion) {
              return;
            }
            setOrganizeStatus("submitting");
            applyMemoryOrganizeSuggestion(suggestionMemoryId, suggestionVersionId, firstSuggestion.suggestedTags)
              .then((payload) => {
                void payload;
                setOrganizeStatus("done");
              })
              .catch(() => setOrganizeStatus("failed"));
          }}
          type="button"
        >
          {organizeStatus === "submitting" ? "正在应用..." : "应用整理建议"}
        </button>
        {organizeStatus === "done" ? (
          <p className="panel-note">整理建议已应用。</p>
        ) : organizeStatus === "failed" ? (
          <p className="panel-note danger">整理建议应用失败，请重试。</p>
        ) : firstSuggestion ? (
          <p className="panel-note">点击后只追加标签和关系，旧经验版本不会被覆盖。</p>
        ) : (
          <p className="panel-note">当前没有后端建议，按钮保持不可用。</p>
        )}
      </div>
      <div className="flat-panel">
        <h3><LockKeyhole size={16} />上下文使用记录</h3>
        <ul>
          <li>已纳入背景资料 {knowledge.contextInjectionInspector.filter((item) => item.redactionStatus !== "denied").length} 条 · 仅作为上下文</li>
          <li>已拒绝敏感资料 {knowledge.contextInjectionInspector.reduce((count, item) => count + item.deniedRefs.length, 0)} 条 · 不进入默认视图</li>
        </ul>
      </div>
    </section>
  );
}

function GovernancePage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const governanceState = useGovernanceReadModel();
  const governance = governanceState.data;
  const teamState = useTeamReadModel({ silentFallback: true });
  const team = teamState.data;
  const selectedPanel = getGovernancePanel(route.query);
  const taskById = new Map(governance.taskCenter.map((task) => [task.taskId, task]));
  return (
    <section className="page-grid governance-grid">
      <div className="section-header">
        <h1 className="sr-only">治理</h1>
        <div className="module-tabs">
          {getGovernanceModules().map((module) => (
            <WorkbenchLink
              active={module.panel === selectedPanel}
              href={module.href}
              key={module.panel}
              onNavigate={onNavigate}
            >
              {module.label}
            </WorkbenchLink>
          ))}
        </div>
      </div>
      <ReadModelStatusBanner status={governanceState.status} onRetry={governanceState.retry} />
      {selectedPanel === "team" ? <ReadModelStatusBanner status={teamState.status} onRetry={teamState.retry} /> : null}
      {selectedPanel === "todos" ? (
        <div className="flat-panel list-panel" data-panel="todos">
          <h3><Layers3 size={16} />待办</h3>
          <div className="task-card-list">
            {governance.unifiedTodos.map((todo) => (
              <TodoCenterCard
                key={todo.todoId}
                todo={todo}
                task={taskById.get(todo.sourceId)}
                onNavigate={onNavigate}
              />
            ))}
            {!governance.unifiedTodos.length ? <p className="panel-note">当前没有需要处理的待办。</p> : null}
          </div>
        </div>
      ) : null}
      {selectedPanel === "team" ? (
        <div className="flat-panel list-panel" data-panel="team">
          <h3><Bot size={16} />团队</h3>
          <div className="team-card-list">
            {team.agentCards.map((agent) => (
              <WorkbenchLink className="mini-team-card" href={`/governance/team/${agent.agentId}`} key={agent.agentId} onNavigate={onNavigate}>
                <strong>{formatTeamDisplayName(agent.displayName)}</strong>
                <span>胜任度 {Math.round(agent.recentQualityScore * 100)}%</span>
                <em>{agent.weaknessTags.length ? `短板：${agent.weaknessTags.join("、")}` : "暂无突出短板"}</em>
              </WorkbenchLink>
            ))}
          </div>
        </div>
      ) : null}
      {selectedPanel === "changes" ? (
        <div className="flat-panel list-panel" data-panel="changes">
          <h3><GitBranch size={16} />变更</h3>
          {route.query.change === "default-context" ? <p className="panel-note">当前提案：默认上下文提案 · 只对后续任务生效</p> : null}
          <ul>
            {governance.governanceChanges.map((change) => (
              <li key={change.changeId}>
                {formatChangeType(change.changeType)}
                {" · "}
                {formatStatus(change.impactLevel)}
                {" · "}
                {formatStatus(change.state)}
                {" · "}
                只影响{formatEffectiveScope(change.effectiveScope)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {selectedPanel === "health" ? (
        <GovernanceHealthPanel />
      ) : null}
      {selectedPanel === "audit" ? (
        <div className="flat-panel list-panel" data-panel="audit">
          <h3><FileSearch size={16} />审计</h3>
          <ul>
            <li>投资流程审计 · 硬异议已交接风控</li>
            <li>重开记录 · 保留证据只读展示</li>
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function AgentTeamPage({ onNavigate }: { onNavigate: Navigate }) {
  const teamState = useTeamReadModel({ silentFallback: true });
  const team = teamState.data;
  return (
    <section className="page-grid team-grid">
      <div className="section-header">
        <h1>团队</h1>
      </div>
      <ReadModelStatusBanner status={teamState.status} onRetry={teamState.retry} />
      <MetricCard icon={<Bot />} title="团队健康" value={`${team.teamHealth.healthyAgentCount}/9`} detail={`运行 ${team.teamHealth.activeAgentRunCount} · 失败/越权 ${team.teamHealth.failedOrDeniedCount}`} tone="jade" />
      <MetricCard icon={<Sparkles />} title="待处理能力提升" value={`${team.teamHealth.pendingDraftCount}`} detail="只进入治理变更，不热改在途任务" tone="gold" />
      {team.agentCards.map((agent) => (
        <article className="agent-card" key={agent.agentId}>
          <div>
            <strong>{formatTeamDisplayName(agent.displayName)}</strong>
            <span>{formatTeamRole(agent.agentId)} · 近期产物质量 {Math.round(agent.recentQualityScore * 100)}%</span>
          </div>
          <p>胜任度 {Math.round(agent.recentQualityScore * 100)}% · 异常 {agent.failureCount} · 拒绝越权 {agent.deniedActionCount}</p>
          <p className="panel-note">短板：{agent.weaknessTags.length ? agent.weaknessTags.join("、") : "暂无突出短板"}</p>
          <div className="agent-actions">
            <WorkbenchLink href={`/governance/team/${agent.agentId}`} onNavigate={onNavigate}><FileSearch size={15} />画像</WorkbenchLink>
            <WorkbenchLink href={`/governance/team/${agent.agentId}/config`} onNavigate={onNavigate}><Sparkles size={15} />提升方案</WorkbenchLink>
          </div>
        </article>
      ))}
    </section>
  );
}

function AgentProfilePage({ agentId, onNavigate }: { agentId: string; onNavigate: Navigate }) {
  const profileState = useAgentProfileReadModel(agentId);
  const profile = profileState.data;
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>{profile.displayName}</h1>
        </div>
        <WorkbenchLink className="inline-action" href={`/governance/team/${profile.agentId}/config`} onNavigate={onNavigate}>能力提升方案</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={profileState.status} onRetry={profileState.retry} />
      <MiniList icon={<CheckCircle2 />} title="能做什么" items={profile.canDo} />
      <MiniList icon={<ShieldAlert />} title="不能做什么" items={profile.cannotDo} />
      <MiniList icon={<ClipboardCheck />} title="质量指标" items={[`结构校验 ${profile.qualityMetrics.schemaPassRate}`, `证据质量 ${profile.qualityMetrics.evidenceQuality}`]} />
      <MiniList
        icon={<GitBranch />}
        title="版本与权限"
        items={[
          `Profile ${profile.versions.profileVersion}`,
          `技能包 ${profile.versions.skillPackageVersion}`,
          `提示词 ${profile.versions.promptVersion}`,
          `上下文 ${profile.versions.contextSnapshotVersion}`,
          `工具权限 ${profile.toolPermissions.join(" / ")}`,
        ]}
      />
      <MiniList
        icon={<Brain />}
        title="CFO 归因"
        items={profile.cfoAttributionRefs.length ? profile.cfoAttributionRefs : ["暂无 CFO 归因关注"]}
      />
      <MiniList
        icon={<AlertTriangle />}
        title="越权/失败"
        items={[
          ...profile.deniedActions.map((item) => formatReason(item.reasonCode)),
          ...profile.failureRecords.map(formatFailureRecord),
          ...(profile.weaknessTags.length ? profile.weaknessTags.map((item) => `短板：${item}`) : ["暂无越权或失败记录"]),
        ]}
      />
    </section>
  );
}

function AgentConfigPage({ agentId, onNavigate }: { agentId: string; onNavigate: Navigate }) {
  const teamState = useTeamReadModel({ silentFallback: true });
  const team = teamState.data;
  const configState = useAgentCapabilityConfigReadModel(agentId);
  const config = configState.data;
  const draft = team.capabilityDraftSubmission;
  const [savedChangeRef, setSavedChangeRef] = useState<string | null>(null);
  const [draftSubmitting, setDraftSubmitting] = useState(false);
  const [draftError, setDraftError] = useState(false);
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>能力提升方案</h1>
          <p>{formatTeamRole(agentId || config.agentId)} · 只提交治理变更</p>
        </div>
        <WorkbenchLink
          className="inline-action"
          href={`/governance/approvals/${draft.ownerApprovalRef}`}
          onNavigate={onNavigate}
        >
          查看审批包
        </WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={teamState.status} onRetry={teamState.retry} />
      <ReadModelStatusBanner status={configState.status} onRetry={configState.retry} />
      <MiniList icon={<Sparkles />} title="可编辑字段" items={config.editableFields.map(formatConfigField)} />
      <MetricCard icon={<LockKeyhole />} title="热改阻断" value="已阻断" detail={formatReason(config.forbiddenDirectUpdateReason)} tone="danger" />
      <MiniList icon={<GitBranch />} title="生效范围" items={config.effectiveScopeOptions.map(formatStatus)} />
      <div className="flat-panel">
        <h3><ClipboardCheck size={16} />提升方案提交</h3>
        <button
          className="inline-action"
          disabled={savedChangeRef !== null || draftSubmitting}
          onClick={() => {
            setDraftSubmitting(true);
            setDraftError(false);
            createCapabilityDraft(agentId)
              .then((payload) => setSavedChangeRef(payload.governanceChangeRef))
              .catch(() => setDraftError(true))
              .finally(() => setDraftSubmitting(false));
          }}
          type="button"
        >
          {draftSubmitting ? "正在提交..." : "提交提升方案"}
        </button>
        {draftSubmitting ? (
          <p className="panel-note">正在提交能力提升方案，请勿重复点击。</p>
        ) : savedChangeRef ? (
          <p className="panel-note">
            已生成治理变更 {savedChangeRef} · 高影响，需进入老板审批 · 只对后续任务生效 · 在途任务继续使用旧快照
          </p>
        ) : draftError ? (
          <p className="panel-note danger">提升方案提交失败：未创建治理变更，请重试。</p>
        ) : (
          <p className="panel-note">提交后只生成治理变更，不会热改正在运行的 Agent。</p>
        )}
      </div>
    </section>
  );
}

function ApprovalDetailPage({ approvalId, onNavigate }: { approvalId: string; onNavigate: Navigate }) {
  const approvalState = useApprovalRecordReadModel(approvalId);
  const approval = approvalState.data;
  const [submittedDecision, setSubmittedDecision] = useState<string | null>(null);
  const [approvalResponse, setApprovalResponse] = useState<ApprovalDecisionApiReadModel | null>(null);
  const [approvalSubmitting, setApprovalSubmitting] = useState(false);
  const [approvalError, setApprovalError] = useState(false);
  const [approvalConflict, setApprovalConflict] = useState<{ code: string; traceId: string } | null>(null);
  const traceHref = `${approval.traceRoute}?returnTo=${encodeURIComponent(`/governance/approvals/${approval.approvalId}`)}`;
  if (approval.triggerReason === "approval_not_found") {
    return (
      <section className="page-grid approval-grid">
        <div className="section-header with-actions">
          <div>
            <h1>审批记录不可用</h1>
            <p>当前记录未出现在审批列表，不能渲染审批包或动作按钮。</p>
          </div>
          <WorkbenchLink className="inline-action" href="/governance?panel=todos" onNavigate={onNavigate}>返回待办</WorkbenchLink>
        </div>
        <ReadModelStatusBanner status={approvalState.status} onRetry={approvalState.retry} />
        <div className="flat-panel">
          <h3><AlertTriangle size={16} />没有可审批材料</h3>
          <p>请从待办进入真实审批记录，或重试读取最新审批列表。</p>
          <button className="ghost-button" onClick={approvalState.retry} type="button">重试</button>
        </div>
      </section>
    );
  }
  return (
    <section className="page-grid approval-grid">
      <div className="section-header with-actions">
        <div>
          <h1>审批包</h1>
          <p>{formatOwnerCopy(approval.subject)} · {formatReason(approval.triggerReason)}</p>
        </div>
        <WorkbenchLink className="inline-action" href={traceHref} onNavigate={onNavigate}>审计追溯</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={approvalState.status} onRetry={approvalState.retry} />
      <MetricCard icon={<ClipboardCheck />} title="推荐结论" value={formatStatus(approval.recommendation)} detail={`影响 ${formatStatus(approval.impactScope)}`} tone="gold" />
      <MiniList icon={<Layers3 />} title="对比分析" items={approval.comparisonOptions.map(formatApprovalText)} />
      <MiniList icon={<ShieldAlert />} title="风险与影响" items={approval.riskAndImpact.map(formatApprovalText)} />
      <MiniList
        icon={<GitBranch />}
        title="影响范围"
        items={[`适用范围：${formatStatus(approval.impactScope)} / 只对后续任务生效`, `回滚方式：已有回滚方案`, `超时${formatApprovalText(approval.timeoutDisposition)}`]}
      />
      <MiniList icon={<FileSearch />} title="替代方案" items={approval.alternatives.map(formatApprovalText)} />
      <div className="flat-panel">
        <h3><Layers3 size={16} />可选动作</h3>
        <div className="command-actions">
          {approval.allowedActions.map((action) => (
            <button
              className={action === "request_changes" ? "ghost-button" : ""}
              disabled={approvalSubmitting || approvalResponse !== null}
              key={action}
              onClick={() => {
                setSubmittedDecision(action);
                setApprovalSubmitting(true);
                setApprovalError(false);
                setApprovalConflict(null);
                setApprovalResponse(null);
                submitApprovalDecision(approval.approvalId, action)
                  .then((payload) => setApprovalResponse(payload))
                  .catch((error: unknown) => {
                    if (
                      error instanceof ApiRequestError
                      && (error.statusCode === 409 || error.code === "SNAPSHOT_MISMATCH" || error.code === "CONFLICT")
                    ) {
                      setApprovalConflict({ code: error.code, traceId: error.traceId });
                    } else {
                      setApprovalError(true);
                    }
                  })
                  .finally(() => setApprovalSubmitting(false));
              }}
              type="button"
            >
              {formatStatus(action)}
            </button>
          ))}
        </div>
        {approvalSubmitting && submittedDecision ? (
          <p className="panel-note">正在提交：{formatStatus(submittedDecision)} · 按钮已锁定，等待后端返回最新审批状态</p>
        ) : approvalResponse ? (
          <p className="panel-note">后端状态：{formatStatus(approvalResponse.decision)} · 生效范围：{formatStatus(approvalResponse.effectiveScope)}</p>
        ) : approvalConflict ? (
          <p className="panel-note danger">审批状态已变化，请刷新 · {approvalConflict.code} · {approvalConflict.traceId}</p>
        ) : approvalError && submittedDecision ? (
          <p className="panel-note danger">提交失败：{formatStatus(submittedDecision)} · 请刷新后重试，不保留本地乐观结论。</p>
        ) : submittedDecision ? (
          <p className="panel-note">已提交：{formatStatus(submittedDecision)} · 等待后端返回最新审批状态 · 生效范围：{formatStatus(approval.impactScope)}</p>
        ) : (
          <p className="panel-note">提交后以后端状态为准，前端只展示提交反馈，不保留乐观结论。</p>
        )}
      </div>
      <MiniList icon={<GitBranch />} title="证据引用" items={approval.evidenceRefs.map(formatBusinessIdentifier)} />
    </section>
  );
}

function useRemoteReadModel<T>(
  fallbackFactory: () => T,
  loader: () => Promise<T>,
  deps: React.DependencyList,
  options: { silentFallback?: boolean } = {},
): RemoteReadModel<T> {
  const [reloadToken, setReloadToken] = useState(0);
  const silentFallback = options.silentFallback ?? false;
  const [state, setState] = useState<{ data: T; status: ReadModelStatus }>(() => ({
    data: fallbackFactory(),
    status: "loading",
  }));

  useEffect(() => {
    let cancelled = false;
    setState((current) => ({ ...current, status: "loading" }));
    loader()
      .then((payload) => {
        if (!cancelled) {
          setState({ data: payload, status: "ready" });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState((current) => ({ ...current, status: silentFallback ? "ready" : "error" }));
        }
      });
    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadToken]);

  return {
    data: state.data,
    status: state.status,
    retry: () => setReloadToken((token) => token + 1),
  };
}

function ReadModelStatusBanner({ status, onRetry }: { status: ReadModelStatus; onRetry: () => void }) {
  if (status === "ready") {
    return null;
  }
  if (status === "loading") {
    return <div className="status-banner">正在读取最新数据</div>;
  }
  return (
    <div className="status-banner danger">
      <span>真实数据不可用 · API 未返回 read model，未展示业务结论</span>
      <button className="ghost-button" onClick={onRetry} type="button">重试</button>
    </div>
  );
}

function useTeamReadModel(options: { silentFallback?: boolean } = {}) {
  return useRemoteReadModel<TeamReadModel>(() => buildTeamReadModel(), loadTeamReadModel, [], options);
}

function useAgentProfileReadModel(agentId: string) {
  const preview = buildTeamReadModel();
  const fallback = preview.agentProfileReadModels.find((item) => item.agentId === agentId)
    ?? preview.agentProfileReadModels[0];
  return useRemoteReadModel<AgentProfileReadModel>(
    () => fallback,
    () => loadAgentProfileReadModel(agentId),
    [agentId],
    { silentFallback: isPreviewAgentId(agentId) },
  );
}

function useAgentCapabilityConfigReadModel(agentId: string) {
  const fallback = { ...buildTeamReadModel().capabilityConfigReadModel, agentId };
  return useRemoteReadModel<CapabilityConfigReadModel>(
    () => fallback,
    () => loadAgentCapabilityConfigReadModel(agentId),
    [agentId],
    { silentFallback: isPreviewAgentId(agentId) },
  );
}

function useKnowledgeReadModel() {
  return useRemoteReadModel<KnowledgeReadModel>(() => buildEmptyKnowledgeReadModel(), loadKnowledgeReadModel, [], { silentFallback: false });
}

function useTraceDebugReadModel(workflowId: string) {
  return useRemoteReadModel<TraceDebugReadModel>(
    () => buildUnavailableTraceDebugReadModel(workflowId),
    () => loadTraceDebugReadModel(workflowId),
    [workflowId],
  );
}

function useInvestmentDossierReadModel(workflowId: string) {
  return useRemoteReadModel<InvestmentDossierReadModel>(
    () => buildUnavailableInvestmentDossierReadModel(workflowId),
    () => loadInvestmentDossierReadModel(workflowId),
    [workflowId],
    { silentFallback: false },
  );
}

function useGovernanceReadModel() {
  return useRemoteReadModel<GovernanceReadModel>(() => buildUnavailableGovernanceReadModel(), loadGovernanceReadModel, [], { silentFallback: false });
}

function useFinanceOverviewReadModel() {
  return useRemoteReadModel<FinanceOverviewReadModel>(() => buildUnavailableFinanceOverviewReadModel(), loadFinanceOverviewReadModel, [], { silentFallback: false });
}

function useDevOpsHealthReadModel(options: { silentFallback?: boolean } = { silentFallback: true }) {
  return useRemoteReadModel<DevOpsHealthReadModel>(() => buildDevOpsHealthReadModel(), loadDevOpsHealthReadModel, [], options);
}

function useApprovalRecordReadModel(approvalId: string) {
  const previewApproval = buildApprovalRecordReadModel();
  const isPreviewApproval = approvalId === previewApproval.approvalId;
  return useRemoteReadModel<ApprovalRecordReadModel>(
    () => isPreviewApproval
      ? previewApproval
      : buildApprovalRecordReadModel({
          approvalId,
          subject: `审批包 ${approvalId}`,
          triggerReason: "approval_not_found",
          comparisonOptions: [],
          riskAndImpact: [],
          evidenceRefs: [],
          allowedActions: [],
        }),
    () => loadApprovalRecordReadModel(approvalId),
    [approvalId],
    { silentFallback: isPreviewApproval },
  );
}

function buildUnavailableGovernanceReadModel(): GovernanceReadModel {
  const base = buildGovernanceReadModel();
  return {
    ...base,
    taskCenter: [],
    approvalCenter: [],
    unifiedTodos: [],
    governanceChanges: [],
  };
}

function buildUnavailableFinanceOverviewReadModel(): FinanceOverviewReadModel {
  return {
    assets: [],
    health: { liquidity: "无法判断", debtRatio: "无法判断", riskBudget: "无法判断", stress: "无法判断" },
    reminders: [],
    nonAAssetBoundary: { actionVisible: false, reasonCode: "api_unavailable" },
  };
}

function isPreviewAgentId(agentId: string) {
  return buildTeamReadModel().agentCards.some((agent) => agent.agentId === agentId);
}

function NotFoundPage({ onNavigate }: { onNavigate: Navigate }) {
  return (
    <section className="page-grid">
      <div className="section-header">
        <h1>未找到页面</h1>
        <p>当前地址不在 V1 工作台路由内。</p>
      </div>
      <WorkbenchLink className="inline-action" href="/" onNavigate={onNavigate}>返回全景</WorkbenchLink>
    </section>
  );
}

function RequestPreviewCard({
  preview,
  confirmedTask,
  onCancel,
  onConfirm,
  onNavigate,
  requestBriefStatus,
  canConfirm,
}: {
  preview: RequestBriefPreview;
  confirmedTask: ConfirmedTaskFeedback | null;
  onCancel: () => void;
  onConfirm: () => void;
  onNavigate: Navigate;
  requestBriefStatus: "idle" | "syncing" | "ready" | "failed";
  canConfirm: boolean;
}) {
  const boundary = preview.taskType === "research_task" ? "不会进入审批或交易" : preview.display.boundaryLabel;
  const needsClarification = preview.status !== "preview";
  return (
    <div className="request-brief-card">
      <h3>请求预览</h3>
      <strong>{needsClarification ? "还缺这些信息" : `系统会安排${preview.display.taskLabel}`}</strong>
      <span>负责人：{preview.display.leadLabel}</span>
      <span>{boundary}</span>
      <span>下一步：{preview.display.nextStepLabel}</span>
      {preview.details?.length ? (
        <dl className="request-preview-details">
          {preview.details.map((detail) => (
            <div key={detail.label}>
              <dt>{detail.label}：</dt>
              <dd>{detail.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {preview.clarificationPrompts?.length ? (
        <ul className="clarification-list">
          {preview.clarificationPrompts.map((item) => <li key={item}>{item}</li>)}
        </ul>
      ) : null}
      {preview.status === "blocked_draft" ? <span>原因：{formatReason(preview.reasonCode)}</span> : null}
      {requestBriefStatus === "syncing" ? <p className="panel-note">正在同步请求预览，稍后即可确认。</p> : null}
      {requestBriefStatus === "failed" ? <p className="panel-note danger">请求预览同步失败，请重试生成预览。</p> : null}
      <div className="command-actions">
        {preview.status === "preview" ? <button type="button" disabled={!canConfirm} onClick={onConfirm}>确认生成任务卡</button> : null}
        <button type="button" className="ghost-button" onClick={onCancel}>{preview.status === "preview" ? "取消" : "继续编辑"}</button>
      </div>
      {confirmedTask ? (
        <p className={`panel-note ${confirmedTask.status === "error" ? "danger" : ""}`.trim()}>
          {confirmedTask.label}{confirmedTask.status === "success" ? " · 等待后端确认后刷新状态" : " · 未创建任务卡"}
          {confirmedTask.status === "success" && confirmedTask.href ? (
            <>
              {" · "}
              <WorkbenchLink className="inline-action" href={confirmedTask.href} onNavigate={onNavigate}>打开投资档案</WorkbenchLink>
            </>
          ) : null}
        </p>
      ) : null}
    </div>
  );
}

function AttentionCard({ label, title, detail, tone, href, onNavigate }: {
  label: string;
  title: string;
  detail: string;
  tone: "danger" | "warn" | "info" | "neutral";
  href: string;
  onNavigate: Navigate;
}) {
  return (
    <WorkbenchLink className={`attention-card ${tone}`} href={href} onNavigate={onNavigate}>
      <span>{label}</span>
      <strong>{title}</strong>
      <p>{detail}</p>
    </WorkbenchLink>
  );
}

function OverviewListLink({ title, detail, href, onNavigate }: {
  title: string;
  detail: string;
  href: string;
  onNavigate: Navigate;
}) {
  return (
    <li>
      <WorkbenchLink className="business-list-link" href={href} onNavigate={onNavigate}>
        <strong>{title}</strong>
        <span>{detail}</span>
      </WorkbenchLink>
    </li>
  );
}

function TodoCenterCard({ todo, task, onNavigate }: {
  todo: GovernanceTodoItem;
  task?: GovernanceReadModel["taskCenter"][number];
  onNavigate: Navigate;
}) {
  if (todo.todoType === "approval") {
    return (
      <article className="task-card approval">
        <div>
          <strong>{formatOwnerCopy(todo.title)}</strong>
          <span>{formatDisplayText(todo.detail)}</span>
        </div>
        <p>来自审批列表，提交后以后端状态刷新。</p>
        <WorkbenchLink className="inline-action" href={todo.actionHref} onNavigate={onNavigate}>{todo.actionLabel}</WorkbenchLink>
      </article>
    );
  }
  if (task) {
    return <TaskCenterCard task={task} onNavigate={onNavigate} />;
  }
  return (
    <article className="task-card">
      <strong>{formatDisplayText(todo.title)}</strong>
      <span>{formatDisplayText(todo.detail)}</span>
      <WorkbenchLink className="inline-action" href={todo.actionHref} onNavigate={onNavigate}>{todo.actionLabel}</WorkbenchLink>
    </article>
  );
}

function TaskCenterCard({ task, onNavigate }: {
  task: GovernanceReadModel["taskCenter"][number];
  onNavigate: Navigate;
}) {
  if (task.taskType !== "manual_todo") {
    return (
      <article className="task-card">
        <strong>{formatTaskType(task.taskType)}</strong>
        <span>{formatStatus(task.currentState)} · {formatReason(task.reasonCode)}</span>
      </article>
    );
  }
  const actionHref = getManualTodoActionHref(task);
  return (
    <article className="task-card manual">
      <div>
        <strong>人工待办：{getManualTodoAction(task)}</strong>
        <span>状态：{formatStatus(task.currentState)}</span>
      </div>
      <p>原因：{formatReason(task.reasonCode)}</p>
      <p>截止时间：{task.dueDate ?? "本周内"}</p>
      <p>风险提示：{task.riskHint ?? getManualTodoRisk(task)}</p>
      <p className="panel-note">不进入审批、执行或交易链路；没有通用完成 API 时，只能去对应模块办理。</p>
      <WorkbenchLink className="inline-action" href={actionHref} onNavigate={onNavigate}>去办理</WorkbenchLink>
    </article>
  );
}

function isActionableGovernanceTask(task: GovernanceReadModel["taskCenter"][number]) {
  if (task.taskType === "manual_todo") {
    return true;
  }
  if (task.reasonCode === "request_brief_confirmed") {
    return false;
  }
  return new Set(["ready", "blocked", "owner_pending", "draft", "waiting"]).has(task.currentState);
}

function getManualTodoAction(task: GovernanceReadModel["taskCenter"][number]) {
  const labels: Record<string, string> = {
    annual_tax: "确认年度税务资料",
    api_tax_window: "确认税务窗口",
    manual_valuation_due: "更新房产或非 A 股资产估值",
    non_a_asset_manual_only: "补充非 A 股资产资料",
    route_non_a_manual_todo: "补充非 A 股资产资料",
    tuition: "确认教育支出",
  };
  return labels[task.reasonCode] ?? "补充人工资料";
}

function getManualTodoRisk(task: GovernanceReadModel["taskCenter"][number]) {
  const labels: Record<string, string> = {
    annual_tax: "税务资料不完整会影响年度现金规划",
    api_tax_window: "税务窗口未确认会影响现金流提醒",
    manual_valuation_due: "估值过期会影响资产配置和风险预算",
    non_a_asset_manual_only: "资料不完整会影响财务规划",
    route_non_a_manual_todo: "资料不完整会影响财务规划",
    tuition: "重大支出未确认会影响现金约束",
  };
  return labels[task.reasonCode] ?? "信息缺失会影响后续规划";
}

function getManualTodoActionHref(task: GovernanceReadModel["taskCenter"][number]) {
  return `/finance?todo=${encodeURIComponent(task.taskId)}`;
}

function MetricCard({ icon, title, value, detail, tone, href, onNavigate }: {
  icon: React.ReactNode;
  title: string;
  value: string;
  detail: string;
  tone: string;
  href?: string;
  onNavigate?: Navigate;
}) {
  const content = (
    <>
      <div className="icon-box">{icon}</div>
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </>
  );
  if (!href || !onNavigate) {
    return <article className={`metric-card ${tone}`}>{content}</article>;
  }
  return (
    <WorkbenchLink className={`metric-card ${tone}`} href={href} onNavigate={onNavigate}>
      {content}
    </WorkbenchLink>
  );
}

function summarizeFinanceAssets(assets: FinanceOverviewReadModel["assets"]) {
  const groups = new Map<string, { amount: number; currency: string; statuses: Set<string>; manual: boolean }>();
  for (const asset of assets) {
    const label = formatAssetLabel(asset.label);
    const amount = parseFinanceAmount(asset.value);
    const currency = asset.value.match(/[A-Z]{3}/)?.[0] ?? "CNY";
    const current = groups.get(label) ?? { amount: 0, currency, statuses: new Set<string>(), manual: false };
    current.amount += amount;
    current.currency = currency;
    current.statuses.add(formatStatus(asset.status));
    current.manual = current.manual || asset.status === "manual_todo" || asset.status === "finance_planning_only";
    groups.set(label, current);
  }
  const entries = Array.from(groups.entries());
  const total = entries.reduce((sum, [label, item]) => label === "负债" ? sum - item.amount : sum + item.amount, 0);
  return {
    totalLabel: `${Math.round(total).toLocaleString("zh-CN")} CNY`,
    categoryCount: entries.length,
    manualCount: entries.filter(([, item]) => item.manual).length,
    lines: entries.length
      ? entries.map(([label, item]) => `${label} · ${Math.round(item.amount).toLocaleString("zh-CN")} ${item.currency} · ${Array.from(item.statuses).join(" / ")}`)
      : ["暂无资产明细，先提交财务档案"],
  };
}

function parseFinanceAmount(value: string) {
  const match = value.replace(/,/g, "").match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

type StageDetailBlock = { title: string; items: string[] };
type SummaryFact = { label: string; value: string };
type DossierDrawerDetail = {
  title: string;
  subtitle: string;
  blocks: StageDetailBlock[];
};
type DirectDetailItem = { label: string; detail: DossierDrawerDetail };
type DirectPanelModel = {
  title: string;
  lead?: string;
  items?: string[];
  detailItems?: DirectDetailItem[];
};
type StageSummaryItem = {
  key: string;
  title: string;
  value: string;
  lines: string[];
  detail: DossierDrawerDetail;
  detailItems?: DirectDetailItem[];
  facts?: SummaryFact[];
  badge?: string;
  span?: 4 | 6 | 8 | 12;
};

function isAnalystStage(stage: string) {
  return stage === "S2" || stage === "S3";
}

function getDefaultAnalystRole(dossier: InvestmentDossierReadModel) {
  const hardDissent = dossier.analystStanceMatrix.find((row) => row.hardDissent);
  if (hardDissent) return hardDissent.role;
  const ranked = [...dossier.analystStanceMatrix].sort((a, b) =>
    (a.evidenceQuality ?? a.confidence) - (b.evidenceQuality ?? b.confidence),
  );
  return ranked[0]?.role ?? dossier.rolePayloadDrilldowns[0]?.role ?? null;
}

function buildCurrentIcStageItems(dossier: InvestmentDossierReadModel) {
  const currentStage = dossier.workflow.currentStage;
  const items = [
    buildCurrentStageHandlingText(dossier),
    `共识 ${Math.round(dossier.consensus.score * 100)}% · 行动强度 ${Math.round(dossier.consensus.actionConviction * 100)}%`,
    `数据：决策核心 ${formatStatus(dossier.dataReadiness.decisionCoreStatus)} · 执行核心 ${formatStatus(dossier.dataReadiness.executionCoreStatus)}`,
  ];

  if (currentStage === "S3") {
    items.splice(1, 0, `辩论 ${dossier.debate.roundsUsed} 轮 · ${dossier.debate.retainedHardDissent ? "硬异议仍保留" : "分歧已收敛"}`);
  } else if (currentStage === "S1") {
    items.splice(1, 0, `数据就绪：${formatStatus(dossier.dataReadiness.qualityBand)}`);
  } else {
    items.splice(1, 0, `当前进度：${currentStage} ${getStageView(currentStage).title}`);
  }

  if (dossier.riskReview.reasonCodes.includes("execution_core_blocked_no_trade")) {
    items.push("S6 执行门槛：执行数据不足，不影响当前 S3 阻断判断");
  }

  return items;
}

function buildCurrentStageHandlingText(dossier: InvestmentDossierReadModel) {
  if (dossier.workflow.currentStage === "S3" && dossier.workflow.state === "blocked") {
    return "当前处理：硬异议保留，需先补证并交风控复核";
  }
  return `当前处理：${formatWorkflowStageState(dossier.workflow.state)}`;
}

function buildDossierStatusLine(dossier: InvestmentDossierReadModel) {
  const currentStage = `${dossier.workflow.currentStage} ${getStageShortTitle(dossier.workflow.currentStage)}${formatWorkflowStageState(dossier.workflow.state)}`;
  const blocker = dossier.workflow.currentStage === "S3" && dossier.workflow.state === "blocked"
    ? " · 硬异议保留，待补证后交风控复核"
    : "";
  return `${dossier.workflow.title} · IC：${currentStage}${blocker}`;
}

function formatWorkflowStageState(value: string) {
  if (value === "running") return "运行中";
  return formatStatus(value);
}

function buildStageSummaryItems(dossier: InvestmentDossierReadModel, selectedStage: string): StageSummaryItem[] {
  if (selectedStage === "S2") {
    return buildS2SummaryItems(dossier);
  }
  return [makeStageSummaryItem(dossier, selectedStage, "stage", "阶段摘要", "暂无摘要", [])];
}

function buildS2SummaryItems(dossier: InvestmentDossierReadModel): StageSummaryItem[] {
  const hardDissent = dossier.analystStanceMatrix.filter((row) => row.hardDissent);
  return [
    {
      key: "S2-conclusion",
      title: "结论摘要",
      value: "分析完成，进入辩论而非决策",
      lines: [],
      detailItems: buildS2ConclusionDetailItems(dossier, hardDissent),
      detail: makeDetail("结论摘要", "S2 分析产物收口", [
        { title: "岗位判断", items: dossier.analystStanceMatrix.map((row) => `${formatRoleName(row.role)}：${formatAnalystDirection(row.direction)} · ${Math.round(row.confidence * 100)}%`) },
        { title: "主要依据", items: dossier.rolePayloadDrilldowns.flatMap((item) => item.highlights).slice(0, 5) },
        { title: "反证风险", items: hardDissent.map((row) => row.hardDissentReason ?? "硬异议保留") },
        { title: "进入 S3 条件", items: ["S2 已形成岗位判断，但硬异议未消除，不能直接放行 S4"] },
        { title: "建议动作", items: ["进入 S3 辩论；补证前不形成 CIO 决策。"] },
      ]),
      span: 12,
    },
  ];
}

function buildS2ConclusionDetailItems(
  dossier: InvestmentDossierReadModel,
  hardDissent: InvestmentDossierReadModel["analystStanceMatrix"],
): DirectDetailItem[] {
  const submitted = dossier.rolePayloadDrilldowns.length;
  const hardDissentLabel = hardDissent[0] ? `${formatRoleName(hardDissent[0].role).replace("分析师", "")}证据不足` : "暂无";
  return [
    {
      label: hardDissent.length ? "去向：进入 S3 辩论" : "去向：等待 CIO 收口",
      detail: makeDetail("去向详情", "S2 分析收口", [
        { title: "当前结论", items: ["四位分析师已形成岗位判断。", hardDissent.length ? "硬异议未消除，不能直接进入 S4。" : "暂无硬异议，等待 CIO 判断是否进入 S4。"] },
        { title: "为什么", items: dossier.analystStanceMatrix.map((row) => `${formatRoleName(row.role)}：${formatAnalystDirection(row.direction)} · 置信 ${Math.round(row.confidence * 100)}%`) },
        { title: "下一步", items: [hardDissent.length ? "进入 S3 辩论并补证。" : "交 CIO 收口。"] },
      ]),
    },
    {
      label: `硬异议：${hardDissentLabel}`,
      detail: makeDetail("硬异议详情", "S2 反证和补证焦点", [
        { title: "保留异议", items: hardDissent.map((row) => `${formatRoleName(row.role)}：${row.hardDissentReason ?? "硬异议保留"}`) },
        { title: "反证风险", items: dossier.rolePayloadDrilldowns.flatMap((item) => item.keyRisks ?? []).slice(0, 4) },
        { title: "补证要求", items: ["资产质量修复证据", "拨备覆盖率趋势", "息差改善证据"] },
        { title: "影响", items: ["补证前不形成 CIO 决策，也不直接进入 S4。"] },
      ]),
    },
    {
      label: `证据：${submitted} 位分析师已交，平均证据 ${getAverageEvidenceQuality(dossier)}%`,
      detail: buildAnalystMatrixDrawerDetail(dossier),
    },
    {
      label: "下一步：补资产质量和息差证据",
      detail: makeDetail("补证详情", "S2 到 S3 的补齐动作", [
        { title: "要补什么", items: ["资产质量修复证据", "拨备覆盖率趋势", "息差改善证据"] },
        { title: "谁使用", items: ["S3 辩论用于重新评估保留异议。", "CIO 收口前必须看到补证结果。"] },
        { title: "完成后", items: ["补证后重新辩论或交风控复核，再判断是否进入 S4。"] },
      ]),
    },
  ];
}

function makeStageSummaryItem(
  dossier: InvestmentDossierReadModel,
  stage: string,
  key: string,
  title: string,
  value: string,
  lines: string[],
  span?: 4 | 6 | 8 | 12,
): StageSummaryItem {
  const detail = buildStageDetail(dossier, stage);
  return {
    key: `${stage}-${key}`,
    title,
    value,
    lines,
    detail: { ...detail, title },
    span: span ?? 4,
  };
}

function makeDetail(title: string, subtitle: string, blocks: StageDetailBlock[]): DossierDrawerDetail {
  return { title, subtitle, blocks };
}

function buildAnalystMatrixBadge(dossier: InvestmentDossierReadModel) {
  const rolesWithPayload = new Set(dossier.rolePayloadDrilldowns.map((item) => item.role));
  const submitted = dossier.analystStanceMatrix.filter((row) => rolesWithPayload.has(row.role)).length;
  return `${submitted}/${dossier.analystStanceMatrix.length} 已提交 · 平均证据 ${getAverageEvidenceQuality(dossier)}%`;
}

function getAverageEvidenceQuality(dossier: InvestmentDossierReadModel) {
  const totalRoles = dossier.analystStanceMatrix.length || 1;
  return Math.round(
    dossier.analystStanceMatrix.reduce((sum, row) => sum + (row.evidenceQuality ?? row.confidence), 0) / totalRoles * 100,
  );
}

function buildAnalystMatrixDrawerDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  const rolesWithPayload = new Set(dossier.rolePayloadDrilldowns.map((item) => item.role));
  const evidenceRows = dossier.analystStanceMatrix.map((row) =>
    `${formatRoleName(row.role)}：${formatAnalystDirection(row.direction)} · 置信 ${Math.round(row.confidence * 100)}% · 证据 ${Math.round((row.evidenceQuality ?? row.confidence) * 100)}% · ${rolesWithPayload.has(row.role) ? "已交" : "待补"} · ${row.hardDissent ? "硬异议" : "正常"}`,
  );
  const lowEvidence = [...dossier.analystStanceMatrix].sort((a, b) =>
    (a.evidenceQuality ?? a.confidence) - (b.evidenceQuality ?? b.confidence),
  )[0];
  return makeDetail("分析师立场矩阵", buildAnalystMatrixBadge(dossier), [
    { title: "岗位判断", items: evidenceRows },
    { title: "证据质量", items: [`平均证据 ${getAverageEvidenceQuality(dossier)}%`, lowEvidence ? `最低证据岗位：${formatRoleName(lowEvidence.role)} ${Math.round((lowEvidence.evidenceQuality ?? lowEvidence.confidence) * 100)}%` : "暂无证据质量"] },
    { title: "产物状态", items: dossier.analystStanceMatrix.map((row) => `${formatRoleName(row.role)}：${rolesWithPayload.has(row.role) ? "已提交" : "待补"}`) },
    { title: "硬异议", items: dossier.analystStanceMatrix.filter((row) => row.hardDissent).map((row) => `${formatRoleName(row.role)}：${row.hardDissentReason ?? "硬异议保留"}`) },
    { title: "建议动作", items: ["低证据岗位先补证，不由单一偏正面观点推动 S4。"] },
  ]);
}

function buildAnalystDrawerDetail(dossier: InvestmentDossierReadModel, role: string): DossierDrawerDetail {
  const analyst = buildAnalystDetail(dossier, role);
  return makeDetail(analyst.roleLabel, analyst.stanceLabel, [
    { title: "岗位判断", items: [analyst.thesis, analyst.stanceLabel] },
    { title: "主要依据", items: analyst.evidenceItems },
    { title: "反证风险", items: analyst.riskItems },
    {
      title: "适用边界",
      items: [
        ...analyst.applicableConditions,
        ...analyst.invalidationConditions.map((item) => `失效：${item}`),
      ],
    },
    { title: "建议动作", items: analyst.actionItems },
  ]);
}

function buildS3AnalystDrawerDetail(dossier: InvestmentDossierReadModel, role: string): DossierDrawerDetail {
  const analyst = buildAnalystDetail(dossier, role);
  const stance = dossier.analystStanceMatrix.find((item) => item.role === role);
  const viewChanges = getAnalystDebateViewChanges(dossier, role);
  return makeDetail(analyst.roleLabel, "S3 辩论后更新", [
    {
      title: "辩论回应",
      items: [
        analyst.thesis,
        stance?.hardDissent ? `硬异议仍保留：${stance.hardDissentReason ?? "需要补证后再判断"}` : "本轮未新增硬异议。",
      ],
    },
    {
      title: "观点变化",
      items: viewChanges.length ? viewChanges : ["后端未返回辩论详情"],
    },
    {
      title: "保留分歧",
      items: getAnalystRetainedDissentItems(dossier, role, stance?.hardDissentReason),
    },
    {
      title: "CIO 处理",
      items: [
        dossier.debate.cioSynthesis ? formatDisplayText(dossier.debate.cioSynthesis) : "后端未返回辩论详情",
        formatS3NextActionSummary(dossier),
      ],
    },
    {
      title: "补证要求",
      items: getS3RequiredEvidenceItems(dossier),
    },
  ]);
}

function missingS3DebateDetail(title: string): DossierDrawerDetail {
  return makeDetail(title, "S3 辩论详情", [
    { title: "详情状态", items: ["后端未返回辩论详情"] },
  ]);
}

function formatS3StatusSummary(dossier: InvestmentDossierReadModel) {
  const status = dossier.debate.statusSummary;
  if (!status) return "后端未返回辩论详情";
  const consensus = typeof status.consensusScore === "number" ? ` · 共识 ${Math.round(status.consensusScore * 100)}%` : "";
  const action = typeof status.actionConviction === "number" ? ` · 行动强度 ${Math.round(status.actionConviction * 100)}%` : "";
  return `已用 ${status.roundsUsed} 轮 · ${status.retainedHardDissent ? "硬异议保留" : "分歧已收敛"} · ${status.riskReviewRequired ? "需交风控复核" : "暂不需要风控复核"}${consensus}${action}`;
}

function formatS3CoreDisputeSummary(dossier: InvestmentDossierReadModel) {
  const dispute = dossier.debate.coreDisputes?.[0];
  if (!dispute) return "后端未返回辩论详情";
  return `${dispute.title}；${dispute.whyItMatters}`;
}

function formatS3ViewChangeSummary(dossier: InvestmentDossierReadModel) {
  const changes = dossier.debate.viewChangeDetails ?? [];
  if (!changes.length) return "后端未返回辩论详情";
  return changes.map((change) => `${change.role}：${change.before} -> ${change.after}`).join("；");
}

function formatS3RetainedDissentSummary(dossier: InvestmentDossierReadModel) {
  const dissent = dossier.debate.retainedDissentDetails?.[0];
  if (!dissent) return "后端未返回辩论详情";
  const rolePrefix = dissent.sourceRole.replace("分析师", "");
  return `${rolePrefix}硬异议仍保留：${dissent.dissent}`;
}

function formatS3NextActionSummary(dossier: InvestmentDossierReadModel) {
  const action = dossier.debate.nextActions?.[0];
  if (!action) return "后端未返回辩论详情";
  return `${action.action}；${action.owner}负责；${action.nextStage}`;
}

function buildS3CoreDisputeDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  const disputes = dossier.debate.coreDisputes ?? [];
  if (!disputes.length) return missingS3DebateDetail("核心分歧详情");
  return makeDetail("核心分歧详情", "S3 辩论与 CIO 综合", [
    { title: "分歧问题", items: disputes.map((item) => item.title) },
    { title: "为什么重要", items: disputes.map((item) => item.whyItMatters) },
    { title: "涉及岗位", items: disputes.map((item) => item.involvedRoles.join(" / ")) },
    { title: "当前结论", items: disputes.map((item) => item.currentConclusion) },
    { title: "补证要求", items: disputes.flatMap((item) => item.requiredEvidence) },
  ]);
}

function buildS3ViewChangeDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  const changes = dossier.debate.viewChangeDetails ?? [];
  if (!changes.length) return missingS3DebateDetail("观点变化详情");
  return makeDetail("观点变化详情", "S3 辩论后岗位判断变化", [
    { title: "岗位变化", items: changes.map((item) => `${item.role}：${item.before} -> ${item.after}`) },
    { title: "变化原因", items: changes.map((item) => `${item.role}：${item.reason}`) },
    { title: "对 S4 的影响", items: changes.map((item) => `${item.role}：${item.impact}`) },
  ]);
}

function buildS3RetainedDissentDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  const dissents = dossier.debate.retainedDissentDetails ?? [];
  if (!dissents.length) return missingS3DebateDetail("保留异议详情");
  return makeDetail("保留异议详情", "S3 硬异议处理", [
    { title: "异议来源", items: dissents.map((item) => item.sourceRole) },
    { title: "异议内容", items: dissents.map((item) => item.dissent) },
    { title: "反证风险", items: dissents.flatMap((item) => item.counterRisks) },
    { title: "处置方式", items: dissents.map((item) => item.handling) },
    { title: "禁止动作", items: dissents.flatMap((item) => item.forbiddenActions) },
  ]);
}

function buildS3RoundDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  const rounds = dossier.debate.roundDetails ?? [];
  if (!rounds.length) return missingS3DebateDetail("轮次详情");
  return makeDetail("轮次详情", "S3 Debate Manager 轮次记录", [
    {
      title: "轮次记录",
      items: rounds.flatMap((round) => [
        `第 ${round.roundNo} 轮：${round.issue}`,
        `参与者：${round.participants.join(" / ")}`,
        `输入证据：${round.inputEvidence.join(" / ")}`,
        `处理结果：${round.outcome}`,
        `未解决问题：${round.unresolvedQuestions.join(" / ")}`,
      ]),
    },
  ]);
}

function getAnalystDebateViewChanges(dossier: InvestmentDossierReadModel, role: string) {
  return (dossier.debate.viewChangeDetails ?? [])
    .filter((item) => s3DetailMatchesRole(item.role, role))
    .map((item) => `${item.before} -> ${item.after}：${item.reason}；影响：${item.impact}`);
}

function getAnalystRetainedDissentItems(dossier: InvestmentDossierReadModel, role: string, hardDissentReason?: string | null) {
  const retained = (dossier.debate.retainedDissentDetails ?? [])
    .filter((item) => s3DetailMatchesRole(item.sourceRole, role))
    .flatMap((item) => [
      item.dissent,
      ...item.counterRisks.map((risk) => `反证风险：${risk}`),
      `处置方式：${item.handling}`,
      ...item.forbiddenActions.map((action) => `禁止动作：${action}`),
    ]);
  const items = [...(hardDissentReason ? [hardDissentReason] : []), ...retained];
  return items.length ? items : ["后端未返回辩论详情"];
}

function getS3RequiredEvidenceItems(dossier: InvestmentDossierReadModel) {
  const items = [
    ...(dossier.debate.coreDisputes ?? []).flatMap((item) => item.requiredEvidence),
    ...(dossier.debate.nextActions ?? []).map((item) => item.action),
  ];
  return items.length ? items : ["后端未返回辩论详情"];
}

function s3DetailMatchesRole(label: string, role: string) {
  const roleLabel = formatRoleName(role);
  const shortLabel = roleLabel.replace("分析师", "");
  const aliases: Record<string, string[]> = {
    macro: ["宏观"],
    macro_analyst: ["宏观"],
    fundamental: ["基本面", "资产质量"],
    fundamental_analyst: ["基本面", "资产质量"],
    quant: ["量化"],
    quant_analyst: ["量化"],
    event: ["事件", "公告"],
    event_analyst: ["事件", "公告"],
  };
  const needles = [roleLabel, shortLabel, ...(aliases[role] ?? [])].filter(Boolean);
  return needles.some((needle) => label.includes(needle));
}

function buildS6ExecutionGateDetail(dossier: InvestmentDossierReadModel): DossierDrawerDetail {
  return makeDetail("成交门槛", "S6 审批与纸面执行", [
    { title: "执行状态", items: [`状态 ${formatStatus(dossier.paperExecution.status)}`, `定价 ${formatPricingMethod(dossier.paperExecution.pricingMethod)}`] },
    { title: "成交门槛", items: ["执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因"] },
    { title: "窗口费用", items: [`窗口 ${dossier.paperExecution.window}`, `费用 ${dossier.paperExecution.fees}`, `T+1 ${formatStatus(dossier.paperExecution.tPlusOne)}`] },
    { title: "不可成交原因", items: ["不显示继续成交入口", ...dossier.riskReview.reasonCodes.map(formatReason)] },
  ]);
}

function buildStageDetail(dossier: InvestmentDossierReadModel, selectedStage: string): {
  title: string;
  subtitle: string;
  blocks: StageDetailBlock[];
} {
  switch (selectedStage) {
    case "S0":
      return {
        title: "请求边界",
        subtitle: formatStatus(dossier.workflow.state),
        blocks: [
          { title: "阶段总览", items: ["接收请求，确认任务边界和无预设结论承诺"] },
          { title: "任务目标", items: [dossier.workflow.title] },
          { title: "当前状态", items: [`${dossier.workflow.currentStage} ${getStageView(dossier.workflow.currentStage).title} · ${formatStatus(dossier.workflow.state)}`] },
        ],
      };
    case "S1":
      return {
        title: "数据就绪",
        subtitle: formatStatus(dossier.dataReadiness.qualityBand),
        blocks: [
          { title: "阶段总览", items: [`数据质量 ${formatStatus(dossier.dataReadiness.qualityBand)}`] },
          { title: "决策问题", items: [dossier.chairBrief.decisionQuestion] },
          { title: "核心数据", items: [`决策核心 ${formatStatus(dossier.dataReadiness.decisionCoreStatus)}`, `执行核心 ${formatStatus(dossier.dataReadiness.executionCoreStatus)}`] },
          { title: "关键缺口", items: dossier.dataReadiness.issues },
        ],
      };
    case "S2":
      return {
        title: "分析备忘",
        subtitle: "按分析师查看",
        blocks: [
          { title: "阶段总览", items: ["四位分析师形成岗位判断，等待 S3 处理分歧"] },
          { title: "分析师", items: dossier.analystStanceMatrix.map((row) => `${formatRoleName(row.role)} · ${formatAnalystDirection(row.direction)} · ${Math.round(row.confidence * 100)}%`) },
        ],
      };
    case "S3":
      return {
        title: "未解决分歧",
        subtitle: dossier.debate.retainedHardDissent ? "硬异议保留" : "分歧已收敛",
        blocks: [
          { title: "阶段总览", items: [`已用 ${dossier.debate.roundsUsed} 轮`, dossier.debate.retainedHardDissent ? "硬异议保留" : "分歧已收敛"] },
          { title: "争议点", items: dossier.debate.issues },
          { title: "观点变化", items: dossier.debate.viewChanges ?? [] },
          { title: "CIO 综合", items: dossier.debate.cioSynthesis ? [formatDisplayText(dossier.debate.cioSynthesis)] : [] },
          {
            title: "当前处理",
            items: [
              ...(dossier.debate.unresolvedDissent ?? []),
              dossier.debate.riskReviewRequired ? "硬异议保留，需补证后交风控复核" : "无需风控复核",
            ],
          },
        ],
      };
    case "S4":
      return {
        title: "CIO 决策",
        subtitle: dossier.consensus.thresholdLabel,
        blocks: [
          { title: "阶段总览", items: ["等待 S3 补证和风控复核后再形成 CIO 决策"] },
          { title: "行动判断", items: [`共识 ${Math.round(dossier.consensus.score * 100)}%`, `行动强度 ${Math.round(dossier.consensus.actionConviction * 100)}%`] },
          { title: "偏离说明", items: [dossier.optimizerDeviation.recommendation] },
        ],
      };
    case "S5":
      return {
        title: "风控结论",
        subtitle: formatStatus(dossier.riskReview.reviewResult),
        blocks: [
          { title: "阶段总览", items: [`风控结论 ${formatStatus(dossier.riskReview.reviewResult)}`] },
          { title: "可修复性", items: [formatStatus(dossier.riskReview.repairability)] },
          { title: "例外审批", items: [dossier.riskReview.ownerExceptionRequired ? "需要 Owner 例外审批" : "不生成 Owner 例外审批"] },
          { title: "原因", items: dossier.riskReview.reasonCodes.map(formatReason) },
        ],
      };
    case "S6":
      return {
        title: "执行门槛",
        subtitle: formatStatus(dossier.paperExecution.status),
        blocks: [
          { title: "阶段总览", items: ["审批与纸面执行只在 S6 判断，不解释当前 S3 阻断"] },
          { title: "执行状态", items: buildExecutionGateItems(dossier).slice(0, 3) },
          { title: "成交门槛", items: dossier.riskReview.reasonCodes.includes("execution_core_blocked_no_trade") ? ["执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因"] : [] },
          { title: "不可成交原因", items: ["不显示继续成交入口"] },
        ],
      };
    case "S7":
      return {
        title: "归因与反思",
        subtitle: "后续回链",
        blocks: [
          { title: "阶段总览", items: ["等待正式执行和归因样本后形成复盘"] },
          { title: "归因摘要", items: [dossier.attribution.summary] },
          { title: "回链", items: dossier.attribution.links },
        ],
      };
    default:
      return { title: "阶段详情", subtitle: "暂无详情", blocks: [] };
  }
}

function buildAnalystDetail(dossier: InvestmentDossierReadModel, role: string) {
  const payload = dossier.rolePayloadDrilldowns.find((item) => item.role === role);
  const stance = dossier.analystStanceMatrix.find((item) => item.role === role);
  const highlights = payload?.highlights ?? [];
  const supportingCount = payload?.supportingEvidenceRefs?.length ?? 0;
  const counterCount = payload?.counterEvidenceRefs?.length ?? 0;
  return {
    roleLabel: formatRoleName(role),
    stanceLabel: stance
      ? `${formatAnalystDirection(stance.direction)} · ${Math.round(stance.confidence * 100)}%${stance.hardDissent ? " · 硬异议" : ""}`
      : "已提交岗位备忘",
    thesis: payload?.thesis ?? stance?.thesis ?? highlights[0] ?? "已提交岗位备忘",
    evidenceItems: [
      ...highlights,
      ...(supportingCount ? [`已引用支撑证据 ${supportingCount} 条`] : []),
    ],
    riskItems: [
      ...(payload?.hardDissentReason ? [`硬异议：${payload.hardDissentReason}`] : []),
      ...(payload?.keyRisks ?? []),
      ...(counterCount ? [`已引用反证 ${counterCount} 条`] : []),
    ],
    applicableConditions: payload?.applicableConditions ?? [],
    invalidationConditions: payload?.invalidationConditions ?? [],
    actionItems: payload?.suggestedActionImplication ? [payload.suggestedActionImplication] : [],
  };
}

function buildExecutionGateItems(dossier: InvestmentDossierReadModel) {
  const items = [
    `状态 ${formatStatus(dossier.paperExecution.status)}`,
    `方式 ${formatPricingMethod(dossier.paperExecution.pricingMethod)} · 窗口 ${dossier.paperExecution.window}`,
    `费用 ${dossier.paperExecution.fees} · T+1 ${formatStatus(dossier.paperExecution.tPlusOne)}`,
    "不显示继续成交入口",
  ];
  if (dossier.riskReview.reasonCodes.includes("execution_core_blocked_no_trade")) {
    items.push("执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因");
  }
  return items;
}

function buildDebateTimelineItems(dossier: InvestmentDossierReadModel) {
  const items = [
    `已用 ${dossier.debate.roundsUsed} 轮`,
    ...dossier.debate.issues.map((item) => `争议点：${item}`),
    ...(dossier.debate.viewChanges ?? []).map((item) => `观点变化：${formatDisplayText(item)}`),
    ...(dossier.debate.cioSynthesis ? [`CIO 综合：${formatDisplayText(dossier.debate.cioSynthesis)}`] : []),
    ...(dossier.debate.unresolvedDissent ?? []).map((item) => `保留分歧：${formatDisplayText(item)}`),
    ...(dossier.debate.rounds ?? []).map((round) => `第 ${round.roundNo ?? "?"} 轮：${round.issue ?? "议题待补"} · ${round.outcome ?? "等待结论"}`),
  ];
  return items.length ? items : ["暂无辩论过程摘要"];
}

function formatTraceRunSummary(run: TraceDebugReadModel["agentRunTree"][number]) {
  if (run.businessSummary) {
    return `${formatRoleName(run.agentId ?? "")} · ${formatStatus(run.status ?? "running")} · ${run.businessSummary}`;
  }
  return `${formatRoleName(run.agentId ?? run.stage)} · ${formatStatus(run.status ?? "running")} · ${formatDisplayText(run.stage)}`;
}

function buildExperienceLibrarySummary(knowledge: KnowledgeReadModel) {
  const meaningful = getOwnerVisibleMemories(knowledge.memoryResults);
  const verified = meaningful.filter((item) => item.promotionState === "promoted" || item.promotionState === "verified").length;
  const pending = Math.max(knowledge.memoryResults.length - verified, 0);
  const conflictCount = knowledge.relationGraph.filter((item) => item.relationType === "contradicts").length;
  return [
    `已验证经验 ${verified} 条`,
    `待整理资料 ${pending} 条`,
    `冲突线索 ${conflictCount} 条`,
  ];
}

function buildDossierRiskReviewItems(dossier: InvestmentDossierReadModel) {
  const currentStage = dossier.workflow.currentStage;
  const currentStageBlocked = dossier.workflow.state === "blocked" && currentStage === "S3";
  const items = [
    `结果 ${formatStatus(dossier.riskReview.reviewResult)}`,
    `可修复性 ${formatStatus(dossier.riskReview.repairability)}`,
    dossier.riskReview.ownerExceptionRequired ? "需要 Owner 例外审批" : "不生成 Owner 例外审批",
  ];
  if (currentStageBlocked) {
    items.push("当前 S3：硬异议保留，需先补证并交风控复核");
  } else {
    items.push(`当前阶段 ${formatDisplayText(currentStage)} · ${formatStatus(dossier.workflow.state)}`);
  }
  if (dossier.riskReview.reasonCodes.includes("execution_core_blocked_no_trade")) {
    items.push("执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因");
  }
  return items;
}

function buildOverviewRiskLinks(dossier: InvestmentDossierReadModel, riskItems: string[]) {
  const links: Array<{ title: string; detail: string; href: string }> = [];
  if (dossier.riskReview.reasonCodes.includes("retained_hard_dissent_risk_review")) {
    links.push({ title: "硬异议保留", detail: "当前 S3 受阻，需先补证并交风控复核。", href: "/investment/wf-001?stage=S3" });
  }
  if (dossier.riskReview.reasonCodes.includes("execution_core_blocked_no_trade")) {
    links.push({ title: "执行数据不足", detail: "这是 S6 成交门槛，不是当前 S3 阻断原因。", href: "/investment/wf-001?stage=S6" });
  }
  if (links.length) {
    return links;
  }
  return riskItems.slice(0, 3).map((item) => ({ title: formatDisplayText(item.split("：")[0] ?? "风险"), detail: item, href: "/investment/wf-001" }));
}

function buildOverviewSystemHealth(health: DevOpsHealthReadModel, status: ReadModelStatus) {
  if (status === "loading") {
    return { value: "读取中", detail: "正在读取健康接口，尚未形成降级判断。" };
  }
  if (status === "error") {
    return { value: "无法判断", detail: "健康接口未连接，不能判断真实降级原因。" };
  }

  const openIncidents = health.incidents.filter((incident) => isOpenHealthStatus(incident.status));
  if (openIncidents.length) {
    const incident = openIncidents[0];
    return {
      value: "降级",
      detail: `${formatIncidentType(incident.incidentType)}异常 · ${formatStatus(incident.status)}。`,
    };
  }

  const degradedChecks = health.routineChecks.filter((check) => isDegradedHealthStatus(check.status));
  if (degradedChecks.length) {
    const check = degradedChecks[0];
    return {
      value: "降级",
      detail: `${formatHealthCheck(check.checkId)} · ${formatStatus(check.status)}。`,
    };
  }

  const blockedRecovery = health.recovery.find((plan) => !plan.investmentResumeAllowed);
  if (blockedRecovery) {
    return {
      value: "恢复待验证",
      detail: `指标采集正常；无公开异常；恢复计划${formatStatus(blockedRecovery.technicalRecoveryStatus ?? "pending_validation")}，投资恢复未放行。`,
    };
  }

  return { value: "正常", detail: "指标采集正常；无公开异常；投资恢复已放行。" };
}

function isOpenHealthStatus(status: string) {
  return !["closed", "resolved", "completed"].includes(status);
}

function isDegradedHealthStatus(status: string) {
  return !["observed", "normal", "ok", "ready", "completed", "passed"].includes(status);
}

function getOwnerVisibleMemories(items: KnowledgeReadModel["memoryResults"]) {
  const visible: KnowledgeReadModel["memoryResults"] = [];
  const seen = new Set<string>();
  for (const item of items) {
    const title = item.title.trim().toLowerCase();
    if (!title || title === "test" || title === "测试" || title === "untitled memory") {
      continue;
    }
    if (/^memory[-_]\d+$/i.test(item.title) || /^artifact[-_]/i.test(item.title)) {
      continue;
    }
    const normalizedTitle = title.replace(/\s+/g, " ");
    if (seen.has(normalizedTitle)) {
      continue;
    }
    seen.add(normalizedTitle);
    visible.push(item);
  }
  return visible.slice(0, 5);
}

function summarizeKnowledgeRelations(relations: KnowledgeReadModel["relationGraph"]) {
  if (!relations.length) {
    return ["暂无已确认资料关系；需要后端提供明确来源和关联理由后才显示。"];
  }
  const counts = relations.reduce<Record<string, number>>((acc, relation) => {
    const label = formatRelationType(relation.relationType);
    acc[label] = (acc[label] ?? 0) + 1;
    return acc;
  }, {});
  const summary = Object.entries(counts).map(([label, count]) => `资料关系 · ${label} · ${count} 条`);
  const examples = relations.slice(0, 3).map((relation) =>
    `${formatKnowledgeRef(relation.sourceMemoryId)} -> ${formatKnowledgeRef(relation.targetRef)} · ${formatRelationType(relation.relationType)} · ${formatOwnerCopy(relation.reason)}`,
  );
  return [...summary, ...examples];
}

function formatEvidenceSourceList(refs: string[]) {
  const labels = refs.map(formatEvidenceSource);
  const uniqueLabels = Array.from(new Set(labels));
  return uniqueLabels.join("、") || "待补来源";
}

function formatEvidenceSource(ref: string) {
  if (ref.startsWith("memory-")) return "已保存经验";
  if (ref.startsWith("artifact-")) return "研究材料";
  if (ref.startsWith("news-")) return "公开新闻";
  if (ref.startsWith("filing-")) return "公告资料";
  return "外部资料";
}

function formatKnowledgeRef(ref: string) {
  if (ref === "research-1") return "半导体资料包";
  if (ref.startsWith("memory-")) return "已保存经验";
  if (ref.startsWith("artifact-")) return "研究材料";
  return formatOwnerCopy(ref);
}

function formatOrganizeSuggestion(item: KnowledgeReadModel["organizeSuggestions"][number]) {
  const tags = item.suggestedTags.join(" / ");
  return `建议标签：${tags || "待确认"}；${item.riskIfApplied}`;
}

function formatMemoryTitle(title: string) {
  const legacyCapturePrefix = new RegExp(`^Owner\\s*${"捕获"}${"记忆"}[:：]\\s*`, "i");
  return title.replace(legacyCapturePrefix, "").trim() || "待命名经验";
}

function formatTaskType(value: string) {
  const labels: Record<string, string> = {
    investment_workflow: "投资任务",
    research_task: "研究任务",
    finance_task: "财务任务",
    governance_task: "治理任务",
    agent_capability_change: "团队能力提升",
    system_task: "系统事项",
    manual_todo: "人工待办",
  };
  return labels[value] ?? value;
}

function formatChangeType(value: string) {
  const labels: Record<string, string> = {
    agent_capability: "团队能力提升",
    default_context: "默认上下文",
    prompt: "提示词",
    skill_package: "能力包",
    data_source_routing: "数据源策略",
    execution_parameter: "执行参数",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatEffectiveScope(value: string) {
  const labels: Record<string, string> = {
    current_attempt_only: "当前尝试",
    new_attempt: "新尝试",
    new_task: "后续任务",
    test: "后续任务",
  };
  return labels[value] ?? "后续任务";
}

function formatAssetLabel(value: string) {
  const labels: Record<string, string> = {
    income: "收入",
    cash: "现金",
    fund: "基金",
    gold: "黄金",
    real_estate: "房产",
    liability: "负债",
    a_share: "A 股",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatBudgetRef(value: string) {
  const labels: Record<string, string> = {
    "risk-budget-finance-v1": "财务风险预算 V1",
    "risk-budget-api": "API 风险预算",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatPricingMethod(value: string) {
  const labels: Record<string, string> = {
    minute_vwap: "分钟成交量加权均价",
    minute_twap: "分钟时间加权均价",
    not_released: "尚未放行",
    twap: "时间加权均价",
    vwap: "成交量加权均价",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatAnalystDirection(value: string) {
  const labels: Record<string, string> = {
    positive: "偏正面",
    neutral: "中性",
    negative: "偏负面",
    observe: "观察",
    cautious: "谨慎",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatReminder(value: string) {
  const labels: Record<string, string> = {
    annual_tax: "年度税务待确认",
    api_tax_window: "税务窗口待确认",
    manual_valuation_due: "手工估值待更新",
    tax_reminder: "税务提醒",
    tuition: "教育支出待确认",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatHealthCheck(value: string) {
  const labels: Record<string, string> = {
    "api-health": "接口健康",
    "data-source-latency": "数据源延迟",
    "execution-core-readiness": "执行数据就绪度",
  };
  return labels[value] ?? "系统检查";
}

function formatIncidentType(value: string) {
  const labels: Record<string, string> = {
    data_source: "数据源",
    runner: "运行器",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatCommandType(value: string) {
  const labels: Record<string, string> = {
    direct_write: "直接写入",
    request_evidence: "请求补证",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatEventType(value: string) {
  const labels: Record<string, string> = {
    guard_failed: "关口失败",
    handoff_created: "已生成交接",
    question_asked: "CIO 追问",
    tool_progress: "工具进展",
    view_update: "观点更新",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatContextReason(value: string) {
  const labels: Record<string, string> = {
    "Researcher digest": "研究员摘要",
    "finance raw field": "财务原始字段",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatRoleName(value: string) {
  const labels: Record<string, string> = {
    CIO: "CIO",
    cio: "CIO",
    macro: "宏观分析师",
    fundamental: "基本面分析师",
    quant: "量化分析师",
    event: "事件分析师",
    macro_analyst: "宏观分析师",
    fundamental_analyst: "基本面分析师",
    quant_analyst: "量化分析师",
    event_analyst: "事件分析师",
    risk_officer: "风控官",
    "Event Analyst": "事件分析员",
    "Risk Officer": "风控官",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatTeamDisplayName(value: string) {
  const labels: Record<string, string> = {
    CIO: "CIO",
    CFO: "CFO",
    "Macro Analyst": "宏观分析师",
    "Fundamental Analyst": "基本面分析师",
    "Quant Analyst": "量化分析师",
    "Event Analyst": "事件分析师",
    "Risk Officer": "风控官",
    "Investment Researcher": "投资研究员",
    "DevOps Engineer": "系统工程师",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatTeamRole(value: string) {
  const labels: Record<string, string> = {
    cio: "投研主席",
    cfo: "财务解释",
    macro_analyst: "宏观研究",
    fundamental_analyst: "基本面研究",
    quant_analyst: "量化研究",
    event_analyst: "事件研究",
    risk_officer: "风控复核",
    investment_researcher: "资料研究",
    devops_engineer: "系统运行",
  };
  return labels[value] ?? "团队成员";
}

function formatBusinessIdentifier(value: string) {
  if (/^(ap|approval)-/i.test(value)) return "审批记录";
  if (/^gov-/i.test(value)) return "治理变更";
  if (/^incident-/i.test(value)) return "运行事件";
  if (/^recovery-/i.test(value)) return "恢复计划";
  if (/^trace-/i.test(value)) return "审计追踪";
  if (/^ctx-/i.test(value)) return "上下文快照";
  if (/^task-/i.test(value)) return "任务";
  if (/^decision-guard-/i.test(value)) return "决策守卫证据";
  if (/^risk-review-/i.test(value)) return "风控复核证据";
  if (/^(source|artifact|handoff|run)-/i.test(value)) return "证据材料";
  return formatDisplayText(value);
}

function formatSensitivity(value: string) {
  const labels: Record<string, string> = {
    public_internal: "内部公开",
    finance_sensitive_raw: "财务敏感原始字段",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatConfigField(value: string) {
  const labels: Record<string, string> = {
    collaboration_commands: "协作命令",
    default_model_profile: "默认模型配置",
    default_skill_packages: "默认能力包",
    default_tool_profile_id: "默认工具配置",
    prompt_version: "提示词版本",
    service_permissions: "服务权限",
    skill_package_version: "技能包版本",
    tools_enabled: "启用工具",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatFailureRecord(value: string) {
  const labels: Record<string, string> = {
    schema_validation_failed: "结构校验失败",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatApprovalText(value: string) {
  if (/^(gov|decision-guard|risk-review|artifact|trace|ctx|ap|approval)-/i.test(value)) {
    return formatBusinessIdentifier(value);
  }
  return formatStatus(value) === formatDisplayText(value) ? formatDisplayText(value) : formatStatus(value);
}

function formatDisplayText(value: string) {
  const labels: Record<string, string> = {
    "Risk conditional path blocked Owner bypass": "风控条件路径已阻断老板绕过",
    "Event Analyst 补证中": "事件分析员补证中",
    "hard dissent retained": "硬异议保留",
    "hard dissent 交接 Risk": "硬异议交接风控",
    "api blocker": "API 阻断项",
    api_stress_checked: "API 压力检查通过",
    cash_floor_checked: "现金底线已检查",
    fenced_background_context_only: "仅作为背景上下文",
    hard_dissent_requires_evidence: "硬异议需要补证",
    hard_dissent_retained: "硬异议保留",
    memory_sensitive_denied: "敏感记忆已拒绝",
    observed: "已观测",
    tax_reminder: "税务提醒",
    timeout_means_no_execution: "超时不执行",
    trade_chain_allowed: "可进入 A 股投研链路",
  };
  return labels[value] ?? replaceBusinessTokens(value);
}

function replaceBusinessTokens(value: string) {
  return value
    .replace(/\bapprove_exception_only_if_risk_accepted\b/g, "仅在风控接受风险后批准例外")
    .replace(/\bcurrent_attempt_only\b/g, "当前尝试")
    .replace(/\bfollow_optimizer\b/g, "跟随优化器建议")
    .replace(/\bhigher_single_name_exposure\b/g, "单股暴露更高")
    .replace(/\bcio_deviation\b/g, "CIO 偏离")
    .replace(/\btrade_chain_allowed\b/g, "可进入 A 股投研链路")
    .replace(/\btax_reminder\b/g, "税务提醒")
    .replace(/\btimeout_means_no_execution\b/g, "超时不执行")
    .replace(/\bincome\b/g, "收入")
    .replace(/\breopen_s3_debate\b/g, "重开 S3 辩论补证")
    .replace(/\bnot_released\b/g, "尚未放行")
    .replace(/\bnot_started\b/g, "未开始")
    .replace(/\bpositive\b/g, "偏正面")
    .replace(/\bneutral\b/g, "中性")
    .replace(/\bpartial\b/g, "部分就绪")
    .replace(/\bpass\b/g, "通过");
}

function formatOwnerCopy(value: string) {
  return value
    .replace(/Agents能力/g, "团队能力")
    .replace(/Agent 团队/g, "团队")
    .replace(/团队草案/g, "团队能力提升")
    .replace(/能力配置草案/g, "能力提升方案")
    .replace(/能力草案/g, "能力提升方案")
    .replace(/高影响草案/g, "高影响方案")
    .replace(/治理变更草案/g, "治理变更");
}

function getSelectedStage(candidate: string | undefined, fallback: string) {
  return getStageView(candidate).title === "未知阶段" ? fallback : candidate ?? fallback;
}

function getStageView(stage: string | undefined) {
  const views: Record<string, { title: string }> = {
    S0: { title: "任务接收" },
    S1: { title: "数据准备" },
    S2: { title: "分析备忘" },
    S3: { title: "辩论与分歧" },
    S4: { title: "CIO 决策" },
    S5: { title: "风控复核" },
    S6: { title: "审批与纸面执行" },
    S7: { title: "归因与反思" },
  };
  return stage ? views[stage] ?? { title: "未知阶段" } : { title: "未知阶段" };
}

function getStageShortTitle(stage: string) {
  const labels: Record<string, string> = {
    S0: "接收",
    S1: "数据",
    S2: "分析",
    S3: "辩论",
    S4: "决策",
    S5: "风控",
    S6: "执行",
    S7: "归因",
  };
  return labels[stage] ?? "";
}

function getGovernanceModules() {
  return [
    { label: "待办", panel: "todos", href: "/governance?panel=todos" },
    { label: "团队", panel: "team", href: "/governance?panel=team" },
    { label: "变更", panel: "changes", href: "/governance?panel=changes" },
    { label: "健康", panel: "health", href: "/governance?panel=health" },
    { label: "审计", panel: "audit", href: "/governance?panel=audit" },
  ];
}

function getGovernancePanel(query: Record<string, string>) {
  if (query.task || query.panel === "tasks" || query.panel === "approvals") return "todos";
  if (query.change) return "changes";
  const knownPanels = new Set(getGovernanceModules().map((module) => module.panel));
  return query.panel && knownPanels.has(query.panel) ? query.panel : "todos";
}

function getTraceReturnLabel(returnHref: string) {
  if (returnHref.includes("/governance/approvals/")) return "返回审批包";
  if (returnHref.includes("/governance")) return "返回治理来源";
  return "返回投资档案";
}

function formatStatus(value: string) {
  const labels: Record<string, string> = {
    accepted: "已接收",
    applied: "已纳入",
    approved: "通过",
    approve_exception_only_if_risk_accepted: "仅在风控接受风险后批准例外",
    blocked: "受阻",
    candidate: "候选",
    conditional_pass: "条件通过",
    completed: "完成",
    degraded: "降级",
    denied: "已拒绝",
    draft: "待完善",
    effective: "已生效",
    extracted: "已抽取",
    failed: "失败",
    finance_planning_only: "仅用于财务规划",
    high: "高影响",
    higher_single_name_exposure: "单股暴露更高",
    hot_patch_denied: "热改已拒绝",
    medium: "中影响",
    manual_only: "人工处理",
    manual_todo: "人工待办",
    monitoring: "观察中",
    new_attempt: "新尝试",
    new_task: "后续任务",
    not_released: "尚未放行",
    not_started: "未开始",
    owner_pending: "等待老板审批",
    pending_validation: "待验证",
    ready: "待处理",
    rejected: "拒绝",
    repairable: "可修复",
    reopen_s3_debate: "重开 S3 辩论补证",
    request_changes: "要求修改",
    researching: "研究中",
    reviewing: "复核中",
    running: "处理中",
    triaged: "已分诊",
    unavailable: "不可用",
    unknown: "未知",
    validated_context: "已保存经验",
    partial: "部分就绪",
    pass: "通过",
    current_attempt_only: "当前尝试",
    follow_optimizer: "跟随优化器建议",
    cio_deviation: "CIO 偏离",
    trade_chain_allowed: "可进入 A 股投研链路",
    tax_reminder: "税务提醒",
    timeout_means_no_execution: "超时不执行",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatGuardLabel(value: string) {
  const labels: Record<string, string> = {
    "Risk blocked": "风控阻断",
    "execution_core blocked": "执行数据不足",
    "非 A 股 manual_todo": "非 A 股人工处理",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatReason(value: string) {
  const labels: Record<string, string> = {
    agent_capability_hot_patch_denied: "运行中任务不可热改",
    data_source_degraded: "数据源降级",
    DIRECT_WRITE_DENIED: "直接写入被拒绝",
    execution_core_blocked_no_trade: "执行数据不足，不能成交",
    high_impact_agent_capability_change: "高影响能力变更",
    api_portfolio_deviation: "组合偏离待确认",
    cio_deviation: "CIO 偏离待确认",
    governance_draft_only: "只能提交提升方案",
    hot_patch_denied: "热改已阻断",
    low_action_no_execution: "行动强度不足，不执行",
    no_trade_or_approval_entry: "不生成审批或交易入口",
    request_brief_confirmed: "请求已确认，等待补充资料",
    manual_valuation_due: "手工估值待更新",
    annual_tax: "年度税务待确认",
    api_tax_window: "税务窗口待确认",
    tuition: "教育支出待确认",
    non_a_asset_manual_only: "非 A 股只做人工事项",
    route_non_a_manual_todo: "非 A 股只做人工事项",
    non_a_asset_no_trade: "非 A 股不生成交易入口",
    request_brief_preview_required: "需先生成请求预览",
    retained_hard_dissent_risk_review: "硬异议保留，需风控复核",
    timeout_means_no_execution: "超时不执行",
    risk_rejected_no_override: "风控拒绝，不可绕过",
    ["supporting_" + "evidence_only"]: "仅作为支撑证据",
  };
  return labels[value] ?? formatDisplayText(value);
}

function formatRelationType(value: string) {
  const labels: Record<string, string> = {
    applies_to: "适用于",
    contradicts: "反驳",
    derived_from: "来源于",
    duplicates: "重复",
    promotes_to: "晋升到",
    promotes_to_knowledge: "晋升知识",
    related_to: "关联",
    supports: "支撑",
    supersedes: "取代",
  };
  return labels[value] ?? value;
}

function MiniList({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <div className="flat-panel">
      <h3>{icon}{title}</h3>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function WorkbenchLink({ href, onNavigate, active = false, className = "", children }: {
  href: string;
  onNavigate: Navigate;
  active?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <a
      className={`${active ? "active" : ""} ${className}`.trim()}
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onNavigate(href);
      }}
    >
      {children}
    </a>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
