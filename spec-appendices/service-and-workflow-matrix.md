# Service And Workflow Matrix

## 0. AI 阅读契约

- 本附件是 `spec.md` 中服务层、编排中心、数据治理和 S0-S7 关系的强证据展开层，不定义新的正式需求、验收或验证义务。
- 任务涉及服务层、编排中心、S0-S7、阶段产物、状态机、降级、重试、数据源路由、缓存、冲突处理或责任边界时，必须读取本附件。
- 若本附件与 `spec.md` 冲突，必须停止并回到 Requirement 修补冲突。
- 服务不拥有投资治理权；编排中心不替代 Agent 判断；数据源供应商不作为不可替换的硬验收对象。

## 1. 编排中心

| 组件 | 职责 | 不负责 |
|---|---|---|
| Request Distribution Center | 入口标准化、请求分类、Request Brief、任务卡、workflow 模板选择 | 投资判断、风控审批、直接执行 |
| Workflow Scheduling Center | 生命周期、优先级、并发、暂停、恢复、取消、重开、Reopen Event、AgentRun 准入与协作会话运行标签 | 产出分析结论、替代 Agent 判断、替代 semantic lead 做领域判断 |
| Service Orchestration Center | 自动调用计算服务、数据/服务重试、降级、结果装配 | 调用 Agent 代替 workflow、直接做投资决策 |

Request Brief 路由规则：

| 条件 | workflow 模板 | 失败或不确定处理 |
|---|---|---|
| A 股普通股、目标是正式投资判断或处置 | `investment_workflow` | 资产/授权/目标不清时保持 Request Brief draft，等待 Owner confirmation。 |
| 投研资料、简报、知识检索、议题准备 | `research_task` | 若可能影响正式 IC，仅生成 candidate 或 Research Package，不直接启动 S0-S7。 |
| 财务档案、基金/黄金/房产、税务、预算或规划 | `finance_task` | 若包含非 A 股交易动作，转为规划提示或 `manual_todo`。 |
| Prompt、Skill、默认上下文、配置、风控参数、数据源策略 | `governance_task` | 高影响进入 Owner approval；低/中影响走自动验证生效。 |
| 系统外人工动作或 V1 范围外动作 | `manual_todo` | 不连接 S5/S6 投资审批或执行。 |
| 系统、数据源、服务、执行环境或安全异常 | `system_task` / incident | 技术恢复不直接放行业务执行；必要时交 Risk。 |

分类可以使用规则、schema 校验或 LLM 辅助，但输出必须是可审计的 Request Brief、route_reason 和 confidence；低置信或多模板冲突时只允许生成待确认草稿，不启动 workflow。

### 1.1 协作协议边界

协作机制是 workflow 的运行层能力，不是新的业务事实源。

| 对象 | 归属 | 作用 |
|---|---|---|
| CollaborationSession | Workflow Scheduling Center | 记录某阶段或某议题的一次协作容器、参与者、semantic lead、粗粒度运行标签。 |
| AgentRun | Workflow Scheduling Center + Authority Gateway | 记录一次受控岗位执行，绑定 ContextSnapshot/ContextSlice、工具权限、SkillPackage、预算和输出 schema。 |
| CollaborationCommand | Authority Gateway | 封闭协作请求；经准入后路由到 workflow、semantic lead、domain lead 或 Owner。 |
| CollaborationEvent | Audit/Event Log | append-only 记录进度、命令、产物提交、失败、超时和 handoff。 |
| HandoffPacket | Artifact Ledger | 阶段完成或跨角色补证后的交接摘要。 |

CollaborationSession 的状态只允许 `open / active / waiting / synthesizing / closed / failed / canceled / expired`。这些状态不表达 Risk rejected、低共识、Owner timeout、数据降级或可执行性；业务判断必须写入 workflow state、artifact、reason code 或 Reopen Event。

## 2. 任务状态模型

### 2.1 Task Envelope

所有任务共享 Task Envelope，用于列表、权限、审计和恢复：

