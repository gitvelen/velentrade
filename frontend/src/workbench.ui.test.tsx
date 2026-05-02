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
  const input = Array.from(document.querySelectorAll("input")).find((item) =>
    item.getAttribute("aria-label")?.includes(name),
  );
  if (!input) {
    throw new Error(`input not found: ${name}`);
  }
  return input as HTMLInputElement;
}

function setInputValue(input: HTMLInputElement, value: string) {
  const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
  descriptor?.set?.call(input, value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function mockJsonResponse(data: unknown) {
  return {
    ok: true,
    json: async () => ({ data, meta: { trace_id: "trace-1", generated_at: "2026-05-02T00:00:00Z" } }),
  } as Response;
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("generates a simple request preview only after the owner clicks the preview button", async () => {
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
    expect(document.body.textContent).toContain("正在同步请求预览");
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
    expect(document.body.textContent).toContain("当前查看：S0 任务接收");
  });

  it("keeps vague owner commands in draft and asks concise clarification questions", async () => {
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

    expect(document.body.textContent).toContain("还缺这些信息");
    expect(document.body.textContent).toContain("请补充目标对象或主题");
    expect(document.body.textContent).toContain("请补充希望产出的结果");
    expect(document.body.textContent).not.toContain("确认生成任务卡");
  });

  it("blocks hot patch requests in free chat and shows the governance boundary", async () => {
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
    expect(document.body.textContent).toContain("当前查看：S5 风控复核");
    expect(document.body.textContent).toContain("只切换查看阶段，不推进流程");
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
    expect(document.body.textContent).toContain("API 决策问题");
    expect(document.body.textContent).toContain("API Analyst");
    expect(buttonByName("S1").getAttribute("aria-pressed")).toBe("true");
  });

  it("switches governance panels and keeps query-driven task filters visible", async () => {
    await bootWorkbench("/governance");

    await act(async () => {
      linkByName("健康").click();
    });

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?panel=health");
    expect(document.querySelector('[data-panel="health"]')).not.toBeNull();
    expect(document.body.textContent).toContain("数据/服务健康");

    await bootWorkbench("/");

    await act(async () => {
      linkByName("人工待办").click();
    });

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?task=manual");
    expect(document.body.textContent).toContain("当前筛选：人工待办");
    expect(document.body.textContent).toContain("不进入审批、执行或交易链路");
  });

  it("loads governance tasks approvals and changes from their API read models", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
      if (href.endsWith("/api/tasks")) {
        return mockJsonResponse({
          task_center: [
            { task_id: "task-api", task_type: "system_task", current_state: "running", reason_code: "api_task_reason" },
          ],
        });
      }
      if (href.endsWith("/api/approvals")) {
        return mockJsonResponse({
          approval_center: [
            { approval_id: "ap-api", approval_type: "owner_approval", trigger_reason: "api_approval_reason", effective_scope: "new_task" },
          ],
        });
      }
      if (href.endsWith("/api/governance/changes")) {
        return mockJsonResponse([
          { change_id: "gov-api", change_type: "agent_capability", impact_level: "high", state: "owner_pending", effective_scope: "new_task" },
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
    expect(document.body.textContent).toContain("api_task_reason");

    await act(async () => {
      linkByName("审批").click();
    });
    expect(document.body.textContent).toContain("ap-api");
    expect(document.body.textContent).toContain("api_approval_reason");

    await act(async () => {
      linkByName("变更").click();
    });
    expect(document.body.textContent).toContain("能力草案 gov-api");
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

  it("saves capability drafts as governance changes and keeps in-flight runs untouched", async () => {
    await bootWorkbench("/governance/team/quant_analyst/config");

    await act(async () => {
      buttonByName("保存草案").click();
    });

    expect(document.body.textContent).toContain("已生成治理变更草案");
    expect(document.body.textContent).toContain("高影响，需进入 Owner 审批");
    expect(document.body.textContent).toContain("只对后续任务生效");
    expect(document.body.textContent).toContain("在途 AgentRun 继续使用旧快照");
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
      buttonByName("保存草案").click();
    });
    await flushAsyncWork();

    expect(document.body.textContent).toContain("gov-change-api-1");
  });

  it("opens governance changes from the knowledge page through query state", async () => {
    await bootWorkbench("/knowledge");

    await act(async () => {
      linkByName("进入治理提案").click();
    });

    expect(window.location.pathname).toBe("/governance");
    expect(window.location.search).toBe("?change=default-context");
    expect(document.querySelector('[data-panel="changes"]')).not.toBeNull();
    expect(document.body.textContent).toContain("默认上下文提案");
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
    expect(document.body.textContent).toContain("2.1.0");
    expect(document.querySelectorAll(".agent-card")).toHaveLength(9);
    expect(document.body.textContent).toContain("CIO");
    expect(document.body.textContent).toContain("Quant Analyst");
    expect(document.body.textContent).not.toContain("Macro Analyst");
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

    const saveButton = buttonByName("保存草案");
    await act(async () => {
      saveButton.click();
    });

    expect(saveButton.disabled).toBe(true);
    expect(saveButton.textContent).toContain("正在提交");
    expect(document.body.textContent).toContain("正在提交能力草案");

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

    expect(document.body.textContent).toContain("default_model_profile");
    expect(document.body.textContent).toContain("governance_draft_only");
  });

  it("falls back to fixture team data when /api/team is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new Error("api unavailable");
    }));

    await bootWorkbench("/governance/team");
    await flushAsyncWork();

    expect(document.body.textContent).toContain("CIO");
    expect(document.body.textContent).toContain("Quant Analyst");
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
    expect(document.body.textContent).toContain("memory-api-1 支撑 artifact-api-1");
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
          },
        ]);
      }
      if (href.endsWith("/api/workflows/wf-1/collaboration-events")) {
        return mockJsonResponse([
          {
            event_type: "handoff_created",
            payload: {},
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

    expect(document.body.textContent).toContain("run-api-1");
    expect(document.body.textContent).toContain("handoff_created · API 交接事件");
    expect(document.body.textContent).toContain("S2 -> S3 · api blocker");
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

    expect(document.body.textContent).toContain("cash · 888000 CNY");
    expect(document.body.textContent).toContain("fund · 66000 CNY");
    expect(document.body.textContent).toContain("risk-budget-api");
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

    expect(document.body.textContent).toContain("api-health · observed");
    expect(document.body.textContent).toContain("incident-api-1 · triaged");
    expect(document.body.textContent).toContain("recovery-api-1 · 投资恢复未放行");
  });
});
