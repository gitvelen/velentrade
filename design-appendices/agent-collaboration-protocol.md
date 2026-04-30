# Agent Collaboration Protocol Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 Agent 协作机制的实现契约，承接 `spec.md` 与 `spec-appendices/agent-capability-matrix.md`，不新增正式需求。
- 实现 AgentRun、协作事件、Authority Gateway、CIO 语义主席、Handoff、Trace/Debug 或相关测试时必须读取本附件。
- Command request/response、前端 Trace/Debug read model 和 artifact schema 还必须读取 `contracts/api-read-models.md` 与 `contracts/domain-artifact-schemas.md`。
- 若本文与 `spec.md` 冲突，以 `spec.md` 为准并回到 Requirement 修补。

## 1. 设计原则

- Workflow 是过程权威，PostgreSQL domain tables 是业务事实源。
- Agent 是受控岗位执行者，可读、可推理、可请求、可产物化，不能直接写业务状态。
- 协作不以自由聊天为权威；正式交接以 typed command、artifact、event、handoff 和 reason code 表达。
- CIO/Risk/CFO/Researcher/DevOps 可以作为 semantic lead，但不能越过 workflow guard。
- 所有协作对象都绑定 `workflow_id`、`attempt_no`、`trace_id`、`ContextSnapshot` 或 `ContextSlice`。

## 2. 核心组件

| 组件 | 职责 | 主要依赖 |
|---|---|---|
| Collaboration Service | 管理 CollaborationSession、Command、Event、Handoff 查询和写入 API | PostgreSQL、Authority Gateway |
| Workflow Scheduling Center | 创建模板内 AgentRun、执行准入、维护 stage 和 attempt | PostgreSQL、Celery、Outbox |
| Authority Gateway | 唯一业务写入口，验证 command/artifact/event/handoff 写入权限 | PostgreSQL、policy registry |
| Agent Runner Service | 隔离执行 Agent，持有只读 DB、文件、网络和允许工具，不持有业务写凭证 | read-only DB、mounted SkillPackage |
| Context Engine | 构建 ContextSnapshot/ContextSlice，执行检索、摘要和上下文 fencing | PostgreSQL FTS/pgvector |
| Debate Manager | S3 过程权威，控制轮次、超时、公式重算、DebateSummary 过程字段 | Workflow、Consensus Service |

## 3. 数据模型

### 3.1 collaboration_session

最小字段：

- `session_id`
- `workflow_id`
- `attempt_no`
- `stage`
- `mode`: `ic_debate / research / finance / incident / governance / ad_hoc_support`
- `semantic_lead_agent_id`
- `status`: `open / active / waiting / synthesizing / closed / failed / canceled / expired`
- `context_snapshot_id`
- `participant_agent_ids`
- `opened_by`
- `opened_at`
- `closed_at`
- `close_reason`

约束：

- `status` 不表达业务结果。
- 同一 workflow/stage 可有多个 session，但必须有明确 `mode` 和 reason。

### 3.2 agent_run

最小字段：

- `agent_run_id`
- `workflow_id`
- `attempt_no`
- `stage`
- `session_id`
- `parent_run_id`
- `agent_id`
- `profile_version`
- `run_goal`
- `admission_type`: `auto_accept / semantic_accept / domain_accept / owner_approval`
- `admission_decision_ref`
- `context_snapshot_id`
- `context_slice_id`
- `tool_profile_id`
- `skill_package_versions`
- `model_profile_id`
- `budget_tokens`
- `timeout_seconds`
- `status`: `queued / running / waiting / completed / failed / canceled / timed_out`
- `output_artifact_schema`
- `allowed_command_types`
- `started_at`
- `ended_at`
- `cost_tokens`
- `cost_estimate`

约束：

- AgentRun 不拥有 workflow state transition 权限。
- AgentRun 输出必须通过 Authority Gateway 写入 artifact/event/command。
- 重试创建新 AgentRun，不覆盖旧 run。

### 3.3 collaboration_command

最小字段：

- `command_id`
- `command_type`
- `workflow_id`
- `attempt_no`
- `stage`
- `session_id`
- `source_agent_run_id`
- `source_agent_id`
- `target_agent_id_or_service`
- `payload`
- `requested_admission_type`
- `admission_status`: `pending / accepted / rejected / owner_pending / expired`
- `admission_reason`
- `result_ref`
- `created_at`
- `resolved_at`

