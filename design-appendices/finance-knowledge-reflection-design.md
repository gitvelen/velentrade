# Finance Knowledge Reflection Design

## 0. AI 阅读契约

- 本附件是 Design 阶段财务、自动归因、CFO 治理、研究员、知识/Prompt/Skill 提案和反思闭环的实现契约。
- 实现 `src/velentrade/domain/finance/**`、`src/velentrade/domain/attribution/**`、`src/velentrade/domain/knowledge/**` 或 `TC-ACC-023` 到 `TC-ACC-028` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`spec-appendices/finance-knowledge-reflection.md`、`contracts/domain-artifact-schemas.md`，不新增正式需求。

## 1. 财务模块

`FinanceProfile` 是财务事实聚合，不是交易授权。覆盖：

- 现金、A 股纸面账户、基金、黄金、房产、其他资产。
- 收入、支出、负债、税务提醒、重大支出计划。
- 流动性、杠杆、压力测试、风险预算、未来现金需求。
- A 股纸面账户收益、回撤、成本、滑点、现金使用率。

资产边界：

| 资产 | 数据来源 | 可进入正式投资链 | 可生成 |
|---|---|---:|---|
| A 股普通股 | Data Service + Paper Account | 是 | IC、Risk、Paper Execution |
| 基金 | 自动行情或手工 | 否 | finance planning、risk提示、manual_todo |
| 黄金 | 自动行情或手工 | 否 | finance planning、risk提示、manual_todo |
| 房产 | Owner 手工或定期估值 | 否 | valuation reminder、manual_todo |
| 其他资产 | Owner 手工 | 否 | planning、manual_todo |

财务敏感原始字段只向 CFO 和财务服务明文开放；其他 Agent 只读脱敏约束摘要。

## 2. 财务写入与 manual_todo

Owner 更新财务资料通过 `/api/finance/assets` 或 Request Brief。写入结果：

- 更新 FinanceProfile 受控字段。
- 写 sensitive field access audit。
- 生成派生摘要 artifact。
- 若资料缺失或过期，生成 `manual_todo`，不生成审批。

房产估值到期、税务提醒、重大支出资料缺失使用 `manual_todo`；manual_todo 超时只 `expired`，不触发审批或执行。

## 3. 自动归因服务

Performance Attribution & Evaluation Service 是自动计算服务。

输入：

- PaperExecutionReceipt、持仓、现金、费用、滑点。
- Market State、Factor result、Risk budget、Portfolio Optimization。
- Analyst Memo、Debate Summary、CIO Decision Memo、Risk Review、Approval Record。
- Data Readiness、Incident summary。

输出 `AttributionReport`：

- market_result
- decision_quality
- execution_quality
- risk_quality
- data_quality
- evidence_quality
- condition_hit
- improvement_items

### 3.1 归因评分算法

所有质量评分均为 `0..1`，保留 3 位小数；输入缺失但该维度不可判定时，该维度输出 `null` 并在 `improvement_items` 写 `missing_input:<artifact_type>`，不得用收益结果倒推 Agent 质量。任一维度 `null` 时，异常判定仍可由其他维度、硬阻断或周期窗口触发。

| 维度 | 输入 | 公式 / 判定 |
|---|---|---|
| `decision_quality` | CIO Decision Memo、Analyst Memo、Debate Summary、后续 market_result | `0.35 * thesis_outcome_fit + 0.25 * decision_rationale_completeness + 0.20 * dissent_handling + 0.20 * invalidation_condition_quality` |
| `execution_quality` | PaperExecutionReceipt、PaperOrder、execution_core snapshot | `0.35 * fill_policy_fit + 0.25 * slippage_score + 0.20 * fee_tax_correctness + 0.20 * execution_core_guard_compliance` |
| `risk_quality` | Risk Review、risk budget、position result、hard blockers | `0.35 * hard_constraint_compliance + 0.25 * conditional_requirement_followthrough + 0.20 * drawdown_or_exposure_control + 0.20 * hard_dissent_assessment_quality` |
| `data_quality` | DataReadiness、DataConflictReport、Incident summary | `min(decision_core_score, execution_core_effective_score_if_used)`；若只有研究/展示数据，则用 DataReadiness `quality_score` |
| `evidence_quality` | Memo evidence refs、counter evidence refs、ResearchPackage、source quality | `0.30 * source_reliability + 0.25 * evidence_ref_completeness + 0.25 * counter_evidence_coverage + 0.20 * stale_or_conflict_penalty_adjusted` |
| `condition_hit` | Memo applicable/invalidation conditions、market state、event outcome | 每个条件输出 `hit / miss / not_observable`；维度得分为 `hit_count / observable_condition_count` |

