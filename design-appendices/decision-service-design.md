# Decision Service Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 CIO Decision Packet、偏离守卫、Owner 例外候选和重开建议的实现契约。
- 实现 `src/velentrade/domain/decision/**` 或 `src/velentrade/domain/investment/{risk,owner_exception}/**` 中 S4 决策服务、组合优化偏离、CIO/Risk/Owner 交接、相关 read model 或 `TC-ACC-018/019` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`spec-appendices/investment-ic-risk-execution.md`、`design-appendices/workflow-data-service-design.md`、`contracts/domain-artifact-schemas.md` 和 `contracts/api-read-models.md`，不新增正式需求。
- 若本文与 `investment-chain-design.md` 或 frozen contract 冲突，以本文的服务边界和 contract 为准回写相关文档，不得让 CIO、Risk、Owner 或服务互相越权。

## 1. 职责边界

Decision Service 是确定性服务，不是新 Agent。

| 负责 | 不负责 |
|---|---|
| 装配 CIO Decision Packet | 替 CIO 写投资语义结论 |
| 校验 S4 输入完整性、版本、ContextSnapshot 和数据质量门 | 直接推进 workflow stage |
| 计算 CIO 目标与组合优化建议的单股偏离、组合主动偏离 | 直接审批重大偏离 |
| 生成 Decision Guard Result | 覆盖 Risk rejected 或降低风控门槛 |
| 生成 Owner 例外候选或重开建议 | 向 Trade Execution Service 下单 |
| 投影 Dossier 中的决策服务卡片和 trace | 将 runner transcript 作为事实源 |

服务输出只能作为 artifact/service_result 和 workflow guard 输入。Workflow Scheduling Center 仍是过程权威；CIO 仍是语义收口者；Risk Officer 仍是风控复核主体；Owner 只审批允许进入审批中心的例外。

## 2. 输入与输出

### 输入

- TaskEnvelope、workflow stage、attempt_no、ContextSnapshot。
- IC Context Package、IC Chair Brief。
- 四份 Analyst Memo。
- Debate Summary 或 `debate_skipped` record。
- consensus_score、action_conviction、hard_dissent 状态。
- Data Readiness Report、Market State、Valuation、Factor、Portfolio Optimization result。
- 当前纸面账户、持仓、现金、风险预算、执行约束。
- 既有 Approval/Risk/Reopen/Incident 事件摘要。

### 输出

| 输出 | 类型 | 用途 |
|---|---|---|
| `DecisionPacket` | supporting artifact | CIO 在 S4 消费的唯一正式决策包 |
| `DecisionGuardResult` | service_result/artifact | S4 guard、Dossier 卡片和验证报告使用 |
| `DecisionExceptionCandidate` | supporting artifact | 重大偏离或条件风险进入 Owner 审批前的候选材料 |
| `ReopenRecommendation` | supporting artifact/event input | 建议 Workflow 创建 Reopen Event，不自行重开 |

`DecisionPacket` 至少包含：决策问题、共享事实摘要、四 Analyst stance、共识与行动强度、保留分歧、数据质量、市场状态、估值区间、组合优化建议、CIO 可选行动菜单、风险约束、执行可行性、历史反思命中、证据引用和不可越权提示。

## 3. S4 运行手册

```text
S3 completed or skipped
 -> Workflow Scheduling Center calls Decision Service
 -> validate required inputs and ContextSnapshot
 -> assemble DecisionPacket
 -> compute deviation candidates from optimizer baseline
 -> emit DecisionGuardResult
 -> Workflow admits CIO AgentRun with DecisionPacket
 -> CIO submits CIODecisionMemo via Authority Gateway
 -> Decision Service validates memo references and recomputes deviation
 -> if no major deviation: handoff to Risk Review
 -> if major deviation: create DecisionExceptionCandidate or ReopenRecommendation
 -> Workflow routes to Owner exception, Risk handoff, or Reopen Event by guard
 -> project Dossier and Trace read models
```

### 3.1 Packet 装配

