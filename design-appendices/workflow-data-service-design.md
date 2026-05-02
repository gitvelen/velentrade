# Workflow Data Service Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 workflow、三类编排中心、数据治理、自动化服务、配置治理和 incident 状态机的实现契约。
- 实现 `src/velentrade/domain/workflow/**`、`src/velentrade/domain/data/**`、`src/velentrade/domain/services/**`、`src/velentrade/domain/governance/**`、`src/velentrade/worker/**`、Decision Service 编排或 `TC-ACC-008/009/010/011/018/030` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`spec-appendices/service-and-workflow-matrix.md`、`design-appendices/decision-service-design.md`、`contracts/domain-artifact-schemas.md`，不新增正式需求。

## 1. 模块职责

| 模块 | 负责 | 不负责 |
|---|---|---|
| Request Distribution Center | 自然语言/页面动作标准化为 Request Brief、任务卡、workflow 模板选择 | 投资判断、风控审批、直接执行 |
| Workflow Scheduling Center | TaskEnvelope、S0-S7、并发、暂停、恢复、取消、Reopen Event、AgentRun 准入 | 产出分析结论、替代 semantic lead |
| Service Orchestration Center | 调用自动化服务、重试、降级、装配服务结果 | 调用 Agent 替代 workflow、投资裁决 |
| Decision Service | 装配 CIO Decision Packet、校验 S4 输入、计算优化器偏离、生成 DecisionGuardResult、Owner 例外候选或重开建议 | 替 CIO 下结论、替 Risk 否决、替 Owner 审批、推进 workflow 状态、下单 |
| Data Collection & Quality Service | Data Request、源路由、归一化、质量评分、fallback、conflict | Owner 裁判原始数据、低质量强行放行 |
| Governance Runtime | 配置/Prompt/Skill/知识/策略、Agent 能力配置草案变更状态机、ContextSnapshot 生效边界 | 热改在途任务或 AgentRun |

Request Brief 路由实现：

| route_type | 条件 | 输出 |
|---|---|---|
| `investment_workflow` | A 股普通股，且目标是正式 IC、持仓处置或纸面交易决策 | confirmed 后创建 S0-S7 workflow。 |
| `research_task` | 资料、简报、知识检索、议题准备或 supporting evidence | TaskEnvelope + Research Package/candidate，不直接执行。 |
| `finance_task` | 财务档案、基金/黄金/房产、税务、预算或规划 | 财务 workflow；非 A 股交易动作转 `manual_todo`。 |
| `governance_task` | Prompt、Skill、默认上下文、配置、数据源或执行参数变更 | governance state machine。 |
| `agent_capability_change` | 团队页提交工具权限、SkillPackage、Prompt、模型路由、默认上下文、预算、升级规则或 rubric 变更 | Governance Change 草案；低/中影响自动验证，高影响 Owner 审批。 |
| `system_task` | 系统、数据源、服务、执行环境、安全或成本异常 | incident state machine。 |
| `manual_todo` | V1 外人工动作或系统外执行 | Task Center 记录，不进入 S5/S6。 |

路由器必须保存 `route_reason`、`route_confidence` 和候选模板；低置信、多模板冲突、资产范围不明或授权边界不明时只生成 RequestBrief draft，等待 Owner confirmation。

自由对话任务主持策略：

| task_type | 默认 semantic lead | 过程权威 | 默认产物/反馈 |
|---|---|---|---|
| `investment_workflow` | CIO | Workflow Scheduling Center + S0-S7 | IC Chair Brief、Analyst Memo、Decision/Risk/Execution artifact、Investment Dossier |
| `research_task` | Investment Researcher；事件来源可靠性或催化窗口需要判断时可请求 Event Analyst | Workflow Scheduling Center | Research Package、Search Summary、MemoryCapture、候选 TopicProposal |
| `finance_task` | CFO | Finance workflow | Finance Planning Summary、risk/budget/tax reminder、manual_todo |
| `governance_task` | 变更所属责任 Agent；跨财务/风险/系统影响时分别由 CFO/Risk/DevOps 参与 | Governance Runtime | Governance Change、impact triage、validation refs、Owner approval packet |
| `agent_capability_change` | 被修改 Agent 的责任域 owner + Governance Runtime | Governance Runtime | AgentCapabilityChangeDraft、validation plan、effective scope |
| `system_task` | DevOps Engineer | Incident Workflow | IncidentReport、RecoveryValidation、Risk handoff |
| `manual_todo` | 无 Agent 主持；Task Center 只记录人工动作 | Task Center | manual_todo 卡片、due date、风险提示 |

