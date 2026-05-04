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
  InvestmentDossierReadModel,
  KnowledgeReadModel,
  ApprovalRecordReadModel,
  RequestBriefPreview,
  ResolvedWorkbenchRoute,
  TeamReadModel,
  TraceDebugReadModel,
  buildApprovalRecordReadModel,
  buildDevOpsHealthReadModel,
  buildFinanceOverviewReadModel,
  buildGovernanceReadModel,
  buildInvestmentDossierReadModel,
  buildInvestmentQueueReadModel,
  buildKnowledgeReadModel,
  buildOwnerDecisionReadModel,
  buildShellReadModel,
  buildTeamReadModel,
  buildTraceDebugReadModel,
  resolveWorkbenchRoute,
  routeOwnerCommand,
} from "./workbench";
import {
  ApiRequestError,
  RequestBriefApiReadModel,
  TaskCardApiReadModel,
  applyMemoryOrganizeSuggestion,
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
            <span className="badge warn">审批 {shell.attentionCounts.approvals}</span>
            <span className="badge info">人工 {shell.attentionCounts.manualTodo}</span>
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
                      setGeneratedPreview(routeOwnerCommand(command));
                      setRequestBrief(null);
                      setRequestBriefStatus("syncing");
                      setConfirmedTask(null);
                      createRequestBrief(command)
                        .then((brief) => {
                          setRequestBrief(brief);
                          setRequestBriefStatus("ready");
                        })
                        .catch(() => setRequestBriefStatus("failed"));
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
                  <div className="request-preview-empty">输入一句话后生成预览，系统只说明将做什么，不会直接执行。</div>
                )}
              </section>
            ) : null}
          </div>
        </header>
        <div className="workspace-content">
          {renderWorkbenchPage(route, navigate)}
        </div>
      </main>
    </div>
  );
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
      return <FinancePage />;
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
  const owner = buildOwnerDecisionReadModel();
  return (
    <section className="page-grid overview-grid" aria-labelledby="overview-title">
      <h1 className="sr-only" id="overview-title">全景</h1>
      <AttentionCard label="风控阻断" title="浦发银行当前不可继续" detail="硬异议未消除，建议回到辩论阶段补证。" tone="danger" href="/investment/wf-001" onNavigate={onNavigate} />
      <AttentionCard label="待审批" title="组合偏离例外今天到期" detail={`建议 ${owner.approvalSummary.nearestDeadline} 前处理，影响 ${owner.approvalSummary.impactScope}。`} tone="warn" href="/governance/approvals/ap-001" onNavigate={onNavigate} />
      <AttentionCard label="团队草案" title="量化分析能力改进待验证" detail="只影响后续任务，不热改正在运行的分析。" tone="info" href="/governance/team" onNavigate={onNavigate} />
      <AttentionCard label="人工待办" title="房产估值本周需更新" detail="补充资料即可，不进入审批或交易链路。" tone="neutral" href="/governance?task=manual" onNavigate={onNavigate} />

      <div className="flat-panel list-panel">
        <div className="card-head"><strong>审批</strong><span className="badge warn">{owner.approvalSummary.pending} 项</span></div>
        <ul className="business-list">
          <li><strong>风控条件通过例外</strong><span>建议通过，影响当前投资任务。</span></li>
          <li><strong>团队能力高影响草案</strong><span>建议要求修改，只对后续任务生效。</span></li>
        </ul>
      </div>
      <MetricCard icon={<WalletCards />} title="纸面账户" value={owner.paperAccount.totalValue} detail={`现金 ${owner.paperAccount.cash} · 收益 ${owner.paperAccount.return}`} tone="jade" href="/finance" onNavigate={onNavigate} />
      <div className="flat-panel">
        <div className="card-head"><strong>风险</strong><span className="badge danger">2 项</span></div>
        <ul className="business-list">
          <li><strong>硬异议保留</strong><span>不允许直接绕过。</span></li>
          <li><strong>执行数据不足</strong><span>只保留研究与观察建议。</span></li>
        </ul>
      </div>
      <div className="flat-panel list-panel">
        <div className="card-head"><strong>每日简报</strong><span className="badge info">研究线索</span></div>
        <ul className="business-list">
          {owner.dailyBriefSummary.map((item) => (
            <li key={item.title}><strong>{item.title}</strong><span>{item.priority} · 只作为研究线索，不跳过正式投研门槛。</span></li>
          ))}
        </ul>
      </div>
      <MetricCard icon={<AlertTriangle />} title="系统" value="降级" detail={owner.systemHealth.incident} tone="indigo" href="/governance?panel=health" onNavigate={onNavigate} />
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
  const stageView = getStageView(selectedStage);
  return (
    <section className="page-grid dossier-grid">
      <div className="section-header with-actions">
        <div>
          <h1>投资档案</h1>
          <p>{dossier.workflow.title} · {formatStatus(dossier.workflow.state)}</p>
        </div>
        <WorkbenchLink className="inline-action" href={dossier.traceRoute} onNavigate={onNavigate}>查看审计</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={dossierState.status} onRetry={dossierState.retry} />
      <div className="stage-rail">
        {dossier.stageRail.map((stage) => (
          <button
            aria-pressed={stage.stage === selectedStage}
            className={`stage-chip ${stage.nodeStatus} ${stage.stage === selectedStage ? "selected" : ""}`.trim()}
            key={stage.stage}
            onClick={() => onNavigate(`${route.pathname}?stage=${stage.stage}`)}
            type="button"
          >
            {stage.stage}<span>{formatStatus(stage.nodeStatus)}</span>
          </button>
        ))}
      </div>
      <div className="analysis-matrix">
        <div className="stage-context">
          <strong>当前查看：{selectedStage} {stageView.title}</strong>
          <span>只切换查看阶段，不推进流程</span>
        </div>
        <h3>CIO 决策摘要</h3>
        <p>{dossier.chairBrief.decisionQuestion}</p>
        {dossier.analystStanceMatrix.map((row) => (
          <div className="matrix-row" key={row.role}>
            <span>{row.role}</span>
            <strong>{row.direction}</strong>
            <small>{Math.round(row.confidence * 100)}%</small>
            {row.hardDissent ? <em>硬异议</em> : <i>正常</i>}
          </div>
        ))}
      </div>
      <GuardPanel />
      <DossierBusinessPanels dossier={dossier} />
    </section>
  );
}

