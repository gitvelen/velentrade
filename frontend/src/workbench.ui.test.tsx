// @vitest-environment jsdom
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

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

describe("WI-004 workbench interactions", () => {
  beforeEach(() => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
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

  it("submits approval decisions with visible local feedback instead of a dead detail page", async () => {
    await bootWorkbench("/governance/approvals/ap-001");

    await act(async () => {
      buttonByName("要求修改").click();
    });

    expect(document.body.textContent).toContain("已提交：要求修改");
    expect(document.body.textContent).toContain("等待后端返回最新审批状态");
    expect(document.body.textContent).toContain("生效范围：后续任务");
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
});
