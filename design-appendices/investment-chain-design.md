# Investment Chain Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 A 股投资主链的实现契约，覆盖机会注册、Topic Queue、IC Context、四 Analyst Memo、共识/辩论、Decision Service、CIO、Risk、Owner 例外、纸面账户/执行和持仓处置。
- 实现 `src/velentrade/domain/investment/**`、`tests/domain/investment/**` 或 `TC-ACC-012` 到 `TC-ACC-022` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`spec-appendices/investment-ic-risk-execution.md`、`design-appendices/decision-service-design.md`、`contracts/domain-artifact-schemas.md`，不新增正式需求。

## 1. 投资主链模块

| 模块 | 职责 |
|---|---|
| Opportunity Registry | 接收 Owner、Analyst、Researcher、服务信号、持仓风险和公告来源 |
| Topic Queue | 硬门槛、四维评分、并发槽、P0 抢占 |
| IC Context Builder | 装配共享事实包、服务结果、组合/风险上下文、研究资料、反思命中和角色附件 |
| Consensus Service | 计算 `consensus_score`、`action_conviction`、hard dissent |
| Debate Manager Adapter | 调用协作协议执行 S3 过程字段和重算 |
| Decision Service | 装配 CIO Decision Packet、校验 S4 输入、计算偏离守卫、生成 Owner 例外候选或重开建议 |
| CIO Decision Builder | 消费 Decision Packet，校验/保存 CIO Decision Memo schema |
| Risk Review Runtime | 三状态、repairability、Owner exception packet |
| Paper Account/Execution | 100 万 CNY 空仓账户、订单、VWAP/TWAP、费用税费、T+1 |
| Position Monitor | 持仓异常、重大公告、风险阈值、执行失败、处置任务 |

## 2. 机会注册与 Topic Queue

Opportunity 输入统一转为 `TopicProposal`：

```yaml
topic_proposal_id: string
source_type: owner | analyst | researcher | service_signal | holding_risk | announcement
symbol: string
raw_trigger_ref: string
supporting_evidence_refs: string[]
requested_priority: P0 | P1 | P2 | null
research_package_ref: string | null
created_by: string
```

正式 IC 硬门槛：

- A 股普通股范围。
- Request Brief 完整。
- decision_core 数据可用。
- 研究资料非空。
- 合规/执行禁区未命中。
- 同主题去重。
- 正式 IC 并发槽可用。
- 四维优先级评分已完成。
- P0 抢占记录完整。

四维评分 0-5：

- opportunity_strength
- data_completeness
- risk_urgency
- portfolio_relevance

默认权重：

```text
priority_score = 0.35 * opportunity_strength
               + 0.25 * data_completeness
               + 0.25 * risk_urgency
               + 0.15 * portfolio_relevance
```

单维评分来源：

- `opportunity_strength`: Owner 明确目标、服务信号强度、估值/因子/事件一致性、反证强度折减；0 表示仅噪声，5 表示多个正式来源一致且行动窗口清晰。
- `data_completeness`: Data Readiness、Research Package、关键证据引用和 source conflict；0 表示 decision_core 不可用，5 表示关键字段 normal 且资料包完整。
- `risk_urgency`: 持仓风险、重大公告、执行失败、止损/暂停建议和 Owner 显式紧急；非持仓正面机会默认不超过 3。
- `portfolio_relevance`: 当前持仓、目标组合偏离、风险预算占用、现金约束和组合集中度；与组合无关默认为 1。

排序规则：先按 P0/P1/P2，再按 `priority_score`，再按 `created_at`。评分只决定排序和并发，不替代 IC 结论。新闻、舆情、资金流等 supporting evidence 只能生成 candidate、Research Package 或研究任务，不能直接进入正式 IC。

P0 抢占规则：

- 只有持仓风险、重大公告/执行失败、Risk/Owner 显式紧急可生成 P0；服务层正面机会默认不能自动 P0。
- 正式 IC active slots 已满时，P0 可抢占最低 `priority_score` 的 P1/P2 active workflow；不得抢占另一个 P0。
- 被抢占 workflow 进入 `waiting`，写 `preempted_by_topic_id`、reason code、preserved artifacts 和 resume priority；不删除 AgentRun 或 artifact。
- 抢占只释放并发槽，不跳过 S1-S7、Risk、Owner 或审计。

