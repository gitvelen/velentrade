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
  ResolvedWorkbenchRoute,
  buildApprovalRecordReadModel,
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
import "./styles.css";

type Navigate = (href: string) => void;

function App() {
  const shell = buildShellReadModel();
  const [pathname, setPathname] = useState(window.location.pathname);
  const route = useMemo(() => resolveWorkbenchRoute(pathname), [pathname]);
  const [command, setCommand] = useState("学习热点事件");
  const preview = useMemo(() => routeOwnerCommand(command), [command]);

  useEffect(() => {
    const onPopState = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate: Navigate = (href) => {
    const url = new URL(href, window.location.origin);
    window.history.pushState({}, "", `${url.pathname}${url.search}`);
    setPathname(url.pathname);
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
        <section className="command-band" aria-label="全局命令">
          <MessageSquareText size={18} />
          <input value={command} onChange={(event) => setCommand(event.target.value)} aria-label="全局命令输入" />
          <span className="status-chip">{preview.status === "blocked_draft" ? "需改写" : "预览"}</span>
        </section>

        <section className="page-grid command-preview compact-preview">
          <div className="section-header">
            <h2>Request Brief</h2>
            <p>{preview.taskType} · {preview.semanticLead}</p>
          </div>
          <div className="flat-panel">
            <dl>
              <dt>过程权威</dt>
              <dd>{preview.processAuthority}</dd>
              <dt>预期产物</dt>
              <dd>{preview.expectedArtifacts.join(" / ")}</dd>
              <dt>阻断原因</dt>
              <dd>{preview.reasonCode}</dd>
            </dl>
          </div>
        </section>

        {renderWorkbenchPage(route, navigate)}
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
      return <InvestmentDossierPage onNavigate={navigate} />;
    case "trace-debug":
      return <TraceDebugPage onNavigate={navigate} />;
    case "finance":
      return <FinancePage />;
    case "knowledge":
      return <KnowledgePage onNavigate={navigate} />;
    case "governance":
      return <GovernancePage onNavigate={navigate} />;
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
    <section className="page-grid overview-grid">
      <div className="section-header">
        <h1>全景</h1>
        <p>待处理、风险、审批和系统状态</p>
      </div>
      <MetricCard icon={<ShieldAlert />} title="风险阻断" value="1" detail={owner.riskSummary.blockers[0]} tone="danger" href="/investment/wf-001" onNavigate={onNavigate} />
      <MetricCard icon={<ClipboardCheck />} title="待审批" value={`${owner.approvalSummary.pending}`} detail={owner.approvalSummary.impactScope} tone="gold" href="/governance/approvals/ap-001" onNavigate={onNavigate} />
      <MetricCard icon={<WalletCards />} title="纸面账户" value={owner.paperAccount.totalValue} detail={`现金 ${owner.paperAccount.cash}`} tone="jade" href="/finance" onNavigate={onNavigate} />
      <MetricCard icon={<AlertTriangle />} title="系统健康" value={owner.systemHealth.data} detail={owner.systemHealth.incident} tone="indigo" href="/governance?panel=health" onNavigate={onNavigate} />
    </section>
  );
}

function InvestmentQueuePage({ onNavigate }: { onNavigate: Navigate }) {
  const queue = buildInvestmentQueueReadModel();
  return (
    <section className="page-grid queue-grid">
      <div className="section-header">
        <h1>投资</h1>
        <p>机会池、IC 队列、硬门槛与 Dossier 入口</p>
      </div>
      <div className="flat-panel list-panel">
        <h3><Landmark size={16} />IC 队列</h3>
        {queue.queues.map((item) => (
          <WorkbenchLink className="list-row link-row" href={item.route} key={item.workflowId} onNavigate={onNavigate}>
            <span>{item.title}</span>
            <strong>{item.stage}</strong>
            <code>{item.state}</code>
          </WorkbenchLink>
        ))}
      </div>
      <MiniList icon={<ShieldAlert />} title="Guard 摘要" items={queue.guardSummary.map((item) => `${item.label} · ${item.reasonCode}`)} />
    </section>
  );
}

function InvestmentDossierPage({ onNavigate }: { onNavigate: Navigate }) {
  const dossier = buildInvestmentDossierReadModel();
  return (
    <section className="page-grid dossier-grid">
      <div className="section-header with-actions">
        <div>
          <h1>Investment Dossier</h1>
          <p>{dossier.workflow.title} · {dossier.workflow.state}</p>
        </div>
        <WorkbenchLink className="inline-action" href={dossier.traceRoute} onNavigate={onNavigate}>查看 Trace</WorkbenchLink>
      </div>
      <div className="stage-rail">
        {dossier.stageRail.map((stage) => (
          <button className={`stage-chip ${stage.nodeStatus}`} key={stage.stage}>{stage.stage}<span>{stage.nodeStatus}</span></button>
        ))}
      </div>
      <div className="analysis-matrix">
        <h3>CIO Chair Brief</h3>
        <p>{dossier.chairBrief.decisionQuestion}</p>
        {dossier.analystStanceMatrix.map((row) => (
          <div className="matrix-row" key={row.role}>
            <span>{row.role}</span>
            <strong>{row.direction}</strong>
            <small>{Math.round(row.confidence * 100)}%</small>
            {row.hardDissent ? <em>hard dissent</em> : <i>正常</i>}
          </div>
        ))}
      </div>
      <GuardPanel />
    </section>
  );
}

function TraceDebugPage({ onNavigate }: { onNavigate: Navigate }) {
  const trace = buildTraceDebugReadModel();
  return (
    <section className="page-grid trace-grid">
      <div className="section-header with-actions">
        <div>
          <h1>Workflow Trace</h1>
          <p>{trace.workflowId} · AgentRun / Command / Handoff / ContextSlice</p>
        </div>
        <WorkbenchLink className="inline-action" href="/investment/wf-001" onNavigate={onNavigate}>返回 Dossier</WorkbenchLink>
      </div>
      <MiniList icon={<Bot />} title="AgentRun 树" items={trace.agentRunTree.map((run) => `${run.runId} · ${run.stage} · ${run.profileVersion}`)} />
      <MiniList icon={<GitBranch />} title="CollaborationCommand" items={trace.commands.map((command) => `${command.commandType} · ${command.admission} · ${command.reasonCode}`)} />
      <MiniList icon={<LockKeyhole />} title="Context 注入" items={trace.contextInjectionRecords.map((record) => `${record.contextSnapshotId} · ${record.redactionStatus} · ${record.whyIncluded}`)} />
      <MiniList icon={<Layers3 />} title="Handoff" items={trace.handoffs.map((handoff) => `${handoff.from} -> ${handoff.to} · ${handoff.blockers.join("/")}`)} />
    </section>
  );
}

function FinancePage() {
  const finance = buildFinanceOverviewReadModel();
  return (
    <section className="page-grid finance-grid">
      <div className="section-header">
        <h1>财务</h1>
        <p>全资产档案、现金流、风险预算和人工待办</p>
      </div>
      <MiniList icon={<WalletCards />} title="全资产档案" items={finance.assets.map((asset) => `${asset.label} · ${asset.value} · ${asset.status}`)} />
      <MetricCard icon={<ShieldAlert />} title="风险预算" value={finance.health.riskBudget} detail={`流动性 ${finance.health.liquidity} · 压力 ${finance.health.stress}`} tone="jade" />
      <MiniList icon={<AlertTriangle />} title="提醒" items={finance.reminders} />
    </section>
  );
}

function KnowledgePage({ onNavigate }: { onNavigate: Navigate }) {
  const knowledge = buildKnowledgeReadModel();
  return (
    <section className="page-grid knowledge-grid">
      <div className="section-header">
        <h1>知识</h1>
        <p>研究资料、经验、关系和上下文注入</p>
      </div>
      <MiniList icon={<Brain />} title="MemoryCollection" items={knowledge.memoryCollections.map((item) => `${item.title} · ${item.resultCount}`)} />
      <MiniList icon={<GitBranch />} title="关系图" items={knowledge.relationGraph.map((item) => `${item.sourceMemoryId} ${item.relationType} ${item.targetRef}`)} />
      <div className="flat-panel">
        <h3><LockKeyhole size={16} />Context 注入</h3>
        <ul>{knowledge.contextInjectionInspector.map((item) => <li key={item.contextSnapshotId}>{item.contextSnapshotId} · {item.redactionStatus}</li>)}</ul>
        <WorkbenchLink className="inline-action" href={knowledge.defaultContextProposalPath} onNavigate={onNavigate}>进入治理提案</WorkbenchLink>
      </div>
    </section>
  );
}

function GovernancePage({ onNavigate }: { onNavigate: Navigate }) {
  const governance = buildGovernanceReadModel();
  const team = buildTeamReadModel();
  return (
    <section className="page-grid governance-grid">
      <div className="section-header">
        <h1>治理</h1>
        <div className="module-tabs">
          {governance.modules.map((module) => (
            <WorkbenchLink href={module === "Agent 团队" ? "/governance/team" : "/governance"} key={module} onNavigate={onNavigate}>{module}</WorkbenchLink>
          ))}
        </div>
      </div>
      <MiniList icon={<Layers3 />} title="任务中心" items={governance.taskCenter.map((task) => `${task.taskType} · ${task.currentState} · ${task.reasonCode}`)} />
      <MiniList icon={<Landmark />} title="审批中心" items={governance.approvalCenter.map((approval) => `${approval.approvalId} · ${approval.triggerReason}`)} />
      <div className="flat-panel">
        <h3><Bot size={16} />Agent 团队</h3>
        <ul>{team.agentCards.slice(0, 5).map((agent) => <li key={agent.agentId}>{agent.displayName} · {agent.recentQualityScore}</li>)}</ul>
        <WorkbenchLink className="inline-action" href="/governance/team" onNavigate={onNavigate}>进入 Agent 团队</WorkbenchLink>
      </div>
    </section>
  );
}

function AgentTeamPage({ onNavigate }: { onNavigate: Navigate }) {
  const team = buildTeamReadModel();
  return (
    <section className="page-grid team-grid">
      <div className="section-header">
        <h1>Agent 团队</h1>
        <p>9 个正式岗位 · 草案只进治理</p>
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
  const team = buildTeamReadModel();
  const profile = team.agentProfileReadModels.find((item) => item.agentId === agentId) ?? team.agentProfileReadModels[0];
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>{profile.displayName}</h1>
          <p>能力画像、质量、权限和 CFO 归因</p>
        </div>
        <WorkbenchLink className="inline-action" href={`/governance/team/${profile.agentId}/config`} onNavigate={onNavigate}>能力草案</WorkbenchLink>
      </div>
      <MiniList icon={<CheckCircle2 />} title="能做什么" items={profile.canDo} />
      <MiniList icon={<ShieldAlert />} title="不能做什么" items={profile.cannotDo} />
      <MiniList icon={<ClipboardCheck />} title="质量指标" items={[`schema pass ${profile.qualityMetrics.schemaPassRate}`, `evidence ${profile.qualityMetrics.evidenceQuality}`]} />
    </section>
  );
}

function AgentConfigPage({ agentId, onNavigate }: { agentId: string; onNavigate: Navigate }) {
  const config = buildTeamReadModel().capabilityConfigReadModel;
  return (
    <section className="page-grid profile-grid">
      <div className="section-header with-actions">
        <div>
          <h1>能力配置草案</h1>
          <p>{agentId || config.agentId} · 只生成 Governance Change</p>
        </div>
        <WorkbenchLink className="inline-action" href="/governance/approvals/ap-001" onNavigate={onNavigate}>查看审批包</WorkbenchLink>
      </div>
      <MiniList icon={<Sparkles />} title="可编辑字段" items={config.editableFields} />
      <MetricCard icon={<LockKeyhole />} title="热改阻断" value="blocked" detail={config.forbiddenDirectUpdateReason} tone="danger" />
      <MiniList icon={<GitBranch />} title="生效范围" items={config.effectiveScopeOptions} />
    </section>
  );
}

function ApprovalDetailPage({ onNavigate }: { onNavigate: Navigate }) {
  const approval = buildApprovalRecordReadModel();
  return (
    <section className="page-grid approval-grid">
      <div className="section-header with-actions">
        <div>
          <h1>审批包</h1>
          <p>{approval.subject} · {approval.triggerReason}</p>
        </div>
        <WorkbenchLink className="inline-action" href={approval.traceRoute} onNavigate={onNavigate}>审计追溯</WorkbenchLink>
      </div>
      <MetricCard icon={<ClipboardCheck />} title="推荐结论" value={approval.recommendation} detail={`影响 ${approval.impactScope}`} tone="gold" />
      <MiniList icon={<Layers3 />} title="可选动作" items={approval.allowedActions} />
      <MiniList icon={<GitBranch />} title="证据引用" items={approval.evidenceRefs} />
    </section>
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
    ["Risk rejected", "risk_rejected_no_override"],
    ["execution_core", "execution_core_blocked_no_trade"],
    ["非 A 股", "non_a_asset_no_trade"],
    ["低行动强度", "low_action_no_execution"],
  ];
  return (
    <div className="guard-panel">
      <h3><CheckCircle2 size={16} />禁用入口</h3>
      {guards.map(([label, reason]) => (
        <div className="guard-row" key={reason}>
          <span>{label}</span>
          <code>{reason}</code>
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