function DossierBusinessPanels({ dossier }: { dossier: InvestmentDossierReadModel }) {
  return (
    <>
      <MiniList
        icon={<ShieldAlert />}
        title="数据就绪"
        items={[
          `质量档位 ${formatStatus(dossier.dataReadiness.qualityBand)}`,
          `决策核心 ${formatStatus(dossier.dataReadiness.decisionCoreStatus)}`,
          `执行核心 ${formatStatus(dossier.dataReadiness.executionCoreStatus)}`,
          ...dossier.dataReadiness.issues,
        ]}
      />
      <MiniList
        icon={<Layers3 />}
        title="角色 payload"
        items={dossier.rolePayloadDrilldowns.map((item) => `${item.role} · ${item.highlights.join(" / ")}`)}
      />
      <MetricCard
        icon={<CheckCircle2 />}
        title="共识与行动强度"
        value={`${Math.round(dossier.consensus.score * 100)}% / ${Math.round(dossier.consensus.actionConviction * 100)}%`}
        detail={dossier.consensus.thresholdLabel}
        tone="jade"
      />
      <MiniList
        icon={<ShieldAlert />}
        title="分歧看板"
        items={[
          dossier.debate.retainedHardDissent ? "硬异议仍保留" : "硬异议已消除",
          dossier.debate.riskReviewRequired ? "需风控复核" : "无需风控复核",
          ...dossier.debate.issues,
        ]}
      />
      <MiniList
        icon={<GitBranch />}
        title="辩论时间线"
        items={[`已用 ${dossier.debate.roundsUsed} 轮`, ...dossier.debate.issues.map((item) => `议题：${item}`)]}
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
        icon={<ShieldAlert />}
        title="风控结论"
        items={[
          `结果 ${formatStatus(dossier.riskReview.reviewResult)}`,
          `可修复性 ${formatStatus(dossier.riskReview.repairability)}`,
          dossier.riskReview.ownerExceptionRequired ? "需要 Owner 例外审批" : "不生成 Owner 例外审批",
          ...dossier.riskReview.reasonCodes.map(formatReason),
        ]}
      />
      <MiniList
        icon={<WalletCards />}
        title="纸面执行"
        items={[
          `状态 ${formatStatus(dossier.paperExecution.status)}`,
          `方式 ${dossier.paperExecution.pricingMethod} · 窗口 ${dossier.paperExecution.window}`,
          `费用 ${dossier.paperExecution.fees} · T+1 ${dossier.paperExecution.tPlusOne}`,
          "不显示继续成交入口",
        ]}
      />
      <MiniList
        icon={<Brain />}
        title="归因回链"
        items={[dossier.attribution.summary, ...dossier.attribution.links]}
      />
    </>
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
          <p>{trace.workflowId} · AgentRun / Command / Handoff / ContextSlice</p>
        </div>
        <WorkbenchLink className="inline-action" href={returnHref} onNavigate={onNavigate}>{returnLabel}</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={traceState.status} onRetry={traceState.retry} />
      <MiniList icon={<Bot />} title="AgentRun 树" items={trace.agentRunTree.map((run) => `${run.runId} · ${run.stage} · ${run.profileVersion}`)} />
      <MiniList icon={<GitBranch />} title="CollaborationCommand" items={trace.commands.map((command) => `${command.commandType} · ${command.admission} · ${command.reasonCode}`)} />
      <MiniList icon={<FileSearch />} title="CollaborationEvent" items={trace.events.map((event) => `${event.eventType} · ${event.summary}`)} />
      <MiniList icon={<LockKeyhole />} title="Context 注入" items={trace.contextInjectionRecords.map((record) => `${record.contextSnapshotId} · ${record.redactionStatus} · ${record.whyIncluded}`)} />
      <MiniList icon={<Layers3 />} title="Handoff" items={trace.handoffs.map((handoff) => `${handoff.from} -> ${handoff.to} · ${handoff.blockers.join("/")}`)} />
    </section>
  );
}

