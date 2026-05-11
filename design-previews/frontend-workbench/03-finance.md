# 03. Finance Page

## 0. 页面目标

财务页回答：“我的全资产、流动性、负债、风险预算和非 A 股人工事项是什么；哪些信息能进入投资链，哪些只能留在财务规划或 manual_todo。”

默认路由：`/finance`

主要 read model：`FinanceOverviewReadModel`

页面归属：`/finance` 归属主菜单“财务”。财务页可以跳到治理 manual_todo 或 Dossier 引用，但非 A 股资产不进入投资审批、执行或交易链。

## 1. 首屏布局

```text
顶部：净资产 / 流动性 / 负债率 / 风险预算卡
中部：全资产档案表 + 财务健康矩阵
下部：投资财务 / 财务规划 / 近期现金流 / 人工待办
侧栏或折叠区：敏感字段说明与审计提示，默认不占用老板首屏
```

## 2. 指标卡

| 编号 | 卡片 | 展示字段 | 点击行为 |
|---|---|---|---|
| FIN-001 | 净资产 | total_assets、total_liabilities、net_worth、generated_at | 展开资产负债明细 |
| FIN-002 | 流动性覆盖 | cash、monthly_expense、coverage_months | 打开流动性规划 |
| FIN-003 | 负债率 | debt_ratio、major_debt_due、risk_level | 打开负债计划 |
| FIN-004 | 风险预算 | budget_total、used、available、investment_constraint | 打开风险预算 |
| FIN-005 | 压力测试 | downside_scenario、liquidity_gap、action_needed | 打开压力测试 |

状态：

- `FIN-006`: 敏感明细 loading 时卡片保留脱敏摘要。
- `FIN-007`: 财务 read model 失败时显示错误卡、trace_id、重试。
- `FIN-008`: stale 数据显示 generated_at，不允许用于新投资执行。

## 3. 全资产档案表

| 编号 | 列 | 说明 |
|---|---|---|
| FIN-009 | asset_id | 可点击 |
| FIN-010 | 类型 | 现金、A 股纸面账户、基金、黄金、房产、负债、收入、支出 |
| FIN-011 | 估值 | 金额、币种、估值时间 |
| FIN-012 | 数据来源 | 自动行情、纸面账户、手工录入、定期估值 |
| FIN-013 | 更新状态 | normal、stale、manual_due、degraded |
| FIN-014 | 投资链边界 | 可用于风险预算、只规划、manual_todo、不可交易 |
| FIN-015 | 敏感级别 | normal、finance_sensitive_raw、redacted_summary |
| FIN-016 | 关联任务 | manual_todo、Governance Proposal、Risk constraint |

交互：

- `FIN-017`: 点击基金、黄金、房产只能进入规划、估值或 manual_todo，不进入交易。
- `FIN-018`: 点击 A 股纸面账户可进入投资财务和持仓风险，但不接真实券商。
- `FIN-019`: 敏感字段详情只在 Owner 财务视图中明文展示，不复制到 Trace 默认区。

## 4. 财务健康矩阵

| 编号 | 模块 | 展示 |
|---|---|---|
| FIN-020 | 负债健康 | debt_ratio、偿付窗口、风险等级 |
| FIN-021 | 流动性 | coverage_months、现金缺口、重大支出 |
| FIN-022 | 风险预算 | 可用于投资链的预算约束 |
| FIN-023 | 税务提醒 | due_date、估算、manual_todo |
| FIN-024 | 压力测试 | 市场下跌、收入中断、流动性缺口 |

规则：

- `FIN-025`: 财务规划建议可生成 Governance Proposal 子类型。
- `FIN-026`: 投资链只消费脱敏约束摘要，例如现金约束、风险预算、流动性边界。

## 5. 投资财务区

| 编号 | 卡片 | 展示字段 |
|---|---|---|
| FIN-027 | 收益 | day_return、total_return、realized/unrealized |
| FIN-028 | 成本 | fee、slippage、tax |
| FIN-029 | 现金使用 | available_cash、planned_cash_usage、constraint |
| FIN-030 | 风险预算使用 | per_position、portfolio、remaining |
| FIN-031 | 归因链接 | AttributionReport refs、Reflection refs |

交互：

- `FIN-032`: 点击归因链接进入 Knowledge/Reflection 或 Dossier S7。
- `FIN-033`: 财务页不直接触发买卖。

## 6. 财务规划区

| 编号 | 区块 | 展示 |
|---|---|---|
| FIN-034 | 重大支出 | 事项、金额、时间、投资约束影响 |
| FIN-035 | 税务提醒 | 类型、预计金额、截止时间、manual_todo |
| FIN-036 | 资产规划建议 | CFO Interpretation、Governance Proposal refs |
| FIN-037 | 家庭/收入敏感摘要 | Owner 可见明细，非财务上下文只见脱敏摘要 |

## 7. 资产处理规则

| 编号 | 资产 | 允许展示 | 允许动作 | 禁止动作 |
|---|---|---|---|---|
| FIN-038 | 基金 | 自动行情、估值、风险提示 | 规划、人工待办 | 交易审批、执行 |
| FIN-039 | 黄金 | 自动行情、估值、风险提示 | 规划、人工待办 | 交易审批、执行 |
| FIN-040 | 房产 | 手工或定期估值 | 估值提醒、人工待办 | 交易审批、执行 |
| FIN-041 | 其他资产 | 档案和规划 | 人工待办 | 自动交易 |

## 8. 财务敏感字段展示

| 编号 | 视图 | 展示规则 |
|---|---|---|
| FIN-042 | Owner `/finance` | 可查看自己录入的收入、负债、税务、重大支出明细 |
| FIN-043 | Dossier | 只显示风险预算、现金约束、重大支出影响 |
| FIN-044 | Trace/Debug | 默认不展示明文，显示 redaction status 和 denied refs |
| FIN-045 | 非 CFO Agent 上下文 | 只读脱敏摘要和派生 artifact |
| FIN-046 | CFO/财务服务上下文 | 可使用明文字段生成 CFO Interpretation 或 FinanceSummary |

规则：

- `FIN-047`: 前端不得通过隐藏 CSS 保存敏感明文。
- `FIN-048`: 明文财务字段不得进入普通日志和 raw trace 默认区域。

## 9. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-023, REQ-031 |
| TC | TC-ACC-023-01, TC-ACC-031-01 |
| Report | governance_task_report.json, security_privacy_report.json |
