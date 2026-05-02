import React, { useEffect, useMemo, useState } from "react";
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
  CapabilityConfigReadModel,
  DevOpsHealthReadModel,
  FinanceOverviewReadModel,
  KnowledgeReadModel,
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
  RequestBriefApiReadModel,
  TaskCardApiReadModel,
  confirmRequestBrief,
  createRequestBrief,
  loadAgentCapabilityConfigReadModel,
  loadAgentProfileReadModel,
  loadDevOpsHealthReadModel,
  loadFinanceOverviewReadModel,
  loadKnowledgeReadModel,
  loadTeamReadModel,
  loadTraceDebugReadModel,
} from "./api";
import "./styles.css";

type Navigate = (href: string) => void;

function App() {
  const shell = buildShellReadModel();
  const [currentLocation, setCurrentLocation] = useState(`${window.location.pathname}${window.location.search}`);
  const route = useMemo(() => resolveWorkbenchRoute(currentLocation), [currentLocation]);
  const [command, setCommand] = useState("学习热点事件");
  const [commandOpen, setCommandOpen] = useState(false);
  const [generatedPreview, setGeneratedPreview] = useState<RequestBriefPreview | null>(null);
  const [requestBrief, setRequestBrief] = useState<RequestBriefApiReadModel | null>(null);
  const [confirmedTask, setConfirmedTask] = useState<string | null>(null);

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
                      setConfirmedTask(null);
                    }}
                    aria-label="自然语言请求"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setGeneratedPreview(routeOwnerCommand(command));
                      setRequestBrief(null);
                      setConfirmedTask(null);
                      createRequestBrief(command)
                        .then((brief) => setRequestBrief(brief))
                        .catch(() => {});
                    }}
                  >
                    生成请求预览
                  </button>
                </div>
                {generatedPreview ? (
                  <RequestPreviewCard
                    preview={generatedPreview}
                    confirmedTask={confirmedTask}
                    onCancel={() => {
                      setGeneratedPreview(null);
                      setRequestBrief(null);
                      setConfirmedTask(null);
                    }}
                    onConfirm={() => {
                      if (!requestBrief?.briefId) {
                        setConfirmedTask(`任务卡已生成：${generatedPreview.display.taskLabel}`);
                        return;
                      }
                      confirmRequestBrief(requestBrief.briefId, requestBrief.version)
                        .then((task: TaskCardApiReadModel) => {
                          setConfirmedTask(`任务卡已生成：${task.taskId}`);
                        })
                        .catch(() => setConfirmedTask(`任务卡已生成：${generatedPreview.display.taskLabel}`));
                    }}
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
      return <ApprovalDetailPage onNavigate={navigate} />;
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
  const dossier = buildInvestmentDossierReadModel();
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
    </section>
  );
}

function TraceDebugPage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const trace = useTraceDebugReadModel(route.params.workflowId ?? "wf-001");
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
      <MiniList icon={<Bot />} title="AgentRun 树" items={trace.agentRunTree.map((run) => `${run.runId} · ${run.stage} · ${run.profileVersion}`)} />
      <MiniList icon={<GitBranch />} title="CollaborationCommand" items={trace.commands.map((command) => `${command.commandType} · ${command.admission} · ${command.reasonCode}`)} />
      <MiniList icon={<FileSearch />} title="CollaborationEvent" items={trace.events.map((event) => `${event.eventType} · ${event.summary}`)} />
      <MiniList icon={<LockKeyhole />} title="Context 注入" items={trace.contextInjectionRecords.map((record) => `${record.contextSnapshotId} · ${record.redactionStatus} · ${record.whyIncluded}`)} />
      <MiniList icon={<Layers3 />} title="Handoff" items={trace.handoffs.map((handoff) => `${handoff.from} -> ${handoff.to} · ${handoff.blockers.join("/")}`)} />
    </section>
  );
}

function FinancePage() {
  const finance = useFinanceOverviewReadModel();
  return (
    <section className="page-grid finance-grid">
      <h1 className="sr-only">财务</h1>
      <MiniList icon={<WalletCards />} title="资产概览" items={finance.assets.map((asset) => `${asset.label} · ${asset.value} · ${formatStatus(asset.status)}`)} />
      <MetricCard icon={<ShieldAlert />} title="风险预算" value={finance.health.riskBudget} detail={`流动性 ${finance.health.liquidity} · 压力 ${finance.health.stress}`} tone="jade" />
      <MiniList icon={<AlertTriangle />} title="提醒" items={finance.reminders} />
    </section>
  );
}

