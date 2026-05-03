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
  artifact_ref: CODESPEC_PROJECT_ROOT=$PWD CODESPEC_DEPLOY_RESULT_FILE=$(mktemp) VELENTRADE_RUN_COMPOSE_SMOKE=1 ./scripts/codespec-deploy at runtime_observed_revision=9b759ac0799115a7fac689e3b27ed97422686b8e; targeted WI-003 Python runtime smoke run_id=1777769530 workflow_id=workflow-a8fdebc689f2 brief_id=brief-284ebbe5813a topic_id=topic-p0-1777769530 api_research_artifact_id=artifact-3f001dbfc401 celery_agent_run_id=run-wi003-celery-1777769530 verified PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint /api/requests/briefs /api/gateway/artifacts /api/artifacts/{id}, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart; ACC-014 assertions covered IC Context Package refs, role attachments, evidence_missing_sections=[], evidence missing refs=[], persisted chair_brief payload, and no_preset_decision_attestation=true with no buy/sell/hold/买入/卖出/持有 preset.
  result: pass
  residual_risk: Chair Brief is persisted inside the ResearchPackage runtime artifact rather than as a separate API artifact type; adding first-class ICContextPackage/ICChairBrief write APIs would require a future WI scope expansion.
  reopen_required: false

- acceptance_ref: ACC-015
  run_id: RUN-WI007-ACC015-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-015-01
  verification_type: automated
  test_type: contract
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
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
  artifact_ref: python -m pytest tests/domain/decision tests/domain/investment/risk tests/domain/investment/owner_exception -q passed 13 tests; python -m compileall src/velentrade passed; compose runtime from WI-008 ACC-018 evidence stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI runtime workflow S0-S7 persistence after API restart already observed at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-008 risk runtime smoke run_id=1777771446 conditional_workflow_id=workflow-87cbeb782a22 conditional_brief_id=brief-1b374be44571 conditional_risk_artifact_id=artifact-adfcc24de9b2 conditional_handoff_id=handoff-8a7c55a1d2b7 owner_packet_candidate_id=decision-exception-e7edd5713d21 owner_approval_id=approval-risk-conditional-1777771446 owner_timeout_disposition=s6_blocked_no_execution rejected_workflow_id=workflow-331dedca03c5 rejected_brief_id=brief-26c48d6bd797 rejected_risk_artifact_id=artifact-12155b91cc3a reopen_event_id=reopen-97f615ba7ce7 risk_bypass_attempt=denied:risk_rejected_no_override s6_bypass_status=409 s6_bypass_reason_code=upstream_stage_not_completed db_counts={risk_review_artifacts:2,reopen_events:1,handoff_packets:3,paper_execution_conditional:0,paper_execution_rejected:0,audit_events_for_objects:3,outbox_events_for_keys:3} restart_check={api_restarted:true,conditional_risk_status:conditional_pass,rejected_risk_status:rejected}; ACC-019 assertions covered Risk approved/conditional/rejected domain states, conditional_pass Owner packet, Owner timeout no-execute disposition, rejected repairable Reopen Event target S4, rejected bypass denial, no PaperExecutionReceipt on blocked paths, workflow/API denial of direct S6 transition, and Dossier risk state visibility after API restart.
  result: pass
  residual_risk: Runtime persists RiskReviewReport, HandoffPacket and ReopenEvent, while Owner ApprovalRecord remains domain-level evidence because WI-008 has no allowed API/Gateway write path for creating approval records; first-class persisted Owner exception approval creation would require API/DB scope expansion.
  reopen_required: false

