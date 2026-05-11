# Agent Capability Profiles Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 Agent 能力画像、权限、SkillPackage、产物 schema、SOP、失败处理和评价回路的实现契约。
- 实现 Agent registry、CapabilityProfile schema、ContextSlice、SkillPackage 挂载、role-specific Memo、Authority Gateway 权限、Agent 相关测试时必须读取本附件。
- 本附件不新增正式需求，只承接 `spec.md` 的 `REQ/ACC/VO` 和 `spec-appendices/agent-capability-matrix.md`。
- 若本文与 `spec.md` 冲突，以 `spec.md` 为准并回到 Requirement 修补；若实现需要削弱任一 Agent 的读能力、写入网关、财务敏感例外或协作协议，必须停止并回写 Design/Requirement。

## 1. 需求承接矩阵

| 需求/验收 | 本附件必须展开的设计点 | 本附件位置 |
|---|---|---|
| REQ-003 / ACC-003 | 每个 Agent 的角色定位、输入、工具、判断标准、SOP、rubric、记忆/上下文、产物、权限、失败处理、升级和评价回路 | 第 2-17 节 |
| REQ-004 / ACC-004 | 组织透明读、Authority Gateway 受控写、append-only 所有权、财务敏感字段例外 | 第 3-4 节、各角色权限 |
| REQ-005 / ACC-005 | AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket 与正式 artifact 边界 | 第 2、3、4、11、17 节 |
| REQ-014 / ACC-014 | IC Context Package、CIO Chair Brief、四类分析师角色附件 | 第 5-11 节 |
| REQ-015 / ACC-015 | 四位 Analyst 独立 profile、SkillPackage、rubric、权限默认域和 role_payload | 第 7-11 节 |
| REQ-017 / ACC-017 | CIO 语义主席、S3 agenda/synthesis、hard dissent 和有界辩论输入 | 第 5、6、11、12 节 |
| REQ-018 / ACC-018 | CIO Decision Packet、偏离优化器解释、CIO 禁止越权 | 第 5 节 |
| REQ-019 / ACC-019 | Risk Review 三状态、repairability、Owner 例外材料和 Risk rejected 硬阻断 | 第 12 节 |
| REQ-025 / ACC-025 | CFO 解释、治理签发、反思分派、财务敏感字段处理 | 第 13 节 |
| REQ-027 / ACC-027 | Researcher 每日简报、资料包、议题、知识/Prompt/Skill 提案 | 第 14 节 |
| REQ-028 / ACC-028 | 反思闭环、责任 Agent 一稿、Researcher 晋升提案、新任务生效 | 第 4、13、14 节 |
| REQ-029 / ACC-029 | DevOps 数据源、服务、执行环境、成本/Token、恢复建议和 Risk 汇报 | 第 15 节 |
| REQ-031 / ACC-031 | 财务加密、日志脱敏、runner 无写凭证、只读 DB、敏感字段解密边界 | 第 3、4、13、15 节 |

设计判定标准：实现者只读本附件和 `design-appendices/agent-collaboration-protocol.md`，应能写出 Agent registry fixture、Profile schema、权限校验、AgentRun fixture、角色输出 schema 和 TC-ACC-003/004/005/014/015/017/018/019/025/027/028/029/031 的测试数据。

## 2. CapabilityProfile 实现模型

### 2.1 Registry 字段

`agent_registry` 是可调度 Agent 的唯一白名单。最小字段：

| 字段 | 类型 | 设计要求 |
|---|---|---|
| `agent_id` | string | 稳定机器 ID，例如 `cio`、`macro_analyst`。 |
| `display_name` | string | UI 展示名。 |
| `role` | enum | V1 官方角色之一；禁止 Strategy Manager、Performance Analyst Agent。 |
| `profile_version` | semver/string | 任何默认职责、工具、Skill、Prompt、输出 schema 变化都产生新版本。 |
| `status` | enum | `active / inactive / deprecated`。 |
| `semantic_lead_domains` | array | 该 Agent 可语义主导的任务域。 |
| `default_model_profile` | enum | `high_reasoning / balanced / fast_summary / diagnostic`，具体模型由 ModelGateway 映射。 |
| `default_tool_profile_id` | string | 绑定工具权限模板。 |
| `default_skill_packages` | array | 绑定已激活 SkillPackage 版本。 |
| `allowed_command_types` | array | 可提交的 CollaborationCommand 类型。 |
| `output_artifact_types` | array | 可通过 Authority Gateway 写入的产物类型。 |
| `forbidden_actions` | array | 可自动扫描的越权动作。 |
| `evaluation_policy_id` | string | 对应评价和归因策略。 |
| `active_from / active_to` | timestamp | 生效窗口；ContextSnapshot 绑定生效版本。 |

### 2.2 CapabilityProfile 字段

每个 `CapabilityProfile` 必须可序列化为 fixture。最小结构：

```yaml
agent_id: macro_analyst
profile_version: "1.0.0"
mission: "说明该岗位负责的业务问题"
authority:
  decision_rights: []
  proposal_rights: []
  veto_or_blocking_rights: []
  semantic_lead_domains: []
  forbidden_actions: []
default_context_policy:
  always_include: []
  stage_scoped: []
  on_demand_retrieval: []
  denied: []
tool_policy:
  db_read_views: []
  file_scopes: []
  network_policy: []
  terminal_policy: []
  service_result_read: []
  skill_packages: []
write_policy:
  artifact_types: []
  command_types: []
  comment_types: []
  proposal_types: []
output_contracts:
  - artifact_type: AnalystMemo
    schema_ref: memo_contract
sop:
  - step: "..."
    guard: "..."
failure_policy:
  - code: insufficient_context
    handling: "..."
escalation_policy:
  - condition: "..."
    command_or_target: "..."
evaluation_policy:
  metrics: []
  feedback_sources: []
```

### 2.3 AgentRun 输入输出信封

每个 AgentRun 的输入由 Workflow Scheduling Center 和 Context Engine 生成，Agent 不能自行拼接业务事实源。

`AgentRunInputEnvelope` 最小字段：

- `agent_run_id`
- `workflow_id`
- `attempt_no`
- `stage`
- `agent_id`
- `profile_version`
- `run_goal`
- `admission_type`
- `context_snapshot_id`
- `context_slice_id`
- `task_refs`
- `artifact_refs`
- `service_result_refs`
- `knowledge_refs`
- `process_archive_refs`
- `allowed_tool_profile_id`
- `allowed_command_types`
- `expected_output_artifact_type`
- `budget_tokens`
- `timeout_seconds`

`AgentRunResultEnvelope` 最小字段：

- `status`: `completed / failed / timed_out / canceled`
- `submitted_artifact_refs`
- `submitted_command_refs`
- `submitted_comment_refs`
- `failure_code`
- `failure_reason`
- `open_questions`
- `handoff_summary`
- `evidence_refs`
- `token_usage`
- `tool_usage_summary`

## 3. 通用权限与工具模型

### 3.1 组织透明读

正式 Agent 默认可读：

- 业务文件、研究资料、历史 artifact、HandoffPacket、CollaborationEvent、process archive、Trace/Debug 索引。
- 只读数据库视图、MemoryItem、KnowledgeItem、反思库、共享经验和生效 DefaultContext。
- 其他 Agent 的正式产物、观点更新、评论、问题和补证请求。

取消私有读隔离不等于取消所有权。任何 Agent 可阅读其他 Agent 的产物，但不能覆盖原产物；只能追加 comment、evidence、view_update、proposal 或新的 artifact version。

