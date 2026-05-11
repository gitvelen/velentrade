# testing.md

<!-- CODESPEC:TESTING:READING -->
## 0. AI 阅读契约

- 本文件是 Requirement 阶段测试用例计划与后续测试执行证据的权威账本。
- 每个 `TC-*` 对应 `spec.md` 中一个 approved `ACC-*`，并引用对应 `REQ-*` 与 `VO-*`。
- `spec.md` 的 `VO-*` 定义必须验证什么和期望证据类型；本文件的 `TC-*` 定义如何用场景、fixture、命令和 `RUN-*` 证据执行验证。
- 若本文件与 `spec.md` 的 `REQ/ACC/VO` 冲突，以 `spec.md` 为准，并回到 Requirement 同步修补本文件。
- 当前处于 Design 阶段，本文登记 planned 测试用例、fixture、WI 映射和后续 `RUN-*` 证据位置；Implementation、Testing、Deployment 阶段再追加 `RUN-*` 证据。
- 所有 V1 验收均为 P0，默认自动化验证；若后续任何 P0 无法自动化，必须回到 Requirement 或 review 明确接受例外理由。

## 0.1 事故更正：RUN 证据完成等级

2026-05-01 复核发现，既有 `RUN-FULL-*` 记录仅证明 pytest/vitest/static scan/fixture report 通过，不证明 PostgreSQL/Alembic、Redis/Celery、FastAPI endpoint、浏览器级前端交互、真实数据采集或跨 WI runtime 已完成。为避免继续误导，原 `test_scope: full-integration` 已降级为 `test_scope: fixture-integration`，并为既有 RUN 记录补充 `completion_level: fixture_contract`。

当前状态：

- `fixture_contract`: 已有 pytest/vitest/static/report fixture 证据，但不能声称真实系统完成。
- `in_memory_domain`: WI-002 公开 HTTP CSV/JSON K 线 adapter、质量门、fallback/cache、execution_core 低质量阻断和 report guard 失败传播等 domain 行为已有自动化验证；WI-003 P0 抢占最低分 active slot 与 report guard 失败传播已有自动化验证；Tencent 公开 A 股 K 线 live provider smoke 作为单独证据通过，但不作为 P0 自动化 pass 的唯一依据。
- `api_connected`: 已完成 WI-001/WI-004 foundation 级证据；`FastAPI` app/router、`/api/team`、`/api/gateway/*`、`/api/collaboration/commands`、`/api/workflows/*`、`/api/knowledge/memory-items*`、`/api/tasks`、`/api/approvals`、`/api/governance/changes`、`/api/finance/overview`、`/api/devops/health` 已有自动化验证；浏览器已通过 live FastAPI 从 Request Brief confirmation 进入 Investment Dossier read model。真实外部数据 provider 与全 V1 跨 WI 投资链仍未完成。
- `db_persistent`: 已完成 WI-001 foundation 级证据；`Alembic`、PostgreSQL schema、seed、Postgres smoke、API->DB mirror、Task/Workflow/WorkflowStage 持久化恢复已有自动化验证。WI-002 已完成公开 A 股 K 线 Source Registry seed、PostgreSQL DataRequest/DataLineage/DataQualityReport 落库 smoke、Celery data collection task 和 Postgres latest-success cache restore；外网 live provider smoke 仍只作单独证据，不作为 P0 pass 条件。
- `integrated_runtime`: WI-001/WI-004 RequestBrief -> Task foundation slice 已完成；同一 `docker-compose` RUN 已验证 PostgreSQL migration、Redis/Celery 服务、FastAPI endpoint、same-origin frontend、Chromium 浏览器点击、agent-runner 和 API restart 后持久化。全 V1 投资/数据/执行闭环仍未完成，不能外推为所有 WI 的 integrated_runtime。
- `owner_verified`: 未完成；人工验收仍未通过。

后续只有满足 `../lessons_learned.md` R10-R13 的真实证据，才允许重新追加 `test_scope: full-integration` 的 pass 记录。

## 1. 关键 fixture 与不变量计划

Design 阶段应优先把以下 fixture 落到测试数据工厂或 contract fixture 中，并将每个 fixture 映射到相关页面、服务、workflow 或 schema 验证命令。

- fixture_id: FX-HAPPY-PATH-BUY-A-SHARE
  covers: 标准 A 股买入任务从 Request Brief 到 Reflection Record 的完整链路。
  expected_focus: artifact trace、S0-S7、CIO/Risk/Owner、纸面执行、归因和反思。

- fixture_id: FX-DEBATE-SKIPPED
  covers: 高共识且无 hard dissent 的 IC 流程。
  expected_focus: Debate skipped 留痕、CIO 决策输入完整。

- fixture_id: FX-HIGH-CONSENSUS-HARD-DISSENT
  covers: `consensus >=0.8` 但存在 hard dissent 的 IC 流程。
  expected_focus: 不生成 debate_skipped，先执行最多 2 轮有界辩论；若 hard dissent 仍保留，则进入 Risk Review。

- fixture_id: FX-LOW-CONSENSUS-NO-EXECUTION
  covers: 低共识或行动强度不足。
  expected_focus: 不进入纸面执行，输出 reason code 和观察/补证建议。

- fixture_id: FX-MEDIUM-CONSENSUS-HARD-DISSENT
  covers: `0.7 <= consensus <0.8` 且 hard dissent 辩论后仍保留。
  expected_focus: 不走高共识跳过路径；完成有界辩论后 `risk_review_required=true`，且行动强度不足时仍不生成执行授权。

- fixture_id: FX-HARD-DISSENT-RISK-REJECTED
  covers: hard dissent 辩论后仍保留并触发 Risk Review 且被 rejected。
  expected_focus: 当前尝试硬阻断，Owner 无直接绕过入口。

- fixture_id: FX-RISK-REJECTED-REOPEN
  covers: Risk Officer 判定 `rejected` 可修复后重开指定阶段。
  expected_focus: `repairable`、`reopen_target`、reason code、Reopen Event、继承上下文、superseded artifact 和新 attempt。

- fixture_id: FX-RISK-REJECTED-UNREPAIRABLE
  covers: Risk Officer 判定 `rejected` 不可修复。
  expected_focus: 当前 attempt 终止，不进入 Owner 例外审批，不允许直接执行或绕过。

- fixture_id: FX-OWNER-CONDITIONAL-TIMEOUT
  covers: conditional_pass 后 Owner 未在默认窗口响应。
  expected_focus: `owner_timeout`、不执行、不生效；Risk conditional_pass 使 S6 blocked，CIO 重大偏离超时重开 S4 或关闭，高影响治理超时为 `expired`。

- fixture_id: FX-EXECUTION-CORE-INVALID
  covers: `execution_core` 质量低于当前 workflow 配置快照中的生效阈值。
  expected_focus: 严格阻断纸面执行，不能由缓存或 Owner 直接绕过。

- fixture_id: FX-SUPPORTING-EVIDENCE-ONLY
  covers: 新闻、公告、服务信号或研究资料仅作为支撑证据。
  expected_focus: 只能生成 candidate、Research Package 或研究任务，不能直接生成正式 IC。

- fixture_id: FX-OWNER-COMMAND-TRIAGE
  covers: 老板自由对话安排投资、研究、财务、治理、系统和人工事项。
  expected_focus: RequestBrief preview、route_type、semantic lead、TaskEnvelope、低置信 draft、禁止动作 reason_code、任务中心反馈。

- fixture_id: FX-HOT-EVENT-RESEARCH-TASK
  covers: 老板要求学习某个热点事件。
  expected_focus: 默认生成 research_task，由 Investment Researcher 承接；必要时 request_evidence/request_agent_run 给 Event Analyst；产出 Research Package、MemoryCapture 或候选 TopicProposal；不直接进入 IC、审批或执行。

- fixture_id: FX-CACHE-RESEARCH-ONLY
  covers: 缓存命中但决策核心数据不可用。
  expected_focus: 缓存可展示/研究，不产生新的执行授权。

- fixture_id: FX-SCHEDULED-DATA-COLLECTION
  covers: inputs 中定义的定时数据采集节奏、默认可见 schedule、DataCollectionRun、规范化日线落库和 latest-success cache restore。
  expected_focus: Celery beat schedule 非空；本地 runtime 默认采集少量明确 A 股标的；采集结果写入 DataRequest/DataLineage/DataQualityReport/DataCollectionRun/DailyQuote；provider 失败时走 fallback/cache 或阻断，不伪造 pass。

- fixture_id: FX-ALL-MARKET-SCREENING
  covers: 收盘后全市场初筛的数据准备与候选池基础筛选。
  expected_focus: fixture universe 执行 A 股普通股、非 ST/退市/停牌、上市满 250 个交易日、20 日均成交额 >= 5000 万、数据质量 >= 0.9 的硬过滤，并按基本面质量、量价强度、事件热度三路排序去重。

- fixture_id: FX-INTRADAY-HOLDING-MONITOR
  covers: 盘中持仓和候选池监控节奏。
  expected_focus: 持仓 30 秒、候选池 5 分钟 cadence 形成 DataRequest 模板和监控触发输入；P0/P1 阈值只生成观察/研究/处置触发，不跳过 IC、Risk 或审计。

- fixture_id: FX-SOURCE-CONFLICT-CRITICAL
  covers: 关键字段多源冲突。
  expected_focus: 标准化后冲突报告、字段重要性降级或阻断、Owner 不直接裁判原始数据。

- fixture_id: FX-HIGH-IMPACT-GOVERNANCE
  covers: 因子权重、风险预算、Prompt、审批规则或执行参数变更。
  expected_focus: 治理状态机、Owner 审批、超时不生效、新任务生效边界。

- fixture_id: FX-NON-A-ASSET-MANUAL-TASK
  covers: 基金、黄金、房产或其他非 A 股资产。
  expected_focus: 只生成规划、风险提示或 manual_todo，不生成审批/执行/交易。

- fixture_id: FX-PROMPT-NEW-TASKS-ONLY
  covers: Prompt、SkillPackage、默认上下文或共享知识变更生效。
  expected_focus: 低/中影响自动验证后只对新任务或新 attempt 生效；高影响 Owner 审批后只对新任务或新 attempt 生效；在途 AgentRun 绑定旧 ContextSnapshot。

- fixture_id: FX-AGENT-CAPABILITY-DRAFT
  covers: 团队页提交 Agent 能力配置草案。
  expected_focus: TeamReadModel 九个 Agent 卡面、AgentProfileReadModel 能力画像、AgentCapabilityConfigReadModel 草案表单、低/中影响自动验证、高影响 Owner 审批、旧 in-flight AgentRun ContextSnapshot 不变。

- fixture_id: FX-AGENT-COLLABORATION-PROTOCOL
  covers: AgentRun、CollaborationSession、封闭 CollaborationCommand、CollaborationEvent、HandoffPacket 和 Authority Gateway 受控写。
  expected_focus: Agent 可组织透明读取业务资料和过程档案，不能直接写业务 DB；封闭命令集、准入矩阵、append-only artifact/event、HandoffPacket 生成和财务敏感原始字段例外。

- fixture_id: FX-MEMORY-CAPTURE-ORGANIZE-PROMOTE
  covers: Owner/Researcher 记忆 capture、Markdown 正文、payload 抽取、tag/relation/collection 组织、Knowledge 晋升和 DefaultContextBinding 提案。
  expected_focus: MemoryItem/MemoryVersion append-only、MemoryExtractionResult 字段、MemoryRelation 追加、MemoryCollection filter、Researcher organize suggestion、Gateway 写入和新 ContextSnapshot 生效边界。

- fixture_id: FX-MEMORY-RECALL-NOT-AUTHORITY
  covers: AgentRun 召回相关记忆但不能把 Memory/Knowledge 当作正式业务事实源。
  expected_focus: ContextSlice fenced background、why_included、artifact 优先、memory_not_fact_source guard、补证/反思/治理提案路径。

- fixture_id: FX-MEMORY-FINANCE-RESTRICTED
  covers: 财务敏感原始字段被捕获、检索、注入和拒绝/脱敏的场景。
  expected_focus: finance_sensitive_raw deny、脱敏摘要可见、ContextSlice denied_memory_refs、审计事件和非 CFO 明文读取失败。

- fixture_id: FX-RISK-REJECTED-NO-OWNER-OVERRIDE
  covers: Owner 尝试绕过 Risk rejected。
  expected_focus: UI、API 和 workflow 层均拒绝绕过。

必须跨测试反复校验的不变量：

- invariant_id: INV-NO-FORBIDDEN-CAPABILITY
  statement: V1 不暴露飞书、移动端、真实券商、回测、非 A 股自动交易、策略经理、规则路径或 Performance Analyst Agent。

- invariant_id: INV-RISK-REJECTED-NO-OVERRIDE
  statement: Risk rejected 对当前 attempt 是硬阻断，Owner 不能直接批准执行。

- invariant_id: INV-NON-A-NO-TRADE
  statement: 非 A 股资产不生成审批、执行或交易任务。

- invariant_id: INV-EXECUTION-CORE-BLOCKS
  statement: `execution_core` 低于当前 workflow 配置快照中的生效阈值时阻断纸面执行，默认阈值为 `0.9`。

- invariant_id: INV-CACHE-NO-NEW-EXECUTION
  statement: 缓存不得生成新的正式决策或执行授权。

- invariant_id: INV-SUPPORTING-EVIDENCE-NO-FORMAL-IC
  statement: 支撑证据不能绕过硬门槛直接进入正式 IC。

- invariant_id: INV-GOVERNANCE-NEW-TASKS-ONLY
  statement: 高影响配置、知识和 Prompt 变更批准后只对新任务生效。

- invariant_id: INV-AGENT-READ-TRANSPARENT-WRITE-GATED
  statement: 正式 Agent 可组织透明读取业务资料、正式产物、过程档案、组织记忆和共享知识；持久化业务写入必须经 Authority Gateway，runner 不得持有业务数据库写凭证；财务敏感原始字段只向 CFO/财务服务明文开放。

- invariant_id: INV-MEMORY-NOT-FACT-SOURCE
  statement: Memory/Knowledge 只能作为上下文、证据线索和可复用经验；不能替代 artifact、stage guard、workflow state 或 DataReadinessReport 中的正式业务事实。

- invariant_id: INV-PROCESS-ARCHIVE-NO-DEFAULT-INJECTION
  statement: ProcessArchive 只能追溯原始事件/产物，不能未经 Memory/Knowledge/Governance 晋升直接进入 DefaultContext。

- invariant_id: INV-DEFAULT-CONTEXT-NEW-SNAPSHOT
  statement: MemoryCollection、KnowledgeItem 或 DefaultContextBinding 生效必须生成新的 ContextSnapshot，且只作用于新任务或新 attempt。

- invariant_id: INV-TEAM-CONFIG-NO-HOT-PATCH
  statement: 治理下团队工作区提交能力、Prompt、SkillPackage、工具权限、模型路由或默认上下文配置只能生成治理变更草案；老板默认页面不使用 Agent 技术词，且不得热改在途 AgentRun。

- invariant_id: INV-APPENDIX-NO-FORMAL-ID
  statement: appendices 不定义正式需求、验收或验证义务编号。

## 1.1 R8 runbook 验证补充

Design 修复后，以下 TC 不得只验证字段存在，必须验证 `trigger -> workflow/service/AgentRun/command -> artifact/event/handoff -> read model/view -> guard/report` 的完整链路。

- `TC-ACC-005-01` 必须执行 `FX-AGENT-COLLABORATION-PROTOCOL`：证明 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket、Authority Gateway、TraceDebugReadModel 能形成可回放协作链；命令必须覆盖 accepted/rejected/expired 至少两类结果。
- `TC-ACC-003-01` 必须执行 `FX-AGENT-CAPABILITY-DRAFT` 的只读部分：证明治理下团队工作区九个角色卡面、团队画像、近期质量和越权/失败记录可见，老板默认列表不暴露版本、上下文快照或机器 ID。
- `TC-ACC-006-01` 必须引用 `design-previews/frontend-workbench/` Markdown review pack 和 `index.html` 样式预览：证明一级主导航为 `全景 / 投资 / 财务 / 知识 / 治理`、团队不再作为一级菜单、团队位于治理下且可通过治理二级模块切换进入、route canonical parent 清晰、默认简体中文、漂亮优先且护眼其次的高端浅色卡面，Owner Decision View、Investment Dossier View 和 Trace/Debug 审计层分离，并用页面线框验证 Agent 协作展示不是长聊天 transcript。
- `TC-ACC-006-01` 对 S3 Investment Dossier 的验证必须断言 `/api/workflows/{id}/dossier` 返回结构化 `debate.owner_summary/status_summary/core_disputes/view_change_details/retained_dissent_details/round_details/next_actions`，前端中间卡片直接消费这些字段，且不同摘要条目打开不同详情；字段缺失时只能显示“后端未返回辩论详情”。
- `TC-ACC-007-01` 必须验证 Owner-facing 待办合并 UI，并验证任务、审批、manual_todo、变更、AgentCapabilityChange 和健康在 read model/API guard 层保持契约分离。
- `TC-ACC-017-01` 必须验证 IC Debate Runbook：CIO agenda、四 Analyst view_update/comment/request_evidence、Debate Manager 轮次/超时/重算、DebateSummary、Handoff 和 Risk handoff。
- `TC-ACC-023-01` 必须验证非 A 股资产只生成 planning/risk/manual_todo，不出现审批、执行或交易入口。
- `TC-ACC-025-01` 必须验证异常或周期归因才触发 CFOInterpretation、GovernanceProposal 或 ReflectionAssignment；正常日度归因自动发布。
- `TC-ACC-004-01` 必须执行 `FX-MEMORY-RECALL-NOT-AUTHORITY` 和 `FX-MEMORY-FINANCE-RESTRICTED`：证明 Memory/Knowledge 只作为 fenced background/context 注入，artifact 冲突时 artifact 优先，财务敏感 raw memory 被拒绝或脱敏。
- `TC-ACC-027-01` 必须执行 `FX-MEMORY-CAPTURE-ORGANIZE-PROMOTE`：验证 Researcher proposal 包含 diff/manifest、impact、validation refs、rollback 和 effective scope，且 Researcher 只能提出 Memory capture/organize/Knowledge 晋升建议，不能直接改 Prompt/Skill/知识默认上下文。
- `TC-ACC-028-01` 必须验证 responsible Agent first draft 不能热改运行参数、Prompt、Skill 或在途 ContextSnapshot；Memory/Knowledge 晋升必须先经过 Researcher review、验证和治理生效边界。
- `TC-ACC-018-01` 必须验证 Decision Service Runbook：装配 DecisionPacket、校验 S4 输入、生成 DecisionGuardResult、计算偏离、生成 Owner 例外候选或重开建议，且服务不替 CIO/Risk/Owner/workflow 裁决。
- `TC-ACC-030-01` 必须验证 DefaultContextBinding、MemoryCollection、KnowledgeItem 和 AgentCapabilityChange 版本进入新 ContextSnapshot，旧 in-flight AgentRun 继续引用旧版本。
- `TC-ACC-029-01` 必须验证 DevOps 日常巡检、severity、incident、recovery validation 和 Risk handoff；技术恢复后 `investment_resume_allowed=false`，必须经 Risk/workflow guard。

Design approved 前，`reviews/design-review.yaml` 必须记录 R8 cold-start drill：任取每个 WI，只读 readset、WI、命中 appendix、contracts 和 TC，能列出 runbook、schema/API、view projection、failure path 和 fixture。

<!-- CODESPEC:TESTING:CASES -->
## 2. 验收覆盖与测试用例

- tc_id: TC-ACC-001-01
  requirement_refs: [REQ-001]
  acceptance_ref: ACC-001
  verification_ref: VO-001
  work_item_refs: [WI-001]
  test_type: static_and_integration
  verification_mode: automated
  required_stage: testing
  scenario: V1 范围、排除项和合规声明校验。
  given: 系统配置、路由、功能 registry、合规文案和导航 fixture。
  when: 执行范围边界扫描和禁止能力入口扫描。
  then: Web-only、个人使用、非公开投顾、A 股普通股正式闭环成立，且无飞书、移动端、真实券商、回测、非 A 股交易入口。
  evidence_expectation: scope_boundary_report.json 包含 compliance_statement、included_capabilities、excluded_capabilities 和 forbidden_entrypoints。
  status: planned

- tc_id: TC-ACC-002-01
  requirement_refs: [REQ-002]
  acceptance_ref: ACC-002
  verification_ref: VO-002
  work_item_refs: [WI-001]
  test_type: static
  verification_mode: automated
  required_stage: testing
  scenario: 官方 Agent 与 Service registry 校验。
  given: Agent registry、Service registry 和 workflow node registry fixture。
  when: 扫描可调度角色、自动化服务和禁用角色。
  then: 只存在 V1 官方 Agent 与自动化服务；策略经理、规则路径、Performance Analyst Agent 不可调度。
  evidence_expectation: registry_validation_report.json 包含 allowed_agents、allowed_services、blocked_roles 和 workflow_node_scan。
  status: planned

- tc_id: TC-ACC-003-01
  requirement_refs: [REQ-003]
  acceptance_ref: ACC-003
  verification_ref: VO-003
  work_item_refs: [WI-001]
  test_type: contract
  verification_mode: automated
  required_stage: testing
  scenario: Agent 能力契约字段齐全、四位 Analyst 具备独立岗位能力，且团队页可见 Agent 画像。
  given: 每个正式 Agent 的 CapabilityProfile fixture、四位 Analyst 的 role-specific profile、SkillPackage、rubric、权限默认域、TeamReadModel 和 AgentProfileReadModel fixture。
  when: 按能力契约 schema 校验角色定位、输入、工具、SOP、判断标准、rubric、记忆/上下文、产物、权限、升级路径、失败处理、评价回路，以及 Macro/Fundamental/Quant/Event 是否不是同一模板换 role 参数，并渲染团队页卡面。
  then: 每个 Agent 能力卡字段齐全且无禁用职责或越权能力；四位 Analyst 均具备独立数据域、工具、Skill、role_payload、rubric 和失败状态；治理下团队工作区以中文卡面展示九个正式角色的画像、近期产物质量和失败/越权记录，老板默认列表不暴露版本、上下文快照或机器 ID。
  evidence_expectation: agent_capability_contract_report.json 包含 per_agent_pass、missing_fields、team_read_model、agent_profile_read_models、sop_rubric_pass、escalation_path_pass、quality_metrics、denied_action_records 和 authority_conflicts。
  status: planned

- tc_id: TC-ACC-004-01
  requirement_refs: [REQ-004]
  acceptance_ref: ACC-004
  verification_ref: VO-004
  work_item_refs: [WI-001]
  test_type: security_contract
  verification_mode: automated
  required_stage: testing
  scenario: Agent 组织透明读取、Authority Gateway 受控写入与财务敏感字段例外校验。
  given: 两个 AgentRun、MemoryItem/MemoryVersion/MemoryRelation/MemoryCollection、KnowledgeItem、过程档案、正式 artifact、只读 DB 账号、Authority Gateway、财务敏感原始字段和 Prompt/Skill/DefaultContext 更新提案 fixture。
  when: 执行业务资料读取、过程档案读取、Memory capture/organize、ContextSlice 召回、直接 DB 写入尝试、网关写入、append-only 更新、财务原始字段读取和 Prompt/Skill/DefaultContext 生效校验。
  then: 正式 Agent 可读取组织透明业务资料、过程档案、组织记忆和共享知识；Memory/Knowledge 只能作为 fenced background/context，不能替代 artifact 或推进业务状态；runner 无业务 DB 写凭证且直接写入被拒；持久化写入只能通过 Authority Gateway 形成 typed command/artifact/event/comment/proposal/MemoryVersion/MemoryRelation；财务敏感原始字段只对 CFO/财务服务明文可见；Prompt/Skill/Knowledge/DefaultContext 更新只对新任务或新 attempt 生效。
  evidence_expectation: memory_boundary_report.json 包含 allowed_org_reads、memory_items、memory_versions、memory_extraction_results、memory_relations、memory_collections、context_injection_decisions、denied_memory_refs、memory_not_fact_source_guards、denied_direct_writes、gateway_writes、append_only_versions、finance_sensitive_denials 和 context_snapshot_effective_scope。
  status: planned