分项口径：

- `thesis_outcome_fit`: 只比较原判断中明确可观测的方向、价格区间、时间窗口和触发条件；不可观测项不计入分母。
- `decision_rationale_completeness`: CIO Memo 是否引用 Analyst view、服务建议、偏离原因、Risk handoff 和不行动理由。
- `dissent_handling`: hard dissent 是否进入 S3/S5，是否保留 unresolved dissent 和 evidence gap；忽略 hard dissent 得 0。
- `invalidation_condition_quality`: 是否在 Memo/Decision 中写明可观测失效条件，且 S7 能追踪命中。
- `fill_policy_fit`: PaperExecutionReceipt 是否按 urgency window、VWAP/TWAP、价格区间、T+1 和 partial/blocked 规则执行。
- `slippage_score`: `max(0, 1 - abs(actual_slippage_bps - policy_slippage_bps) / 20)`。
- `hard_constraint_compliance`: Risk hard blocker、execution_core blocker、non-A boundary 无绕过为 1；存在绕过尝试且被拒为 0.7；绕过成功必须 fail。
- `source_reliability`: 按 Data Source Registry 信任层级和 source conflict 结果投影；rumor/supporting evidence 单独推进 decision_core 得 0。

### 3.2 异常与 CFO 触发

正常日度归因由服务自动发布，不创建 CFO AgentRun。以下任一条件命中时，`needs_cfo_interpretation=true` 并创建 CFO 解释或反思链路：

| trigger | 条件 | 默认动作 |
|---|---|---|
| single_dimension_low | `decision_quality / execution_quality / risk_quality / data_quality / evidence_quality` 任一非空分数 `< 0.60` | CFO Interpretation |
| repeated_degradation | 同一 Agent、服务或 workflow template 连续 3 次同维度 `< 0.70` | CFO Interpretation + ReflectionAssignment |
| rolling_drop | 同维度较最近 20 次滚动中位数下降 `>= 0.25`，且样本数 `>= 8` | CFO Interpretation |
| hard_blocker_hit | Risk rejected、execution_core blocked、critical data conflict、sensitive log/security incident 影响投资链 | CFO 或 DevOps/Risk handoff，按主因分派 |
| condition_failure | 关键 applicable condition 未命中或 invalidation condition 命中 | ReflectionAssignment |
| periodic_window | weekly / monthly / quarterly 解释窗口 | CFO Interpretation；只有发现改进行动才生成治理或反思 |

周期窗口不要求异常；异常触发不等待周期窗口。若同时命中多个 trigger，优先级为 `hard_blocker_hit > single_dimension_low > rolling_drop > repeated_degradation > condition_failure > periodic_window`。

边界：

- 不生成自然语言治理判断。
- 不签发 Governance Proposal。
- 不把收益好坏直接等同为 Agent 质量高低。
- 日度归因可自动发布；异常或周期窗口触发 CFO。

## 4. CFO 治理链

CFO 调用场景：

- 自动归因异常，需要解释和责任分类。
- 周/月/季解释窗口。
- 财务规划、现金约束、重大支出或风险预算影响投资链。
- 归因或反思发现知识、Prompt、Skill、规则或预算变更候选。
- 需要分派反思任务。

CFO 产物：

`CFOInterpretation`：

```yaml
interpretation_id: string
attribution_ref: string
period: string
summary_for_owner: string
market_vs_decision_vs_execution: object
finance_context_used: string
sensitive_data_redaction_summary: string
recommended_followups: string[]
```

`GovernanceProposal` 使用 contract 字段，`proposal_type` 可为 `risk_budget / factor_weight / prompt / skill / default_context / approval_rule / execution_param / finance_planning`。

`ReflectionAssignment`：

```yaml
assignment_id: string
trigger_ref: string
responsible_agent_id: string
classification: decision_error | market_shift | unexpected_event | execution_problem | data_quality_problem | methodology_decay
questions_to_answer: string[]
due_policy: string
```

CFO 分派规则：