`command_type` 必须属于封闭集合；新增类型需治理变更。

payload 最小约束：

- `ask_question`: `question`、`target_context_refs`、`expected_answer_format`。
- `request_view_update`: `artifact_ref`、`requested_fields`、`reason_code`。
- `request_agent_run`: `agent_id`、`run_goal`、`expected_output_artifact_type`、`requested_context_refs`。
- `request_data`: `data_domain`、`required_usage`、`required_fields`、`freshness_requirement`。
- `request_reopen`: `from_stage`、`target_stage`、`reason_code`、`invalidated_artifact_refs`。
- `request_owner_input`: `input_type`、`question`、`timeout_policy`、`no_effect_disposition`。
- `propose_prompt_update` / `propose_skill_update` / `propose_config_change`: `diff_or_manifest_ref`、`impact_level`、`validation_result_refs`、`rollback_plan`。

### 3.4 collaboration_event

最小字段：

- `event_id`
- `event_type`
- `workflow_id`
- `attempt_no`
- `session_id`
- `agent_run_id`
- `command_id`
- `artifact_id`
- `trace_id`
- `payload`
- `created_at`

常见 `event_type`：

- `session_opened`
- `agent_run_created`
- `agent_run_started`
- `tool_progress`
- `command_requested`
- `command_accepted`
- `command_rejected`
- `artifact_submitted`
- `handoff_created`
- `guard_failed`
- `session_closed`

### 3.5 handoff_packet

最小字段：

- `handoff_id`
- `workflow_id`
- `attempt_no`
- `from_stage`
- `to_stage_or_agent`
- `producer_agent_id_or_service`
- `source_artifact_refs`
- `summary`
- `open_questions`
- `blockers`
- `decisions_made`
- `invalidated_artifacts`
- `preserved_artifacts`
- `created_at`

生成粒度：

- 阶段完成。
- semantic lead 完成跨角色综合。
- 跨角色补证完成且影响下游。
- Reopen 前后。

## 4. Command 准入矩阵

| command_type | 默认准入 | 可触发 AgentRun | 典型接收者 |
|---|---|---:|---|
| `ask_question` | auto_accept | 否 | Agent / semantic lead |
| `request_view_update` | semantic_accept | 是 | 原 Memo producer |
| `request_peer_review` | semantic_accept | 是 | 同域或指定 Agent |
| `request_agent_run` | semantic_accept/domain_accept | 是 | Workflow |
| `request_data` | auto_accept/domain_accept | 否 | Data Service |
| `request_evidence` | auto_accept/semantic_accept | 可选 | Researcher / Agent |
| `request_service_recompute` | domain_accept | 否 | Service Orchestration |
| `request_source_health_check` | domain_accept | 可选 | DevOps |
| `request_reopen` | domain_accept | 否 | Workflow / Risk |
| `request_pause_or_hold` | domain_accept | 否 | Workflow / Risk |
| `request_resume` | domain_accept | 否 | Workflow / Risk |
| `request_owner_input` | owner_approval 或 confirmation | 否 | Owner UI |
| `request_manual_todo` | auto_accept/domain_accept | 否 | Task Center |
| `request_reflection` | semantic_accept | 是 | CFO / responsible Agent |
| `propose_knowledge_promotion` | semantic_accept | 否 | Researcher / Governance |
| `propose_prompt_update` | semantic_accept/owner_approval | 否 | Governance |
| `propose_skill_update` | semantic_accept/owner_approval | 否 | Governance |
| `propose_config_change` | domain_accept/owner_approval | 否 | Governance |
| `report_incident` | auto_accept | 可选 | DevOps / Incident Workflow |
| `request_degradation` | domain_accept | 否 | DevOps / Risk |
| `request_recovery_validation` | domain_accept | 可选 | DevOps / Risk |
| `request_risk_impact_review` | domain_accept | 是 | Risk |

## 5. IC 协作流程