Request Distribution Center 不创建 AgentRun、不调用业务服务、不写正式 artifact；它只产出 `RequestBrief draft`、路由候选、任务预览和禁止动作 reason code。AgentRun 只能由 confirmed TaskEnvelope 进入模板后，由 Workflow Scheduling Center 按准入创建。

## 2. Domain Commands

| Command | 输入 | Guard | 输出 |
|---|---|---|---|
| `create_request_brief` | raw input、source、scope | source 合法；不得直接执行动作 | RequestBrief draft |
| `confirm_request_brief` | brief_id、Owner decision | draft 未过期；client version 匹配 | TaskEnvelope + workflow |
| `start_stage` | workflow_id、stage | 上游 completed；无 blocked guard | WorkflowStage running |
| `complete_stage` | stage、artifact_refs | 必需 artifact schema pass | WorkflowStage completed |
| `block_stage` | stage、reason_code | reason code 合法 | WorkflowStage blocked |
| `request_reopen` | from_stage、target_stage、reason | target 合法；invalidated/preserved 明确 | ReopenEvent |
| `apply_owner_timeout` | approval_id/task_id | now >= deadline | expired/blocked/no-effect |
| `submit_governance_change` | proposal | schema pass | governance draft |
| `triage_governance_change` | proposal | impact policy available | low/medium/high |
| `activate_context_version` | version refs | validation pass；scope new task/new attempt | ContextSnapshot version |

所有 command 必须写 audit_event 和 outbox_event；失败时返回错误码和 reason_code，不做半写入。

## 2.1 三类编排中心运行手册

### Request Distribution Center

```text
raw input or page action
 -> classify intent and asset scope
 -> build RequestBrief or GovernanceChange draft
 -> validate forbidden direct actions
 -> Owner confirm/edit/cancel when required
 -> emit TaskEnvelope or governance draft
```

中心只做入口归一化和模板选择。遇到“直接下单”“绕过风控”“立刻改某个 Agent 权限”等输入时，必须转为受控 brief/draft 或拒绝，并写入 reason_code。

自由对话承接步骤：

1. 解析 raw input，抽取目标、对象、资产/领域、动作动词、紧急度、授权边界和时间预算；保存原文 ref，但原文不作为正式事实源。
2. 匹配 route_type 与 workflow template；若候选模板分数接近、资产范围不明、成功标准不清或授权越界，只生成 `RequestBrief(owner_confirmation_status=draft)`。
3. 生成 preview：展示任务类型、建议 semantic lead、过程权威、预计产物、是否会创建 AgentRun、是否可能触发 Owner approval、禁止动作转换说明。
4. Owner 选择 confirm/edit/cancel；edit 重新路由，cancel/expired 不创建 TaskEnvelope。
5. confirm 后创建 TaskEnvelope，绑定 `task_type`、priority、owner_role、reason_code、artifact_refs 和 ContextSnapshot。
6. Workflow Scheduling Center 选择模板、检查并发和 guard，再按模板创建 service call 或首个 AgentRun。
7. 首个 AgentRun 完成后必须写正式 artifact 或 blocked reason；不能只返回聊天文本。
8. Read model 同步刷新 Owner Decision View、Task Center、领域详情页和 Trace/Debug。

### Workflow Scheduling Center

```text
TaskEnvelope
 -> select workflow template and attempt_no
 -> check concurrency and stage guards
 -> create ContextSnapshot binding
 -> admit service call or AgentRun
 -> receive artifact/event through Authority Gateway
 -> transition stage or block/reopen
 -> project read model
```

中心是过程权威。它可以创建 AgentRun 和 service_call，但不能替 Agent 写语义 artifact，也不能把服务输出直接当审批或风控结论。

### Service Orchestration Center

```text
stage guard requests service result
 -> resolve ContextSnapshot and data policy
 -> call deterministic service with idempotency key
 -> retry/fallback/degrade by policy
 -> write service_result or incident
 -> return guard input to workflow
```

