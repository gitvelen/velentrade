# Investment IC Risk Execution

## 0. AI 阅读契约

- 本附件是 `spec.md` 中投资链路细节的强证据展开层，不定义新的正式需求、验收或验证义务。
- 任务涉及 A 股 IC、机会注册、硬门槛、IC Chair Brief、Memo、共识/辩论、CIO、风控、Owner 例外或纸面执行时，必须读取本附件。
- 若本附件与 `spec.md` 冲突，必须停止并回到 Requirement 修补冲突。
- 正式投资闭环仅覆盖 A 股普通股；所有真实资金动作由人负责。

## 1. 机会到正式 IC

机会来源包括：

- Owner 自由对话或页面操作。
- 四位分析师在工作中发现。
- Investment Researcher 简报、资料包或检索发现。
- 持仓异常波动、重大公告、风险阈值。
- 服务层信号，例如因子、估值、市场状态或风险提示。

机会注册不等于正式 IC。新闻、舆情、资金流等 supporting evidence 只能触发候选机会、研究任务或资料包；必须补齐 decision_core 后才能进入正式 IC。

进入正式 IC 前必须完成：

- A 股普通股范围检查。
- Request Brief 完整性检查。
- decision_core 数据可用性检查。
- 研究资料非空。
- 合规/执行禁区检查。
- 同主题去重。
- 正式 IC 并发槽检查。
- 四维优先级评分。
- P0 抢占记录。

P0 默认只来自持仓、风险或 Owner 显式紧急硬触发；非持仓正面机会不默认 P0。

## 2. 四维评分

四维均为 0-5：

- 机会强度。
- 数据/资料完备度。
- 风险紧急度。
- 组合/持仓相关性。

评分用于排序和并发，不直接代替 IC 结论。

## 3. IC Context Package 与 CIO Chair Brief

正式 IC 启动后先生成 IC Context Package，再由 CIO 输出 IC Chair Brief。

IC Context Package 应包含：

- Request Brief。
- Data Readiness Report。
- Market State。
- 服务计算结果。
- 组合上下文。
- 风险约束。
- 研究员资料包。
- 历史反思和经验命中。
- 四类角色附件。
- 当前 ContextSnapshot 引用。

角色附件应限制在角色所需领域，避免上下文污染。由于 V1 采用组织透明读，限制的是默认注入和任务聚焦，不是业务资料可读性。

IC Chair Brief 由 CIO 生产，最小字段：

- `decision_question`
- `scope_boundary`
- `key_tensions`
- `must_answer_questions`
- `time_budget`
- `action_standard`
- `risk_constraints_to_respect`
- `forbidden_assumptions`
- `no_preset_decision_attestation`

Chair Brief 只能定义议题焦点、关键矛盾和行动判定口径，不得预设买入、卖出、持有、目标仓位或任何分析师应得出的结论。

## 4. Analyst Memo 与共识

四位分析师是四套独立岗位能力，不是一个通用模板换 role 参数。

Analyst Memo 使用统一外壳：

- `memo_id`
- `workflow_id`
- `attempt_no`
- `analyst_id`
- `role`
- `context_snapshot_id`
- `decision_question`
- `direction_score(-5..+5)`
- `confidence(0..1)`
- `evidence_quality(0..1)`
- `hard_dissent`
- `hard_dissent_reason`
- `thesis`
- `supporting_evidence_refs`
- `counter_evidence_refs`
- `key_risks`
- `applicable_conditions`
- `invalidation_conditions`
- `suggested_action_implication`
- `data_quality_notes`
- `needs_reopen_or_escalation`
- `collaboration_command_refs`
- `role_payload`

`suggested_action_implication` 只表示该视角对 IC 的行动含义，不是最终交易指令。

role_payload 概要：

- Macro：市场状态、政策传导、流动性、信用周期、行业/风格、宏观顺风/逆风、传导路径和宏观风险触发器。
- Fundamental：商业模式、护城河、财务质量、盈利情景、估值方法、公允价值区间、安全边际、敏感性、会计红旗和关键 KPI。
- Quant：信号假设、趋势状态、量价确认、因子暴露、样本上下文、信号稳定性、regime fit、择时含义和过热/拥挤风险。
- Event：事件类型、时间线、来源可靠性、验证状态、催化强度、时间窗口、基本面假设影响、情绪/资金流、历史类比和反转风险。

