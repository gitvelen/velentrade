# 00. Shell And Navigation

## 0. 页面目标

全局壳层负责让 Owner 始终知道：现在在哪个主菜单、当前详情页归属哪个业务域、有哪些待处理事项、自然语言请求会被转成什么受控对象，以及如何从默认 Owner 视图 drill down 到详情或审计层。

## 1. 主导航

| 编号 | 菜单 | 默认路由 | 页面目标 | 首屏核心信息 | 主要跳转 |
|---|---|---|---|---|---|
| NAV-001 | 全景 | `/` | 判断今天是否需要处理 | 风险、审批、manual_todo、纸面账户、系统健康 | 投资 Dossier、审批包、治理健康、任务详情 |
| NAV-002 | 投资 | `/investment` | 管理 A 股 IC 队列和决策档案 | 机会池、正式 IC、优先级、硬门槛、阶段状态 | `/investment/:workflowId`、workflow Trace |
| NAV-003 | 财务 | `/finance` | 查看全资产财务档案和规划 | 净资产、现金、负债、风险预算、现金流提醒 | 人工待办、治理提案、财务明细 |
| NAV-004 | 知识 | `/knowledge` | 管理研究、记忆、反思和提案 | 每日简报、研究资料包、高价值经验、反思、改进提案 | 提案详情、敏感信息保护、治理 |
| NAV-005 | 治理 | `/governance` | 处理任务、审批、Agent 团队、配置、健康和审计 | 任务中心、审批中心、Agent 团队、变更管理、系统健康、审计记录 | 审批包、Agent 画像、审计摘要、任务详情 |

确认点：

- `NAV-007`: 主导航只出现上述五项，不出现团队、飞书、移动端、真实券商、回测、策略经理或规则路径。
- `NAV-008`: 当前菜单高亮按 canonical parent menu 判断；Dossier 和 workflow Trace 高亮“投资”，Agent 画像和能力配置高亮“治理”，审批包高亮“治理”。
- `NAV-009`: 菜单文案全部为简体中文；专业对象在页面内部保留英文 id。

## 1.1 页面层级与来源入口

| 编号 | 层级 | 路由 | canonical parent menu | 来源入口 |
|---|---|---|---|---|
| NAV-010A | 全景页 | `/` | 全景 | 主导航、Brand |
| NAV-010B | 投资队列 | `/investment` | 投资 | 主导航、全景投资摘要 |
| NAV-010C | 投资档案 | `/investment/:workflowId` | 投资 | 投资队列、全景关注卡、治理任务卡 |
| NAV-010D | 流程审计 | `/investment/:workflowId/trace` | 投资 | 投资档案审计入口、治理审计/健康中的流程审计引用 |
| NAV-010E | 财务页 | `/finance` | 财务 | 主导航、全景账户卡 |
| NAV-010F | 知识页 | `/knowledge` | 知识 | 主导航、每日简报、研究资料包链接 |
| NAV-010G | 治理页 | `/governance` | 治理 | 主导航、Attention badge、全景任务卡 |
| NAV-010H | Agent 团队 | `/governance/team` | 治理 | 治理 Agent 团队、全景 Agent 草案卡 |
| NAV-010I | Agent 画像 | `/governance/team/:agentId` | 治理 | Agent 团队 roster、治理 AgentCapabilityChange |
| NAV-010J | 能力配置草案 | `/governance/team/:agentId/config` | 治理 | Agent 画像、Agent 草案入口 |
| NAV-010K | 审批详情 | `/governance/approvals/:approvalId` | 治理 | 治理审批中心、全景待审批卡 |

规则：

- `NAV-010L`: 来源入口只决定返回路径，不改变 canonical parent menu。
- `NAV-010M`: 其他非投资 trace 不新增前端详情路由；治理 Audit/Health 展示 trace 摘要、trace_id 和相关对象链接。

## 2. Shell 固定区域

| 编号 | 区域 | 展示信息 | 交互 |
|---|---|---|---|
| NAV-011 | Brand | 紧凑展示 `Velentrade` 与品牌标识；不展示“单老板投研工作台”等长副标题 | 点击回到全景页 |
| NAV-012 | 主导航 | 五个主菜单、当前 active 状态 | 点击切换路由，只切换视图 |
| NAV-013 | 全局命令输入 | 输入框、`生成请求简报`按钮、最近一次 Request Brief 状态 | 提交到 Request Brief preview，不直接启动 workflow |
| NAV-014 | Attention badge | 风控阻断、审批、manual_todo、数据降级、incident、团队草案数量 | 点击进入对应列表或过滤后的治理页 |
| NAV-015 | 页面标题区 | 页面名、业务日期、当前筛选、全局状态、来源返回路径 | 不承担核心操作 |
| NAV-016 | 内容区 | 当前页面的卡片、表格、阶段轨和详情面板 | 页面内交互不推进后端 workflow state |

治理二级模块：

| 编号 | 模块 | 入口 |
|---|---|---|
| NAV-016A | 任务中心 | `/governance` 默认模块 |
| NAV-016B | 审批中心 | `/governance?panel=approvals` 或页内二级模块切换 |
| NAV-016C | Agent 团队 | `/governance/team`，通过治理页二级模块切换进入，卡片入口为辅助入口 |
| NAV-016D | 变更管理 | `/governance?panel=changes` |
| NAV-016E | 系统健康 | `/governance?panel=health` |
| NAV-016F | 审计记录 | `/governance?panel=audit` |