| 主异常 | classification | responsible_agent_id 默认优先级 | questions_to_answer 模板 |
|---|---|---|---|
| CIO 结论、仓位、偏离或不行动理由质量低 | `decision_error` | CIO；若由单一 Memo 主导，则对应 Analyst | 原判断是什么；关键证据/反证是否被正确使用；哪些失效条件被忽略；下次决策口径如何收紧 |
| 市场状态或宏观环境突变 | `market_shift` | Macro Analyst；若 Factor/Quant regime 失配则 Quant | 当时 market state 是什么；变化何时可观测；Macro override 是否应提出；哪些条件应进入默认上下文 |
| 公告、政策、舆情或突发事件 | `unexpected_event` | Event Analyst；涉及研究资料缺口时 Researcher | 事件来源何时出现；是否只是 supporting evidence；是否影响基本面假设；需要补充哪些来源 |
| 纸面执行、滑点、窗口、T+1 或 execution_core | `execution_problem` | DevOps Engineer 或 CIO；若是执行策略参数候选则 CFO 生成治理提案 | 执行规则是否被遵守；阻断是否正确；参数是否需治理；是否影响在途/新任务 |
| 数据质量、冲突、缓存或 source 问题 | `data_quality_problem` | DevOps Engineer；涉及 Analyst 使用低质数据时追加对应 Agent | 哪些字段/来源冲突；fallback 是否执行；是否应重开 S1；是否需 source routing 治理 |
| 适用条件长期失效、Prompt/Skill/知识过期 | `methodology_decay` | Researcher + 责任 Agent；CFO 保留治理签发 | 哪条方法论失效；适用场景如何拆分；是否需要知识/Prompt/Skill proposal；验证 fixture 是什么 |

若多个分类同分，CFO 必须选择一个 primary classification，并把次要分类写入 `recommended_followups`，避免一个 assignment 同时要求多个 Agent 互相推责。`questions_to_answer` 至少包含 3 个问题，且必须引用 trigger 和 source artifact。

CFO 不能覆盖 CIO、Risk 或 Owner，不能直接让 Prompt/Skill/规则/预算/执行参数生效。

## 5. 因子研究治理

新因子流程：

```text
hypothesis
 -> sample_scope + applicable_market_state
 -> independent_validation
 -> registry_entry
 -> monitoring_rule
 -> invalidation_diagnosis
```

V1 不实现 Backtrader、历史 LLM 回放或完整回测。验证可使用 fixture、独立样本说明和静态 contract，不把回测作为 P0 条件。

因子上线或权重变更若影响默认行为，按高影响治理处理。

因子治理实现细则：

| 步骤 | 必填内容 | 验证 |
|---|---|---|
| `hypothesis` | 因子名称、经济/行为解释、预期方向、适用资产范围、禁止使用场景 | schema validation；不得只有技术指标名 |
| `sample_scope` | 样本时间段、股票池、数据源、排除规则、applicable_market_state | fixture 检查样本说明完整；不要求回测收益曲线 |
| `independent_validation` | 与原提出者不同的 validator、输入快照、泄漏检查、缺失值检查、方向一致性检查 | golden fixture + boundary fixture；输出 pass/warn/fail 和证据引用 |
| `registry_entry` | factor_id、version、owner、formula_ref、input_fields、market_state_scope、risk_notes、validation_refs、monitoring_rule_ref、rollback_ref、status | registry 字段非空；状态只能 `candidate / validated / active / retired / invalidated` |
| `monitoring_rule` | 监控频率、drift 指标、coverage 下限、data quality 下限、失效阈值、通知对象 | 模拟 drift/coverage/data_quality 三类 fixture |
| `invalidation_diagnosis` | 触发指标、受影响 workflow、是否暂停默认权重、是否生成治理提案 | invalidated fixture 必须只影响新任务/新 attempt |

默认监控阈值：coverage `< 0.80`、data quality `< 0.85`、连续 5 个观察窗口方向一致性失败，或 MarketState 不在 `market_state_scope` 内仍被用于默认权重，均生成 monitoring alert。影响默认因子权重的变更永远是高影响治理。

## 6. Researcher Workflow

Investment Researcher 可产出：

- DailyBrief
- ResearchPackage
- TopicProposal
- MemoryCapture
- MemoryOrganizeSuggestion
- KnowledgePromotionProposal
- PromptUpdateProposal
- SkillUpdateProposal