Event 的 `rumor_only` 或 `supporting_evidence_only` 不得作为 decision_core 单独推进。

共识度和行动强度按 `spec.md` 正文公式执行。高共识不等于可跳过风控；低共识或行动强度不足不允许纸面执行。

hard dissent 按正文业务契约判定；高共识但存在 hard dissent 时不得跳过 S3，必须先完成有界辩论；中等共识辩论后仍保留 hard dissent 时同样触发 Risk Review，但不允许绕过低共识、低行动强度或风控硬阻断。

## 5. 辩论流程

S3 采用双层模型：

- Workflow/Debate Manager 是过程权威，负责派发、轮次、超时、状态、公式重算、schema 校验和审计。
- CIO 是语义主席，负责 agenda、追问、关键矛盾梳理、补证要求和 synthesis。

合法路径：

- 高共识、行动强度达标且无 hard dissent：生成 `debate_skipped`。
- 高共识但行动强度不足：不生成执行授权；可直接进入 S4 形成 `observe / no_action / reopen`，或按 CIO agenda 请求补证。
- 高共识但存在 hard dissent：不得生成 `debate_skipped`，先执行最多 2 轮有界辩论；若 hard dissent 仍保留，则进入 Risk Review。
- 中等共识：最多 2 轮有界辩论；若 hard dissent 仍保留，则进入 Risk Review。
- 每轮只能引用 IC Context Package、IC Chair Brief、既有 Memo 或补充 evidence_refs。
- 辩论后重算 consensus_score 和 action_conviction。
- 重算后仍低共识或行动强度不足时，不允许进入纸面执行。

共识/行动强度组合矩阵：

| consensus_score | hard dissent | action_conviction | S3 处理 | 后续授权 |
|---|---|---|---|---|
| `>=0.8` | 无 | `>=0.65` | 跳过，生成 `debate_skipped` | 可进入 S4；仍需 S5/S6 guard。 |
| `>=0.8` | 无 | `<0.65` | 可跳过或按 CIO 补证请求进入 S3 | 不得执行；S4 只能 `observe / no_action / reopen`。 |
| `>=0.8` | 有 | 任意 | 最多 2 轮有界辩论 | 保留 hard dissent 则 Risk Review；行动强度不足仍不得执行。 |
| `0.7 <= score <0.8` | 任意 | 任意 | 最多 2 轮有界辩论 | 保留 hard dissent 则 Risk Review；行动强度不足不得执行。 |
| `<0.7` | 任意 | 任意 | 不为执行目的辩论 | 阻断纸面执行，输出补证/观察/reopen reason。 |

Debate Summary 是联合产物。过程字段由 Debate Manager 生成，CIO 语义字段由 CIO 署名生成。

过程字段至少包含：

- `rounds_used`
- `participants`
- `issues`
- `new_evidence_refs`
- `view_changes`
- `retained_dissent`
- `hard_dissent_present`
- `retained_hard_dissent`
- `risk_review_required`
- `recomputed_consensus_score`
- `recomputed_action_conviction`
- `stop_reason`
- `next_stage_decision`

CIO 语义字段至少包含：

- `agenda`
- `questions_asked`
- `synthesis`
- `resolved_issues`
- `unresolved_dissent`
- `chair_recommendation_for_next_stage`
- `semantic_lead_signature`

停止原因：

- `skipped_high_consensus`
- `max_rounds_reached`
- `no_new_evidence`
- `converged`
- `retained_hard_dissent`
- `hard_dissent_risk_handoff`
- `low_consensus_blocked`
- `low_action_conviction_blocked`

CIO 在 S3 可发起 `ask_question`、`request_view_update`、`request_evidence`、`request_agent_run`，但这些请求仍需经 CollaborationCommand 准入。CIO 不能直接增加轮次上限、直接推进 workflow 状态或绕过公式和风控。

## 6. CIO 与组合优化器

CIO 是投资判断与组合行动的语义收口者，不是服务操作员、路由器、风控官、审批人或执行服务。

组合优化器负责：

- 在硬约束内生成目标权重。
- 给出现金、集中度、换手率、风险预算影响。
- 计算与 CIO 目标组合的单股偏离和组合主动偏离。

CIO 负责：