- acceptance_ref: ACC-020
  run_id: RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-020-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; compose runtime from WI-008 ACC-018 evidence stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow persistence foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-009 runtime smoke run_id=1777771944 execution_workflow_id=workflow-f8c2d9797fac execution_brief_id=brief-10169f128303 execution_task_id=task-87b33ce8f713 initial_account_ref=artifact-314c7d8facf5 updated_account_ref=artifact-50a9bde22130 account_initial={cash:1000000 CNY,positions:{},cash_ratio:1.0,benchmark_ref:baseline-cash} account_after_filled_buy={cash:987788.718 CNY,position_600000_SH_quantity:1200.0,available_quantity:0.0,t_plus_one_state:locked_until_next_trading_day,total_value:999994.878,return_value:-5.122}; db_counts={PaperAccount:2,PaperExecutionReceipt:4,PaperOrder:4,AnalystMemo:4,CIODecisionMemo:1,RiskReview:1,Attribution:1,DataReadiness:1,DecisionGuardResult:1,workflow_stage_statuses:{S0:completed,S1:completed,S2:completed,S3:completed,S4:completed,S5:completed,S6:completed,S7:completed},audit_events_for_refs:7,outbox_events_for_wi009_keys:{wi001.artifact:29,wi001.handoff:3}} restart_check={api_restarted:true,dossier_paper_execution_status:filled,initial_account_artifact_read_after_restart:true,updated_account_cash_after_restart:987788.718 CNY,filled_receipt_t_plus_one_after_restart:locked_until_next_trading_day}; ACC-020 assertions covered 1,000,000 CNY default PaperAccount initialization, empty positions, cash baseline, risk budget, PaperAccount persistence through FastAPI Gateway/PostgreSQL, account update from filled buy, T+1 locked availability, S6 completion, and artifact readability after API restart.
  result: pass
  residual_risk: Runtime persists PaperAccount through the generic Gateway artifact ledger using trade_execution; the dedicated paper_account table is present from DB foundation but not updated by this Gateway write path within WI-009 scope.
  reopen_required: false

- acceptance_ref: ACC-021
  run_id: RUN-WI009-ACC021-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-021-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; same docker compose runtime with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click, and cross-WI workflow runtime as RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503; targeted WI-009 paper execution smoke run_id=1777771944 workflow_id=workflow-f8c2d9797fac filled_receipt_ref=artifact-44353eb29f69 blocked_receipt_ref=artifact-2a64ae4f3c97 expired_receipt_ref=artifact-5c5b3a56b9b2 twap_receipt_ref=artifact-53bbbe990d1c filled_receipt={paper_order_id:paper-order-filled-1777771944,execution_window:2h,pricing_method:minute_vwap,fill_status:filled,fill_price:10.1718,fill_quantity:1200,fees:{commission:5.0,transfer:0.122},taxes:{stamp_tax:0},slippage:{policy_bps:5},t_plus_one_state:locked_until_next_trading_day} blocked_receipt={paper_order_id:paper-order-blocked-1777771944,execution_window:30m,fill_status:blocked,reason_code:execution_core_blocked,market_data_refs:[execution-core-blocked-1777771944]} expired_receipt={paper_order_id:paper-order-expired-1777771944,execution_window:30m,fill_status:expired,reason_code:price_range_not_hit} twap_receipt={paper_order_id:paper-order-twap-1777771944,execution_window:full_day,pricing_method:minute_twap,fill_status:filled,fill_price:10.3698,fill_quantity:100}; db_counts={receipt_statuses:{filled:2,blocked:1,expired:1},PaperOrder:4,PaperExecutionReceipt:4,S6:completed,S7:completed} restart_check={api_restarted:true,dossier_paper_execution_status:filled,dossier_pricing_method:minute_vwap,dossier_evidence_has_receipts:{filled:true,blocked:true,expired:true,twap:true},blocked_reason_after_restart:execution_core_blocked,expired_status_after_restart:expired,twap_pricing_after_restart:minute_twap}; ACC-021 assertions covered urgency windows, minute VWAP/TWAP, price range miss, fees/taxes/slippage, execution_core blocked no-fill, T+1 state, no real broker/order/backtest call, S6/S7 workflow completion, Dossier projection, and persisted receipt reads after API restart.
  result: pass
  residual_risk: Runtime persists PaperOrder and PaperExecutionReceipt through the generic Gateway artifact ledger and Dossier first-receipt projection; the dedicated paper_order/paper_execution_receipt tables are DB foundation tables but are not the current Gateway mirror target in WI-009 scope.
  reopen_required: false