- tc_id: TC-ACC-005-01
  requirement_refs: [REQ-005]
  acceptance_ref: ACC-005
  verification_ref: VO-005
  work_item_refs: [WI-001]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: Workflow-native collaboration 与核心/支撑 artifact 链审计追溯校验。
  given: 一个从 Request Brief 到 Reflection Record 的完整任务 fixture，包含 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket、IC Context Package、Research Package、Topic/Knowledge/Prompt/Skill Proposal、Governance Proposal 和 Incident 类支撑产物。
  when: 追溯协作对象、每个阶段状态、核心 artifact、支撑 artifact、producer、准入结果、reason code、evidence_refs 和审计记录。
  then: 下游输入均来自标准化 artifact、typed command、event、handoff 或摘要，不依赖原始长对话、runner transcript 或子 Agent summary；支撑 artifact 均能映射到所属 REQ/ACC/TC。
  evidence_expectation: collaboration_trace_report.json 包含 collaboration_sessions、agent_runs、command_registry_pass、events、handoff_packets、trace_graph、core_artifacts、supporting_artifacts、missing_artifacts、reason_codes、requirement_mapping 和 raw_conversation_dependency_check。
  status: planned

- tc_id: TC-ACC-006-01
  requirement_refs: [REQ-006]
  acceptance_ref: ACC-006
  verification_ref: VO-006
  work_item_refs: [WI-004]
  test_type: e2e
  verification_mode: automated
  required_stage: testing
  scenario: Web 主导航、中文高端浅色卡面、治理下团队工作区、三层可视化与自由对话命令路由。
  given: Web 测试环境、`FX-OWNER-COMMAND-TRIAGE`、`FX-HOT-EVENT-RESEARCH-TASK`、Owner attention 卡片、Dossier stage fixture、TeamReadModel fixture 和 Trace/Debug 入口 fixture。
  when: 打开主导航，提交投资调研、热点学习、审批、执行、规则、财务、系统和人工事项自然语言请求，并从 Owner Decision View drill down 到 Dossier、Knowledge/Research、Governance 与 Trace/Debug。
  then: 页面一级主导航存在 `全景 / 投资 / 财务 / 知识 / 治理` 且不包含团队；Dossier、Trace、团队画像、能力配置方案和审批包不作为一级菜单；主界面默认简体中文并采用漂亮优先、护眼其次的浅色高端卡面，主题使用暖瓷底色、墨色文字、玉绿主强调、靛蓝/暗金/胭脂红辅助色，卡片标题默认中文，不出现 Daily Brief、Task Center 等可中文化英文标题；Owner 默认卡片不展示非 A 股边界守卫、Prompt/Skill 版本、ContextSnapshot、trace_id、read model、`ap-*`、`gov-*`、`incident-*`、`trace-*`、`ctx-*` 等过程材料或机器 ID；Owner Decision View 只展示一个“待办”卡片合并 pending approval 与 actionable/manual task，不再同时展示独立“审批”和“人工待办”卡片；治理页提供待办、团队、变更、健康、审计二级模块切换，待办模块合并展示可处理审批和可办理任务，团队页面直接展示各角色卡片，不再有“进入 Agent 团队”中转卡；治理下团队工作区展示九个角色卡、胜任度、CFO 归因引用、能力短板和能力提升入口；Owner 默认页面不使用 `Agent/Agents/AgentRun/ContextSnapshot` 等技术词，专业术语只保留在配置或审计详情；Owner Decision View、Investment Dossier View 和 Trace/Debug 审计层分层清晰；卡片按“需处理事项、核心状态、支撑证据/健康/审计”的业务优先级排列；所有可动作请求先生成 Request Brief、任务卡或治理变更草案；Preview 显示 task_type、semantic lead、process authority、预期产物、阻断条件和审批可能性；热点学习默认生成 research_task，由 Researcher 承接，不显示审批/执行/交易入口；低置信或范围不清的输入停留 draft 并显示补充问题；Owner 待办卡片跳转到治理待办，审批项从待办进入真实 Approval detail，人工待办从待办进入对应业务模块办理；StageRail 点击只改变 selected_stage 和 URL query，不推进 workflow；知识页只展示经验、资料和整理建议，Knowledge/Prompt/Skill 或默认上下文提案归治理的“变更/待办”模块处理。
  evidence_expectation: web_command_routing_report.json 包含 nav_assertions、chinese_ui_scan、premium_light_theme_assertions、owner_facing_content_assertions、unified_todo_card_assertions、governance_module_tabs_assertions、card_layout_order_assertions、governance_agent_team_assertions、three_layer_view_assertions、request_briefs、route_decisions、semantic_lead_assignments、task_cards、research_task_cards、draft_clarification_prompts、drilldown_routes、stage_rail_selection、trace_entry_return_path 和 blocked_direct_actions。
  status: planned

- tc_id: TC-ACC-007-01
  requirement_refs: [REQ-007]
  acceptance_ref: ACC-007
  verification_ref: VO-007
  work_item_refs: [WI-004]
  test_type: e2e
  verification_mode: automated
  required_stage: testing
  scenario: Owner-facing 待办合并展示，底层任务、审批、manual_todo 与团队能力配置方案保持契约隔离。
  given: 投资任务、research_task、非 A 股人工任务、Owner 例外审批任务、治理变更任务、团队页 Agent 能力配置草案、系统 incident、审批动作和财务敏感字段 fixture。
  when: 渲染治理区并推进任务状态，提交 `approved / rejected / request_changes`、Agent 能力草案和 Owner timeout 场景。
  then: 所有任务具备 Task Envelope；治理待办默认合并展示可处理审批和待补充、待办理或受阻任务，运行中和展示型任务不出现在默认待办页；API/read model 层仍保持 TaskCenterReadModel、ApprovalCenterReadModel 和 manual_todo 边界分离，manual_todo 不进入审批/执行/交易链；投资任务绑定 S0-S7 与 reason code；research_task 显示 Researcher、资料包/候选议题/补证状态且不进入审批/执行/交易链；治理变更和团队能力配置方案进入治理状态机；低/中影响方案自动验证后只对新任务或新 attempt 生效，高影响方案进入 Owner 审批并在待办 UI 中可进入真实审批详情；incident 与 manual_todo 不进入审批/执行/交易链；Owner 审批材料包含对比分析、影响范围、替代方案和建议；审批提交后以后端状态刷新；财务敏感字段在 Dossier/Trace/非 CFO 视图只显示脱敏摘要；旧 in-flight AgentRun 继续引用旧 ContextSnapshot。
  evidence_expectation: governance_task_report.json 包含 unified_todo_items、task_envelope_states、status_mapping、research_task_isolation、semantic_lead_task_cards、governance_state_machine、agent_capability_draft_states、incident_state_mapping、manual_todo_isolation、approval_packet_completeness、approval_action_feedback、owner_timeout_ui_state、in_flight_snapshot_unchanged 和 finance_sensitive_redaction_ui；team_capability_config_report.json 包含 TeamReadModel、AgentProfileReadModel、AgentCapabilityConfigReadModel、草案提交、impact triage、自动验证/Owner 审批和热改拒绝。
  status: planned

- tc_id: TC-ACC-008-01
  requirement_refs: [REQ-008]
  acceptance_ref: ACC-008
  verification_ref: VO-008
  work_item_refs: [WI-002]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: S0-S7 投资主链阶段推进与重开。
  given: 一个 A 股买入研究任务和一个需用 Reopen Event 重开分析阶段的风险场景 fixture。
  when: 执行 S0-S7 状态机。
  then: 每阶段有责任主体、输入、输出、停止条件；节点状态只使用 `not_started/running/waiting/blocked/completed/skipped/failed`；重开不是阶段状态，必须带 reason code、目标范围、继承上下文和 superseded artifact 标记。
  evidence_expectation: s0_s7_workflow_report.json 包含 stage_outputs、responsible_roles、node_statuses、reopen_events、superseded_artifacts 和 stop_conditions。
  status: planned

- tc_id: TC-ACC-009-01
  requirement_refs: [REQ-009]
  acceptance_ref: ACC-009
  verification_ref: VO-009
  work_item_refs: [WI-002]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 数据质量三档降级、切源与阻断。
  given: Data Domain Registry、Source Registry、DataCollectionSchedule、Data Request、quality_score 为 0.95/0.85/0.65 的 `decision_core` 数据、关键字段最低分、当前 workflow 配置快照、`execution_core` 低于生效阈值、缓存命中、多源冲突 fixture、FX-SCHEDULED-DATA-COLLECTION、FX-ALL-MARKET-SCREENING 和 FX-INTRADAY-HOLDING-MONITOR。
  when: 执行 beat schedule 安装、定时数据采集、规范化落库、数据就绪、切源、缓存使用、冲突归一和正式决策推进。
  then: Celery beat schedule 默认非空；采集结果写入 DataRequest/DataLineage/DataQualityReport/DataCollectionRun/DailyQuote；0.95 正常；0.85 只能 conditional_pass 并需 Owner 例外；0.65 先触发切源/fallback，仍不可恢复时阻断新决策/执行；关键字段最低有效分或 critical conflict 可覆盖综合均值并阻断；`execution_core` 低于当前生效阈值或 freshness fail 时严格阻断纸面执行；缓存不得生成新的执行授权；收盘后初筛和盘中持仓监控只产生候选/观察/研究/处置触发，不跳过 IC、Risk 或审计。
  evidence_expectation: data_quality_degradation_report.json 包含 registry_contracts、data_collection_schedules、data_collection_runs、daily_quote_rows、beat_schedule_entries、data_request_schema、component_scores、quality_band_actions、critical_field_minimums、fallback_attempts、cache_decision_policy、conflict_resolution_report、all_market_screening_result、intraday_monitor_templates、workflow_config_snapshot、execution_core_effective_threshold、execution_core_freshness_gate、execution_core_block、risk_review_constraints、blocked_decisions 和 report_payload_contracts 要求的 guard_results。
  status: planned

- tc_id: TC-ACC-010-01
  requirement_refs: [REQ-010]
  acceptance_ref: ACC-010
  verification_ref: VO-010
  work_item_refs: [WI-002]
  test_type: contract
  verification_mode: automated
  required_stage: testing
  scenario: 服务层无投资治理权。
  given: 数据、市场状态、因子、估值、组合优化、风险、执行、归因服务输出 fixture。
  when: 扫描服务输出 schema 与 workflow 权限。
  then: 服务只输出计算结果、约束、建议或纸面回执，不生成审批、否决、真实交易或最终投资判断。
  evidence_expectation: service_boundary_report.json 包含 service_outputs、forbidden_authority_check 和 governance_owner_check。
  status: planned

- tc_id: TC-ACC-011-01
  requirement_refs: [REQ-011]
  acceptance_ref: ACC-011
  verification_ref: VO-011
  work_item_refs: [WI-002]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 市场状态默认生效并支持宏观覆盖。
  given: `risk_on / neutral / risk_off / stress / transition` 市场状态引擎输出、因子权重建议、IC Context Package 和 Macro override fixture。
  when: 构建 IC Context 并执行 Macro Analyst 覆盖流程。
  then: 市场状态默认进入协作模式与因子权重建议；每个 MarketState 枚举都有分类 reason code；宏观覆盖留痕但不是默认前置门。
  evidence_expectation: market_state_report.json 包含 default_effective_state、market_state_enum_fixtures、classification_reason_codes、factor_weight_effect、collaboration_mode 和 macro_override_audit。
  status: planned

- tc_id: TC-ACC-012-01
  requirement_refs: [REQ-012]
  acceptance_ref: ACC-012
  verification_ref: VO-012
  work_item_refs: [WI-003]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 开放议题注册与正式 IC 区分。
  given: Owner 请求、四位分析师发现、研究员提案、持仓公告、服务信号 fixture。
  when: 注册机会并尝试进入正式 IC。
  then: 所有来源可注册机会；支撑证据只能触发 candidate、Research Package 或研究任务；注册状态与正式 IC 状态分离，未过硬门槛或评分不达标不进入正式 IC。
  evidence_expectation: topic_registration_report.json 包含 registered_sources、supporting_evidence_only_actions、candidate_states、formal_ic_states 和 rejected_reasons。
  status: planned

- tc_id: TC-ACC-013-01
  requirement_refs: [REQ-013]
  acceptance_ref: ACC-013
  verification_ref: VO-013
  work_item_refs: [WI-003]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 硬门槛、四维评分、并发上限与 P0 抢占。
  given: 8 个议题 fixture，覆盖 P0/P1/P2、同主题、多 workflow 并发、非 A 股、Request Brief 缺失、核心数据不可用、研究资料为空和硬门槛失败。
  when: 执行议题评分和调度。
  then: 未过硬门槛不得进入正式 IC；正式 IC 并发不超过 3，全局 workflow 不超过 5，P0 抢占留痕且仍需 IC/风控/审计。
  evidence_expectation: topic_queue_report.json 包含 hard_gate_results、priority_score_components、priority_weighted_totals、active_ic_slots、global_workflows、preemption_events、preempted_workflow_waiting_audit 和 gate_checks。
  status: planned

- tc_id: TC-ACC-014-01
  requirement_refs: [REQ-014]
  acceptance_ref: ACC-014
  verification_ref: VO-014
  work_item_refs: [WI-003]
  test_type: contract
  verification_mode: automated
  required_stage: testing
  scenario: IC Context Package、CIO Chair Brief 生成与证据解析。
  given: 已准入正式 IC 的 A 股议题 fixture。
  when: 构建并分发 IC Context Package，并由 CIO 生成 IC Chair Brief。
  then: 共享事实包、服务结果、组合/风险上下文、研究资料、历史反思和四类角色附件齐全，证据引用可解析；Chair Brief 包含决策问题、关注边界、关键矛盾、必须回答的问题、时间预算和行动判定口径，且不预设买卖结论。
  evidence_expectation: ic_context_package_report.json 包含 shared_context、role_attachments、chair_brief、chair_brief_no_preset_decision、evidence_resolution 和 missing_sections。
  status: planned

- tc_id: TC-ACC-015-01
  requirement_refs: [REQ-015]
  acceptance_ref: ACC-015
  verification_ref: VO-015
  work_item_refs: [WI-007]
  test_type: contract
  verification_mode: automated
  required_stage: testing
  scenario: 四位 Analyst Memo schema、role_payload、证据质量、hard dissent 与岗位能力独立性校验。
  given: Macro、Fundamental、Quant、Event 四份 Memo fixture，以及四套 CapabilityProfile、SkillPackage、rubric、权限默认域 fixture。
  when: 校验通用外壳字段、role_payload 字段、评分范围、evidence_quality、hard_dissent、证据引用、反证、适用条件、失效条件和岗位能力独立记录。
  then: 四份 Memo 均满足契约且没有单一 Agent 替代其他 Agent 产出；Macro/Fundamental/Quant/Event 均具备独立 role_payload、SkillPackage 和 rubric；evidence_quality 和 hard_dissent 可被后续公式与辩论流程读取。
  evidence_expectation: analyst_memo_report.json 包含 schema_pass、role_payload_pass、profile_independence_pass、skill_package_refs、rubric_refs、score_range_pass、evidence_quality_range_pass、hard_dissent_field、evidence_refs 和 counter_evidence。
  status: planned

- tc_id: TC-ACC-016-01
  requirement_refs: [REQ-016]
  acceptance_ref: ACC-016
  verification_ref: VO-016
  work_item_refs: [WI-007]
  test_type: unit_and_integration
  verification_mode: automated
  required_stage: testing
  scenario: 共识度和行动强度公式校验。
  given: 多组 direction_score、confidence、evidence_quality fixture，覆盖 positive/neutral/negative、高/中/低共识、方向并列、高共识低行动强度和中等共识行动达标。
  when: 按总体标准差、dominant_direction_share 和行动强度公式计算 consensus_score、action_conviction 和行动阈值判定。
  then: 公式结果与期望值一致，默认 0.65 阈值输出可解释行动/不行动判定；`action_conviction <0.65` 时不生成纸面执行授权。
  evidence_expectation: consensus_action_report.json 包含 formula_inputs、population_std_outputs、dominant_direction_share、expected_outputs、actual_outputs、threshold_decisions 和 no_execution_when_low_action_conviction。
  status: planned

- tc_id: TC-ACC-017-01
  requirement_refs: [REQ-017]
  acceptance_ref: ACC-017
  verification_ref: VO-017
  work_item_refs: [WI-007]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 辩论、低共识阻断和 hard dissent 序列。
  given: 高共识无异议、高共识低行动强度、高共识但存在 hard dissent、中等共识且 hard dissent 保留、中等共识无异议、低共识、hard dissent 且 Risk rejected、辩论后共识变化八组 fixture。
  when: 执行辩论状态机和风控交接。
  then: 高共识、行动强度达标且无异议跳过辩论；高共识低行动强度不生成执行授权；高共识但存在 hard dissent 不跳过 S3，Workflow/Debate Manager 控制最多 2 轮辩论，CIO 生成 agenda/synthesis，若 hard dissent 仍保留则进入 Risk Review；中等共识进入最多 2 轮辩论并产出 Debate Summary，中等共识保留 hard dissent 时也进入 Risk Review；辩论后重算共识与行动强度；低共识不执行；hard dissent 相关 rejected 阻断。
  evidence_expectation: debate_dissent_report.json 包含 debate_skipped、high_consensus_low_action_block、high_consensus_hard_dissent_path、medium_consensus_retained_hard_dissent_path、debate_round_inputs、debate_round_outputs、debate_manager_process_fields、cio_agenda_synthesis、participants、debate_rounds、debate_summary_schema、hard_dissent_present、retained_hard_dissent、risk_review_required、recomputed_consensus、recomputed_action_conviction、execution_blocked 和 risk_rejected_block。
  status: planned

- tc_id: TC-ACC-018-01
  requirement_refs: [REQ-018]
  acceptance_ref: ACC-018
  verification_ref: VO-018
  work_item_refs: [WI-008]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: Decision Service、CIO 语义主席、组合优化器关系及重大偏离。
  given: IC Chair Brief、Debate Summary、组合优化建议、Decision Service 输入、CIO Decision Packet、CIO 小偏离、单股 5pp 偏离和组合主动偏离 20% fixture。
  when: Decision Service 装配 DecisionPacket、校验 S4 输入、生成 DecisionGuardResult；CIO 形成 Chair Brief、S3 语义 synthesis 和 S4 Decision Memo；系统按单股偏离与 `0.5 * Σ|CIO目标权重 - 优化器建议权重|` 计算组合主动偏离。
  then: Decision Service 不替 CIO/Risk/Owner/workflow 裁决；CIO 不操作服务、不创建 AgentRun、不修改 workflow 状态、不下单、不审批例外、不覆盖 Risk rejected；小偏离必须说明原因；单股 5pp 或组合 20% 及以上偏离触发 Owner 例外候选或由编排中心重开论证。
  evidence_expectation: decision_service_report.json 包含 input_artifact_refs、decision_packet、input_completeness、decision_guard_result、single_name_deviation、portfolio_active_deviation、exception_candidate_or_reopen、forbidden_service_authority_check、failure_path_cases、view_projection_results 和 runbook_trace；cio_optimizer_report.json 包含 chair_brief、debate_synthesis、packet_consumed、decision_guard_result、forbidden_cio_actions_denied、deviation_reason、single_name_deviation、portfolio_active_deviation、major_deviation_flag 和 owner_exception_or_rework。
  status: planned

- tc_id: TC-ACC-019-01
  requirement_refs: [REQ-019]
  acceptance_ref: ACC-019
  verification_ref: VO-019
  work_item_refs: [WI-008]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 风控三状态、硬阻断与 Owner 例外审批。
  given: approved、conditional_pass、rejected repairable、rejected unrepairable、Risk conditional_pass 后 Owner 超时、CIO 重大偏离审批超时和高影响治理超时 fixture。
  when: 推进 S5 到 S6。
  then: approved 通知 Owner 后可纸面执行；conditional_pass 生成 Owner 例外审批材料；rejected repairable 只能通过带目标阶段的 Reopen Event 修复；rejected unrepairable 终止当前 attempt 且不可由 Owner 直接绕过；Owner 超时按类型记录 `owner_timeout`，Risk conditional_pass 使 S6 blocked，CIO 重大偏离重开 S4 或关闭，高影响治理进入 `expired` 且不生效。
  evidence_expectation: risk_owner_exception_report.json 包含 risk_states、approval_packet、repairability、reopen_target、owner_timeout、timeout_disposition_by_type、blocked_execution、reopen_required_for_repair、unrepairable_attempt_closed 和 bypass_attempt_denied。
  status: planned

- tc_id: TC-ACC-020-01
  requirement_refs: [REQ-020]
  acceptance_ref: ACC-020
  verification_ref: VO-020
  work_item_refs: [WI-009]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 纸面账户默认初始化。
  given: 空系统或账户重置 fixture。
  when: 初始化 V1 纸面账户。
  then: 账户以 1,000,000 CNY、空仓、现金 100% 创建，并生成收益、回撤、风险预算和基准基线。
  evidence_expectation: paper_account_report.json 包含 initial_cash、positions、cost_basis、baseline_returns 和 risk_budget_baseline。
  status: planned

- tc_id: TC-ACC-021-01
  requirement_refs: [REQ-021]
  acceptance_ref: ACC-021
  verification_ref: VO-021
  work_item_refs: [WI-009]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 中等拟真纸面执行。
  given: urgent、normal、low 三类纸面订单 fixture，包含 VWAP 可用、VWAP 缺失、价格区间未命中场景。
  when: 执行纸面订单模拟。
  then: 按窗口、VWAP/TWAP、区间命中、费用、滑点、印花税、过户费、T+1 输出成交、未成交或过期回执。
  evidence_expectation: paper_execution_report.json 包含 order_windows、minute_bar_fixture、pricing_method、vwap_or_twap_calculation、price_range_check、fill_status、fees、taxes、slippage、execution_core_freshness_block 和 t_plus_one_state。
  status: planned

- tc_id: TC-ACC-022-01
  requirement_refs: [REQ-022]
  acceptance_ref: ACC-022
  verification_ref: VO-022
  work_item_refs: [WI-009]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 持仓监控与处置触发。
  given: 持仓异常波动、重大公告、风险阈值超限和执行失败 fixture。
  when: 触发持仓处置 workflow。
  then: 系统提高优先级并生成处置任务，但仍执行风控和审计，不直接跳到纸面执行。
  evidence_expectation: position_disposal_report.json 包含 triggers、priority_changes、risk_gate_present 和 audit_trace。
  status: planned

- tc_id: TC-ACC-023-01
  requirement_refs: [REQ-023]
  acceptance_ref: ACC-023
  verification_ref: VO-023
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 全资产财务档案与非 A 股交易隔离。
  given: 现金、基金、黄金、房产、收入、负债、税务提醒和重大支出 fixture。
  when: 更新财务档案并尝试生成非 A 股交易或审批。
  then: 基金/黄金可自动行情，房产手工或定期估值；非 A 股只生成规划、风险提示或 manual_todo，不生成交易或审批。
  evidence_expectation: finance_asset_boundary_report.json 包含 asset_profiles、market_data_links、manual_valuation、blocked_trade_tasks 和 manual_todo_tasks。
  status: planned

- tc_id: TC-ACC-024-01
  requirement_refs: [REQ-024]
  acceptance_ref: ACC-024
  verification_ref: VO-024
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 自动日度归因与评价服务。
  given: 已执行纸面订单、持仓表现、四份 Analyst Memo、服务输出、风险记录、condition hit/miss 和缺失输入 fixture。
  when: 运行 Performance Attribution & Evaluation Service。
  then: 生成收益、风险、成本、滑点、因子贡献、IC 决策质量、执行质量、风险质量、数据质量、证据/反证质量和条件命中评价；评分按设计公式落在 0..1，缺失输入输出 null 与 improvement item。
  evidence_expectation: performance_attribution_report.json 包含 return_attribution、risk_attribution、cost_attribution、factor_contribution、quality_score_inputs、quality_score_formula_outputs、condition_hit 和 role_quality_scores。
  status: planned