function FinancePage() {
  const financeState = useFinanceOverviewReadModel();
  const finance = financeState.data;
  const [assetUpdateStatus, setAssetUpdateStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const [updatedAssetId, setUpdatedAssetId] = useState<string | null>(null);
  return (
    <section className="page-grid finance-grid">
      <h1 className="sr-only">财务</h1>
      <ReadModelStatusBanner status={financeState.status} onRetry={financeState.retry} />
      <MiniList icon={<WalletCards />} title="资产概览" items={finance.assets.map((asset) => `${asset.label} · ${asset.value} · ${formatStatus(asset.status)}`)} />
      <MetricCard icon={<ShieldAlert />} title="风险预算" value={finance.health.riskBudget} detail={`流动性 ${finance.health.liquidity} · 压力 ${finance.health.stress}`} tone="jade" />
      <MiniList icon={<AlertTriangle />} title="提醒" items={finance.reminders} />
      <div className="flat-panel">
        <h3><WalletCards size={16} />财务档案</h3>
        <button
          className="inline-action"
          disabled={assetUpdateStatus === "submitting"}
          onClick={() => {
            setAssetUpdateStatus("submitting");
            updateFinanceAsset()
              .then((payload) => {
                setUpdatedAssetId(payload.assetId);
                setAssetUpdateStatus("done");
              })
              .catch(() => setAssetUpdateStatus("failed"));
          }}
          type="button"
        >
          {assetUpdateStatus === "submitting" ? "正在更新..." : "更新现金档案"}
        </button>
        {assetUpdateStatus === "done" ? (
          <p className="panel-note">财务档案已更新 {updatedAssetId} · 不触发审批、执行或交易链路</p>
        ) : assetUpdateStatus === "failed" ? (
          <p className="panel-note danger">财务档案更新失败，请重试。</p>
        ) : (
          <p className="panel-note">资产档案更新只影响财务视图，不触发审批、执行或交易链路。</p>
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
      <h3><AlertTriangle size={16} />数据/服务健康</h3>
      <ReadModelStatusBanner status={healthState.status} onRetry={healthState.retry} />
      <ul>
        {health.routineChecks.map((check) => (
          <li key={check.checkId}>{check.checkId} · {check.status}</li>
        ))}
        {health.incidents.map((incident) => (
          <li key={incident.incidentId}>{incident.incidentId} · {incident.status} · {incident.incidentType}</li>
        ))}
        {health.recovery.map((plan) => (
          <li key={plan.planId}>{plan.planId} · {plan.investmentResumeAllowed ? "投资恢复已放行" : "投资恢复未放行"}</li>
        ))}
      </ul>
    </div>
  );
}

function KnowledgePage({ onNavigate }: { onNavigate: Navigate }) {
  const knowledgeState = useKnowledgeReadModel();
  const knowledge = knowledgeState.data;
  const [captureStatus, setCaptureStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const [capturedMemoryId, setCapturedMemoryId] = useState<string | null>(null);
  const defaultMemoryDraft = "Owner 捕获记忆：后续研究资料需要保留来源、标签和适用边界。";
  const memoryDraftRef = useRef<HTMLInputElement>(null);
  const [organizeStatus, setOrganizeStatus] = useState<"idle" | "submitting" | "done" | "failed">("idle");
  const [organizeRelationId, setOrganizeRelationId] = useState<string | null>(null);
  const firstSuggestion = knowledge.organizeSuggestions[0];
  const suggestionMemoryId = firstSuggestion?.targetMemoryRefs[0] ?? knowledge.memoryResults[0]?.memoryId ?? "memory";
  const suggestionVersionId = knowledge.memoryResults.find((item) => item.memoryId === suggestionMemoryId)?.currentVersionId
    ?? knowledge.memoryResults[0]?.currentVersionId
    ?? "memory-version";
  return (
    <section className="page-grid knowledge-grid">
      <h1 className="sr-only">知识</h1>
      <ReadModelStatusBanner status={knowledgeState.status} onRetry={knowledgeState.retry} />
      <MiniList icon={<Brain />} title="每日简报" items={knowledge.dailyBrief.map((item) => `${item.priority} · ${item.title} · ${item.supportingEvidenceOnly ? "只作支撑证据" : "正式资料"}`)} />
      <MiniList icon={<FileSearch />} title="研究资料包" items={knowledge.researchPackages.map((item) => `${item.title} · ${formatStatus(item.status)} · ${item.evidenceRefs.join(" / ")}`)} />
      <MiniList icon={<Brain />} title="资料集" items={knowledge.memoryCollections.map((item) => `${item.title} · ${item.resultCount} 条`)} />
      <div className="flat-panel">
        <h3><Layers3 size={16} />记忆工作区</h3>
        <p className="panel-note">capture / review / digest / organize · Memory 不是正式业务事实源</p>
        <input
          aria-label="记忆正文"
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
                setCapturedMemoryId(payload.memoryId);
                setCaptureStatus("done");
              })
              .catch(() => setCaptureStatus("failed"));
          }}
          type="button"
        >
          {captureStatus === "submitting" ? "正在捕获..." : "捕获记忆"}
        </button>
        {captureStatus === "done" ? (
          <p className="panel-note">已捕获记忆 {capturedMemoryId} · 经 Gateway 写入 · append-only</p>
        ) : captureStatus === "failed" ? (
          <p className="panel-note danger">记忆捕获失败，请重试。</p>
        ) : null}
        <ul>
          {knowledge.memoryResults.map((item) => (
            <li key={item.memoryId}>
              {item.title} · 抽取状态 {formatStatus(item.extractionStatus)} · 晋升状态 {formatStatus(item.promotionState)} · sensitivity {item.sensitivity} · {item.tags.join(" / ")}
            </li>
          ))}
        </ul>
      </div>
      <MiniList
        icon={<GitBranch />}
        title="关系图"
        items={knowledge.relationGraph.map((item) => `${item.sourceMemoryId} ${formatRelationType(item.relationType)} ${item.targetRef} · ${item.reason}`)}
      />
      <MiniList
        icon={<ClipboardCheck />}
        title="待应用组织建议"
        items={knowledge.organizeSuggestions.map((item) =>
          `${item.suggestionId} · ${item.suggestedTags.join(" / ")} · ${item.requiresGatewayWrite ? "经 Gateway 应用" : "无需写入"} · ${item.riskIfApplied}`,
        )}
      />
      <div className="flat-panel">
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
                setOrganizeRelationId(payload.relationId);
                setOrganizeStatus("done");
              })
              .catch(() => setOrganizeStatus("failed"));
          }}
          type="button"
        >
          {organizeStatus === "submitting" ? "正在应用..." : "应用建议 / 应用组织建议"}
        </button>
        {organizeStatus === "done" ? (
          <p className="panel-note">组织建议已提交 {organizeRelationId} · 组织建议已经通过 Gateway 应用 · 未覆盖旧 MemoryVersion</p>
        ) : organizeStatus === "failed" ? (
          <p className="panel-note danger">组织建议应用失败，请重试。</p>
        ) : (
          <p className="panel-note">应用建议只追加 relation / collection 变更，不直接使 DefaultContext 生效。</p>
        )}
      </div>
      <div className="flat-panel">
        <h3><LockKeyhole size={16} />Context 注入检查</h3>
        <ul>
          {knowledge.contextInjectionInspector.map((item) => (
            <li key={`${item.contextSnapshotId}-${item.sourceRef}`}>
              {item.contextSnapshotId} · {item.sourceRef} · why_included {item.whyIncluded} · {formatStatus(item.redactionStatus)} · denied refs {item.deniedRefs.join(" / ") || "none"}
            </li>
          ))}
        </ul>
      </div>
      <div className="flat-panel">
        <h3><Sparkles size={16} />Knowledge / Prompt / Skill 提案</h3>
        <ul>
          {knowledge.proposals.map((proposal) => (
            <li key={proposal.proposalId}>
              {proposal.proposalId} · diff / manifest · {formatStatus(proposal.impactLevel)} · 验证结果 {proposal.validationResultRefs.join(" / ")} · 适用范围 {formatStatus(proposal.effectiveScope)} · 回滚 {proposal.rollbackPlan}
            </li>
          ))}
        </ul>
        <p className="panel-note">提案不直接生效；低/中影响走自动验证，高影响进入审批中心。</p>
        <WorkbenchLink className="inline-action" href={knowledge.defaultContextProposalPath} onNavigate={onNavigate}>进入治理提案</WorkbenchLink>
      </div>
    </section>
  );
}