1. S1 完成 Data Readiness 后，Workflow 创建 CIO AgentRun，目标是生成 IC Chair Brief。
2. Workflow 创建四个 S2 Analyst AgentRun，分别绑定独立 profile、role-specific SkillPackage 和 ContextSlice。
3. 四位 Analyst 提交 Analyst Memo，Authority Gateway 校验统一外壳、role_payload、证据引用和禁止越权字段。
4. Consensus Service 计算共识和行动强度。
5. Debate Manager 根据阈值决定 `debate_skipped` 或打开 S3 CollaborationSession。
6. 若进入 S3，CIO 作为 semantic lead 生成 agenda，四位 Analyst 通过 `request_view_update`、`request_evidence`、`ask_question` 完成最多 2 轮辩论。
7. Debate Manager 生成过程字段，CIO 生成 synthesis 字段，合成 DebateSummary。
8. 若 guard 允许，Workflow 创建 S4 CIO Decision AgentRun；否则阻断、重开或进入 Risk handoff。

## 6. API 边界

后端内部服务 API 使用 typed command，不暴露任意 SQL 写入。

REST 入口和 DTO 以 `contracts/api-read-models.md` 为准。本附件约束协作专属入口：

- `POST /api/collaboration/commands`
- `POST /api/gateway/artifacts`
- `POST /api/gateway/events`
- `POST /api/gateway/handoffs`
- `GET /api/collaboration/sessions/{session_id}`
- `GET /api/workflows/{workflow_id}/agent-runs`
- `GET /api/workflows/{workflow_id}/collaboration-events`
- `GET /api/workflows/{workflow_id}/handoffs`

所有写入接口必须：

- 校验当前 workflow/attempt/stage。
- 校验 source agent 的 CapabilityProfile。
- 校验 command_type 是否允许。
- 校验 artifact/event/handoff payload schema_version。
- 校验 `context_snapshot_id` 与 AgentRun 绑定一致。
- 校验 `idempotency_key`，重复请求返回同一写入结果，不生成重复 artifact/event。
- 写 audit event。
- 通过 outbox 发布异步任务。
- 返回统一错误响应；`command rejected` 不改变 workflow state。

Gateway 写入顺序固定为：schema validation -> permission check -> stage guard -> snapshot match -> append-only write -> audit_event -> outbox_event。实现不得在任一步失败后保留半写入。

Trace/Debug read model 必须能回放 session/run/command/event/handoff、ContextSlice、Gateway 写入和拒绝记录；字段见 `contracts/api-read-models.md` 的 `read_models.TraceDebugReadModel`。

## 7. 错误与降级

| 场景 | 处理 |
|---|---|
| AgentRun timeout | 写 `agent_run.timed_out` event，stage 进入 waiting/blocked，按模板决定重试或 request_reopen。 |
| command rejected | 写拒绝原因，不改变 workflow state。 |
| semantic lead 不响应 | session 进入 waiting，达到超时后由 workflow guard 关闭、重试或升级。 |
| DebateSummary schema fail | 重开 S3；若缺新证据回 S2。 |
| Runner 直接业务写入 | DB credential 层拒绝，Authority Gateway 记录 security event。 |
| 财务敏感字段越权读取 | 返回 `sensitive_data_restricted`，记录审计事件。 |

## 8. 测试重点

- 封闭命令集扫描。
- AgentRun 准入矩阵。
- Runner 无业务写凭证。
- Authority Gateway append-only 写入。
- IC Chair Brief 不预设结论。
- DebateSummary 同时包含过程字段和 CIO 语义字段。
- HandoffPacket 在阶段/跨角色交接生成。
- Trace/Debug 能回放 session/run/command/event/handoff。

## 9. R8 Runbook 标准

本附件的实现输入不以对象存在为完成标准。任何实现必须能按以下 runbook 证明协作如何发生、如何被准入、如何进入 artifact、如何展示、如何测试。

每个协作 runbook 必须包含：

- trigger：触发事件和所属 workflow/stage。
- participants：semantic lead、process authority、required agents/services。
- preconditions：TaskEnvelope、ContextSnapshot、已有 artifact、service result。
- command flow：允许的 command、准入类型、拒绝/过期处理。
- artifact flow：哪些输出进入正式 artifact，哪些只进 event/process archive。
- failure path：timeout、schema fail、service unavailable、permission denied、sensitive data denied、reopen/block。
- view projection：Owner/Dossier/TraceDebug 分别看到什么。
- verification：TC、fixture、report 和 read model 断言。

