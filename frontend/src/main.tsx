import React, { useMemo, useState } from "react";
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
  buildGovernanceReadModel,
  buildInvestmentDossierReadModel,
  buildKnowledgeReadModel,
  buildOwnerDecisionReadModel,
  buildShellReadModel,
  buildTeamReadModel,
  routeOwnerCommand,
} from "./workbench";
import "./styles.css";

function App() {
  const shell = buildShellReadModel();
  const owner = buildOwnerDecisionReadModel();
  const dossier = buildInvestmentDossierReadModel();
  const governance = buildGovernanceReadModel();
  const team = buildTeamReadModel();
  const knowledge = buildKnowledgeReadModel();
  const [command, setCommand] = useState("学习热点事件");
  const preview = useMemo(() => routeOwnerCommand(command), [command]);

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">Velentrade</div>
        <nav>
          {shell.navItems.map((item) => (
            <a className={item.id === "overview" ? "active" : ""} href={item.route} key={item.id}>
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <main className="workspace">
        <section className="command-band" aria-label="全局命令">
          <MessageSquareText size={18} />
          <input value={command} onChange={(event) => setCommand(event.target.value)} aria-label="全局命令输入" />
          <span className="status-chip">{preview.status === "blocked_draft" ? "需改写" : "预览"}</span>
        </section>

        <section className="page-grid overview-grid">
          <div className="section-header">
            <h1>全景</h1>
            <p>待处理、风险、审批和系统状态</p>
          </div>
          <MetricCard icon={<ShieldAlert />} title="风险阻断" value="1" detail={owner.riskSummary.blockers[0]} tone="danger" />
          <MetricCard icon={<ClipboardCheck />} title="待审批" value={`${owner.approvalSummary.pending}`} detail={owner.approvalSummary.impactScope} tone="gold" />
          <MetricCard icon={<WalletCards />} title="纸面账户" value={owner.paperAccount.totalValue} detail={`现金 ${owner.paperAccount.cash}`} tone="jade" />
          <MetricCard icon={<AlertTriangle />} title="系统健康" value={owner.systemHealth.data} detail={owner.systemHealth.incident} tone="indigo" />
        </section>

        <section className="page-grid command-preview">
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

        <section className="page-grid dossier-grid">
          <div className="section-header">
            <h2>投资 Dossier</h2>
            <p>{dossier.workflow.title} · {dossier.workflow.state}</p>
          </div>
          <div className="stage-rail">
            {dossier.stageRail.map((stage) => (
              <button className={`stage-chip ${stage.nodeStatus}`} key={stage.stage}>{stage.stage}<span>{stage.nodeStatus}</span></button>
            ))}
          </div>
          <div className="analysis-matrix">
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

        <section className="page-grid knowledge-grid">
          <div className="section-header">
            <h2>知识</h2>
            <p>研究资料、经验、关系和上下文注入</p>
          </div>
          <MiniList icon={<Brain />} title="MemoryCollection" items={knowledge.memoryCollections.map((item) => `${item.title} · ${item.resultCount}`)} />
          <MiniList icon={<GitBranch />} title="关系图" items={knowledge.relationGraph.map((item) => `${item.sourceMemoryId} ${item.relationType} ${item.targetRef}`)} />
          <MiniList icon={<LockKeyhole />} title="Context 注入" items={knowledge.contextInjectionInspector.map((item) => `${item.contextSnapshotId} · ${item.redactionStatus}`)} />
        </section>

        <section className="page-grid governance-grid">
          <div className="section-header">
            <h2>治理</h2>
            <p>{governance.modules.join(" / ")}</p>
          </div>
          <MiniList icon={<Layers3 />} title="任务中心" items={governance.taskCenter.map((task) => `${task.taskType} · ${task.currentState}`)} />
          <MiniList icon={<Landmark />} title="审批中心" items={governance.approvalCenter.map((approval) => `${approval.approvalId} · ${approval.triggerReason}`)} />
          <MiniList icon={<Bot />} title="Agent 团队" items={team.agentCards.slice(0, 5).map((agent) => `${agent.displayName} · ${agent.recentQualityScore}`)} />
        </section>

        <section className="page-grid team-grid">
          <div className="section-header">
            <h2>Agent 团队</h2>
            <p>9 个正式岗位 · 草案只进治理</p>
          </div>
          {team.agentCards.map((agent) => (
            <article className="agent-card" key={agent.agentId}>
              <div>
                <strong>{agent.displayName}</strong>
                <span>{agent.profileVersion}</span>
              </div>
              <p>胜任度 {Math.round(agent.recentQualityScore * 100)}%</p>
              <button><FileSearch size={15} />能力草案</button>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}

function MetricCard({ icon, title, value, detail, tone }: { icon: React.ReactNode; title: string; value: string; detail: string; tone: string }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="icon-box">{icon}</div>
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
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

createRoot(document.getElementById("root")!).render(<App />);