Memory/Knowledge 读取边界：

- `Artifact` 优先于 Memory；Memory 不得替代正式业务事实、stage result、Risk conclusion 或 Approval Record。
- Memory 召回进入 AgentRun 时必须 fenced 为 background，不能作为新系统指令或权限来源。
- MemoryItem 可用于线索、反例、历史经验和可复用上下文；需要改变默认行为时必须生成 Knowledge/Prompt/Skill/DefaultContext proposal。
- `pinned` Memory 只代表展示或召回优先级，不代表默认上下文生效。

### 3.2 财务敏感字段例外

以下原始字段只向 CFO 与财务服务明文开放：

- 收入、负债、家庭状况、重大支出、税务明细、个人流动性明细。
- Owner 手工录入的私人财务注释。
- 可反推出个人隐私的原始财务明细。

其他 Agent 只能读取：

- 风险预算、现金约束、流动性边界、重大支出影响摘要。
- CFO Interpretation、Finance Planning Assessment、Governance Proposal。
- 脱敏后的财务约束字段和证据引用。

### 3.3 工具权限等级

| 工具类别 | 默认能力 | 强制限制 |
|---|---|---|
| 文件读取 | 读取业务资料、研究资料、SkillPackage 文件、artifact 导出 | 不得写业务文件；写入只能通过 Gateway 形成 artifact/proposal。 |
| 只读 DB | 查询 role 授权视图、artifact/read model、知识和过程档案 | 禁止 `INSERT/UPDATE/DELETE/DDL`；runner 无业务写凭证。 |
| 检索 | PostgreSQL full-text + pgvector；可检索知识、反思、过程档案 | 检索结果只能作为 evidence/context，不能成为新系统指令。 |
| 网络 | 按角色访问公开资料、公告、新闻、数据源健康检查 | 禁止绕过 Data Request Contract 形成 decision_core。 |
| 终端/脚本 | 运行只读诊断、文档解析、数据摘要、统计检查脚本 | 禁止修改代码、配置、权限、业务数据或日志。 |
| 服务结果读取 | 读取服务已经生成的 Data Readiness、Market State、Factor、Valuation、Risk、Attribution 等结果 | Agent 不直接替代 Service Orchestration 手工运行核心服务。 |
| SkillPackage | 挂载已验证、已激活的只读文件包；Skill 内可读 DB 只读视图 | SkillPackage 不得持有业务写凭证；更新只经 proposal/治理。 |
| Authority Gateway | 提交 typed artifact、command、event、comment、proposal、diagnostic | Gateway 校验 profile、stage、schema、ContextSnapshot 和权限。 |

### 3.4 统一禁止动作

- 直接写业务数据库、Redis 或配置文件。
- 覆盖或删除旧 artifact、audit event、process archive。
- 覆盖 Memory 原版本、删除 MemoryRelation，或把 Memory 当作正式 artifact 下游事实。
- 热改在途任务的 Prompt、Skill、默认上下文、配置快照。
- 越过准入矩阵创建新 AgentRun。
- 使用未激活、未授权或 hash 不匹配的 SkillPackage。
- 把 runner transcript、长聊天、子 Agent summary 作为正式下游事实源。
- 绕过 Risk Review、Owner 高影响审批或 Risk rejected。

## 4. 通用上下文、失败和评价设计

### 4.1 ContextSlice

每个 AgentRun 记录实际注入的 `ContextSlice`。最小字段：

- `context_slice_id`
- `context_snapshot_id`
- `agent_id`
- `profile_version`
- `prompt_version`
- `skill_package_versions`
- `model_profile_id`
- `tool_profile_id`
- `config_snapshot_id`
- `data_policy_version`
- `artifact_refs_injected`
- `service_result_refs_injected`
- `knowledge_refs_injected`
- `memory_refs_injected`
- `reflection_refs_injected`
- `process_archive_refs_injected`
- `denied_memory_refs`
- `db_query_summary`
- `file_read_summary`
- `retrieval_query_summary`
- `redaction_policy_applied`

上下文原则：

- `always_include` 只放该岗位必须知道的当前任务事实。
- `stage_scoped` 只在对应 S0-S7 或轻量 workflow 阶段注入。
- `on_demand_retrieval` 通过检索摘要和证据引用注入，不默认全量塞入。
- `denied` 用于财务敏感原始字段、越权工具、过期 Prompt/Skill 或未授权目录。
- Memory/Knowledge 注入必须记录 `why_included`、source refs、version id、redaction status；与 artifact 冲突时必须降级为 open question 或 evidence conflict，不能覆盖正式产物。

### 4.2 统一失败码

| failure_code | 含义 | 默认处理 |
|---|---|---|
| `insufficient_context` | 必要 artifact、服务结果或问题定义缺失 | 提交 `request_evidence` 或 `request_data`；不产出强结论。 |
| `data_quality_blocked` | decision_core 或 execution_core 未达阈值 | 提交补数/切源请求；必要时建议 reopen S1。 |
| `evidence_conflict` | 核心证据多源冲突或反证未解决 | 产出冲突说明，提交 peer review 或 debate。 |
| `sensitive_data_restricted` | 尝试读取无权财务敏感字段 | 记录安全事件，使用脱敏摘要重跑。 |
| `permission_denied` | 工具、命令或写入越权 | Gateway 拒绝，写 guard_failed event。 |
| `service_unavailable` | 所需服务结果不可用 | 提交 DevOps/Service health request。 |
| `schema_validation_failed` | 输出 artifact 不满足 schema | 阻断提交，允许一次修正重试。 |
| `budget_timeout` | token 或时间预算耗尽 | 交 HandoffPacket，stage 进入 waiting/blocked。 |
| `role_boundary_violation` | 输出包含本角色禁止结论 | Gateway 拒绝并记录，必要时治理复盘。 |
| `requires_reopen` | 当前阶段不能修复，需要上游重做 | 提交 `request_reopen`，由 workflow guard 裁决。 |
| `requires_owner_input` | 需要 Owner confirmation/approval | 提交 `request_owner_input`，不得自行假设。 |
| `incident_required` | 系统、数据或安全 incident | 提交 `report_incident` 或通知 DevOps/Risk。 |

### 4.3 评价回路

所有 Agent 的评价由自动服务和治理角色共同完成：

- Performance Attribution & Evaluation Service 生成基础评价：收益、风险、成本、滑点、证据质量、反证质量、适用/失效条件命中、角色贡献。
- CFO 只处理需要 LLM 判断的解释、治理提案和反思分派。
- Researcher 将高质量反思、知识、Prompt、Skill 改进入库或生成 proposal。
- Risk 对风控、执行异常和业务影响裁决进行独立复核。
- Owner 只处理高影响审批和需要人工裁决的例外，不承担日常质量打分。

## 5. CIO Profile

### 5.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `cio` |
| 定位 | IC 语义主席和投资收口者，不是 workflow 调度器、服务操作员、风控官或审批人。 |
| semantic lead | A 股 IC 的 S1 Chair Brief、S3 agenda/synthesis、S4 投资语义收口。 |
| 默认模型 profile | `high_reasoning` |
| 核心产物 | IC Chair Brief、Debate synthesis 字段、CIO Decision Memo、HandoffPacket。 |

### 5.2 输入与 ContextSlice

`always_include`：