### 9.1 CollaborationSession 生命周期

```text
open
 -> active
 -> waiting | synthesizing
 -> active | closed
terminal: failed | canceled | expired
```

状态只表达协作容器运行状态，不表达业务结果。Risk rejected、low consensus、owner_timeout、data degraded、execution blocked 必须写入 workflow state、artifact payload、reason code 或 ReopenEvent。

创建 session 的合法入口：

- workflow template 进入需要多 Agent 协作的 stage。
- semantic lead 请求补证、追问、观点更新或反思。
- domain lead 请求 Risk/CFO/DevOps/Researcher 交接。
- workflow guard 发现 schema fail、证据不足或服务异常，需要协作修复。

semantic lead 选择规则：

| task_type / session mode | 默认 semantic lead | 说明 |
|---|---|---|
| `investment_workflow` / `ic_debate` | CIO | 只主持投资 IC 的议题、追问、综合和 S4 决策语义，不承担全局任务调度。 |
| `research_task` / `research` 或 `cross_agent_evidence` | Investment Researcher | 承接热点学习、资料整理、知识检索和候选议题准备；事件事实判断可请求 Event Analyst。 |
| `finance_task` / `finance_reflection` | CFO | 承接财务解释、规划、预算和反思范围确认。 |
| `system_task` / `incident` | DevOps Engineer | 承接系统、数据源、服务、执行环境、安全或成本异常。 |
| `governance_task` / `governance` | 变更责任域对应 Agent；跨域时由 Governance Runtime 指定 primary lead | 只能形成 proposal、validation 和 handoff，不能直接生效。 |
| `manual_todo` | 无 Agent semantic lead | 只生成 Task Center 人工待办；如需解释，另开 research/finance/system task。 |

未命中明确规则、多个 semantic lead 冲突或任务目标不清时，不创建 CollaborationSession；Workflow 必须把 TaskEnvelope 保持在 draft/waiting，并通过 RequestBrief preview 或 `request_owner_input` 追问。

关闭 session 的必需动作：

- 写 `session_closed` event。
- 若对下游有影响，生成 HandoffPacket。
- 若产生正式结论，必须引用 accepted artifact。
- 若关闭原因是失败、过期或取消，必须写 close_reason 和 unresolved blockers。

## 10. IC 辩论 Runbook

trigger：

- `consensus_score >= 0.8` 且存在 hard dissent。
- `0.7 <= consensus_score < 0.8`。
- 高共识但 `action_conviction < 0.65` 且 CIO 请求补证。
- DebateSummary schema fail 后重开 S3。

participants：

- semantic lead：CIO。
- process authority：Debate Manager / Workflow Scheduling Center。
- required agents：Macro、Fundamental、Quant、Event。
- services：Consensus Service；Data/Service Orchestration 只按 command 补证。
- forbidden：Owner 不参与普通辩论；Risk 不提前裁决，除非 hard dissent handoff 到 S5。

steps：

1. Debate Manager 打开 `CollaborationSession(mode=ic_debate)`，绑定 workflow、attempt、S3、ContextSnapshot 和四份 Memo。
2. CIO AgentRun 读取 Chair Brief、Memo x4、Consensus/action_conviction，提交 agenda 和 questions；禁止预设买卖结论。
3. Debate Manager 创建 round 1，向四 Analyst 派发 questions；每个 question 写 CollaborationEvent。
4. Analyst 只能提交 comment、view_update、request_evidence 或 request_peer_review；不得覆盖原 Memo。
5. 新 evidence 必须通过 `request_evidence` 进入 Researcher/Data Service，不得在聊天 transcript 中直接成为正式事实。
6. Debate Manager 收集 responses，记录 timeout、缺席、view_changes 和 unresolved issues。
7. Consensus Service 使用最新 accepted view_update 重算 consensus_score 和 action_conviction。
8. CIO 提交 synthesis、resolved_issues、unresolved_dissent 和 chair_recommendation_for_next_stage。
9. Debate Manager 判断 converged、no_new_evidence、retained_hard_dissent、low_action_conviction_blocked 或 max_rounds_reached；最多两轮。
10. 关闭 session，生成 DebateSummary；若影响下游，生成 HandoffPacket 给 S4/S5。