Daily Brief 必须区分 P0/P1/P2；非持仓正面机会不默认 P0。

Research Package 可进入 IC Context；supporting evidence 不得绕过硬门槛直接进入正式 IC。

Researcher 的记忆整理能力借鉴 `/home/admin/memos` 的 capture/review/daily_digest/organize，但必须项目化：

| 动作 | 输入 | 输出 | 禁止 |
|---|---|---|---|
| capture | Owner 观察、研究摘录、反思草稿、外部资料摘要 | `MemoryItem` draft + `MemoryExtractionResult` | 直接生成投资结论或默认上下文 |
| review | query、tag、symbol、artifact refs | SearchSummary + evidence refs | 用召回结果覆盖正式 artifact |
| daily_digest | 时间窗口、持仓/关注列表、collection | DailyBrief + candidate memories | 把普通正面机会升为 P0 |
| organize | untagged/loose memories、relation candidates | MemoryOrganizeSuggestion | 未经 Gateway 批准直接改写旧版本 |
| promote | validated Memory/Reflection | Knowledge/Prompt/Skill proposal | 热改在途 ContextSnapshot |

Memory capture 的最小 payload 必须包含：`title`、`tags`、`source_refs`、`symbol_refs`、`artifact_refs`、`agent_refs`、`sensitivity`、`suggested_relations`。Researcher 可以提出 tag/relation/collection 建议，但应用建议仍走 Authority Gateway，且所有正文修改生成新 `MemoryVersion`。

Knowledge/Prompt/Skill Proposal 必须包含：

- diff 或 manifest。
- affected roles/workflows。
- validation result refs。
- impact level。
- rollback plan。
- effective scope: new task / new attempt。

Researcher 不能直接改共享知识、Prompt、SkillPackage、审批规则、风险预算或执行参数。

## 7. 记忆与知识状态机

```text
observation/process_archive/research_note/reflection_draft
 -> MemoryItem(draft)
 -> MemoryItem(validated_context)
 -> candidate_knowledge
 -> validated_knowledge
 -> default_context_candidate
 -> effective_default_context
```

状态含义：

| 状态 | 含义 | 可被检索 | 可进默认上下文 |
|---|---|---:|---:|
| `MemoryItem(draft)` | 快速捕获、未整理或仅有单一来源 | 是 | 否 |
| `MemoryItem(validated_context)` | 已完成 metadata extraction、relation、来源和敏感字段检查 | 是 | 否 |
| `candidate_knowledge` | 具备复用价值但尚未验证适用边界 | 是 | 否 |
| `validated_knowledge` | 经归因、反思或多次任务验证 | 是 | 仅按需 |
| `default_context_candidate` | 可能改变默认上下文、checklist、playbook 或 Prompt 背景 | 是 | 否，先做 impact triage |
| `effective_default_context` | 低/中影响自动验证或高影响 Owner 批准后生效 | 是 | 仅新任务/新 attempt |
 
Memory/Knowledge 永远不是正式业务事实源。若 Memory 与 Artifact 冲突，Artifact 优先；若 Memory 暴露潜在事实冲突，Researcher 只能生成 DataConflictReport 请求、KnowledgePromotionProposal 或反思任务。

质量维度：

- 来源可信度。
- 证据可解析性。
- 时间有效性。
- 适用场景。
- 反例和失效条件。
- 与既有知识冲突。
- 是否影响默认行为或审批门槛。

冲突：

- 事实冲突回到来源、时间戳和 Data Quality。
- 方法论冲突拆分适用场景。
- 高影响冲突由 Researcher 汇总，CFO 或相关 Agent 签发治理提案。

冲突处理流程：

| 冲突类型 | 判定者 | 处理 | 写入位置 |
|---|---|---|---|
| 事实冲突 | Data Service + Researcher | 比较 source priority、timestamp、schema、cross-source tolerance；critical conflict 回 S1/Data Quality | DataConflictReport、Knowledge item conflict refs |
| 解释冲突 | 相关 semantic lead | 保留多个解释，要求每个解释绑定 evidence_refs 和适用条件 | ReflectionRecord 或 Memo comment |
| 方法论冲突 | Researcher | 拆成不同 `applicable_market_state / asset_scope / time_window / failure_condition` 的候选知识 | KnowledgePromotionProposal |
| 记忆归类冲突 | Researcher | 保留多标签、多关系或 collection 建议，低风险可自动整理，高影响默认上下文仍走治理 | MemoryOrganizeSuggestion、MemoryRelation |
| 高影响冲突 | CFO/Risk/Owner 按类型 | 生成 GovernanceProposal 或 Owner Approval，不自动改默认上下文 | GovernanceChange / ApprovalRecord |