- acceptance_ref: ACC-022
  run_id: RUN-WI009-ACC022-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-022-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/domain/investment/paper_account tests/domain/investment/execution tests/domain/investment/position -q passed 21 tests; python -m compileall src/velentrade passed; same docker compose runtime with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click, and cross-WI workflow runtime as RUN-WI009-ACC020-FULL-RUNTIME-FOUNDATION-20260503; targeted WI-009 position disposal smoke run_id=1777771944 disposal_workflow_id=workflow-59c312df57f6 disposal_brief_id=brief-77203704ec9e disposal_handoff_ref=handoff-047ddc203d99 disposal_task={task_id:position-disposal-0cefb6bff97e,symbol:600000.SH,triggers:[abnormal_volatility,major_announcement,risk_threshold_breach],priority:P0,risk_gate_present:true,execution_core_guard_present:true,direct_execution_allowed:false,workflow_route:S5_risk_review,reason_code:position_disposal_requires_risk_review} blocked_direct_s6_workflow_id=workflow-c7a3a0294dfd blocked_direct_s6_status=409 blocked_direct_s6_reason_code=upstream_stage_not_completed; db_counts={disposal_handoff_count:1,disposal_receipt_count:0,blocked_workflow_s6:{node_status:blocked,reason_code:upstream_stage_not_completed},audit_events_for_refs:7,outbox_events_for_wi009_keys:{wi001.artifact:29,wi001.handoff:3}} restart_check={api_restarted:true,disposal_risk_status_after_restart:approved,disposal_handoff_persisted:true}; ACC-022 assertions covered abnormal volatility/major announcement/risk threshold triggers, P0 escalation, PositionDisposalTask risk gate and execution_core guard fields, direct_execution_allowed=false, route back to S5 Risk Review via persisted handoff, no PaperExecutionReceipt on disposal workflow, and direct S6 bypass blocked by workflow guard.
  result: pass
  residual_risk: PositionDisposalTask remains represented as domain payload plus HandoffPacket because WI-009 has no allowed first-class PositionDisposalTask artifact/API/schema path; adding that projection would require expanding API/DB contract scope.
  reopen_required: false

- acceptance_ref: ACC-023
  run_id: RUN-WI005-ACC023-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-023-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 finance runtime smoke run_id=1777772442 finance_assets={fund:{asset_id:fund-wi005-1777772442,boundary_label:finance_planning_only,source:auto_quote},gold:{asset_id:gold-wi005-1777772442,boundary_label:finance_planning_only,source:auto_quote},real_estate:{asset_id:real_estate-wi005-1777772442,boundary_label:finance_planning_only,source:manual}} runtime_overview_manual_todo=[real_estate] non_a_brief_id=brief-478200059820 manual_task_id=task-617e689185a3 manual_task={task_type:manual_todo,current_state:ready,reason_code:request_brief_confirmed,workflow_id:null} approvals_before_after={before:1,after:1} guard_decisions={fund:non_a_asset_no_trade,gold:non_a_asset_no_trade,fake_a_share_AAPL_SH:non_a_asset_no_trade,valid_a_share_600000_SH:a_share_trade_chain_allowed} projected_to=[planning,risk_hint,manual_todo] domain_manual_todo_types=[real_estate,tax,major_expense]; db_counts={manual_task:{task_type:manual_todo,current_state:ready,reason_code:request_brief_confirmed},workflow_for_manual_task:0,paper_execution_for_manual_task:0,approval_rows_total:0} restart_check={api_restarted:true,manual_task_visible_after_restart:true,approvals_after_restart_count:1,finance_overview_fixture_asset_types:[cash,fund,gold,real_estate,liability],finance_overview_manual_todo_types:[real_estate,tax,major_expense]}; ACC-023 assertions covered fund/gold planning-only assets, real_estate manual valuation todo, non-A trade RequestBrief conversion to manual_todo, no workflow creation, no approval count increase, no paper execution artifact, invalid exchange-suffixed AAPL.SH denied, valid A-share control allowed, PostgreSQL persisted manual task, and API readability after restart.
  result: pass
  residual_risk: Finance asset updates themselves remain API in-memory read models in current scope; durable evidence is the persisted manual_todo TaskEnvelope and absence of workflow/approval/execution for non-A trade. First-class FinanceProfile persistence would require API/DB scope outside WI-005.
  reopen_required: false