| 字段 | 用途 |
|---|---|
| `task_id` | 任务唯一标识。 |
| `task_type` | `investment_workflow / research_task / finance_task / governance_task / system_task / manual_todo`。 |
| `priority` | P0/P1/P2 或任务内排序权重。 |
| `owner_role` | 责任角色，不一定是 Owner 本人。 |
| `current_state` | 通用任务状态或领域状态映射。 |
| `blocked_reason` | 阻塞原因。 |
| `reason_code` | 可机读原因码。 |
| `artifact_refs` | 关联产物。 |
| `created_at / updated_at / closed_at` | 生命周期时间。 |

轻量任务生命周期：

```text
draft -> ready -> queued -> running -> waiting | blocked | paused -> running -> completed
terminal: completed | canceled | failed | expired
```

`reopened` 不作为状态，而是 Reopen Event。领域进展优先使用 artifact 或 milestone，不为每个小步骤新增状态。

### 2.2 严格投资主链

投资任务严格执行 S0-S7。每个阶段都有节点状态：

```text
not_started
running
waiting
blocked
completed
skipped
failed
```

以下业务结果不作为节点状态：

- `degraded`: 数据或服务结果字段。
- `rejected / conditional_pass`: Risk Review 业务结果。
- `owner_timeout`: 审批结果 reason code。
- `unfilled / expired`: 纸面执行结果字段。
- `reopened`: Reopen Event。
- `paused / canceled`: workflow 级状态。

### 2.3 高影响治理状态机

治理任务适用于 Prompt、SkillPackage、默认上下文、共享知识、配置、风控参数、审批规则、服务降级策略、数据源路由策略和执行参数等会改变系统行为的变更。低/中影响变更可自动 triage、验证、版本快照和审计后生效；高影响变更必须 Owner 审批。

```text
draft -> triage -> assessment -> owner_pending -> approved -> effective
terminal without effect: rejected | expired | canceled | activation_failed
```

| 状态 | 含义 |
|---|---|
| `draft` | 提案材料未完整，不产生系统行为变化。 |
| `triage` | Governance Impact Policy 自动判定影响等级、影响范围和确认角色。 |
| `assessment` | Risk/CFO/DevOps/Researcher 等责任角色确认领域影响，不是审批。 |
| `owner_pending` | 审批包完整，等待 Owner 批准、拒绝、要求修改或超时。 |
| `approved` | Owner 已批准，但尚未生效；系统生成版本、校验 diff 和快照。 |
| `effective` | 只对新任务生效，在途任务继续绑定旧快照。 |
| `activation_failed` | Owner 已批准，但版本生成、校验或快照绑定失败，不能假装已生效。 |

Governance Impact Policy 可配置；修改这套规则本身永远属于高影响治理。规则支持自动升级，不支持静默降级；从高影响降级必须 Owner 明确批准并留痕。

### 2.4 System Incident 状态机

系统任务不套 S0-S7，使用最小 incident 状态：

```text
detected -> triaged -> mitigating -> monitoring -> closed
terminal: unresolved | escalated
```

DevOps 处理系统与数据源问题，Risk Officer 判断业务影响。系统恢复不等于投资任务可继续执行。

## 3. S0-S7 交接