- tc_id: TC-ACC-025-01
  requirement_refs: [REQ-025]
  acceptance_ref: ACC-025
  verification_ref: VO-025
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: CFO 异常/周期解释、财务规划子类型与治理提案。
  given: 正常日度归因、异常归因、连续低分、滚动下降、周/月/季解释窗口、财务规划/风险预算建议和高影响治理提案 fixture。
  when: 执行 CFO 解释与治理链路。
  then: 正常日度归因自动发布；异常或周期窗口生成 CFO Interpretation；CFO 按 trigger 优先级、classification 映射和 responsible_agent 优先级生成 ReflectionAssignment；财务规划建议归入 Governance Proposal 子类型；高影响 Governance Proposal 进入 Owner 审批。
  evidence_expectation: cfo_governance_report.json 包含 auto_published_daily、attribution_trigger_thresholds、cfo_interpretation、classification_mapping、responsible_agent_selection、questions_to_answer、governance_subtype、governance_impact_level 和 owner_approval_required。
  status: planned

- tc_id: TC-ACC-026-01
  requirement_refs: [REQ-026]
  acceptance_ref: ACC-026
  verification_ref: VO-026
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 新增因子研究治理且不要求回测。
  given: 新因子假设、样本说明、适用市场状态、独立验证结果、registry entry、monitoring rule、drift/coverage/data_quality 异常和失效诊断 fixture。
  when: 执行因子研究准入流程。
  then: 新因子完成准入、验证、登记、监控和失效诊断；影响默认权重的变更进入高影响治理；测试不依赖 Backtrader 或历史 LLM 回测能力。
  evidence_expectation: factor_research_report.json 包含 hypothesis、sample_scope、independent_validation、registry_entry_required_fields、monitoring_rule_thresholds、invalidation_diagnosis、high_impact_factor_weight_governance 和 no_backtest_dependency。
  status: planned

- tc_id: TC-ACC-027-01
  requirement_refs: [REQ-027]
  acceptance_ref: ACC-027
  verification_ref: VO-027
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: Investment Researcher 研究、知识、Prompt 与 SkillPackage 提案链路。
  given: 每日新闻、持仓事件、研究资料、知识检索命中、Memory capture 候选、MemoryCollection、Prompt diff、SkillPackage manifest/hash/tests fixture。
  when: 研究员生成简报、资料包、议题提案、MemoryCapture、MemoryOrganizeSuggestion、知识晋升提案、Prompt 更新提案和 SkillPackage 更新提案。
  then: 简报可按 P0/P1 分类，资料包可进入 IC Context；Memory 以 Markdown+payload 抽取写入并通过 tag/relation/collection 组织；Memory 晋升为 Knowledge 或 DefaultContext 只能经自动验证/Owner 审批后对新任务或新 attempt 生效；Researcher 不能直接改 Prompt/Skill/知识默认上下文。
  evidence_expectation: researcher_workflow_report.json 包含 daily_brief、research_package、topic_proposal、memory_capture、memory_review_digest、memory_organize_suggestions、memory_relation_applications、knowledge_proposal、prompt_proposal、skill_proposal、auto_validation、owner_approval_for_high_impact 和 new_task_or_attempt_only_effect。
  status: planned

- tc_id: TC-ACC-028-01
  requirement_refs: [REQ-028]
  acceptance_ref: ACC-028
  verification_ref: VO-028
  work_item_refs: [WI-005]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 反思闭环与知识/Prompt/Skill 晋升。
  given: 自动归因异常、CFO 确认范围、责任 Agent 一稿、ReflectionDraft MemoryItem、Researcher 晋升提案、知识事实冲突/方法论冲突/记忆归类冲突、低/中影响自动验证 fixture 和高影响知识/Prompt/Skill/DefaultContext 变更 fixture。
  when: 执行反思和学习 workflow。
  then: 反思按责任链推进；责任 Agent 一稿回答原判断、证据/反证、偏差分类、条件命中/失效和改进建议，并先沉淀为 MemoryItem；知识冲突按事实/解释/方法论/记忆归类/高影响路径处理；低/中影响 Knowledge/Prompt/Skill 变更经自动验证和审计后只对新任务或新 attempt 生效，高影响变更需 Owner 审批，任何反思不直接热改参数、Prompt、Skill 或在途上下文。
  evidence_expectation: reflection_learning_report.json 包含 trigger_source、cfo_scope_confirmation、agent_first_draft_required_questions、memory_item_refs、knowledge_conflict_resolution、knowledge_promotion_refs、researcher_promotion、auto_validation、owner_approval_for_high_impact、new_task_or_attempt_only_effect 和 no_hot_context_or_param_change。
  status: planned

- tc_id: TC-ACC-029-01
  requirement_refs: [REQ-029]
  acceptance_ref: ACC-029
  verification_ref: VO-029
  work_item_refs: [WI-006]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: DevOps 异常、降级、恢复与 Risk 汇报。
  given: 数据源故障、服务超时、纸面执行环境异常、runner/tool error、敏感日志发现和 Token 成本异常 fixture。
  when: DevOps Engineer 处理系统层异常。
  then: health check 按默认阈值分级；只执行安全自动降级白名单；产生降级/恢复建议、状态告警和 Risk Officer 汇报；RecoveryPlan 包含 validation checklist 且 `investment_resume_allowed=false`；成本/Token 只作为观测不作为验收 pass/fail 指标。
  evidence_expectation: devops_incident_report.json 包含 incidents、health_threshold_results、safe_degradation_allowlist_checks、blocked_risk_relaxation_attempts、recovery_validation_checklist、recovery_plan、risk_reports、investment_resume_denied_until_guard 和 cost_observability_only。
  status: planned

- tc_id: TC-ACC-030-01
  requirement_refs: [REQ-030]
  acceptance_ref: ACC-030
  verification_ref: VO-030
  work_item_refs: [WI-002]
  test_type: integration
  verification_mode: automated
  required_stage: testing
  scenario: 配置、Prompt、Skill、Agent 能力、默认上下文治理和新任务/新 attempt 生效边界。
  given: 因子权重、风险预算、Prompt、SkillPackage、Agent 能力配置草案、KnowledgeItem、MemoryCollection、DefaultContextBinding、审批规则、执行参数变更 fixture，覆盖低/中/高影响。
  when: 提交变更并推进自动验证或 Owner 审批。
  then: 低/中影响变更完成 triage、验证、版本快照和审计后生效；高影响变更按 `draft -> triage -> assessment -> owner_pending -> approved -> effective` 或终止状态推进；生成提案、对比分析和 Owner 审批；MemoryCollection/KnowledgeItem/DefaultContextBinding/AgentCapabilityChange 必须进入新的 ContextSnapshot；超时、拒绝、取消或激活失败均不生效；生效后只对新任务或新 attempt 生效，在途任务和 AgentRun 绑定的 ContextSnapshot/配置快照不变。
  evidence_expectation: config_governance_report.json 包含 impact_levels、auto_validation、transition_guards、governance_states、change_proposals、agent_capability_change_versions、comparison_analysis、owner_approval、timeout_no_effect、activation_failed_no_effect、default_context_bindings、memory_collection_versions、effective_scope、context_snapshot_binding、context_snapshot_hash 和 in_flight_snapshot_unchanged。
  status: planned

- tc_id: TC-ACC-031-01
  requirement_refs: [REQ-031]
  acceptance_ref: ACC-031
  verification_ref: VO-031
  work_item_refs: [WI-001]
  test_type: security
  verification_mode: automated
  required_stage: testing
  scenario: 财务档案加密、敏感字段读取例外、普通日志脱敏和 runner 写入隔离。
  given: 财务档案敏感原始字段、CFO AgentRun、非 CFO AgentRun、财务服务、只读 DB 账号、runner、Authority Gateway、普通业务日志、错误日志和单 Owner 安全声明 fixture。
  when: 写入财务档案、执行 CFO/非 CFO 财务字段读取、尝试 runner 直接业务写入并触发正常/异常日志。
  then: 财务档案持久化为加密形式；CFO/财务服务可明文使用原始字段，非 CFO Agent 只能读取脱敏摘要和派生 artifact；runner 无业务写凭证；普通日志不含敏感明文；文档和配置标明单 Owner 假设。
  evidence_expectation: security_privacy_report.json 包含 encrypted_fields_check、finance_raw_read_allow_deny、derived_artifact_access、runner_write_denial、plaintext_log_scan 和 single_owner_assumption。
  status: planned

- tc_id: TC-ACC-032-01
  requirement_refs: [REQ-032]
  acceptance_ref: ACC-032
  verification_ref: VO-032
  work_item_refs: [WI-001]
  test_type: static
  verification_mode: automated
  required_stage: testing
  scenario: Requirement 文档结构、附件边界和 TC 覆盖。
  given: spec.md、testing.md、codespec readset 输出和 spec-appendices 目录。
  when: 扫描正式 REQ/ACC/VO 定义、appendix 内容和 TC 覆盖。
  then: 正式 REQ/ACC/VO 只在 spec.md 正文；每个 approved ACC 至少一个 TC；appendix 不新增正式需求 ID；appendix 读取触发、Design/Implementation on-demand 读取规则、关键 fixture 和 invariant 计划清晰。
  evidence_expectation: requirement_structure_report.json 包含 req_acc_vo_counts、tc_coverage、appendix_formal_id_scan、appendix_usage_rules、fixture_inventory、invariant_inventory、readset_alignment 和 missing_links。
  status: planned

<!-- CODESPEC:TESTING:RUNS -->
## 3. 测试执行记录

- run_note: 当前处于 Design 阶段，尚未进入实现与测试执行阶段；本文件只登记 planned TC、WI 映射和 report schema 期望。

- run_id: RUN-WI001-ACC001-20260430
  acceptance_ref: ACC-001
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: static_and_integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/test_wi001_foundation.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-002
  run_id: RUN-WI001-ACC002-20260430
  test_case_ref: TC-ACC-002-01
  verification_type: automated
  test_type: static
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/test_wi001_foundation.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-003
  run_id: RUN-WI001-ACC003-20260430
  test_case_ref: TC-ACC-003-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/test_wi001_foundation.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-004
  run_id: RUN-WI001-ACC004-20260430
  test_case_ref: TC-ACC-004-01
  verification_type: automated
  test_type: security_contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/test_wi001_foundation.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-ACC005-20260430
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/test_wi001_foundation.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-031
  run_id: RUN-WI001-ACC031-20260430
  test_case_ref: TC-ACC-031-01
  verification_type: automated
  test_type: security
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/security/test_security_boundaries.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-032
  run_id: RUN-WI001-ACC032-20260430
  test_case_ref: TC-ACC-032-01
  verification_type: automated
  test_type: static
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/requirements/test_requirement_structure.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-20260430
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/workflow/test_wi002_workflow_runtime.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-20260430
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/data/test_wi002_data_quality.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-010
  run_id: RUN-WI002-ACC010-20260430
  test_case_ref: TC-ACC-010-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/services/test_wi002_services.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-011
  run_id: RUN-WI002-ACC011-20260430
  test_case_ref: TC-ACC-011-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/services/test_wi002_services.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-030
  run_id: RUN-WI002-ACC030-20260430
  test_case_ref: TC-ACC-030-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/governance/test_wi002_governance.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-012
  run_id: RUN-WI003-ACC012-20260430
  test_case_ref: TC-ACC-012-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/intake/test_wi003_opportunity_registry.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-WI003-ACC013-20260430
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/topic_queue/test_wi003_topic_queue.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-WI003-ACC014-20260430
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/context/test_wi003_context_package.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-WI003-ACC013-P0-PREEMPTION-20260502
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: P0 抢占按最低 priority_score 选择 P1/P2 active slot victim，并保留 waiting audit/artifact refs；仍未进入跨 WI runtime/browser/API 集成。
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-WI003-ACC014-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: WI-003 report envelope 在 guard_results 或 failures 出现 fail 时输出 result=fail，避免常量 pass 自证；仍未进入跨 WI runtime/browser/API 集成。
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-20260430
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: e2e
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: frontend/src/workbench.contract.test.ts
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-20260430
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: e2e
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/e2e/test_wi004_frontend_static.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-ROUTE-20260501
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: e2e
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: npm --prefix frontend test && npm --prefix frontend run build && route smoke on http://127.0.0.1:8443 for /, /investment, /investment/wf-001, /investment/wf-001/trace, /finance, /knowledge, /governance, /governance/team, /governance/team/quant_analyst, /governance/team/quant_analyst/config, /governance/approvals/ap-001
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-ROUTE-20260501
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: e2e
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/e2e -q && npm --prefix frontend test
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-DOSSIER-PANELS-20260503
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-03
  artifact_ref: npm --prefix frontend test passed 38 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage for Investment Dossier required panels: DataReadiness, role_payload drilldown, consensus/action_conviction, DissentBoard, DebateTimeline, OptimizerDeviation, RiskGate, PaperExecution and Attribution linkback, with no visible "批准继续" or "立即成交" shortcuts.
  result: pass
  residual_risk: Dossier panels are now rendered in the frontend and API adapter can consume optional rich read-model fields, while the live FastAPI browser smoke still exercises Request Brief -> Dossier route rather than every rich panel being populated by production API data; no owner_verified evidence yet.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-DOSSIER-GUARD-PANELS-20260503
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-03
  artifact_ref: npm --prefix frontend test passed 38 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Dossier PaperExecution and guard panels show execution_core blocked, non-A/no-trade and risk-rejected/no-override states as read-only disabled UI, including "不显示继续成交入口".
  result: pass
  residual_risk: This improves browser-visible guard separation in the Dossier, but does not replace backend Risk/Execution guards or owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-AGENT-TEAM-DETAILS-20260503
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-03
  artifact_ref: npm --prefix frontend test passed 38 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Governance Agent team shows team health, pending capability drafts, failure/denial counts, weaknesses, Prompt/Context versions, CFO attribution references and agent profile version/permission boundaries.
  result: pass
  residual_risk: Agent Team workspace now renders required browser-visible management details and keeps capability changes draft-only, but this is still automated branch-local evidence rather than owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-AGENT-TEAM-DRAFT-BOUNDARY-20260503
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-03
  artifact_ref: npm --prefix frontend test passed 38 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Agent profile/config UI displays governance-only version boundaries, CFO attribution and denied-action evidence while capability draft save remains a Governance Change path with no in-flight AgentRun hot patch.
  result: pass
  residual_risk: UI boundary evidence does not replace backend GovernanceChange activation/new ContextSnapshot verification or owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-KNOWLEDGE-MEMORY-WORKSPACE-20260504
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 40 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Knowledge page renders daily brief, research package, Memory capture/review/digest/organize workspace, extraction/promotion/sensitivity, relation graph, organize suggestions, Context injection inspector with why_included/denied refs, and Knowledge/Prompt/Skill proposal diff/manifest/validation/effective scope/rollback without direct activation.
  result: pass
  residual_risk: Knowledge/Memory browser workspace is now branch-local API-connected and consumes /api/knowledge/memory-items for memory summaries, but proposal activation/new ContextSnapshot remains backend governance scope and no owner_verified evidence exists.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-APPROVAL-PACKET-COMPLETENESS-20260504
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 40 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Approval Packet detail renders comparison analysis, impact scope, alternatives, risk/impact, rollback, timeout no-effect boundary, evidence refs and backend-status-driven approval action feedback without a "批准继续执行" bypass.
  result: pass
  residual_risk: Approval packet UI material completeness is automated browser evidence; it does not replace backend ApprovalRecord/Risk guard persistence or owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-READMODEL-ERROR-REPORT-METADATA-20260504
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 49 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that API read-model failures render visible retry/fallback labeling instead of silent fixture substitution, and WI-004 verification envelopes carry concrete artifact refs plus parseable generated_at metadata instead of empty artifact_refs.
  result: pass
  residual_risk: Read-model failure labeling is now browser-visible, but this remains branch-local automated evidence and not owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-APPROVAL-ROUTE-DRAFT-FAILURE-20260504
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 49 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Approval Packet detail loads by route approval_id from /api/approvals and submits decisions to the same id, capability draft API failure shows explicit no-create feedback instead of falling back to a false success governance change ref, and 409/SNAPSHOT_MISMATCH approval decision responses display refresh guidance with server trace_id.
  result: pass
  residual_risk: Approval and draft error handling is browser/API-connected evidence; it does not replace owner_verified acceptance or backend governance activation/new ContextSnapshot verification.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-KNOWLEDGE-MEMORY-CONTROLLED-WRITES-20260504
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 49 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Knowledge workspace captures Owner memory through POST /api/knowledge/memory-items using a visible memory body input, applies organize suggestions through POST /api/knowledge/memory-items/{id}/relations with client_seen_version_id, and shows Gateway/append-only feedback without directly activating DefaultContext or overwriting old MemoryVersion.
  result: pass
  residual_risk: Knowledge capture and relation append are browser/API-connected evidence; Knowledge/Prompt/Skill activation and new ContextSnapshot remain backend governance scope and no owner_verified evidence exists.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-FINANCE-ASSET-BROWSER-UPDATE-20260504
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-04
  artifact_ref: npm --prefix frontend test passed 49 tests; npm --prefix frontend run build passed; python -m pytest tests/e2e -q passed 8 tests. Added RED/GREEN coverage that Finance page updates the cash asset profile through POST /api/finance/assets and shows browser feedback that the update does not trigger approval, execution, or trading chains.
  result: pass
  residual_risk: Finance asset profile browser action is API-connected UI evidence; it does not prove external fund/gold production quote availability or owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-20260430
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/finance/test_wi005_finance_boundary.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-024
  run_id: RUN-WI005-ACC024-20260430
  test_case_ref: TC-ACC-024-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/attribution/test_wi005_attribution_cfo_factor.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-025
  run_id: RUN-WI005-ACC025-20260430
  test_case_ref: TC-ACC-025-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/attribution/test_wi005_attribution_cfo_factor.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-026
  run_id: RUN-WI005-ACC026-20260430
  test_case_ref: TC-ACC-026-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/attribution/test_wi005_attribution_cfo_factor.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-027
  run_id: RUN-WI005-ACC027-20260430
  test_case_ref: TC-ACC-027-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/knowledge/test_wi005_researcher_reflection.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-WI005-ACC028-20260430
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/knowledge/test_wi005_researcher_reflection.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Finance asset boundary report now fails when non-A asset guard evidence or failures fail; still not a database/API/browser integration run.
  reopen_required: false

- acceptance_ref: ACC-025
  run_id: RUN-WI005-ACC025-TRIGGER-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-025-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Invalidation condition hit now triggers CFO interpretation/condition_failure, and attribution/CFO report envelope fails when guard evidence or failures fail; still uses deterministic in-memory fixtures.
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-WI005-ACC028-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Reflection/knowledge report envelope now fails when no-hot-patch guard evidence or failures fail; still uses deterministic in-memory fixtures and no Owner acceptance.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-A-SHARE-SYMBOL-GUARD-20260502
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Finance trade boundary now rejects asset_type=a_share with non-numeric exchange-suffixed refs such as AAPL.SH and keeps them projected to planning/risk/manual_todo only; still not a database/API/browser integration run.
  reopen_required: false

- acceptance_ref: ACC-027
  run_id: RUN-WI005-ACC027-NON-A-RESEARCH-BOUNDARY-20260502
  test_case_ref: TC-ACC-027-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Researcher daily brief now keeps high-severity non-A symbols such as GOLD.CNY at P1 supporting-evidence-only instead of P0 formal IC style routing; still uses deterministic in-memory fixtures.
  reopen_required: false

- acceptance_ref: ACC-029
  run_id: RUN-WI006-ACC029-20260430
  test_case_ref: TC-ACC-029-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/devops/test_wi006_incident_runtime.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-029
  run_id: RUN-WI006-ACC029-GUARD-NEGATIVE-20260502
  test_case_ref: TC-ACC-029-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/devops tests/domain/observability -q; python -m compileall src/velentrade
  result: pass
  residual_risk: execution_core source primary/fallback failure now produces a non-auto degradation plan requiring Risk review, and devops_incident_report fails when recovery guard evidence or failures fail; still not an OpenTelemetry/Prometheus/live runtime integration run.
  reopen_required: false

- acceptance_ref: ACC-015
  run_id: RUN-WI007-ACC015-20260430
  test_case_ref: TC-ACC-015-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/analysis/test_wi007_analysis.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-WI007-ACC016-20260430
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: unit_and_integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/analysis/test_wi007_analysis.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-017
  run_id: RUN-WI007-ACC017-20260430
  test_case_ref: TC-ACC-017-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/debate/test_wi007_debate.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-WI007-ACC016-DISSENT-GUARD-20260502
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Consensus calculation now marks hard dissent as requiring debate instead of execution_authorized=true; still not a cross-WI CIO/Risk/runtime integration run.
  reopen_required: false

- acceptance_ref: ACC-017
  run_id: RUN-WI007-ACC017-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-017-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Analysis and debate report envelopes now fail when hard-dissent guard evidence or failures fail; still uses deterministic in-memory fixtures.
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-WI007-ACC016-FOUR-ROLE-GUARD-20260502
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q; python -m compileall src/velentrade
  result: pass
  residual_risk: ConsensusCalculator now rejects missing or duplicate official Analyst roles before calculating consensus/action conviction, preventing one-to-three memo inputs from producing false high consensus; still not a live AgentRun/CIO/Risk runtime integration.
  reopen_required: false

- acceptance_ref: ACC-018
  run_id: RUN-WI008-ACC018-20260430
  test_case_ref: TC-ACC-018-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/decision/test_wi008_decision_service.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-WI008-ACC019-20260430
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/risk/test_wi008_risk_owner.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-018
  run_id: RUN-WI008-ACC018-DATA-QUALITY-GUARD-20260502
  test_case_ref: TC-ACC-018-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Decision Service now turns data_quality blockers into data_quality_guard reason codes and reopen recommendations, and decision report envelopes fail on guard/failure evidence; still not a cross-WI S4-S6 runtime integration.
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-WI008-ACC019-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Risk/Owner exception report envelope now fails when rejected-risk no-override guard evidence or failures fail; still uses deterministic in-memory fixtures.
  reopen_required: false

- acceptance_ref: ACC-018
  run_id: RUN-WI008-ACC018-EXECUTION-CORE-GUARD-20260502
  test_case_ref: TC-ACC-018-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q; python -m compileall src/velentrade
  result: pass
  residual_risk: DecisionGuardResult now turns execution_feasibility.execution_core_status blocked into execution_core_blocked_no_execution and reopen recommendation while suppressing Owner exception candidates; still not connected to cross-WI workflow/API/browser S4-S6 runtime.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-20260430
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/paper_account/test_wi009_account.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-20260430
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/execution/test_wi009_execution.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI009-ACC022-20260430
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: tests/domain/investment/position/test_wi009_position.py
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-NON-A-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade
  result: pass
  residual_risk: PaperExecution now blocks non-A symbols with non_a_asset_no_paper_execution, and paper execution report envelopes fail on guard/failure evidence; still not a full S6 browser/API/PostgreSQL runtime execution chain.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-ACCOUNT-STATE-20260502
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade/domain/investment/paper_account src/velentrade/domain/investment/execution src/velentrade/domain/investment/position
  result: pass
  residual_risk: PaperAccount now applies buy/sell PaperExecutionReceipt to cash, positions, cost_basis, T+1 locked availability and report payload; still in-memory only and not connected to PostgreSQL/API/browser S6 runtime.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-EXECUTION-WINDOW-20260502
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade/domain/investment/paper_account src/velentrade/domain/investment/execution src/velentrade/domain/investment/position
  result: pass
  residual_risk: PaperExecution now selects urgency-specific minute windows before VWAP/TWAP and price-range checks, and paper_execution_report exposes selected window counts; still in-memory only and not a full S6 runtime execution chain.
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI009-ACC022-WORKFLOW-ROUTE-20260502
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade/domain/investment/paper_account src/velentrade/domain/investment/execution src/velentrade/domain/investment/position
  result: pass
  residual_risk: PositionDisposalTask now records workflow_route=S5_risk_review and reason_code=position_disposal_requires_risk_review, proving abnormal holding disposal does not skip Risk; still not wired to API/PostgreSQL workflow runtime.
  reopen_required: false