- acceptance_ref: ACC-024
  run_id: RUN-WI005-ACC024-FULL-RUNTIME-FOUNDATION-20260503
  test_case_ref: TC-ACC-024-01
  verification_type: automated
  test_type: integration
  test_scope: full-integration
  completion_level: integrated_runtime
  executed_at: 2026-05-03
  artifact_ref: python -m pytest tests/domain/finance tests/domain/attribution tests/domain/knowledge -q passed 14 tests; python -m compileall src/velentrade passed; compose runtime stayed running with PostgreSQL/Alembic migration, Redis/Celery worker, FastAPI endpoint, Chromium browser click from deploy smoke, and cross-WI workflow runtime foundation at revision=91451ee01a3418859dddcf6ea4158d6d3eca4df8; targeted WI-005 attribution runtime smoke run_id=1777772723 workflow_id=workflow-f8c2d9797fac routine_attr_ref=artifact-209e910bef8b missing_condition_attr_ref=artifact-b4a9b090493a routine_scores={decision_quality:0.818,execution_quality:0.948,risk_quality:0.87,data_quality:0.95,evidence_quality:0.897,condition_score:1.0,needs_cfo:false,triggers:[]} missing_condition_scores={decision_quality:0.425,execution_quality:0.767,risk_quality:null,improvement_items:[missing_input:risk_review],condition_score:0.0,needs_cfo:true,triggers:[single_dimension_low,condition_failure]}; db_counts={attribution_artifacts:2,outbox_events_for_keys:2,audit_events_for_objects:2} restart_check={api_restarted:true,dossier_attribution_status:completed,dossier_evidence_has_new_refs:{routine:true,missing_condition:true},routine_needs_cfo_after_restart:false,missing_risk_quality_after_restart:null,missing_improvement_items_after_restart:[missing_input:risk_review]}; ACC-024 assertions covered return/benchmark inputs, decision/execution/risk/data/evidence quality scores in 0..1, condition hit/miss scoring, normal daily auto publication without CFO, missing risk input yielding null risk_quality plus improvement item, Dossier attribution projection, PostgreSQL persistence, outbox/audit, and API artifact readability after restart.
  result: pass
  residual_risk: Runtime uses the existing performance_attribution_evaluation service producer and generic Gateway artifact ledger; dedicated attribution-specific tables or richer Owner-facing attribution drilldown projection would require API/DB/frontend scope outside WI-005.
  reopen_required: false

<!-- CODESPEC:TESTING:RISKS -->
## 4. 残留风险与返工判断