| 阶段 | 编排/服务重点 | Agent 重点 | 主要产物 | 关键 guard |
|---|---|---|---|---|
| S0 请求受理 | 入口标准化、任务卡、开放机会注册 | Owner、分析师、Researcher、服务信号输入意图 | Request Brief | 目标、范围、授权、成功标准、阻断条件齐全 |
| S1 数据就绪 | 数据请求、源路由、质量评分、冲突处理、切源；装配 CIO 可用的议题输入 | DevOps 处理系统异常并向 Risk 汇报；CIO 读取 S1 输出后生成 IC Chair Brief | Data Readiness Report、IC Chair Brief | decision_core 关键项可用；execution_core 低于当前生效阈值不得执行；Chair Brief 不得预设结论 |
| S2 分析研判 | 服务结果注入、IC Context 装配、四位 AgentRun 准入 | 四位分析师以独立 CapabilityProfile/Skill/rubric 产出 Memo | Analyst Memo | Memo 通用外壳、role_payload、证据、反证、适用/失效条件齐全 |
| S3 辩论收敛 | Debate Manager 管理分歧检测、轮次、超时、公式重算、事件和 Debate Summary 过程字段 | CIO 作为语义主席提出 agenda、追问、synthesis；四位分析师参与有界辩论 | Debate Summary 或 debate_skipped | 最多 2 轮，低共识不执行；高共识 hard dissent 不跳过辩论，异议保留则进入风控；CIO 不改状态、不增轮次 |
| S4 CIO 收口 | Decision Packet 装配、偏离计算、重大偏离例外/重开请求 | CIO 输出投资语义结论 | CIO Decision Memo | 偏离优化器必须说明，重大偏离触发例外或重开；CIO 不操作服务、不下单、不覆盖 Risk |
| S5 风控复核 | 风险指标、执行约束、数据质量、审批规则 | Risk Officer 独立复核 | Risk Review Report | 三状态输出；rejected 阻断当前 attempt，并由 Risk 判定可修复性 |
| S6 授权与纸面执行 | Owner 例外、纸面执行模拟 | Owner 仅处理例外审批 | Approval Record、Paper Execution Receipt | 超时不执行；execution_core 低于当前生效阈值严格阻断 |
| S7 归因反思 | 自动归因、评价、异常标记 | CFO/责任 Agent/Researcher 反思和晋升 | Attribution Report、Reflection Record | 不改历史执行链，只追加归因、反思和后续任务 |

## 4. Reopen Event

重开是事件，不是状态。每次重开必须记录：

- `reopen_event_id`
- `workflow_id`
- `from_stage`
- `target_stage`
- `reason_code`
- `requested_by`
- `approved_by_or_guard`
- `invalidated_artifacts`
- `preserved_artifacts`
- `attempt_no`
- `created_at`

重开规则：

- 数据源、质量、缓存、行情时效问题：重开 S1，并使 S2-S6 当前产物失效。
- Analyst Memo 缺字段、证据不足或角色越权：重开 S2，并使 S3-S6 当前产物失效。
- Debate Summary 缺争议点、CIO agenda/synthesis、过程字段或补证引用不合规：重开 S3；若需新增证据则回到 S2。
- CIO Decision Memo 缺偏离说明或行动方案不完整：重开 S4。
- Risk rejected：阻断当前 attempt；Risk Officer 判定 `repairable / unrepairable`，可修复时附 target stage 通过 Reopen Event 回上游重做，不可修复时关闭当前 attempt 且不得进入 Owner 例外审批。
- Owner request_changes：通常重开 S4 或治理 draft/assessment。
- S7 发现问题：不修改历史执行链，只创建反思、治理提案或新任务。

禁止：

- 用重开绕过 Risk rejected。
- 直接编辑旧 artifact 替代重开。
- 删除旧产物。
- DevOps 以系统恢复为理由直接放行投资执行。

## 5. Owner 交互边界

三类 Owner 交互必须分离：

| 类型 | 用途 | 是否审批 |
|---|---|---|
| confirmation | 把自然语言请求标准化成 Request Brief，Owner 可确认、修改、取消。 | 否 |
| approval | 允许一个本来不能自动生效的高影响动作生效。 | 是 |
| manual_todo | 系统外人工动作，例如补充资料、更新房产估值。 | 否 |

进入审批中心的事项：

- Risk conditional_pass。
- CIO 重大偏离组合优化建议。
- 高影响治理变更。
- 高影响 Prompt、SkillPackage、默认上下文或知识晋升。
- 高风险财务规划或风险预算变更。

只通知不审批的事项：

- Risk approved 的正常 IC 结论。
- Daily Brief、Research Package、普通归因报告。
- 低/中影响治理建议。
- 系统异常恢复结果，除非需要改变高影响配置。
- 纸面订单正常成交、未成交或过期。

默认超时策略：