failure_paths：

- Analyst timeout：记录 timeout event；不伪造观点更新；材料不足时 stage waiting/blocked。
- `request_evidence` 被拒绝：保留拒绝原因，CIO synthesis 必须说明证据缺口。
- DebateSummary schema fail：重开 S3；若缺新证据则 request_reopen 到 S2。
- hard dissent retained：`risk_review_required=true`，S5 必须显式评估。
- action_conviction < 0.65：不得生成纸面执行授权。

view_projection：

- Owner Decision View：只展示“存在保留异议/已进入风控/不执行原因”。
- Investment Dossier：展示 Dissent Board、Debate Timeline、view_update、CIO synthesis、Handoff。
- Trace/Debug：展示 Session、rounds、Command、Event、AgentRun、ContextSlice、Gateway write。

verification：

- `TC-ACC-017-01` / `FX-HIGH-CONSENSUS-HARD-DISSENT`。
- `TC-ACC-017-01` / `FX-MEDIUM-CONSENSUS-HARD-DISSENT`。
- `debate_dissent_report.json` 必须包含 command/event trace、round inputs/outputs、retained hard dissent、recomputed scores 和 blocked execution。

## 11. 跨 Agent 补证 Runbook

trigger：

- Memo、Decision、Risk Review、CFO Interpretation 或 IncidentReport 证据不足。
- semantic lead 发现 artifact 缺少关键解释。
- DevOps incident 影响 DataReadiness、ServiceResult、AgentRun 或 Execution。
- Researcher 发现新资料可能影响当前 IC、反思或知识晋升。
- schema pass 但 semantic review 发现证据链不足。

steps：

1. requesting Agent 提交 CollaborationCommand：`ask_question`、`request_evidence`、`request_view_update` 或 `request_peer_review`。
2. Authority Gateway 校验 source AgentRun、stage、command_type、profile 权限和 ContextSnapshot。
3. Collaboration Service 执行准入：`auto_accept / semantic_accept / domain_accept / owner_approval`。`semantic_accept` 交当前 semantic lead 判断相关性。
4. accepted 后创建 target task 或 target AgentRun；轻量 answer/comment 可不创建新 AgentRun，需要正式 artifact 时必须创建。
5. target 读取原 artifact、问题、证据引用和 ContextSlice；不得读取未授权财务敏感明文。
6. target 输出 answer/comment、evidence artifact、view_update、peer_review_note 或 failure。
7. Authority Gateway 校验输出 schema、producer 权限、source_refs、evidence_refs 和禁止覆盖原 artifact。
8. CollaborationEvent 记录 requested、accepted/rejected、started、submitted、expired。
9. 若补证影响下游，生成 HandoffPacket，注明新增证据、未解决问题、保留旧结论和下游消费方。
10. Workflow guard 判断继续、waiting、blocked、reopen 或 close。

allowed：

- 对他人 artifact 追加 comment。
- 提交 view_update，声明观点变化、原因和引用。
- 提交 evidence artifact、ResearchPackage 或 peer_review_note。
- 请求 reopen，但不能直接 reopen。

forbidden：

- 覆盖其他 Agent 原 Memo/Decision/Risk Report。
- 把聊天 transcript 或 tool output 原文作为正式事实。
- 未经准入创建 AgentRun。
- 用补证绕过 stage guard。
- 非 CFO Agent 请求财务敏感明文。
- Researcher 直接改 Prompt/Skill/默认上下文。

verification：

- `FX-AGENT-COLLABORATION-PROTOCOL`：证明 command 准入、AgentRun 创建、view_update、handoff 和 Trace 回放。
- `FX-SUPPORTING-EVIDENCE-ONLY`：Event/Researcher 补证只能进入 supporting evidence，不能成为 decision_core。
- `FX-RISK-REJECTED-NO-OWNER-OVERRIDE`：补证不能绕过 Risk rejected。

## 11.1 研究任务协作 Runbook

trigger：