## 3. IC Context 与 Chair Brief

`ICContextPackage` 必须引用：

- Request Brief。
- Data Readiness Report。
- Market State。
- Factor/Valuation/Portfolio/Risk service results。
- 组合上下文与风险约束。
- Research Package。
- 历史反思和经验命中。
- 四类角色附件。
- ContextSnapshot。

角色附件限制默认注入范围，不限制组织透明读。

S1 完成后创建 CIO AgentRun 输出 `ICChairBrief`。Chair Brief 必须包含：

- decision_question
- scope_boundary
- key_tensions
- must_answer_questions
- time_budget
- action_standard
- risk_constraints_to_respect
- forbidden_assumptions
- no_preset_decision_attestation

Chair Brief 禁止预设买/卖/持有、目标仓位或任何分析师结论。

## 4. Analyst Memo 与共识

四位 Analyst Memo 共享外壳，role_payload 必须独立。实现中应使用 schema validator：

- Macro payload：市场状态、政策传导、流动性、信用周期、行业/风格、顺风/逆风、传导路径、宏观风险。
- Fundamental payload：商业模式、护城河、财务质量、盈利情景、估值方法、公允价值、安全边际、会计红旗、KPI。
- Quant payload：信号假设、趋势、量价、因子暴露、样本上下文、稳定性、regime fit、择时、拥挤风险。
- Event payload：事件类型、时间线、来源可靠性、验证状态、催化强度、窗口、基本面假设影响、情绪/资金流、历史类比、反转风险。

共识计算：

```text
direction_sign = positive if direction_score > 0, neutral if = 0, negative if < 0
dominant_direction_share = count(max direction_sign) / 4
std = population_std(direction_score / 5)
consensus_score = 0.6 * (1 - std) + 0.4 * dominant_direction_share
action_conviction = 0.35 * abs(avg(direction_score / 5))
                  + 0.25 * avg(confidence)
                  + 0.20 * avg(evidence_quality)
                  + 0.20 * consensus_score
```

默认行动阈值 `0.65`。

hard dissent：

- 某 analyst 方向与多数非 neutral 方向相反，且 `abs(direction_score) >= 4` 或 `confidence >= 0.7`。
- 不存在多数非 neutral 方向时不自动 hard dissent，按低共识/辩论处理。

## 5. 辩论与 S3

路径：

- `consensus >= 0.8`、`action_conviction >=0.65` 且无 hard dissent：生成 `debate_skipped` artifact。
- `consensus >= 0.8` 但 `action_conviction <0.65` 且无 hard dissent：不生成执行授权；可跳过 S3 进入 S4 的 `observe / no_action / reopen`，或由 CIO 请求补证。
- `consensus >= 0.8` 且有 hard dissent：必须进入最多 2 轮辩论。
- `0.7 <= consensus < 0.8`：进入最多 2 轮辩论。
- `< 0.7`：不允许纸面执行，输出 reason code 和补证/观察建议。

S3 后重算矩阵：

| 重算结果 | next_stage_decision |
|---|---|
| `consensus >=0.7`、`action_conviction >=0.65`、无 retained hard dissent | 可进入 S4。 |
| retained hard dissent | 标记 `risk_review_required=true`；可进入 S4 形成语义结论，但 S5 必须显式评估 hard dissent。 |
| `action_conviction <0.65` | 不得执行；S4 只能 `observe / no_action / reopen`。 |
| `consensus <0.7` | 阻断执行，输出 `low_consensus_no_execution` 或补证/reopen reason。 |

Debate Manager 过程字段：

- rounds_used、participants、issues、new_evidence_refs、view_changes。
- retained_dissent、hard_dissent_present、retained_hard_dissent。
- risk_review_required、recomputed_consensus_score、recomputed_action_conviction。
- stop_reason、next_stage_decision。

CIO 语义字段：

