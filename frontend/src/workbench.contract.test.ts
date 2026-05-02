import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";

import {
  buildReportEnvelope,
  buildGovernanceReadModel,
  buildRouteManifest,
  buildShellReadModel,
  buildTeamReadModel,
  buildWorkbenchReports,
  resolveWorkbenchRoute,
  routeOwnerCommand,
} from "./workbench";

describe("WI-004 workbench contracts", () => {
  it("uses the approved Chinese top navigation and keeps Agent team under governance", () => {
    const shell = buildShellReadModel();

    expect(shell.navItems.map((item) => item.label)).toEqual(["全景", "投资", "财务", "知识", "治理"]);
    expect(shell.navItems.map((item) => item.label)).not.toContain("团队");
    expect(shell.governanceModules).toContain("Agent 团队");
  });

  it("maps every approved navigation and drill-down route to a distinct workbench page", () => {
    const manifest = buildRouteManifest();

    expect(manifest.map((route) => route.path)).toEqual([
      "/",
      "/investment",
      "/investment/:workflowId",
      "/investment/:workflowId/trace",
      "/finance",
      "/knowledge",
      "/governance",
      "/governance/team",
      "/governance/team/:agentId",
      "/governance/team/:agentId/config",
      "/governance/approvals/:approvalId",
    ]);
    expect(resolveWorkbenchRoute("/investment/wf-001").page).toBe("investment-dossier");
    expect(resolveWorkbenchRoute("/investment/wf-001?stage=S5").query.stage).toBe("S5");
    expect(resolveWorkbenchRoute("/investment/wf-001/trace").page).toBe("trace-debug");
    expect(resolveWorkbenchRoute("/governance?panel=health").query.panel).toBe("health");
    expect(resolveWorkbenchRoute("/governance/team/quant_analyst/config").page).toBe("agent-config");
    expect(resolveWorkbenchRoute("/governance/approvals/ap-001").page).toBe("approval-detail");
    expect(resolveWorkbenchRoute("/unknown").page).toBe("not-found");
  });

  it("routes owner commands through request brief previews instead of direct actions", () => {
    const research = routeOwnerCommand("学习热点事件");
    const directTrade = routeOwnerCommand("帮我下单买入腾讯");
    const ambiguous = routeOwnerCommand("帮我处理一下");
    const hotPatch = routeOwnerCommand("把量化分析的 Prompt 直接生效");

    expect(research.taskType).toBe("research_task");
    expect(research.semanticLead).toBe("Investment Researcher");
    expect(research.blockedDirectActions).toContain("no_trade_or_approval_entry");
    expect(research.display.taskLabel).toBe("热点研究");
    expect(research.display.leadLabel).toBe("投资研究员");
    expect(research.display.boundaryLabel).toBe("只做研究，不进入审批或交易");
    expect(directTrade.status).toBe("blocked_draft");
    expect(directTrade.reasonCode).toBe("non_a_asset_no_trade");
    expect(directTrade.display.statusLabel).toBe("需补充");
    expect(ambiguous.status).toBe("draft");
    expect(ambiguous.display.taskLabel).toBe("待补充请求");
    expect(ambiguous.clarificationPrompts).toEqual([
      "请补充目标对象或主题",
      "请补充希望产出的结果",
      "请说明是否只做研究、审批还是人工跟进",
    ]);
    expect(hotPatch.status).toBe("blocked_draft");
    expect(hotPatch.reasonCode).toBe("agent_capability_hot_patch_denied");
    expect(hotPatch.display.statusLabel).toBe("已阻断");
  });

  it("keeps free-form command as a collapsed topbar drawer instead of page content", () => {
    const shell = buildShellReadModel();

    expect(shell.commandLayer).toEqual({
      placement: "topbar_drawer",
      defaultExpanded: false,
      pageNarrativeIntrusion: false,
      previewTitle: "请求预览",
    });
  });

  it("keeps owner default copy free of internal process terms and explanatory page subtitles", () => {
    const reports = buildWorkbenchReports();
    const ownerContent = reports["web_command_routing_report.json"].owner_facing_content_assertions as {
      forbidden_terms_absent: string[];
      removed_page_subtitles: string[];
    };

    expect(ownerContent.forbidden_terms_absent).toEqual([
      "Request Brief",
      "research_task",
      "supporting_evidence_only",
      "Workflow Scheduling Center",
      "schema pass",
      "Governance Change",
    ]);
    expect(ownerContent.removed_page_subtitles).toContain("待处理、风险、审批和系统状态");
  });

  it("separates task center, approval center, manual todo and hot patch denials", () => {
    const governance = buildGovernanceReadModel();

    expect(governance.taskCenter.map((task) => task.taskType)).toContain("manual_todo");
    expect(governance.approvalCenter.every((approval) => approval.kind === "approval")).toBe(true);
    expect(governance.manualTodoIsolation.connectedToS5S6).toBe(false);
    expect(governance.uiGuardResponses.riskRejected.actionVisible).toBe(false);
    expect(governance.uiGuardResponses.agentCapabilityHotPatch.reasonCode).toBe("agent_capability_hot_patch_denied");
  });

  it("exposes nine Agent cards and draft-only capability configuration", () => {
    const team = buildTeamReadModel();

    expect(team.agentCards).toHaveLength(9);
    expect(team.agentCards.every((card) => card.configDraftEntry === "governance_draft_only")).toBe(true);
    expect(team.capabilityConfigReadModel.forbiddenDirectUpdateReason).toBe("hot_patch_denied");
    expect(team.capabilityDraftSubmission.state).toBe("draft");
  });

  it("builds all WI-004 verification reports with required payload fields", () => {
    const reports = buildWorkbenchReports();

    expect(Object.keys(reports).sort()).toEqual([
      "governance_task_report.json",
      "team_capability_config_report.json",
      "web_command_routing_report.json",
    ]);
    expect(reports["web_command_routing_report.json"].nav_scan.top_level_labels).toEqual(["全景", "投资", "财务", "知识", "治理"]);
    expect(reports["web_command_routing_report.json"].draft_clarification_prompts).toEqual([
      "请补充目标对象或主题",
      "请补充希望产出的结果",
      "请说明是否只做研究、审批还是人工跟进",
    ]);
    expect(reports["web_command_routing_report.json"].trace_entry_return_path.from_approval_detail).toBe(
      "/investment/wf-001/trace?returnTo=%2Fgovernance%2Fapprovals%2Fap-001",
    );
    expect(reports["governance_task_report.json"].agent_capability_hot_patch_denial.reason_code).toBe(
      "agent_capability_hot_patch_denied",
    );
    expect(reports["team_capability_config_report.json"].in_flight_agent_run_snapshot_unchanged).toBe(true);
  });

  it("marks WI-004 verification reports failed when a guard or failure fails", () => {
    const report = buildReportEnvelope(
      "web_command_routing_report.json",
      "TC-ACC-006-01",
      "ACC-006",
      { probe: "negative" },
      {
        guardResults: [
          {
            guard: "button_feedback",
            input_ref: "save-capability-draft",
            expected: "visible_feedback",
            actual: "no_feedback",
            result: "fail",
          },
        ],
        failures: [
          {
            code: "button_without_feedback",
            message: "button click produced no visible feedback",
            evidence_ref: "save-capability-draft",
          },
        ],
      },
    );

    expect(report.result).toBe("fail");
    expect(report.failures).toHaveLength(1);
  });

  it("does not leave enabled buttons without feedback handlers", () => {
    const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf-8");
    const buttonBlocks = [...source.matchAll(/<button\b[\s\S]*?<\/button>/g)].map((match) => match[0]);

    const noFeedbackButtons = buttonBlocks.filter((button) => !button.includes("onClick=") && !button.includes("disabled"));

    expect(noFeedbackButtons).toEqual([]);
  });
});