- 服务读取冻结的 ContextSnapshot，不读取可变配置。
- 所有输入必须来自 artifact ledger、service_result、workflow state 或 event log。
- Analyst stance 必须保留四位 Analyst 的独立字段，不能只留平均分。
- hard dissent、low consensus、low action_conviction 必须被显式标记到 guard result。
- 数据质量 degraded/blocker 必须带 source_refs、reason_code 和 execution_core status。

### 3.2 CIO Memo 校验

CIO 提交 `CIODecisionMemo` 后，Decision Service 校验：

- memo 引用的 DecisionPacket 与当前 attempt/context_snapshot 一致。
- action 属于 `buy / sell / hold / observe / no_action / reopen / reduce / increase` 等契约允许集合。
- 目标权重、价格区间、执行窗口和条件不违反纸面账户、风险预算和执行核心数据门。
- 偏离优化器建议时必须提供语义原因。
- memo 没有审批例外、覆盖 Risk rejected、直接下单或改状态字段。

### 3.3 偏离守卫

- 单股偏离：`abs(cio_target_weight - optimizer_target_weight)`。
- 组合主动偏离：`0.5 * Σ abs(cio_target_weight_i - optimizer_target_weight_i)`。
- 任一单股偏离 `>= 5pp` 或组合主动偏离 `>= 20%` 时，`DecisionGuardResult.major_deviation=true`。
- 重大偏离必须生成 `DecisionExceptionCandidate` 或 `ReopenRecommendation`，由 workflow 根据 reason code 决定进入 Owner 例外或重开论证。
- CIO 小偏离可继续进入 Risk Review，但 memo 必须留偏离说明。

## 4. 失败路径

| 场景 | 服务处理 | Workflow 结果 |
|---|---|---|
| 缺少四份 Analyst Memo | `missing_required_artifact` | S4 blocked，返回 S2/S3 补齐 |
| Debate Summary 缺失且 S3 不可跳过 | `invalid_debate_state` | S4 blocked |
| Data Readiness stale/degraded | `data_quality_guard` | degraded 进入 Risk 条件路径；blocked 重开 S1 |
| action_conviction 低于阈值 | `low_action_conviction` | 不生成执行授权，CIO 只能 observe/no_action/reopen |
| retained hard dissent | `retained_hard_dissent` | 必须进入 Risk Review |
| 组合优化不可用 | `optimizer_unavailable` | CIO 可形成 no_action/reopen/observe；不能无基准生成重大执行授权 |
| CIO memo schema fail | `memo_schema_invalid` | S4 waiting 或 failed，按 retry policy |
| CIO 重大偏离缺说明 | `missing_deviation_rationale` | S4 blocked |
| 服务超时 | `decision_service_timeout` | incident/degraded，不伪造 packet |

所有失败都必须写 audit_event、trace_id、reason_code 和可恢复建议；不得生成半完整 DecisionPacket。

## 5. 视图投影

### Investment Dossier

Decision Service 在 Dossier 中投影为“决策服务卡片”：

- 输入完整性：IC Context、Chair Brief、四 Memo、Debate、Optimizer、Data Readiness。
- 共识与行动强度：数值、阈值、是否允许行动。
- 优化器基准 vs CIO 目标：单股偏离、组合主动偏离、重大偏离标记。
- 例外路径：Owner exception candidate、Risk handoff、Reopen recommendation。
- 不可越权提示：CIO 不能下单、审批、覆盖 Risk rejected。

### Trace/Debug

Trace/Debug 显示：

- service_call_id、input_artifact_refs、context_snapshot_id。
- guard_result、reason_codes、schema validation。
- DecisionPacket hash、CIODecisionMemo validation、exception/reopen artifact refs。
- latency、retry、timeout、idempotency key。

## 6. Verification

- `decision_service_report.json`：验证 DecisionPacket 装配、输入完整性、失败路径、guard reason code 和服务无越权。
- `cio_optimizer_report.json`：验证 CIO 消费 packet、偏离公式、重大偏离例外/重开和 CIO 禁止动作。
- `risk_owner_exception_report.json`：验证重大偏离、conditional_pass、Risk rejected 与 Owner 审批边界。
- `web_command_routing_report.json`：验证 Dossier 决策服务卡片和 Trace/Debug service call 可见。