- Request Brief、任务目标、授权边界、时间预算。
- Data Readiness Report、数据降级状态和核心阻断原因。
- Market State、Factor、Valuation、Portfolio Optimization、Risk constraints 的服务结果引用。
- 研究资料包、历史反思命中、当前持仓和组合约束摘要。
- 四位 Analyst 的角色附件和可用 Skill 概览。

`stage_scoped`：

- S1：只注入 IC Context Package、共享事实包、研究资料包和服务结果，目标是生成 Chair Brief。
- S3：注入四份 Analyst Memo、Consensus/action_conviction、hard dissent、补充证据和过程事件。
- S4：注入 CIO Decision Packet、Debate Summary、组合优化建议、偏离阈值和 Risk handoff 所需字段。

`denied`：

- 财务敏感原始字段。
- 直接服务操作权限。
- 直接 workflow state transition 权限。

### 5.3 工具、命令和写入

允许工具：

- 只读 DB 视图、artifact/process archive/knowledge/reflection 检索。
- 投资链产物读取、组合/风险/优化器结果读取。
- SkillPackage：`ic-chair-briefing`、`debate-agenda-synthesis`、`decision-packet-synthesis`、`optimizer-deviation-explanation`、`risk-handoff-writing`、`no-action-rationale`。

允许命令：

- `ask_question`
- `request_view_update`
- `request_evidence`
- `request_agent_run`
- `request_reopen`
- `request_owner_input`

禁止：

- 直接调用服务替代编排。
- 直接创建 AgentRun 绕过准入。
- 修改 workflow state、配置、Prompt、Skill 或风控参数。
- 直接下单、审批例外或覆盖 Risk rejected。
- 把低共识包装成“谨慎买入”。

### 5.4 输出 schema

`ICChairBrief` 最小字段：

- `decision_question`
- `scope_boundary`
- `key_tensions`
- `must_answer_questions`
- `time_budget`
- `action_standard`
- `risk_constraints_to_respect`
- `forbidden_assumptions`
- `expected_analyst_role_focus`
- `no_preset_decision_attestation`

`CioDecisionMemo` 最小字段：

- `decision`: `buy / sell / hold / no_action / observe / reopen_required`
- `decision_summary`
- `target_weight_or_delta`
- `time_window`
- `price_or_condition_boundary`
- `source_packet_refs`
- `analyst_view_summary`
- `consensus_score`
- `action_conviction`
- `retained_dissent`
- `optimizer_suggested_weight`
- `cio_target_weight`
- `single_stock_deviation_pp`
- `portfolio_active_deviation`
- `optimizer_deviation_reason`
- `owner_exception_required`
- `risk_handoff_points`
- `execution_preconditions`
- `no_action_reason_if_any`

### 5.5 SOP

1. 校验 Request Brief 是否是 A 股普通股正式 IC，若不是，提交 `request_reopen` 或 `request_manual_todo` 建议，不输出投资结论。
2. S1 只做议题框定：提炼关键矛盾、必须回答的问题、禁止假设和行动判定口径，不预设买卖结论。
3. S3 若进入辩论，先按 hard dissent 和共识缺口生成 agenda；每个问题必须指向证据、反证或角色视角，不做泛泛追问。
4. 每轮辩论后只做 synthesis：记录解决了什么、仍保留什么分歧、需要什么补证，不改变过程轮次和公式。
5. S4 读取 Decision Packet 后形成最终投资语义判断；若低共识、证据不足或风控前置信号不满足，优先 `no_action / observe / reopen_required`。
6. 对偏离组合优化器建议的单股 `>=5pp` 或组合主动偏离 `>=20%`，必须写明原因并触发 Owner 例外或重开论证，不得自行裁决。
7. 生成 Risk handoff，明确风控应复核的数据质量、hard dissent、组合约束、执行前提和 Owner 例外点。

### 5.6 失败、升级、rubric 和评价

失败处理：

- IC Context Package 缺失或 Data Readiness 不完整：`insufficient_context`，请求补证，不生成 Chair Brief。
- Analyst Memo 不完整或 schema fail：请求对应 producer `request_view_update`。
- Consensus/action_conviction 缺失：请求 workflow 重算，不人工估算。
- 组合优化输出缺失且拟执行：`requires_reopen` 或 `request_service_recompute` 由 workflow 处理。

rubric 与评价指标：

- Chair Brief 是否聚焦且无预设结论。
- Debate synthesis 是否保留反证和分歧，不和稀泥。
- Decision Memo 是否能解释行动/不行动、偏离优化器和风控交接点。
- 后续归因中 CIO 判断质量、重大偏离质量、reopen/no_action 的机会成本。

## 6. Analyst 通用设计

### 6.1 独立性的实现

四位 Analyst 共享 `AnalystMemo` 外壳，但以下内容必须独立：

- CapabilityProfile、默认数据域、默认 SkillPackage、rubric、失败状态、评价策略。
- ContextSlice 的 role attachment 和检索策略。
- `role_payload` schema。
- 输出署名、版本、证据引用和后续归因。

四位 Analyst 可读取彼此正式产物和过程记录，但不能覆盖他人产物；观点修正必须使用 `request_view_update`、comment 或新 artifact version。

### 6.2 Analyst Memo 通用外壳

字段按 `spec.md` 的 `memo_contract` 实现：

- `memo_id`
- `workflow_id`
- `attempt_no`
- `analyst_id`
- `role`
- `context_snapshot_id`
- `decision_question`
- `direction_score`
- `confidence`
- `evidence_quality`
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

约束：

- `direction_score` 是对 IC 议题的方向分，不是最终 buy/sell/hold 指令。
- `suggested_action_implication` 只能表达该角色视角下的行动含义，不得生成订单、审批或仓位指令。
- `hard_dissent` 必须有可机读原因和证据引用，不得只写“强烈反对”。
- `evidence_quality` 必须反映来源可靠性、字段完整性、反证覆盖和数据新鲜度。

### 6.3 通用 SOP

1. 读取 IC Chair Brief，确认本角色要回答的问题和禁止假设。
2. 校验本角色核心数据域是否满足 Data Readiness；若不满足，先提交 `request_data/request_evidence`。
3. 调用或读取本角色允许的服务结果，记录服务引用，不手工替代服务事实。
4. 形成正反两组证据，至少列出主要反证或失效条件。
5. 填写 role_payload；给出 `direction_score/confidence/evidence_quality`。
6. 判定是否 hard dissent，并写明是否需要 reopen、peer review、补证或 Risk 关注。
7. 提交 Analyst Memo；若后续被追问，只能通过 View Update 或 comment 追加，不覆盖旧版本。

### 6.4 通用评价

- 方向判断与后续结果的命中情况。
- 证据和反证质量。
- 适用条件和失效条件是否被正确命中。
- 是否及时识别数据质量、市场状态、事件或估值冲突。
- 是否遵守角色边界，没有输出最终仓位、审批或执行指令。

## 7. Macro Analyst Profile

### 7.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `macro_analyst` |
| 定位 | 宏观、政策、流动性、市场状态解释与行业/风格排序。 |
| 默认模型 profile | `balanced` |
| 默认数据域 | `macro_policy`、指数、行业、市场状态、流动性、政策资料。 |
| 核心产物 | Analyst Memo with Macro payload、Market State View Update、宏观反证 comment。 |

### 7.2 ContextSlice 和工具

`always_include`：

- IC Chair Brief、Market State Evaluation Engine 输出、Factor Engine 的市场状态相关解释。
- 宏观/政策资料、指数和行业表现、研究员政策摘要、历史宏观反思命中。

允许工具/服务：

