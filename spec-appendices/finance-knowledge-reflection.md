# Finance Knowledge Reflection

## 0. AI 阅读契约

- 本附件是 `spec.md` 中财务、知识、归因和反思链路的强证据展开层，不定义新的正式需求、验收或验证义务。
- 任务涉及财务模块、自动归因、CFO 治理、研究员、知识晋升、Prompt/Skill 提案或反思闭环时，必须读取本附件。
- 若本附件与 `spec.md` 冲突，必须停止并回到 Requirement 修补冲突。
- Performance Analyst 不是 V1 Agent；归因评价由自动化服务完成，CFO 承接需要 LLM 的解释、财务规划判断和治理签发。

## 1. 财务模块

财务模块的目标是把个人资产、负债、现金流和投资主链连接起来，为风险预算、现金约束、重大支出计划和绩效解释提供上下文。

覆盖对象：

- 全资产档案：现金、A 股纸面账户、基金、黄金、房产、其他资产。
- 现金流：收入、支出、负债、税务提醒、重大支出计划。
- 财务健康：流动性、杠杆、压力测试、风险预算、未来现金需求。
- 投资绩效：A 股纸面账户收益、回撤、成本、滑点、基准和现金使用。

边界：

- A 股普通股可进入正式投资主链。
- 基金和黄金可自动同步行情和估值，但不生成 V1 自动交易链。
- 房产默认手工估值或定期估值，不要求实时行情。
- 非 A 股资产只生成规划、风险提示或 `manual_todo`，不生成审批、执行或交易任务。
- 财务规划建议必须通过治理提案表达，不作为独立交易授权。
- 财务敏感原始字段只向 CFO 与财务服务明文开放；其他 Agent 只读取脱敏约束摘要、风险预算、流动性边界和派生 artifact。

## 2. CFO 调用边界

CFO 的能力定义、SOP、rubric 和产物字段只在 `agent-capability-matrix.md#7-cfo` 维护；本附件只说明财务、归因和反思链路在什么场景调用 CFO。

调用场景：

- 自动归因服务发现异常，需要 LLM 解释和责任分类。
- 到达周、月、季等周期解释窗口，需要面向 Owner 的财务解释。
- 财务规划、现金约束、重大支出或风险预算影响投资链。
- 归因或反思发现知识、Prompt、Skill、规则或预算变更候选。
- 需要向相关 Agent 分派反思任务。

调用约束：

- CFO 只消费自动归因、财务档案、治理记录和反思材料，不替代自动归因服务做底层计算。
- CFO 可以签发 Governance Proposal 或 Reflection Assignment；低/中影响事项可自动验证和审计后只对新任务或新 attempt 生效，高影响事项必须进入 Owner 审批。
- CFO 不能覆盖 CIO 投资结论、Risk Officer 风控结论或 Owner 审批结果。
- CFO 不能直接让 Prompt、Skill、规则、风险预算或执行参数生效。

## 3. 自动归因服务

自动归因服务是计算和评价服务，不是 Agent。它负责生成结构化归因和异常信号，供 CFO、Researcher、Risk Officer 和反思链路使用。

输入：

- 纸面订单、成交回执、持仓、现金、费用、滑点。
- 组合基准、市场状态、因子、风险预算、组合优化建议。
- Analyst Memo、Debate Summary、CIO Decision Memo、Risk Review、Owner 审批记录。
- 数据质量报告、执行服务报告、系统 incident 摘要。

输出维度：

- `market_result`：市场方向、市场状态、基准相对收益。
- `decision_quality`：IC 证据质量、反证处理、共识与行动强度匹配。
- `execution_quality`：成交窗口、成交价、滑点、费用、T+1 约束。
- `risk_quality`：风险约束、敞口、回撤、超限处理。
- `data_quality`：关键字段完整性、时效性、一致性、来源冲突。
- `evidence_quality`：关键结论是否有可解析证据，证据是否仍有效。
- `condition_hit`：CIO/Risk/Owner 设置的观察条件是否触发。
- `improvement_items`：需要 CFO 解释、Researcher 补证、Risk 复核或 DevOps 诊断的事项。

服务边界：

- 不生成自然语言治理判断。
- 不签发 Governance Proposal。
- 不修改 Prompt、规则、风险预算或执行参数。
- 不把收益好坏直接等同为 Agent 质量高低。