- residual_risk: medium
- reopen_required: false
- notes:
  - 本阶段已追加 WI-001/WI-004 的 `api_connected` 与 `db_persistent` 级实现证据；历史 `RUN-FULL-*` 仍仅为 `fixture_contract`。
  - Implementation 阶段必须按 `contracts/verification-report-schemas.md` 生成可复核 report artifact。
  - WI-002 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI workflow endpoint、Chromium 浏览器交互、S0-S7 persistence、Reopen Event、公开 A 股 K 线 Source Registry/采集落库、execution_core 阻断、服务边界、市场状态和治理 ContextSnapshot 生效边界。Tencent 公开 A 股 K 线 live provider smoke 仍只作单独证据，不作为 P0 pass 条件；真实外部 provider 生产可用性、全 V1 业务语义和 Owner 人工验收仍未完成。
  - WI-003 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI workflow/Gateway endpoint、Chromium 浏览器交互、Opportunity Registry、Topic Queue、P0 抢占、IC Context Package 和 CIO Chair Brief 持久化载荷。WI-003 scope 明确不允许新增 API/DB schema；first-class ICContextPackage/ICChairBrief API artifact type 需要未来扩大 scope。
  - WI-007 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI Gateway/Collaboration/Workflow/Dossier endpoint、Chromium 浏览器交互、四 Analyst Memo artifact、S3 CollaborationCommand/Event、hard dissent Risk handoff、PostgreSQL audit/outbox 和 API restart 后 Dossier 可见。WI-007 scope 明确不拥有 Risk verdict、Owner exception、paper execution 或前端页面实现。
  - WI-008/ACC-018 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PostgreSQL/Alembic、Redis/Celery worker、FastAPI Gateway/Workflow/Dossier/artifact endpoint、Chromium 浏览器交互、DecisionPacket、CIODecisionMemo、DecisionGuardResult、Owner exception candidate、S4 handoff、PostgreSQL audit/outbox 和 API restart 后 artifact/Dossier 可见。当前官方 deploy hook 在最终服务列表 pipe check 处存在 rc=141 工具残留，后续以 docker compose ps/API/tasks/targeted smoke 补证；修复 deploy hook 需进入对应脚本 scope。
  - WI-008/ACC-019 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 RiskReviewReport conditional_pass/rejected、Owner timeout no-execute domain disposition、Reopen Event、Risk rejected bypass denial、直接 S6 workflow command 被阻断、无 PaperExecutionReceipt、PostgreSQL audit/outbox 和 API restart 后 Dossier risk 状态可见。ApprovalRecord 创建仍停留在 domain evidence；持久化审批创建入口需未来 API/DB scope。
  - WI-009/ACC-020..022 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 PaperAccount 初始化与填充后账户、PaperOrder/PaperExecutionReceipt 的 filled/blocked/expired/TWAP 路径、execution_core 阻断、T+1、S0-S7 completion、Dossier paper_execution、API restart 后 artifact 可读、PositionDisposalTask P0 处置 handoff、直接 S6 bypass 阻断、无真实券商/真实下单/回测。当前证据通过 generic Gateway artifact ledger 和 HandoffPacket 持久化；专用 paper_* 表镜像与一等 PositionDisposalTask API/schema 仍需未来 API/DB scope。
  - WI-005/ACC-023 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证 Finance API 对 fund/gold/real_estate 的 planning-only 边界、real_estate manual_todo、非 A trade RequestBrief 转 manual_todo、PostgreSQL task 持久化、API restart 后任务可读、无 workflow/approval/paper execution。FinanceProfile 资产更新仍是 API 内存读模型；专用财务档案持久化需未来 API/DB scope。
  - WI-005/ACC-024 已追加 foundation 级 `integrated_runtime` 自动化证据：同一 docker compose runtime 下验证自动归因日度发布、评分公式、condition hit/miss、缺失输入 null/improvement item、Dossier attribution、PostgreSQL artifact/audit/outbox、API restart 后读回。证据仍通过 generic Gateway artifact ledger；专用 attribution drilldown/API 展示需未来 API/DB/frontend scope。
  - 2026-05-02 docker compose runtime blocker 已修复到 WI-001/WI-004 `integrated_runtime` foundation 级：允许 Dockerfile/预构建镜像/`wheelhouse/`，runtime image 在 build 阶段通过 PyPI mirror 或 wheelhouse 安装依赖，api/worker/beat/agent-runner 启动命令不再 `pip install -e .`；同一 compose runtime 已通过 same-origin frontend、Chromium 浏览器点击、RequestBrief->Task、agent-runner fake_test、API restart 后 task 持久化和六个服务 running 检查。仍不能外推到全 V1，因为 S0-S7、真实外部数据、纸面执行和 Owner 人工验收未闭环。
  - 若后续任何 P0 自动化不可行，必须回到 Requirement 或 review 明确记录例外理由。
