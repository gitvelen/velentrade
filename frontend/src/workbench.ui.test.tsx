// @vitest-environment jsdom
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

async function bootWorkbench(path: string) {
  vi.resetModules();
  document.body.innerHTML = '<div id="root"></div>';
  window.history.replaceState({}, "", path);
  await act(async () => {
    await import("./main");
  });
}

function buttonByName(name: string) {
  const button = Array.from(document.querySelectorAll("button")).find((item) =>
    item.textContent?.includes(name),
  );
  if (!button) {
    throw new Error(`button not found: ${name}`);
  }
  return button as HTMLButtonElement;
}

function detailRowByText(name: string) {
  const row = Array.from(document.querySelectorAll('[role="button"]')).find((item) =>
    item.textContent?.includes(name),
  );
  if (!row) {
    throw new Error(`detail row not found: ${name}`);
  }
  return row as HTMLElement;
}

function linkByName(name: string) {
  const link = Array.from(document.querySelectorAll("a")).find((item) =>
    item.textContent?.includes(name),
  );
  if (!link) {
    throw new Error(`link not found: ${name}`);
  }
  return link as HTMLAnchorElement;
}

function inputByLabel(name: string) {
  const input = Array.from(document.querySelectorAll("input, textarea")).find((item) =>
    item.getAttribute("aria-label")?.includes(name),
  );
  if (!input) {
    throw new Error(`input not found: ${name}`);
  }
  return input as HTMLInputElement | HTMLTextAreaElement;
}

function summaryCardByTitle(title: string) {
  const card = Array.from(document.querySelectorAll(".summary-card, .summary-focus-item")).find((item) =>
    item.querySelector(".summary-card-heading span")?.textContent?.includes(title),
  ) ?? Array.from(document.querySelectorAll(".summary-focus-item")).find((item) => item.textContent?.includes(title));
  if (!card) {
    throw new Error(`summary card not found: ${title}`);
  }
  return card as HTMLElement;
}

function stageSummaryCards() {
  return Array.from(document.querySelectorAll(".stage-summary-grid > .summary-card")) as HTMLElement[];
}

function stageSummaryCardTitles() {
  return stageSummaryCards().map((card) => card.querySelector(".summary-card-heading span")?.textContent);
}

async function openSummaryDetail(title: string) {
  await act(async () => {
    summaryCardByTitle(title).click();
  });
  await flushAsyncWork();
  const sheet = document.querySelector(".dossier-detail-sheet") as HTMLElement | null;
  if (!sheet) {
    throw new Error(`detail sheet not found after clicking ${title}`);
  }
  return sheet;
}

function detailBlockText() {
  return Array.from(document.querySelectorAll(".dossier-detail-sheet .detail-block"))
    .map((item) => item.textContent ?? "")
    .join("|");
}

function directPanelTitles() {
  return Array.from(document.querySelectorAll(".direct-info-panel h3")).map((item) => item.textContent);
}

function expectOwnerDefaultTextClean(text: string) {
  for (const token of ["AgentRun", "ContextSnapshot", "DecisionPacket", "trace_id", "reason_code", "artifact-", "ctx-"]) {
    expect(text).not.toContain(token);
  }
}

function setInputValue(input: HTMLInputElement | HTMLTextAreaElement, value: string) {
  const prototype = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");
  descriptor?.set?.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function mockJsonResponse(data: unknown) {
  return {
    ok: true,
    json: async () => ({ data, meta: { trace_id: "trace-1", generated_at: "2026-05-02T00:00:00Z" } }),
  } as Response;
}

function mockDossierReadModel() {
  return {
    workflow: { workflow_id: "wf-001", title: "浦发银行 A 股研究", current_stage: "S3", state: "blocked" },
    stage_rail: ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"].map((stage) => ({
      stage,
      node_status: stage === "S3" ? "blocked" : stage < "S3" ? "completed" : "not_started",
      reason_code: stage === "S3" ? "retained_hard_dissent_risk_review" : null,
      artifact_count: stage < "S3" ? 1 : 0,
    })),
    chair_brief: { decision_question: "是否值得围绕浦发银行进入完整 IC 论证", key_tensions: ["硬异议保留"], no_preset_decision_attestation: true },
    analyst_stance_matrix: [
      { role: "macro", direction: "positive", confidence: 0.72, evidence_quality: 0.76, hard_dissent: false },
      {
        role: "fundamental",
        direction: "neutral",
        confidence: 0.68,
        evidence_quality: 0.62,
        hard_dissent: true,
        hard_dissent_reason: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
      },
      { role: "quant", direction: "positive", confidence: 0.74, evidence_quality: 0.78, hard_dissent: false },
      { role: "event", direction: "neutral", confidence: 0.61, evidence_quality: 0.72, hard_dissent: false },
    ],
    data_readiness: {
      quality_band: "partial",
      decision_core_status: "pass",
      execution_core_status: "blocked",
      issues: ["分钟级执行数据不足，S6 不允许成交。"],
      lineage_refs: ["tencent-public-kline:600000.SH"],
      owner_summary: "S1 已拿到可用于研究的数据；成交前还缺 S6 执行核心数据。",
      source_status: [
        {
          source_name: "腾讯公开日线行情",
          source_ref: "tencent-public-kline:600000.SH",
          required_usage: "decision_core",
          requested_fields: ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
          obtained_fields: ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
          missing_fields: [],
          status: "available",
          quality_label: "可用于研究判断",
          evidence_ref: "tencent-public-kline:600000.SH",
        },
        {
          source_name: "实时执行行情",
          source_ref: "execution-core:600000.SH",
          required_usage: "execution_core",
          requested_fields: ["最新成交价", "盘口深度", "可成交窗口"],
          obtained_fields: [],
          missing_fields: ["最新成交价", "盘口深度", "可成交窗口"],
          status: "missing",
          quality_label: "缺失，不能用于成交",
          evidence_ref: "execution-core:600000.SH",
        },
      ],
      data_gaps: [
        {
          gap: "实时执行行情缺失",
          affects_stage: "S6",
          impact: "不能生成纸面成交授权，不影响当前 S3 硬异议判断。",
          next_action: "进入 S6 前重新采集最新成交价、盘口深度和可成交窗口，并由风控复核。",
        },
      ],
    },
    role_payload_drilldowns: [
      {
        role: "macro",
        highlights: ["宏观环境支持观察", "利率和政策环境尚未构成反对理由"],
        thesis: "宏观环境支持观察，但不能替代个股资产质量补证。",
        supporting_evidence_refs: ["artifact-wf001-macro"],
        key_risks: ["宽信用落地慢于预期"],
        applicable_conditions: ["宏观环境稳定且银行板块风险偏好未恶化"],
        invalidation_conditions: ["政策预期转弱或信用利差快速走阔"],
        suggested_action_implication: "宏观不阻断，但不单独推动进入 S4。",
        role_payload: { policy: "supportive", liquidity: "watch" },
      },
      {
        role: "fundamental",
        highlights: ["资产质量修复证据不足", "需要补充不良率、拨备覆盖率和息差趋势"],
        hard_dissent_reason: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
        thesis: "估值低位不能单独支持推进，需要看到资产质量和息差同时改善。",
        supporting_evidence_refs: ["artifact-wf001-data-readiness"],
        counter_evidence_refs: ["source-wf001-fundamental-npl", "source-wf001-fundamental-nim"],
        key_risks: ["不良率拐点未确认", "息差修复慢于预期"],
        applicable_conditions: ["补齐最近两个季度资产质量数据后再进入 S4"],
        invalidation_conditions: ["不良率继续上行或拨备覆盖率继续下降"],
        suggested_action_implication: "S3 先补证，保留硬异议并交风控复核。",
        role_payload: { asset_quality: "insufficient", valuation_gap: "needs_confirmation" },
      },
      {
        role: "quant",
        highlights: ["因子信号偏正面", "辩论后降为观察"],
        thesis: "趋势和因子仍偏正面，但补证前不支持推进执行。",
        supporting_evidence_refs: ["artifact-wf001-quant"],
        key_risks: ["拥挤度上升"],
        applicable_conditions: ["基本面补证完成后再恢复偏正面权重"],
        invalidation_conditions: ["量价跌破观察区间"],
        suggested_action_implication: "维持观察，不单独推动 S4。",
        role_payload: { factor_signal: "positive", timing: "watch" },
      },
      {
        role: "event",
        highlights: ["暂无强催化", "公告和监管信息未形成放行依据"],
        thesis: "暂无强催化，事件侧只支持观察。",
        supporting_evidence_refs: ["artifact-wf001-event"],
        key_risks: ["后续监管公告改变风险定价"],
        applicable_conditions: ["公告未新增负面事件"],
        invalidation_conditions: ["监管处罚或资产质量负面公告出现"],
        suggested_action_implication: "继续跟踪公告，不单独推动 S4。",
        role_payload: { catalyst: "weak", monitor: "announcement" },
      },
    ],
    consensus: { consensus_score: 0.75, action_conviction: 0.6, threshold_label: "需补证" },
    debate: {
      rounds_used: 2,
      retained_hard_dissent: true,
      risk_review_required: true,
      issues: ["资产质量修复是否足以抵消估值低位"],
      view_changes: ["量化观点由偏正面降为观察；基本面仍保留硬异议"],
      cio_synthesis: "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
      unresolved_dissent: ["基本面硬异议仍保留"],
      rounds: [
        { round_no: 1, issue: "资产质量修复是否成立", outcome: "要求补充不良率和拨备证据" },
        { round_no: 2, issue: "补证后是否能进入 S4", outcome: "CIO synthesis 维持 S3 受阻" },
      ],
      owner_summary: "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
      status_summary: {
        rounds_used: 2,
        retained_hard_dissent: true,
        risk_review_required: true,
        consensus_score: 0.75,
        action_conviction: 0.6,
      },
      core_disputes: [
        {
          title: "资产质量修复是否足以抵消估值低位",
          why_it_matters: "如果资产质量没有确认修复，低估值可能是价值陷阱，不能直接进入 S4 决策。",
          involved_roles: ["基本面分析师", "量化分析师", "CIO"],
          current_conclusion: "补证前不能进入 S4，先保留 S3 阻断。",
          required_evidence: ["不良率趋势", "拨备覆盖率趋势", "息差改善证据"],
        },
      ],
      view_change_details: [
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
      retained_dissent_details: [
        {
          source_role: "基本面分析师",
          dissent: "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
          counter_risks: ["不良率拐点未确认", "拨备覆盖率可能继续承压", "息差修复慢于预期"],
          handling: "保留硬异议，补证后交风控复核。",
          forbidden_actions: ["不能直接放行 S4", "不能进入 S6 执行"],
        },
      ],
      round_details: [
        {
          round_no: 1,
          issue: "资产质量修复是否成立",
          participants: ["CIO", "基本面分析师", "量化分析师"],
          input_evidence: ["不良率趋势", "拨备覆盖率"],
          outcome: "要求补充不良率和拨备证据",
          unresolved_questions: ["资产质量修复证据是否足够"],
        },
        {
          round_no: 2,
          issue: "补证后是否能进入 S4",
          participants: ["CIO", "基本面分析师", "量化分析师"],
          input_evidence: ["息差趋势", "估值分位"],
          outcome: "CIO 维持 S3 受阻",
          unresolved_questions: ["补证后是否足以解除基本面硬异议"],
        },
      ],
      next_actions: [
        {
          action: "补齐资产质量、拨备覆盖率和息差趋势证据",
          owner: "基本面分析师",
          completion_signal: "形成可复核补证包并更新硬异议判断",
          next_stage: "交风控复核后再判断是否进入 S4",
        },
      ],
    },
    optimizer_deviation: { single_name_deviation: "待定", portfolio_deviation: "待定", recommendation: "先补证" },
    risk_review: {
      review_result: "blocked",
      repairability: "reopen_s3_debate",
      owner_exception_required: false,
      reason_codes: ["retained_hard_dissent_risk_review", "execution_core_blocked_no_trade"],
    },
    paper_execution: { status: "blocked", pricing_method: "not_released", window: "不可用", fees: {}, t_plus_one: "not_started" },
    attribution: { summary: "暂无归因。", links: [] },
    evidence_map: {
      data_refs: ["tencent-public-kline:600000.SH"],
      source_quality: [
        {
          source: "腾讯公开日线行情",
          used_for: "支持判断：是否值得继续分析浦发银行",
          quality: "可用于研究判断",
        },
      ],
      conflict_refs: ["分钟级成交数据缺失"],
    },
    forbidden_actions: { execution_core_blocked_no_trade: { action_visible: false, reason_code: "execution_core_blocked_no_trade" } },
  };
}