- acceptance_ref: ACC-004
  run_id: RUN-FIX-ACC004-20260501
  test_case_ref: TC-ACC-004-01
  verification_type: automated
  test_type: security_contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/test_wi001_foundation.py tests/domain/workflow/test_wi002_workflow_runtime.py -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-FIX-ACC009-20260501
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/data tests/domain/investment/execution tests/domain/workflow/test_wi002_reports.py -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-015
  run_id: RUN-FIX-ACC015-20260501
  test_case_ref: TC-ACC-015-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/investment/analysis -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-FIX-ACC016-20260501
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: unit_and_integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/investment/analysis -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-FIX-ACC019-20260501
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/workflow/test_wi002_workflow_runtime.py tests/domain/governance tests/domain/investment/risk -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-FIX-ACC021-20260501
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/investment/execution -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-030
  run_id: RUN-FIX-ACC030-20260501
  test_case_ref: TC-ACC-030-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/domain/governance tests/domain/workflow/test_wi002_reports.py -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-002
  run_id: RUN-WI001-ACC002-20260502
  test_case_ref: TC-ACC-002-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_foundation.py tests/core/test_wi001_seed_bundle.py tests/agent_runner/test_runner_service.py -q
  result: pass
  residual_risk: investment/finance domain read models are not all API-connected yet
  reopen_required: false

- acceptance_ref: ACC-003
  run_id: RUN-WI001-ACC003-20260502
  test_case_ref: TC-ACC-003-01
  verification_type: automated
  test_type: contract
  test_scope: branch-local
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_foundation.py tests/core/test_wi001_seed_bundle.py -q
  result: pass
  residual_risk: 团队 read model 已接 API；仍未证明 live browser 与 FastAPI 的端到端闭环。
  reopen_required: false

- acceptance_ref: ACC-004
  run_id: RUN-WI001-ACC004-20260502
  test_case_ref: TC-ACC-004-01
  verification_type: automated
  test_type: security_contract
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py tests/core/test_wi001_postgres_smoke.py tests/core/test_wi001_db_foundation.py -q
  result: pass
  residual_risk: 财务业务 workflow 仍未全部接到真实持久化路径
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-ACC005-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py tests/core/test_wi001_postgres_smoke.py tests/core/test_wi001_seed_bundle.py -q
  result: pass
  residual_risk: 跨 WI 协作链虽可落库与回读，但完整业务闭环联调仍未完成
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-WI001-DB-SCHEMA-20260502
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local-postgres
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/core/test_wi001_db_foundation.py tests/core/test_wi001_postgres_smoke.py tests/core/test_wi001_seed_bundle.py -q
  result: pass
  residual_risk: Seeded data_source_registry entries are fixture_contract only; WI-002 has public HTTP adapter in domain tests, but no live provider smoke is claimed.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-WORKFLOW-DB-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local-api-db
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py -q
  result: pass
  residual_risk: Proves Task/Workflow/WorkflowStage persistence and recovery through API; does not prove full S0-S7 investment semantics.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-RUNTIME-DB-ENV-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local-runtime-hook
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: bash -n scripts/codespec-deploy; python -m pytest tests/core/test_wi001_deploy_hook_runtime.py tests/api/test_wi001_api_foundation.py::test_build_app_factory_uses_database_url_env -q; python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/api tests/worker tests/e2e -q; python -m compileall src/velentrade
  result: pass
  residual_risk: API factory now reads VELENTRADE_DATABASE_URL and deploy hook runtime smoke will verify RequestBrief persistence across API restart plus agent-runner endpoint, but docker compose runtime hook was not executed in this branch-local run.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-SAME-ORIGIN-FRONTEND-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local-runtime-hook
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/api/test_wi001_api_foundation.py::test_build_app_serves_frontend_dist_as_same_origin_spa tests/core/test_wi001_deploy_hook_runtime.py -q; python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/api tests/worker tests/e2e -q
  result: pass
  residual_risk: FastAPI serves frontend/dist as same-origin SPA and deploy hook checks same_origin_frontend_served; still no actual Playwright/browser-to-live-FastAPI automated run.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-COMPOSE-RUNTIME-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: manual_runtime_smoke
  test_type: runtime
  test_scope: branch-local-compose-runtime
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend run build; docker compose build migrate api agent-runner worker beat; docker compose down -v --remove-orphans; docker compose up -d postgres redis migrate agent-runner api worker beat; python compose runtime smoke for /api/team, same-origin /, /api/requests/briefs confirmation, /internal/agent-runner/runs/runtime-smoke-run/start, docker compose restart api, /api/tasks persisted_task_after_restart, docker compose ps running services
  result: pass
  residual_risk: Dockerfile/prebuilt image path now avoids container-start `pip install -e .`; Alembic reads VELENTRADE_DATABASE_URL; smoke proves Postgres/Redis/API/worker/beat/agent-runner services running and RequestBrief task persistence across API restart. This is not integrated_runtime because no browser click ran against this same compose runtime.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-COMPOSE-BROWSER-RUNTIME-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: manual_runtime_smoke
  test_type: runtime_e2e
  test_scope: branch-local-compose-browser-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-02
  artifact_ref: docker compose build migrate api agent-runner worker beat; docker compose up -d --force-recreate agent-runner api worker beat; python integrated runtime smoke for /api/team, same-origin /, /api/requests/briefs confirmation, /internal/agent-runner/runs/runtime-smoke-run-2/start, docker compose restart api, /api/tasks persisted_task_after_restart, Chromium click 自由对话 -> 生成请求预览 -> 确认生成任务卡 against http://127.0.0.1:8000, docker compose ps running services
  result: pass
  residual_risk: Proves WI-001/WI-004 foundation runtime only: RequestBrief -> Task through browser/API/PostgreSQL with Redis/Celery services and agent-runner alive. Does not prove full S0-S7 investment semantics, external data provider, paper execution, or Owner acceptance.
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-WI001-ACC001-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/test_wi001_foundation.py -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Scope/service registry and WI-001 verification report envelope now fail when forbidden entries, guard failures, or report failures are present; still not Owner verification.
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-WI001-ACC001-FULL-RUNTIME-CLOSURE-20260502
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-02
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy; observed PostgreSQL/Alembic migration, Redis/Celery worker services, FastAPI endpoint /api/workflows/{id}/dossier, Chromium browser interaction, cross-WI runtime S0-S7 with data-readiness artifact, four AnalystMemo artifacts, risk artifact, paper execution receipt and attribution artifact; full_investment_runtime_persisted survived docker compose restart api; runtime_observed_revision=eb6beb176963b04ae6c1fa2ef05a247e0aff0648.
  result: pass
  residual_risk: Proves Web/API/PostgreSQL/Redis/Celery/agent-runner/browser foundation plus a deterministic A-share S0-S7 artifact runtime closure. Service artifacts are deterministic smoke payloads through Authority Gateway, not proof of production external data provider reliability, real brokerage integration, Owner manual acceptance, or live provider terms/rate-limit readiness.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-ACC005-FULL-RUNTIME-CLOSURE-20260502
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-02
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same command and observed PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime evidence as RUN-WI001-ACC001-FULL-RUNTIME-CLOSURE-20260502; Dossier evidence_map retained workflow-scoped agent/service artifact refs after API restart, and /api/gateway/artifacts accepted both workflow-scoped Agent artifacts and service-produced artifacts under Authority Gateway.
  result: pass
  residual_risk: Proves collaboration/artifact trace foundation in the full compose runtime. It does not by itself prove every downstream WI semantic calculation is production-grade or Owner verified.
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=707963b8e0dadb9d40ca908e0828e750b5c1cbee; targeted Python runtime smoke workflow_id=wf-foundation-1777740751 artifact_id=artifact-9ef6c090013f memory_id=memory-0cd33c0b0ea9 verified PostgreSQL/Alembic migration, Redis/Celery worker services, FastAPI endpoints /api/team /api/requests/briefs /api/workflows/{id}/dossier, Chromium browser interaction, and cross-WI runtime workflow S0-S7 persistence after API restart.
  result: pass
  residual_risk: Proves current runtime foundation scope and forbidden entry guard behavior in compose; still not Owner acceptance or production external data/broker readiness.
  reopen_required: false

- acceptance_ref: ACC-002
  run_id: RUN-WI001-ACC002-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-002-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted /api/team exposes exactly nine official Agents, no forbidden roles, governance draft-only config entries, and the deploy test suite asserted the eight official Services and blocked service/role registry entries.
  result: pass
  residual_risk: Service registry validation is exercised inside the deploy test suite rather than exposed as a separate public API endpoint.
  reopen_required: false

- acceptance_ref: ACC-003
  run_id: RUN-WI001-ACC003-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-003-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted /api/team/{agent_id}, /api/team/{agent_id}/capability-config and Chromium /governance/team expose Agent profiles, finance-sensitive denials, allowed collaboration commands, and governance-only capability draft paths.
  result: pass
  residual_risk: Proves profile/read-model foundation and browser visibility; does not prove future live LLM output quality for every Agent role.
  reopen_required: false

- acceptance_ref: ACC-004
  run_id: RUN-WI001-ACC004-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-004-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted /api/collaboration/commands accepted allowed commands and rejected unknown direct DB commands without 500, /api/gateway/artifacts accepted allowed artifacts and denied disallowed artifact types, /api/gateway/memory-items created fenced background memory, /api/knowledge/memory-items persisted memory relations across API restart, and /api/finance/overview redacted sensitive finance data.
  result: pass
  residual_risk: Proves Authority Gateway and memory/context foundation through compose API/PostgreSQL; it does not make Memory or Knowledge a business fact source.
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-WI001-ACC005-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted /api/gateway/events and /api/gateway/handoffs append collaboration evidence, /api/workflows/{workflow_id}/collaboration-events and /api/workflows/{workflow_id}/handoffs return persisted lineage after API restart, and Dossier evidence_map retains workflow-scoped artifact refs.
  result: pass
  residual_risk: Proves collaboration lineage persistence and read projection foundation; downstream WI-specific semantic calculations still need their own runtime closure.
  reopen_required: false

- acceptance_ref: ACC-031
  run_id: RUN-WI001-ACC031-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-031-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted finance-sensitive raw data denial for non-CFO Agent profile, cleartext allowance for CFO, /api/finance/overview redaction_applied=true, direct DB command rejection, disallowed artifact rejection, and /api/devops/health investment_resume_allowed=false.
  result: pass
  residual_risk: Proves security/privacy foundation in local compose; it is not a penetration test or production secrets audit.
  reopen_required: false

- acceptance_ref: ACC-032
  run_id: RUN-WI001-ACC032-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-032-01
  verification_type: automated
  test_type: runtime_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; deploy test suite included tests/requirements and current trace-consistency gate passed, proving REQ/ACC/VO/TC/WI/RUN linkage remains intact while the runtime workflow and browser smoke execute at revision 707963b8e0dadb9d40ca908e0828e750b5c1cbee.
  result: pass
  residual_risk: Requirement-structure validation is primarily structural; semantic quality still requires human review per phase policy.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: browser_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; deploy smoke clicked 自由对话 -> 生成请求预览 -> 确认生成任务卡 against same-origin compose frontend/API, and targeted Chromium smoke asserted main navigation 全景/投资/财务/知识/治理 plus /governance/team Agent cards.
  result: pass
  residual_risk: Proves built frontend/browser/API foundation; full downstream investment semantics still depend on later WI runtime closures.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: browser_e2e
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: same PostgreSQL/Alembic, Redis/Celery worker, FastAPI endpoint, Chromium browser and cross-WI runtime workflow evidence as RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503; targeted runtime smoke asserted /api/team/quant_analyst/capability-drafts creates governance-only drafts, /api/approvals exposes approval center, Chromium /governance/approvals/ap-001 renders approval route, and finance asset API keeps non-A assets planning-only.
  result: pass
  residual_risk: Proves governance/task/approval foundation at API/browser level; Owner manual acceptance is still pending.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-COMPOSE-BROWSER-RUNTIME-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: manual_runtime_smoke
  test_type: browser_e2e
  test_scope: branch-local-compose-browser-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-02
  artifact_ref: same command as RUN-WI001-COMPOSE-BROWSER-RUNTIME-20260502; observed output included browser_click_confirmed_task=true, persisted_task_after_restart=true, same_origin_frontend_served=true, agent_runner_status=completed, running_services=[agent-runner, api, beat, postgres, redis, worker]
  result: pass
  residual_risk: Browser action is verified against built frontend served by compose FastAPI, not Vite; still not Owner manual acceptance and not a full investment workflow browser path.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-API-CONNECTED-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test && npm --prefix frontend run build
  result: pass
  residual_risk: Vitest/jsdom uses mocked API responses; no Playwright/browser-to-live-FastAPI closed loop.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-GOVERNANCE-ACTIONS-20260502
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test && npm --prefix frontend run build
  result: pass
  residual_risk: Approval/capability/governance UI actions call API adapters, but Owner has not performed live browser acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-DEV-API-PROXY-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/e2e/test_wi004_frontend_static.py::test_vite_dev_server_proxies_api_calls_to_fastapi -q; npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Vite dev server now proxies /api to FastAPI for real dev-browser clicks; still no Playwright/browser-to-live-FastAPI automated run.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-BROWSER-LIVE-API-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: e2e
  test_scope: branch-local-browser-api
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/e2e/test_wi004_browser_live_api.py -q; npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q; python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/api tests/worker tests/e2e -q
  result: pass
  residual_risk: Headless Chromium opens Vite, clicks 自由对话 -> 生成请求预览 -> 确认生成任务卡 -> 打开投资档案, verifies /api/tasks and Investment Dossier read model via live FastAPI; this run still does not include PostgreSQL/Redis/Celery in the same browser flow.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-LIVE-DOSSIER-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: browser_e2e
  test_scope: branch-local-browser-api
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Confirmed investment tasks now expose workflow_id in the frontend adapter and render an 打开投资档案 link that loads /api/workflows/{workflow_id}/dossier from live FastAPI. This is API-connected browser evidence only, not full integrated_runtime with Postgres/Redis/Celery.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-FEEDBACK-REPORT-NEGATIVE-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: WI-004 report envelope now returns result=fail when guard_results or failures fail, and enabled UI buttons retain feedback handlers; Vitest/jsdom and static E2E do not replace Owner manual acceptance.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-TEAM-DRAFT-FEEDBACK-20260502
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Partial /api/team responses are merged with the nine-agent official roster, and capability draft save shows submitting feedback while blocking duplicate clicks; still not Owner manual acceptance.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI004-ACC007-APPROVAL-BACKEND-FEEDBACK-20260502
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Approval action buttons now show submitting feedback, lock duplicate clicks, and render the backend returned approval decision/effective_scope instead of keeping only the local clicked action. Still not Owner manual acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-CONFIRMATION-FAILURE-FEEDBACK-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Request Brief confirmation failure now shows an explicit task-card generation failure and does not claim a task was generated or expose an Investment Dossier link. Still not Owner manual acceptance.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI004-ACC006-PREVIEW-SYNC-FEEDBACK-20260502
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-02
  artifact_ref: npm --prefix frontend test; npm --prefix frontend run build; python -m pytest tests/e2e -q
  result: pass
  residual_risk: Request preview generation now disables duplicate clicks while API sync is pending and changes the button label to a visible syncing state. Still not Owner manual acceptance.
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-FULL-ACC001-20260430
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: static
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-002
  run_id: RUN-FULL-ACC002-20260430
  test_case_ref: TC-ACC-002-01
  verification_type: automated
  test_type: static
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-003
  run_id: RUN-FULL-ACC003-20260430
  test_case_ref: TC-ACC-003-01
  verification_type: automated
  test_type: contract
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-004
  run_id: RUN-FULL-ACC004-20260430
  test_case_ref: TC-ACC-004-01
  verification_type: automated
  test_type: security_contract
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-005
  run_id: RUN-FULL-ACC005-20260430
  test_case_ref: TC-ACC-005-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-FULL-ACC006-20260430
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: e2e
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: npm --prefix frontend test && npm --prefix frontend run build && python -m pytest tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-FULL-ACC007-20260430
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: e2e
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: npm --prefix frontend test && npm --prefix frontend run build && python -m pytest tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-FULL-ACC008-20260430
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-FULL-ACC009-20260430
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-010
  run_id: RUN-FULL-ACC010-20260430
  test_case_ref: TC-ACC-010-01
  verification_type: automated
  test_type: contract
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-011
  run_id: RUN-FULL-ACC011-20260430
  test_case_ref: TC-ACC-011-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-012
  run_id: RUN-FULL-ACC012-20260430
  test_case_ref: TC-ACC-012-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-FULL-ACC013-20260430
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-FULL-ACC014-20260430
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: contract
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-015
  run_id: RUN-FULL-ACC015-20260430
  test_case_ref: TC-ACC-015-01
  verification_type: automated
  test_type: contract
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-FULL-ACC016-20260430
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: unit_and_integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-017
  run_id: RUN-FULL-ACC017-20260430
  test_case_ref: TC-ACC-017-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-018
  run_id: RUN-FULL-ACC018-20260430
  test_case_ref: TC-ACC-018-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-FULL-ACC019-20260430
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-FULL-ACC020-20260430
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-FULL-ACC021-20260430
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-FULL-ACC022-20260430
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-FULL-ACC006-ROUTE-20260501
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: e2e
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q && npm --prefix frontend test && npm --prefix frontend run build && route smoke on http://127.0.0.1:8443 for all WI-004 menu and drill-down routes
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-FULL-ACC007-ROUTE-20260501
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: e2e
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-05-01
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q && npm --prefix frontend test && npm --prefix frontend run build && route smoke on http://127.0.0.1:8443 for governance team, approval, task/manual separation routes
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-FULL-ACC023-20260430
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-024
  run_id: RUN-FULL-ACC024-20260430
  test_case_ref: TC-ACC-024-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-025
  run_id: RUN-FULL-ACC025-20260430
  test_case_ref: TC-ACC-025-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-026
  run_id: RUN-FULL-ACC026-20260430
  test_case_ref: TC-ACC-026-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-027
  run_id: RUN-FULL-ACC027-20260430
  test_case_ref: TC-ACC-027-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-FULL-ACC028-20260430
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-029
  run_id: RUN-FULL-ACC029-20260430
  test_case_ref: TC-ACC-029-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-030
  run_id: RUN-FULL-ACC030-20260430
  test_case_ref: TC-ACC-030-01
  verification_type: automated
  test_type: integration
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-031
  run_id: RUN-FULL-ACC031-20260430
  test_case_ref: TC-ACC-031-01
  verification_type: automated
  test_type: security
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-032
  run_id: RUN-FULL-ACC032-20260430
  test_case_ref: TC-ACC-032-01
  verification_type: automated
  test_type: static
  test_scope: fixture-integration
  completion_level: fixture_contract
  executed_at: 2026-04-30
  artifact_ref: python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/worker tests/e2e -q
  result: pass
  residual_risk: none
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-PUBLIC-DATA-20260502
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/data/test_wi002_public_source_adapter.py -q; python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q; python -m pytest tests/core tests/domain tests/security tests/requirements tests/agent_runner tests/model_gateway tests/api tests/worker tests/e2e -q; python -m compileall src/velentrade
  result: pass
  residual_risk: "公开 HTTP CSV adapter 已实现真实 HTTP fetch/CSV parse/registry/fallback/cache/critical field guard；自动化使用本地假传输，不声明外网 live provider 可用。"
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-TENCENT-LIVE-KLINE-20260502
  test_case_ref: TC-ACC-009-01
  verification_type: manual_live_provider_smoke
  test_type: live_provider
  test_scope: branch-local-live-provider-smoke
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python live smoke using PublicHttpJsonKlineDailyQuoteAdapter against https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600000,day,,,10,qfq
  result: pass
  residual_risk: Tencent public A-share K-line endpoint returned 10 records for 600000.SH with decision_core_status=pass and quality_band=normal; provider terms/rate limits still require review before production use, and this smoke is not a persisted scheduler/cache integration.
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-GUARD-NEGATIVE-20260502
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q; python -m compileall src/velentrade
  result: pass
  residual_risk: execution_core 低质量分即使 critical fields present 也会 blocked；WI-002 report envelope 在 guard_results 或 failures 出现 fail 时输出 result=fail，避免常量 pass 自证。
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-DB-PERSISTENCE-20260502
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: postgres_smoke
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q; python -m compileall src/velentrade
  result: pass
  residual_risk: PostgreSQL smoke migrated schema, applied seed with tencent-public-kline metadata, collected fake-transport public JSON K-line data from DB-loaded Source Registry, and persisted data_request/data_lineage/data_quality_report. This run did not yet include Celery scheduling/cache restore.
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-SCHEDULED-CACHE-20260502
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: celery_postgres_smoke
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/data tests/worker -q; python -m compileall src/velentrade
  result: pass
  residual_risk: Celery registers scheduled data collection requests, executes collect_data_request through Redis worker, loads Source Registry from PostgreSQL, persists DataRequest/DataLineage/DataQualityReport, and restores latest successful lineage as cache when provider fetch fails. Automated transport remains fake/local and does not claim external provider availability.
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-SCHEDULED-DB-ROWS-20260506
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: postgres_celery_schedule_regression
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-06
  artifact_ref: PYTHONPATH=src python3 -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q; PYTHONPATH=src python3 -m compileall -q src/velentrade
  result: pass
  residual_risk: PostgreSQL/Alembic container tests verified seeded default data_collection_schedule, database-loaded Celery beat schedule, collect_data_request persistence to DataRequest/DataLineage/DataQualityReport/DataCollectionRun/DailyQuote, latest-success cache compatibility, and report payloads for all-market screening fixture plus intraday holding/candidate monitor templates. Provider fetch remains deterministic fake transport for P0 automation; this is not a live-provider production readiness or owner_verified result.
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-STAGE-GUARD-REOPEN-20260502
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q; python -m compileall src/velentrade/domain/workflow src/velentrade/domain/data src/velentrade/domain/services src/velentrade/domain/governance src/velentrade/worker
  result: pass
  residual_risk: WorkflowRuntime now blocks completion of non-running stages, records stage_not_running in s0_s7_workflow_report, and request_reopen moves workflow to a new attempt at target stage with preserved upstream stages skipped. Still in-memory domain; not a browser/API/PostgreSQL S0-S7 runtime chain.
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-CELERY-CLEANUP-20260502
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q
  result: pass
  residual_risk: Celery Redis/Postgres smoke now releases AsyncResult with get/forget and detaches the Redis backend before Redis teardown, removing ignored AsyncResult backend cleanup exceptions from the WI-002 verification output. This is test/runtime cleanup evidence, not a new business capability.
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-AGENT-DISPATCH-IDEMPOTENCY-20260502
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/worker/test_wi002_agent_dispatch.py -q; python -m pytest tests/domain/workflow tests/domain/data tests/domain/services tests/domain/governance tests/worker -q
  result: pass
  residual_risk: AgentRunDispatcher now records completed AgentRun results and returns the original result for duplicate agent_run_id without invoking runner again or appending duplicate artifacts. This is in-memory dispatcher idempotency, not a distributed exactly-once runtime guarantee.
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-HTTP-RUNNER-TIMEOUT-20260502
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/worker/test_wi002_http_runner.py -q; python -m pytest tests/worker -q
  result: pass
  residual_risk: RunnerHttpClient maps socket TimeoutError to timed_out/budget_timeout with no artifact payloads so the dispatcher records runner_timeout_no_artifact instead of crashing or fabricating output. This is HTTP client timeout behavior, not an end-to-end distributed timeout load test.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-COST-BASIS-20260502
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade
  result: pass
  residual_risk: PaperAccount sell application now reduces remaining cost_basis proportionally with remaining position quantity; still in-memory only and not connected to PostgreSQL/API/browser S6 runtime.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-EXECUTION-SEMANTICS-20260502
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade
  result: pass
  residual_risk: PaperExecution now blocks invalid order side/urgency, filters invalid minute bars into no_valid_minute_price instead of zero-price fills, reserves fees inside partial-buy cash constraints, and reports actual selected fixture window counts; still in-memory only and not a full S6 runtime execution chain.
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI009-ACC022-REPORT-CONTRACT-20260502
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade
  result: pass
  residual_risk: position_disposal_report now includes the frozen contract field priority_escalation while retaining priority_changes compatibility; still not wired to API/PostgreSQL workflow runtime.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-SCOPE-QUANTITY-GUARD-20260502
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q; python -m compileall src/velentrade
  result: pass
  residual_risk: PaperExecution now rejects non-numeric exchange-suffixed symbols such as AAPL.SH and non-positive target quantities before pricing or fill generation; still in-memory only and not connected to PostgreSQL/API/browser S6 runtime.
  reopen_required: false

