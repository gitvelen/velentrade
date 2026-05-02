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
- `in_memory_domain`: 部分 domain dataclass 行为可由现有测试支撑，但尚未逐 RUN 复核升级。
- `api_connected`: 已完成 WI-001/WI-004 foundation 级证据；`FastAPI` app/router、`/api/team`、`/api/gateway/*`、`/api/collaboration/commands`、`/api/workflows/*`、`/api/knowledge/memory-items*`、`/api/tasks`、`/api/approvals`、`/api/governance/changes`、`/api/finance/overview`、`/api/devops/health` 已有自动化验证，但真实外部数据采集和跨 WI 浏览器到后端闭环仍未完成。
- `db_persistent`: 已完成 WI-001 foundation 级证据；`Alembic`、PostgreSQL schema、seed、Postgres smoke、API->DB mirror、Task/Workflow/WorkflowStage 持久化恢复已有自动化验证，但真实外部数据源 adapter 仍未接入。
- `integrated_runtime`: 未完成；已有 `docker-compose`、`Redis/Celery`、runtime smoke 和前端浏览器级交互验证，但尚无 PostgreSQL + Redis/Celery + API + 前端浏览器 + 跨 WI 数据流的闭环联调。
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
  statement: 治理下 Agent 团队工作区提交 Agent 能力、Prompt、SkillPackage、工具权限、模型路由或默认上下文配置只能生成治理变更草案；不得热改在途 AgentRun。

- invariant_id: INV-APPENDIX-NO-FORMAL-ID
  statement: appendices 不定义正式需求、验收或验证义务编号。

## 1.1 R8 runbook 验证补充

Design 修复后，以下 TC 不得只验证字段存在，必须验证 `trigger -> workflow/service/AgentRun/command -> artifact/event/handoff -> read model/view -> guard/report` 的完整链路。

- `TC-ACC-005-01` 必须执行 `FX-AGENT-COLLABORATION-PROTOCOL`：证明 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket、Authority Gateway、TraceDebugReadModel 能形成可回放协作链；命令必须覆盖 accepted/rejected/expired 至少两类结果。
- `TC-ACC-003-01` 必须执行 `FX-AGENT-CAPABILITY-DRAFT` 的只读部分：证明治理下 Agent 团队工作区九个 Agent 卡面、Agent 画像、版本、近期质量和越权/失败记录可见。
- `TC-ACC-006-01` 必须引用 `design-previews/frontend-workbench/` Markdown review pack 和 `index.html` 样式预览：证明一级主导航为 `全景 / 投资 / 财务 / 知识 / 治理`、团队不再作为一级菜单、Agent 团队位于治理下且可通过治理二级模块切换进入、route canonical parent 清晰、默认简体中文、漂亮优先且护眼其次的高端浅色卡面，Owner Decision View、Investment Dossier View 和 Trace/Debug 审计层分离，并用页面线框验证 Agent 协作展示不是长聊天 transcript。
- `TC-ACC-007-01` 必须验证任务中心、审批中心、manual_todo、变更管理、AgentCapabilityChange 和数据/服务健康在 UI/read model/API guard 三层分离。
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
  then: 每个 Agent 能力卡字段齐全且无禁用职责或越权能力；四位 Analyst 均具备独立数据域、工具、Skill、role_payload、rubric 和失败状态；治理下 Agent 团队工作区以中文卡面展示九个正式 Agent 的画像、版本、近期产物质量和失败/越权记录。
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
  scenario: Web 主导航、中文高端浅色卡面、治理下 Agent 团队工作区、三层可视化与自由对话命令路由。
  given: Web 测试环境、`FX-OWNER-COMMAND-TRIAGE`、`FX-HOT-EVENT-RESEARCH-TASK`、Owner attention 卡片、Dossier stage fixture、TeamReadModel fixture 和 Trace/Debug 入口 fixture。
  when: 打开主导航，提交投资调研、热点学习、审批、执行、规则、财务、系统和人工事项自然语言请求，并从 Owner Decision View drill down 到 Dossier、Knowledge/Research、Governance 与 Trace/Debug。
  then: 页面一级主导航存在 `全景 / 投资 / 财务 / 知识 / 治理` 且不包含团队；Dossier、Trace、Agent 画像、能力配置草案和审批包不作为一级菜单；主界面默认简体中文并采用漂亮优先、护眼其次的浅色高端卡面，主题使用暖瓷底色、墨色文字、玉绿主强调、靛蓝/暗金/胭脂红辅助色，卡片标题默认中文，不出现 Daily Brief、Task Center 等可中文化英文标题；Owner 默认卡片不展示非 A 股边界守卫、Prompt/Skill 版本、ContextSnapshot、trace_id、read model 等过程材料；治理页提供任务、审批、Agent 团队、变更、健康、审计二级模块切换，Agent 团队不只藏在卡片入口中；治理下 Agent 团队工作区展示九个 Agent 卡、胜任度、CFO 归因引用、能力短板和能力草案入口；Owner Decision View、Investment Dossier View 和 Trace/Debug 审计层分层清晰；卡片按“需处理事项、核心状态、支撑证据/健康/审计”的业务优先级排列；所有可动作请求先生成 Request Brief、任务卡或治理变更草案；Preview 显示 task_type、semantic lead、process authority、预期产物、阻断条件和审批可能性；热点学习默认生成 research_task，由 Researcher 承接，不显示审批/执行/交易入口；低置信或范围不清的输入停留 draft 并显示补充问题；Owner 卡片跳转到正确 Dossier/Knowledge/Approval/Health/治理 Agent 团队；StageRail 点击只改变 selected_stage 和 URL query，不推进 workflow。
  evidence_expectation: web_command_routing_report.json 包含 nav_assertions、chinese_ui_scan、premium_light_theme_assertions、owner_facing_content_assertions、governance_module_tabs_assertions、card_layout_order_assertions、governance_agent_team_assertions、three_layer_view_assertions、request_briefs、route_decisions、semantic_lead_assignments、task_cards、research_task_cards、draft_clarification_prompts、drilldown_routes、stage_rail_selection、trace_entry_return_path 和 blocked_direct_actions。
  status: planned