服务编排负责自动服务的顺序、重试、降级和审计。S4 调用 Decision Service 时，也按该路径生成 service_call、DecisionPacket 和 DecisionGuardResult；后续进入 CIO AgentRun、Risk Review、Owner exception 或 Reopen Event 仍由 Workflow Scheduling Center 决定。

## 3. 状态机

轻量任务：

```text
draft -> ready -> queued -> running -> waiting | blocked | paused -> running -> completed
terminal: completed | canceled | failed | expired
```

投资主链每阶段节点状态：

```text
not_started -> running -> waiting | blocked | completed | skipped | failed
```

治理任务：

```text
draft -> triage -> assessment -> owner_pending -> approved -> effective
terminal without effect: rejected | expired | canceled | activation_failed
```

incident：

```text
detected -> triaged -> mitigating -> monitoring -> closed
terminal: unresolved | escalated
```

`reopened`、`owner_timeout`、`degraded`、`rejected`、`unfilled` 不作为节点状态。

## 4. S0-S7 运行契约

| 阶段 | 必需输入 | 主要输出 | Guard |
|---|---|---|---|
| S0 | confirmed Request Brief | TaskEnvelope、Topic candidate | 目标/范围/授权/阻断条件齐全 |
| S1 | DataRequest、SourceRegistry | DataReadinessReport、IC Chair Brief | decision_core 可用；execution_core 不足只记录 blocker |
| S2 | IC Context、四 Analyst AgentRun | AnalystMemo x4 | Memo schema、role_payload、证据引用 |
| S3 | Memo x4、consensus | DebateSummary 或 debate_skipped | 最多 2 轮；低共识阻断 |
| S4 | DecisionPacket | CIODecisionMemo、DecisionGuardResult、DecisionExceptionCandidate/ReopenRecommendation | Decision Service 输入完整；偏离解释；CIO 禁止越权 |
| S5 | CIO Memo、Risk inputs | RiskReviewReport | 三状态；rejected 硬阻断 |
| S6 | Risk approved/conditional approval | ApprovalRecord、PaperExecutionReceipt | Owner 超时不执行；execution_core pass |
| S7 | execution/position/decision artifacts | AttributionReport、ReflectionRecord | 只追加归因反思，不改历史链 |

## 5. Data Request 与质量门

Data Request 必须包含 `data_domain`、`required_usage`、`freshness_requirement`、`required_fields` 和请求来源。路由流程：

```text
Data Request
 -> eligible sources by domain/usage
 -> primary source fetch
 -> normalization
 -> quality score
 -> fallback/cross-check if needed
 -> cache/display-only or block
 -> Data Readiness Report
```

### 5.1 公开 HTTP 数据源最小实现

WI-002 的真实数据采集最小实现不绑定付费或需密钥供应商；默认交付一个可由 Source Registry 配置的 `public_http_csv_daily_quote` adapter。该 adapter 必须真实执行 HTTP fetch、解析公开 CSV 行情响应、归一化为 `symbol/trade_date/open/high/low/close/volume/source_timestamp/source_id`，并把 `license_summary`、`rate_limit`、`endpoint_template`、`cache_ttl_seconds`、`adapter_kind` 写入 source metadata。自动化测试不得依赖外网可用性；必须用本地 HTTP 或 fake transport 验证真实 fetch/parse/quality/fallback/cache 路径。外网 live provider smoke 只能作为单独运行证据记录，失败不得被伪装成自动化 pass。

Source Registry 默认至少区分三类来源：

| adapter_kind | 用途 | completion_level |
|---|---|---|
| `public_http_csv_daily_quote` | 公开 HTTP CSV 日线行情；可用于 `research` / `decision_core`，不得用于 `execution_core` 新成交。 | `in_memory_domain` 或更高，取决于是否接入持久化/运行环境 |
| `fixture_contract` | 合同 fixture 与离线测试。 | `fixture_contract` |
| `cache_snapshot` | 最近一次成功采集的展示/研究缓存；不得生成新的执行授权。 | `in_memory_domain` |

公开源失败或字段缺失时必须先按 `fallback_order` 尝试替代源；若仍失败，`decision_core` 输出 degraded/blocked，`execution_core` 一律 `blocked`。缓存命中只能用于展示、研究或降级诊断；用于 `decision_core` 时质量上限为 `0.7`，用于 `execution_core` 时必须阻断纸面执行。