## 3. 全局命令层

流程：

```text
自然语言输入
 -> Request Brief preview
 -> Owner confirm / edit / cancel
 -> TaskEnvelope 或治理变更草案
 -> workflow 或治理状态机由后端接管
```

| 编号 | 状态 | 展示字段 | 可用动作 | 禁止动作 |
|---|---|---|---|---|
| CMD-001 | 初始 | placeholder、输入提示、受控边界提示 | 输入文本、提交 | 直接交易、直接审批、直接改 Prompt |
| CMD-002 | preview loading | skeleton、请求 id、生成中 | 取消本次 preview | 重复提交 |
| CMD-003 | preview ready | 目标、范围、资产边界、优先级、授权边界、成功标准、阻断条件 | 确认、编辑、取消 | 将 confirmation 当 approval |
| CMD-004 | preview rejected | 拒绝原因、reason_code、可改写建议 | 编辑后重新生成 | 绕过拒绝继续执行 |
| CMD-005 | confirmed | 新 Task 卡、workflow id 或治理变更草案 id | 跳转详情 | 本地乐观推进阶段 |
| CMD-006 | stale/conflict | 服务端最新版本、trace_id | 刷新 preview | 保留本地旧结论 |

命令分类规则：

| 编号 | 输入类型 | 转换结果 |
|---|---|---|
| CMD-007 | 研究 A 股 | Request Brief + 投资 TaskEnvelope |
| CMD-008 | 买入、卖出、下单 | Request Brief；若越界则显示拒绝或进入受控投资 workflow |
| CMD-009 | 审批某事项 | 跳转对应 Approval Packet；不得在命令层直接 approval |
| CMD-010 | 修改 Prompt/Skill/权限 | 治理变更草案 |
| CMD-011 | 修改 Agent 能力 | AgentCapabilityChangeDraft |
| CMD-012 | 财务动作 | 财务任务、规划建议或 manual_todo |
| CMD-013 | 非 A 股交易请求 | manual_todo 或规划/风险提示，不生成交易审批 |

## 4. Attention Badge

| 编号 | badge | 计数来源 | 点击行为 |
|---|---|---|---|
| NAV-017 | 风控阻断 | Risk rejected、execution_core blocked、hard blocker | `/governance?panel=tasks&filter=risk_blocked` |
| NAV-018 | 审批 | pending ApprovalRecord | `/governance?panel=approvals` |
| NAV-019 | 人工待办 | manual_todo TaskEnvelope | `/governance?panel=tasks&filter=manual_todo` |
| NAV-020 | 数据降级 | Data/Service Health degraded | `/governance?panel=health&filter=data` |
| NAV-021 | 系统事故 | active incident | `/governance?panel=health&filter=incident` |
| NAV-022 | Agent 草案 | AgentCapabilityChangeDraft pending | `/governance/team?panel=drafts` 查看编辑入口，或 `/governance?panel=changes&type=agent_capability` 查看治理状态 |

## 5. 路由恢复

| 编号 | 路由 | 恢复规则 |
|---|---|---|
| NAV-023 | `/investment/:workflowId?stage=S3&artifact=:artifactId` | 高亮投资；恢复 selected_stage、artifact 聚焦和来源返回路径 |
| NAV-024 | `/investment/:workflowId/trace?attempt=2&run=:runId&from=governance` | 高亮投资；恢复 attempt、AgentRun 聚焦；返回路径可指向 Dossier 或治理来源 |
| NAV-025 | `/governance/team/:agentId` | 高亮治理；恢复选中 Agent 和画像 tab |
| NAV-026 | `/governance/team/:agentId/config?draft=:draftId` | 高亮治理；恢复草案编辑器和 client_seen_version |
| NAV-027 | `/governance/approvals/:approvalId` | 高亮治理；展示审批包最新服务端版本 |

## 6. 壳层状态

| 编号 | 状态 | 展示 | 行为 |
|---|---|---|---|
| STATE-001 | Shell loading | 导航可见，内容区 skeleton | 不清空旧 badge，标记刷新中 |
| STATE-002 | Shell read model error | 顶部错误条、trace_id、重试 | 主导航仍可用 |
| STATE-003 | Shell stale | `generated_at`、last_success_at | 允许查看旧数据，动作前强制刷新 |
| STATE-004 | 无待处理 badge | `当前无待处理事项` | badge 区不隐藏，只显示零状态 |

## 7. 全局禁止入口

| 编号 | 禁止入口 | UI 表现 |
|---|---|---|
| GUARD-001 | 直接下单 | 命令层生成 Request Brief 或拒绝，不出现执行按钮 |
| GUARD-002 | 绕过 Risk rejected | 不显示 Owner 批准继续 |
| GUARD-003 | 热改 Prompt/Skill/权限 | 只能保存治理变更草案 |
| GUARD-004 | 非 A 股审批/执行/交易 | 只显示 planning、risk、manual_todo |
| GUARD-005 | raw transcript 默认展开 | Trace 中默认折叠并标注非正式事实源 |