function defaultFetch(input: string | URL | Request, init?: RequestInit): Promise<Response> {
  const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
  if (href.endsWith("/api/workflows/wf-001/dossier")) return Promise.resolve(mockJsonResponse(mockDossierReadModel()));
  if (href.endsWith("/api/tasks")) return Promise.resolve(mockJsonResponse({ task_center: [] }));
  if (href.endsWith("/api/approvals")) {
    return Promise.resolve(mockJsonResponse({
      approval_center: [
        {
          approval_id: "ap-001",
          approval_type: "agent_capability_change",
          subject: "量化分析能力提升方案",
          trigger_reason: "high_impact_agent_capability_change",
          recommended_decision: "request_changes",
          effective_scope: "new_task",
          comparison_options: ["维持当前能力版本", "降低模型路由风险后重提"],
          risk_and_impact: ["影响量化分析后续研究质量", "不改变在途任务"],
          timeout_policy: "不生效",
          rollback_ref: "gov-change-001",
          evidence_refs: ["team_capability_config_report.json"],
          trace_route: "/investment/wf-001/trace",
          allowed_actions: ["approved", "rejected", "request_changes"],
        },
      ],
    }));
  }
  if (href.endsWith("/api/governance/changes")) {
    return Promise.resolve(mockJsonResponse([
      { change_id: "gov-change-001", change_type: "agent_capability", impact_level: "high", state: "owner_pending", effective_scope: "new_task" },
    ]));
  }
  if (href.endsWith("/api/finance/overview")) {
    return Promise.resolve(mockJsonResponse({
      asset_profile: [{ asset_type: "cash", valuation: { amount: 1000000, currency: "CNY" }, boundary_label: "可用" }],
      finance_health: { liquidity: 1000000, risk_budget: { budget_ref: "risk-budget-finance-v1" }, stress_test_summary: "可承受" },
      manual_todo: [],
    }));
  }
  if (href.endsWith("/api/devops/health")) {
    return Promise.resolve(mockJsonResponse({ routine_checks: [{ check_id: "metric-collection", status: "observed" }], incidents: [], recovery: [], metrics: {} }));
  }
  if (href.endsWith("/api/knowledge/memory-items") && init?.method !== "POST") {
    return Promise.resolve(mockJsonResponse([
      {
        memory_id: "memory-api-1",
        current_version_id: "version-api-1",
        title: "后续研究资料需要保留来源、标签和适用边界。",
        summary: "后续研究资料需要保留来源、标签和适用边界。",
        status: "validated_context",
        promotion_state: "validated_context",
        sensitivity: "public_internal",
        tags: ["研究复盘"],
        source_refs: ["owner-note-real"],
        relations: [{ relation_id: "relation-api-1", target_ref: "artifact-research-1", relation_type: "supports", reason: "API relation", evidence_refs: ["artifact-research-1"] }],
        why_included: "fenced_background_context_only",
      },
    ]));
  }
  if (href.endsWith("/api/workflows/wf-001/agent-runs")) return Promise.resolve(mockJsonResponse([]));
  if (href.endsWith("/api/workflows/wf-001/collaboration-events")) return Promise.resolve(mockJsonResponse([]));
  if (href.endsWith("/api/workflows/wf-001/handoffs")) return Promise.resolve(mockJsonResponse([]));
  return Promise.resolve(mockJsonResponse({}));
}