事实冲突未解决前，不得晋升为 `validated_knowledge`；方法论冲突未拆适用场景前，不得进入 `effective_default_context`。

## 8. 反思闭环

流程：

```text
Attribution anomaly or periodic window
 -> CFO confirms scope/responsible agent/impact
 -> responsible Agent first draft
 -> Researcher extracts reusable improvement
 -> Knowledge/Prompt/Skill/Governance Proposal
 -> auto validation for low/medium OR Owner approval for high
 -> effective only for new task/new attempt
```

责任 Agent 一稿必须回答：

- 原判断是什么。
- 当时证据和反证是什么。
- 偏差来自决策、市场、执行、数据、事件还是方法论。
- 哪些条件命中或失效。
- 改进建议是否影响 Prompt、Skill、知识或配置。

反思不得直接热改运行参数、Prompt、Skill 或在途上下文。

## 9. 验证映射

- `finance_asset_boundary_report.json`：全资产、非 A 股隔离、manual_todo。
- `performance_attribution_report.json`：自动归因维度。
- `cfo_governance_report.json`：CFO Interpretation、Governance Proposal、Reflection Assignment、高影响审批。
- `factor_research_report.json`：因子准入、独立验证、登记、监控、无回测依赖。
- `researcher_workflow_report.json`：Daily Brief、Research Package、Topic/Knowledge/Prompt/Skill Proposal。
- `reflection_learning_report.json`：反思责任链、Memory/Knowledge 晋升、新任务生效、在途不热改。

## 10. R8 财务、归因与反思 Runbook

本附件必须证明财务和学习闭环如何运行，而不是只列 FinanceProfile、AttributionReport、Proposal 名称。

### 10.1 财务档案与规划 Runbook

trigger：

- Owner 更新现金、基金、黄金、房产、收入、负债、税务或重大支出。
- 基金/黄金行情更新。
- 房产估值到期。
- 财务规划影响风险预算、现金下限或重大支出硬约束。

steps：

```text
1. Request Brief 或页面表单进入 finance_task。
2. Finance service 校验 asset_type、valuation、valuation_date、source 和 client_seen_version。
3. 原始敏感字段加密存储，只给 CFO/财务服务明文读取。
4. 生成 FinanceProfile 和脱敏 FinanceSummary artifact。
5. 资料缺失、估值过期或 Owner 线下动作生成 manual_todo，不进入审批。
6. 非 A 股资产只生成 planning、risk提示或 manual_todo，不生成交易、审批或执行链。
7. 若规划影响风险预算、现金下限、重大支出硬约束，CFO 生成 GovernanceProposal。
8. Governance Runtime triage：低/中影响自动验证；高影响进入 Owner Approval。
9. effective 后只影响新任务或新 attempt 的 ContextSnapshot。
```

view：

- Finance：展示全资产、财务健康、风险预算、manual_todo 和非 A 股边界。
- Governance：展示高影响财务约束 proposal、影响范围、回滚和生效边界。
- Dossier：只显示脱敏现金约束、风险预算、重大支出影响摘要。

### 10.2 自动归因与 CFO 解释 Runbook

trigger：

- 每日收盘后自动归因。
- 周/月/季解释窗口。
- 归因异常：收益、风险、执行、数据、证据、条件命中异常。
- 某 Agent 的失效条件被触发。

steps：

```text
1. Performance Attribution Service 读取 PaperExecutionReceipt、持仓、Memo、DebateSummary、CIODecisionMemo、RiskReviewReport、ApprovalRecord、DataReadiness 和 Incident summary。
2. 自动生成 AttributionReport；不调用 CFO 做底层计算。
3. 无异常的日度归因自动发布。
4. 异常或周期窗口创建 CFO AgentRun。
5. CFO 读取 AttributionReport、FinanceProfile、风险预算、相关 artifact 和脱敏/授权财务上下文。
6. CFO 生成 CFOInterpretation，解释 market / decision / execution / data / risk / evidence 贡献。
7. 若需要改变系统行为，CFO 生成 GovernanceProposal。
8. 若需要学习闭环，CFO 生成 ReflectionAssignment，指定 responsible_agent、classification、questions_to_answer 和 due_policy。
```