质量分：

```text
quality_score = 0.4 * completeness + 0.4 * accuracy + 0.2 * timeliness
```

分项计算口径：

- `completeness`: `required_fields`、time_range、symbol/scope、单位/币种/复权/报告期等归一化字段齐备比例。
- `accuracy`: 主备源交叉、source priority、字段容差、schema validation、conflict severity 的综合结果。
- `timeliness`: 数据时间戳相对 `freshness_requirement`、交易日历、公告/财报发布时点和执行窗口的新鲜度。

实现算法：

- `completeness = sum(weight(field) for present_valid_required_fields) / sum(weight(field) for required_fields)`；默认每个字段权重 1，执行价格、停复牌、交易日历、证券代码、报告期、复权/单位/币种等可在 Data Domain Registry 标记 `critical=true`，critical 字段缺失时该字段有效分固定为 0。
- `accuracy = 0.35 * source_trust + 0.25 * schema_validation + 0.25 * cross_source_agreement + 0.15 * normalization_quality - conflict_penalty`，裁剪到 0..1。`source_trust` 默认 T0/T1/T2/T3/T4 为 1.0/0.95/0.85/0.60/0.70；`schema_validation` 通过为 1，失败为 0；`cross_source_agreement` 无备源但主源合法时为 0.8，有备源且容差内为 1；`normalization_quality` 按代码、单位、币种、复权、报告期、时间戳归一成功比例计算；`minor/material/critical_conflict` 的 penalty 为 0/0.25/1。
- `timeliness` 以 `freshness_requirement` 为基准：`age <= requirement` 得 1；`requirement < age <= 2 * requirement` 得 0.7；`2 * requirement < age <= 5 * requirement` 得 0.4；更旧得 0。公告/财报使用发布时间和报告期双重检查，交易执行使用交易日历和分钟 bar 时间戳。
- `execution_core` 不使用综合分兜底。执行价格、VWAP/TWAP 输入分钟线、交易日历、停复牌、涨跌停/可交易状态、费用税费参数必须各自 `effective_score >= effective_threshold` 且 freshness pass；任一失败则 `execution_core_status=blocked`。
- 派生服务输出 `output_quality_score <= min(input_quality_scores)`，不能通过计算服务把低质量输入变成高质量输出。

示例：

```yaml
decision_core_daily_quote:
  required_fields: [symbol, trade_date, close, volume, adjustment, source_timestamp]
  completeness: 1.0
  accuracy: 0.86
  timeliness: 1.0
  quality_score: 0.944
  band: normal
execution_core_intraday:
  required_fields: [minute_ts, price, volume, trade_calendar, halt_status, fee_profile]
  critical_field_results:
    volume: {effective_score: 0.0, reason: missing}
  execution_core_status: blocked
```

放行规则：

- `decision_core_status` 取所有 `decision_core` 关键请求/关键字段的最低有效分；`>=0.9` 正常，`0.7 <= score <0.9` 可研究但 Risk 只能 `conditional_pass`，`<0.7` 先 fallback，仍不可恢复则阻断新决策和执行。
- `execution_core_status` 要求执行价格、VWAP/TWAP 所需行情、交易日历、停复牌状态和费用税费参数都达到 `effective_threshold` 且 freshness pass；任一失败即严格阻断纸面执行，默认阈值 `0.9`，Owner 不能例外批准降级成交。
- 缓存可展示/研究；用于 decision_core 时质量上限 `0.7`；不得用于 execution_core 新成交。
- Data Readiness Report 可展示综合均值用于诊断，但放行只能看关键字段最低有效分、freshness 和冲突等级。

冲突等级：

- `minor_conflict`：记录 variance，继续。
- `material_conflict`：accuracy 降级，进入 degraded。
- `critical_conflict`：涉及执行核心、停复牌、交易日历、重大财报字段或持仓/风险约束，阻断相关阶段。

## 6. 自动化服务 I/O