- tc_id: TC-ACC-007-01
  requirement_refs: [REQ-007]
  acceptance_ref: ACC-007
  verification_ref: VO-007
  work_item_refs: [WI-004]
  test_type: e2e
  verification_mode: automated
  required_stage: testing
  scenario: 任务中心、审批中心、manual_todo 与 Agent 能力配置草案隔离。
  given: 投资任务、research_task、非 A 股人工任务、Owner 例外审批任务、治理变更任务、团队页 Agent 能力配置草案、系统 incident、审批动作和财务敏感字段 fixture。
  when: 渲染治理区并推进任务状态，提交 `approved / rejected / request_changes`、Agent 能力草案和 Owner timeout 场景。
  then: 所有任务具备 Task Envelope；投资任务绑定 S0-S7 与 reason code；research_task 显示 Researcher、资料包/候选议题/补证状态且不进入审批/执行/交易链；治理变更和 Agent 能力配置草案进入治理状态机；低/中影响草案自动验证后只对新任务或新 attempt 生效，高影响草案进入 Owner 审批；incident 与 manual_todo 不进入审批/执行/交易链；Owner 审批材料包含对比分析、影响范围、替代方案和建议；审批提交后以后端状态刷新；财务敏感字段在 Dossier/Trace/非 CFO 视图只显示脱敏摘要；旧 in-flight AgentRun 继续引用旧 ContextSnapshot。
  evidence_expectation: governance_task_report.json 包含 task_envelope_states、status_mapping、research_task_isolation、semantic_lead_task_cards、governance_state_machine、agent_capability_draft_states、incident_state_mapping、manual_todo_isolation、approval_packet_completeness、approval_action_feedback、owner_timeout_ui_state、in_flight_snapshot_unchanged 和 finance_sensitive_redaction_ui；team_capability_config_report.json 包含 TeamReadModel、AgentProfileReadModel、AgentCapabilityConfigReadModel、草案提交、impact triage、自动验证/Owner 审批和热改拒绝。
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
  given: Data Domain Registry、Source Registry、Data Request、quality_score 为 0.95/0.85/0.65 的 `decision_core` 数据、关键字段最低分、当前 workflow 配置快照、`execution_core` 低于生效阈值、缓存命中和多源冲突 fixture。
  when: 执行数据就绪、切源、缓存使用、冲突归一和正式决策推进。
  then: 0.95 正常；0.85 只能 conditional_pass 并需 Owner 例外；0.65 先触发切源/fallback，仍不可恢复时阻断新决策/执行；关键字段最低有效分或 critical conflict 可覆盖综合均值并阻断；`execution_core` 低于当前生效阈值或 freshness fail 时严格阻断纸面执行；缓存不得生成新的执行授权。
  evidence_expectation: data_quality_degradation_report.json 包含 registry_contracts、data_request_schema、component_scores、quality_band_actions、critical_field_minimums、fallback_attempts、cache_decision_policy、conflict_resolution_report、workflow_config_snapshot、execution_core_effective_threshold、execution_core_freshness_gate、execution_core_block、risk_review_constraints、blocked_decisions 和 report_payload_contracts 要求的 guard_results。
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

- acceptance_ref: ACC-001
  run_id: RUN-WI001-ACC001-20260430
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
  residual_risk: Agent 团队 read model 已接 API；仍未证明 live browser 与 FastAPI 的端到端闭环。
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
  residual_risk: Headless Chromium opens Vite, clicks 自由对话 -> 生成请求预览 -> 确认生成任务卡, and verifies /api/tasks via live FastAPI; this run still does not include PostgreSQL/Redis/Celery in the same browser flow.
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

<!-- CODESPEC:TESTING:RISKS -->
## 4. 残留风险与返工判断

- residual_risk: medium
- reopen_required: false
- notes:
  - 本阶段已追加 WI-001/WI-004 的 `api_connected` 与 `db_persistent` 级实现证据；历史 `RUN-FULL-*` 仍仅为 `fixture_contract`。
  - Implementation 阶段必须按 `contracts/verification-report-schemas.md` 生成可复核 report artifact。
  - 公开 HTTP CSV 数据源 adapter 已达到 `in_memory_domain` 自动化验证；外网 live provider smoke、live browser -> FastAPI -> PostgreSQL/Redis/Celery 跨 WI 闭环和 Owner 人工验收仍未完成。
  - 2026-05-02 手工尝试 docker compose runtime smoke；postgres/redis 可启动，但 api/worker/beat/agent-runner 仍在容器启动时从 PyPI 安装依赖，`files.pythonhosted.org` 下载超时导致 runtime smoke 不可稳定完成。已追加 pip timeout/retry/cache 缓解，但若要可靠通过 integrated runtime，需要允许 Dockerfile/预构建镜像或本地 wheelhouse，不能继续声称 compose runtime 已完成。
  - 若后续任何 P0 自动化不可行，必须回到 Requirement 或 review 明确记录例外理由。