- agenda、questions_asked、synthesis、resolved_issues、unresolved_dissent、chair_recommendation_for_next_stage、semantic_lead_signature。

CIO 可发 `ask_question`、`request_view_update`、`request_evidence`、`request_agent_run`，但必须经过 CollaborationCommand 准入；不能直接改状态或增加轮次上限。

单轮辩论流程：

| step | 输入 | 责任方 | 输出 / guard |
|---|---|---|---|
| round_open | IC Context、Chair Brief、四 Memo、上一轮 summary、补证 refs | Debate Manager | 创建 round record，校验 `round_no <= 2` |
| agenda | hard dissent、低共识维度、证据冲突 | CIO | `agenda` 和 `questions_asked`，不能预设结论 |
| analyst_response | agenda、自己原 Memo、可引用 evidence refs | 四 Analyst | view update/comment/evidence request；不得覆盖原 Memo |
| process_collect | 四 Analyst responses | Debate Manager | `issues`、`new_evidence_refs`、`view_changes`、timeout/缺席记录 |
| recompute | 最新有效方向分、置信度、证据质量、hard dissent | Consensus Service | recomputed consensus/action_conviction |
| round_close | process fields、CIO synthesis | Debate Manager + CIO | 判断 `converged/no_new_evidence/max_rounds/retained_hard_dissent/low_*_blocked` |

若某 Analyst 超时，Debate Manager 记录 timeout event；只要剩余材料足以形成 guard 判断，可结束本轮，但不能伪造该 Analyst 观点更新。新增正式 AgentRun 或补证请求仍走 CollaborationCommand 准入。

## 6. CIO Decision 与优化器

S4 Decision Packet 由 Decision Service 装配，详细运行手册见 `design-appendices/decision-service-design.md`。本附件只保留投资链上下文。

Decision Packet 输入：

- IC Context Package、Chair Brief、四 Memo、Consensus/action conviction、Debate Summary。
- Portfolio Optimization result、Risk Engine precheck、Data Readiness。
- 当前持仓、现金、风险预算、执行约束。

`CIODecisionMemo` payload：

- decision: `buy / sell / hold / observe / no_action / reopen`
- target_symbol、target_weight、price_range、urgency。
- decision_rationale、analyst_view_comparison、consensus_action_summary。
- optimizer_comparison、deviation_reason。
- risk_handoff_notes、conditions、invalidation_triggers、monitoring_points。
- evidence_refs、reopen_target_if_any。

偏离计算由 Decision Service 执行，结果写入 `DecisionGuardResult`：

- 单股偏离：`abs(CIO目标权重 - 优化器建议权重)`。
- 组合主动偏离：`0.5 * sum(abs(CIO目标权重 - 优化器建议权重))`。
- 单股偏离 `>= 5pp` 或组合主动偏离 `>= 20%` 时，由编排中心生成 Owner 例外审批或 Reopen Event，CIO 不自行裁决。

## 7. Risk 与 Owner 例外

Risk Review 三状态：

- `approved`：通知 Owner 后可进入纸面执行。
- `conditional_pass`：生成 Owner 例外审批。
- `rejected`：当前 attempt 硬阻断。

Risk Review Report 必须包含：

- review_result、repairability、risk_summary。
- hard_blockers、conditional_requirements。
- data_quality_assessment、portfolio_risk_assessment、liquidity_execution_assessment。
- cio_deviation_assessment、hard_dissent_assessment。
- owner_exception_required、reopen_target_if_any、reason_codes、evidence_refs。

`rejected` 必须由 Risk Officer 判定 `repairable / unrepairable`：

- repairable：通过 Reopen Event 回到指定阶段。
- unrepairable：关闭当前 attempt。
- 不进入 Owner 例外审批，Owner 不能覆盖。

Owner exception packet 使用 `ApprovalRecord`，必须含对比方案、影响范围、替代方案、建议、生效边界和超时策略。

## 8. 纸面账户与执行

账户初始化：

- initial_cash: `1,000,000 CNY`
- positions: empty
- cash_ratio: 100%
- baseline_returns、drawdown、risk_budget_baseline 初始化。