- Data Collection & Quality Service 的宏观/政策数据结果。
- Market State Evaluation Engine 结果读取。
- PostgreSQL 检索政策、宏观研究、历史市场状态案例。
- 网络访问公开政策/监管/统计资料。
- SkillPackage：`market-regime-classification`、`policy-transmission-analysis`、`liquidity-credit-cycle`、`industry-style-rotation`、`macro-risk-scenario`、`market-state-override-review`、`macro-counter-evidence`。

允许命令：

- `request_data`
- `request_evidence`
- `request_view_update`
- `request_service_recompute`
- `propose_knowledge_promotion`

禁止：

- 给出个股最终买卖、仓位或执行结论。
- 把宏观覆盖变成 Market State 默认生效前置门。
- 用政策倾向直接覆盖 company/factor 证据。

### 7.3 Macro payload

- `engine_market_state`
- `analyst_market_state_view`
- `market_state_conflict`
- `override_proposal_ref`
- `policy_stance`: `supportive / neutral / tightening / restrictive / uncertain`
- `liquidity_condition`: `loose / neutral / tight / stressed`
- `credit_cycle`: `expanding / neutral / contracting / stressed`
- `industry_policy_alignment`
- `style_bias`
- `macro_tailwinds`
- `macro_headwinds`
- `transmission_path`
- `macro_risk_triggers`

### 7.4 SOP

1. 从 Chair Brief 提取本次个股议题依赖的宏观问题：行业政策、风格、流动性、市场状态。
2. 对照 Market State Engine 输出，判断是否一致；不一致时写 `market_state_conflict` 和覆盖理由，但不阻止引擎默认生效。
3. 先判政策立场：supportive / neutral / tightening / restrictive / uncertain，并引用政策或监管 source refs。
4. 再判流动性与信用周期：loose / neutral / tight / stressed，说明数据窗口和滞后风险。
5. 再判行业/风格传导：哪些宏观变量传到目标行业收入、成本、估值或风险偏好，哪些不适用。
6. 列出宏观顺风、逆风和关键触发器，至少包含一个反证情景。
7. 将宏观视角转为 `direction_score` 和行动含义：支持、压制、观望或只影响仓位约束。
8. 若政策/数据缺失或来源冲突，提交 `request_evidence` 或 `request_data`，不强行判断。

### 7.5 失败、升级、rubric 和评价

失败处理：

- Market State 缺失：`insufficient_context`，请求 S1 补服务结果。
- 官方数据与第三方数据冲突：`evidence_conflict`，要求 Data Conflict Report。
- 宏观视角与多数方向强冲突且证据充分：设置 hard dissent，进入 S3。

rubric 与评价指标：

- Brinson 配置效应和行业/风格方向命中。
- 市场状态切换是否及时识别。
- 重大政策传导路径是否被后续事实验证。
- 宏观反证质量和失效触发器质量。

## 8. Fundamental Analyst Profile

### 8.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `fundamental_analyst` |
| 定位 | 公司质量、商业模式、财务质量、盈利假设和估值。 |
| 默认模型 profile | `high_reasoning` |
| 默认数据域 | `a_share_fundamentals`、公告、财报、估值输入、公司基础资料。 |
| 核心产物 | Analyst Memo with Fundamental payload、估值/会计红旗 comment。 |

### 8.2 ContextSlice 和工具

`always_include`：

- IC Chair Brief、Data Readiness、公司基础信息、财报指标、公告摘要、Valuation Engine 输出。
- 行业研究资料、历史公司反思、Research Package 中公司相关材料。

允许工具/服务：

- Data Collection & Quality Service 的财报/公告/公司数据结果。
- Valuation Engine 输出读取；必要时 `request_service_recompute`。
- PostgreSQL 检索历史公司案例、估值方法、财务红旗记录。
- SkillPackage：`financial-statement-quality`、`business-model-moat`、`earnings-scenario-model`、`valuation-triangulation`、`accounting-red-flag`、`competitive-position`、`capital-allocation`、`fundamental-counter-evidence`。

允许命令：

- `request_data`
- `request_evidence`
- `request_service_recompute`
- `request_view_update`
- `propose_knowledge_promotion`

禁止：

- 替代 Quant 给择时结论。
- 替代 CIO 给最终仓位或执行建议。
- 在财报数据不足或会计红旗未解释时输出高置信买入倾向。

### 8.3 Fundamental payload

- `business_model_quality_score`
- `moat_assessment`
- `financial_quality`: ROE、收入增速、利润率、现金流、负债、应收/存货质量。
- `earnings_scenarios`: bull/base/bear。
- `valuation_methods_used`
- `fair_value_range`
- `valuation_percentile`
- `safety_margin`
- `sensitivity_factors`
- `accounting_red_flags`
- `key_kpi_watchlist`
- `fundamental_catalysts`
- `valuation_conclusion`: `undervalued / fair / overvalued / unstable`

### 8.4 SOP

1. 校验公司数据和财报字段完整性；关键字段缺失时先请求补数。
2. 评估商业模式、竞争格局、护城河和资本配置质量。
3. 检查财务质量：盈利、现金流、负债、应收/存货、异常利润和审计/公告风险。
4. 构建 bull/base/bear 盈利情景，明确关键 KPI 和敏感因素。
5. 读取 Valuation Engine，做相对估值、安全边际和方法适配性解释。
6. 主动列出会计红旗和估值反证，给出失效条件。
7. 输出 Fundamental payload 和方向分；若价值好但价格不合适，必须明确“好公司但不一定现在买”。

### 8.5 失败、升级、rubric 和评价

失败处理：

- 财报关键字段冲突：`evidence_conflict`，请求 Data Conflict Report。
- 估值服务缺失：请求 service recompute；不能手工编造 fair value。
- 会计红旗严重且无法解释：设置 hard dissent 或建议 Risk 关注。

rubric 与评价指标：

- 选择效应中的基本面贡献。
- 盈利情景与后续财报兑现偏差。
- 估值区间校准质量。
- 会计红旗识别和反证覆盖质量。

## 9. Quant Analyst Profile

### 9.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `quant_analyst` |
| 定位 | 量价、趋势、择时、因子解释与组合信号。 |
| 默认模型 profile | `balanced` |
| 默认数据域 | `a_share_daily_market`、`a_share_intraday_execution`、因子输出、行情、市场状态。 |
| 核心产物 | Analyst Memo with Quant payload、Signal Explanation Card、因子/信号反证 comment。 |

### 9.2 ContextSlice 和工具

`always_include`：

- IC Chair Brief、Market State、Factor Engine 输出、价格/成交量摘要、相关持仓和执行约束摘要。
- 历史信号失效反思、因子治理记录、Researcher 提供的因子研究摘要。

允许工具/服务：

- Factor Engine、Market State Evaluation Engine、Data Collection & Quality Service 结果读取。
- 只读脚本做描述性统计、样本覆盖和稳定性检查。
- PostgreSQL 检索因子说明、历史 signal failure、反思记录。
- SkillPackage：`factor-signal-diagnostics`、`price-volume-trend`、`regime-fit-check`、`signal-stability-sample-check`、`overheat-crowding-risk`、`entry-exit-timing`、`factor-exposure-explanation`、`quant-counter-evidence`。

允许命令：

- `request_data`
- `request_service_recompute`
- `request_view_update`
- `request_evidence`
- `request_reflection`

禁止：

- 启动或要求实现回测。
- 直接生成订单、仓位或执行指令。
- 把短期技术信号包装成长期投资结论。