边界：

- CFO 不是 Performance Analyst Agent 替身；自动归因服务负责计算，CFO 负责解释、治理判断和反思分派。
- CFO 不能覆盖 CIO、Risk 或 Owner，不能直接让 Prompt、Skill、风险预算或执行参数生效。

### 10.3 反思与知识晋升 Runbook

trigger：

- CFO ReflectionAssignment。
- AttributionReport 标记 `methodology_decay`、evidence gap 或 condition miss。
- Risk/DevOps/Researcher 发现可复用经验。
- Agent 输出质量评价持续偏低。

`Agent 输出质量评价持续偏低` 的实现口径：同一 `agent_id + profile_version + task_type` 最近 5 个可评分样本中，任一归因维度均值 `<0.70`，或最近 3 个样本连续 `<0.65`。样本少于 3 个时只记录 observation，不触发强制反思。

steps：

```text
1. Reflection Workflow 创建 session；semantic lead=CFO 或 Researcher；process authority=Reflection Workflow。
2. responsible Agent 读取原判断、当时证据、反证、失效条件、归因结果和 ContextSnapshot。
3. responsible Agent 产出 first draft：原判断、证据与反证、偏差分类、条件命中/失效、改进建议。
4. first draft 只能形成 ReflectionRecord，不得直接热改 Prompt、Skill、知识、参数或在途上下文。
5. Researcher 提取可复用改进，先生成或关联 MemoryItem/MemoryRelation；具备复用价值时生成 KnowledgePromotionProposal、PromptUpdateProposal 或 SkillUpdateProposal。
6. Governance Runtime 做 impact triage。
7. 低/中影响：schema validation + fixture validation + rollback plan + snapshot check 后自动生效。
8. 高影响：生成 Approval Packet，Owner 批准后生效。
9. 生效只绑定新任务或新 attempt；在途 AgentRun 继续旧 ContextSnapshot。
```

知识状态 guard：

- `MemoryItem(draft)` 只能被检索和整理，不进默认上下文。
- `MemoryItem(validated_context)` 可作为 fenced background 注入，但不得覆盖 artifact 或系统指令。
- `candidate_knowledge` 必须声明证据、适用场景和反例。
- `validated_knowledge` 可被检索和引用。
- `default_context_candidate` 必须做 impact triage。
- `effective_default_context` 必须绑定新 ContextSnapshot。

### 10.4 敏感字段与上下文投影

| 消费者 | 可见内容 | 禁止 |
|---|---|---|
| CFO / 财务服务 | 财务敏感原始字段明文、FinanceProfile、AttributionReport | 直接绕过治理生效 |
| CIO / Risk / Analyst | 脱敏现金约束、风险预算、重大支出影响摘要、CFO Interpretation | 收入、负债、家庭、税务、私人财务注释明文 |
| Researcher | 反思摘要、知识候选、Prompt/Skill diff、验证结果 | 私人财务原始字段 |
| Owner UI | 明文财务页、审批包、manual_todo | 把敏感字段泄露到普通日志或 Trace 默认视图 |

### 10.5 R8 Verification

- `finance_asset_boundary_report.json` 必须证明非 A 股资产只生成 planning/risk/manual_todo，不能生成审批/执行/交易。
- `performance_attribution_report.json` 必须证明正常日度归因自动发布，不调用 CFO。
- `cfo_governance_report.json` 必须证明异常或周期窗口触发 CFOInterpretation、GovernanceProposal 或 ReflectionAssignment。
- `researcher_workflow_report.json` 必须证明 Researcher capture/review/digest/organize 只能生成 Memory、relation、collection 建议或 proposal，且 proposal 包含 diff/manifest、impact、validation refs、rollback 和 effective scope。
- `reflection_learning_report.json` 必须证明 responsible Agent 一稿、Memory/Knowledge 晋升、低/中影响自动验证、高影响 Owner approval、no hot patch guard。
- `security_privacy_report.json` 必须证明非 CFO Agent 读取财务敏感明文被拒绝并审计。
