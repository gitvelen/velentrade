# Frontend Workbench Markdown Review Pack

## 0. 阅读说明

本目录包含两类前端设计预览：

- `index.html` + `styles.css`: 可直接在浏览器打开的样式预览，覆盖五个一级主菜单页面和治理下 Agent 团队工作区的视觉效果与首屏排布。
- `*.md`: Markdown 确认稿，用于逐项确认路由层级、禁用入口、字段和 Agent 管理视角。

权威边界：

- 需求权威仍是 `spec.md` 的 `REQ-006 / REQ-007`、`ACC-006 / ACC-007`、`VO-006 / VO-007`。
- 测试计划仍是 `testing.md` 的 `TC-ACC-006-01 / TC-ACC-007-01`。
- read model 契约仍是 `contracts/api-read-models.md`。
- 本目录不新增需求，只把前端展示与交互拆到可确认粒度。

## 1. 确认顺序

先打开 `index.html` 看整体样式和页面排布，再按下表阅读 Markdown 确认项。

| 文件 | 确认主题 | 重点确认 |
|---|---|---|
| `index.html` | 五个主菜单样式预览 | 漂亮优先、护眼其次的高端浅色卡面、页面密度、首屏排布、治理下 Agent 团队展示是否符合预期 |
| `00-shell-and-navigation.md` | 全局壳层、主导航、命令层 | 菜单是否完整，命令层是否不会直接执行，Attention badge 是否合理 |
| `01-overview.md` | 全景页 | Owner 首屏是否知道今天要处理什么 |
| `02-investment.md` | 投资队列、Dossier、Trace 入口 | S0-S7、Agent 分歧、风控、执行、归因是否能被看懂 |
| `03-finance.md` | 财务页 | 全资产、现金流提醒、敏感字段展示是否合理 |
| `04-knowledge.md` | 知识、记忆、反思、提案 | Memory/Knowledge 是否只作为上下文和经验，不直接生效 |
| `05-team.md` | Agent 团队工作区 | 治理下九个 Agent 画像、质量、配置草案是否满足管理视角 |
| `06-governance.md` | 治理页 | 任务、审批、Agent 团队、治理变更、健康、审计是否分离 |
| `07-states-and-guards.md` | 通用状态与禁用入口 | loading/empty/error/blocked、禁止按钮和跳转是否完整 |

## 2. 编号规则

每个确认项使用稳定编号，后续反馈可以直接引用编号：

- `NAV-*`: 全局导航和壳层。
- `CMD-*`: 全局命令层。
- `OV-*`: 全景页。
- `INV-*`: 投资队列、Dossier 和 Trace。
- `FIN-*`: 财务页。
- `KN-*`: 知识页。
- `TEAM-*`: 治理下 Agent 团队工作区。
- `GOV-*`: 治理页。
- `STATE-*`: 通用状态。
- `GUARD-*`: 禁用入口和边界。

## 3. 全局设计默认值

| 项目 | 默认值 |
|---|---|
| 产品形态 | 单老板桌面 Web 工作台 |
| 语言 | 老板默认页面使用简体中文；专业对象名只在审计、配置详情或契约说明中保留英文 |
| 视觉 | 漂亮优先、护眼其次；暖瓷底色、墨色文字、玉绿主强调、靛蓝/暗金/胭脂红辅助色的高端浅色主题 |
| 主导航 | `全景 / 投资 / 财务 / 知识 / 治理` |
| 默认视图 | Owner Decision View，不默认展示长聊天或 raw trace |
| drill down | Owner 卡片进入 Dossier，审计和排障进入 Trace/Debug |
| 写入边界 | 前端只提交 Request Brief confirmation、approval action 或治理变更草案，不推进 workflow state |

老板默认卡片不展示实现或设计过程材料，例如非 A 股边界守卫、Prompt/Skill 版本、ContextSnapshot、trace_id、read model 或工具调用；这些信息必须转译成业务提醒，或下沉到审计和配置详情。