| 类型 | 默认超时 | 超时结果 |
|---|---:|---|
| Request Brief confirmation | 24 小时 | 请求草稿过期，不创建 workflow。 |
| Risk conditional_pass / S6 投资例外 | urgent 30 分钟、normal 2 小时、low 到下一交易日收盘 | 不执行，记录 `owner_timeout`，S6 blocked。 |
| CIO 重大偏离审批 | 2 小时或下一交易日收盘，取较早 | 不执行，重开 S4 或关闭。 |
| 高影响治理变更 | 72 小时 | 不生效，提案 `expired`。 |
| Prompt / Skill / 默认上下文 / 知识高影响晋升 | 72 小时 | 不生效，提案保留但不进入默认上下文。 |
| 财务风险预算/规划高影响变更 | 7 天 | 不生效，可重新提交。 |
| manual_todo | 由任务指定 due_date，默认 7 天 | 标记 `expired`，不触发审批/执行。 |

## 6. 自动化服务

| 服务 | 主要输入 | 主要输出 | 治理边界 |
|---|---|---|---|
| Data Collection & Quality | Data Request、Source Registry、外部/内部数据源 | Data Readiness Report、质量分、冲突报告、切源记录 | 不自行放行低质量正式决策或执行 |
| Market State Evaluation | 宏观、指数、行业、波动、流动性 | Market State、趋势清晰度、协作模式建议、因子权重建议 | 默认生效，可被 Macro 覆盖并留痕 |
| Factor Engine | 行情、财务、市场状态、因子定义 | 因子暴露、因子得分、因子风险 | 不宣称因子永久有效 |
| Valuation Engine | 财报、可比公司、估值参数 | 估值区间、分位、敏感性 | 不替代 Fundamental 判断 |
| Portfolio Optimization | 当前持仓、风险预算、约束、候选动作 | 目标权重、约束满足情况、偏离度 | 是约束收敛器，不是最终裁决者 |
| Risk Engine | 组合、订单、行情、约束 | 风险指标、预警、硬约束命中 | 支撑 Risk Officer，不替代 Risk Review |
| Trade Execution Service | 已放行纸面订单、行情、执行窗口 | Paper Execution Receipt | V1 仅纸面执行，无真实券商动作 |
| Performance Attribution & Evaluation | 执行、持仓表现、决策产物、服务产物 | 日度归因、评价分、异常标记 | 自动计算，不承担 LLM 治理解释 |

## 7. 数据治理

### 7.1 Data Domain Registry

V1 默认数据域：

| data_domain | 用途 |
|---|---|
| `a_share_daily_market` | A 股日线行情。 |
| `a_share_intraday_execution` | 分钟线、VWAP/TWAP、执行窗口价格。 |
| `a_share_fundamentals` | 财报三表、财务指标、估值基础数据。 |
| `a_share_corporate_actions` | 分红、复权、停复牌、ST、上市状态。 |
| `announcements` | 交易所公告、公司公告。 |
| `news_sentiment` | 财经新闻、舆情、资金流。 |
| `macro_policy` | 宏观、政策、指数、利率、流动性。 |
| `fund_gold_quotes` | 基金和黄金行情，限财务规划。 |
| `real_estate_valuation` | 房产手工或定期估值。 |
| `portfolio_internal` | 纸面账户、持仓、成本、订单、归因内部数据。 |
| `calendar_reference` | 交易日历、节假日、交易时段。 |

`allowed_usage` 必须使用以下值之一或组合：`display / research / decision_core / execution_core / finance_planning`。

### 7.2 可信层级

| 层级 | 示例 | 默认用途 |
|---|---|---|
| T0 internal | 纸面账户、持仓、订单、配置快照 | 内部权威 |
| T1 official | 交易所公告、监管/官方宏观、公司正式公告 | 重大事实确认 |
| T2 structured_provider | AKShare、Tushare、BaoStock 等结构化接口 | 行情、财务、交易日历、指标 |
| T3 crawler/news | 财经新闻、舆情、社区、研报摘要 | supporting evidence |
| T4 manual | Owner 手工录入的房产估值、收入支出、重大支出计划 | finance_planning 或 manual_todo |

### 7.3 默认源矩阵