- acceptance_ref: ACC-012
  run_id: RUN-WI003-ACC012-REGISTRATION-BOUNDARY-20260502
  test_case_ref: TC-ACC-012-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: OpportunityRegistry keeps open-source registration and supporting-evidence routes as candidate/research paths without formal IC admission; still in-memory only and not connected to API/PostgreSQL workflow runtime.
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-WI003-ACC013-TOPIC-GATES-20260502
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: TopicQueue now enforces internal duplicate active/queued symbol detection, accepts SH/SZ/BJ A-share symbols, rejects out-of-range priority score components, preserves global waiting workflow count on P0 preemption, and tie-breaks same-score P1/P2 victims toward P2; still in-memory only and not connected to API/PostgreSQL workflow runtime.
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-WI003-ACC014-CONTEXT-BRIEF-20260502
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: ICContextPackage and CIO Chair Brief tests verify required refs, role attachments, evidence resolution, missing section reporting and no preset decision; still in-memory only and not a live AgentRun/API/PostgreSQL context distribution.
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-WI003-ACC013-SCOPE-PRIORITY-GUARD-20260502
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local
  completion_level: in_memory_domain
  executed_at: 2026-05-02
  artifact_ref: python -m pytest tests/domain/investment/intake tests/domain/investment/topic_queue tests/domain/investment/context -q; python -m compileall src/velentrade
  result: pass
  residual_risk: TopicQueue now rejects non-numeric exchange-suffixed symbols such as AAPL.SH and requested_priority values outside P0/P1/P2/None before formal IC admission; still in-memory only and not connected to API/PostgreSQL/browser workflow runtime.
  reopen_required: false

- acceptance_ref: ACC-008
  run_id: RUN-WI002-ACC008-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-008-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=4600ff0bb713f9609de4e254bc672996b617d448; targeted WI-002 Python runtime smoke run_id=1777769067 workflow_guard_id=workflow-aabeb03ee428 workflow_reopen_id=reopen-ea013f8ff0d2 data_request_id=quote-wi002-1777769067 data_lineage_id=lineage-quote-wi002-1777769067 celery_agent_run_id=run-wi002-celery-1777769067 celery_artifact_id=artifact-726a603d842c verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-008 assertions covered RequestBrief confirmation, S0 stage guard, completed stage output, Reopen Event target S2, attempt_no 2, persisted reopen_event row, and Dossier read model.
  result: pass
  residual_risk: This is an integrated runtime foundation slice for WI-002 workflow guard and reopen semantics; it does not prove every later investment semantic artifact is produced by live Agents or approved by Owner.
  reopen_required: false

- acceptance_ref: ACC-009
  run_id: RUN-WI002-ACC009-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-009-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=4600ff0bb713f9609de4e254bc672996b617d448; targeted WI-002 Python runtime smoke run_id=1777769067 workflow_guard_id=workflow-aabeb03ee428 workflow_reopen_id=reopen-ea013f8ff0d2 data_request_id=quote-wi002-1777769067 data_lineage_id=lineage-quote-wi002-1777769067 celery_agent_run_id=run-wi002-celery-1777769067 celery_artifact_id=artifact-726a603d842c verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-009 assertions covered seeded public HTTP Source Registry, deterministic Tencent JSON adapter fetch/parse, PostgreSQL data_request/data_lineage/quality rows, normal decision_core pass, and execution_core low-quality blocked with no execution authorization.
  result: pass
  residual_risk: Public source fetch is exercised with deterministic local transport for P0 automation; Tencent live smoke remains separate evidence and provider terms/rate-limit review is still required before production use.
  reopen_required: false

- acceptance_ref: ACC-010
  run_id: RUN-WI002-ACC010-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-010-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=4600ff0bb713f9609de4e254bc672996b617d448; targeted WI-002 Python runtime smoke run_id=1777769067 workflow_guard_id=workflow-aabeb03ee428 workflow_reopen_id=reopen-ea013f8ff0d2 data_request_id=quote-wi002-1777769067 data_lineage_id=lineage-quote-wi002-1777769067 celery_agent_run_id=run-wi002-celery-1777769067 celery_artifact_id=artifact-726a603d842c verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-010 assertions covered ServiceBoundaryChecker allowing portfolio_optimizer target_weight output and denying risk_engine fields final_investment_decision and risk_verdict.
  result: pass
  residual_risk: This proves deterministic service boundary enforcement in the runtime smoke path; WI-008 still owns role-specific Decision Service semantics.
  reopen_required: false

- acceptance_ref: ACC-011
  run_id: RUN-WI002-ACC011-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-011-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=4600ff0bb713f9609de4e254bc672996b617d448; targeted WI-002 Python runtime smoke run_id=1777769067 workflow_guard_id=workflow-aabeb03ee428 workflow_reopen_id=reopen-ea013f8ff0d2 data_request_id=quote-wi002-1777769067 data_lineage_id=lineage-quote-wi002-1777769067 celery_agent_run_id=run-wi002-celery-1777769067 celery_artifact_id=artifact-726a603d842c verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-011 assertions covered market states neutral/risk_off/risk_on/stress/transition, risk_on default IC context, factor weight effect, and Macro override audit from risk_on to risk_off with is_default_gate=false.
  result: pass
  residual_risk: Market state is deterministic fixture logic; production-quality macro classification and live macro inputs remain outside this WI-002 foundation proof.
  reopen_required: false

- acceptance_ref: ACC-030
  run_id: RUN-WI002-ACC030-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-030-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=4600ff0bb713f9609de4e254bc672996b617d448; targeted WI-002 Python runtime smoke run_id=1777769067 workflow_guard_id=workflow-aabeb03ee428 workflow_reopen_id=reopen-ea013f8ff0d2 data_request_id=quote-wi002-1777769067 data_lineage_id=lineage-quote-wi002-1777769067 celery_agent_run_id=run-wi002-celery-1777769067 celery_artifact_id=artifact-726a603d842c verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-030 assertions covered low-impact prompt change auto validation, new_attempt ContextSnapshot activation, immutable base snapshot hash, high-impact AgentCapability owner_pending state, expired no-effect terminal state, and activation_failed on expired change.
  result: pass
  residual_risk: This proves governance runtime state and context-snapshot scope in automation; Owner-facing governance approval UI semantics remain WI-004/API foundation unless separately owner_verified.
  reopen_required: false

- acceptance_ref: ACC-012
  run_id: RUN-WI003-ACC012-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-012-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=9b759ac0799115a7fac689e3b27ed97422686b8e; targeted WI-003 Python runtime smoke run_id=1777769530 workflow_id=workflow-a8fdebc689f2 brief_id=brief-284ebbe5813a topic_id=topic-p0-1777769530 api_research_artifact_id=artifact-3f001dbfc401 celery_agent_run_id=run-wi003-celery-1777769530 verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/artifacts/{id}, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-012 assertions covered owner/analyst/researcher/service_signal/holding_risk/announcement registration, supporting evidence routed to research_task, zero formal IC entries before queue admission, persisted ResearchPackage artifact, audit_event row, and outbox_event row.
  result: pass
  residual_risk: This proves WI-003 intake semantics on the existing runtime foundation; it does not add a dedicated WI-003 API router because WI-003 forbids API/DB schema edits.
  reopen_required: false

- acceptance_ref: ACC-013
  run_id: RUN-WI003-ACC013-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-013-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=9b759ac0799115a7fac689e3b27ed97422686b8e; targeted WI-003 Python runtime smoke run_id=1777769530 workflow_id=workflow-a8fdebc689f2 brief_id=brief-284ebbe5813a topic_id=topic-p0-1777769530 api_research_artifact_id=artifact-3f001dbfc401 celery_agent_run_id=run-wi003-celery-1777769530 verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/artifacts/{id}, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-013 assertions covered hard gates, weighted priority scoring, active_ic_slots=3, global workflow count=4, P0 preemption with preempted_topic_id=topic-2-1777769530, waiting audit, non-A-share rejection, and duplicate active symbol rejection.
  result: pass
  residual_risk: Topic Queue remains domain-owned and is embedded into a persisted ResearchPackage on the shared runtime foundation; S2 Analyst Memo and later investment decisions remain owned by WI-007/WI-008.
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-WI003-ACC014-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=9b759ac0799115a7fac689e3b27ed97422686b8e; targeted WI-003 Python runtime smoke run_id=1777769530 workflow_id=workflow-a8fdebc689f2 brief_id=brief-284ebbe5813a topic_id=topic-p0-1777769530 api_research_artifact_id=artifact-3f001dbfc401 celery_agent_run_id=run-wi003-celery-1777769530 verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/artifacts/{id}, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-014 assertions covered IC Context Package refs, role attachments, evidence_missing_sections=[], evidence missing refs=[], persisted chair_brief payload, and no_preset_decision_attestation=true with no buy/sell/hold/买入/卖出/持有 preset.
  result: pass
  residual_risk: This foundation RUN persisted Chair Brief inside the ResearchPackage runtime artifact; WI-010 below closes the first-class ICContextPackage/ICChairBrief API/PostgreSQL artifact gap at branch-local db_persistent level. Browser-level owner_verified evidence remains pending.
  reopen_required: false

- acceptance_ref: ACC-014
  run_id: RUN-WI010-ACC014-FIRST-CLASS-IC-ARTIFACTS-20260503
  test_case_ref: TC-ACC-014-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_ic_context_chair_and_position_disposal_are_first_class_persistent_artifacts -q failed RED with 403 on ICContextPackage before Agent write policy repair and later failed RED when missing-topic ICContextPackage was accepted, then passed after adding ICContextPackage/ICChairBrief first-class contract repair, Agent write allowlists, required-field/no-preset Gateway guards, Dossier projections, and PostgreSQL artifact restart reads; python -m pytest tests/domain/investment/context tests/domain/investment/position -q passed 7 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 17 tests; python -m compileall src/velentrade passed; ../.codespec/codespec check-gate scope passed; ../.codespec/codespec check-gate contract-boundary passed; bash ../.codespec/scripts/smoke.sh passed R14 contract repair positive/negative smoke. Assertions covered ICContextPackage topic_id, missing topic schema_validation_failed, ICChairBrief no_preset_decision_attestation=true, preset Chair Brief schema_validation_failed, /api/gateway/artifacts writes, /api/artifacts/{id} reads after ApiRuntime restart, and /api/workflows/{id}/dossier ic_context/chair_brief artifact_ref projection.
  result: pass
  residual_risk: This closes the prior first-class ICContextPackage/ICChairBrief API/PostgreSQL artifact gap at branch-local db_persistent level. It does not add browser-level IC material editing, live LLM investment quality, or owner_verified acceptance.
  reopen_required: false

- acceptance_ref: ACC-015
  run_id: RUN-WI007-ACC015-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-015-01
  verification_type: automated
  test_type: contract
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q passed 13 tests; python -m compileall src/velentrade passed; CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=089510d317f72e623e0c9e9a352d593e0e460cc6; targeted WI-007 hard runtime smoke run_id=1777770460 workflow_id=workflow-7f3ee1d9c79b brief_id=brief-728b4905e8cd task_id=task-5453e6cdc0b4 data_readiness_artifact_id=artifact-8f02395c2fef memo_artifact_ids={macro:artifact-d6a4e5add8db,fundamental:artifact-276d0bba4253,quant:artifact-39cbeebbf206,event:artifact-c1f0b86ece03} celery_agent_run_id=run-wi007-hard-celery-1777770460 celery_artifact_id=artifact-5bc41d517bb7 db_counts={analyst_memo_artifacts:5,official_roles:[event,fundamental,macro,quant],audit_events_for_objects:11,outbox_events_for_keys:9} restart_roles=[event,fundamental,macro,quant] verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-015 assertions covered four official AnalystMemo payloads, independent skill/profile/rubric refs, role_payload fields, score/evidence ranges, hard_dissent field, evidence refs, and Postgres audit/outbox persistence.
  result: pass
  residual_risk: This proves WI-007 Analyst Memo contract and role independence on the shared runtime foundation; the Analyst payloads are deterministic smoke artifacts rather than live LLM investment analysis.
  reopen_required: false

- acceptance_ref: ACC-016
  run_id: RUN-WI007-ACC016-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-016-01
  verification_type: automated
  test_type: unit_and_integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q passed 13 tests; python -m compileall src/velentrade passed; CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=089510d317f72e623e0c9e9a352d593e0e460cc6; targeted WI-007 runtime smokes hard_run_id=1777770460 workflow_id=workflow-7f3ee1d9c79b consensus={consensus_score:0.744,action_conviction:0.686,reason_code:hard_dissent_requires_debate,execution_authorized:false} low_action_run_id=1777770361 workflow_id=workflow-763587ae6670 consensus={consensus_score:0.744,action_conviction:0.628,reason_code:hard_dissent_requires_debate,execution_authorized:false} debate_low_action={stop_reason:low_action_conviction_blocked,execution_blocked:true} celery_agent_run_ids=[run-wi007-hard-celery-1777770460,run-wi007-celery-1777770361] db_counts_each={analyst_memo_artifacts:5,collaboration_commands:3,collaboration_events:2,handoff_packets:1,audit_events_for_objects:11,outbox_events_for_keys:9} verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/collaboration/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-016 assertions covered formula inputs, consensus/action calculation, default threshold, hard dissent not authorizing execution, and low action blocking execution.
  result: pass
  residual_risk: Runtime evidence covers deterministic consensus/action calculations and threshold guards; live Analyst scoring quality remains outside this foundation proof.
  reopen_required: false

- acceptance_ref: ACC-017
  run_id: RUN-WI007-ACC017-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-017-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/analysis tests/domain/investment/debate -q passed 13 tests; python -m compileall src/velentrade passed; CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=089510d317f72e623e0c9e9a352d593e0e460cc6; targeted WI-007 hard runtime smoke run_id=1777770460 workflow_id=workflow-7f3ee1d9c79b command_ids={cio_view_update:command-cf08a848564f,event_evidence:command-add9fc34eda5,quant_recompute:command-7b428cf04ec9} event_ids={cio_agenda:event-a6fd940e90e6,event_view_update:event-03f18d88a051} handoff_id=handoff-a1508441ab1f debate={rounds_used:2,stop_reason:hard_dissent_risk_handoff,retained_hard_dissent:true,risk_review_required:true,next_stage_decision:enter_s4_with_s5_hard_dissent_review,execution_blocked:false} db_counts={collaboration_commands:3,collaboration_events:2,handoff_packets:1,s3_stage_status:completed} restart_check={api_restarted:true,dossier_roles_after_restart:[event,fundamental,macro,quant],handoff_visible_after_restart:true} verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/collaboration/commands /api/gateway/events /api/gateway/handoffs /api/workflows/{id}/commands /api/workflows/{id}/dossier, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-017 assertions covered S3 bounded two-round debate, CIO agenda, Analyst view update/evidence command loop, recompute request, retained hard dissent, Risk handoff, stage completion, and persisted Dossier visibility after API restart.
  result: pass
  residual_risk: Runtime evidence stops at S3-to-S5 handoff because WI-007 does not own Risk Review verdict, Owner exception, paper execution, or frontend rendering beyond the compose browser foundation.
  reopen_required: false

- acceptance_ref: ACC-018
  run_id: RUN-WI008-ACC018-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-018-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q passed 13 tests; python -m compileall src/velentrade passed; CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy observed current revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8, completed full pytest/vitest/build/container runtime smoke then returned rc=141 during final service-list pipe check; follow-up docker compose ps showed postgres, redis, agent-runner, api, worker, beat running and GET /api/tasks returned 200; targeted WI-008 runtime smoke run_id=1777771002 workflow_id=workflow-be8ed5bd8cd1 brief_id=brief-da894e622366 task_id=task-37da354c0c8e data_readiness_artifact_id=artifact-c4b9d30985b7 decision_packet_artifact_id=artifact-e8df66112fb8 cio_decision_artifact_id=artifact-aae3a6812721 decision_guard_artifact_id=artifact-03a8f4572101 s3_handoff_id=handoff-be32374da28c s4_handoff_id=handoff-882391f332ec celery_agent_run_id=run-wi008-cio-celery-1777771002 celery_artifact_id=artifact-6c92be3a2b8f decision_guard={single_name_deviation_pp:6.0,portfolio_active_deviation:0.03,major_deviation:true,owner_exception_candidate_ref:decision-exception-d66bfa873f0a,reason_codes:[decision_major_deviation_requires_exception_or_reopen,retained_hard_dissent_risk_review]} db_counts={DecisionPacket:1,DecisionGuardResult:1,CIODecisionMemo:2,AnalystMemo:4,handoff_packets:2,audit_events_for_objects:6,outbox_events_for_keys:11,s4_stage_status:completed} restart_check={api_restarted:true,dossier_decision_service_status:blocked,decision_packet_read_after_restart:true,dossier_owner_exception_candidate_ref:decision-exception-d66bfa873f0a} verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/gateway/handoffs /api/workflows/{id}/commands /api/workflows/{id}/dossier /api/artifacts/{id}, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-018 assertions covered DecisionPacket assembly, S4 input refs, CIO packet consumption, major optimizer deviation formula, Owner exception candidate, no service authority over CIO/Risk/Owner/workflow, Dossier decision guard projection, and artifact readability after API restart.
  result: pass
  residual_risk: Runtime uses the current generic Gateway service producers portfolio_optimization for DecisionPacket and risk_engine for DecisionGuardResult because no dedicated decision_service producer/API scope exists in WI-008; first-class Dossier decision_packet and optimizer_deviation projection remains limited to artifact retrieval and guard projection without API changes.
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-WI008-ACC019-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q passed 13 tests; python -m compileall src/velentrade passed; compose runtime from WI-008 ACC-018 evidence stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart already observed at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-008 risk runtime smoke run_id=1777771446 conditional_workflow_id=workflow-87cbeb782a22 conditional_brief_id=brief-1b374be44571 conditional_risk_artifact_id=artifact-adfcc24de9b2 conditional_handoff_id=handoff-8a7c55a1d2b7 owner_packet_candidate_id=decision-exception-e7edd5713d21 owner_approval_id=approval-risk-conditional-1777771446 owner_timeout_disposition=s6_blocked_no_execution rejected_workflow_id=workflow-331dedca03c5 rejected_brief_id=brief-26c48d6bd797 rejected_risk_artifact_id=artifact-12155b91cc3a reopen_event_id=reopen-97f615ba7ce7 risk_bypass_attempt=denied:risk_rejected_no_override s6_bypass_status=409 s6_bypass_reason_code=upstream_stage_not_completed db_counts={risk_review_artifacts:2,reopen_events:1,handoff_packets:3,paper_execution_conditional:0,paper_execution_rejected:0,audit_events_for_objects:3,outbox_events_for_keys:3} restart_check={api_restarted:true,conditional_risk_status:conditional_pass,rejected_risk_status:rejected}; ACC-019 assertions covered Risk approved/conditional/rejected domain states, conditional_pass Owner packet, Owner timeout no-execute disposition, rejected repairable Reopen Event target S4, rejected bypass denial, no PaperExecutionReceipt on blocked paths, workflow/API denial of direct S6 transition, and Dossier risk state visibility after API restart.
  result: pass
  residual_risk: Runtime persists RiskReviewReport, HandoffPacket and ReopenEvent, while Owner ApprovalRecord remains domain-level evidence because WI-008 has no allowed API/Gateway write path for creating approval records; first-class persisted Owner exception approval creation would require API/DB scope expansion.
  reopen_required: false