Paper Order：

```yaml
paper_order_id: string
workflow_id: string
decision_memo_ref: string
symbol: string
side: buy | sell
target_quantity_or_weight: number
price_range: object
urgency: urgent | normal | low
execution_core_snapshot_ref: string
status: pending | released | filled | partial | unfilled | expired | blocked
```

执行规则：

- urgent：30 分钟窗口。
- normal：2 小时窗口。
- low：全日窗口。
- 优先 1 分钟 VWAP；缺失时 TWAP。
- 价格区间未命中则 unfilled/expired。
- 记录佣金、印花税、过户费、滑点和 T+1。
- execution_core 不达标严格阻断；缓存不可用于新成交价格。

模拟算法：

1. 以订单释放后的下一个 A 股交易日为默认执行日；urgent 从开盘后或释放后最近可交易分钟起取 30 分钟，normal 取 2 小时，low 取当日剩余连续交易窗口。
2. `execution_core` 必须提供分钟 bar：`minute_ts`、`open/high/low/close`、`volume`、交易日历、停复牌/可交易状态、涨跌停或不可成交标记、费用税费参数。分钟 bar 不满足 freshness 或 quality threshold 时订单 `blocked`，不使用日线或缓存价格伪造成交。
3. 有 volume 时使用 1 分钟 VWAP：`sum(typical_price * volume) / sum(volume)`，`typical_price = (high + low + close) / 3`。窗口内有效 volume 总和为 0 时 fallback 到 TWAP。
4. TWAP 使用窗口内有效分钟 `typical_price` 算术均值；若无有效分钟价格，订单 `unfilled` 或 `expired`。
5. 买入价格区间命中条件：窗口内存在 `low <= max_price` 且 simulated_price <= max_price；卖出命中条件：窗口内存在 `high >= min_price` 且 simulated_price >= min_price。未命中则 `unfilled`；窗口结束且订单不再有效则 `expired`。
6. 滑点使用 deterministic bps policy，不随机：urgent 8 bps、normal 5 bps、low 3 bps；若当日分钟振幅 `(max(high)-min(low))/start_price > 3%`，额外加 2 bps。买入加滑点，卖出减滑点。
7. V1 默认费用参数作为纸面模拟配置：佣金 2.5 bps，最低 5 CNY；印花税卖出 10 bps、买入 0；过户费双边 0.1 bps。参数变更属于高影响治理，只影响新任务/新 attempt。
8. 成交量 V1 不模拟盘口撮合；目标数量/权重按 simulated_price 和现金/持仓约束计算，现金或持仓不足则 partial 或 blocked，并写 reason code。
9. A 股 T+1：买入生成持仓但当日不可卖，卖出资金按纸面账户规则入账并记录 `t_plus_one_state`；T+1 只影响持仓可用性，不接真实券商。

V1 不模拟复杂撮合、撤单博弈或真实券商通道。

## 9. 持仓监控与处置

触发源：

- A 股持仓异常波动。
- 重大公告。
- 风险阈值。
- 执行失败。
- 止损/暂停建议。

输出：

- PositionDisposalTask，priority 可升级为 P0。
- 进入正式处置仍需 S5 Risk、审计和 execution_core guard。
- 紧急不等于跳过风控；Risk rejected 仍硬阻断。

## 10. 验证映射

- `topic_registration_report.json`：开放来源、supporting evidence 不直入正式 IC。
- `topic_queue_report.json`：硬门槛、四维评分、并发 3/5、P0 抢占。
- `ic_context_package_report.json`：Context Package 和 Chair Brief 字段。
- `analyst_memo_report.json`：四 Memo schema、role payload、独立性。
- `consensus_action_report.json`：公式和阈值。
- `debate_dissent_report.json`：S3 路径、hard dissent、低共识阻断。
- `cio_optimizer_report.json`：Decision Packet、偏离、CIO 禁止动作。
- `risk_owner_exception_report.json`：Risk 三状态、Owner 例外、超时、reopen。
- `paper_account_report.json`、`paper_execution_report.json`、`position_disposal_report.json`：纸面账户、执行和持仓处置。