| Data Domain | 默认主源 | 默认备源 | allowed_usage |
|---|---|---|---|
| A 股日线行情 | AKShare | BaoStock / Tushare | research, decision_core |
| A 股分钟/执行行情 | AKShare 或具备分钟数据的结构化源 | Tushare entitlement 可用时作为备源 | execution_core，必须过 freshness gate |
| 股票基础信息/上市状态 | Tushare stock_basic 或 AKShare | BaoStock | decision_core |
| 交易日历 | Tushare trade_cal 或交易所日历 | AKShare | execution_core |
| 财报/财务指标 | AKShare / Tushare | BaoStock / 官方公告核对 | decision_core |
| 公告/重大事项 | 上交所/深交所/公司公告 | 新闻聚合只做发现 | decision_core/supporting |
| 新闻/舆情/资金流 | 财经新闻源/爬虫/AKShare 资金流 | 多源交叉 | supporting_evidence |
| 宏观/政策 | AKShare + 官方来源 | 手工补录/公告源 | research, decision_core for Macro |
| 基金/黄金行情 | AKShare 或结构化行情源 | 手工/其他行情源 | finance_planning |
| 房产估值 | Owner 手工/定期估值 | 无 | finance_planning |
| 纸面账户/持仓/订单 | 内部系统 | 备份快照 | internal authoritative |

该矩阵是默认 registry，不把任何第三方 API 可用性作为唯一验收条件。

### 7.4 路由与质量

路由流程：

```text
Data Request
 -> 按 data_domain + required_usage 选 eligible sources
 -> 主源拉取
 -> 归一化
 -> 质量评分
 -> 必要时备源交叉校验
 -> 不达标则 fallback
 -> 仍不达标则 cache/display-only 或 block
 -> 输出 Data Readiness Report
```

质量分：

```text
quality_score = 0.4 * completeness + 0.4 * accuracy + 0.2 * timeliness
```

单请求评分口径：

- `completeness`: 必需字段、时间范围、证券代码、单位/币种/复权等归一化字段齐备比例。
- `accuracy`: 主备源交叉、官方来源优先级、字段容差、冲突等级和校验规则综合后的可信度。
- `timeliness`: 按 `freshness_requirement`、交易日历、公告/财报发布时间和执行窗口计算的新鲜度。
- 任一分项缺证据时不得默认满分；必须写入 Data Readiness Report 的 `critical_field_results`。

正式放行使用关键项硬门槛：

- `decision_core_status` 先按每个 `decision_core` Data Request 计算 `quality_score`，再取关键请求/关键字段的最低有效分；`>=0.9` 为 normal，`0.7-0.9` 为 degraded，`<0.7` 先 fallback，仍不可恢复则 blocked。
- `execution_core_status` 必须所有执行关键项达到当前 workflow 配置快照中的生效阈值，默认 `0.9`，且 freshness gate pass；任一失败即 blocked、纸面执行阻断或转为未成交/过期，不用缓存价格假装执行。
- `supporting_evidence` 降级：不阻断研究，但降低 evidence_quality，不能作为唯一执行依据。
- `finance_non_trade` 降级：只影响财务规划可信度和页面提示。
- 派生服务输出质量不得高于其关键输入质量。
- 多请求平均值、加权均值或展示用综合分只用于诊断和排序，不得覆盖关键字段硬阻断。

### 7.5 缓存与冲突

缓存规则：

- 可用于页面展示、研究背景、历史回放。
- 不可用于 execution_core 的纸面成交价格。
- 用于 decision_core 时必须显式标记，质量上限默认为 `0.7`。
- 超过 TTL 的缓存只能展示“过期数据”，不能参与正式决策评分。

多源冲突规则：

- 先做代码、复权、单位、币种、报告期、时间戳等归一化。
- `minor_conflict`: 差异在容差内，记录 source variance，继续。
- `material_conflict`: 超过容差但不涉及执行核心，accuracy 降级，进入 degraded。
- `critical_conflict`: 涉及执行核心、停复牌、交易日历、重大财报字段或持仓/风险约束，阻断相关阶段。
- Owner 不直接判断数据源；只有在降级下仍要推进正式执行时才承担例外审批。

## 8. 降级原则

- 数据和服务异常优先安全降级，不优先维持自动执行连续性。
- 安全降级可自动，风险放宽不能自动。
- 核心数据降级时可以继续研究，但正式新执行必须受风控条件和 Owner 例外约束。
- 服务超时可产出 degraded 状态和缺口说明，不得伪造完整结果。
- 系统异常由 DevOps 处理，业务风险由 Risk Officer 处理。