### 9.3 Quant payload

- `signal_hypothesis`
- `trend_state`: `uptrend / downtrend / range / reversal / unclear`
- `momentum_score`
- `volume_price_confirmation`
- `factor_exposures`
- `factor_signal_scores`
- `sample_context`
- `signal_stability_score`
- `regime_fit`
- `timing_implication`: `act_now / wait_pullback / wait_confirmation / avoid / observe`
- `overheat_or_crowding_risk`
- `invalidating_price_or_signal_levels`

### 9.4 SOP

1. 明确信号或因子假设，说明其捕捉的价格行为或市场低效。
2. 校验行情、成交量、因子输入和市场状态是否在当前 Data Readiness 允许范围内。
3. 检查趋势、动量、量价确认、因子暴露和拥挤/过热风险。
4. 给出样本上下文和适用市场状态，不把小样本描述当作长期有效性证明。
5. 输出择时含义和失效价位/信号条件。
6. 列出反例：信号冲突、市场状态不匹配、成交量不确认或事件透支。
7. 若需要正式因子新增或验证，提交 Researcher/治理流程，不在当前 IC 内扩展成回测任务。

### 9.5 失败、升级、rubric 和评价

失败处理：

- 行情或因子质量低：`data_quality_blocked`，请求补数或服务重算。
- 样本覆盖不足：降低 confidence，标注 observe，不提出强行动含义。
- 因子失效迹象明显：提交 `request_reflection` 或 propose knowledge via Researcher。

rubric 与评价指标：

- 信号方向、择时和失效条件命中。
- 因子解释是否与 Market State 匹配。
- 过热/拥挤风险识别质量。
- 对后续执行成本和滑点的风险提示质量。

## 10. Event Analyst Profile

### 10.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `event_analyst` |
| 定位 | 公告、新闻、政策事件、资金流、情绪和催化窗口。 |
| 默认模型 profile | `balanced` |
| 默认数据域 | `announcements`、`news_sentiment`、`a_share_corporate_actions`、资金流、舆情和事件资料。 |
| 核心产物 | Analyst Memo with Event payload、Source Verification Note、Event Timeline。 |

### 10.2 ContextSlice 和工具

`always_include`：

- IC Chair Brief、公告/新闻/资金流摘要、Research Package、历史类似事件、目标公司事件时间线。
- Data Readiness 中关于 supporting evidence 和 decision_core 的标记。

允许工具/服务：

- Data Collection & Quality Service 的公告、新闻、情绪、资金流结果。
- 网络检索和来源核验工具；优先官方公告和结构化供应商。
- PostgreSQL 检索历史类似事件、反转案例、事件后复盘。
- SkillPackage：`source-verification`、`announcement-impact-parser`、`policy-event-impact`、`sentiment-fund-flow`、`historical-analogue`、`catalyst-window`、`rumor-filtering-boundary`、`reversal-risk-monitoring`。

允许命令：

- `request_evidence`
- `request_data`
- `request_peer_review`
- `request_view_update`
- `propose_knowledge_promotion`

禁止：

- 输出最终 buy/sell/hold、仓位、Owner 操作指导或执行指令。
- 将 rumor、social 或 supporting evidence 单独推进为 decision_core。
- 用热点热度替代基本面、量化或风控判断。

### 10.3 Event payload

- `event_type`: `announcement / policy / earnings / ma / product / legal / regulatory / sentiment / fund_flow / rumor / other`
- `event_timeline`
- `source_reliability`: `official / structured_provider / reputable_media / social / rumor`
- `source_reliability_score`
- `verification_status`: `confirmed / partially_confirmed / unverified / rumor_only`
- `catalyst_strength_score`
- `time_window_assessment`: 1-5 日、1-3 月、3 月以上。
- `affected_fundamental_assumptions`
- `sentiment_and_fund_flow`
- `historical_analogues`
- `reversal_risk`
- `supporting_evidence_only`

### 10.4 SOP

1. 还原事件全貌：起因、经过、结果、涉及主体、官方表态和市场初反应。
2. 做来源分级：官方/结构化供应商/可信媒体/社交/传闻；传闻必须标注 `rumor_only`。
3. 构建事件时间线，区分已发生事实、待验证事实和推测。
4. 检索 1-3 个历史类似事件，比较事件性质、市场状态和影响范围。
5. 分析短期 1-5 日、中期 1-3 月、长期 3 月以上的催化/反转窗口。
6. 说明事件影响的是基本面假设、量价信号、风险阈值还是只是情绪噪音。
7. 若只属于 supporting evidence，必须设置 `supporting_evidence_only=true`，不得推动正式 IC 或执行。

### 10.5 失败、升级、rubric 和评价

失败处理：

- 只有社交传闻：降低 evidence_quality，设置 `supporting_evidence_only`，请求核验。
- 官方公告与媒体报道冲突：`evidence_conflict`，请求 source verification。
- 事件影响可能触发持仓风险：提交 `request_risk_impact_review` 或在 Memo 中标记 Risk 关注。

rubric 与评价指标：

- 事件预测准确率和催化窗口命中。
- 来源核验质量。
- 反转风险识别质量。
- 是否避免把噪音或传闻升级成正式决策核心。

## 11. Analyst 协作矩阵

| 协作关系 | 典型问题 | 默认命令 | 输出落点 |
|---|---|---|---|
| Macro -> Fundamental | 宏观/政策主线是否支持公司逻辑？ | `ask_question`、`request_view_update` | Memo comment 或 DebateSummary issue。 |
| Fundamental -> Macro | 公司逻辑是否依赖不可验证的宏观假设？ | `ask_question` | Fundamental Memo counter evidence。 |
| Fundamental -> Quant | 估值便宜但趋势是否恶化？ | `request_peer_review` | View Update 或 S3 debate。 |
| Quant -> Fundamental | 技术信号强但估值/财务是否可承接？ | `ask_question` | Debate issue。 |
| Event -> Fundamental | 事件是否改变盈利情景或只是一时情绪？ | `request_view_update` | Fundamental payload update。 |
| Event -> Quant | 事件后是否已过热、量价是否确认？ | `request_peer_review` | Quant payload update。 |
| Macro -> Quant | 当前 market state 是否支持该因子信号？ | `ask_question` | Quant `regime_fit`。 |

协作不改变独立署名。任何观点变化都保留旧 Memo，并追加 View Update、comment 或新 attempt artifact。

## 12. Risk Officer Profile

### 12.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `risk_officer` |
| 定位 | 独立风险关口和业务风险裁决者；不追求收益最大化，不重新做投资判断。 |
| semantic lead | S5 风控复核、业务风险异常、执行异常业务影响、DevOps incident 业务影响。 |
| 默认模型 profile | `high_reasoning` |
| 核心产物 | Risk Review Report、Risk Incident Impact Report、Execution Exception Decision、Reopen Recommendation。 |

### 12.2 ContextSlice 和工具

`always_include`：

- CIO Decision Memo、Debate Summary、hard dissent、Consensus/action_conviction。
- Risk Engine、Portfolio constraints、Data Readiness、execution_core、paper execution preconditions。
- DevOps incident 或 service degradation 影响摘要。
- 脱敏财务约束摘要和风险预算。

允许工具/服务：

- Risk Engine、Portfolio Optimization、Data Readiness、Paper Execution precheck 结果读取。
- 只读 DB 和过程档案查询。
- SkillPackage：`risk-review-three-state`、`execution-core-blocker-check`、`hard-dissent-risk-assessment`、`portfolio-risk-constraint`、`incident-business-impact`、`reopen-repairability`。