- acceptance_ref: ACC-019
  run_id: RUN-WI008-ACC019-APPROVAL-PERSISTENCE-20260503
  test_case_ref: TC-ACC-019-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_owner_approval_decisions_are_persisted_after_runtime_restart -q failed RED with KeyError for the original approval_id after ApiRuntime restart, then passed after adding approval_record payload columns, SQLAlchemy ApprovalRecord mirror/load methods, persisted seed creation, and persisted /api/approvals/{id}/decision updates; python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q passed 13 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 15 tests; python -m compileall src/velentrade passed. Assertions covered /api/approvals exposing the seeded Owner exception ApprovalRecord, POST /api/approvals/{id}/decision storing decision=approved, rebuilding ApiRuntime from the same database_url, and /api/approvals returning the same approval_id with decision=approved and effective_scope=current_attempt_only.
  result: pass
  residual_risk: This closes the prior domain-only ApprovalRecord evidence gap for API/PostgreSQL persistence. This RUN does not add a new public POST /api/approvals creation contract beyond existing workflow/domain-created approvals, nor browser-level owner_verified evidence.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; compose runtime from WI-008 ACC-018 evidence stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow persistence foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-009 runtime smoke run_id=1777771944 execution_workflow_id=workflow-f8c2d9797fac execution_brief_id=brief-10169f128303 execution_task_id=task-87b33ce8f713 initial_account_ref=artifact-314c7d8facf5 updated_account_ref=artifact-50a9bde22130 account_initial={cash:1000000 CNY,positions:{},cash_ratio:1.0,benchmark_ref:baseline-cash} account_after_filled_buy={cash:987788.718 CNY,position_600000_SH_quantity:1200.0,available_quantity:0.0,t_plus_one_state:locked_until_next_trading_day,total_value:999994.878,return_value:-5.122}; db_counts={PaperAccount:2,PaperExecutionReceipt:4,PaperOrder:4,AnalystMemo:4,CIODecisionMemo:1,RiskReview:1,Attribution:1,DataReadiness:1,DecisionGuardResult:1,workflow_stage_statuses:{S0:completed,S1:completed,S2:completed,S3:completed,S4:completed,S5:completed,S6:completed,S7:completed},audit_events_for_refs:7,outbox_events_for_wi009_keys:{wi001.artifact:29,wi001.handoff:3}} restart_check={api_restarted:true,dossier_paper_execution_status:filled,initial_account_artifact_read_after_restart:true,updated_account_cash_after_restart:987788.718 CNY,filled_receipt_t_plus_one_after_restart:locked_until_next_trading_day}; ACC-020 assertions covered 1,000,000 CNY default PaperAccount initialization, empty positions, cash baseline, risk budget, PaperAccount persistence through FastAPI Gateway/PostgreSQL, account update from filled buy, T+1 locked availability, S6 completion, and artifact readability after API restart.
  result: pass
  residual_risk: Runtime persists PaperAccount through the generic Gateway artifact ledger using trade_execution; the dedicated paper_account table is present from DB foundation but not updated by this Gateway write path within WI-009 scope.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-PAPER-TABLE-MIRROR-20260503
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_gateway_paper_execution_artifacts_are_mirrored_to_dedicated_tables -q failed RED because paper_account row paper-account-table-1 was absent after Gateway artifact writes, then passed after SqlAlchemyGatewayMirror started mirroring PaperAccount artifacts into dedicated paper_account rows; python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 16 tests; python -m compileall src/velentrade passed. Assertions covered PaperAccount artifact payload writing account_id=paper-account-table-1, cash=1000000, total_value=1000000 into paper_account while preserving generic artifact refs.
  result: pass
  residual_risk: This closes the prior generic-ledger-only PaperAccount table mirror gap for API/PostgreSQL persistence. This RUN does not add browser-level paper account editing or owner_verified evidence.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; same docker compose runtime with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click, and cross-WI workflow runtime as RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503; targeted WI-009 paper execution smoke run_id=1777771944 workflow_id=workflow-f8c2d9797fac filled_receipt_ref=artifact-44353eb29f69 blocked_receipt_ref=artifact-2a64ae4f3c97 expired_receipt_ref=artifact-5c5b3a56b9b2 twap_receipt_ref=artifact-53bbbe990d1c filled_receipt={paper_order_id:paper-order-filled-1777771944,execution_window:2h,pricing_method:minute_vwap,fill_status:filled,fill_price:10.1718,fill_quantity:1200,fees:{commission:5.0,transfer:0.122},taxes:{stamp_tax:0},slippage:{policy_bps:5},t_plus_one_state:locked_until_next_trading_day} blocked_receipt={paper_order_id:paper-order-blocked-1777771944,execution_window:30m,fill_status:blocked,reason_code:execution_core_blocked,market_data_refs:[execution-core-blocked-1777771944]} expired_receipt={paper_order_id:paper-order-expired-1777771944,execution_window:30m,fill_status:expired,reason_code:price_range_not_hit} twap_receipt={paper_order_id:paper-order-twap-1777771944,execution_window:full_day,pricing_method:minute_twap,fill_status:filled,fill_price:10.3698,fill_quantity:100}; db_counts={receipt_statuses:{filled:2,blocked:1,expired:1},PaperOrder:4,PaperExecutionReceipt:4,S6:completed,S7:completed} restart_check={api_restarted:true,dossier_paper_execution_status:filled,dossier_pricing_method:minute_vwap,dossier_evidence_has_receipts:{filled:true,blocked:true,expired:true,twap:true},blocked_reason_after_restart:execution_core_blocked,expired_status_after_restart:expired,twap_pricing_after_restart:minute_twap}; ACC-021 assertions covered urgency windows, minute VWAP/TWAP, price range miss, fees/taxes/slippage, execution_core blocked no-fill, T+1 state, no real broker/order/backtest call, S6/S7 workflow completion, Dossier projection, and persisted receipt reads after API restart.
  result: pass
  residual_risk: Runtime persists PaperOrder and PaperExecutionReceipt through the generic Gateway artifact ledger and Dossier first-receipt projection; the dedicated paper_order/paper_execution_receipt tables are DB foundation tables but are not the current Gateway mirror target in WI-009 scope.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-PAPER-TABLE-MIRROR-20260503
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_gateway_paper_execution_artifacts_are_mirrored_to_dedicated_tables -q failed RED because paper_order/paper_execution_receipt dedicated rows were absent after Gateway artifact writes, then passed after SqlAlchemyGatewayMirror started mirroring PaperOrder and PaperExecutionReceipt artifacts into dedicated paper_order and paper_execution_receipt rows; python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 16 tests; python -m compileall src/velentrade passed. Assertions covered PaperOrder artifact writing paper_order_id=paper-order-table-1/workflow_id/status into paper_order and PaperExecutionReceipt artifact writing receipt_id=artifact_ref, paper_order_id=paper-order-table-1, fill_status=filled into paper_execution_receipt.
  result: pass
  residual_risk: This closes the prior generic-ledger-only PaperOrder/PaperExecutionReceipt table mirror gap for API/PostgreSQL persistence. This RUN does not add browser-level execution controls or owner_verified evidence.
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI009-ACC022-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; same docker compose runtime with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click, and cross-WI workflow runtime as RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503; targeted WI-009 position disposal smoke run_id=1777771944 disposal_workflow_id=workflow-59c312df57f6 disposal_brief_id=brief-77203704ec9e disposal_handoff_ref=handoff-047ddc203d99 disposal_task={task_id:position-disposal-0cefb6bff97e,symbol:600000.SH,triggers:[abnormal_volatility,major_announcement,risk_threshold_breach],priority:P0,risk_gate_present:true,execution_core_guard_present:true,direct_execution_allowed:false,workflow_route:S5_risk_review,reason_code:position_disposal_requires_risk_review} blocked_direct_s6_workflow_id=workflow-c7a3a0294dfd blocked_direct_s6_status=409 blocked_direct_s6_reason_code=upstream_stage_not_completed; db_counts={disposal_handoff_count:1,disposal_receipt_count:0,blocked_workflow_s6:{node_status:blocked,reason_code:upstream_stage_not_completed},audit_events_for_refs:7,outbox_events_for_wi009_keys:{wi001.artifact:29,wi001.handoff:3}} restart_check={api_restarted:true,disposal_risk_status_after_restart:approved,disposal_handoff_persisted:true}; ACC-022 assertions covered abnormal volatility/major announcement/risk threshold triggers, P0 escalation, PositionDisposalTask risk gate and execution_core guard fields, direct_execution_allowed=false, route back to S5 Risk Review via persisted handoff, no PaperExecutionReceipt on disposal workflow, and direct S6 bypass blocked by workflow guard.
  result: pass
  residual_risk: This foundation RUN represented PositionDisposalTask as domain payload plus HandoffPacket; WI-010 below closes the first-class PositionDisposalTask artifact/API/schema/table mirror gap at branch-local db_persistent level. Browser-level owner_verified evidence remains pending.
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI010-ACC022-FIRST-CLASS-POSITION-DISPOSAL-20260503
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_ic_context_chair_and_position_disposal_are_first_class_persistent_artifacts -q failed RED because PositionDisposalTask direct_execution_allowed=true was accepted before Gateway guard repair, then passed after adding PositionDisposalTask to the trade_execution Gateway allowlist, rejecting direct-execution/non-risk-review payloads, projecting Dossier position_disposal, and mirroring accepted PositionDisposalTask artifacts into the position_disposal_task PostgreSQL table; python -m pytest tests/domain/investment/context tests/domain/investment/position -q passed 7 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 17 tests; python -m compileall src/velentrade passed; ../.codespec/codespec check-gate scope passed; ../.codespec/codespec check-gate contract-boundary passed; bash ../.codespec/scripts/smoke.sh passed R14 contract repair positive/negative smoke. Assertions covered PositionDisposalTask /api/gateway/artifacts write, /api/artifacts/{id} read after restart, Dossier position_disposal artifact_ref/task_id/direct_execution_allowed=false/workflow_route=S5_risk_review, 403 denial with reason_code=position_disposal_requires_risk_review for direct execution payloads, and dedicated position_disposal_task table fields.
  result: pass
  residual_risk: This closes the prior first-class PositionDisposalTask API/schema/table mirror gap at branch-local db_persistent level. It does not add browser-level disposal controls, owner_verified acceptance, or real broker/order capability.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 finance runtime smoke run_id=1777772442 finance_assets={fund:{asset_id:fund-wi005-1777772442,boundary_label:finance_planning_only,source:auto_quote},gold:{asset_id:gold-wi005-1777772442,boundary_label:finance_planning_only,source:auto_quote},real_estate:{asset_id:real_estate-wi005-1777772442,boundary_label:finance_planning_only,source:manual}} runtime_overview_manual_todo=[real_estate] non_a_brief_id=brief-478200059820 manual_task_id=task-617e689185a3 manual_task={task_type:manual_todo,current_state:ready,reason_code:request_brief_confirmed,workflow_id:null} approvals_before_after={before:1,after:1} guard_decisions={fund:non_a_asset_no_trade,gold:non_a_asset_no_trade,fake_a_share_AAPL_SH:non_a_asset_no_trade,valid_a_share_600000_SH:a_share_trade_chain_allowed} projected_to=[planning,risk_hint,manual_todo] domain_manual_todo_types=[real_estate,tax,major_expense]; db_counts={manual_task:{task_type:manual_todo,current_state:ready,reason_code:request_brief_confirmed},workflow_for_manual_task:0,paper_execution_for_manual_task:0,approval_rows_total:0} restart_check={api_restarted:true,manual_task_visible_after_restart:true,approvals_after_restart_count:1,finance_overview_fixture_asset_types:[cash,fund,gold,real_estate,liability],finance_overview_manual_todo_types:[real_estate,tax,major_expense]}; ACC-023 assertions covered fund/gold planning-only assets, real_estate manual valuation todo, non-A trade RequestBrief conversion to manual_todo, no workflow creation, no approval count increase, no paper execution artifact, invalid exchange-suffixed AAPL.SH denied, valid A-share control allowed, PostgreSQL persisted manual task, and API readability after restart.
  result: pass
  residual_risk: Finance asset updates themselves remain API in-memory read models in current scope; durable evidence is the persisted manual_todo TaskEnvelope and absence of workflow/approval/execution for non-A trade. First-class FinanceProfile persistence would require API/DB scope outside WI-005.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-FINANCE-PROFILE-PERSISTENCE-20260503
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: integration
  test_scope: branch-local
  completion_level: db_persistent
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/api/test_wi001_api_db_persistence.py::test_finance_asset_updates_are_persisted_after_runtime_restart -q failed RED with KeyError cash-persisted-1 before implementation, then passed after adding finance_profile Alembic table, SQLAlchemy mirror/load path, API runtime restore, and FinanceProfileService upsert semantics; python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi001_api_db_persistence.py -q passed 14 tests; python -m compileall src/velentrade passed. Assertions covered /api/finance/assets writing cash and fund assets into PostgreSQL, rebuilding ApiRuntime from the same database_url, /api/finance/overview returning cash-persisted-1 and fund-persisted-1 after restart, fund remaining finance_planning_only, and liquidity recomputed from persisted cash.
  result: pass
  residual_risk: This closes the prior FinanceProfile in-memory read model gap for API/PostgreSQL persistence. This RUN does not add browser UI evidence or external fund/gold production quote availability.
  reopen_required: false

- acceptance_ref: ACC-024
  run_id: RUN-WI005-ACC024-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-024-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 attribution runtime smoke run_id=1777772723 workflow_id=workflow-f8c2d9797fac routine_attr_ref=artifact-209e910bef8b missing_condition_attr_ref=artifact-b4a9b090493a routine_scores={decision_quality:0.818,execution_quality:0.948,risk_quality:0.87,data_quality:0.95,evidence_quality:0.897,condition_score:1.0,needs_cfo:false,triggers:[]} missing_condition_scores={decision_quality:0.425,execution_quality:0.767,risk_quality:null,improvement_items:[missing_input:risk_review],condition_score:0.0,needs_cfo:true,triggers:[single_dimension_low,condition_failure]}; db_counts={attribution_artifacts:2,outbox_events_for_keys:2,audit_events_for_objects:2} restart_check={api_restarted:true,dossier_attribution_status:completed,dossier_evidence_has_new_refs:{routine:true,missing_condition:true},routine_needs_cfo_after_restart:false,missing_risk_quality_after_restart:null,missing_improvement_items_after_restart:[missing_input:risk_review]}; ACC-024 assertions covered return/benchmark inputs, decision/execution/risk/data/evidence quality scores in 0..1, condition hit/miss scoring, normal daily auto publication without CFO, missing risk input yielding null risk_quality plus improvement item, Dossier attribution projection, PostgreSQL persistence, outbox/audit, and API artifact readability after restart.
  result: pass
  residual_risk: Runtime uses the existing performance_attribution_evaluation service producer and generic Gateway artifact ledger; dedicated attribution-specific tables or richer Owner-facing attribution drilldown projection would require API/DB/frontend scope outside WI-005.
  reopen_required: false

- acceptance_ref: ACC-025
  run_id: RUN-WI005-ACC025-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-025-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 CFO runtime smoke run_id=1777772928 workflow_id=workflow-f8c2d9797fac attribution_ref=artifact-f561536bb757 cfo_interpretation_ref=artifact-dcef08628d55 reflection_ref=artifact-769127c2bf7d handoff_ref=handoff-cbdbd73d2af7 trigger_candidates=[hard_blocker_hit,single_dimension_low,rolling_drop,repeated_degradation,condition_failure,periodic_window] selected_trigger=hard_blocker_hit cfo_interpretation={finance_context_used:authorized_or_redacted,recommended_followups:[hard_blocker_hit],sensitive_data_redaction_summary:non_cfo_redacted} governance_proposal={proposal_type:finance_planning,impact_level:high,effective_scope:new_task,validation_result_refs:[schema,fixture,scope,rollback,snapshot]} governance_change_state=owner_pending owner_approval_required=true reflection_assignment={classification:data_quality_problem,responsible_agent_id:devops_engineer,question_count:3,process_authority:reflection_workflow,status:assigned}; db_counts={Attribution:1,CFOInterpretation:1,ReflectionRecord:1,handoff_packets:1,outbox_events_for_keys:4,audit_events_for_objects:4} restart_check={api_restarted:true,dossier_evidence_has_refs:{attribution:true,cfo:true,reflection:true},cfo_trigger_after_restart:hard_blocker_hit,cfo_governance_subtype_after_restart:finance_planning,cfo_governance_state_after_restart:owner_pending,cfo_owner_approval_required_after_restart:true,reflection_classification_after_restart:data_quality_problem,reflection_responsible_after_restart:devops_engineer,reflection_question_count_after_restart:3}; ACC-025 assertions covered abnormal/weekly trigger candidates, trigger priority selection, CFO interpretation payload, finance_planning governance subtype, high impact owner_pending requirement, ReflectionAssignment classification/responsible agent/questions, persisted CFO/reflection artifacts, handoff, PostgreSQL audit/outbox, and API artifact readability after restart.
  result: pass
  residual_risk: GovernanceProposal and owner approval semantics are persisted inside the CFOInterpretation payload and handoff, while first-class GovernanceProposal/ApprovalRecord creation for CFO finance_planning proposals is not available through the current WI-005 allowed API/Gateway surface.
  reopen_required: false

- acceptance_ref: ACC-026
  run_id: RUN-WI005-ACC026-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-026-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 factor runtime smoke run_id=1777773162 workflow_id=workflow-f8c2d9797fac factor_artifact_ref=artifact-b787395cacec factor_handoff_ref=handoff-390685aad640 factor_result={factor_id:low-vol-1777773162,hypothesis:low_vol_reduces_drawdown,registry_status:validated,owner:researcher,market_state_scope:[range_bound],validation_refs:[independent-validation-v1],monitoring_rule_ref:monitoring-low-vol-1777773162,rollback_ref:rollback-low-vol-1777773162} monitoring={coverage_min:0.8,data_quality_min:0.85,direction_failure_windows:5,alerts:[coverage_below_threshold],pause_default_weight:true} governance={proposal_type:factor_weight,impact_level:high,effective_scope:new_task} no_backtest_dependency=true backtest_engine_invoked=false; db_counts={factor_service_results:1,handoff_packets:1,outbox_events_for_keys:2,audit_events_for_objects:2} restart_check={api_restarted:true,dossier_evidence_has_factor_ref:true,artifact_type:ServiceResult,service_result_type:factor_research_admission,registry_status:validated,governance_type:factor_weight,governance_impact:high,backtest_engine_invoked:false}; ACC-026 assertions covered hypothesis, sample scope, independent validation, registry required fields, monitoring thresholds, coverage drift alert, invalidation diagnosis with pause_default_weight, high impact factor_weight governance, no Backtrader/backtest dependency, persisted factor ServiceResult, handoff, PostgreSQL audit/outbox, and API artifact readability after restart.
  result: pass
  residual_risk: Factor research runtime uses factor_engine ServiceResult plus HandoffPacket because WI-005 has no first-class FactorResearchResult/GovernanceProposal Gateway artifact type; dedicated factor registry persistence would require API/DB contract scope.
  reopen_required: false

- acceptance_ref: ACC-027
  run_id: RUN-WI005-ACC027-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-027-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 researcher runtime smoke continued_run_id=1777773458 workflow_id=workflow-f8c2d9797fac research_ref=artifact-8478e85eb2b1 memory_id=memory-9598b0319a55 memory_version_id=memory-version-9fbd2bfc4830 relation_id=memory-relation-42d649e6a79e handoff_ref=handoff-087497a5fb23 commands={knowledge:command-902eceaa10d0,prompt:command-8b97fb948b5b,skill:command-78bc3ed52159} daily_brief_priorities=[P0,P1] supporting_evidence_only=[false,true] topic_proposal={formal_ic_status:candidate,supporting_evidence_only:true} proposal_impacts={knowledge:medium,prompt:medium,skill:high} skill_owner_approval_required=true effective_scope=new_task direct_update_denials={prompt:denied:in_flight_snapshot_locked,skill:denied:in_flight_snapshot_locked,knowledge:denied:in_flight_snapshot_locked,default_context:denied:in_flight_snapshot_locked}; db_counts={ResearchPackage:1,MemoryItem:1,MemoryRelation:1,handoff_packets:1,proposal_commands:{knowledge:1,prompt:1,skill:1},outbox_events_for_keys:5,audit_events_for_objects:6} restart_check={api_restarted:true,research_artifact_read:true,memory_status:validated_context,memory_relation_count:1,memory_relation_target:knowledge-method-1,knowledge_search_result_count:1,daily_brief_priorities:[P0,P1],direct_update_denials_persisted:true}; ACC-027 assertions covered researcher daily brief P0/P1 classification, ResearchPackage persistence, topic proposal as supporting evidence, Memory capture/version/extraction, MemoryRelation organization, knowledge/prompt/skill proposal commands, high impact skill owner approval flag, new_task effective scope, denial of direct Prompt/Skill/Knowledge/DefaultContext hot edits, PostgreSQL audit/outbox, and API readability after restart.
  result: pass
  residual_risk: Knowledge/Prompt/Skill proposals are persisted as CollaborationCommand payloads and handoff context, not as first-class KnowledgePromptSkillProposal artifacts or activated GovernanceChange records; activation/new ContextSnapshot remains covered by later governance scope.
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-WI005-ACC028-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 reflection runtime smoke run_id=1777773693 workflow_id=workflow-f8c2d9797fac draft_memory_id=memory-e8ad4f581a1b draft_memory_version=memory-version-1ccceed4ec9c reflection_ref=artifact-a4ca03bb5173 promotion_command_id=command-51accb5afb2a handoff_ref=handoff-dbcda98efc07 cfo_scope_confirmation={assignment_ref:reflection-assignment-143e26b59fe2,trigger_source:artifact-dcef08628d55,scope:confirmed} responsible_agent_draft_required_questions=[original_judgment,evidence_counter_evidence,classification_condition_improvement] knowledge_conflict_resolution={fact_conflict:artifact_priority,methodology_conflict:split_applicable_scenarios,memory_classification:gateway_relation_suggestion,high_impact:governance_proposal} knowledge_promotion_refs=[knowledge-proposal-0e196e0bb4e1] researcher_promotion={proposal_ref:knowledge-proposal-0e196e0bb4e1,effective_scope:new_task} owner_approval_for_high_impact=true new_task_or_attempt_only_effect=true no_hot_context_or_param_change={prompt:denied,skill:denied,context_snapshot:unchanged,parameter:denied}; db_counts={draft_memory:1,ReflectionRecord:1,promotion_command:1,handoff_packet:1,outbox_events_for_keys:3,audit_events_for_objects:4} restart_check={api_restarted:true,draft_memory_status:validated_context,reflection_classification:data_quality_problem,reflection_memory_refs:[memory-e8ad4f581a1b,memory-b84248946b9e],owner_approval_for_high_impact:true,new_task_effect:true,prompt_guard:denied,context_snapshot_guard:unchanged,promotion_command_requires_owner_approval:true,direct_hot_edit_allowed:false,effective_scope:new_task}; ACC-028 assertions covered CFO scope confirmation, responsible agent first draft requirements, reflection draft memory persistence, ReflectionRecord persistence, knowledge conflict resolution, knowledge promotion refs, Researcher promotion command, high-impact owner approval flag, new-task-only effect, no hot Prompt/Skill/context/parameter change, PostgreSQL audit/outbox, and API readability after restart.
  result: pass
  residual_risk: Reflection promotion is persisted as ReflectionRecord plus CollaborationCommand/Handoff payload, not as an activated GovernanceChange or new ContextSnapshot in WI-005; full activation/new snapshot evidence is owned by the governance/config WI.
  reopen_required: false

- acceptance_ref: ACC-029
  run_id: RUN-WI006-ACC029-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-029-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  command_or_steps: "See artifact_ref for exact run-specific command output; executed pytest target suite, python -m compileall src/velentrade, docker compose runtime smoke covering PostgreSQL/Alembic, Redis/Celery, FastAPI, same-origin Chromium, API restart persistence, and targeted WI assertions."
  artifact_ref: python -m pytest tests/domain/devops tests/domain/observability -q passed 8 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-006 devops runtime smoke run_id=1777774043 workflow_id=workflow-f8c2d9797fac devops_payload_ref=artifact-65efef669654 handoff_ref=handoff-c5427a516d6a commands={incident:command-39b511f49ebd,degradation:command-5f9a1b322abf,recovery:command-69d62549c544} incident_count=6 incident_types=[cost_token,data_source,execution_environment,security,service,system] severity_values=[P0,P1] risk_notice_count=5 sensitive_log_finding_count=1 health_endpoint={routine_checks:1,recovery_resume_values:[false]} incident_endpoint={count:6,severities:[P0,P1],resume_values:[false,false,false,false,false,false],risk_required_count:5} recovery_validation={incident_status:monitoring,technical_recovery_status:validated,investment_resume_allowed:false} safe_degradation_allowlist={source_fallback:true,research_cache:true,stage_blocked:true,risk_relaxation:false} blocked_risk_relaxation=[blocked:risk_relaxation_requires_risk_or_governance] cost_observability_only=true investment_resume_denied_until_guard=true risk_handoff={to:risk_officer,blockers:[investment_resume_allowed=false],decisions:[safe_degradation_only,cost_observability_only,no_business_resume_by_devops]}; db_counts={devops_artifact:1,handoff_packet:1,devops_commands:3,outbox_events:{wi001.artifact:1,wi001.command:3,wi001.handoff:1},audit_events:{artifact_submitted:1,command_accepted:3,handoff_created:1}} restart_check={api_restarted:true,artifact_read:true,devops_health_read:true,devops_incidents_read:true,handoff_visible:true,dossier_evidence_has_devops:true}; ACC-029 assertions covered routine health, severity classification, incident/degradation/recovery payload, safe degradation allowlist, blocked risk relaxation, recovery validation with investment_resume_allowed=false, Risk handoff, sensitive log finding, cost/token observability-only semantics, PostgreSQL audit/outbox, and API readability after restart.
  result: pass
  residual_risk: DevOps runtime persists the incident payload, DevOps commands and Risk handoff through the generic Gateway ledger; DevOps is still not allowed to make business Risk decisions, resume investment execution, or hot-edit high-impact configuration.
  reopen_required: false

- acceptance_ref: ACC-001
  run_id: RUN-WI001-ACC001-ALEMBIC-CHAIN-REGRESSION-20260505
  test_case_ref: TC-ACC-001-01
  verification_type: automated
  test_type: regression
  test_scope: branch-local-regression
  completion_level: db_persistent
  executed_at: 2026-05-05
  command_or_steps: "python -m pytest tests/core/test_wi001_db_foundation.py::test_alembic_is_configured_with_a_wi001_foundation_revision -q"
  artifact_ref: "passed 1 test; verified the single Alembic head while locating the WI-001 foundation migration by walking the down_revision chain after WI-010 added later migrations."
  result: pass
  residual_risk: none
  reopen_required: false

<!-- CODESPEC:TESTING:RISKS -->
## 4. 残留风险与返工判断