- Owner 在自由对话中要求学习热点事件、整理资料、调研主题、准备议题或理解对持仓/行业的影响。
- Daily Brief、知识检索或 Researcher 发现 supporting evidence，但未满足正式 IC 硬门槛。

participants：

- semantic lead：Investment Researcher。
- process authority：Workflow Scheduling Center。
- optional agents：Event Analyst 评估公告/舆情/事件来源，Macro/Fundamental/Quant 仅在 Researcher 通过 `request_agent_run` 明确请求时参与。
- forbidden：CIO 不主持普通研究任务；研究任务不能直接进入 S5/S6、Owner approval 或纸面执行。

steps：

1. confirmed `research_task` 创建 Researcher AgentRun，绑定 RequestBrief、ContextSnapshot、允许工具和输出 schema。
2. Researcher 先产出研究计划和 source refs；需要数据时提交 `request_data`，需要事件判断时提交 `request_evidence` 或 `request_agent_run` 给 Event Analyst。
3. 补证命令经 auto/semantic/domain accept 后创建目标 AgentRun 或 service call；拒绝、超时和敏感数据拒绝都写 CollaborationEvent。
4. Researcher 汇总 accepted evidence，输出 ResearchPackage、SearchSummary、MemoryCapture 或候选 TopicProposal。
5. 若资料显示可能进入投资链，只生成候选 TopicProposal，由 Opportunity/Topic Queue 重新做硬门槛和评分；不得把 research_task 原 session 改造成正式 IC。
6. 若只适合学习沉淀，输出 MemoryCapture/Knowledge candidate，并按知识治理生效边界处理。
7. session 关闭时生成 HandoffPacket，列出可用证据、未解决问题、是否建议进入 Topic Queue、以及不能直接交易的 reason_code。

failure_paths：

- 热点来源不可靠：ResearchPackage 标记 source quality，TopicProposal 不进入正式队列。
- 证据不足：任务 waiting/blocked，列出缺口和建议补充来源。
- 用户原意不清：通过 `request_owner_input` 追问，不创建额外 AgentRun。
- 发现持仓风险或重大公告：生成候选 TopicProposal，必要时 P0 抢占，但仍不得跳过 S1-S7、Risk 和审计。

view_projection：

- Owner Decision View：显示研究任务状态、是否需要补充输入、是否产生候选议题。
- Knowledge/Research 详情：展示 ResearchPackage、source quality、MemoryCapture、TopicProposal 候选和下一步建议。
- Trace/Debug：展示 Researcher/Event AgentRun、request_data/request_evidence、拒绝原因、Handoff。

verification：

- `TC-ACC-006-01` 覆盖自由对话到 research task 的 preview 和任务卡。
- `TC-ACC-005-01` 覆盖 Researcher 请求 Event/Data 补证的 CollaborationCommand 链。
- `FX-SUPPORTING-EVIDENCE-ONLY` 证明 supporting evidence 不直接生成正式 IC、审批或执行。

## 12. DevOps 与财务反思协作 Runbook

DevOps handoff：

1. Incident Workflow 创建 DevOps AgentRun。
2. DevOps 输出 IncidentReport、DegradationPlan 或 RecoveryPlan。
3. 若影响 decision_core、execution_core、CIO/Risk/Execution 输入或敏感日志，提交 `request_risk_impact_review`。
4. Risk Officer 判断业务影响；DevOps 技术恢复不能直接 resume 投资执行。
5. Trace/Debug 显示 incident -> affected workflow/artifact -> Risk handoff -> guard decision。

Finance reflection：

1. Attribution anomaly 或 periodic window 创建 Reflection Workflow。
2. CFO 作为 semantic lead 确认 scope、responsible_agent 和 questions。
3. responsible Agent 提交 first draft；只能写 ReflectionRecord，不得热改 Prompt/Skill/配置。
4. Researcher 提交 Knowledge/Prompt/Skill Proposal。
5. Governance Runtime triage；低/中影响自动验证，高影响 Owner approval。
6. 生效只绑定新任务或新 attempt；在途 AgentRun 继续旧 ContextSnapshot。

verification：

- `devops_incident_report.json` 必须证明 recovery 后仍需 Risk/workflow guard。
- `reflection_learning_report.json` 必须证明 responsible Agent 一稿、Researcher proposal 和 no hot patch guard。