## 11. R8 投资主链场景剧本

本附件的实现标准不是“存在 TopicQueue、Memo、Debate、Risk、Execution 对象”，而是每个关键 fixture 能按 S0-S7 跑出可审计的 Agent/Service/Artifact/View/Verification 链。

### 11.1 S0-S7 责任矩阵

| 阶段 | Workflow/Service 动作 | Agent 动作 | 必需 artifact | 失败/阻断 |
|---|---|---|---|---|
| S0 请求受理 | Request Brief 标准化、TaskEnvelope、候选机会注册 | Owner/Researcher/Analyst/服务信号提供触发语义 | RequestBrief、TopicProposal | scope/asset/auth 不清则 draft/waiting |
| S1 数据就绪 | DataRequest、source routing、DataReadiness、MarketState、服务预计算 | CIO 读取 S1 输出生成 Chair Brief | DataReadinessReport、ICContextPackage、ICChairBrief | decision_core blocked 阻断；execution_core 只记录 S6 blocker |
| S2 分析研判 | 准入四 Analyst AgentRun，注入 role ContextSlice | 四 Analyst 产出独立 Memo，不互相覆盖 | AnalystMemo x4 | memo schema fail、证据不足、角色越权重开 S2 |
| S3 辩论收敛 | Debate Manager 控制 session、轮次、超时、重算 | CIO agenda/synthesis；Analyst view_update/comment/evidence request | DebateSummary 或 debate_skipped | low consensus/action blocked；retained hard dissent -> S5 重点评估 |
| S4 CIO 收口 | DecisionPacket、优化器偏离计算 | CIO 产出 DecisionMemo，解释行动/不行动与偏离 | CIODecisionMemo | 重大偏离触发 Owner exception 或 reopen |
| S5 风控复核 | Risk Engine 输入装配、stage guard | Risk Officer 三状态复核、repairability 判断 | RiskReviewReport | rejected 硬阻断；conditional_pass -> Owner approval |
| S6 授权执行 | Owner 例外、execution_core guard、Paper Execution | Owner 只审批例外；Trade Execution Service 纸面执行 | ApprovalRecord、PaperExecutionReceipt | owner_timeout 不执行；execution_core blocked 不执行 |
| S7 归因反思 | Performance Attribution、Reflection trigger | CFO/责任 Agent/Researcher 解释与晋升 | AttributionReport、ReflectionRecord | 不改历史链，只追加学习/治理 |

### 11.2 Happy Path 买入剧本

fixture：`FX-HAPPY-PATH-BUY-A-SHARE`

1. Owner 在全局命令输入 A 股研究请求，Request Distribution Center 生成 RequestBrief preview。
2. Owner confirmation 后，Workflow 创建 investment_workflow TaskEnvelope 和 TopicProposal。
3. Topic Queue 通过硬门槛和四维评分，进入 active IC slot。
4. S1 创建 DataRequest；Data Service 生成 `decision_core_status=pass`，`execution_core_status=pass` 或记录 future blocker。
5. IC Context Builder 装配 shared context、service results、portfolio/risk、ResearchPackage 和 role attachments。
6. CIO AgentRun 生成 ICChairBrief，只定义问题、边界、关键矛盾和行动标准，不预设结论。
7. S2 创建四 Analyst AgentRun；Macro/Fundamental/Quant/Event 输出独立 Memo 和 role_payload。
8. Consensus Service 计算 consensus/action_conviction；高共识、行动强度达标、无 hard dissent 时生成 debate_skipped。
9. S4 CIO 读取 DecisionPacket，形成 buy/hold/observe/no_action 决策；若买入则给出 target_weight、price_range、urgency。
10. S5 Risk Officer 输出 approved。
11. S6 Trade Execution Service 根据 execution_core 生成 PaperExecutionReceipt。
12. S7 Attribution Service 自动归因；如无异常，自动发布，不触发 CFO。

view：