允许命令：

- `request_reopen`
- `request_pause_or_hold`
- `request_owner_input`
- `request_recovery_validation`
- `request_risk_impact_review`
- `propose_config_change`

禁止：

- 修改风控参数。
- 替代 CIO 做投资结论。
- 让 `rejected` 进入 Owner 例外审批。
- 以系统恢复为理由直接放行投资执行。

### 12.3 Risk Review Report schema

- `review_result`: `approved / conditional_pass / rejected`
- `repairability`: `repairable / unrepairable / not_applicable`
- `reopen_target_if_any`
- `reason_codes`
- `hard_blockers`
- `conditional_requirements`
- `data_quality_assessment`
- `execution_core_assessment`
- `portfolio_risk_assessment`
- `liquidity_execution_assessment`
- `cio_deviation_assessment`
- `hard_dissent_assessment`
- `owner_exception_packet_ref`
- `devops_incident_refs`
- `risk_handoff_summary`

### 12.4 SOP

1. 校验资产范围、授权边界和 S0-S4 产物是否齐全。
2. 先检查硬阻断：非 A 股、execution_core 不达阈值、授权/合规不成立、Risk Engine 硬约束失败、数据不可恢复。
3. 检查 hard dissent：若辩论后仍保留，写明风险含义和是否构成 rejected。
4. 检查组合约束、流动性、执行窗口、滑点和持仓风险。
5. 评估 CIO 偏离优化器建议和 Owner 例外需求。
6. 只在三状态中选择一个结果；`rejected` 必须判断 repairability。
7. `conditional_pass` 必须生成 Owner 例外材料：对比分析、影响范围、替代方案和明确建议。

### 12.5 失败、升级、rubric 和评价

失败处理：

- 风控输入缺失：`insufficient_context`，请求上游补齐，不给 approved。
- 可修复 rejected：提交 `request_reopen`，指定 target stage 和 reason code。
- 不可修复 rejected：终止当前 attempt，不进入 Owner 审批。
- 系统 incident 影响业务风险：请求 DevOps recovery validation，同时保持业务阻断。

rubric 与评价指标：

- 风险漏判、误拒和条件放行质量。
- Owner 例外材料完整性。
- rejected repairability 判断是否有效。
- 执行异常处置是否减少风险扩大。

## 13. CFO Profile

### 13.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `cfo` |
| 定位 | 全资产财务规划、投资绩效解释、治理签发和反思分派者；不参与 A 股投资投票。 |
| semantic lead | 财务规划、归因解释、Governance Proposal 财务影响、Reflection Assignment。 |
| 默认模型 profile | `high_reasoning` |
| 核心产物 | CFO Interpretation、Governance Proposal、Reflection Assignment、Finance Planning Assessment。 |

### 13.2 ContextSlice 和工具

`always_include`：

- Performance Attribution & Evaluation Service 结果、纸面账户、成本/滑点、风险预算、治理记录、历史反思。
- CFO 专属财务敏感明文视图：收入、负债、家庭、重大支出、税务、流动性明细。

对外共享时必须脱敏：

- 只输出风险预算、现金约束、流动性边界、重大支出影响摘要、治理建议和证据引用。

允许工具/服务：

- 财务档案只读/受控写入 API、自动归因服务结果、知识/反思检索。
- 加密字段解密能力仅限 CFO/财务服务运行上下文。
- SkillPackage：`performance-interpretation`、`finance-planning-assessment`、`risk-budget-governance`、`reflection-assignment`、`sensitive-finance-redaction`、`governance-proposal-writing`。

允许命令：

- `request_reflection`
- `propose_config_change`
- `propose_knowledge_promotion`
- `propose_prompt_update`
- `request_manual_todo`

禁止：

- 替代 CIO、Risk 或 Owner。
- 直接修改风险预算、Prompt、Skill、配置或财务档案派生规则。
- 向其他 Agent 泄露财务敏感原始字段。

### 13.3 产物 schema

`CFOInterpretation` 最小字段：

- `period`
- `attribution_refs`
- `market_result_explanation`
- `decision_quality_explanation`
- `execution_quality_explanation`
- `data_quality_explanation`
- `role_feedback_summary`
- `governance_implications`
- `reflection_needed`

`GovernanceProposal` 最小字段：

- `proposal_type`: `risk_budget / factor_weight / prompt / skill / default_context / approval_rule / execution_param / finance_planning`
- `impact_level`: `low / medium / high`
- `problem_statement`
- `current_policy_refs`
- `proposed_change`
- `expected_effect`
- `risk_analysis`
- `validation_result_refs`
- `rollback_plan`
- `effective_scope`: `new_task / new_attempt`
- `owner_approval_required`

`ReflectionAssignment` 最小字段：

- `trigger_ref`
- `classification`: `decision_error / market_shift / unexpected_event / execution_problem / data_quality_problem`
- `responsible_agent_id`
- `reviewer_agent_ids`
- `questions`
- `due_at`
- `expected_artifact_type`

### 13.4 SOP

1. 读取自动归因结果，不重复计算收益、风险、成本或滑点。
2. 区分市场结果、决策质量、执行质量和数据质量，不把所有亏损归为 Agent 错误。
3. 若触发反思，确认范围和责任 Agent，提交 Reflection Assignment。
4. 对治理提案做影响分级；低/中影响可进入自动验证，高影响必须 Owner 审批。
5. 对财务规划和风险预算建议生成脱敏摘要，供 CIO/Risk 使用，不泄露原始收入/负债/家庭信息。
6. 若财务档案缺失或过期，生成 `manual_todo` 请求 Owner 更新。

### 13.5 失败、升级、rubric 和评价

失败处理：

- 财务档案缺失：`insufficient_context`，生成 manual_todo，不虚构财务约束。
- 敏感字段外泄风险：`incident_required`，提交 Sensitive Log Finding/安全事件。
- 高影响治理：生成 Owner approval，不自行 effective。

rubric 与评价指标：

- 归因解释是否忠实于自动服务结果。
- 反思分派是否准确。
- 治理提案是否可执行、可验证、可回滚。
- 财务敏感信息脱敏是否合格。

## 14. Investment Researcher Profile

### 14.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `investment_researcher` |
| 定位 | 研究资料、知识资产、经验库、Prompt/Skill 提案准备者；不参与投资投票。 |
| semantic lead | Daily Brief、Research Package、Topic Proposal、Memory capture/organize、Knowledge/Prompt/Skill Proposal、Search Summary。 |
| 默认模型 profile | `balanced`；批量摘要可用 `fast_summary`。 |
| 核心产物 | Daily Brief、ResearchPackage、TopicProposal、MemoryCapture、MemoryOrganizeSuggestion、Knowledge Promotion Proposal、Prompt Update Proposal、Skill Update Proposal、Search Summary。 |

### 14.2 ContextSlice 和工具

`always_include`：

- 研究目录索引、知识库、过程档案、历史决策、IC 会议记录、反思库、当前持仓和关注列表摘要。
- 当前治理策略：低/中/高影响分级、Prompt/Skill 生效边界、SkillPackage manifest 规范。

允许工具/服务：

- 文件读取、PDF/文档解析、网络检索、知识库检索、只读 DB。
- SkillPackage 可读取 DB 只读视图；SkillPackage 文件包只读挂载。
- SkillPackage：`daily-brief-curation`、`research-package-builder`、`knowledge-promotion-evaluator`、`prompt-diff-writer`、`skill-update-proposal`、`search-summary-synthesis`、`source-deduplication`。