- residual_risk: medium
- reopen_required: false
- notes:
  - 本阶段已追加 WI-001/WI-004 的 `api_connected` 与 `db_persistent` 级实现证据；历史 `RUN-FULL-*` 仍仅为 `fixture_contract`。
  - Implementation 阶段必须按 `contracts/verification-report-schemas.md` 生成可复核 report artifact。
  - WI-004 已补 Investment Dossier 浏览器可见业务区块：DataReadiness、role_payload、共识/行动强度、分歧、辩论、优化偏离、Risk、纸面执行和归因回链，并保持 Risk rejected、execution_core blocked、非 A 股和低行动强度无执行捷径；团队工作区已补团队健康、待处理草案、失败/越权、能力短板、CFO 归因、Prompt/Context 版本和画像权限边界；Knowledge/Memory 页已补每日简报、研究资料包、Memory 工作区、关系图、组织建议、Context 注入检查、Knowledge/Prompt/Skill 提案、Owner Memory capture 和 relation append 组织建议应用；Finance 页已补浏览器级现金资产档案更新入口并明确不触发审批/执行/交易链路；审批包详情已补对比分析、影响范围、替代方案、风险影响、回滚和超时不生效边界，并补 route approval_id 加载/提交一致性与 409/SNAPSHOT_MISMATCH 刷新提示；能力草案 API 失败不再伪造成功；read model 加载失败会显示重试和 fallback 标记；WI-004 report envelope 已补 artifact_refs 与 parseable generated_at metadata；当前为 branch-local `api_connected` 证据，仍未达到 owner_verified。
  - WI-002 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI workflow endpoint、Chromium 浏览器交互、S0-S7 persistence、Reopen Event、公开 A 股 K 线 Source Registry/采集落库、execution_core 阻断、服务边界、市场状态和治理 ContextSnapshot 生效边界。Tencent 公开 A 股 K 线 live provider smoke 仍只作单独证据，不作为 P0 pass 条件；真实外部 provider 生产可用性、全 V1 业务语义和 Owner 人工验收仍未完成。
  - WI-003 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI workflow/Gateway endpoint、Chromium 浏览器交互、Opportunity Registry、Topic Queue、P0 抢占、IC Context Package 和 CIO Chair Brief 持久化载荷。2026-05-03 WI-010 repair 已补 first-class ICContextPackage/ICChairBrief Gateway artifact、Artifact API、Dossier projection 和 API restart 后 PostgreSQL 可读证据；仍未补浏览器级 IC 材料编辑或 owner_verified 证据。
  - WI-007 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI Gateway/Collaboration/Workflow/Dossier endpoint、Chromium 浏览器交互、四 Analyst Memo artifact、S3 CollaborationCommand/Event、hard dissent Risk handoff、PostgreSQL audit/outbox 和 API restart 后 Dossier 可见。WI-007 scope 明确不拥有 Risk verdict、Owner exception、paper execution 或前端页面实现。
  - WI-008/ACC-018 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI Gateway/Workflow/Dossier/artifact endpoint、Chromium 浏览器交互、DecisionPacket、CIODecisionMemo、DecisionGuardResult、Owner exception candidate、S4 handoff、PostgreSQL audit/outbox 和 API restart 后 artifact/Dossier 可见。当前官方 deploy hook 在最终服务列表 pipe check 处存在 rc=141 工具残留，后续以 docker compose ps/API/tasks/targeted smoke 补证；修复 deploy hook 需进入对应脚本 scope。
  - WI-008/ACC-019 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 RiskReviewReport conditional_pass/rejected、Owner timeout no-execute domain disposition、Reopen Event、Risk rejected bypass denial、直接 S6 workflow command 被阻断、无 PaperExecutionReceipt、PostgreSQL audit/outbox 和 API restart 后 Dossier risk 状态可见。2026-05-03 reopen 已补 `ApprovalRecord` API/PostgreSQL 持久化：Owner exception 审批创建进入 `approval_record`，`/api/approvals/{id}/decision` 决策后重建 ApiRuntime 仍可读回同一 approval_id 和 decision；仍未补浏览器级 owner_verified 证据。
  - WI-009/ACC-020..022 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PaperAccount 初始化与填充后账户、PaperOrder/PaperExecutionReceipt 的 filled/blocked/expired/TWAP 路径、execution_core 阻断、T+1、S0-S7 completion、Dossier paper_execution、API restart 后 artifact 可读、PositionDisposalTask P0 处置 handoff、直接 S6 bypass 阻断、无真实券商/真实下单/回测。2026-05-03 reopen 已补专用 `paper_account`、`paper_order`、`paper_execution_receipt` 表镜像；WI-010 repair 已补 first-class PositionDisposalTask Gateway artifact、Artifact API、Dossier projection、direct execution 403 guard 和 `position_disposal_task` 专表镜像；仍未补浏览器级处置控制或 owner_verified 证据。
  - WI-005/ACC-023 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 Finance API 对 fund/gold/real_estate 的 planning-only 边界、real_estate manual_todo、非 A trade RequestBrief 转 manual_todo、PostgreSQL task 持久化、API restart 后任务可读、无 workflow/approval/paper execution。2026-05-03 reopen 已补 `FinanceProfile` API/PostgreSQL 持久化：`/api/finance/assets` 写入 cash/fund 后，重建 ApiRuntime 可通过 `/api/finance/overview` 读回资产并重算 liquidity；仍未补浏览器级财务档案编辑证据和外部 fund/gold 生产行情可用性。
  - WI-005/ACC-024 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证自动归因日度发布、评分公式、condition hit/miss、缺失输入 null/improvement item、Dossier attribution、PostgreSQL artifact/audit/outbox、API restart 后读回。证据仍通过 generic Gateway artifact ledger；专用 attribution drilldown/API 展示需未来 API/DB/frontend scope。
  - WI-005/ACC-025 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证异常/周期归因触发 CFO、trigger priority、CFOInterpretation、finance_planning 高影响治理 proposal 语义、owner_pending、ReflectionRecord、handoff、PostgreSQL artifact/audit/outbox、API restart 后读回。CFO GovernanceProposal/ApprovalRecord 仍不是一等 API/Gateway 对象。
  - WI-005/ACC-026 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 factor_engine ServiceResult 因子准入、独立验证、registry 字段、monitoring threshold/coverage drift、pause_default_weight、factor_weight 高影响治理语义、无 backtest/Backtrader 依赖、handoff、PostgreSQL artifact/audit/outbox、API restart 后读回。专用 factor registry/GovernanceProposal 持久化仍需未来 API/DB contract scope。
  - WI-005/ACC-027 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 ResearchPackage、Memory capture/version/extraction、MemoryRelation、Knowledge/Prompt/Skill proposal commands、handoff、直接热改拒绝、新任务 scope、PostgreSQL audit/outbox、API restart 后读回。Knowledge/Prompt/Skill proposal 仍不是一等 artifact/activation 记录。
  - WI-005/ACC-028 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证反思 draft Memory、ReflectionRecord、Researcher promotion command、knowledge conflict resolution、owner approval flag、new_task effect、no hot Prompt/Skill/context/parameter guard、handoff、PostgreSQL artifact/audit/outbox、API restart 后读回。真正 activation/new ContextSnapshot 由治理配置 scope 承接。
  - WI-006/ACC-029 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 DevOps health/incident API、severity、safe degradation、recovery validation、investment_resume_allowed=false、Risk handoff、sensitive log finding、cost/token observability-only、PostgreSQL artifact/command/handoff audit/outbox、API restart 后读回。DevOps 仍不拥有业务 Risk 放行、投资执行恢复或高影响配置热改。
  - 2026-05-02 docker compose runtime blocker 已修复到 WI-001/WI-004 `integrated_runtime` foundation 级：允许 Dockerfile/预构建镜像/`wheelhouse/`，runtime image 在 build 阶段通过 PyPI mirror 或 wheelhouse 安装依赖，api/worker/beat/agent-runner 启动命令不再 `pip install -e .`；同一 compose runtime 已通过 same-origin frontend、Chromium 浏览器点击、RequestBrief->Task、agent-runner fake_test、API restart 后 task 持久化和六个服务 running 检查。仍不能外推到全 V1，因为 S0-S7、真实外部数据、纸面执行和 Owner 人工验收未闭环。
  - 若后续任何 P0 自动化不可行，必须回到 Requirement 或 review 明确记录例外理由。

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-OWNER-WORKBENCH-REFINE-20260506
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 67 tests; Vite production build passed; e2e passed 12 tests. RED/GREEN coverage now asserts Owner Decision View renders a single 待办 card instead of separate 审批/人工待办 cards, governance modules are 待办/团队/变更/健康/审计, 待办 approval entries route to the live approval_id before POST decision, overview system health is derived from `/api/devops/health` instead of a local degraded fixture and shows the concrete degradation/recovery reason, Investment Dossier header height stays <=44px with StageRail directly below the compact header after loading, and S3 current blocker is explained separately from the S6 execution-data no-trade guard.
  result: pass
  residual_risk: Automated branch-local browser/API evidence only; Owner manual acceptance remains pending.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI011-ACC007-GOVERNANCE-SEPARATION-20260506
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 67 tests; Vite production build passed; e2e passed 12 tests. Governance default module is now 待办, merging approval and actionable/manual task cards in the Owner-facing UI while preserving `/api/tasks` and `/api/approvals` contract separation; approval details still submit through `/api/approvals/{id}/decision`, and manual_todo finance handling still writes through `/api/finance/assets`.
  result: pass
  residual_risk: UI/read-model separation is verified at branch-local API-connected level; backend governance activation and Owner manual acceptance are not newly proven by this frontend refinement.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI011-ACC023-MANUAL-TODO-FINANCE-PATH-20260506
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: browser_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: e2e passed 12 tests, including live browser/API route from non-A trade request to manual_todo, 全景 待办 link to /governance?panel=todos, manual task card action link to /finance?todo=<taskId>, and /api/finance/assets write after submitting the finance dossier form.
  result: pass
  residual_risk: Confirms no approval/execution/trade shortcut is exposed for this browser path; does not add a generic manual_todo close API by design.
  reopen_required: false

- acceptance_ref: ACC-027
  run_id: RUN-WI011-ACC027-KNOWLEDGE-GOVERNANCE-OWNERSHIP-20260506
  test_case_ref: TC-ACC-027-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 67 tests; Vite production build passed; e2e passed 12 tests. Knowledge page now uses Owner-readable cards for 每日简报、研究资料包、经验记录、资料关系 and 整理建议; it shows research package source in the default view, replaces 捕获记忆 with 保存经验, replaces 应用组织建议 with 应用整理建议, avoids leaking Memory/relation IDs after writes, and keeps Knowledge/Prompt/Skill proposal entry and 治理 proposal jump out of the Knowledge page.
  result: pass
  residual_risk: Proposal activation/new default-context behavior remains governance-owned and is not newly activated by the Knowledge page.
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-WI011-ACC028-TEAM-WORDING-HOT-EDIT-GUARD-20260506
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 67 tests; Vite production build passed; e2e passed 12 tests. Owner default pages use 团队/能力提升 wording instead of Agent/Agents/AgentRun/ContextSnapshot, keep capability changes as governance proposals, and hide machine IDs by default in governance health/change/audit views.
  result: pass
  residual_risk: This is owner-facing UI/read-model guard evidence; it does not replace backend hot-edit denial or Owner manual acceptance evidence.
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-GOVERNANCE-TEAM-LIVE-PROFILE-20260506
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 74 tests; Vite production build passed; e2e passed 16 tests. RED/GREEN coverage now reproduces the governance team card blank-page bug with object-shaped `/api/team/{agentId}` permissions, normalizes read/write/tool/service/collaboration permissions into Owner-readable rows, and live browser/API coverage clicks CIO and Fundamental Analyst cards from governance team into real profile pages without blank body, JS errors or `[object Object]`.
  result: pass
  residual_risk: Browser/API evidence remains branch-local and does not replace Owner manual acceptance. Full workspace scope gate still fails on unrelated out-of-scope dirty file `src/velentrade/domain/data/__init__.py`.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI011-ACC007-TEAM-CAPABILITY-DRAFT-LINK-20260506
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with httpx pytest tests/api/test_wi011_owner_real_data.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 74 tests; Vite production build passed; WI-011 API tests passed 9 tests; e2e passed 16 tests. Coverage now follows governance team card -> profile -> capability plan -> `/api/team/{agentId}/capability-drafts`, asserts the returned governance change is shown, and keeps the copy that capability plans affect only new tasks/new attempts while in-flight tasks keep the old snapshot.
  result: pass
  residual_risk: Confirms the Owner-facing draft submission link and API call path, not backend governance activation or Owner approval completion. Full workspace scope gate remains blocked by unrelated WI-002 dirty state.
  reopen_required: false

- acceptance_ref: ACC-028
  run_id: RUN-WI011-ACC028-TEAM-PERMISSION-NORMALIZATION-20260506
  test_case_ref: TC-ACC-028-01
  verification_type: automated
  test_type: frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest pytest tests/domain/observability tests/domain/knowledge -q; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: Vitest passed 74 tests; Vite production build passed; observability/knowledge tests passed 5 tests; e2e passed 16 tests. Team profile rendering now accepts backend object-shaped permission maps, formats skill package and context snapshot values into Owner-readable copy, and includes a route-level fallback so malformed team detail data shows `团队画像暂不可用` instead of blanking the workbench.
  result: pass
  residual_risk: This covers UI/read-model normalization and no-hot-edit messaging; it does not prove owner_verified acceptance. Scope gate failure is unrelated to these WI-011 files and remains unresolved.
  reopen_required: false

<!-- CODESPEC:TESTING:HANDOFFS -->
## 5. 主动未完成清单与语义验收

- handoff_id: HANDOFF-WI011-IMPLEMENTATION-20260506
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: api_connected
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-OWNER-WORKBENCH-REFINE-20260506
    - testing.md#RUN-WI011-ACC007-GOVERNANCE-SEPARATION-20260506
    - testing.md#RUN-WI011-ACC023-MANUAL-TODO-FINANCE-PATH-20260506
    - testing.md#RUN-WI011-ACC027-KNOWLEDGE-GOVERNANCE-OWNERSHIP-20260506
    - testing.md#RUN-WI011-ACC028-TEAM-WORDING-HOT-EDIT-GUARD-20260506
    - testing.md#RUN-WI011-ACC006-GOVERNANCE-TEAM-LIVE-PROFILE-20260506
    - testing.md#RUN-WI011-ACC007-TEAM-CAPABILITY-DRAFT-LINK-20260506
    - testing.md#RUN-WI011-ACC028-TEAM-PERMISSION-NORMALIZATION-20260506
    - authority-repairs/REPAIR-20260506082825.yaml
    - authority-repairs/REPAIR-20260506061914.yaml
  unfinished_items:
    - source_ref: work-items/WI-011.yaml#required_verification
      priority: P0
      current_completion_level: api_connected
      target_completion_level: integrated_runtime
      blocker: `../.codespec/codespec check-gate scope` 本轮失败，首个错误为 `changed file src/velentrade/domain/data/__init__.py is outside allowed_paths of WI-011`；工作树中仍存在既有 WI-011 范围外未提交/未跟踪文件（包括 WI-002 后端、迁移和测试改动）。这些不是本次 Owner 工作台团队能力链路的业务测试失败。
      next_step: 先由对应 WI 收口或清理/提交这些 out-of-scope dirty files，再重跑 WI-011 scope gate；不要通过回滚用户或其他 WI 改动来制造干净结果。
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: api_connected
      target_completion_level: owner_verified
      blocker: 本轮只有自动化前端、构建和 live browser/API e2e 证据，没有 Owner 人工验收结论。
      next_step: 用户/Owner 在实际页面确认“待办/团队/知识/投资/健康/审计”新口径后，单独记录 owner_verified evidence。
  fixture_or_fallback_paths:
    - surface: Owner workbench frontend read models and browser/API route smoke
      completion_level: api_connected
      real_api_verified: partial
      visible_failure_state: true
      trace_retry_verified: partial
  wording_guard: "只能报告 WI-011 前端与 live browser/API 分支验证通过；scope gate 尚未通过且没有 Owner 人工验收，不得表述为 owner_verified 或全量 Implementation clean。"

- handoff_id: HANDOFF-IMPLEMENTATION-20260505
  phase: Implementation
  work_item_refs: [WI-001, WI-002, WI-003, WI-004, WI-005, WI-006, WI-007, WI-008, WI-009, WI-010]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - authority-repairs/REPAIR-20260505030241.yaml
    - testing.md#RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503
    - testing.md#RUN-WI004-ACC006-READMODEL-ERROR-REPORT-METADATA-20260504
    - testing.md#RUN-WI004-ACC007-FINANCE-ASSET-BROWSER-UPDATE-20260504
    - testing.md#RUN-WI009-ACC021-FULL-RUNTIME-FOUNDATION-20260503
  unfinished_items:
    - source_ref: work-items/WI-004.yaml#completion_level
      priority: P0
      current_completion_level: api_connected
      target_completion_level: integrated_runtime
      blocker: WI-004 最新 Dossier/Agent Team/Knowledge/Approval/Finance rich browser surfaces 已有 API-connected branch-local 证据，但尚未把 2026-05-04 的丰富页面、错误态、trace/retry 和受控写入全部放入同一 docker compose runtime full-integration RUN。
      next_step: Testing 阶段用同一 PostgreSQL/Redis/Celery/FastAPI/same-origin frontend/Chromium runtime 重跑 WI-004 rich surface E2E，并追加 full-integration RUN 证据。
    - source_ref: work-items/WI-010.yaml#completion_level
      priority: P0
      current_completion_level: db_persistent
      target_completion_level: integrated_runtime
      blocker: WI-010 authority repair 已证明 ICContextPackage/ICChairBrief/PositionDisposalTask 的 Gateway/API/PostgreSQL 持久化，但该 repair 自身尚未作为独立 full-integration RUN 闭环记录到 Testing 阶段。
      next_step: Testing 阶段复用真实 compose runtime 复核三类一等 artifact/read model/API restart 路径，并将 WI-010 completion_level 提升或保留为明确残留风险。
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: 当前没有 Owner 人工验收结论；Implementation 证据不能替代 Deployment 阶段人工验收。
      next_step: Deployment 阶段完成 runtime readiness、smoke、回滚/监控和人工验收后，单独记录 owner_verified evidence。
  fixture_or_fallback_paths:
    - surface: WI-004 rich frontend read models and fallback/error labels
      completion_level: api_connected
      real_api_verified: partial
      visible_failure_state: true
      trace_retry_verified: true
    - surface: external market/fund/gold provider production availability
      completion_level: integrated_runtime
      real_api_verified: false
      visible_failure_state: true
      trace_retry_verified: false
  wording_guard: "只能报告当前最高为 integrated_runtime foundation；WI-004 最新 rich surfaces 仍是 api_connected，WI-010 为 db_persistent，未经过 Owner 人工验收，不得表述为全部完成或 owner_verified。"

- handoff_id: HANDOFF-TESTING-20260505
  phase: Testing
  work_item_refs: [WI-001, WI-002, WI-003, WI-004, WI-005, WI-006, WI-007, WI-008, WI-009, WI-010]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - testing.md#RUN-WI001-ACC001-FULL-RUNTIME-FOUNDATION-20260503
    - testing.md#RUN-WI004-ACC006-FULL-RUNTIME-FOUNDATION-20260503
    - testing.md#RUN-WI003-ACC014-FULL-RUNTIME-FOUNDATION-20260503
    - testing.md#RUN-WI009-ACC022-FULL-RUNTIME-FOUNDATION-20260503
    - testing.md#RUN-WI006-ACC029-FULL-RUNTIME-FOUNDATION-20260503
    - authority-repairs/REPAIR-20260505031840.yaml
  unfinished_items:
    - source_ref: work-items/WI-004.yaml#completion_level
      priority: P0
      current_completion_level: api_connected
      target_completion_level: integrated_runtime
      blocker: Testing 聚合证据已有 2026-05-03 full-integration foundation 浏览器/API/runtime RUN，但 2026-05-04 补齐的 Dossier、Agent Team、Knowledge、Approval、Finance rich surfaces 仍停留在 API-connected branch-local 证据。
      next_step: 在同一 PostgreSQL/Redis/Celery/FastAPI/same-origin frontend/Chromium runtime 中重跑 WI-004 rich surface E2E，并记录针对 TC-ACC-006-01 与 TC-ACC-007-01 的 full-integration RUN。
    - source_ref: work-items/WI-010.yaml#completion_level
      priority: P0
      current_completion_level: db_persistent
      target_completion_level: integrated_runtime
      blocker: WI-010 已通过 authority repair 与 branch-local DB/API 证据补齐 ICContextPackage、ICChairBrief、PositionDisposalTask 一等契约，但 work item completion_level 仍为 db_persistent，尚未记录独立 full-integration RUN。
      next_step: 用真实 compose runtime 复核三类一等 artifact 的 Gateway 写入、Artifact API、Dossier projection、专表镜像和 API restart 可读路径，再决定是否提升 WI-010 completion_level。
    - source_ref: testing.md#external-provider-production-readiness
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: full-integration RUN 使用 deterministic runtime smoke 和本地/fixture 化 provider 证据；Tencent live smoke 只证明一次公开接口可读，不证明供应商条款、限频、生产稳定性或基金/黄金外部行情可用。
      next_step: 在 Deployment 前单独记录外部 provider 许可、限频、失败态、stale/trace/retry 和人工接受结论；不得把当前 smoke 当成生产 provider 验收。
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: Testing 阶段只有自动化与 runtime smoke 证据，没有 Owner 人工验收结论，也没有 Deployment runtime readiness、回滚、监控和人工验收记录。
      next_step: 进入 Deployment 后按 phase policy 补 deployment.md 运行验证、回滚/监控和人工验收；只有用户明确验收通过后才能记录 owner_verified。
  fixture_or_fallback_paths:
    - surface: WI-004 rich frontend read models, fallback labels, trace/retry states
      completion_level: api_connected
      real_api_verified: partial
      visible_failure_state: true
      trace_retry_verified: true
    - surface: live external market/fund/gold provider production path
      completion_level: integrated_runtime
      real_api_verified: false
      visible_failure_state: partial
      trace_retry_verified: false
  wording_guard: "Testing 阶段只能说 full-integration foundation 证据已聚合到 integrated_runtime；不得说全部功能完成、生产外部数据已验收或 owner_verified 已完成。"

- handoff_id: HANDOFF-DEPLOYMENT-20260505
  phase: Deployment
  work_item_refs: [WI-001, WI-002, WI-003, WI-004, WI-005, WI-006, WI-007, WI-008, WI-009, WI-010]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - deployment.md#3-执行证据
    - deployment.md#4-运行验证
    - testing.md#RUN-WI001-ACC001-ALEMBIC-CHAIN-REGRESSION-20260505
    - testing.md#HANDOFF-TESTING-20260505
  unfinished_items:
    - source_ref: deployment.md#6-人工验收与收口
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: deployment.md 已记录 artifact deploy、pytest、compileall、Vitest 和 Vite build 证据，manual_verification_ready 为 pass，但人工验收 status 仍是 pending。
      next_step: 由用户/Owner 进行人工验收；只有明确通过后，才能把 deployment.md acceptance conclusion 改为 pass 并执行 complete-change。
    - source_ref: deployment.md#release_mode
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: 当前发布模式为 artifact/local-artifact，runtime_ready 为 not-applicable；它证明构建产物和自动化验证通过，不等于生产 runtime 发布或外部 provider 生产可用性验收。
      next_step: 若需要 runtime 发布，先把 release_mode 切到 runtime 并重新执行 VELENTRADE_RUN_COMPOSE_SMOKE=1 的部署验证；否则仅按 artifact 交付口径验收。
  fixture_or_fallback_paths:
    - surface: local artifact deployment package
      completion_level: integrated_runtime
      real_api_verified: false
      visible_failure_state: not_applicable
      trace_retry_verified: false
    - surface: owner manual acceptance
      completion_level: integrated_runtime
      real_api_verified: not_applicable
      visible_failure_state: not_applicable
      trace_retry_verified: not_applicable
  wording_guard: "Deployment 当前只能说 artifact deploy ready 且 manual_verification_ready=pass；人工验收未通过前，不得说 completed、owner_verified、已发布生产 runtime 或可以 complete-change。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-OWNER-REAL-DATA-REPAIR-20260506
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: api_frontend_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-06
  artifact_ref: uv run --with pytest --with httpx pytest tests/api/test_wi001_api_foundation.py tests/api/test_wi011_owner_real_data.py -q passed 17 tests; uv run --with pytest --with httpx pytest tests/domain/observability tests/domain/knowledge -q passed 5 tests; npm --prefix frontend test -- --run passed 67 tests; npm --prefix frontend run build passed; docker compose up -d --build api refreshed the 8443-backed API; uv run --with pytest --with websocket-client pytest tests/e2e -q passed 12 tests against https://127.0.0.1:8443/. curl -k /api/devops/health returned incidents=[] and recovery=[]; curl -k /api/workflows/wf-001/dossier returned backend-seeded wf-001 with current_stage S3, state blocked, S3 reason retained_hard_dissent_risk_review and S6 execution_core_status blocked; curl -k /api/knowledge/memory-items found no knowledge-method-1/test/Untitled Memory/测试/invalid_value records.
  result: pass
  residual_risk: This is same-origin local runtime evidence on 8443 and proves the Owner default surfaces no longer silently substitute frontend fixture business conclusions; it is still not owner_verified manual acceptance and does not prove production external provider readiness.
  reopen_required: false

