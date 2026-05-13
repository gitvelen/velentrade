# Source Normalization

## 0. AI 阅读契约

- 本附件是 `spec.md` 中来源归一化、旧口径裁剪和原始材料追溯的强证据展开层，不定义新的正式需求、验收或验证义务。
- 任务涉及来源追溯、旧输入冲突、Requirement 重开或判断正文与原始材料关系时，必须读取本附件。
- 若本附件与 `spec.md` 冲突，必须停止并回到 Requirement 修补冲突。
- 本附件中的外部资料只用于解释设计取舍和行业参照，不自动成为 V1 范围、验收条件或供应商绑定。

## 1. 已采用项目来源

| 来源 | 用途 |
|---|---|
| `../inputs/sessonlog.txt` | Requirement 讨论记录和用户最新确认结论 |
| `../inputs/investagents.md` | 项目蓝图、角色、服务、工作台和历史演进 |
| `../inputs/investagents/workflow-architecture.md` | S0-S7、运行时协作、阶段产物、状态机 |
| `../inputs/investagents/core-mechanisms.md` | IC、辩论、共识、候选池、风控和反馈闭环的历史来源 |
| `../inputs/investagents/data-flow.md` | 数据分类、数据源矩阵、质量治理 |
| `../inputs/investagents/07-decision-services/data-collection-service.md` | 数据采集和质量服务职责 |
| `../inputs/investagents/07-decision-services/*` | 市场状态、因子、估值、组合优化、风险、交易执行服务来源 |
| `../inputs/investagents/01-command-hub/*` | CIO 与 Owner 历史职责来源 |
| `../inputs/investagents/05-performance-attribution/chief-financial-officer.md` | CFO 财务和归因职责来源 |
| `../inputs/investagents/06-support-operations/*` | 研究员、风控、DevOps 来源 |
| `../inputs/investagents/02-investment-committee/*` | 四位 IC 分析师来源 |

## 2. 已废弃或降级旧口径

| 旧口径 | V1 处理 |
|---|---|
| 策略经理 | 删除/禁用，不进入 V1 官方 Agent 清单 |
| 规则路径 | 删除/禁用，不进入 V1 workflow、验收和测试 |
| Performance Analyst Agent | 取消，归因评价改为自动化服务，CFO 承接解释和治理 |
| Data Lead Agent | 不设独立 Agent；数据治理由注册表、数据服务、DevOps 和 Risk 分工承接 |
| 飞书通知/审批 | V1 不做，全部改为 Web 内通知、横幅、任务和审批中心 |
| 邮件、短信、外部 IM 通知 | V1 不做，不作为触达或审批通道 |
| 移动端 | V1 不做 |
| 真实券商通道 | V1 不做，只保留纸面执行 |
| Broker API 适配 | V1 不做，不预留为验收条件 |
| Backtrader 或回测 | V1 不做，不作为验收条件 |
| token 成本预算作为 pass/fail | 降级为可观测指标，不作为需求验收成败条件 |
| 旧前端聊天式主界面 | 降级为命令入口；主界面必须以 artifact、任务、审批和阶段进展为中心 |
| `frontend-design.md` 旧导航 | 仅历史参考，不作为 V1 导航权威 |
| `data-strategy.md` | 当前未落盘，不作为权威来源 |

旧口径处理原则：

- 用户最新确认高于旧输入文档。
- `spec.md` 正文高于本附件。
- 旧文档保留更大蓝图，不代表进入 V1。
- 明确排除项不得在 Design 中以“预留扩展”“底层兼容”名义实现。
- 被降级为参考的内容可以用于解释设计动机，但不能驱动 work item、接口或测试验收。

## 3. 外部行业参照

这些资料仅用于校准角色边界、治理职责、可观测性和多 Agent 工作台设计，不把任何外部产品形态搬进 V1。