| 服务 | 输入 | 输出 artifact/result | Guard |
|---|---|---|---|
| Market State Evaluation | macro/index/industry/liquidity data | MarketState、collaboration mode、factor weight suggestion | Macro override 留痕，不是默认前置门 |
| Factor Engine | market/fundamental/market state/factor defs | factor exposure、signal score、risk | 不回测，不宣称永久有效 |
| Valuation Engine | fundamentals、comparables、params | valuation range、sensitivity | 不替代 Fundamental Memo |
| Portfolio Optimization | holdings、risk budget、constraints、candidate action | target weights、constraint status、deviation | 不做最终投资裁决 |
| Decision Service | IC Context、Chair Brief、Memo、Debate、optimizer、data readiness、holdings/constraints | DecisionPacket、DecisionGuardResult、DecisionExceptionCandidate、ReopenRecommendation | 不替 CIO/Risk/Owner 决策；不推进 workflow |
| Risk Engine | portfolio、order、market、constraints | risk metrics、hard constraint hit | 支撑 Risk Officer |
| Trade Execution Service | released paper order、execution_core data | PaperExecutionReceipt | V1 仅纸面执行 |
| Performance Attribution | execution、position、decision artifacts | AttributionReport、quality scores | 不签发治理判断 |

服务输出只可作为 artifact 或 service_result；不得直接生成审批、否决、真实交易或最终投资判断。

### 6.1 Market State 默认分类

Market State Evaluation Engine 输出 `MarketState` 支撑 artifact，不是投资裁决。V1 默认枚举：

| state | 分类标准 | collaboration mode | factor weight suggestion |
|---|---|---|---|
| `risk_on` | 趋势广度正常、波动/回撤低、流动性/信用不收缩、无 stress flag | 标准 IC；高共识无 hard dissent 可按规则跳过 S3 | 可适度提高动量、盈利质量、行业景气因子解释权重 |
| `neutral` | 多数输入中性，未命中 risk_on/risk_off/stress | 标准 IC；Macro 不成为前置门 | 使用默认因子权重 |
| `risk_off` | 市场广度转弱、波动或回撤升高、流动性/信用收缩任两项命中 | 更倾向保留 S3 讨论；CIO Chair Brief 必须要求风险/仓位问题 | 降低高 beta/拥挤动量，提高质量、防御、流动性约束权重 |
| `stress` | 跌停/停牌/流动性风险、重大政策/信用冲击或 execution environment P0 命中 | 必须显式 Risk handoff；禁止用 Market State 本身生成交易结论 | 不提高进攻因子；执行和风险约束优先 |
| `transition` | 最近两个观察窗口 state 不一致，或 Macro/Event 证据显示状态切换但数据尚未稳定 | S3 默认不因高共识自动省略，除非无 hard dissent 且 CIO 写明 transition 影响已覆盖 | 因子建议只作为 sensitivity，不改变默认权重 |

输入维度和默认评分：

- `trend_breadth`: 指数趋势、行业上涨比例、宽基/行业相对强弱。
- `volatility_drawdown`: 波动率、最大回撤、涨跌停/停复牌异常。
- `liquidity_credit`: 成交额、换手、资金利率/信用利差、融资环境。
- `policy_industry_style`: 政策立场、行业风格、事件冲击。

实现按 deterministic rule 先判 `stress`，再判 `transition`，再在 `risk_on / risk_off / neutral` 中选择。每次输出必须包含 `state`、`input_window`、`dimension_scores`、`reason_codes`、`confidence`、`collaboration_mode`、`factor_weight_suggestion` 和 `source_refs`。Macro Analyst 可提交 `Market State View Update` 或 override proposal；override 只进入审计和 Dossier/Trace 展示，不阻止 engine 默认 state 进入 IC Context。

## 7. ContextSnapshot 与治理生效

`ContextSnapshot` 必须绑定：

- 阈值、风控参数、审批规则。
- Prompt、SkillPackage、默认上下文、模型路由、工具权限。
- 服务降级策略、数据源路由策略、执行参数。
- data policy version 和 registry version。

`ContextSnapshot` schema 以 `contracts/domain-artifact-schemas.md` 为准，运行时必须满足：

- 创建时计算 canonical JSON `content_hash`，`frozen=true` 后不可更新。
- workflow attempt 和 AgentRun 只保存 `context_snapshot_id` 与 `context_slice_id`，不复制可变配置。
- 新 Prompt、SkillPackage、数据源路由、执行参数或默认上下文生效时只能生成新 snapshot；旧 in-flight workflow、旧 AgentRun 和旧 artifact lineage 保持旧 snapshot。
- 测试 fixture 可创建 `effective_scope=test_fixture` snapshot，但不得进入真实任务默认 registry。