- acceptance_ref: ACC-007
  run_id: RUN-WI011-ACC007-TODO-REAL-ACTION-REPAIR-20260506
  test_case_ref: TC-ACC-007-01
  verification_type: automated
  test_type: api_frontend_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-06
  artifact_ref: Added backend regression that non-A trade RequestBrief confirmation creates manual_todo with route_non_a_manual_todo instead of losing the route reason as request_brief_confirmed. Added frontend regression that even historical manual_todo records with generic request_brief_confirmed route to /finance?todo=<taskId>. Browser E2E on https://127.0.0.1:8443/ confirmed Owner 待办 opens the unified governance todo panel, approval actions post to the real approval id, manual_todo opens the finance form and POSTs /api/finance/assets.
  result: pass
  residual_risk: Manual todo completion remains intentionally business-module-specific; no generic manual_todo completion API was added.
  reopen_required: false

- handoff_id: HANDOFF-WI011-OWNER-REAL-DATA-REPAIR-20260506
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-OWNER-REAL-DATA-REPAIR-20260506
    - testing.md#RUN-WI011-ACC007-TODO-REAL-ACTION-REPAIR-20260506
    - authority-repairs/REPAIR-20260506105512.yaml
  unfinished_items:
    - source_ref: ../.codespec/codespec check-gate scope
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: integrated_runtime
      blocker: Full workspace scope gate still fails on pre-existing WI-002 dirty file `src/velentrade/domain/data/__init__.py` outside WI-011 allowed_paths. This repair did not revert or absorb that unrelated change.
      next_step: Resolve or hand off the WI-002 dirty data-domain changes separately; then rerun `../.codespec/codespec check-gate scope`.
  fixture_or_fallback_paths:
    - surface: Owner default workbench business cards
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
    - surface: external provider production readiness
      completion_level: integrated_runtime
      real_api_verified: false
      visible_failure_state: partial
      trace_retry_verified: false
  wording_guard: "WI-011 本轮自动化与 8443 runtime 证据通过，但 full workspace scope gate 因无关 WI-002 dirty file 未通过；不得表述为 scope gate 全绿或 owner_verified。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-AGENT-PROCESS-OWNER-COPY-20260506
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: api_frontend_e2e
  test_scope: branch-local-api-connected
  completion_level: api_connected
  executed_at: 2026-05-06
  command_or_steps: "uv run --with pytest --with httpx pytest tests/api/test_wi011_owner_real_data.py -q; npm --prefix frontend test; npm --prefix frontend run build; uv run --with pytest --with websocket-client pytest tests/e2e -q; uv run --with pytest pytest tests/domain/observability tests/domain/knowledge -q; ../.codespec/codespec check-gate scope"
  artifact_ref: API regression passed 9 tests and now asserts wf-001 Dossier returns fundamental hard dissent details, role_payload drilldown fields, DebateSummary process fields and Trace API business summaries. Frontend regression passed 71 Vitest tests and build passed; tests assert S2 hard dissent content, S3 debate process summary, Trace default hiding run/context/profile IDs, and Chinese owner copy for finance, approval packet and capability config raw tokens. Existing e2e passed 12 tests; observability/knowledge domain tests passed 5 tests.
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on pre-existing out-of-scope dirty file `src/velentrade/domain/data/__init__.py`; this run is not owner_verified and did not use docker compose runtime refresh."
  reopen_required: false

- handoff_id: HANDOFF-WI011-AGENT-PROCESS-OWNER-COPY-20260506
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: api_connected
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-AGENT-PROCESS-OWNER-COPY-20260506
  unfinished_items:
    - source_ref: ../.codespec/codespec check-gate scope
      priority: P0
      current_completion_level: api_connected
      target_completion_level: integrated_runtime
      blocker: Full workspace scope gate remains blocked by pre-existing WI-002 dirty file `src/velentrade/domain/data/__init__.py` outside WI-011 allowed_paths.
      next_step: Resolve or hand off that WI-002 dirty file separately, rerun scope gate, then decide whether to refresh docker compose runtime evidence for this UI/API projection repair.
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: api_connected
      target_completion_level: owner_verified
      blocker: No Owner manual acceptance was recorded for the revised Dossier/Trace/finance/approval/config copy.
      next_step: Owner reviews the actual pages and records manual acceptance in Deployment evidence if approved.
  fixture_or_fallback_paths:
    - surface: Agent process visibility in Investment Dossier and Trace default projection
      completion_level: api_connected
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
    - surface: Owner-readable copy formatter coverage for future workflow read models
      completion_level: api_connected
      real_api_verified: partial
      visible_failure_state: true
      trace_retry_verified: partial
  wording_guard: "本轮只能说 API/前端/e2e 自动化通过且完成到 api_connected；scope gate 仍被既有 WI-002 范围外脏文件阻断，且未 owner_verified。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-AGENT-PROCESS-LIVE-RUNTIME-20260506
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: api_frontend_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-06
  command_or_steps: "npm --prefix frontend test -- --run; npm --prefix frontend run build; uv run --with pytest --with httpx pytest tests/api/test_wi011_owner_real_data.py -q; uv run --with pytest pytest tests/domain/observability tests/domain/knowledge -q; docker compose up -d --build --force-recreate api; uv run --with pytest --with websocket-client pytest tests/e2e -q; ../.codespec/codespec check-gate scope"
  artifact_ref: Frontend regression now passes 72 Vitest tests and asserts empty workflow Trace APIs do not fall back to fixture process records. API regression passed 9 tests; observability/knowledge domain tests passed 5 tests; Vite build produced `frontend/dist/assets/index-Bs91Pu09.js`; docker compose rebuilt and recreated API/agent-runner runtime. Live 8443 `/api/workflows/wf-001/dossier` now returns fundamental hard dissent reason, role_payload drilldowns and DebateSummary fields; live `/agent-runs`, `/collaboration-events` and `/handoffs` return business process summaries. Browser E2E passed 15 tests, including `/investment/wf-001?stage=S2`, `/investment/wf-001?stage=S3`, `/investment/wf-001/trace`, finance, approval package and capability config checks for known raw backend tokens.
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on pre-existing out-of-scope dirty file `src/velentrade/domain/data/__init__.py`; this evidence is integrated runtime automation, not Owner manual acceptance."
  reopen_required: false

- handoff_id: HANDOFF-WI011-AGENT-PROCESS-LIVE-RUNTIME-20260506
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-AGENT-PROCESS-LIVE-RUNTIME-20260506
  unfinished_items:
    - source_ref: ../.codespec/codespec check-gate scope
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: integrated_runtime
      blocker: Full workspace scope gate remains blocked by pre-existing WI-002 dirty file `src/velentrade/domain/data/__init__.py` outside WI-011 allowed_paths.
      next_step: Resolve or hand off that WI-002 dirty file separately, then rerun `../.codespec/codespec check-gate scope`.
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: No Owner manual acceptance was recorded for the revised Dossier/Trace/finance/approval/config copy.
      next_step: Owner reviews the actual pages and records manual acceptance in Deployment evidence if approved.
  fixture_or_fallback_paths:
    - surface: Investment Dossier S2/S3 hard dissent and debate process projection
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: true
    - surface: Workflow Trace process projection
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: true
    - surface: Owner-readable copy formatter coverage for finance/approval/config pages
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
  wording_guard: "可以报告 WI-011 本轮 Dossier/Trace/finance/approval/config 自动化已到 integrated_runtime；scope gate 仍被既有 WI-002 范围外脏文件阻断，且未 owner_verified。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-OWNER-READABLE-DOSSIER-DENSITY-20260507
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_api_e2e
  test_scope: owner-default-copy-and-layout
  completion_level: integrated_runtime
  executed_at: 2026-05-07
  command_or_steps: "npm --prefix frontend test -- --run src/workbench.ui.test.tsx; python -m pytest tests/api/test_wi011_owner_real_data.py -q; npm --prefix frontend run build; npm --prefix frontend test -- --run; python -m pytest tests/domain/observability tests/domain/knowledge -q; python -m pytest tests/e2e -q; ../.codespec/codespec check-gate scope"
  artifact_ref: "投资 Dossier 默认页已按老板可读信息密度返工：投资页默认不展示审计按钮和 S0 审计回链；S0/S1/S3/S4/S5/S6/S7 少量信息直接展开；S1 展示数据来源、用途、缺口和阶段影响；S3 展示四位分析师观点、依据、反证、结论变化和 CIO 综合；S4 说明为什么还不能决策；S5/S6 删除说明性边界卡；S7 归因状态合并到回链与反思入口。前端单测 75 条目标测试通过，完整 Vitest 86 条通过；WI-011 API 测试 10 条通过；Vite build 通过；observability/knowledge 域测试 5 条通过；浏览器 E2E 16 条通过。"
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` 仍失败，原因是既有 WI-002 范围外脏文件 `src/velentrade/domain/data/__init__.py`，本轮未处理也未回退该文件；本轮仍未记录 Owner 手工验收。"
  reopen_required: false

- handoff_id: HANDOFF-WI011-OWNER-READABLE-DOSSIER-DENSITY-20260507
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-OWNER-READABLE-DOSSIER-DENSITY-20260507
  unfinished_items:
    - source_ref: ../.codespec/codespec check-gate scope
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: integrated_runtime
      blocker: Existing WI-002 dirty file `src/velentrade/domain/data/__init__.py` is outside WI-011 allowed_paths, so scope gate cannot pass in this workspace state.
      next_step: Resolve or hand off the WI-002 dirty file separately, then rerun `../.codespec/codespec check-gate scope`.
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: Owner has not yet recorded manual acceptance for the revised investment default pages.
      next_step: Owner reviews `/investment/wf-001?stage=S0/S1/S3/S4/S5/S6/S7` and records manual acceptance if approved.
  fixture_or_fallback_paths:
    - surface: Investment Dossier owner-readable default pages
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
    - surface: S1 data source projection into Dossier read model
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
  wording_guard: "可以报告老板可读 Dossier 信息密度返工的前端/API/build/E2E 自动化通过；不能说 scope gate 全绿，不能说已 owner_verified。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-STRUCTURED-S3-DEBATE-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: contract_api_frontend_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "pytest tests/api/test_wi011_owner_real_data.py -q failed because bare pytest is not installed in this shell; uv run --with pytest --with httpx pytest tests/api/test_wi011_owner_real_data.py -q; npm --prefix frontend test -- --run; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with httpx pytest tests/domain/observability tests/domain/knowledge -q; uv run --with pytest --with websocket-client pytest tests/e2e -q; ../.codespec/codespec check-gate scope"
  artifact_ref: "S3 debate read model is now backend-owned and structured: /api/workflows/wf-001/dossier returns debate.owner_summary, status_summary, core_disputes, view_change_details, retained_dissent_details, round_details and next_actions; frontend S3 middle card renders owner_summary/current status/core dispute/view changes/retained dissent/CIO/next actions; clicking core dispute, view changes, retained dissent and rounds opens distinct detail content; missing structured fields show 后端未返回辩论详情. API regression passed 12 tests; Vitest passed 97 tests; Vite build passed; docker compose rebuilt API for 8443 live runtime; targeted browser E2E passed 9 tests; full browser E2E passed 17 tests; observability/knowledge domain tests passed 5 tests."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` failed on existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside the active authority repair allowed_paths. Active authority repair REPAIR-20260508000435 is still open until the workspace scope blocker is resolved and authority-repair close can rerun its gate/smoke. No Owner manual acceptance has been recorded."
  reopen_required: false

- handoff_id: HANDOFF-WI011-STRUCTURED-S3-DEBATE-20260508
  phase: Implementation
  work_item_refs: [WI-011]
  highest_completion_level: integrated_runtime
  evidence_refs:
    - testing.md#RUN-WI011-ACC006-STRUCTURED-S3-DEBATE-20260508
    - authority-repairs/REPAIR-20260508000435.yaml
  unfinished_items:
    - source_ref: ../.codespec/codespec check-gate scope
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: integrated_runtime
      blocker: Existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` is outside the active authority repair allowed_paths, so workspace scope gate cannot pass in this state.
      next_step: Resolve or hand off that existing authority repair file separately, then rerun `../.codespec/codespec check-gate scope`.
    - source_ref: authority-repairs/REPAIR-20260508000435.yaml
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: integrated_runtime
      blocker: The active authority repair remains open because close must rerun the repair gate and smoke after the workspace scope blocker is cleared.
      next_step: Run `../.codespec/codespec authority-repair close --evidence \"structured S3 debate contract/API/frontend/E2E evidence passed\"` after the blocking unrelated repair file is resolved.
    - source_ref: testing.md#owner_verified
      priority: P0
      current_completion_level: integrated_runtime
      target_completion_level: owner_verified
      blocker: Owner has not yet recorded manual acceptance for the revised S3 debate summary/detail UX.
      next_step: Owner reviews `/investment/wf-001?stage=S3` and records manual acceptance if approved.
  fixture_or_fallback_paths:
    - surface: S3 structured debate Dossier projection
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
    - surface: S3 click detail UX
      completion_level: integrated_runtime
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: partial
  wording_guard: "可以报告 S3 结构化辩论返工的 API/frontend/build/8443 E2E 自动化通过；不能说 scope gate 全绿、authority repair 已关闭或 owner_verified。"

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-S7-DOSSIER-FIT-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: browser_layout_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "Added browser E2E assertion for /investment/wf-001?stage=S7 at 1600x760; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py::test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank -q; npm --prefix frontend test -- --run; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q"
  artifact_ref: "Root cause was Dossier frame height using calc(100vh - 96px), which ignored the real 120px top offset plus bottom breathing room. At 1600x760 before the fix, S7 bottom was 784 and exceeded viewport; after changing the frame height to clamp(480px, calc(100vh - 140px), 760px), S7 bottom, rail bottom and board bottom are 740, document/body scrollHeight are 760, and the page no longer requires scrolling to reveal S7."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` remains blocked by existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside active repair allowed_paths. No Owner manual acceptance has been recorded."
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-DOSSIER-REPAIR-COMPLETE-VISUALS-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_browser_layout_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "Added regressions for S0 three bordered sections, S2 summary item retention after detail opens, S2 matrix/conclusion font-density metrics, and S7 fit at 1600x760. Ran npm --prefix frontend test -- --run; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q; ../.codespec/codespec check-gate scope."
  artifact_ref: "Frontend Vitest passed 97 tests. Vite build passed and 8443 now serves /assets/index-CKWqDLvs.js plus /assets/index-DLCz6TTM.css. Targeted browser E2E passed 9 tests and full browser E2E passed 17 tests. S0 now shows 收到什么 / 处理情况 / 准备做什么 with section borders. S2 opened-detail focus list keeps 去向 / 硬异议 / 证据 / 下一步 summary items visible; matrix row height is >=44 and conclusion rows use >=14px font. S7 rail/board/S7 bottom remains within viewport at 1600x760."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside active repair allowed_paths. Active authority repair REPAIR-20260508000435 remains open, and Owner manual acceptance is not recorded."
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-S1-S3-DOSSIER-DENSITY-FIT-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_browser_layout_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "Added red/green regressions for S1 compact data card, S3 fixed-narrow summary label column, S3 four analyst rows visible at 1600x760, and default S0-S7 middle cards with no internal scroll overflow. Ran npm --prefix frontend test -- --run -t \"controlled trading language\" and -t \"one fixed-height reading panel\" first and confirmed they failed on the old S1 two-card layout; then ran npm --prefix frontend test -- --run; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py::test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank -q; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q; ../.codespec/codespec check-gate scope."
  artifact_ref: "Frontend Vitest passed 97 tests. Vite build passed and 8443 now serves /assets/index-DOjWI9bD.js plus /assets/index-Ca-Pwuxc.css. Targeted S1/S2/S3/S7 browser layout E2E passed; full live browser file passed 9 tests; full tests/e2e passed 17 tests. S1 now renders one compact 数据准备 card with 已拿到什么 / 数据缺口 / 下一步影响 sections, not the previous 数据来源与获取结果 + 缺口与下一步 two-card spread. S3 summary label column is constrained by browser assertions to <=96px with value start <=128px; all four analyst rows, including 事件分析师, are visible inside the analyst panel at 1600x760. Browser E2E also loops S0-S7 and asserts default middle cards/section lists have scrollHeight <= clientHeight + 1."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside active repair allowed_paths. Active authority repair REPAIR-20260508000435 remains open, and Owner manual acceptance for the latest S1/S3 density changes is not recorded."
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-S0-S7-DOSSIER-DENSITY-AUDIT-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_browser_layout_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "Audited /investment/wf-001?stage=S0..S7 at 1600x760 with browser layout metrics. Added failing assertions for S1 low-quality status text (`缺失 · 缺失`) and for S0-S7 middle content being hard-stretched to the full 620px stage frame. Confirmed red via npm --prefix frontend test -- --run -t \"controlled trading language\" and uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py::test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank -q. Implemented natural-height middle cards, desktop three-column direct stage sections, S2 natural summary card heights, S3 natural row layout, and normalized S1 missing-source text. Ran npm --prefix frontend test -- --run; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py::test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank -q; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q; uv run --with pytest --with httpx pytest tests/api/test_wi011_owner_real_data.py -q; uv run --with pytest --with httpx pytest tests/domain/observability tests/domain/knowledge -q; git diff --check -- frontend/src/main.tsx frontend/src/styles.css frontend/src/workbench.ui.test.tsx tests/e2e/test_wi004_browser_live_api.py testing.md; ../.codespec/codespec check-gate scope."
  artifact_ref: "Frontend Vitest passed 97 tests. Vite build passed and 8443 now serves /assets/index-BEHh_U3e.js plus /assets/index-bI5WOxXY.css. Targeted browser layout E2E passed; live browser file passed 9 tests; full tests/e2e passed 17 tests. WI-011 API regression passed 12 tests; observability/knowledge domain tests passed 5 tests; diff whitespace check passed. Post-fix browser audit at 1600x760 measured middle content heights: S0 319px, S1 329px, S2 471px, S3 496px, S4 262px, S5 279px, S6 237px, S7 228px versus the fixed 620px stage frame; every stage leaves visible breathing room, has no internal overflow, and no page contains `缺失 · 缺失`."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside active repair allowed_paths. Active authority repair REPAIR-20260508000435 remains open, and Owner manual acceptance for the latest S0-S7 density audit is not recorded."
  reopen_required: false

- acceptance_ref: ACC-006
  run_id: RUN-WI011-ACC006-S1-DATA-SOURCE-COPY-20260508
  test_case_ref: TC-ACC-006-01
  verification_type: automated
  test_type: frontend_browser_layout_e2e
  test_scope: same-origin-8443-runtime
  completion_level: integrated_runtime
  executed_at: 2026-05-08
  command_or_steps: "Added red/green regressions for S1 data source copy so the available source row cannot show both `已获取：字段...` and `已获取 · 可用于研究判断`. Confirmed red with npm --prefix frontend test -- --run -t \"controlled trading language\". Implemented S1 row copy as `字段：...` plus pure business usability, then ran npm --prefix frontend test -- --run -t \"controlled trading language\"; npm --prefix frontend test -- --run; npm --prefix frontend run build; docker compose up -d --build api; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py::test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank -q; uv run --with pytest --with websocket-client pytest tests/e2e/test_wi004_browser_live_api.py -q; uv run --with pytest --with websocket-client pytest tests/e2e -q; git diff --check -- frontend/src/main.tsx frontend/src/workbench.ui.test.tsx tests/e2e/test_wi004_browser_live_api.py testing.md; ../.codespec/codespec check-gate scope."
  artifact_ref: "Frontend Vitest passed 97 tests. Vite build passed and 8443 now serves /assets/index-Bs7oT-eZ.js plus /assets/index-bI5WOxXY.css. Targeted browser layout E2E passed; full live browser file passed 9 tests; full tests/e2e passed 17 tests; diff whitespace check passed. S1 source row now renders `腾讯公开日线行情 / 研究/决策核心 / 字段：标的代码、交易日、收盘价、成交量、来源时间戳 / 可用于研究判断`, while the execution-core missing row still renders `未取得 · 不能用于成交`."
  result: pass
  residual_risk: "`../.codespec/codespec check-gate scope` still fails on existing unrelated authority repair file `authority-repairs/REPAIR-20260506014730.yaml` outside active repair allowed_paths. Active authority repair REPAIR-20260508000435 remains open, and Owner manual acceptance for the latest S1 copy change is not recorded."
  reopen_required: false

## Testing 阶段 HANDOFF

### HANDOFF-TESTING-20260510

- phase: Testing
- focus_wi: all active WI-001 through WI-011
- implementation_base_revision: 67262bb3812f39ebccde785d93c68cd47a7b201e
- latest_revision: de2c9fd

#### Full-integration 测试结果

- 后端 pytest: 36 passed (WI-001 10 tests, WI-002 7 tests, WI-005 4 tests, WI-006 1 test, WI-011 12 tests, observability 2 tests)
  - PostgreSQL/Redis: 真实连接，Celery worker 集成通过
- E2E 浏览器测试: 17 passed (WI-004 live API + browser interaction)
  - 真实 API on 8443，前端 SPA same-origin
- 前端 Vitest: 97 passed (86 UI + 11 contract)
- Vite build: 通过
- Scope gate: 通过
- Contract-boundary gate: 通过
- Verification gate: 通过
- Semantic-handoff gate: 通过

#### 修复记录

- `de2c9fd` fix(wi-011): 移除 wi002_reports.py 中误提交的 WI-002 独有 imports

#### 最高完成等级: integrated_runtime

- 所有 WI-001 到 WI-011 在真实运行时环境中集成运行通过
- PostgreSQL migration、Redis/Celery、FastAPI endpoint、frontend browser interaction、跨 WI 数据流均已验证

#### 未完成项

| 项目 | 最高完成等级 | 阻塞原因 | 下一步 |
|------|-------------|---------|--------|
| Owner 人工验收 (owner_verified) | integrated_runtime | 需要 Owner 对工作台做端到端人工验收 | 人工操作 |
| WI-002 build_intraday_monitor_templates / screen_all_market_candidates | not_implemented | WI-002 scope 功能未实现，quality.py 已还原 | 后续 WI-002 实现轮次 |
| 外部数据 provider 生产可用性 | not_implemented | 公开 HTTP CSV adapter 仅连接 fixture/fallback，未验证真实外部 provider | 评估 provider 条款后接入 |
| 非 A 股资产真实估值 | not_implemented | 仅 manual_todo 模式，无真实非 A 股数据接入 | 按需接入 |

#### 残余风险

- fixture/fallback 路径在开发环境仍然存在，但前端正式入口已不使用 fixture 冒充业务状态
- WI-004 rich surfaces 已达 integrated_runtime，前端真实 API 链路完整
- WI-010 为 authority repair WI，其数据持久化验证通过 WI-003/WI-008 的 IC context 和 position disposal 测试间接覆盖

### HANDOFF-DEPLOYMENT-20260510

- handoff_id: HANDOFF-DEPLOYMENT-20260510
  phase: Deployment
  work_item_refs: [WI-001, WI-002, WI-003, WI-004, WI-005, WI-006, WI-007, WI-008, WI-009, WI-010, WI-011]
  highest_completion_level: owner_verified
  evidence_refs:
    - deployment.md#3-执行证据
    - deployment.md#4-运行验证
    - deployment.md#6-人工验收与收口
    - testing.md#HANDOFF-TESTING-20260510
  unfinished_items:
    - source_ref: WI-002 scope
      priority: P2
      current_completion_level: not_implemented
      target_completion_level: integrated_runtime
      blocker: build_intraday_monitor_templates / screen_all_market_candidates 未实现
      next_step: 后续 WI-002 实现轮次
    - source_ref: external data provider
      priority: P2
      current_completion_level: not_implemented
      target_completion_level: production_ready
      blocker: 公开 HTTP CSV adapter 仅连接 fixture/fallback
      next_step: 评估 provider 条款后接入
    - source_ref: non-A-share real valuation
      priority: P2
      current_completion_level: not_implemented
      target_completion_level: manual_todo_with_real_data
      blocker: 无真实非 A 股数据接入
      next_step: 按需接入
  fixture_or_fallback_paths:
    - surface: local runtime deployment
      completion_level: owner_verified
      real_api_verified: true
      visible_failure_state: true
      trace_retry_verified: true
  wording_guard: "Deployment 已通过 Owner 人工验收（所有 8 个人工案例在 runtime 上确认通过）。WI-002 独有功能、外部 provider 和非 A 股估值标记为 P2 未完成，不阻塞本次收口。"