| 外部参照 | 参考入口 | 使用边界 |
|---|---|---|
| CFA Institute: Portfolio Management / Asset Allocation / Risk Management | `https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-management-overview` | 用于校准 CIO、Risk、CFO 的投资治理、资产配置、风险预算和绩效报告语义 |
| Google SRE: Monitoring, Incident, Postmortem | `https://sre.google/sre-book/monitoring-distributed-systems/` | 用于校准 DevOps 的监控、告警、降级、恢复和复盘边界 |
| LangGraph Studio / LangSmith Studio | `https://docs.langchain.com/langsmith/studio` | 用于理解多 Agent 图、状态、运行和调试视图，但 Owner 工作台不直接暴露成工程调试器 |
| CrewAI Tracing | `https://docs.crewai.com/en/observability/tracing` | 用于理解 Agent trace、span、tool 调用和可观测性，不要求采用 CrewAI |
| AutoGen Studio | `https://microsoft.github.io/autogen/stable/user-guide/autogenstudio-user-guide/index.html` | 用于参考团队构建、消息流和工作流可视化，不要求采用 AutoGen Studio |
| Microsoft Agent Framework | `https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/` | 用于参考 workflow、memory、tool 和 DevUI 概念，不要求采用 Microsoft 技术栈 |
| AKShare / Tushare / BaoStock 等 A 股数据源 | `https://akshare.akfamily.xyz/`、`https://tushare.pro/document/2`、`https://pypi.org/project/baostock/` | 用于参考可获取数据域，不绑定特定 API、字段名或商业可用性 |

外部参照的落地规则：

- 只能影响“为什么这样设计”的解释，不能直接生成 V1 验收。
- 若外部工具形态与用户确认冲突，以用户确认和 `spec.md` 为准。
- 若第三方数据源字段、权限、稳定性变化，Design 应通过 Source Registry 和 Data Request 适配，而不是重写业务需求。
- 任何外部 API 的许可、限频、成本和可用性必须在 Design/Implementation 阶段作为工程约束重新确认。

## 4. 数据源归一化原则

第三方数据源是可替换供应商，不是业务能力本身。

归一化要求：

- Data Domain Registry 定义系统需要哪些数据域、关键字段和质量阈值。
- Source Registry 定义具体供应商、覆盖范围、信任层级、限频、成本、缓存和降级策略。
- Data Request 用标准字段表达业务需要，不直接暴露供应商字段。
- Source Adapter 负责供应商字段映射、时区/交易日归一、复权口径、币种和单位归一。
- Data Quality Gate 对 critical 字段严格阻断，对 aggregate 指标给出诊断和降级建议。
- 多源冲突必须先标准化再比较，不允许让 Owner 直接判断原始字段谁对谁错。

默认数据源策略：

- A 股交易日历、OHLCV、复权、停复牌、涨跌停、公告和财务字段是正式投资链关键域。
- 宏观、行业、新闻和舆情可以作为研究资料或支撑证据；在未达 formal gate 前不得单独触发正式 IC。
- 缓存可用于展示和研究；decision core 缓存默认只读，不能生成新的执行授权。
- `execution_core` 质量低于默认阈值时严格阻断纸面执行；阈值本身属于高影响治理项。

## 5. 前端旧输入归一化

前端从“聊天/调试/Agent 面板”归一为“Owner artifact workbench”。

保留：

- 自由对话作为命令入口。
- Agent trace 作为调试层。
- 任务、审批、artifact、阶段进展、风险和异常作为 Owner 主视角。

降级：

- 长聊天历史不作为默认工作区。
- 原始 Agent 消息流不作为 Owner 决策依据。
- 工程调试图不作为普通 Owner 主导航。

删除：

- 移动端适配。
- 飞书、邮件、短信审批。
- 非 Web 通道的任务闭环。

## 6. 用户最新确认优先级

归一化原则：

- 用户在 Requirement 讨论中的最新确认高于旧输入文档。
- 正式正文高于本附件。
- 如果旧文档保留了更大蓝图，不代表进入 V1。
- 如果某项能力被用户明确排除，不得在 Design 中以“预留扩展”名义实现。
- 如果 Design 阶段发现旧材料和正式正文存在冲突，必须回到 Requirement 修补正式正文，而不是在 Design 中自行解释。