生效规则：

- 低/中影响变更：triage -> schema/fixture validation -> version snapshot -> audit -> effective。
- 高影响变更：draft -> triage -> assessment -> owner_pending -> approved -> effective。
- 任何 effective 只作用于新任务或新 attempt；in-flight workflow 和 AgentRun 继续使用旧快照。
- Governance Impact Policy 可配置，但修改它本身永远是高影响。

治理状态转换：

| from | trigger / actor | guard | to | side effect |
|---|---|---|---|---|
| draft | `submit_governance_change` / Researcher、CFO、DevOps、Risk 或 Owner | proposal schema pass，change_type 合法 | triage | 写 audit_event，锁定 proposal version |
| triage | `triage_governance_change` / Governance Runtime | Governance Impact Policy 可用；不能把 high 静默降级 | assessment | 记录 impact_level、affected_roles、affected_workflows |
| assessment | 自动领域评估 / Risk、CFO、DevOps、Researcher 或服务 | schema validation、fixture validation、scope impact、rollback plan 均完成 | effective 或 owner_pending | low/medium 可自动生成 version snapshot；high 生成 Owner approval packet |
| owner_pending | Owner decision approved | approval packet version 匹配，未超时 | approved | 记录 approval_ref |
| owner_pending | Owner rejected | approval packet version 匹配 | rejected | 不生成新 snapshot |
| owner_pending | timeout | now >= deadline | expired | 不生成新 snapshot |
| approved | `activate_context_version` / Governance Runtime | target versions 可解析，snapshot hash 生成成功，rollback refs 存在 | effective | 注册新 ContextSnapshot，只对新任务/新 attempt 生效 |
| approved | activation error | 版本生成、schema 校验或 snapshot 绑定失败 | activation_failed | 保留错误和回滚 refs，不生效 |
| draft/triage/assessment | cancel / proposer or guard | 尚未 effective | canceled | 不生效，写 close reason |

低/中影响自动验证固定检查：

- schema validation：proposal、manifest、diff、目标 artifact schema 通过。
- fixture validation：至少运行命中的 `TC-*` fixture 子集或 seed fixture，结果引用写入 `validation_result_refs`。
- scope/impact check：确认不改变审批规则、风险预算、执行参数、Agent 权限或 Governance Impact Policy 的高影响边界。
- rollback check：存在 rollback plan 和旧版本 refs。
- snapshot check：新 `ContextSnapshot.content_hash` 可复算，且 in-flight snapshot 未变化。

## 8. 错误、重试与降级

| 场景 | 处理 |
|---|---|
| command validation fail | 返回 `VALIDATION_ERROR`，不写业务状态 |
| stage guard fail | 写 audit event，stage blocked/waiting，返回 reason_code |
| Celery 重试 | 使用 outbox + idempotency key，重复消息不重复写 artifact |
| service timeout | 写 degraded result 或 incident，不伪造完整结果 |
| Data fallback fail | DataReadiness blocked；按 stage guard 阻断 |
| activation failed | governance 状态 `activation_failed`，不生效 |
| owner timeout | 按审批类型写 `expired`、`blocked` 或 reopen/close |

## 9. 验证映射

- `s0_s7_workflow_report.json`：验证 stage guard、节点状态、ReopenEvent、artifact superseded。
- `data_quality_degradation_report.json`：验证三档质量、fallback、cache、conflict 和 execution_core 阻断。
- `service_boundary_report.json`：扫描服务输出和 forbidden authority。
- `market_state_report.json`：验证 Market State 默认进入 IC Context 和 Macro override 留痕。
- `decision_service_report.json`：验证 DecisionPacket、S4 guard、偏离守卫、失败路径和服务无越权。
- `config_governance_report.json`：验证低/中/高影响治理状态机、ContextSnapshot 和 in-flight 不热改。

## 10. R8 通用运行主干

所有领域 workflow 必须复用同一条 spine。实现者不得在投资、财务、知识、DevOps 或治理链路中绕过该 spine 创建隐式状态或隐式事实源。