function GovernanceHealthPanel() {
  const health = useDevOpsHealthReadModel();
  return (
    <div className="flat-panel list-panel" data-panel="health">
      <h3><AlertTriangle size={16} />数据/服务健康</h3>
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
  const knowledge = useKnowledgeReadModel();
  return (
    <section className="page-grid knowledge-grid">
      <h1 className="sr-only">知识</h1>
      <MiniList icon={<Brain />} title="资料集" items={knowledge.memoryCollections.map((item) => `${item.title} · ${item.resultCount} 条`)} />
      <MiniList icon={<GitBranch />} title="关联线索" items={knowledge.relationGraph.map((item) => `${item.sourceMemoryId} 支撑 ${item.targetRef}`)} />
      <div className="flat-panel">
        <h3><LockKeyhole size={16} />上下文保护</h3>
        <ul>{knowledge.contextInjectionInspector.map((item) => <li key={item.contextSnapshotId}>研究摘要已纳入 · {formatStatus(item.redactionStatus)}</li>)}</ul>
        <WorkbenchLink className="inline-action" href={knowledge.defaultContextProposalPath} onNavigate={onNavigate}>进入治理提案</WorkbenchLink>
      </div>
    </section>
  );
}

function GovernancePage({ route, onNavigate }: { route: ResolvedWorkbenchRoute; onNavigate: Navigate }) {
  const governance = buildGovernanceReadModel();
  const team = useTeamReadModel();
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
            <li>默认上下文提案 · 只对后续任务生效</li>
            <li>能力草案 gov-change-001 · 高影响待审批</li>
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
  const team = useTeamReadModel();
  return (
    <section className="page-grid team-grid">
      <div className="section-header">
        <h1>Agent 团队</h1>
      </div>
      {team.agentCards.map((agent) => (
        <article className="agent-card" key={agent.agentId}>
          <div>
            <strong>{agent.displayName}</strong>
            <span>{agent.profileVersion}</span>
          </div>
          <p>胜任度 {Math.round(agent.recentQualityScore * 100)}% · 越权 {agent.deniedActionCount}</p>
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
  const profile = useAgentProfileReadModel(agentId);
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>{profile.displayName}</h1>
        </div>
        <WorkbenchLink className="inline-action" href={`/governance/team/${profile.agentId}/config`} onNavigate={onNavigate}>能力草案</WorkbenchLink>
      </div>
      <MiniList icon={<CheckCircle2 />} title="能做什么" items={profile.canDo} />
      <MiniList icon={<ShieldAlert />} title="不能做什么" items={profile.cannotDo} />
      <MiniList icon={<ClipboardCheck />} title="质量指标" items={[`结构校验 ${profile.qualityMetrics.schemaPassRate}`, `证据质量 ${profile.qualityMetrics.evidenceQuality}`]} />
    </section>
  );
}

function AgentConfigPage({ agentId, onNavigate }: { agentId: string; onNavigate: Navigate }) {
  const team = useTeamReadModel();
  const config = useAgentCapabilityConfigReadModel(agentId);
  const draft = team.capabilityDraftSubmission;
  const [saved, setSaved] = useState(false);
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>能力配置草案</h1>
          <p>{agentId || config.agentId} · 只生成治理变更草案</p>
        </div>
        <WorkbenchLink className="inline-action" href="/governance/approvals/ap-001" onNavigate={onNavigate}>查看审批包</WorkbenchLink>
      </div>
      <MiniList icon={<Sparkles />} title="可编辑字段" items={config.editableFields} />
      <MetricCard icon={<LockKeyhole />} title="热改阻断" value="已阻断" detail={formatReason(config.forbiddenDirectUpdateReason)} tone="danger" />
      <MiniList icon={<GitBranch />} title="生效范围" items={config.effectiveScopeOptions.map(formatStatus)} />
      <div className="flat-panel">
        <h3><ClipboardCheck size={16} />草案提交</h3>
        <button className="inline-action" disabled={saved} onClick={() => setSaved(true)} type="button">保存草案</button>
        {saved ? (
          <p className="panel-note">
            已生成治理变更草案 {draft.governanceChangeRef} · 高影响，需进入 Owner 审批 · 只对后续任务生效 · 在途 AgentRun 继续使用旧快照
          </p>
        ) : (
          <p className="panel-note">提交后只生成治理变更草案，不会热改正在运行的 Agent。</p>
        )}
      </div>
    </section>
  );
}

function ApprovalDetailPage({ onNavigate }: { onNavigate: Navigate }) {
  const approval = buildApprovalRecordReadModel();
  const [submittedDecision, setSubmittedDecision] = useState<string | null>(null);
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
      <MetricCard icon={<ClipboardCheck />} title="推荐结论" value={formatStatus(approval.recommendation)} detail={`影响 ${formatStatus(approval.impactScope)}`} tone="gold" />
      <div className="flat-panel">
        <h3><Layers3 size={16} />可选动作</h3>
        <div className="command-actions">
          {approval.allowedActions.map((action) => (
            <button
              className={action === "request_changes" ? "ghost-button" : ""}
              disabled={submittedDecision !== null}
              key={action}
              onClick={() => setSubmittedDecision(action)}
              type="button"
            >
              {formatStatus(action)}
            </button>
          ))}
        </div>
        {submittedDecision ? (
          <p className="panel-note">已提交：{formatStatus(submittedDecision)} · 等待后端返回最新审批状态 · 生效范围：{formatStatus(approval.impactScope)}</p>
        ) : (
          <p className="panel-note">提交后以后端状态为准，前端只展示提交反馈，不保留乐观结论。</p>
        )}
      </div>
      <MiniList icon={<GitBranch />} title="证据引用" items={approval.evidenceRefs} />
    </section>
  );
}

function useTeamReadModel() {
  const [team, setTeam] = useState<TeamReadModel>(() => buildTeamReadModel());

  useEffect(() => {
    let cancelled = false;
    loadTeamReadModel()
      .then((payload) => {
        if (!cancelled) {
          setTeam(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return team;
}

function useAgentProfileReadModel(agentId: string) {
  const fallback = buildTeamReadModel().agentProfileReadModels.find((item) => item.agentId === agentId)
    ?? buildTeamReadModel().agentProfileReadModels[0];
  const [profile, setProfile] = useState<AgentProfileReadModel>(fallback);

  useEffect(() => {
    let cancelled = false;
    loadAgentProfileReadModel(agentId)
      .then((payload) => {
        if (!cancelled) {
          setProfile(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  return profile;
}

function useAgentCapabilityConfigReadModel(agentId: string) {
  const [config, setConfig] = useState<CapabilityConfigReadModel>(() => buildTeamReadModel().capabilityConfigReadModel);

  useEffect(() => {
    let cancelled = false;
    loadAgentCapabilityConfigReadModel(agentId)
      .then((payload) => {
        if (!cancelled) {
          setConfig(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  return config;
}

function useKnowledgeReadModel() {
  const [knowledge, setKnowledge] = useState<KnowledgeReadModel>(() => buildKnowledgeReadModel());

  useEffect(() => {
    let cancelled = false;
    loadKnowledgeReadModel()
      .then((payload) => {
        if (!cancelled) {
          setKnowledge(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return knowledge;
}

function useTraceDebugReadModel(workflowId: string) {
  const [trace, setTrace] = useState<TraceDebugReadModel>(() => buildTraceDebugReadModel());

  useEffect(() => {
    let cancelled = false;
    loadTraceDebugReadModel(workflowId)
      .then((payload) => {
        if (!cancelled) {
          setTrace(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [workflowId]);

  return trace;
}

function useFinanceOverviewReadModel() {
  const [finance, setFinance] = useState<FinanceOverviewReadModel>(() => buildFinanceOverviewReadModel());

  useEffect(() => {
    let cancelled = false;
    loadFinanceOverviewReadModel()
      .then((payload) => {
        if (!cancelled) {
          setFinance(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return finance;
}

function useDevOpsHealthReadModel() {
  const [health, setHealth] = useState<DevOpsHealthReadModel>(() => buildDevOpsHealthReadModel());

  useEffect(() => {
    let cancelled = false;
    loadDevOpsHealthReadModel()
      .then((payload) => {
        if (!cancelled) {
          setHealth(payload);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return health;
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
}: {
  preview: RequestBriefPreview;
  confirmedTask: string | null;
  onCancel: () => void;
  onConfirm: () => void;
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
      <div className="command-actions">
        {preview.status === "preview" ? <button type="button" onClick={onConfirm}>确认生成任务卡</button> : null}
        <button type="button" className="ghost-button" onClick={onCancel}>{preview.status === "preview" ? "取消" : "继续编辑"}</button>
      </div>
      {confirmedTask ? <p className="panel-note">{confirmedTask} · 等待后端确认后刷新状态</p> : null}
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