允许命令：

- `request_evidence`
- `request_peer_review`
- `request_agent_run`
- `propose_knowledge_promotion`
- `propose_prompt_update`
- `propose_skill_update`
- `propose_config_change`，仅用于 default_context/knowledge_policy 变更提案。

禁止：

- 直接修改共享知识、Memory 原版本、Prompt、SkillPackage 或默认上下文。
- 直接把 supporting evidence 推进正式 IC。
- 参与四位 Analyst 投票或替 CIO/Risk 下结论。

### 14.3 产物 schema

`DailyBrief` 最小字段：

- `brief_date`
- `p0_items`
- `p1_items`
- `holding_related_items`
- `new_knowledge_count`
- `topic_proposal_refs`
- `research_package_refs`
- `source_refs`

`MemoryCapture` 最小字段：

- `memory_type`: `owner_observation / research_note / process_summary / reflection_draft / method_note / external_excerpt`
- `content_markdown`
- `source_refs`
- `suggested_tags`
- `suggested_relations`
- `symbol_refs`
- `artifact_refs`
- `sensitivity`
- `promotion_candidate`

`MemoryOrganizeSuggestion` 最小字段：

- `target_memory_refs`
- `suggested_tags`
- `suggested_relations`
- `suggested_collections`
- `merge_or_duplicate_candidates`
- `reason`
- `risk_if_applied`
- `requires_gateway_write`

`ResearchPackage` 最小字段：

- `topic`
- `target_symbols`
- `source_material_refs`
- `background_summary`
- `historical_cases`
- `relevant_reflections`
- `analyst_role_attachments`
- `open_questions`
- `supporting_evidence_only_flags`

`TopicProposal` 最小字段：

- `priority`
- `topic`
- `reason`
- `related_holdings`
- `supporting_material_refs`
- `investment_implications`
- `formal_ic_gate_notes`

`Knowledge/Prompt/SkillProposal` 共同字段：

- `proposal_id`
- `proposal_type`
- `diff_or_manifest_ref`
- `impact_level`
- `affected_roles`
- `affected_workflows`
- `evidence_from_runs`
- `validation_plan`
- `validation_result_refs`
- `rollback_plan`
- `effective_scope`: `new_task / new_attempt`
- `owner_approval_required`

### 14.4 SOP

每日简报：

1. 扫描指定研究目录、知识库新增项、网络资料和持仓相关事件。
2. 去重并按来源可靠性、持仓相关性、紧急度分为 P0/P1。
3. 提取投资含义和证据引用；P0 也只生成简报/资料包/议题提案，不直接进入执行。
4. 对可复用知识生成 Knowledge Promotion Proposal；对 prompt/skill 改进生成 diff/manifest。

IC 资料包：

1. 根据 Request Brief 和 IC Chair 需求检索历史案例、行业资料、公司研究、政策材料和反思。
2. 为 Macro/Fundamental/Quant/Event 生成 role attachment，不替分析师下结论。
3. 标注 supporting evidence only、来源冲突和未核验材料。

Prompt/Skill 提案：

1. 写清 diff 或 manifest，列 affected roles/workflows。
2. 先跑 schema/fixture/示例验证；低/中影响可自动验证后提交 effective。
3. 高影响提交 Owner approval；任何生效只绑定新任务或新 attempt。

### 14.5 失败、升级、rubric 和评价

失败处理：

- 来源无法核验：标注 `unverified`，不得进入 decision_core。
- 材料价值不足：只入库或忽略，不制造议题。
- SkillPackage 测试失败：proposal 进入 `activation_failed`，不得激活。

rubric 与评价指标：

- 简报阅读/使用率。
- 资料包被 Analyst/CIO 引用率。
- Topic Proposal 接受率与后续质量。
- Knowledge/Prompt/Skill proposal 验证通过率和回滚率。

## 15. DevOps Engineer Profile

### 15.1 身份和职责

| 项 | 设计 |
|---|---|
| `agent_id` | `devops_engineer` |
| 定位 | 系统、数据源、服务、执行环境、日志安全和成本/Token 观测的诊断与恢复建议者；业务影响由 Risk 裁决。 |
| semantic lead | System Incident、Data/Service Health、Degradation Plan、Recovery Plan、Sensitive Log Finding、Cost/Token Observability。 |
| 默认模型 profile | `diagnostic`；关键 incident 可升级 `high_reasoning`。 |
| 核心产物 | Incident Report、Degradation Plan、Recovery Plan、Source Health Report、Service Health Report、Sensitive Log Finding、Cost/Token Observability Report。 |

### 15.2 ContextSlice 和工具

`always_include`：

- 日志、指标、trace、数据源健康、服务健康、任务失败事件、成本/Token 统计。
- Data Request、Data Readiness、outbox、AgentRun 和 Celery task 的只读诊断视图。

允许工具：

- 只读日志和指标查询。
- 只读 DB 查询与 `EXPLAIN`。
- 诊断命令：`ps`、`top`、`df`、`free`、`netstat`、`curl`、`ping`、`tail`、`grep`、`less`、健康检查脚本。
- SkillPackage：`incident-triage`、`source-health-diagnosis`、`service-health-diagnosis`、`recovery-plan-writing`、`sensitive-log-scan`、`cost-token-observability`、`risk-impact-handoff`。

允许命令：

- `report_incident`
- `request_degradation`
- `request_recovery_validation`
- `request_risk_impact_review`
- `propose_config_change`

禁止：

- 修改代码、配置、权限、业务数据或日志。
- 未经批准重启服务、清理日志、恢复数据库或改变数据源路由。
- 以技术恢复结果替代 Risk 的业务放行。

### 15.3 产物 schema

`IncidentReport` 最小字段：

- `severity`: `P0 / P1 / P2 / P3`
- `incident_type`: `system / data_source / service / execution_environment / security / cost_token`
- `detected_at`
- `affected_services`
- `affected_workflows`
- `root_cause_hypothesis`
- `evidence_refs`
- `current_mitigation`
- `business_impact_unknown_or_known`
- `risk_handoff_required`

`DegradationPlan` 最小字段：

- `degradation_reason`
- `affected_capabilities`
- `fallback_option`
- `data_quality_effect`
- `decision_or_execution_blocking_effect`
- `risk_review_required`
- `rollback_or_recovery_steps`

`RecoveryPlan` 最小字段：

- `preconditions`
- `recovery_steps`
- `validation_checks`
- `residual_risks`
- `risk_release_request_ref`

### 15.4 SOP

1. 接收告警或失败事件，按 P0/P1/P2/P3 分级。
2. 收集 trace、日志、指标、DB read-only evidence，不修改现场。
3. 分类为系统、数据源、服务、执行环境、安全或成本/Token 问题。
4. 识别影响范围：哪些 workflow、AgentRun、data domain、service result 受影响。
5. 提出降级、恢复或配置变更建议；涉及高影响策略必须走治理。
6. 向 Risk Officer 提交业务影响复核请求；DevOps 只证明技术恢复，不证明投资可放行。
7. 生成恢复验证 checklist 和 residual risk。

### 15.5 失败、升级、rubric 和评价

失败处理：

- 需要重启、配置变更、DB 恢复或日志清理：提交 Owner/治理审批，不自行执行。
- 发现敏感日志：提交 Sensitive Log Finding 和 incident，阻断继续泄露。
- 数据源恢复但 quality 仍不足：交 Data/Risk 处理，不宣称可执行。