function stubDossierResponse(workflowId: string, dossier: unknown) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
    if (href.endsWith(`/api/workflows/${workflowId}/dossier`)) {
      return mockJsonResponse(dossier);
    }
    return defaultFetch(input, init);
  }));
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("WI-004 workbench interactions", () => {
  beforeEach(() => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    vi.stubGlobal("fetch", vi.fn(defaultFetch));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("generates a simple request preview only after the owner clicks the preview button", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-preview",
          route_type: "research_task",
          version: 1,
        });
      }
      return defaultFetch(input);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });

    expect(document.body.textContent).toContain("输入一句话后生成预览");
    expect(document.body.textContent).not.toContain("系统会安排热点研究");

    await act(async () => {
      buttonByName("生成请求预览").click();
    });

    expect(document.body.textContent).toContain("系统会安排热点研究");
    expect(document.body.textContent).toContain("负责人：投资研究员");
    expect(document.body.textContent).toContain("不会进入审批或交易");
    expect(document.body.textContent).toContain("下一步：确认后生成研究任务卡");
  });

  it("renders the request brief preview fields required by the command layer design", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-fields",
          route_type: "research_task",
          suggested_semantic_lead: "investment_researcher",
          process_authority: "workflow_scheduling_center",
          predicted_outputs: ["ResearchPackage", "MemoryCapture", "TopicProposalCandidate"],
          forbidden_action_reason_code: "supporting_evidence_only",
          owner_confirmation_status: "draft",
          version: 1,
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      const input = inputByLabel("自然语言请求");
      setInputValue(input, "学习美伊热点事件");
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("目标：热点事件研究");
    expect(document.body.textContent).toContain("范围：学习美伊热点事件");
    expect(document.body.textContent).toContain("资产边界：只做研究，不进入审批或交易");
    expect(document.body.textContent).toContain("任务类型：研究任务");
    expect(document.body.textContent).toContain("建议负责人：投资研究员");
    expect(document.body.textContent).toContain("过程权威：流程调度");
    expect(document.body.textContent).toContain("预期产物：研究资料包 / 记忆摘录 / 候选议题");
    expect(document.body.textContent).toContain("优先级：普通");
    expect(document.body.textContent).toContain("授权边界：只能生成研究任务卡");
    expect(document.body.textContent).toContain("成功标准：形成可复用研究资料和候选议题");
    expect(document.body.textContent).toContain("阻断条件：不生成审批、执行或交易入口");
    expect(document.body.textContent).toContain("审批可能性：通常不触发审批");
  });

  it("uses the API route type as the request brief source of truth", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-manual",
          route_type: "manual_todo",
          suggested_semantic_lead: "owner",
          process_authority: "task_center",
          predicted_outputs: ["ManualTodo"],
          forbidden_action_reason_code: "asset_scope_unclear",
          owner_confirmation_status: "draft",
          version: 1,
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      const input = inputByLabel("自然语言请求");
      setInputValue(input, "学习热点但先让我人工确认资产范围");
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("系统会安排人工事项");
    expect(document.body.textContent).toContain("任务类型：人工待办");
    expect(document.body.textContent).toContain("建议负责人：老板确认");
    expect(document.body.textContent).not.toContain("系统会安排热点研究");
  });

  it("does not show an arranged request preview when the request brief API fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        throw new Error("api unavailable");
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("请求预览生成失败");
    expect(document.body.textContent).not.toContain("系统会安排热点研究");
    expect(document.body.textContent).not.toContain("确认生成任务卡");
  });

  it("disables duplicate request preview clicks while syncing with the API", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return await new Promise<Response>(() => {});
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });

    expect(buttonByName("正在生成预览").disabled).toBe(true);
    expect(document.body.textContent).toContain("正在向 API 生成请求预览");
  });

  it("creates a request brief through the API and confirms it through the confirmation endpoint", async () => {
    const fetchSpy = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          brief_id: "brief-api-1",
          route_type: "research_task",
          suggested_semantic_lead: "investment_researcher",
          process_authority: "workflow_scheduling_center",
          predicted_outputs: ["ResearchPackage", "MemoryCapture"],
          forbidden_action_reason_code: null,
          owner_confirmation_status: "draft",
          version: 1,
        });
      }
      if (href.endsWith("/api/requests/briefs/brief-api-1/confirmation")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          task_id: "task-api-1",
          task_type: "research_task",
          current_state: "ready",
          reason_code: "request_brief_confirmed",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    });
    vi.stubGlobal("fetch", fetchSpy);

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();
    await act(async () => {
      buttonByName("确认生成任务卡").click();
    });
    await flushAsyncWork();

    expect(fetchSpy).toHaveBeenCalledWith("/api/requests/briefs", expect.objectContaining({ method: "POST" }));
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/requests/briefs/brief-api-1/confirmation",
      expect.objectContaining({ method: "POST" }),
    );
    expect(document.body.textContent).toContain("任务卡已生成：task-api-1");
  });

  it("does not claim a task card was generated when confirmation fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-fail",
          route_type: "research_task",
          suggested_semantic_lead: "investment_researcher",
          process_authority: "workflow_scheduling_center",
          predicted_outputs: ["ResearchPackage"],
          owner_confirmation_status: "draft",
          version: 1,
        });
      }
      if (href.endsWith("/api/requests/briefs/brief-api-fail/confirmation")) {
        return { ok: false, json: async () => ({ error: { code: "SERVICE_UNAVAILABLE" } }) } as Response;
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();
    await act(async () => {
      buttonByName("确认生成任务卡").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("任务卡生成失败，请重试");
    expect(document.body.textContent).not.toContain("任务卡已生成：热点研究");
  });

  it("links confirmed investment tasks to the live investment dossier read model", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          brief_id: "brief-investment-1",
          route_type: "investment_workflow",
          suggested_semantic_lead: "cio",
          process_authority: "workflow_scheduling_center",
          predicted_outputs: ["ICChairBrief", "DecisionPacket"],
          forbidden_action_reason_code: null,
          owner_confirmation_status: "draft",
          version: 1,
        });
      }
      if (href.endsWith("/api/requests/briefs/brief-investment-1/confirmation")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          task_id: "task-investment-1",
          task_type: "investment_workflow",
          current_state: "ready",
          reason_code: "request_brief_confirmed",
          workflow_id: "workflow-api-1",
        });
      }
      if (href.endsWith("/api/workflows/workflow-api-1/dossier")) {
        return mockJsonResponse({
          workflow: {
            workflow_id: "workflow-api-1",
            title: "API 投资档案",
            current_stage: "S0",
            state: "running",
          },
          stage_rail: [{ stage: "S0", node_status: "not_started", reason_code: null, artifact_count: 0 }],
          chair_brief: {
            decision_question: "是否进入正式 IC",
            key_tensions: ["真实 API 链路"],
            no_preset_decision_attestation: true,
          },
          analyst_stance_matrix: [],
          forbidden_actions: {},
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });
    await act(async () => {
      const input = inputByLabel("自然语言请求");
      setInputValue(input, "请正式研究浦发银行");
    });
    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();
    await act(async () => {
      buttonByName("确认生成任务卡").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("任务卡已生成：task-investment-1");

    await act(async () => {
      linkByName("打开投资档案").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/investment/workflow-api-1");
    expect(document.body.textContent).toContain("API 投资档案");
    expect(document.body.textContent).toContain("IC：S0 接收运行中");
    expect(document.body.textContent).not.toContain("只切换查看阶段，不推进流程");
  });

  it("keeps vague owner commands in draft and asks concise clarification questions", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-clarify",
          route_type: "manual_todo",
          version: 1,
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });

    await act(async () => {
      const input = inputByLabel("自然语言请求");
      setInputValue(input, "帮我处理一下");
    });

    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("还缺这些信息");
    expect(document.body.textContent).toContain("请补充目标对象或主题");
    expect(document.body.textContent).toContain("请补充希望产出的结果");
    expect(document.body.textContent).not.toContain("确认生成任务卡");
  });

  it("blocks hot patch requests in free chat and shows the governance boundary", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/requests/briefs")) {
        return mockJsonResponse({
          brief_id: "brief-api-hot-patch",
          route_type: "agent_capability_change",
          version: 1,
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");

    await act(async () => {
      buttonByName("自由对话").click();
    });

    await act(async () => {
      const input = inputByLabel("自然语言请求");
      setInputValue(input, "把量化分析的 Prompt 直接生效");
    });

    await act(async () => {
      buttonByName("生成请求预览").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("还缺这些信息");
    expect(document.body.textContent).toContain("不能热改运行中的 Agent");
    expect(document.body.textContent).toContain("原因：运行中任务不可热改");
    expect(document.body.textContent).not.toContain("确认生成任务卡");
  });

  it("keeps top-level pages free of duplicate visible menu headings", async () => {
    const cases = [
      ["/investment", "投资"],
      ["/finance", "财务"],
      ["/knowledge", "知识"],
      ["/governance", "治理"],
    ];

    for (const [path, label] of cases) {
      await bootWorkbench(path);

      const visibleHeadings = Array.from(document.querySelectorAll("h1"))
        .filter((heading) => !heading.classList.contains("sr-only"))
        .map((heading) => heading.textContent?.trim());

      expect(visibleHeadings).not.toContain(label);
    }
  });

  it("selects a dossier stage by updating the URL query without advancing workflow state", async () => {
    await bootWorkbench("/investment/wf-001");

    await act(async () => {
      buttonByName("S5").click();
    });

    expect(window.location.pathname).toBe("/investment/wf-001");
    expect(window.location.search).toBe("?stage=S5");
    expect(buttonByName("S5").getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector(".dossier-status-line")?.textContent).toContain("IC：S3 辩论受阻");
    expect(document.body.textContent).toContain("风控拒绝，可修复");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
    expect(document.body.textContent).not.toContain("当前阶段：S5");
    expect(document.body.textContent).not.toContain("当前阶段摘要");
    expect(document.body.textContent).not.toContain("当前详情");
    expect(document.body.textContent).not.toContain("当前查看：S5 风控复核");
    expect(document.body.textContent).not.toContain("只切换查看阶段，不推进流程");
  });

  it("loads the wf-001 dossier from the real dossier API instead of local preview data", async () => {
    const fetchSpy = vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/workflows/wf-001/dossier")) {
        return mockJsonResponse(mockDossierReadModel());
      }
      return defaultFetch(input);
    });
    vi.stubGlobal("fetch", fetchSpy);

    await bootWorkbench("/investment/wf-001");
    await flushAsyncWork();

    expect(fetchSpy).toHaveBeenCalledWith("/api/workflows/wf-001/dossier", undefined);
    expect(document.body.textContent).toContain("浦发银行 A 股研究");
    expect(document.body.textContent).not.toContain("投资档案不可用");
  });

  it("keeps built-in preview pages usable when APIs are unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      throw new Error(`api unavailable: ${href}`);
    }));

    const routes = [
      ["/investment/wf-001/trace", "流程审计"],
      ["/finance", "资产摘要"],
      ["/knowledge", "经验库"],
      ["/governance", "待办"],
      ["/governance?panel=approvals", "待办"],
      ["/governance?panel=changes", "变更"],
      ["/governance?panel=health", "健康"],
      ["/governance?panel=team", "团队"],
      ["/governance/team", "团队健康"],
      ["/governance/team/quant_analyst", "能做什么"],
      ["/governance/team/quant_analyst/config", "能力提升方案"],
      ["/governance/approvals/ap-001", "审批包"],
    ];

    for (const [route, marker] of routes) {
      await bootWorkbench(route);
      await flushAsyncWork();

      expect(document.body.textContent, route).toContain(marker);
      expect(document.body.textContent, route).not.toContain("API 未连接");
      expect(document.body.textContent, route).not.toContain("本地预览数据");
    }
  });

  it("does not expose non-professional English machine values across workbench pages", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [
            { asset_type: "cash", valuation: { amount: 120000, currency: "CNY" }, boundary_label: "finance_planning_only" },
            { asset_type: "fund", valuation: { amount: 80000, currency: "CNY" }, boundary_label: "finance_planning_only" },
            { asset_type: "gold", valuation: { amount: 30000, currency: "CNY" }, boundary_label: "finance_planning_only" },
            { asset_type: "real_estate", valuation: { amount: 3000000, currency: "CNY" }, boundary_label: "finance_planning_only" },
            { asset_type: "liability", valuation: { amount: 500000, currency: "CNY" }, boundary_label: "finance_planning_only" },
          ],
          finance_health: {
            liquidity: 120000,
            risk_budget: { budget_ref: "risk-budget-finance-v1" },
            stress_test_summary: "cash_floor_checked",
          },
          manual_todo: [
            { risk_hint: "manual_valuation_due" },
            { risk_hint: "annual_tax" },
            { risk_hint: "tuition" },
          ],
        });
      }
      throw new Error(`api unavailable: ${href}`);
    }));

    const routes = [
      "/",
      "/investment",
      "/investment/wf-001",
      "/investment/wf-001/trace",
      "/finance",
      "/knowledge",
      "/governance",
      "/governance?panel=todos",
      "/governance?panel=changes",
      "/governance?panel=health",
      "/governance?panel=audit",
      "/governance/team",
      "/governance/team/quant_analyst",
      "/governance/team/quant_analyst/config",
      "/governance/approvals/ap-001",
    ];
    const forbidden = [
      "finance_planning_only",
      "manual_valuation_due",
      "annual_tax",
      "tuition",
      "cash_floor_checked",
      "risk-budget-finance-v1",
      "conditional_pass",
      "repairable",
      "minute_vwap",
      "request_evidence",
      "direct_write",
      "DIRECT_WRITE_DENIED",
      "tool_progress",
      "guard_failed",
      "Researcher digest",
      "finance raw field",
      "public_internal",
      "candidate",
      "extracted",
      "reviewing",
      "triaged",
      "data_source",
      "owner_pending",
      "schema_validation_failed",
      "default_model_profile",
      "default_tool_profile_id",
      "fenced_background_context_only",
      "tools_enabled",
      "service_permissions",
      "collaboration_commands",
      "skill_package_version",
      "prompt_version",
      "hot_patch_denied",
      "governance_draft_only",
      "hard dissent",
      "positive",
      "neutral",
      "partial",
      "pass",
      "reopen_s3_debate",
      "not_released",
      "trade_chain_allowed",
      "tax_reminder",
      "fundamental_analyst",
      "default_skill_packages",
      "approve_exception_only_if_risk_accepted",
      "current_attempt_only",
      "follow_optimizer",
      "cio_deviation",
      "relation / collection",
      "DefaultContext",
      "MemoryVersion",
    ];

    for (const route of routes) {
      await bootWorkbench(route);
      await flushAsyncWork();
      const text = document.body.textContent ?? "";
      for (const token of forbidden) {
        expect(text, `${route} exposes ${token}`).not.toContain(token);
      }
    }
  });

  it("makes overview summary rows actionable instead of static card text", async () => {
    await bootWorkbench("/");

    const capabilityHrefs = Array.from(document.querySelectorAll("a"))
      .filter((link) => link.textContent?.includes("团队能力"))
      .map((link) => link.getAttribute("href"));
    expect(capabilityHrefs).toContain("/governance?panel=team");
    expect(Array.from(document.querySelectorAll("a")).map((link) => link.getAttribute("href"))).toContain("/governance?panel=todos");
    expect(linkByName("硬异议保留").getAttribute("href")).toBe("/investment/wf-001?stage=S3");
    expect(linkByName("执行数据不足").getAttribute("href")).toBe("/investment/wf-001?stage=S6");
    expect(linkByName("暂无每日简报").getAttribute("href")).toBe("/knowledge");
  });

  it("routes overview pending approval to the real approval id from the API", async () => {
    let submittedApprovalId: string | null = null;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({ task_center: [] });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            {
              approval_id: "approval-live-001",
              subject: "API 组合偏离审批",
              trigger_reason: "api_portfolio_deviation",
              recommended_decision: "request_changes",
              effective_scope: "new_task",
              comparison_options: ["方案 A：要求补证"],
              risk_and_impact: ["影响后续投资任务"],
              rollback_ref: "rollback-api",
              allowed_actions: ["request_changes"],
            },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([]);
      }
      if (href.endsWith("/api/approvals/approval-live-001/decision")) {
        submittedApprovalId = "approval-live-001";
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          approval_id: "approval-live-001",
          decision: "request_changes",
          effective_scope: "new_task",
        });
      }
      return defaultFetch(input, init);
    }));

    await bootWorkbench("/");
    await flushAsyncWork();

    expect(linkByName("待办").getAttribute("href")).toBe("/governance?panel=todos");

    await act(async () => {
      linkByName("待办").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?panel=todos");
    expect(document.body.textContent).toContain("API 组合偏离审批");

    await act(async () => {
      linkByName("办理审批").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/governance/approvals/approval-live-001");
    expect(document.body.textContent).toContain("API 组合偏离审批");
    expect(document.body.textContent).toContain("可选动作");
    expect(document.body.textContent).not.toContain("approval_not_found");

    await act(async () => {
      buttonByName("要求修改").click();
    });
    await flushAsyncWork();

    expect(submittedApprovalId).toBe("approval-live-001");
    expect(document.body.textContent).toContain("后端状态：要求修改");
  });

  it("uses one unified todo card without separate approval and manual todo cards", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            { task_id: "task-ready", task_type: "manual_todo", current_state: "ready", reason_code: "manual_valuation_due" },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            {
              approval_id: "approval-live-001",
              subject: "API 组合偏离审批",
              trigger_reason: "api_portfolio_deviation",
              effective_scope: "new_task",
              allowed_actions: ["request_changes"],
            },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([]);
      }
      return defaultFetch(input);
    }));

    await bootWorkbench("/");
    await flushAsyncWork();

    const attentionLabels = Array.from(document.querySelectorAll(".attention-card span")).map((item) => item.textContent?.trim());
    expect(attentionLabels).toEqual(["风控阻断", "待办", "团队能力"]);
    expect(linkByName("待办").getAttribute("href")).toBe("/governance?panel=todos");
    expect(document.body.textContent).not.toContain("待审批");
    expect(document.body.textContent).not.toContain("审批中心");
    expect(attentionLabels).not.toContain("审批");
    expect(attentionLabels).not.toContain("人工待办");
  });

  it("drives the overview system card from /api/devops/health instead of a local degraded fixture", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({ task_center: [] });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({ approval_center: [] });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([]);
      }
      if (href.endsWith("/api/devops/health")) {
        return mockJsonResponse({
          routine_checks: [{ check_id: "metric-collection", status: "observed" }],
          incidents: [],
          recovery: [{
            plan_id: "recovery-api-1",
            technical_recovery_status: "pending_validation",
            investment_resume_allowed: false,
          }],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("系统");
    expect(document.body.textContent).toContain("恢复待验证");
    expect(document.body.textContent).toContain("指标采集正常；无公开异常；恢复计划待验证，投资恢复未放行。");
    expect(document.body.textContent).not.toContain("数据获取");
    expect(document.body.textContent).not.toContain("公开行情和资料源延迟");
    expect(document.body.textContent).not.toContain("系统降级");
  });

  it("keeps owner default governance pages free of Agent wording and raw machine ids", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            { task_id: "task-running", task_type: "system_task", current_state: "running", reason_code: "data_source_degraded" },
            { task_id: "task-ready", task_type: "manual_todo", current_state: "ready", reason_code: "manual_valuation_due" },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            { approval_id: "ap-api-123", subject: "高影响能力方案", trigger_reason: "high_impact_agent_capability_change", effective_scope: "new_task" },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([
          { change_id: "gov-change-api-123", change_type: "agent_capability", impact_level: "high", state: "owner_pending", effective_scope: "new_task" },
        ]);
      }
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({ team_health: { healthy_agent_count: 9 }, agent_cards: [] });
      }
      if (href.endsWith("/api/devops/health")) {
        return mockJsonResponse({
          routine_checks: [{ check_id: "data-source-latency", status: "degraded" }],
          incidents: [{ incident_id: "incident-api-123", status: "triaged", incident_type: "data_source" }],
          recovery: [{ plan_id: "recovery-api-123", investment_resume_allowed: false }],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    for (const route of [
      "/governance",
      "/governance?panel=todos",
      "/governance?panel=team",
      "/governance?panel=changes",
      "/governance?panel=health",
      "/governance?panel=audit",
    ]) {
      await bootWorkbench(route);
      await flushAsyncWork();
      const text = document.body.textContent ?? "";

      expect(text, route).not.toContain("Agent");
      expect(text, route).not.toMatch(/\b(?:ap|gov|incident|trace|ctx|task)-[A-Za-z0-9_-]+\b/);
      expect(text, route).not.toContain("进入 Agent 团队");
    }
  });

  it("shows one actionable governance todo panel for approvals and manual tasks", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            { task_id: "task-running", task_type: "system_task", current_state: "running", reason_code: "data_source_degraded" },
            { task_id: "task-completed", task_type: "research_task", current_state: "completed", reason_code: "supporting_evidence_only" },
            { task_id: "task-confirmed", task_type: "investment_workflow", current_state: "ready", reason_code: "request_brief_confirmed" },
            { task_id: "task-ready", task_type: "manual_todo", current_state: "ready", reason_code: "request_brief_confirmed" },
            { task_id: "task-blocked", task_type: "investment_workflow", current_state: "blocked", reason_code: "retained_hard_dissent_risk_review" },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            { approval_id: "approval-live-001", subject: "API 组合偏离审批", trigger_reason: "api_portfolio_deviation", effective_scope: "new_task" },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("人工待办");
    expect(document.body.textContent).toContain("API 组合偏离审批");
    expect(linkByName("办理审批").getAttribute("href")).toBe("/governance/approvals/approval-live-001");
    expect(linkByName("去办理").getAttribute("href")).toBe("/finance?todo=task-ready");
    expect(document.body.textContent).toContain("投资任务");
    expect(document.body.textContent).not.toContain("request_brief_confirmed");
    expect(document.body.textContent).not.toContain("系统事项");
    expect(document.body.textContent).not.toContain("研究任务");
  });

  it("keeps knowledge proposals out of the knowledge page and exposes one aligned organize action", async () => {
    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    const buttons = Array.from(document.querySelectorAll("button")).map((button) => button.textContent?.trim());
    expect(buttons).toContain("应用整理建议");
    expect(buttons).not.toContain("应用组织建议");
    expect(buttons).not.toContain("应用建议 / 应用组织建议");
    expect(document.body.textContent).not.toContain("知识与方法提案");
    expect(document.body.textContent).not.toContain("进入治理提案");
  });

  it("uses a compact investment dossier header without default audit entry", async () => {
    await bootWorkbench("/investment/wf-001");

    expect(document.querySelector("h1")?.textContent).not.toContain("投资档案");
    expect(document.body.textContent).not.toContain("审计回链");
    expect(document.body.textContent).not.toContain("查看审计");
    const header = document.querySelector(".compact-dossier-header");
    expect(header).not.toBeNull();
    expect(getComputedStyle(header as Element).maxHeight).toBe("44px");
    expect(header?.textContent).toContain("浦发银行 A 股研究 · IC：S3 辩论受阻");
  });

  it("shows a real not-found state for missing approvals without fake action buttons", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({ approval_center: [] });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/approvals/missing-approval");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("审批记录不可用");
    expect(document.body.textContent).toContain("返回待办");
    expect(document.body.textContent).not.toContain("可选动作");
    expect(document.body.textContent).not.toContain("推荐结论");
    expect(document.body.textContent).not.toContain("approval_not_found");
  });

  it("routes manual todos to a finance handling form and writes through /api/finance/assets", async () => {
    let financeAssetBody: Record<string, unknown> | null = null;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            {
              task_id: "task-manual-api",
              task_type: "manual_todo",
              current_state: "ready",
              reason_code: "manual_valuation_due",
              due_date: "2026-05-08",
              risk_hint: "房产估值过期会影响财务规划",
            },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({ approval_center: [] });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([]);
      }
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [],
          finance_health: { liquidity: 1000000, risk_budget: { budget_ref: "risk-budget-ui" } },
          manual_todo: [],
        });
      }
      if (href.endsWith("/api/finance/assets")) {
        financeAssetBody = JSON.parse(String(init?.body));
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          asset_id: "asset-from-todo",
          asset_type: "real_estate",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/");
    await flushAsyncWork();

    await act(async () => {
      linkByName("待办").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?panel=todos");
    expect(document.body.textContent).toContain("人工待办：更新房产或非 A 股资产估值");
    expect(document.body.textContent).toContain("截止时间：2026-05-08");
    expect(document.body.textContent).toContain("房产估值过期会影响财务规划");
    expect(document.body.textContent).toContain("不进入审批、执行或交易链路");

    await act(async () => {
      linkByName("去办理").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/finance");
    expect(window.location.search).toBe("?todo=task-manual-api");
    expect(document.body.textContent).toContain("正在办理：task-manual-api");

    await act(async () => {
      setInputValue(inputByLabel("估值金额"), "3200000");
      setInputValue(inputByLabel("资料来源"), "业主手工确认");
    });
    await act(async () => {
      buttonByName("提交财务档案").click();
    });
    await flushAsyncWork();

    expect(financeAssetBody).toMatchObject({
      asset_id: "finance-task-manual-api",
      asset_type: "real_estate",
      valuation: { amount: 3200000, currency: "CNY" },
      source: "业主手工确认",
    });
    expect(document.body.textContent).toContain("财务档案已更新 asset-from-todo");
  });

  it("hides raw memory names and internal ids from the default Knowledge owner view", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/knowledge/memory-items")) {
        return mockJsonResponse([
          {
            memory_id: "memory-1",
            title: "test",
            current_version_id: "artifact-research-1",
            sensitivity: "public_internal",
            relations: [{ target_ref: "artifact-raw-1", relation_type: "supports" }],
          },
          {
            memory_id: "memory-2",
            title: "测试",
            current_version_id: "memory-version-2",
            sensitivity: "public_internal",
            relations: [],
          },
          {
            memory_id: "memory-3",
            title: "Owner 捕获记忆：后续研究资料需要保留来源、标签和适用边界。",
            current_version_id: "memory-version-3",
            sensitivity: "public_internal",
            relations: [],
          },
          {
            memory_id: "memory-4",
            title: "Owner 捕获记忆：后续研究资料需要保留来源、标签和适用边界。",
            current_version_id: "memory-version-4",
            sensitivity: "public_internal",
            relations: [],
          },
        ]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("暂无每日简报。");
    expect(document.body.textContent).toContain("暂无可复核资料包。");
    expect(document.body.textContent).not.toContain("今日影响：");
    expect(document.body.textContent).not.toContain("下一步：");
    expect(document.body.textContent).toContain("待整理资料");
    expect(document.body.textContent).not.toContain("memory-1");
    expect(document.body.textContent).not.toContain("artifact-research-1");
    expect(document.body.textContent).not.toContain("Untitled Memory");
    expect(document.body.textContent).not.toContain("测试 ·");
    expect(document.body.textContent).not.toContain("test · 1 条");
    expect(document.body.textContent).not.toContain("Owner 捕获记忆");
    expect((document.body.textContent?.match(/后续研究资料需要保留来源、标签和适用边界/g) ?? []).length).toBe(1);
  });

  it("loads investment dossier stage rail and summary from the workflow dossier API", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/workflows/workflow-api-1/dossier")) {
        return mockJsonResponse({
          workflow: {
            workflow_id: "workflow-api-1",
            title: "API 投资档案",
            current_stage: "S1",
            state: "running",
          },
          stage_rail: [
            { stage: "S0", node_status: "completed", reason_code: null, artifact_count: 1 },
            { stage: "S1", node_status: "running", reason_code: null, artifact_count: 0 },
            { stage: "S2", node_status: "not_started", reason_code: null, artifact_count: 0 },
          ],
          chair_brief: {
            decision_question: "API 决策问题",
            key_tensions: ["数据完整性"],
            no_preset_decision_attestation: true,
          },
          analyst_stance_matrix: [
            { role: "API Analyst", direction: "观察", confidence: 0.88, hard_dissent: false },
          ],
          data_readiness: {
            quality_band: "partial",
            decision_core_status: "pass",
            execution_core_status: "blocked",
            issues: ["实时执行行情缺失"],
            lineage_refs: ["api-source-daily"],
            owner_summary: "API S1 已返回后端数据准备结果。",
            source_status: [
              {
                source_name: "API 行情源",
                source_ref: "api-source-daily",
                required_usage: "decision_core",
                requested_fields: ["标的代码", "交易日", "收盘价"],
                obtained_fields: ["标的代码", "交易日", "收盘价"],
                missing_fields: [],
                status: "available",
                quality_label: "可用于研究判断",
                evidence_ref: "api-source-daily",
              },
            ],
            data_gaps: [
              {
                gap: "实时执行行情缺失",
                affects_stage: "S6",
                impact: "不能生成纸面成交授权。",
                next_action: "进入 S6 前补采执行行情。",
              },
            ],
          },
          forbidden_actions: {
            execution_core_blocked_no_trade: { action_visible: false, reason_code: "execution_core_blocked_no_trade" },
          },
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/investment/workflow-api-1");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 投资档案");
    expect(document.body.textContent).toContain("API S1 已返回后端数据准备结果");
    expect(document.body.textContent).toContain("API 行情源");
    expect(document.body.textContent).toContain("已取得字段");
    expect(document.body.textContent).toContain("标的代码");
    expect(document.body.textContent).toContain("交易日");
    expect(document.body.textContent).toContain("收盘价");
    expect(document.body.textContent).toContain("可用于研究判断");
    expect(document.querySelector(".s1-status-grid")).not.toBeNull();
    expect(document.querySelector(".s1-source-table")).not.toBeNull();
    expect(document.querySelector(".s1-impact-chain")).not.toBeNull();
    expect(document.body.textContent).not.toContain("已获取：标的代码、交易日、收盘价");
    expect(document.body.textContent).not.toContain("字段：标的代码");
    expect(document.body.textContent).not.toContain("已获取 · 可用于研究判断");
    expect(document.body.textContent).toContain("数据准备");
    expect(document.body.textContent).toContain("IC：S1 数据运行中");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
    expect(document.body.textContent).not.toContain("当前阶段摘要");
    expect(document.body.textContent).not.toContain("当前详情");
    expect(document.body.textContent).not.toContain("API Analyst");
    expect(buttonByName("S1").getAttribute("aria-pressed")).toBe("true");
  });

  it("renders every required Investment Dossier business panel without exposing execution shortcuts", async () => {
    await bootWorkbench("/investment/wf-001");

    for (const label of [
      "辩论摘要",
      "分析师要点",
      "下一步：补齐资产质量、拨备覆盖率和息差趋势证据",
    ]) {
      expect(document.body.textContent).toContain(label);
    }

    expect(document.querySelector(".dossier-status-line")?.textContent).toContain("浦发银行 A 股研究");
    expect(document.querySelector(".dossier-status-line")?.textContent).toContain("IC：S3 辩论受阻");
    expect(document.querySelector(".dossier-status-line")?.textContent).toContain("硬异议保留");
    expect(document.querySelector("h1")?.textContent).not.toContain("投资档案");
    expect(buttonByName("S6 执行").textContent).not.toContain("审批执行");
    expect(document.querySelector(".dossier-grid.drawer-open")).toBeNull();
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
    expect(document.body.textContent).not.toContain("当前阶段摘要");
    expect(document.body.textContent).not.toContain("分析过程");
    expect(document.body.textContent).not.toContain("等待 S1/S2 产物后形成 CIO Chair Brief");
    expect(document.body.textContent).not.toContain("批准继续");
    expect(document.body.textContent).not.toContain("立即成交");
  });

  it("uses controlled trading language in S0 and S1 without placeholder process copy", async () => {
    await bootWorkbench("/investment/wf-001?stage=S0");
    await flushAsyncWork();

    let text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["任务接收"]);
    expect(document.querySelectorAll(".stage-unified-summary-card")).toHaveLength(1);
    expect(Array.from(document.querySelectorAll(".stage-summary-section h4")).map((item) => item.textContent)).toEqual([
      "收到什么",
      "处理情况",
      "准备做什么",
    ]);
    expect(document.querySelectorAll(".stage-summary-section.stage-summary-section-card")).toHaveLength(3);
    expect(text).toContain("标的：浦发银行 A 股");
    expect(text).toContain("目标：是否值得围绕浦发银行进入完整 IC 论证");
    expect(text).toContain("建立投资任务");
    expect(text).toContain("拉取研究与决策核心数据");
    expect(text).toContain("请求已标准化");
    expect(text).toContain("等待 S1 数据准备结果");
    expect(text).not.toContain("做到哪一步");
    expect(text).toContain("不预设结论");
    expect(text).not.toContain("现在研究");
    expect(text).not.toContain("要回答的问题");
    expect(text).not.toContain("等待 S1/S2");
    expect(text).not.toContain("CIO Chair Brief");

    await bootWorkbench("/investment/wf-001?stage=S1");
    await flushAsyncWork();

    text = document.body.textContent ?? "";
    expect(text).toContain("S1 已拿到可用于研究的数据");
    expect(text).toContain("腾讯公开日线行情");
    expect(text).toContain("已取得字段");
    for (const field of ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"]) {
      expect(text).toContain(field);
    }
    expect(text).toContain("可用于研究判断");
    expect(text).toContain("实时执行行情缺失");
    expect(directPanelTitles()).toEqual(["数据准备"]);
    expect(document.querySelectorAll(".s1-data-readiness-card")).toHaveLength(1);
    expect(document.querySelectorAll(".direct-info-grid.two")).toHaveLength(0);
    expect(document.querySelectorAll(".s1-status-block")).toHaveLength(2);
    expect(document.querySelectorAll(".s1-source-table")).toHaveLength(1);
    expect(document.querySelectorAll(".owner-data-source-row")).toHaveLength(2);
    expect(document.querySelectorAll(".s1-impact-row")).toHaveLength(1);
    expect(text).toContain("来源矩阵");
    expect(text).toContain("缺口影响链");
    expect(text).not.toContain("缺失 · 缺失");
    expect(text).not.toContain("字段：标的代码");
    expect(text).not.toContain("已获取：标的代码、交易日、收盘价、成交量、来源时间戳");
    expect(text).not.toContain("已获取 · 可用于研究判断");
    expect(text).toContain("未取得 · 不能用于成交");
    expect(text).not.toContain("当前数据可支持研究判断");
    expect(text).not.toContain("后续成交缺口");
    expect(text).not.toContain("不能直接支持成交");
  });

  it("uses the backend zero-success S1 data state instead of a separate empty gap card", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/workflows/wf-no-data/dossier")) {
        return mockJsonResponse({
          ...mockDossierReadModel(),
          workflow: { workflow_id: "wf-no-data", title: "零数据 A 股研究", current_stage: "S1", state: "running" },
          data_readiness: {
            quality_band: "blocked",
            decision_core_status: "blocked",
            execution_core_status: "blocked",
            issues: ["日线行情源超时，公告源返回空结果。"],
            lineage_refs: [],
            owner_summary: "本轮 S1 没有成功获取可用数据。",
            source_status: [
              {
                source_name: "腾讯公开日线行情",
                source_ref: "tencent-public-kline:600000.SH",
                required_usage: "decision_core",
                requested_fields: ["标的代码", "交易日", "收盘价"],
                obtained_fields: [],
                missing_fields: ["标的代码", "交易日", "收盘价"],
                status: "failed",
                quality_label: "采集失败",
                evidence_ref: "artifact-no-data-readiness",
              },
            ],
            data_gaps: [
              {
                gap: "日线行情源超时，公告源返回空结果。",
                affects_stage: "S1",
                impact: "无法形成研究判断或进入后续分析。",
                next_action: "重试日线行情源，并补充公告/财报来源。",
              },
            ],
          },
          evidence_map: { data_refs: [], source_quality: [], conflict_refs: [] },
        });
      }
      return defaultFetch(input);
    }));

    await bootWorkbench("/investment/wf-no-data?stage=S1");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["数据准备"]);
    expect(document.querySelectorAll(".s1-data-readiness-card")).toHaveLength(1);
    expect(text).toContain("本轮 S1 没有成功获取可用数据");
    expect(text).toContain("腾讯公开日线行情");
    expect(text).toContain("缺失字段");
    expect(text).toContain("标的代码");
    expect(text).toContain("交易日");
    expect(text).toContain("收盘价");
    expect(text).toContain("无法形成研究判断或进入后续分析");
    expect(text).not.toContain("还缺什么");
    expect(text).not.toContain("影响当前阶段：S2/S3 可以继续");
  });

  it("does not invent S1 source rows when the backend returns no source details", async () => {
    stubDossierResponse("wf-no-source", {
      ...mockDossierReadModel(),
      workflow: { workflow_id: "wf-no-source", title: "空来源 A 股研究", current_stage: "S1", state: "running" },
      data_readiness: {
        quality_band: "blocked",
        decision_core_status: "blocked",
        execution_core_status: "blocked",
        issues: ["未取得可用于研究的数据。"],
        lineage_refs: [],
        owner_summary: "未读取到 S1 数据准备结果。",
        source_status: [],
        data_gaps: [],
      },
      evidence_map: { data_refs: [], source_quality: [], conflict_refs: [] },
    });

    await bootWorkbench("/investment/wf-no-source?stage=S1");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["数据准备"]);
    expect(document.querySelectorAll(".s1-data-readiness-card")).toHaveLength(1);
    expect(document.querySelectorAll(".owner-data-source-row")).toHaveLength(0);
    expect(text).toContain("未读取到 S1 数据准备结果");
    expect(text).toContain("暂无明确数据缺口");
    expect(text).not.toContain("后端未返回数据来源");
    expect(text).not.toContain("缺失字段：后端未返回字段明细");
    expect(text).not.toContain("不可用");
  });

  it("uses one fixed-height reading panel for compact stages and keeps S1 as one compact data card", async () => {
    const expectations: Array<[string, string[]]> = [
      ["S0", ["任务接收"]],
      ["S1", ["数据准备"]],
      ["S4", ["决策形成"]],
      ["S5", ["风控复核"]],
      ["S6", ["纸面执行"]],
      ["S7", ["归因复盘"]],
    ];

    for (const [stage, titles] of expectations) {
      await bootWorkbench(`/investment/wf-001?stage=${stage}`);
      await flushAsyncWork();

      expect(directPanelTitles()).toEqual(titles);
      if (stage !== "S1") {
        expect(document.querySelectorAll(".stage-unified-summary-card")).toHaveLength(1);
      } else {
        expect(document.querySelectorAll(".s1-data-readiness-card")).toHaveLength(1);
        expect(document.querySelectorAll(".direct-info-grid.two")).toHaveLength(0);
      }
      expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
      expect(stageSummaryCards()).toHaveLength(0);
    }
  });

  it("keeps the middle reading frame aligned with the full S0-S7 stage rail instead of the selected chip", async () => {
    await bootWorkbench("/investment/wf-001?stage=S6");
    await flushAsyncWork();

    const grid = document.querySelector(".dossier-grid") as HTMLElement | null;
    const board = document.querySelector(".stage-summary-board") as HTMLElement | null;
    const rail = document.querySelector(".stage-rail") as HTMLElement | null;
    const chips = Array.from(document.querySelectorAll(".stage-chip")) as HTMLElement[];

    expect(grid?.getAttribute("style") ?? "").not.toContain("--stage-align-offset");
    expect(board).not.toBeNull();
    expect(rail).not.toBeNull();
    expect(rail?.classList).toContain("full-stage-rail");
    expect(board?.classList).toContain("stage-reading-frame");
    expect(chips.map((chip) => chip.querySelector("strong")?.textContent)).toEqual([
      "S0 接收",
      "S1 数据",
      "S2 分析",
      "S3 辩论",
      "S4 决策",
      "S5 风控",
      "S6 执行",
      "S7 归因",
    ]);
  });

  it("keeps owner default investment copy free of internal technical terms", async () => {
    for (const stage of ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]) {
      await bootWorkbench(`/investment/wf-001?stage=${stage}`);
      await flushAsyncWork();
      expectOwnerDefaultTextClean(document.body.textContent ?? "");
    }
  });

  it("folds S2 hard dissent and stage judgment into one conclusion summary with item details", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    expect(stageSummaryCardTitles()).toEqual([
      "分析师立场矩阵",
      "结论摘要",
    ]);
    expect(document.body.textContent).toContain("分析完成，进入辩论而非决策");
    expect(document.body.textContent).toContain("去向：进入 S3 辩论");
    expect(document.body.textContent).toContain("硬异议：基本面证据不足");
    expect(document.body.textContent).toContain("证据：4 位分析师已交，平均证据 72%");
    expect(document.body.textContent).toContain("下一步：补资产质量和息差证据");
    expect(document.body.textContent).not.toContain("硬异议与补证焦点");
    expect(document.body.textContent).not.toContain("S2 阶段判断");
    expect(document.body.textContent).not.toContain("证据质量");
    expect(document.body.textContent).not.toContain("角色产物完整度");
    expect(document.body.textContent).not.toContain("进入 S3 原因");

    const matrix = document.querySelector(".analyst-matrix-card") as HTMLElement | null;
    const header = matrix?.querySelector(".analyst-matrix-header") as HTMLElement | null;
    expect(matrix?.classList).toContain("summary-span-12");
    expect(matrix?.classList).toContain("quiet-matrix");
    expect(header?.textContent).toContain("角色");
    expect(header?.textContent).toContain("方向");
    expect(header?.textContent).toContain("置信");
    expect(header?.textContent).toContain("证据");
    expect(header?.textContent).toContain("产物");
    expect(header?.textContent).toContain("状态");

    const rows = Array.from(document.querySelectorAll(".analyst-matrix-card .matrix-row")) as HTMLElement[];
    expect(rows).toHaveLength(4);
    expect(rows[1].textContent).toContain("基本面分析师");
    expect(rows[1].textContent).toContain("68%");
    expect(rows[1].textContent).toContain("62%");
    expect(rows[1].textContent).toContain("已交");
    expect(rows[1].textContent).toContain("硬异议");

    const conclusionItems = Array.from(document.querySelectorAll('.s2-conclusion-list [role="button"]')) as HTMLElement[];
    expect(conclusionItems.map((item) => item.textContent)).toEqual([
      "去向：进入 S3 辩论",
      "硬异议：基本面证据不足",
      "证据：4 位分析师已交，平均证据 72%",
      "下一步：补资产质量和息差证据",
    ]);
    expect(document.querySelectorAll(".stage-summary-board button")).toHaveLength(0);

    await act(async () => {
      conclusionItems[1].click();
    });
    await flushAsyncWork();

    const detailText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(detailText).toContain("硬异议详情");
    expect(detailText).toContain("资产质量修复证据不足");
    expect(detailText).toContain("补证要求");
    const focusedItems = Array.from(document.querySelectorAll(".summary-focus-list .summary-focus-item")) as HTMLElement[];
    expect(focusedItems.map((item) => item.textContent)).toEqual(expect.arrayContaining([
      expect.stringContaining("去向：进入 S3 辩论"),
      expect.stringContaining("硬异议：基本面证据不足"),
      expect.stringContaining("证据：4 位分析师已交，平均证据 72%"),
      expect.stringContaining("下一步：补资产质量和息差证据"),
    ]));
  });

  it("switches the opened S2 analyst detail into focus mode instead of squeezing the matrix", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    await act(async () => {
      detailRowByText("基本面分析师").click();
    });
    await flushAsyncWork();

    expect(document.querySelector(".dossier-grid.drawer-open")).not.toBeNull();
    expect(document.querySelector(".stage-summary-board.summary-focus-mode")).not.toBeNull();
    expect(document.querySelector(".summary-focus-list")).not.toBeNull();
    expect(document.querySelector(".stage-summary-grid")).toBeNull();
    expect(document.querySelector(".analyst-matrix-card")).toBeNull();
    expect(document.querySelectorAll(".summary-focus-analyst-row")).toHaveLength(4);
    expect(document.querySelector(".summary-focus-item.is-active")?.textContent).toContain("基本面分析师");
  });

  it("keeps the IC work stage fixed while a clicked stage changes only the selected stage view", async () => {
    await bootWorkbench("/investment/wf-001?stage=S1");
    await flushAsyncWork();

    expect(buttonByName("S1").getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector(".dossier-status-line")?.textContent).toContain("IC：S3 辩论受阻");
    expect(document.body.textContent).toContain("数据准备");
    expect(document.body.textContent).toContain("腾讯公开日线行情");
    expect(document.body.textContent).toContain("已取得字段");
    for (const field of ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"]) {
      expect(document.body.textContent).toContain(field);
    }
    expect(document.body.textContent).toContain("可用于研究判断");
    expect(document.body.textContent).not.toContain("已获取：标的代码、交易日、收盘价、成交量、来源时间戳");
    expect(document.body.textContent).not.toContain("字段：标的代码");
    expect(document.body.textContent).not.toContain("已获取 · 可用于研究判断");
    expect(document.body.textContent).toContain("来源矩阵");
    expect(document.body.textContent).toContain("缺口影响链");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
    expect(document.body.textContent).not.toContain("当前阶段摘要");
    expect(document.body.textContent).not.toContain("S1 数据准备");
    expect(document.body.textContent).not.toContain("决策问题：是否值得围绕浦发银行进入完整 IC 论证");
  });

  it("switches stage summary cards without opening the detail drawer from the stage rail", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("结论摘要");
    expect(document.body.textContent).not.toContain("硬异议与补证焦点");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();

    await act(async () => {
      buttonByName("S6 执行").click();
    });
    await flushAsyncWork();

    expect(window.location.search).toBe("?stage=S6");
    expect(document.body.textContent).toContain("不能执行");
    expect(document.body.textContent).toContain("影响与下一步");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
  });

  it("opens detail drawer from S2 analyst rows and switches between all four analyst details", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    for (const [role, expected] of [
      ["宏观分析师", "宏观环境支持观察"],
      ["基本面分析师", "资产质量修复证据不足"],
      ["量化分析师", "趋势和因子仍偏正面"],
      ["事件分析师", "暂无强催化"],
    ]) {
      await act(async () => {
        detailRowByText(role).click();
      });
      await flushAsyncWork();

      expect(document.querySelector(".dossier-detail-drawer")?.textContent).toContain(role);
      expect(document.querySelector(".dossier-detail-drawer")?.textContent).toContain(expected);
      expect(document.querySelector(".dossier-grid.drawer-open")).not.toBeNull();
    }
  });

  it("renders opened details as a distinct side sheet instead of another summary card", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    await act(async () => {
      detailRowByText("基本面分析师").click();
    });
    await flushAsyncWork();

    const sheet = document.querySelector(".dossier-detail-sheet") as HTMLElement | null;
    expect(sheet).not.toBeNull();
    expect(sheet?.textContent).toContain("基本面分析师");
    expect(sheet?.classList).not.toContain("flat-panel");
    expect(sheet?.classList).not.toContain("summary-card");
  });

  it("shows S6 no-trade explanation directly without a detail drawer", async () => {
    await bootWorkbench("/investment/wf-001?stage=S6");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(text).toContain("缺少成交所需的核心数据");
    expect(text).toContain("这是 S6 成交门槛，不是当前 S3 辩论受阻原因");
    expect(text).toContain("补齐执行核心数据后再判断");
    expect(text).not.toContain("审批边界");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
  });

  it("shows S2 analyst memo details and the hard dissent reason in owner-readable language", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    await act(async () => {
      detailRowByText("基本面分析师").click();
    });
    await flushAsyncWork();

    const text = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(text).toContain("岗位判断");
    expect(text).toContain("主要依据");
    expect(text).toContain("反证风险");
    expect(text).toContain("基本面分析师");
    expect(text).toContain("资产质量修复证据不足");
    expect(text).toContain("需要补充不良率、拨备覆盖率和息差趋势");
    expect(text).toContain("S3 先补证，保留硬异议并交风控复核");
    for (const token of ["fundamental", "neutral", "positive", "partial", "pass", "payload", "[object Object]"]) {
      expect(text).not.toContain(token);
    }
  });

  it("shows every analyst view in S3 directly without mixing in the S6 execution guard", async () => {
    await bootWorkbench("/investment/wf-001?stage=S3");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(document.querySelector(".s3-debate-summary")).not.toBeNull();
    expect(directPanelTitles()).toEqual(["辩论摘要", "分析师要点"]);
    expect(document.querySelectorAll(".s3-debate-summary .stage-summary-pair")).toHaveLength(6);
    expect(document.querySelectorAll(".s3-debate-summary .stage-detail-row")).toHaveLength(4);
    expect(document.querySelectorAll(".s3-analyst-summary-row")).toHaveLength(4);
    expect(document.querySelectorAll(".stage-summary-board button")).toHaveLength(0);
    expect(document.querySelectorAll(".debate-analyst-card")).toHaveLength(0);
    expect(text).toContain("辩论摘要");
    expect(text).toContain("分析师要点");
    for (const role of ["宏观分析师", "基本面分析师", "量化分析师", "事件分析师"]) {
      expect(text).toContain(role);
    }
    expect(text).toContain("资产质量修复是否足以抵消估值低位");
    expect(text).toContain("CIO 要求先补齐资产质量和息差证据");
    expect(text).toContain("共识 75% · 行动强度 60%");
    expect(text).toContain("低估值可能是价值陷阱");
    expect(text).toContain("量化分析师：偏正面 -> 观察");
    expect(text).toContain("基本面分析师：中性 -> 维持硬异议");
    expect(text).toContain("补齐资产质量、拨备覆盖率和息差趋势证据");
    expect(text).toContain("基本面硬异议仍保留");
    expect(text).toContain("轮次");
    expect(text).toContain("保留异议");
    expect(text).not.toContain("默认先看辩论综合");
    expect(text).not.toContain("观点：");
    expect(text).not.toContain("依据：");
    expect(text).not.toContain("结论：");
    expect(text).not.toContain("执行数据不足是 S6 成交门槛，不是当前 S3 阻断原因");
    expect(text).not.toContain("reopen_s3_debate");
    expect(text).not.toContain("not_released");
    expect(text).not.toContain("查看辩论详情");
    expect(text).not.toContain("完整辩论详情");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
  });

  it("opens rich S3 debate detail from a specific summary item instead of a generic button", async () => {
    await bootWorkbench("/investment/wf-001?stage=S3");
    await flushAsyncWork();

    await act(async () => {
      detailRowByText("核心分歧").click();
    });
    await flushAsyncWork();

    const disputeText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(disputeText).toContain("核心分歧详情");
    expect(disputeText).toContain("低估值可能是价值陷阱");
    expect(disputeText).toContain("基本面分析师 / 量化分析师 / CIO");

    await act(async () => {
      detailRowByText("观点变化").click();
    });
    await flushAsyncWork();

    const viewChangeText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(viewChangeText).toContain("观点变化详情");
    expect(viewChangeText).toContain("量化分析师：偏正面 -> 观察");
    expect(viewChangeText).toContain("基本面补证不足");
    expect(viewChangeText).not.toEqual(disputeText);

    await act(async () => {
      detailRowByText("保留异议").click();
    });
    await flushAsyncWork();

    const dissentText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(dissentText).toContain("保留异议详情");
    expect(dissentText).toContain("不良率拐点未确认");
    expect(dissentText).toContain("不能直接放行 S4");
    expect(dissentText).not.toEqual(viewChangeText);

    await act(async () => {
      detailRowByText("轮次").click();
    });
    await flushAsyncWork();

    const roundText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(roundText).toContain("轮次详情");
    expect(roundText).toContain("第 1 轮：资产质量修复是否成立");
    expect(roundText).toContain("输入证据：不良率趋势 / 拨备覆盖率");
    expect(roundText).not.toEqual(dissentText);
    expect(document.body.textContent).not.toContain("查看辩论详情");
  });

  it("does not invent S3 detail text when the backend omits structured debate fields", async () => {
    const dossier = mockDossierReadModel();
    const debate: Record<string, unknown> = { ...dossier.debate };
    delete debate.owner_summary;
    delete debate.status_summary;
    delete debate.core_disputes;
    delete debate.view_change_details;
    delete debate.retained_dissent_details;
    delete debate.round_details;
    delete debate.next_actions;
    stubDossierResponse("wf-s3-missing-structured", {
      ...dossier,
      workflow: { workflow_id: "wf-s3-missing-structured", title: "缺结构辩论 A 股研究", current_stage: "S3", state: "blocked" },
      debate,
    });

    await bootWorkbench("/investment/wf-s3-missing-structured?stage=S3");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("后端未返回辩论详情");

    await act(async () => {
      detailRowByText("核心分歧").click();
    });
    await flushAsyncWork();

    const detailText = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(detailText).toContain("核心分歧详情");
    expect(detailText).toContain("后端未返回辩论详情");
    expect(detailText).not.toContain("低估值可能是价值陷阱");
  });

  it("uses different S2 and S3 analyst detail content for the same analyst", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    await act(async () => {
      detailRowByText("基本面分析师").click();
    });
    await flushAsyncWork();

    const s2Text = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(s2Text).toContain("岗位判断");
    expect(s2Text).toContain("主要依据");
    expect(s2Text).not.toContain("辩论回应");

    await bootWorkbench("/investment/wf-001?stage=S3");
    await flushAsyncWork();

    await act(async () => {
      const row = Array.from(document.querySelectorAll(".s3-analyst-summary-row"))
        .find((item) => item.textContent?.includes("基本面分析师")) as HTMLElement | undefined;
      if (!row) throw new Error("S3 analyst row not found: 基本面分析师");
      row.click();
    });
    await flushAsyncWork();

    const s3Text = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(s3Text).toContain("辩论回应");
    expect(s3Text).toContain("观点变化");
    expect(s3Text).toContain("CIO 处理");
    expect(s3Text).not.toEqual(s2Text);
  });

  it("shows S4 blocked decision basis directly in owner-readable language", async () => {
    await bootWorkbench("/investment/wf-001?stage=S4");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["决策形成"]);
    expect(document.querySelectorAll(".stage-unified-summary-card")).toHaveLength(1);
    expect(text).toContain("基本面硬异议仍未解除");
    expect(text).toContain("资产质量和息差证据不足");
    expect(text).toContain("行动强度未达到执行阈值");
    expect(text).toContain("重开 S2/S3 补证");
    expect(text).toContain("补齐证据后重新收口");
    expect(text).not.toContain("为什么还不能决策");
    expect(text).toContain("基本面硬异议还没解除");
    expect(text).toContain("共识 75%");
    expect(text).toContain("行动强度 60%");
    expect(text).not.toContain("DecisionPacket");
    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();
  });

  it("shows S4 formed decisions and major deviations as separate states", async () => {
    stubDossierResponse("wf-s4-formed", {
      ...mockDossierReadModel(),
      workflow: { workflow_id: "wf-s4-formed", title: "可决策 A 股研究", current_stage: "S4", state: "running" },
      consensus: { consensus_score: 0.82, action_conviction: 0.7, threshold_label: "可进入风控" },
      cio_decision: {
        decision: "observe",
        decision_rationale: "估值低位和量价改善支持观察，基本面异议已处理。",
        conditions: ["风险预算未越线", "价格区间需要后续验证"],
        monitoring_points: ["继续跟踪资产质量"],
      },
      decision_guard: { major_deviation: false, single_name_deviation_pp: 2, portfolio_active_deviation: 0.08 },
      optimizer_deviation: { single_name_deviation: "2pp", portfolio_deviation: "8%", recommendation: "可进入风控复核" },
    });

    await bootWorkbench("/investment/wf-s4-formed?stage=S4");
    await flushAsyncWork();

    let text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["决策形成"]);
    expect(document.querySelectorAll(".stage-unified-summary-card")).toHaveLength(1);
    expect(text).toContain("建议：观察");
    expect(text).toContain("共识：82%，行动强度：70%");
    expect(text).toContain("估值低位和量价改善支持观察");
    expect(text).toContain("单股偏离：2pp，未触发重大偏离");
    expect(text).toContain("进入 S5 风控复核");

    stubDossierResponse("wf-s4-deviation", {
      ...mockDossierReadModel(),
      workflow: { workflow_id: "wf-s4-deviation", title: "重大偏离 A 股研究", current_stage: "S4", state: "blocked" },
      cio_decision: {
        decision: "buy",
        decision_rationale: "CIO 判断机会窗口较短。",
        deviation_reason: "低估值窗口需要更高目标权重。",
      },
      decision_guard: { major_deviation: true, single_name_deviation_pp: 6, portfolio_active_deviation: 0.22 },
      optimizer_deviation: { single_name_deviation: "6pp", portfolio_deviation: "22%", recommendation: "进入例外候选或重开论证" },
    });

    await bootWorkbench("/investment/wf-s4-deviation?stage=S4");
    await flushAsyncWork();

    text = document.body.textContent ?? "";
    expect(directPanelTitles()).toEqual(["决策形成"]);
    expect(document.querySelectorAll(".stage-unified-summary-card")).toHaveLength(1);
    expect(text).toContain("CIO 判断与组合优化建议差异较大");
    expect(text).toContain("单股目标权重偏离 >= 5pp，或组合主动偏离 >= 20%");
    expect(text).toContain("进入老板例外候选，或重开论证");
  });

  it("shows S5 risk review states with useful next steps", async () => {
    const cases = [
      {
        id: "wf-s5-approved",
        risk_review: { review_result: "approved", repairability: "not_required", owner_exception_required: false, reason_codes: [] },
        titles: ["风控复核"],
        contains: ["可进入授权与纸面执行检查", "数据质量满足当前决策用途", "进入 S6", "执行核心数据满足成交门槛"],
      },
      {
        id: "wf-s5-conditional",
        risk_review: { review_result: "conditional_pass", repairability: "not_required", owner_exception_required: true, reason_codes: ["cio_deviation"] },
        titles: ["风控复核"],
        contains: ["需要老板确认例外", "不同方案的风险与影响", "进入审批包，而不是直接执行"],
      },
      {
        id: "wf-s5-repairable",
        risk_review: { review_result: "rejected", repairability: "repairable", owner_exception_required: false, reason_codes: ["retained_hard_dissent_risk_review"] },
        titles: ["风控复核"],
        contains: ["当前尝试暂停", "硬异议仍未被证据消除", "回到指定阶段补证或重开论证"],
      },
      {
        id: "wf-s5-unrepairable",
        risk_review: { review_result: "rejected", repairability: "unrepairable", owner_exception_required: false, reason_codes: ["risk_rejected_no_override"] },
        titles: ["风控复核"],
        contains: ["当前尝试终止", "关键风险无法通过补证消除", "关闭本轮尝试"],
      },
    ];

    for (const item of cases) {
      stubDossierResponse(item.id, {
        ...mockDossierReadModel(),
        workflow: { workflow_id: item.id, title: "风控状态 A 股研究", current_stage: "S5", state: "running" },
        risk_review: item.risk_review,
      });
      await bootWorkbench(`/investment/${item.id}?stage=S5`);
      await flushAsyncWork();

      const text = document.body.textContent ?? "";
      expect(directPanelTitles(), item.id).toEqual(item.titles);
      expect(document.querySelectorAll(".stage-unified-summary-card"), item.id).toHaveLength(1);
      for (const expected of item.contains) {
        expect(text, item.id).toContain(expected);
      }
      expect(text, item.id).not.toContain("老板不能直接绕过");
      expect(text, item.id).not.toContain("复核人");
      expect(text, item.id).not.toContain("审批与交易边界");
    }
  });

  it("shows S6 execution states with order, fill, cost and no-trade details", async () => {
    const cases = [
      {
        id: "wf-s6-filled",
        paper_execution: {
          status: "filled",
          pricing_method: "minute_vwap",
          window: "normal 2 小时",
          fees: { commission: "5 CNY", stamp_tax: "0 CNY" },
          taxes: { transfer_fee: "0.2 CNY" },
          slippage: "5 bps",
          t_plus_one: "locked_until_next_trading_day",
        },
        titles: ["纸面执行"],
        contains: ["已按规则模拟成交", "风控已通过 / 例外已确认", "方法：分钟成交量加权均价", "成本：", "T+1：资金或持仓次日可用", "进入 S7 归因反思"],
      },
      {
        id: "wf-s6-unfilled",
        paper_execution: {
          status: "expired",
          pricing_method: "minute_twap",
          window: "urgent 30 分钟",
          fees: {},
          t_plus_one: "not_applicable",
        },
        titles: ["纸面执行"],
        contains: ["条件满足，但价格窗口未命中", "订单已释放", "不产生持仓变化", "保留执行记录供归因分析"],
      },
      {
        id: "wf-s6-blocked",
        paper_execution: {
          status: "blocked",
          pricing_method: "not_released",
          window: "不可用",
          fees: {},
          t_plus_one: "not_started",
        },
        titles: ["纸面执行"],
        contains: ["缺少成交所需的核心数据", "分钟级价格 / 成交量", "这是 S6 成交门槛，不是当前 S3 辩论受阻原因", "补齐执行核心数据后再判断"],
      },
    ];

    for (const item of cases) {
      stubDossierResponse(item.id, {
        ...mockDossierReadModel(),
        workflow: { workflow_id: item.id, title: "执行状态 A 股研究", current_stage: "S6", state: "running" },
        risk_review: { review_result: "approved", repairability: "not_required", owner_exception_required: false, reason_codes: [] },
        paper_execution: item.paper_execution,
      });
      await bootWorkbench(`/investment/${item.id}?stage=S6`);
      await flushAsyncWork();

      const text = document.body.textContent ?? "";
      expect(directPanelTitles(), item.id).toEqual(item.titles);
      expect(document.querySelectorAll(".stage-unified-summary-card"), item.id).toHaveLength(1);
      for (const expected of item.contains) {
        expect(text, item.id).toContain(expected);
      }
      expect(text, item.id).not.toContain("审批边界");
    }
  });

  it("shows S7 attribution and reflection states without inventing attribution from missing execution", async () => {
    const cases = [
      {
        id: "wf-s7-attributed",
        attribution: {
          summary: "本轮归因已生成。",
          links: ["attribution-report-001"],
          market_result: "小幅跑赢基准",
          decision_quality: 0.82,
          execution_quality: 0.76,
          risk_quality: 0.88,
          data_quality: 0.91,
          evidence_quality: 0.84,
          condition_hit: "hit",
          improvement_items: [],
          needs_cfo_interpretation: false,
        },
        titles: ["归因复盘"],
        contains: ["本轮结果已进入复盘", "收益、风险、成本、滑点", "决策质量、执行质量、风控质量", "正常：自动发布归因"],
      },
      {
        id: "wf-s7-empty",
        attribution: { summary: "暂无归因。", links: [] },
        titles: ["归因复盘"],
        contains: ["没有可复盘的执行结果", "当前还没有纸面成交或持仓变化", "不能用未发生的执行倒推角色质量", "等待执行样本或周期复盘窗口"],
      },
      {
        id: "wf-s7-reflection",
        attribution: {
          summary: "执行核心阻断触发反思。",
          links: ["reflection-assignment-001"],
          improvement_items: ["execution_core blocked", "evidence gap"],
          needs_cfo_interpretation: true,
        },
        titles: ["归因复盘"],
        contains: ["命中改进触发条件", "风控拒绝 / 执行核心阻断 / 数据冲突", "CFO 解释", "只对新任务或新尝试生效"],
      },
    ];

    for (const item of cases) {
      stubDossierResponse(item.id, {
        ...mockDossierReadModel(),
        workflow: { workflow_id: item.id, title: "复盘 A 股研究", current_stage: "S7", state: "running" },
        attribution: item.attribution,
      });
      await bootWorkbench(`/investment/${item.id}?stage=S7`);
      await flushAsyncWork();

      const text = document.body.textContent ?? "";
      expect(directPanelTitles(), item.id).toEqual(item.titles);
      expect(document.querySelectorAll(".stage-unified-summary-card"), item.id).toHaveLength(1);
      for (const expected of item.contains) {
        expect(text, item.id).toContain(expected);
      }
      expect(text, item.id).not.toContain("归因状态");
    }
  });

  it("removes explanatory boundary cards from S5 S6 and folds S7 attribution into reflection", async () => {
    await bootWorkbench("/investment/wf-001?stage=S5");
    await flushAsyncWork();
    expect(directPanelTitles()).toEqual(["风控复核"]);
    expect(document.body.textContent).not.toContain("审批与交易边界");

    await bootWorkbench("/investment/wf-001?stage=S6");
    await flushAsyncWork();
    expect(directPanelTitles()).toEqual(["纸面执行"]);
    expect(document.body.textContent).not.toContain("审批边界");

    await bootWorkbench("/investment/wf-001?stage=S7");
    await flushAsyncWork();
    expect(directPanelTitles()).toEqual(["归因复盘"]);
    expect(document.body.textContent).not.toContain("归因状态");
    expect(document.body.textContent).toContain("没有可复盘的执行结果");
  });

  it("opens the S2 analyst drawer from a clicked analyst row", async () => {
    await bootWorkbench("/investment/wf-001?stage=S2");
    await flushAsyncWork();

    expect(document.querySelector(".dossier-detail-drawer")).toBeNull();

    await act(async () => {
      detailRowByText("量化分析师").click();
    });
    await flushAsyncWork();

    const text = document.querySelector(".dossier-detail-drawer")?.textContent ?? "";
    expect(text).toContain("量化分析师");
    expect(text).toContain("趋势和因子仍偏正面");
    expect(text).toContain("维持观察，不单独推动 S4");
  });

  it("switches governance panels and keeps query-driven task filters visible", async () => {
    await bootWorkbench("/governance");

    await act(async () => {
      linkByName("健康").click();
    });

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?panel=health");
    expect(document.querySelector('[data-panel="health"]')).not.toBeNull();
    expect(document.body.textContent).toContain("健康");

    await bootWorkbench("/");

    await act(async () => {
      linkByName("待办").click();
    });

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?panel=todos");
    expect(document.body.textContent).toContain("待办");
    expect(document.body.textContent).toContain("办理审批");
  });

  it("loads governance tasks approvals and changes from their API read models", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            { task_id: "task-api", task_type: "system_task", current_state: "ready", reason_code: "data_source_degraded" },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            { approval_id: "ap-api", approval_type: "owner_approval", subject: "API 审批事项", trigger_reason: "api_approval_reason", effective_scope: "new_task" },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([
          { change_id: "gov-api", change_type: "agent_capability", impact_level: "high", state: "owner_pending", effective_scope: "test" },
        ]);
      }
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({ team_health: { healthy_agent_count: 9 }, agent_cards: [] });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("系统事项");
    expect(document.body.textContent).toContain("数据源降级");

    expect(document.body.textContent).toContain("API 审批事项");
    expect(document.body.textContent).not.toContain("ap-api");

    await act(async () => {
      linkByName("变更").click();
    });
    expect(document.body.textContent).toContain("团队能力提升");
    expect(document.body.textContent).not.toContain("gov-api");
    expect(document.body.textContent).not.toContain("只影响test");
    expect(document.body.textContent).toContain("后续任务");
  });

  it("submits approval decisions with visible local feedback instead of a dead detail page", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/approvals/ap-001/decision")) {
        expect(init?.method).toBe("POST");
        return await new Promise<Response>(() => {});
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/approvals/ap-001");

    await act(async () => {
      buttonByName("要求修改").click();
    });

    expect(document.body.textContent).toContain("正在提交：要求修改");
    expect(document.body.textContent).toContain("等待后端返回最新审批状态");
    expect(buttonByName("通过").disabled).toBe(true);
  });

  it("loads approval detail by route id and submits the same approval id", async () => {
    let submittedApprovalId: string | null = null;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            {
              approval_id: "ap-route",
              subject: "API 高影响能力草案",
              trigger_reason: "api_high_impact_governance",
              recommended_decision: "rejected",
              effective_scope: "new_attempt",
              comparison_options: ["方案 A：拒绝", "方案 B：要求修改"],
              risk_and_impact: ["API 风险影响"],
              timeout_disposition: "不生效",
              rollback_ref: "rollback-api",
              evidence_refs: ["artifact-api-approval"],
              trace_route: "/investment/wf-api/trace",
              allowed_actions: ["rejected"],
            },
          ],
        });
      }
      if (href.endsWith("/api/approvals/ap-route/decision")) {
        submittedApprovalId = "ap-route";
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          approval_id: "ap-route",
          decision: "rejected",
          effective_scope: "new_attempt",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/approvals/ap-route");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 高影响能力提升方案");
    expect(document.body.textContent).toContain("API 风险影响");
    expect(document.body.textContent).toContain("已有回滚方案");

    await act(async () => {
      buttonByName("拒绝").click();
    });
    await flushAsyncWork();

    expect(submittedApprovalId).toBe("ap-route");
    expect(document.body.textContent).toContain("后端状态：拒绝");
  });

  it("preserves governance return path when entering trace from an approval detail page", async () => {
    await bootWorkbench("/governance/approvals/ap-001");

    await act(async () => {
      linkByName("审计追溯").click();
    });

    expect(window.location.pathname).toBe("/investment/wf-001/trace");
    expect(window.location.search).toBe("?returnTo=%2Fgovernance%2Fapprovals%2Fap-001");
    expect(document.body.textContent).toContain("返回审批包");

    await act(async () => {
      linkByName("返回审批包").click();
    });

    expect(window.location.pathname).toBe("/governance/approvals/ap-001");
  });

  it("renders complete approval packet materials and timeout/no-effect boundaries", async () => {
    await bootWorkbench("/governance/approvals/ap-001");

    expect(document.body.textContent).toContain("对比分析");
    expect(document.body.textContent).toContain("影响范围");
    expect(document.body.textContent).toContain("替代方案");
    expect(document.body.textContent).toContain("风险与影响");
    expect(document.body.textContent).toContain("回滚方式");
    expect(document.body.textContent).toContain("超时不生效");
    expect(document.body.textContent).toContain("只对后续任务生效");
    expect(document.body.textContent).not.toContain("批准继续执行");
  });

  it("renders the Knowledge page as owner-readable cards with clear source and action labels", async () => {
    await bootWorkbench("/knowledge");

    for (const label of [
      "每日简报",
      "暂无每日简报。",
      "研究资料包",
      "暂无可复核资料包。",
      "经验库",
      "经验记录",
      "保存经验",
      "资料关系",
      "整理建议",
      "应用整理建议",
      "上下文使用记录",
    ]) {
      expect(document.body.textContent).toContain(label);
    }

    expect(document.body.textContent).not.toContain("记忆工作区");
    expect(document.body.textContent).not.toContain("捕获记忆");
    expect(document.body.textContent).not.toContain("今日影响：");
    expect(document.body.textContent).not.toContain("下一步：");
    expect(document.body.textContent).not.toContain("关系图");
    expect(document.body.textContent).not.toContain("组织建议");
    expect(document.body.textContent).not.toContain("应用组织建议");
    expect(document.body.textContent).not.toContain("validated_context");
    expect(document.body.textContent).not.toContain("memory-relation");
    expect(document.body.textContent).not.toContain("知识与方法提案");
    expect(document.body.textContent).not.toContain("进入治理提案");
    expect(document.body.textContent).not.toContain("capture / review / digest / organize");
    expect(document.body.textContent).not.toContain("Context 注入检查");
    expect(document.body.textContent).not.toContain("why_included");
    expect(document.body.textContent).not.toContain("denied refs");
    expect(document.body.textContent).not.toContain("diff / manifest");
    expect(document.body.textContent).not.toContain("立即生效");
    expect(document.body.textContent).not.toContain("覆盖旧 MemoryVersion");
  });

  it("captures owner memory through the Knowledge memory API", async () => {
    let capturedBody: Record<string, unknown> | null = null;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/knowledge/memory-items") && init?.method === "POST") {
        capturedBody = JSON.parse(String(init.body));
        return mockJsonResponse({
          memory_id: "memory-new",
          title: "Owner 捕获笔记",
          current_version_id: "memory-version-new",
          sensitivity: "public_internal",
          tags: ["owner_capture"],
        });
      }
      if (href.endsWith("/api/knowledge/memory-items")) {
        return mockJsonResponse([]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    setInputValue(inputByLabel("经验内容"), "复盘今天的硬异议处理");
    await act(async () => {
      buttonByName("保存经验").click();
    });
    await flushAsyncWork();

    expect(capturedBody).toMatchObject({
      source_type: "owner_note",
      content_markdown: "复盘今天的硬异议处理",
      suggested_memory_type: "research_note",
      sensitivity: "public_internal",
      client_seen_context_snapshot_id: "ctx-v1",
    });
    expect(document.body.textContent).toContain("经验已保存，可在经验记录里复核。");
    expect(document.body.textContent).not.toContain("memory-new");
    expect(document.body.textContent).not.toContain("经网关写入");
  });

  it("does not apply Knowledge organize suggestions without a backend suggestion", async () => {
    let relationBody: Record<string, unknown> | null = null;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/knowledge/memory-items/memory-api-1/relations")) {
        relationBody = JSON.parse(String(init?.body));
        throw new Error("relation should not be posted without a backend suggestion");
      }
      if (href.endsWith("/api/knowledge/memory-items")) {
        return mockJsonResponse([
          {
            memory_id: "memory-api-1",
            title: "API 研究笔记",
            current_version_id: "version-api-1",
            relations: [],
          },
        ]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    expect(buttonByName("应用整理建议").disabled).toBe(true);
    await flushAsyncWork();

    expect(relationBody).toBeNull();
    expect(document.body.textContent).toContain("暂无可应用整理建议");
  });

  it("saves capability drafts as governance changes and keeps in-flight runs untouched", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({ team_health: { healthy_agent_count: 9 }, agent_cards: [] });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          editable_fields: [{ field: "default_model_profile" }],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task"],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-drafts")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          draft_id: "draft-api",
          governance_change_ref: "gov-change-api",
          impact_level: "high",
          effective_scope: "new_task",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/quant_analyst/config");

    await act(async () => {
      buttonByName("提交提升方案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("已生成治理变更");
    expect(document.body.textContent).toContain("高影响，需进入老板审批");
    expect(document.body.textContent).toContain("只对后续任务生效");
    expect(document.body.textContent).toContain("在途任务继续使用旧快照");
  });

  it("submits capability draft saves through the governance draft API when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/quant_analyst")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          display_name: "Quant Analyst",
          capability_summary: "api profile",
          can_do: [],
          cannot_do: [],
          quality_metrics: { schema_pass_rate: 1, evidence_quality: 1 },
          denied_actions: [],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          editable_fields: [{ field: "default_model_profile" }],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task"],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-drafts")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          draft_id: "draft-api-1",
          agent_id: "quant_analyst",
          governance_change_ref: "gov-change-api-1",
          impact_level: "high",
          effective_scope: "new_task",
        });
      }
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({
          team_health: { healthy_agent_count: 9 },
          agent_cards: [],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/quant_analyst/config");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("提交提升方案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("gov-change-api-1");
  });

  it("does not route knowledge proposals from the knowledge page", async () => {
    await bootWorkbench("/knowledge");

    const proposalLinks = Array.from(document.querySelectorAll("a")).filter((link) =>
      link.textContent?.includes("治理提案"),
    );
    expect(proposalLinks).toHaveLength(0);
    expect(document.body.textContent).not.toContain("知识与方法提案");
  });

  it("submits approval decisions through the approval decision API when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/approvals/ap-001/decision")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          approval_id: "ap-001",
          decision: "approved",
          effective_scope: "new_task",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/approvals/ap-001");

    await act(async () => {
      buttonByName("要求修改").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("后端状态：通过");
    expect(document.body.textContent).toContain("生效范围：后续任务");
    expect(document.body.textContent).not.toContain("已提交：要求修改 · 后端已接收");
  });

  it("shows snapshot mismatch guidance when approval decision API returns 409", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            {
              approval_id: "ap-001",
              subject: "API 审批包",
              trigger_reason: "high_impact_agent_capability_change",
              allowed_actions: ["request_changes"],
            },
          ],
        });
      }
      if (href.endsWith("/api/approvals/ap-001/decision")) {
        return {
          ok: false,
          status: 409,
          json: async () => ({
            error: {
              code: "SNAPSHOT_MISMATCH",
              reason_code: "client_seen_version_mismatch",
              trace_id: "trace-conflict",
            },
          }),
        } as Response;
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/approvals/ap-001");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("要求修改").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("审批状态已变化，请刷新");
    expect(document.body.textContent).toContain("SNAPSHOT_MISMATCH");
    expect(document.body.textContent).toContain("trace-conflict");
  });

  it("merges partial API team cards with the nine-agent roster instead of dropping missing agents", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({
          team_health: {
            healthy_agent_count: 1,
            active_agent_run_count: 1,
            pending_draft_count: 0,
            failed_or_denied_count: 0,
            last_quality_window: "live",
          },
          agent_cards: [
            {
              agent_id: "macro_analyst",
              display_name: "API 宏观分析员",
              profile_version: "2.1.0",
              skill_package_version: "macro-skill@2.1.0",
              prompt_version: "2.0.0",
              context_snapshot_version: "ctx-api",
              recent_quality_score: 0.97,
              failure_count: 0,
              denied_action_count: 0,
              config_draft_entry: "governance_draft_only",
              weakness_tags: [],
            },
          ],
          capability_drafts: [],
          quality_alerts: [],
          governance_links: ["/governance/team/macro_analyst/config"],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 宏观分析员");
    expect(document.body.textContent).not.toContain("2.1.0");
    expect(document.querySelectorAll(".agent-card")).toHaveLength(9);
    expect(document.body.textContent).toContain("CIO");
    expect(document.body.textContent).toContain("量化分析师");
    expect(document.body.textContent).not.toContain("Macro Analyst");
  });

  it("shows team health, attribution refs, weaknesses and keeps version boundaries out of the default team page", async () => {
    await bootWorkbench("/governance/team");

    expect(document.body.textContent).toContain("团队健康");
    expect(document.body.textContent).toContain("待处理能力提升");
    expect(document.body.textContent).toContain("失败/越权");
    expect(document.body.textContent).toContain("证据不足");
    expect(document.body.textContent).toContain("敏感字段拒绝");
    expect(document.body.textContent).not.toContain("上下文 ctx-v1");
    expect(document.body.textContent).not.toContain("Agent");

    await bootWorkbench("/governance/team/quant_analyst");

    expect(document.body.textContent).toContain("CFO 归因");
    expect(document.body.textContent).toContain("cfo-attribution-001");
    expect(document.body.textContent).toContain("版本与权限");
    expect(document.body.textContent).toContain("提示词 1.0.0");
    expect(document.body.textContent).toContain("越权/失败");

    await bootWorkbench("/governance/team/macro_analyst");

    expect(document.body.textContent).toContain("越权/失败");
    expect(document.body.textContent).toContain("敏感字段拒绝");
  });

  it("shows submitting feedback and disables duplicate capability draft saves", async () => {
    let resolveDraft: ((value: Response) => void) | undefined;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/quant_analyst")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          display_name: "Quant Analyst",
          capability_summary: "api profile",
          can_do: [],
          cannot_do: [],
          quality_metrics: { schema_pass_rate: 1, evidence_quality: 1 },
          denied_actions: [],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          editable_fields: [{ field: "default_model_profile" }],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task"],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-drafts")) {
        expect(init?.method).toBe("POST");
        return await new Promise<Response>((resolve) => {
          resolveDraft = resolve;
        });
      }
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({ team_health: { healthy_agent_count: 9 }, agent_cards: [] });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/quant_analyst/config");
    await flushAsyncWork();

    const saveButton = buttonByName("提交提升方案");
    await act(async () => {
      saveButton.click();
    });

    expect(saveButton.disabled).toBe(true);
    expect(saveButton.textContent).toContain("正在提交");
    expect(document.body.textContent).toContain("正在提交能力提升方案");

    resolveDraft?.(mockJsonResponse({
      draft_id: "draft-api-1",
      agent_id: "quant_analyst",
      governance_change_ref: "gov-change-api-1",
      impact_level: "high",
      effective_scope: "new_task",
    }));
    await flushAsyncWork();
    expect(document.body.textContent).toContain("gov-change-api-1");
  });

  it("shows capability draft API failure instead of fallback success", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/quant_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "quant_analyst",
          editable_fields: [{ field: "default_model_profile" }],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task"],
        });
      }
      if (href.endsWith("/api/team/quant_analyst/capability-drafts")) {
        expect(init?.method).toBe("POST");
        return { ok: false, json: async () => ({ data: null }) } as Response;
      }
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({ team_health: { healthy_agent_count: 9 }, agent_cards: [] });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/quant_analyst/config");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("提交提升方案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("提升方案提交失败");
    expect(document.body.textContent).not.toContain("已生成治理变更 gov-change-001");
  });

  it("labels non-preview read model loading failures and exposes retry", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new Error("api unavailable");
    }));

    await bootWorkbench("/governance/team/unknown_agent");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("真实数据不可用");
    expect(document.body.textContent).toContain("API 未返回 read model");
    expect(document.body.textContent).not.toContain("读取最新数据失败");
    expect(buttonByName("重试")).not.toBeNull();
    expect(document.body.textContent).toContain("能做什么");
  });

  it("loads agent profile and capability config from /api/team endpoints when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/macro_analyst")) {
        return mockJsonResponse({
          agent_id: "macro_analyst",
          display_name: "API 宏观分析员",
          capability_summary: "只读 API 画像",
          can_do: ["读取 API 资料", "提交 API 产物"],
          cannot_do: ["热改运行中任务", "直接写业务库"],
          quality_metrics: {
            schema_pass_rate: 0.98,
            evidence_quality: 0.93,
          },
          denied_actions: [],
          config_draft_entry: "governance_draft_only",
        });
      }
      if (href.endsWith("/api/team/macro_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "macro_analyst",
          editable_fields: [
            { field: "default_model_profile" },
            { field: "default_tool_profile_id" },
          ],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task", "new_attempt"],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/macro_analyst");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 宏观分析员");
    expect(document.body.textContent).toContain("读取 API 资料");
    expect(document.body.textContent).toContain("热改运行中任务");

    await bootWorkbench("/governance/team/macro_analyst/config");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("默认模型配置");
    expect(document.body.textContent).toContain("只能提交提升方案");
  });

  it("opens governance team cards with live object-shaped permissions and submits a capability plan", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team")) {
        return mockJsonResponse({
          team_health: { healthy_agent_count: 9, active_agent_run_count: 2, pending_draft_count: 1, failed_or_denied_count: 0 },
          agent_cards: [
            {
              agent_id: "cio",
              display_name: "CIO",
              role: "cio",
              profile_version: "1.0.0",
              skill_package_version: "cio-decision-synthesis",
              prompt_version: "1.0.0",
              context_snapshot_version: "ctx-v1",
              recent_quality_score: 0.96,
              failure_count: 0,
              denied_action_count: 0,
              weakness_tags: ["证据链追问偏慢"],
            },
          ],
        });
      }
      if (href.endsWith("/api/team/cio")) {
        return mockJsonResponse({
          agent_id: "cio",
          display_name: "CIO 能力画像",
          capability_summary: "负责投资语义收口和关键矛盾追问。",
          can_do: ["形成 IC 语义结论", "要求补证", "提出重开建议"],
          cannot_do: ["直接推进流程", "绕过风控拒绝"],
          read_permissions: {
            db_read_views: ["readonly_business_view", "artifact_read_model"],
            file_scopes: ["business_materials", "active_skill_packages"],
          },
          write_permissions: {
            artifact_types: ["CIODecisionMemo", "ICChairBrief"],
            command_types: ["ask_question", "request_view_update", "request_reopen"],
          },
          service_permissions: ["data_readiness", "market_state", "risk"],
          tool_permissions: {
            network_policy: ["approved_public_sources"],
            terminal_policy: ["readonly_diagnostics"],
            skill_packages: ["cio-decision-synthesis"],
          },
          collaboration_commands: ["ask_question", "request_view_update", "request_reopen"],
          quality_metrics: { schema_pass_rate: 0.99, evidence_quality: 0.94 },
          weakness_tags: ["证据链追问偏慢"],
          cfo_attribution_refs: ["CFO 归因：证据贡献需继续观察"],
          denied_actions: [{ reason_code: "direct_write_denied" }],
          failure_records: [{ reason_code: "schema_validation_failed" }],
        });
      }
      if (href.endsWith("/api/team/cio/capability-config")) {
        return mockJsonResponse({
          agent_id: "cio",
          editable_fields: [
            { field: "service_permissions" },
            { field: "collaboration_commands" },
            { field: "prompt_version" },
            { field: "timeout_seconds" },
          ],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task", "new_attempt"],
        });
      }
      if (href.endsWith("/api/team/cio/capability-drafts")) {
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          draft_id: "draft-cio-api",
          agent_id: "cio",
          governance_change_ref: "gov-change-cio-api",
          impact_level: "high",
          effective_scope: "new_task",
        });
      }
      return defaultFetch(input);
    }));

    await bootWorkbench("/governance?panel=team");
    await flushAsyncWork();

    const profileLink = Array.from(document.querySelectorAll("a")).find((link) =>
      link.getAttribute("href") === "/governance/team/cio",
    );
    expect(profileLink).not.toBeUndefined();

    await act(async () => {
      (profileLink as HTMLAnchorElement).click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/governance/team/cio");
    const profileText = document.body.textContent ?? "";
    expect(profileText).toContain("CIO 能力画像");
    expect(profileText).toContain("能做什么");
    expect(profileText).toContain("版本与权限");
    expect(profileText).toContain("工具权限");
    expect(profileText).toContain("授权网络来源");
    expect(profileText).toContain("证据链追问偏慢");
    expect(profileText).not.toContain("[object Object]");
    expect(profileText).not.toBe("");

    await act(async () => {
      linkByName("能力提升方案").click();
    });
    await flushAsyncWork();

    expect(window.location.pathname).toBe("/governance/team/cio/config");
    expect(document.body.textContent).toContain("服务权限");
    expect(document.body.textContent).toContain("协作命令");
    expect(document.body.textContent).toContain("只提交治理变更");

    await act(async () => {
      buttonByName("提交提升方案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("gov-change-cio-api");
    expect(document.body.textContent).toContain("只对后续任务生效");
    expect(document.body.textContent).toContain("在途任务继续使用旧快照");
  });

  it("shows a team detail fallback instead of blanking the whole workbench on render errors", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/cio")) {
        return mockJsonResponse({
          agent_id: "cio",
          display_name: { malformed: "CIO" },
          can_do: ["形成 IC 语义结论"],
          cannot_do: ["直接推进流程"],
          tool_permissions: ["readonly_diagnostics"],
          quality_metrics: { schema_pass_rate: 1, evidence_quality: 1 },
          denied_actions: [],
        });
      }
      return defaultFetch(input);
    }));

    await bootWorkbench("/governance/team/cio");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("团队画像暂不可用");
    expect(document.body.textContent).toContain("返回团队");
    expect(document.body.textContent).not.toBe("");
  });

  it("falls back to fixture team data when /api/team is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new Error("api unavailable");
    }));

    await bootWorkbench("/governance/team");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("CIO");
    expect(document.body.textContent).toContain("量化分析师");
  });

  it("loads knowledge memory summaries from /api/knowledge/memory-items when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/knowledge/memory-items")) {
        return mockJsonResponse([
          {
            memory_id: "memory-api-1",
            title: "API 研究笔记",
            relations: [{ target_ref: "artifact-api-1", relation_type: "supports" }],
            why_included: "api_context",
            current_version_id: "ctx-api-1",
            sensitivity: "public_internal",
          },
        ]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 研究笔记");
    expect(document.body.textContent).toContain("资料关系 · 支撑 · 1 条");
  });

  it("captures memory and keeps organize action disabled without backend suggestions", async () => {
    let captured = false;
    let relationApplied = false;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/knowledge/memory-items") && init?.method !== "POST") {
        return mockJsonResponse([
          {
            memory_id: "memory-api-1",
            title: "API 研究笔记",
            current_version_id: "version-api-1",
            relations: [],
          },
        ]);
      }
      if (href.endsWith("/api/knowledge/memory-items") && init?.method === "POST") {
        captured = true;
        return mockJsonResponse({
          memory_id: "memory-created-1",
          title: "Owner 捕获记忆",
          current_version_id: "version-created-1",
        });
      }
      if (href.endsWith("/api/knowledge/memory-items/memory-api-1/relations")) {
        relationApplied = true;
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          source_memory_id: "memory-api-1",
          target_ref: "collection:政策/质量",
          relation_type: "applies_to",
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/knowledge");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("保存经验").click();
    });
    await flushAsyncWork();

    expect(buttonByName("应用整理建议").disabled).toBe(true);
    await flushAsyncWork();

    expect(captured).toBe(true);
    expect(relationApplied).toBe(false);
    expect(document.body.textContent).toContain("经验已保存，可在经验记录里复核。");
    expect(document.body.textContent).toContain("暂无可应用整理建议");
    expect(document.body.textContent).not.toContain("memory-created-1");
  });

  it("loads trace runs, events and handoffs from workflow read endpoints when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/workflows/wf-1/agent-runs")) {
        return mockJsonResponse([
          {
            agent_run_id: "run-api-1",
            stage: "S2",
            profile_version: "api-profile@2.0.0",
            run_goal: "基本面分析师补充资产质量证据",
            agent_id: "fundamental_analyst",
            status: "completed",
            context_slice_id: "ctx-api-1",
          },
        ]);
      }
      if (href.endsWith("/api/workflows/wf-1/collaboration-events")) {
        return mockJsonResponse([
          {
            event_type: "handoff_created",
            payload: { business_summary: "CIO 已把基本面硬异议交给风控复核" },
            summary: "API 交接事件",
          },
        ]);
      }
      if (href.endsWith("/api/workflows/wf-1/handoffs")) {
        return mockJsonResponse([
          {
            from_stage: "S2",
            to_stage_or_agent: "S3",
            blockers: ["api blocker"],
          },
        ]);
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/investment/wf-1/trace");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("基本面分析师补充资产质量证据");
    expect(document.body.textContent).toContain("已生成交接 · CIO 已把基本面硬异议交给风控复核");
    expect(document.body.textContent).toContain("S2 -> S3 · API 阻断项");
    expect(document.body.textContent).not.toContain("run-api-1");
    expect(document.body.textContent).not.toContain("ctx-api-1");
    expect(document.body.textContent).not.toContain("api-profile@2.0.0");
    expect(document.body.textContent).not.toContain("AgentRun");
  });

  it("does not replace empty workflow trace APIs with fixture process records", async () => {
    await bootWorkbench("/investment/wf-001/trace");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(text).toContain("暂无真实过程记录");
    expect(text).not.toContain("事件分析师补充公告影响");
    expect(text).not.toContain("Event Analyst 补证中");
    expect(text).not.toContain("hard dissent 交接 Risk");
    expect(text).not.toContain("ctx-v1");
    expect(text).not.toContain("run-cio-001");
  });

  it("renders capability config route and editable fields in owner-readable copy", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/team/fundamental_analyst/capability-config")) {
        return mockJsonResponse({
          agent_id: "fundamental_analyst",
          editable_fields: [{ field: "default_skill_packages" }, { field: "service_permissions" }],
          forbidden_direct_update_reason: "governance_draft_only",
          effective_scope_options: ["new_task", "current_attempt_only"],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance/team/fundamental_analyst/config");
    await flushAsyncWork();

    const text = document.body.textContent ?? "";
    expect(text).toContain("基本面研究");
    expect(text).toContain("默认能力包");
    expect(text).toContain("服务权限");
    expect(text).toContain("当前尝试");
    expect(text).not.toContain("fundamental_analyst");
    expect(text).not.toContain("default_skill_packages");
  });

  it("loads finance overview from /api/finance/overview when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [
            { asset_type: "cash", valuation: { amount: 888000, currency: "CNY" }, boundary_label: "finance_planning_only" },
            { asset_type: "fund", valuation: { amount: 66000, currency: "CNY" }, boundary_label: "finance_planning_only" },
          ],
          finance_health: {
            liquidity: 888000,
            risk_budget: { budget_ref: "risk-budget-api" },
            stress_test_summary: "api_stress_checked",
          },
          manual_todo: [{ risk_hint: "api_tax_window" }],
          sensitive_data_notice: { redaction_applied: true },
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/finance");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("现金 · 888,000 CNY");
    expect(document.body.textContent).toContain("基金 · 66,000 CNY");
    expect(document.body.textContent).toContain("API 风险预算");
  });

  it("translates finance and approval raw backend tokens before rendering owner pages", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [
            { asset_type: "income", valuation: { amount: 50000, currency: "CNY" }, boundary_label: "trade_chain_allowed" },
          ],
          finance_health: {
            liquidity: 50000,
            risk_budget: { budget_ref: "risk-budget-finance-v1" },
            stress_test_summary: "tax_reminder",
          },
          manual_todo: [{ risk_hint: "tax_reminder" }],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            {
              approval_id: "ap-raw",
              approval_type: "owner_exception",
              subject: "组合偏离例外审批",
              trigger_reason: "cio_deviation",
              recommended_decision: "approve_exception_only_if_risk_accepted",
              effective_scope: "current_attempt_only",
              comparison_options: ["follow_optimizer", "higher_single_name_exposure"],
              risk_and_impact: ["cio_deviation", { option: "follow_optimizer", risk: "higher_single_name_exposure" }],
              timeout_policy: "timeout_means_no_execution",
              rollback_ref: "gov-change-001",
              evidence_refs: ["decision-guard-1", "risk-review-1"],
              trace_route: "/investment/wf-001/trace",
              allowed_actions: ["approved", "rejected", "request_changes"],
            },
          ],
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/finance");
    await flushAsyncWork();
    let text = document.body.textContent ?? "";
    expect(text).toContain("收入");
    expect(text).toContain("可进入 A 股投研链路");
    expect(text).toContain("税务提醒");

    await bootWorkbench("/governance/approvals/ap-raw");
    await flushAsyncWork();
    text = document.body.textContent ?? "";
    expect(text).toContain("仅在风控接受风险后批准例外");
    expect(text).toContain("当前尝试");
    expect(text).toContain("跟随优化器建议");
    expect(text).toContain("CIO 偏离");
    expect(text).toContain("已有回滚方案");
    for (const token of [
      "trade_chain_allowed",
      "tax_reminder",
      "income",
      "approve_exception_only_if_risk_accepted",
      "current_attempt_only",
      "follow_optimizer",
      "higher_single_name_exposure",
      "cio_deviation",
      "gov-change-001",
      "decision-guard-1",
      "risk-review-1",
    ]) {
      expect(text).not.toContain(token);
    }
  });

  it("updates finance asset profile through /api/finance/assets with browser feedback", async () => {
    let updateCalled = false;
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [],
          finance_health: { liquidity: 1000000, risk_budget: { budget_ref: "risk-budget-ui" } },
          manual_todo: [],
        });
      }
      if (href.endsWith("/api/finance/assets")) {
        updateCalled = true;
        expect(init?.method).toBe("POST");
        return mockJsonResponse({
          asset_id: "asset-cash-ui",
          asset_type: "cash",
          valuation: { amount: 1000000, currency: "CNY" },
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/finance");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("提交财务档案").click();
    });
    await flushAsyncWork();

    expect(updateCalled).toBe(true);
    expect(document.body.textContent).toContain("财务档案已更新 asset-cash-ui");
    expect(document.body.textContent).toContain("不触发审批、执行或交易链路");
  });

  it("explains finance profile write failures as missing API connection instead of a vague retry error", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/finance/overview")) {
        return mockJsonResponse({
          asset_profile: [],
          finance_health: { liquidity: 1000000, risk_budget: { budget_ref: "risk-budget-ui" } },
          manual_todo: [],
        });
      }
      if (href.endsWith("/api/finance/assets") && init?.method === "POST") {
        throw new Error("api unavailable");
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/finance");
    await flushAsyncWork();

    await act(async () => {
      buttonByName("提交财务档案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("API 未连接，财务档案未写入");
    expect(document.body.textContent).not.toContain("财务档案更新失败，请重试");
  });

  it("loads governance health from /api/devops/health when available", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/devops/health")) {
        return mockJsonResponse({
          routine_checks: [{ check_id: "api-health", status: "observed" }],
          incidents: [{ incident_id: "incident-api-1", status: "triaged", incident_type: "runner" }],
          recovery: [{ plan_id: "recovery-api-1", investment_resume_allowed: false }],
          audit_trail: [],
          metrics: { incident_open_total: 1 },
        });
      }
      throw new Error(`unexpected fetch: ${href}`);
    }));

    await bootWorkbench("/governance?panel=health");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("接口健康 · 已观测");
    expect(document.body.textContent).toContain("运行器异常 · 已分诊");
    expect(document.body.textContent).toContain("恢复计划 · 投资恢复未放行");
    expect(document.body.textContent).not.toContain("incident-api-1");
    expect(document.body.textContent).not.toContain("recovery-api-1");
  });
});