- Owner View 显示任务进度、数据可信、谁支持/反对、Risk approved、纸面执行结果。
- Dossier 显示 S0-S7、Memo matrix、debate_skipped、CIO/Risk/Execution/Attribution。
- Trace 显示 AgentRun、Gateway writes、service calls。

### 11.3 Hard Dissent 剧本

fixture：`FX-HIGH-CONSENSUS-HARD-DISSENT`、`FX-MEDIUM-CONSENSUS-HARD-DISSENT`

1. S2 Memo x4 accepted 后，Consensus Service 发现 high/medium consensus 且 hard dissent。
2. Debate Manager 打开 S3 CollaborationSession。
3. CIO 生成 agenda，必须聚焦 hard dissent 的证据、反证、适用条件和失效条件。
4. 四 Analyst 在最多两轮内提交 view_update/comment/request_evidence；不得覆盖原 Memo。
5. 新证据必须经 Researcher/Data Service accepted 后进入 evidence artifact。
6. Debate Manager 重算 consensus/action_conviction。
7. 若 retained hard dissent，DebateSummary 写 `risk_review_required=true`。
8. S4 可形成语义结论，但 S5 RiskReviewReport 必须显式评估 hard_dissent_assessment。
9. 若 Risk rejected，当前 attempt 硬阻断；Owner 无覆盖按钮。

### 11.4 低共识/低行动强度剧本

fixture：`FX-LOW-CONSENSUS-NO-EXECUTION`

- `consensus < 0.7`：不为执行目的进入无界辩论；输出 low_consensus_no_execution，建议 observe、补证或 reopen。
- `action_conviction < 0.65`：即使 consensus 高，也不得生成 paper order；S4 只能 `observe / no_action / reopen`。
- Dossier 必须展示不行动原因和需要补证的问题；前端不得显示继续成交入口。

### 11.5 Risk Rejected 剧本

fixture：`FX-RISK-REJECTED-REOPEN`、`FX-RISK-REJECTED-UNREPAIRABLE`

1. Risk Officer 输出 `review_result=rejected`。
2. RiskReviewReport 必须包含 `repairability`。
3. repairable：Risk 只能附 `reopen_target` 和 reason_code；Workflow 写 ReopenEvent，旧 artifact superseded。
4. unrepairable：当前 attempt 关闭，不进入 Owner approval。
5. Owner、CIO、前端、API 都不能覆盖 rejected。
6. Trace/Debug 显示 rejected -> reopen/close 决策链。

### 11.6 Execution Core Blocked 剧本

fixture：`FX-EXECUTION-CORE-INVALID`

- S1 或 S6 发现分钟线、交易日历、停复牌、费用参数、freshness 任一低于阈值时，`execution_core_status=blocked`。
- Risk approved 或 Owner approval 都不能绕过 execution_core。
- PaperOrder 状态为 blocked，不生成成交价格。
- 前端显示 Data Readiness 缺口，不显示继续成交入口。

### 11.7 P0 持仓风险剧本

fixture：持仓重大公告或异常波动。

1. Position Monitor 注册 holding_risk TopicProposal，默认可 P0。
2. P0 可抢占最低 P1/P2 active slot，但不得跳过 S1-S7。
3. Event Analyst 验证公告来源，Quant 检查量价和执行风险，Fundamental 评估盈利假设变化，Macro 只在宏观/行业相关时输出。
4. CIO 做处置语义收口；Risk 必须复核；execution_core pass 后才可纸面执行。

### 11.8 Verification

投资链相关 report 必须证明 runbook，而不是仅证明字段：

- `topic_queue_report.json`：硬门槛、评分、P0 抢占和 preserved artifacts。
- `ic_context_package_report.json`：Chair Brief 未预设结论，role attachments 限默认注入而非读隔离。
- `analyst_memo_report.json`：四 Analyst role_payload、证据引用和禁止越权。
- `debate_dissent_report.json`：Command、round、view_update、handoff、重算和 Risk handoff。
- `risk_owner_exception_report.json`：rejected 无 Owner override，conditional_pass 才进入 approval。
- `paper_execution_report.json`：execution_core guard、VWAP/TWAP、费用、滑点、T+1 和 blocked/unfilled/expired。