```text
Request Brief
 -> TaskEnvelope
 -> workflow template selection
 -> stage guard / domain command
 -> DataRequest / ServiceResult / AgentRun admission
 -> ContextSnapshot + ContextSlice
 -> AgentRun or service execution
 -> CollaborationCommand loop when semantic coordination is needed
 -> Authority Gateway artifact/event/handoff submission
 -> HandoffPacket
 -> stage completed / waiting / blocked / skipped / failed / reopened
 -> read model projection
 -> verification report
```

### 10.1 Spine 职责分工

| 角色 | 拥有 | 不拥有 |
|---|---|---|
| Workflow Scheduling Center | 阶段、节点状态、attempt、并发、暂停、恢复、超时、ReopenEvent、AgentRun 准入 | 投资判断、业务解释、服务计算 |
| Service Orchestration Center | 自动服务调用、重试、降级、服务结果装配、outbox | Agent 语义判断、Risk 放行、Owner 审批 |
| Data Collection & Quality Service | DataRequest、源路由、质量评分、缓存/冲突/fallback、lineage | Owner 裁判原始数据、低质量强行放行 |
| Authority Gateway | typed command/artifact/event/handoff 写入校验、append-only、audit/outbox | 业务阶段推进、语义综合 |
| Semantic lead Agent | 议程、追问、解释、综合、治理提案或反思分派 | workflow state transition、服务操作、审批或风控绕过 |

### 10.2 Workflow Template Runbook

所有模板必须按以下结构登记：

```yaml
template_id: string
task_type: investment_workflow | research_task | finance_task | governance_task | system_task | manual_todo
trigger_sources: string[]
semantic_lead_policy: string
process_authority: string
required_context_snapshot: true
owner_preview_fields: string[]
first_feedback_sla: string
stages:
  - stage_id: string
    entry_guard: string[]
    required_inputs: string[]
    allowed_services: string[]
    allowed_agent_runs: string[]
    allowed_commands: string[]
    required_outputs: string[]
    failure_paths: string[]
read_model_projection: string[]
verification_refs: string[]
```

实现约束：

- 模板必须静态登记；Request Distribution Center 只能选择模板，不能让 LLM 临时发明流程或主持人。
- `semantic_lead_policy` 必须能解析为明确角色或角色选择规则；CIO 只作为投资 IC 的默认 semantic lead。
- `owner_preview_fields` 至少覆盖任务类型、负责人、预期产物、后续审批可能性、禁止动作处理和阻断条件。
- `first_feedback_sla` 是前端反馈承诺，不代表投资或研究完成时限；超时必须写 waiting/blocked reason。
- `start_stage` 只能在上游完成或允许 skipped 时执行。
- `complete_stage` 必须校验 required_outputs 的 artifact schema 和 source_refs。
- `block_stage` 必须写 reason_code，并投影到 Owner/Dossier/Trace。
- `request_reopen` 必须声明 invalidated/preserved artifacts。
- `apply_owner_timeout` 只能根据审批类型写 no-effect 结果，不得默认批准。

### 10.3 服务执行 Runbook

```text
1. Workflow 或 Agent command 提交 service request。
2. Service Orchestration Center 校验 stage、usage、ContextSnapshot 和 idempotency key。
3. Data Service 获取所需 DataRequest，执行 source routing、quality scoring、fallback/cache/conflict。
4. 自动化服务读取 accepted DataReadiness 和上游 artifact。
5. 服务输出 ServiceResult 或 artifact；output_quality_score 不得超过输入质量下限。
6. Authority Gateway 或 domain handler 写入 ServiceResult、audit_event、outbox_event。
7. Workflow guard 根据质量、schema 和业务规则决定 continue、degraded、blocked 或 reopen。
8. Read model 投影服务状态、限制和阻断原因。
```

失败处理：

- service timeout：写 degraded result 或 incident，不伪造完整结果。
- schema fail：stage waiting/blocked，必要时 request_reopen。
- data fallback fail：DataReadiness blocked。
- execution_core blocked：S6 不得执行，Owner 无例外入口。
- duplicate task：idempotency key 返回原结果，不重复写 artifact。

### 10.4 Read Model Projection

每个 stage guard 结果必须投影到至少一个观察面：

- Owner Decision View：只投影需要 Owner 注意、审批、manual_todo、blocked、incident 的摘要。
- Investment Dossier：投影 S0-S7 stage、artifact、reason code、data quality、Agent stance、Risk/Execution/Attribution。
- Trace/Debug：投影 command、event、AgentRun、service call、gateway write、guard fail、ContextSlice。
- Governance/Health：投影 governance change、data/service health、incident、audit trail。

