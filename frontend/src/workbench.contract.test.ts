import { describe, expect, it } from "vitest";

import {
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
    expect(resolveWorkbenchRoute("/investment/wf-001/trace").page).toBe("trace-debug");
    expect(resolveWorkbenchRoute("/governance/team/quant_analyst/config").page).toBe("agent-config");
    expect(resolveWorkbenchRoute("/governance/approvals/ap-001").page).toBe("approval-detail");
    expect(resolveWorkbenchRoute("/unknown").page).toBe("not-found");
  });

  it("routes owner commands through request brief previews instead of direct actions", () => {
    const research = routeOwnerCommand("学习热点事件");
    const directTrade = routeOwnerCommand("帮我下单买入腾讯");

    expect(research.taskType).toBe("research_task");
    expect(research.semanticLead).toBe("Investment Researcher");
    expect(research.blockedDirectActions).toContain("no_trade_or_approval_entry");
    expect(directTrade.status).toBe("blocked_draft");
    expect(directTrade.reasonCode).toBe("non_a_asset_no_trade");
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
    expect(reports["governance_task_report.json"].agent_capability_hot_patch_denial.reason_code).toBe(
      "agent_capability_hot_patch_denied",
    );
    expect(reports["team_capability_config_report.json"].in_flight_agent_run_snapshot_unchanged).toBe(true);
  });
});
