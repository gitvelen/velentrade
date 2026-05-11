# 01. Overview Page

## 0. 页面目标

全景页回答：“今天我需要处理什么，哪些事情已经自动推进，哪些被阻断，哪些只是需要我知道。”

默认路由：`/`

主要 read model：`OwnerDecisionReadModel`

页面归属：`/` 归属主菜单“全景”。全景页只做摘要和 drill-down，不承载 Dossier、审批包、Agent 画像或 Trace 本身。

## 1. 首屏布局

```text
顶部：今日关注条
第一组：优先处理，展示审批摘要、系统健康、团队草案
第二组：核心状态，展示纸面账户、风险摘要、每日简报
底部：投资状态分布 / 最近关键事件 / 快捷 drill-down
```

排列规则：先放需要 Owner 处理或立即感知的事项，再放账户、风险和研究等核心状态；支撑信息和历史事件不得打乱首屏处理优先级。

## 2. 今日关注条

| 编号 | 元素 | 展示字段 | 点击行为 | 空状态 |
|---|---|---|---|---|
| OV-001 | 风控阻断卡 | workflow_id、标的、阶段、reason_code、阻断摘要、trace_id | 打开 Dossier 对应阶段 | 无风控阻断 |
| OV-002 | 待审批卡 | approval_id、对象、到期时间、影响范围、推荐结论 | 打开审批包 | 无待审批 |
| OV-003 | manual_todo 卡 | task_id、动作、due_date、风险提示、负责人 | 打开任务详情 | 无人工待办 |
| OV-004 | 数据降级卡 | domain、质量档位、影响 workflow、fallback 状态 | 打开 Health 面板 | 数据正常 |
| OV-005 | incident 卡 | severity、服务、业务影响、Risk handoff 状态 | 打开 Health/Trace | 系统正常 |
| OV-006 | 团队草案卡 | agent_id、变更类型、impact_level、验证状态 | 打开团队草案或治理变更 | 无草案 |

交互规则：

- `OV-007`: 卡片点击只跳转，不在全景页执行审批、恢复、重开或配置生效。
- `OV-008`: 高风险卡片固定在关注条左侧；低风险按更新时间排序。
- `OV-009`: 同一 workflow 同时有阻断和审批时，优先显示阻断，审批作为次级链接。

## 3. 纸面账户摘要卡

| 编号 | 字段 | 展示方式 |
|---|---|---|
| OV-010 | total_value | 主数值，CNY |
| OV-011 | cash | 次级数值 |
| OV-012 | position_value | 次级数值 |
| OV-013 | day_return / total_return | 语义色，正负分明 |
| OV-014 | drawdown | 风险色，超过阈值时进入关注条 |
| OV-015 | risk_budget_used | 进度条和百分比 |
| OV-016 | baseline | 显示默认纸面本金 `1,000,000 CNY` |

操作：

- `OV-017`: 点击账户卡进入 `/finance?panel=investment-finance`。
- `OV-018`: 点击持仓风险进入相关 Dossier 或治理任务。
- `OV-019`: 不显示真实券商、真实账户同步或真实下单入口。

状态：

| 编号 | 状态 | 展示 |
|---|---|---|
| OV-020 | 初始空仓 | `1,000,000 CNY 空仓初始化` |
| OV-021 | 账户 read model 失败 | 错误卡、trace_id、重试；不阻断其他卡片 |
| OV-022 | 数据 stale | 显示 generated_at 与 last_success_at |

## 4. 风险摘要卡

| 编号 | 字段 | 展示方式 | drill-down |
|---|---|---|---|
| OV-023 | concentration | 集中度指标和语义色 | 风险详情 |
| OV-024 | risk_budget_used | 风险预算进度条 | 财务风险预算 |
| OV-025 | blockers | 阻断数量和最高 severity | 治理任务过滤 |
| OV-026 | conditional_pass | 条件通过数量、到期时间 | 审批中心 |
| OV-027 | rejected | 被拒绝 workflow 和 repairability | Dossier S5 |

禁止：

- `OV-028`: Risk rejected 不显示 Owner 继续按钮。
- `OV-029`: 风控数据不可用时，不隐藏风险区域，显示 degraded。

## 5. 审批摘要

| 编号 | 表格列 | 说明 |
|---|---|---|
| OV-030 | approval_id | 可点击 |
| OV-031 | 审批对象 | 投资例外、治理变更、Agent 能力高影响草案 |
| OV-032 | 推荐结论 | CIO/Risk/CFO 或系统推荐 |
| OV-033 | 到期时间 | 超时默认 disposition |
| OV-034 | 影响范围 | workflow、new_task、new_attempt |
| OV-035 | 状态 | pending、expired、approved、rejected、request_changes |

交互：

- `OV-036`: 点击行进入 `/governance/approvals/:approvalId`。
- `OV-037`: 全景只展示摘要，不提供 approve/reject 操作按钮。
- `OV-038`: 审批列表失败时，Shell badge 仍显示 last known count 和错误提示。

## 6. manual_todo 摘要

| 编号 | 字段 | 展示方式 |
|---|---|---|
| OV-039 | task_id | 可点击 |
| OV-040 | 类型 | 房产估值、线下资料、非 A 股人工动作等 |
| OV-041 | due_date | 逾期标红 |
| OV-042 | 风险提示 | 简短摘要 |
| OV-043 | 关联对象 | 财务资产、知识资料或 workflow |

规则：

- `OV-044`: 人工待办不进入审批中心。
- `OV-045`: 非 A 股 manual_todo 不出现交易、审批或执行动作。

## 7. 每日简报摘要

| 编号 | 字段 | 展示方式 |
|---|---|---|
| OV-046 | priority | P0/P1/P2 |
| OV-047 | title | 高信号标题 |
| OV-048 | boundary | `supporting evidence only`、候选机会、研究任务等 |
| OV-049 | source | Researcher、服务信号、公告、Owner |

交互：

- `OV-050`: 点击标题进入 `/knowledge?brief=:briefId`。
- `OV-051`: P0 简报可以引导到投资队列，但不能跳过硬门槛。
- `OV-052`: 简报失败不阻断投资 workflow。

## 8. 系统健康摘要

| 编号 | 卡片 | 字段 |
|---|---|---|
| OV-053 | 数据质量 | source health、quality band、fallback、conflict |
| OV-054 | 服务状态 | service name、state、latency、recent errors |
| OV-055 | incident | severity、business impact、recovery status、Risk handoff |
| OV-056 | 成本/Token | cost trend、token trend、budget signal |

规则：

- `OV-057`: 技术恢复后仍显示 `investment_resume_allowed=false`，直到 Risk/workflow guard 放行。
- `OV-058`: 成本/Token 只作运营观测，不作为投资事实。

## 9. 全景页加载、空、错

| 编号 | 场景 | 展示 |
|---|---|---|
| OV-059 | 全页面 loading | 保留 Shell，内容区 skeleton |
| OV-060 | 无关注事项 | 明确显示当前无待处理，不隐藏区域 |
| OV-061 | 部分卡失败 | 对应卡显示错误和 trace_id，其他卡正常 |
| OV-062 | read model stale | 顶部显示 generated_at，动作前刷新 |
| OV-063 | 空投资账户 | 纸面账户卡显示初始化本金和空仓 |

## 10. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-006, REQ-007 |
| Acceptance | ACC-006, ACC-007 |
| TC | TC-ACC-006-01, TC-ACC-007-01 |
| Report | web_command_routing_report.json, governance_task_report.json |