禁止把 read model 做成业务写入口。前端只能提交 RequestBrief、WorkflowCommand、ApprovalDecision 或 CollaborationCommand；业务推进仍由 domain command handler 执行。

### 10.5 自由对话任务承接 Runbook

trigger：

- Owner 在全局命令层安排研究、学习、财务、治理、系统或人工事项。
- 页面 action 需要创建任务、补证、审批材料或治理草案。

participants：

- process authority：Request Distribution Center 只负责归一化；Workflow Scheduling Center 或对应 runtime 负责后续状态。
- semantic lead：按 task_type 模板选择，投资为 CIO，研究为 Researcher，财务为 CFO，系统为 DevOps，治理按变更责任域选择。
- required services：Context Engine、Data Service、Authority Gateway、read model projector。

steps：

1. `create_request_brief` 写 draft，保存 raw input ref、route candidates、route_reason、route_confidence 和 forbidden action checks。
2. 前端展示 RequestBrief preview；若是“学习热点事件”，默认 route 为 `research_task`，目标是 Research Package/Memory/候选 TopicProposal，不直接进入 IC。
3. Owner confirm 后，`confirm_request_brief` 创建 TaskEnvelope；edit 重新生成 draft；cancel/expired 只写 audit，不创建 workflow。
4. Workflow 模板创建 ContextSnapshot，并按 `semantic_lead_policy` 创建首个 AgentRun 或 service call。
5. AgentRun 通过 Authority Gateway 写 ResearchPackage、FinanceSummary、IncidentReport、GovernanceChange 或投资链 artifact；轻量进展写 CollaborationEvent。
6. 若 semantic lead 需要其他 Agent，必须提交 CollaborationCommand，按准入矩阵 accepted 后才创建目标 AgentRun。
7. 完成、等待、阻断、失败或过期都必须写 reason_code，并投影到 Task Center。

failure_paths：

- 低置信或多模板冲突：保持 draft，preview 显示需要 Owner 补充的问题。
- 禁止动作：拒绝或转为受控 workflow，并写 `blocked_direct_action` 类 reason_code。
- 首个 AgentRun timeout/schema fail：任务进入 waiting/blocked，可 request_reopen 或 request_manual_todo。
- supporting evidence 试图直接进入 IC：生成 candidate/ResearchPackage，不生成正式 IC slot。

view_projection：

- Owner Decision View：只显示需处理的摘要、等待确认、blocked 或 manual_todo。
- Task Center：显示 task_type、priority、current_state、semantic lead、blocked_reason、reason_code。
- 领域详情页：投资进入 Dossier；研究进入 Knowledge/Research 详情；治理进入 Governance；系统进入 Health/Incident。
- Trace/Debug：显示 brief、route decision、template、AgentRun、Command/Event、Gateway write 和拒绝原因。

verification：

- `TC-ACC-006-01` 验证自由对话 preview、确认、任务卡和三层视图跳转。
- `TC-ACC-007-01` 验证 Task Center 中 task_type、state、reason_code、manual_todo 和审批隔离。
- `FX-SUPPORTING-EVIDENCE-ONLY` 验证热点/新闻只生成候选或研究任务，不直接进入正式 IC。

### 10.5 R8 Verification

`s0_s7_workflow_report.json` 必须证明：

- 每个阶段的 entry_guard、required_inputs、required_outputs 和 failure_paths 被执行。
- ReopenEvent 使旧 artifact superseded，新 attempt 继承 preserved context。
- blocked/waiting/skipped/failed 由 guard 写入，不由前端或 Agent 直接写入。
- Read model 可以解释每个 blocked reason。

`service_boundary_report.json` 必须证明：

- 服务输出不包含 approval、Risk verdict、final investment decision 或 real trade action。
- 服务 failure 不会被伪造成完整结果。
- ServiceResult 限制能被 Agent 和 UI 看到。

`config_governance_report.json` 必须证明：

- 低/中影响自动验证包含 schema、fixture、scope/impact、rollback、snapshot check。
- 高影响必须进入 Owner approval。
- in-flight workflow 和 AgentRun 的 ContextSnapshot 不变。