function GovernancePage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const governanceState = useGovernanceReadModel();
  const governance = governanceState.data;
  const teamState = useTeamReadModel();
  const team = teamState.data;
  const selectedPanel = getGovernancePanel(route.query);
  const taskCenter = route.query.task === "manual"
    ? governance.taskCenter.filter((task) => task.taskType === "manual_todo")
    : governance.taskCenter;
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
      {selectedPanel === "tasks" ? (
        <div className="flat-panel list-panel" data-panel="tasks">
          <h3><Layers3 size={16} />任务中心</h3>
          {route.query.task === "manual" ? <p className="panel-note">当前筛选：人工待办 · 不进入审批、执行或交易链路</p> : null}
          <ul>
            {taskCenter.map((task) => (
              <li key={task.taskId}>{formatTaskType(task.taskType)} · {formatStatus(task.currentState)} · {formatReason(task.reasonCode)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {selectedPanel === "approvals" ? (
        <div className="flat-panel list-panel" data-panel="approvals">
          <h3><Landmark size={16} />审批中心</h3>
          <ul>{governance.approvalCenter.map((approval) => <li key={approval.approvalId}>{approval.approvalId} · {formatReason(approval.triggerReason)}</li>)}</ul>
        </div>
      ) : null}
      {selectedPanel === "team" ? (
        <div className="flat-panel list-panel" data-panel="team">
          <h3><Bot size={16} />Agent 团队</h3>
          <ul>{team.agentCards.slice(0, 5).map((agent) => <li key={agent.agentId}>{agent.displayName} · {agent.recentQualityScore}</li>)}</ul>
          <WorkbenchLink className="inline-action" href="/governance/team" onNavigate={onNavigate}>进入 Agent 团队</WorkbenchLink>
        </div>
      ) : null}
      {selectedPanel === "changes" ? (
        <div className="flat-panel list-panel" data-panel="changes">
          <h3><GitBranch size={16} />变更管理</h3>
          {route.query.change === "default-context" ? <p className="panel-note">当前提案：默认上下文提案 · 只对后续任务生效</p> : null}
          <ul>
            {governance.governanceChanges.map((change) => (
              <li key={change.changeId}>{formatChangeType(change.changeType)} {change.changeId} · {formatStatus(change.state)} · {formatStatus(change.effectiveScope)}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {selectedPanel === "health" ? (
        <GovernanceHealthPanel />
      ) : null}
      {selectedPanel === "audit" ? (
        <div className="flat-panel list-panel" data-panel="audit">
          <h3><FileSearch size={16} />审计记录</h3>
          <ul>
            <li>trace-wf-001 · hard dissent 交接</li>
            <li>reopen-s3-001 · 保留证据只读展示</li>
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function AgentTeamPage({ onNavigate }: { onNavigate: Navigate }) {
  const teamState = useTeamReadModel();
  const team = teamState.data;
  return (
    <section className="page-grid team-grid">
      <div className="section-header">
        <h1>Agent 团队</h1>
      </div>
      <ReadModelStatusBanner status={teamState.status} onRetry={teamState.retry} />
      <MetricCard icon={<Bot />} title="团队健康" value={`${team.teamHealth.healthyAgentCount}/9`} detail={`运行 ${team.teamHealth.activeAgentRunCount} · 失败/越权 ${team.teamHealth.failedOrDeniedCount}`} tone="jade" />
      <MetricCard icon={<Sparkles />} title="待处理能力草案" value={`${team.teamHealth.pendingDraftCount}`} detail="只进入治理变更，不热改在途任务" tone="gold" />
      {team.agentCards.map((agent) => (
        <article className="agent-card" key={agent.agentId}>
          <div>
            <strong>{agent.displayName}</strong>
            <span>{agent.profileVersion} · Prompt {agent.promptVersion} · Context {agent.contextSnapshotVersion}</span>
          </div>
          <p>胜任度 {Math.round(agent.recentQualityScore * 100)}% · 失败 {agent.failureCount} · 越权 {agent.deniedActionCount}</p>
          <p className="panel-note">短板：{agent.weaknessTags.length ? agent.weaknessTags.join("、") : "暂无突出短板"}</p>
          <div className="agent-actions">
            <WorkbenchLink href={`/governance/team/${agent.agentId}`} onNavigate={onNavigate}><FileSearch size={15} />画像</WorkbenchLink>
            <WorkbenchLink href={`/governance/team/${agent.agentId}/config`} onNavigate={onNavigate}><Sparkles size={15} />草案</WorkbenchLink>
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
        <WorkbenchLink className="inline-action" href={`/governance/team/${profile.agentId}/config`} onNavigate={onNavigate}>能力草案</WorkbenchLink>
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
          `Skill ${profile.versions.skillPackageVersion}`,
          `Prompt ${profile.versions.promptVersion}`,
          `Context ${profile.versions.contextSnapshotVersion}`,
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
          ...profile.deniedActions.map((item) => item.reasonCode),
          ...profile.failureRecords,
          ...(profile.weaknessTags.length ? profile.weaknessTags.map((item) => `短板：${item}`) : ["暂无越权或失败记录"]),
        ]}
      />
    </section>
  );
}

function AgentConfigPage({ agentId, onNavigate }: { agentId: string; onNavigate: Navigate }) {
  const teamState = useTeamReadModel();
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
          <h1>能力配置草案</h1>
          <p>{agentId || config.agentId} · 只生成治理变更草案</p>
        </div>
        <WorkbenchLink className="inline-action" href="/governance/approvals/ap-001" onNavigate={onNavigate}>查看审批包</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={teamState.status} onRetry={teamState.retry} />
      <ReadModelStatusBanner status={configState.status} onRetry={configState.retry} />
      <MiniList icon={<Sparkles />} title="可编辑字段" items={config.editableFields} />
      <MetricCard icon={<LockKeyhole />} title="热改阻断" value="已阻断" detail={formatReason(config.forbiddenDirectUpdateReason)} tone="danger" />
      <MiniList icon={<GitBranch />} title="生效范围" items={config.effectiveScopeOptions.map(formatStatus)} />
      <div className="flat-panel">
        <h3><ClipboardCheck size={16} />草案提交</h3>
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
          {draftSubmitting ? "正在提交..." : "保存草案"}
        </button>
        {draftSubmitting ? (
          <p className="panel-note">正在提交能力草案，请勿重复点击。</p>
        ) : savedChangeRef ? (
          <p className="panel-note">
            已生成治理变更草案 {savedChangeRef} · 高影响，需进入 Owner 审批 · 只对后续任务生效 · 在途 AgentRun 继续使用旧快照
          </p>
        ) : draftError ? (
          <p className="panel-note danger">草案提交失败：未创建治理变更草案，请重试。</p>
        ) : (
          <p className="panel-note">提交后只生成治理变更草案，不会热改正在运行的 Agent。</p>
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
  return (
    <section className="page-grid approval-grid">
      <div className="section-header with-actions">
        <div>
          <h1>审批包</h1>
          <p>{approval.subject} · {formatReason(approval.triggerReason)}</p>
        </div>
        <WorkbenchLink className="inline-action" href={traceHref} onNavigate={onNavigate}>审计追溯</WorkbenchLink>
      </div>
      <ReadModelStatusBanner status={approvalState.status} onRetry={approvalState.retry} />
      <MetricCard icon={<ClipboardCheck />} title="推荐结论" value={formatStatus(approval.recommendation)} detail={`影响 ${formatStatus(approval.impactScope)}`} tone="gold" />
      <MiniList icon={<Layers3 />} title="对比分析" items={approval.comparisonOptions} />
      <MiniList icon={<ShieldAlert />} title="风险与影响" items={approval.riskAndImpact} />
      <MiniList
        icon={<GitBranch />}
        title="影响范围"
        items={[`适用范围：${formatStatus(approval.impactScope)} / 只对后续任务生效`, `回滚方式：${approval.rollbackRef}`, `超时${approval.timeoutDisposition}`]}
      />
      <MiniList icon={<FileSearch />} title="替代方案" items={approval.alternatives.map(formatStatus)} />
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
      <MiniList icon={<GitBranch />} title="证据引用" items={approval.evidenceRefs} />
    </section>
  );
}

function useRemoteReadModel<T>(
  fallbackFactory: () => T,
  loader: () => Promise<T>,
  deps: React.DependencyList,
): RemoteReadModel<T> {
  const [reloadToken, setReloadToken] = useState(0);
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
          setState((current) => ({ ...current, status: "error" }));
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
      <span>读取最新数据失败 · 显示上次可用数据</span>
      <button className="ghost-button" onClick={onRetry} type="button">重试</button>
    </div>
  );
}

function useTeamReadModel() {
  return useRemoteReadModel<TeamReadModel>(() => buildTeamReadModel(), loadTeamReadModel, []);
}

function useAgentProfileReadModel(agentId: string) {
  const fallback = buildTeamReadModel().agentProfileReadModels.find((item) => item.agentId === agentId)
    ?? buildTeamReadModel().agentProfileReadModels[0];
  return useRemoteReadModel<AgentProfileReadModel>(() => fallback, () => loadAgentProfileReadModel(agentId), [agentId]);
}

function useAgentCapabilityConfigReadModel(agentId: string) {
  return useRemoteReadModel<CapabilityConfigReadModel>(
    () => buildTeamReadModel().capabilityConfigReadModel,
    () => loadAgentCapabilityConfigReadModel(agentId),
    [agentId],
  );
}

function useKnowledgeReadModel() {
  return useRemoteReadModel<KnowledgeReadModel>(() => buildKnowledgeReadModel(), loadKnowledgeReadModel, []);
}

function useTraceDebugReadModel(workflowId: string) {
  return useRemoteReadModel<TraceDebugReadModel>(() => buildTraceDebugReadModel(), () => loadTraceDebugReadModel(workflowId), [workflowId]);
}

function useInvestmentDossierReadModel(workflowId: string) {
  return useRemoteReadModel<InvestmentDossierReadModel>(
    () => buildInvestmentDossierReadModel(),
    () => loadInvestmentDossierReadModel(workflowId),
    [workflowId],
  );
}

function useGovernanceReadModel() {
  return useRemoteReadModel<GovernanceReadModel>(() => buildGovernanceReadModel(), loadGovernanceReadModel, []);
}

function useFinanceOverviewReadModel() {
  return useRemoteReadModel<FinanceOverviewReadModel>(() => buildFinanceOverviewReadModel(), loadFinanceOverviewReadModel, []);
}

function useDevOpsHealthReadModel() {
  return useRemoteReadModel<DevOpsHealthReadModel>(() => buildDevOpsHealthReadModel(), loadDevOpsHealthReadModel, []);
}

function useApprovalRecordReadModel(approvalId: string) {
  return useRemoteReadModel<ApprovalRecordReadModel>(
    () => buildApprovalRecordReadModel({ approvalId }),
    () => loadApprovalRecordReadModel(approvalId),
    [approvalId],
  );
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

function formatTaskType(value: string) {
  const labels: Record<string, string> = {
    investment_workflow: "投资任务",
    research_task: "研究任务",
    finance_task: "财务任务",
    governance_task: "治理任务",
    agent_capability_change: "能力草案",
    system_task: "系统事项",
    manual_todo: "人工待办",
  };
  return labels[value] ?? value;
}

function formatChangeType(value: string) {
  const labels: Record<string, string> = {
    agent_capability: "能力草案",
    default_context: "默认上下文",
    prompt: "Prompt",
    skill_package: "Skill",
    data_source_routing: "数据源策略",
    execution_parameter: "执行参数",
  };
  return labels[value] ?? value;
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

function getGovernanceModules() {
  return [
    { label: "任务", panel: "tasks", href: "/governance?panel=tasks" },
    { label: "审批", panel: "approvals", href: "/governance?panel=approvals" },
    { label: "Agent 团队", panel: "team", href: "/governance?panel=team" },
    { label: "变更", panel: "changes", href: "/governance?panel=changes" },
    { label: "健康", panel: "health", href: "/governance?panel=health" },
    { label: "审计", panel: "audit", href: "/governance?panel=audit" },
  ];
}

function getGovernancePanel(query: Record<string, string>) {
  if (query.task === "manual") return "tasks";
  if (query.change) return "changes";
  const knownPanels = new Set(getGovernanceModules().map((module) => module.panel));
  return query.panel && knownPanels.has(query.panel) ? query.panel : "tasks";
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
    blocked: "受阻",
    completed: "完成",
    degraded: "降级",
    draft: "草案",
    failed: "失败",
    hot_patch_denied: "热改已拒绝",
    manual_only: "人工处理",
    manual_todo: "人工待办",
    monitoring: "观察中",
    new_attempt: "新尝试",
    new_task: "后续任务",
    not_started: "未开始",
    ready: "待处理",
    rejected: "拒绝",
    request_changes: "要求修改",
    researching: "研究中",
    running: "处理中",
  };
  return labels[value] ?? value;
}

function formatGuardLabel(value: string) {
  const labels: Record<string, string> = {
    "Risk blocked": "风控阻断",
    "execution_core blocked": "执行数据不足",
    "非 A 股 manual_todo": "非 A 股人工处理",
  };
  return labels[value] ?? value;
}

function formatReason(value: string) {
  const labels: Record<string, string> = {
    agent_capability_hot_patch_denied: "运行中任务不可热改",
    data_source_degraded: "数据源降级",
    execution_core_blocked_no_trade: "执行数据不足，不能成交",
    high_impact_agent_capability_change: "高影响能力变更",
    low_action_no_execution: "行动强度不足，不执行",
    non_a_asset_manual_only: "非 A 股只做人工事项",
    non_a_asset_no_trade: "非 A 股不生成交易入口",
    retained_hard_dissent_risk_review: "硬异议保留，需风控复核",
    risk_rejected_no_override: "风控拒绝，不可绕过",
  };
  return labels[value] ?? value;
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

function GuardPanel() {
  const guards = [
    ["风控拒绝", "risk_rejected_no_override"],
    ["执行数据", "execution_core_blocked_no_trade"],
    ["非 A 股", "non_a_asset_no_trade"],
    ["低行动强度", "low_action_no_execution"],
  ];
  return (
    <div className="guard-panel">
      <h3><CheckCircle2 size={16} />禁用入口</h3>
      {guards.map(([label, reason]) => (
        <div className="guard-row" key={reason}>
          <span>{label}</span>
          <strong>{formatReason(reason)}</strong>
        </div>
      ))}
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