## 3.1 主菜单与路由归属

一级主菜单只有五个：`全景 / 投资 / 财务 / 知识 / 治理`。`团队` 不再作为一级菜单；Agent 画像、能力配置草案和团队绩效都归入治理下的 Agent 团队工作区。进入 Agent 团队的主入口是治理页顶部二级模块切换条，治理页 Agent 团队卡片只是辅助入口。Dossier、Trace、Agent 画像、能力配置草案和审批包都不是一级菜单；它们必须归属到某个主菜单下。

| 主菜单 | 页面层级 | 路由 | 说明 |
|---|---|---|---|
| 全景 | 全景页 | `/` | Owner 开屏摘要，只做关注事项和 drill-down，不承载详情处理。 |
| 投资 | 投资队列 | `/investment` | A 股 candidate / formal IC / holding risk 队列。 |
| 投资 | Investment Dossier | `/investment/:workflowId` | 投资 workflow 详情页；Dossier 不是主菜单。 |
| 投资 | Workflow Trace | `/investment/:workflowId/trace` | 投资 workflow 的审计详情页；Trace 不是主菜单。 |
| 财务 | 财务页 | `/finance` | 全资产、流动性、风险预算和现金流提醒。 |
| 知识 | 知识页 | `/knowledge` | 每日简报、研究资料包、高价值经验、反思和改进提案。 |
| 治理 | 治理页 | `/governance` | 任务、审批、Agent 团队、变更、健康、审计聚合。 |
| 治理 | Agent 团队 | `/governance/team` | 九个 Agent roster、胜任度、短板和草案入口。 |
| 治理 | Agent 画像 | `/governance/team/:agentId` | 单 Agent 详情页，归属治理菜单。 |
| 治理 | 能力配置草案 | `/governance/team/:agentId/config` | 草案编辑页，归属治理菜单；只保存 draft。 |
| 治理 | Approval Packet | `/governance/approvals/:approvalId` | 审批详情页，归属治理菜单。 |

来源入口不改变页面归属：全景关注卡可以跳到 Dossier、审批包或治理面板；治理 Health/Audit 可以跳到投资 workflow trace；这些跳转必须保留来源返回路径，但 active 主菜单按目标页面的 canonical parent menu 显示。

## 4. 全局交互词汇

| 交互 | 说明 |
|---|---|
| 查看详情 | 进入相关 Dossier、审批包、任务详情或 Agent 画像 |
| 生成请求简报 | 把自然语言转换为 Request Brief preview |
| 确认请求简报 | 创建 TaskEnvelope 或 workflow，不等于 Owner approval |
| 提交审批动作 | 只在审批中心中执行 `approved / rejected / request_changes` |
| 保存草案 | 生成治理变更或 AgentCapabilityChangeDraft，不直接生效 |
| 打开审计 | 进入具体业务对象的 Trace/Debug；投资 workflow 使用 `/investment/:workflowId/trace`，其他对象先在治理 Audit/Health 中展示 trace 摘要 |
| 重试 | 只重新拉取 read model，不改变业务状态 |

## 5. 当前确认状态

| 主题 | 状态 |
|---|---|
| 主导航与壳层 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 全景页 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 投资队列与 Dossier | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| Trace/Debug | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 财务页 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 知识页 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 治理下 Agent 团队 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 治理页 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |
| 通用状态与禁用入口 | Design 语义复审通过；Design->Implementation 仍需人工阶段切换确认 |

## 6. 后续回写范围

后续 Owner 对 Markdown review pack 再次确认或提出修改后，按以下范围回写：

- 将确认后的页面、表格、卡片和交互写入 `design-appendices/frontend-workbench-design.md`。
- 将旧静态预览和截图证据引用改为 Markdown review pack 引用。
- 同步 `testing.md` 和 `reviews/design-review.yaml` 中对静态预览路径和证据形态的描述。