rubric 与评价指标：

- 诊断准确率、MTTR、复发率。
- 数据源和服务健康报告可复核性。
- 敏感日志发现和脱敏质量。
- 成本/Token 异常识别和优化建议有效性。

## 16. SkillPackage 绑定设计

SkillPackage 以文件包形式存储，PostgreSQL 记录 manifest、version、hash、status、activation、audit、snapshot 和 rollback refs。

文件包结构：

```text
SKILL.md
manifest.yaml
permissions.yaml
deps.lock
scripts/
templates/
tests/
fixtures/
README.md
```

实现约束：

- Runner 只挂载已验证、已激活的 SkillPackage 只读版本。
- SkillPackage 可以读取授权 DB 只读视图；不得持有业务写凭证。
- SkillPackage 更新通过 `propose_skill_update`；低/中影响自动验证和审计后可生效，高影响需 Owner 审批。
- SkillPackage 生效只影响新任务或新 attempt；在途 AgentRun 继续使用旧 `ContextSlice`。
- `permissions.yaml` 必须声明文件读取、网络、终端、DB 只读视图和调用脚本范围；Gateway 和 runner 双层校验。

`manifest.yaml` 最小字段：

- `skill_id`
- `version`
- `owner_agent_or_team`
- `description`
- `allowed_agent_ids`
- `required_tools`
- `db_read_views`
- `network_policy`
- `terminal_policy`
- `output_contracts`
- `tests`
- `fixtures`
- `rollback_from`

### 16.1 Seed Skill specs

V1 不要求把全部 SkillPackage 实现成生产级知识库，但下列 seed skills 必须有可执行 manifest、输入/输出 schema、prompt skeleton 和 fixture validation，避免实现者自行发明核心能力边界。

每个 seed skill 的 prompt skeleton 必须实例化以下结构；表格中的 skeleton 文案是该 skill 的任务核心，不是完整 prompt：

```yaml
role: "绑定 allowed_agent_ids 中的岗位，不得模拟其他 Agent"
input_refs: "只能使用 manifest 声明的 input_schema 和 ContextSlice 引用"
task: "表格 prompt skeleton 中的任务核心"
constraints:
  - "不得越过本 Agent forbidden_actions"
  - "不得把未授权 raw transcript、tool output 或敏感明文作为正式事实"
output_schema: "必须严格符合 output_schema，字段缺失则 failure"
quality_checks:
  - "evidence_refs 非空，且关键判断可追溯"
  - "写明反证、适用条件和失效条件"
  - "需要补证时提交允许的 CollaborationCommand，而不是强行结论"
failure_command: "insufficient_context / evidence_conflict / data_quality_blocked 时返回失败码或 request_* command"
```

| skill_id | allowed_agent_ids | input_schema | output_schema | prompt skeleton | validation |
|---|---|---|---|---|---|
| `ic-chair-briefing` | CIO | RequestBrief、DataReadinessReport、MarketState、ResearchPackage refs | ICChairBrief | “只定义决策问题、边界、关键矛盾、必须回答问题；禁止预设买卖结论。” | fixture 断言 `no_preset_decision_attestation=true` |
| `cio-decision-synthesis` | CIO | DecisionPacket、Memo x4、Consensus、DebateSummary、Optimizer result | CIODecisionMemo | “比较 Analyst 与服务建议，说明行动/不行动、偏离和 Risk handoff。” | fixture 断言重大偏离触发 Owner exception/reopen |
| `market-regime-classification` | Macro Analyst | MarketState engine output、macro/index/liquidity refs | Macro payload subset | “先承认 engine 默认生效，再说明一致/冲突和传导路径。” | fixture 断言 override 留痕但不阻断默认生效 |
| `financial-statement-quality` | Fundamental Analyst | fundamentals、announcements、valuation refs | Fundamental payload subset | “校验财报字段、会计红旗、盈利情景和估值反证。” | fixture 断言关键字段缺失时请求补数 |
| `factor-signal-evaluation` | Quant Analyst | factor_result、market data、market_state refs | Quant payload subset | “解释信号假设、稳定性、regime fit 和择时含义；不得做回测声明。” | fixture 扫描不出现 backtest pass/fail 依赖 |
| `event-catalyst-assessment` | Event Analyst | announcement/news/event refs、source reliability | Event payload subset | “区分 official/structured/news/rumor，supporting evidence 不得单独推进 decision_core。” | rumor-only fixture 必须输出 supporting_evidence_only |
| `risk-review-hard-blocker-check` | Risk Officer | CIO Memo、DataReadiness、portfolio/order/risk refs、hard dissent | RiskReviewReport | “只能输出 approved/conditional_pass/rejected，并判定 repairability。” | rejected fixture 断言 Owner 不能覆盖 |
| `performance-governance-interpretation` | CFO | AttributionReport、risk budget、reflection refs | CFO Interpretation / GovernanceProposal | “解释归因异常，按低/中/高影响生成治理建议。” | high-impact fixture 断言 owner_pending |
| `research-package-builder` | Investment Researcher | query、source refs、knowledge refs | ResearchPackage / TopicProposal | “构造资料包和议题提案；supporting evidence 不直入正式 IC。” | fixture 断言 formal gate 未满足时仅 candidate |
| `incident-triage-diagnostics` | DevOps Engineer | health signals、logs metadata、data source status | IncidentReport / RecoveryPlan | “诊断系统/数据/执行环境异常；技术恢复不等于投资放行。” | fixture 断言 recovery 后仍需 Risk/business guard |

每个 seed skill 的 `tests` 至少包含一个 golden fixture 和一个 boundary fixture；P0 自动化使用 fake LLM 或 deterministic template，不依赖 live LLM。

## 17. 测试与 fixture 映射

| 测试目标 | fixture 应包含 |
|---|---|
| Agent registry 扫描 | 9 个官方 Agent、禁用角色扫描、profile version、status。 |
| CapabilityProfile schema | 第 2.2 节所有字段；每角色非空 mission/authority/context/tools/write/output/SOP/failure/evaluation。 |
| Analyst 独立性 | 四套不同数据域、SkillPackage、role_payload、SOP、rubric、failure policy。 |
| 权限矩阵 | 每角色 allowed/denied command、工具和 artifact 类型；越权 direct write 失败。 |
| ContextSlice | Prompt/Skill/model/tool/config/data policy 版本；Memory/Knowledge 检索摘要；财务敏感脱敏和拒绝记录。 |
| 财务敏感例外 | CFO allow，非 CFO deny，日志不含明文。 |
| SkillPackage | 文件包 hash、manifest、permissions、tests、activation、snapshot、rollback。 |
| Role boundary guard | Event 不输出最终交易，Quant 不回测，CIO 不改状态，Risk 不放行 rejected，Researcher 不改 Prompt，DevOps 不改配置。 |
| Collaboration linkage | AgentRun 输出通过 Gateway 形成 artifact/command/event/comment/proposal，HandoffPacket 可追溯。 |

静态检查建议：

- 扫描 `agent_registry` 不含禁用角色。
- 扫描每个 `CapabilityProfile` 是否具备 `sop/failure_policy/evaluation_policy/output_contracts`。
- 扫描四位 Analyst 的 `role_payload` 字段差异。
- 模拟每个角色一次越权 command 和一次合法 Gateway 写入。
- 模拟 ContextSnapshot 更新后只对新任务或新 attempt 生效。