## 4. Investment Researcher 调用边界

Investment Researcher 的能力定义、SOP、rubric 和产物字段只在 `agent-capability-matrix.md#8-investment-researcher` 维护；本附件只说明知识、Prompt 和反思链路在什么场景调用 Researcher。

调用场景：

- Daily Brief 或外部资料需要进入研究资料池。
- 新闻、公告、服务信号、归因异常或反思结论需要转成 Topic Proposal。
- 正式 IC 需要 Research Package 作为 IC Context 的资料输入。
- 反思结论具备复用价值，需要生成 Knowledge Promotion Proposal。
- Prompt、SkillPackage 或方法论改进需要生成 Prompt Update Proposal 或 Skill Update Proposal。

调用约束：

- Researcher 产物只作为资料包、议题提案、知识晋升提案、Prompt 更新提案或 Skill 更新提案，不直接形成投资结论。
- 支撑证据不能绕过硬门槛直接进入正式 IC。
- 低/中影响知识、Prompt 或 Skill 变更可经自动验证和审计后只对新任务或新 attempt 生效；高影响变更必须经治理链和 Owner 审批。
- Researcher 不能直接修改共享知识、Prompt、SkillPackage、审批规则、风险预算或执行参数。

## 5. 知识晋升

知识晋升路径：

- `observation`：一次性观察或简报，不进入共享默认上下文。
- `candidate_knowledge`：具备证据但尚未验证适用边界。
- `validated_knowledge`：经过归因、反思或多次任务验证，可被检索使用。
- `default_context_candidate`：可能进入默认上下文、checklist、playbook、SkillPackage 或 Prompt 背景，需先做影响评级。
- `effective_default_context`：低/中影响经自动验证或高影响经 Owner 批准后，只对新任务或新 attempt 生效。

质量维度：

- 来源可信度。
- 证据可解析性。
- 时间有效性。
- 适用场景。
- 反例和失效条件。
- 与既有知识的冲突关系。
- 是否影响默认行为或审批门槛。

冲突处理：

- 事实冲突优先回到来源、时间戳和数据质量。
- 方法论冲突拆分适用场景，不直接覆盖旧知识。
- 高影响冲突由 Researcher 汇总，CFO 或相关 Agent 签发治理提案。

## 6. 反思闭环

推荐顺序：

- 自动归因服务发现问题或到达周期窗口。
- CFO 判断反思范围、责任对象和影响等级。
- 责任 Agent 产出第一稿，说明原判断、证据、偏差和改进建议。
- Researcher 整理可复用部分，生成知识晋升、Prompt 更新或 Skill 更新提案。
- 低/中影响提案经自动验证、版本快照和审计后生效；Owner 审批高影响知识、Prompt、Skill、规则或预算变化。
- 新任务或新 attempt 读取生效后的知识、Prompt、Skill 或配置快照；在途任务和 AgentRun 不被热改。

反思分类：

- 决策错误：证据不足、反证忽略、共识误判、行动强度不匹配。
- 市场偏离：市场状态突变、行业冲击、宏观假设失效。
- 执行问题：窗口、成交价格、费用、滑点或 T+1 约束处理不当。
- 数据问题：字段缺失、时效过期、多源冲突、缓存误用。
- 事件冲击：公告、政策、舆情或不可预见事件。
- 方法论退化：Prompt、Skill、checklist、因子、权重或风险预算不再适用。

反思不得直接热改运行参数、Prompt、Skill 或在途上下文；所有高影响变化必须走治理链。

## 7. 高影响边界

以下变化默认高影响，必须进入治理审批并只对新任务或新 attempt 生效：

- 默认上下文、checklist、playbook、SkillPackage 或 Prompt 背景若改变 Agent 默认行为、权限或硬边界。
- 因子权重、风险预算、审批规则或执行参数。
- 数据源信任层级、关键字段阈值或缓存使用规则。
- 正式 IC 准入门槛、共识阈值或 Risk Review 规则。
- 财务规划约束、现金下限或重大支出对投资链的硬约束。

低/中影响示例：

- 不改变默认行为的知识条目新增。
- 只影响检索摘要质量的模板改进。
- 单个 SkillPackage 内部说明或测试补充，且权限、依赖和输出 schema 不变。
- Prompt 文案澄清，不改变职责边界、审批规则、风险阈值或工具权限。