## 7. 文件名说明

当前落盘讨论记录文件名为 `../inputs/sessonlog.txt`。用户口头提到的 `sessionlog.txt` 在本仓库当前材料中不存在；后续引用应使用实际文件名，除非文件被用户重命名。

## 8. Requirement Source Closure

本节保留 `spec.md` 中各 `REQ-*` 的来源展开。`spec.md` 正文里的 `source_ref` 统一指向本附件，避免把已确认决策 ID、逗号组合项或仓库外旧输入文件误声明为可直接校验的 repo artifact。

| REQ | normalized_source | original_source_basis |
|---|---|---|
| REQ-001 | `spec-appendices/source-normalization.md` | `spec-appendices/source-normalization.md` |
| REQ-002 | `spec-appendices/source-normalization.md` | `DEC-004, DEC-005` |
| REQ-003 | `spec-appendices/source-normalization.md` | `DEC-007` |
| REQ-004 | `spec-appendices/source-normalization.md` | `DEC-007, DEC-018, DEC-023` |
| REQ-005 | `spec-appendices/source-normalization.md` | `workflow-architecture.md, DEC-007, DEC-019` |
| REQ-006 | `spec-appendices/source-normalization.md` | `DEC-001` |
| REQ-007 | `spec-appendices/source-normalization.md` | `DEC-001, DEC-002, DEC-009` |
| REQ-008 | `spec-appendices/source-normalization.md` | `workflow-architecture.md` |
| REQ-009 | `spec-appendices/source-normalization.md` | `DEC-009, data-flow.md, data-collection-service.md` |
| REQ-010 | `spec-appendices/source-normalization.md` | `DEC-006` |
| REQ-011 | `spec-appendices/source-normalization.md` | `market-state-evaluation-engine.md` |
| REQ-012 | `spec-appendices/source-normalization.md` | `core-mechanisms.md, DEC-008` |
| REQ-013 | `spec-appendices/source-normalization.md` | `DEC-008` |
| REQ-014 | `spec-appendices/source-normalization.md` | `workflow-architecture.md, DEC-020` |
| REQ-015 | `spec-appendices/source-normalization.md` | `core-mechanisms.md, DEC-021` |
| REQ-016 | `spec-appendices/source-normalization.md` | `core-mechanisms.md` |
| REQ-017 | `spec-appendices/source-normalization.md` | `core-mechanisms.md, DEC-009, DEC-020` |
| REQ-018 | `spec-appendices/source-normalization.md` | `DEC-006, DEC-020` |
| REQ-019 | `spec-appendices/source-normalization.md` | `DEC-009` |
| REQ-020 | `spec-appendices/source-normalization.md` | `DEC-003` |
| REQ-021 | `spec-appendices/source-normalization.md` | `trade-execution-service.md, DEC-003` |
| REQ-022 | `spec-appendices/source-normalization.md` | `workflow-architecture.md` |
| REQ-023 | `spec-appendices/source-normalization.md` | `DEC-002` |
| REQ-024 | `spec-appendices/source-normalization.md` | `DEC-005` |
| REQ-025 | `spec-appendices/source-normalization.md` | `DEC-005, DEC-007` |
| REQ-026 | `spec-appendices/source-normalization.md` | `DEC-001, DEC-010` |
| REQ-027 | `spec-appendices/source-normalization.md` | `DEC-007, DEC-022` |
| REQ-028 | `spec-appendices/source-normalization.md` | `DEC-005, DEC-007, DEC-022` |
| REQ-029 | `spec-appendices/source-normalization.md` | `DEC-010` |
| REQ-030 | `spec-appendices/source-normalization.md` | `DEC-007, DEC-009, DEC-022` |
| REQ-031 | `spec-appendices/source-normalization.md` | `DEC-001, DEC-018, DEC-023` |
| REQ-032 | `spec-appendices/source-normalization.md` | `phase-review-policy.md` |