- S1 后输出 IC Chair Brief。
- S3 必要时担任语义主席。
- 消费 Decision Packet。
- 比较四位分析师观点与服务建议。
- 说明为什么现在行动或不行动。
- 判断是否偏离优化器。
- 给出可执行或不可执行的 CIO Decision Memo。

CIO 不能：

- 绕过 Risk Officer。
- 直接下单。
- 直接创建 AgentRun。
- 直接调服务替代编排。
- 修改 workflow state。
- 审批例外。
- 覆盖 Risk rejected。
- 把非 A 股资产纳入投资执行链。
- 把低共识包装成“谨慎买入”。

CIO Decision Memo 最小字段：

- `decision`: `buy / sell / hold / observe / no_action / reopen`
- `target_symbol`
- `target_weight`
- `price_range`
- `urgency`
- `decision_rationale`
- `analyst_view_comparison`
- `consensus_action_summary`
- `optimizer_comparison`
- `deviation_reason`
- `risk_handoff_notes`
- `conditions`
- `invalidation_triggers`
- `monitoring_points`
- `evidence_refs`
- `reopen_target_if_any`

组合主动偏离按 `0.5 * sum(abs(CIO目标权重 - 优化器建议权重))` 计算；超过阈值时由编排中心生成 Owner 例外审批或 Reopen Event，CIO 不自行裁决。

## 7. 风控与 Owner 例外

Risk Review 只有三类结果：

- `approved`: 可进入纸面执行或 Owner 通知。
- `conditional_pass`: 需 Owner 例外审批。
- `rejected`: 当前 attempt 硬阻断。

Risk rejected 语义：

- 阻断当前 attempt，不能执行。
- CIO 和 Owner 都不能覆盖。
- Risk Officer 必须判定 `repairable / unrepairable`。
- 若可修复，Risk 可附 `reopen_target` 和 reason code，通过 Reopen Event 回上游重做。
- 若不可修复，当前 attempt 终止，不进入 Owner 例外审批。
- Risk rejected 不等于允许原路径继续推进。

Risk Review Report 至少包含：

- `review_result`
- `repairability`
- `risk_summary`
- `hard_blockers`
- `conditional_requirements`
- `data_quality_assessment`
- `portfolio_risk_assessment`
- `liquidity_execution_assessment`
- `cio_deviation_assessment`
- `hard_dissent_assessment`
- `owner_exception_required`
- `reopen_target_if_any`
- `reason_codes`
- `evidence_refs`

Owner 审批必须少而精。审批包必须包含：

- 审批对象。
- 触发原因。
- 推荐结论。
- 对比方案。
- 风险和影响范围。
- 证据引用。
- 生效边界。
- 超时默认。
- 回滚方式。

投资链路中，Risk `conditional_pass` 和 CIO 重大偏离可进入 Owner 例外审批；Risk `approved` 的正常 IC 结论只通知 Owner；Risk `rejected` 不进入 Owner 例外审批。

审批结果：

- `approved`
- `rejected`
- `request_changes`
- `expired`

所有超时默认不执行/不生效，并记录 `owner_timeout`；Risk `conditional_pass` 或 S6 投资例外超时使 S6 blocked，CIO 重大偏离审批超时重开 S4 或关闭，高影响治理类超时为 `expired`。

## 8. 纸面执行

纸面执行必须记录：

- 决策意图。
- 目标价格区间。
- 执行窗口。
- 使用 VWAP 或 TWAP 的依据。
- 成交、未成交或过期。
- 费用、税费、滑点。
- T+1 状态。
- 可归因引用。

execution_core 规则：

- 执行价格、VWAP/TWAP 所需行情、交易日历、停复牌状态和费用税费参数必须满足当前 workflow 配置快照中的生效质量阈值，默认 `0.9`。
- execution_core 未达标时严格阻断纸面执行；Owner 不能例外批准用降级执行数据成交。
- 缓存不可用于生成新的纸面成交价格。
- 执行数据失效可导致订单未成交、过期、S6 blocked 或 Reopen Event。

V1 不模拟复杂撮合、撤单博弈或真实券商通道。

## 9. 持仓监控与处置

持仓监控覆盖：

- A 股持仓异常波动。
- 重大公告。
- 风险阈值。
- 执行失败。
- 止损/暂停建议。

紧急任务可提高优先级和触发 P0 抢占，但不得取消 S5 风控、审计、Risk rejected 硬阻断或 execution_core 阈值。
