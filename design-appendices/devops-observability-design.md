# DevOps Observability Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 DevOps incident、health、degradation、recovery、Risk notification、成本/Token 观测和敏感日志发现的实现契约。
- 实现 `src/velentrade/domain/devops/**`、`src/velentrade/domain/observability/**` 或 `TC-ACC-029` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`design-appendices/agent-capability-profiles.md` 和 `contracts/domain-artifact-schemas.md`，不新增正式需求。

## 1. 职责边界

DevOps Engineer 负责系统、数据源、服务、执行环境、日志安全和成本/Token 观测的诊断与恢复建议。业务影响由 Risk Officer 裁决。

DevOps 不能：

- 替代 Risk Officer 做业务风险放行。
- 以技术恢复结果直接恢复投资执行。
- 热改高影响配置。
- 绕过 Data Request、Authority Gateway、Governance runtime。

## 2. Incident 模型

Incident 类型：

- `system`
- `data_source`
- `service`
- `execution_environment`
- `security`
- `cost_token`

状态机：

```text
detected -> triaged -> mitigating -> monitoring -> closed
terminal: unresolved | escalated
```

`IncidentReport` 必须记录：

- incident_type、severity、affected_workflows、affected_data_domains。
- detected_by、technical_summary、evidence_refs。
- business_impact_unknown/pass_to_risk 标记。
- risk_notification_ref。
- current_status。

## 3. Health Check Contract

| Health check | 输入 | 输出 | 降级边界 |
|---|---|---|---|
| source health | source registry、最近 DataRequest、错误率、限频 | source status、fallback suggestion | 不改变 source priority，除非治理生效 |
| service health | service call、latency、timeout、schema fail | service status、retry/degradation suggestion | 不伪造 service result |
| execution environment | trading calendar、minute data、fee config、worker health | execution precheck status | execution_core 不足必须阻断 |
| runner health | AgentRun duration、timeout、tool error、write denial | runner incident/diagnostic | 不重跑业务状态，需 workflow guard |
| log security | log scan、trace archive、error payload | Sensitive Log Finding | 敏感泄露需 security incident |
| cost/token | model profile、token/cost、budget trend | observability summary | 只作运营观测，不作为 P0 pass/fail |

默认阈值：

| Health check | P0 / blocked | P1 / incident | P2 / degraded | P3 / observe |
|---|---|---|---|---|
| source health | execution_core critical field 缺失、critical conflict、主备源均失败 | decision_core source 连续 2 次 timeout 或错误率 `>=20%/15m` | display/research source 错误率 `>=10%/30m` 且有 fallback | 单次 timeout、限频接近上限 |
| service health | Risk/Execution 必需服务 timeout 或 schema fail 且无可用旧结果 | CIO/Risk/Execution 输入服务 `p95 latency > 10s` 持续 10m 或 timeout rate `>=10%` | 非关键服务 `p95 latency > 5s` 或单次 fallback | 单次重试成功 |
| execution environment | 交易日历、停复牌、分钟线、费用税费任一 execution_core 输入不可用 | 分钟线延迟 `>5m` 或执行窗口内 freshness fail | 非当前订单执行数据延迟 | 盘后数据延迟 |
| runner health | runner 直接写业务表、敏感字段越权、影响 active workflow 的 AgentRun 全部超时 | AgentRun 超过 `timeout_seconds` 或 tool error rate `>=15%/30m` | 单角色连续 2 次 schema fail | 单次可重试 tool error |
| log security | 财务敏感明文进入普通日志/trace 或非授权 archive | 错误日志疑似敏感字段需人工确认 | 脱敏规则命中但已阻断 | 扫描统计异常 |
| cost/token | 不作为 P0 | 单日 cost/token 较 20 日中位数 `>=2x` 且影响模型路由建议 | 连续 3 日 `>=1.5x` | 单日 `>=1.2x` |

阈值用于 V1 默认实现；修改阈值、降级策略或模型路由属于配置治理。成本/Token 阈值只触发观测报告或治理提案，不让 P0 验收失败。

## 4. Degradation 与 Recovery

降级原则：

- 数据和服务异常优先安全降级，不优先维持自动执行连续性。
- 安全降级可自动，风险放宽不能自动。
- decision_core 降级可继续研究；execution_core 不足不得成交。
- 系统恢复不等于投资任务可继续执行。

安全自动降级白名单：

| 自动动作 | 允许条件 | 禁止事项 |
|---|---|---|
| source fallback | Data Source Registry 中已有同 domain/usage fallback，且 schema/data quality pass | 自动改变 source priority 或新增数据源 |
| research/display cache | required_usage 为 `display` 或 `research`，并展示 stale/freshness 标记 | 用缓存生成新 decision_core 或 execution_core |
| degraded ServiceResult | 服务 timeout 但可输出明确 limitations、input refs 和 output_quality_score | 伪造完整 service result 或隐藏限制 |
| stage waiting/blocked | guard 判定输入缺失、schema fail、data blocked、service unavailable | 自动批准 Owner/Risk/Execution 放行 |
| incident / Risk notification | 影响 active workflow、decision_core、execution_core、敏感日志或权限 | DevOps 自行裁决业务风险 |

风险放宽黑名单：降低 `decision_core/execution_core` 阈值、放宽 Risk hard blocker、允许 Risk rejected 后继续、扩大 Owner approval 生效范围、热改 Prompt/Skill/配置、改变执行参数或费用税费口径。这些只能走治理或 Risk/workflow guard，不可由 DevOps 自动执行。

`DegradationPlan`：

- incident_ref。
- fallback_option。
- affected_usage。
- auto_allowed。
- owner_or_governance_required。
- risk_review_required。

`RecoveryPlan`：

- validation_steps。
- technical_recovery_status。
- residual_risk。
- risk_review_required。
- investment_resume_allowed 固定为 false；真正恢复由 workflow/Risk guard 决定。

Recovery validation 默认 checklist：

```yaml
validation_steps:
  - reproduce_failure_cleared: "原 health probe 或失败 fixture 重新执行为 pass"
  - schema_validation: "受影响 ServiceResult / DataReadiness / IncidentReport schema pass"
  - data_quality_recompute: "受影响 data_domain 重新计算 quality band 和 critical fields"
  - affected_workflow_replay: "至少重放一个受影响 workflow 的 guard，不直接 resume"
  - no_fabricated_result: "timeout/degraded 期间没有伪造完整结果"
  - sensitive_log_rescan: "若涉及日志/权限，复扫普通日志、error payload 和 trace archive"
  - risk_notification_complete: "若影响 business input，RiskNotification 含业务问题、建议 hold/reopen 和 evidence_refs"
  - investment_resume_allowed_false: "RecoveryPlan 固定 investment_resume_allowed=false"
```

DevOps 只能把 checklist 结果写入 RecoveryPlan；workflow/Risk 决定 resume、reopen、继续 blocked 或 close。

## 5. Risk Handoff

以下情况必须向 Risk Officer 交接：

- execution_core 曾被阻断后数据源恢复。
- service outage 影响 CIO/Risk/Execution 输入。
- Data conflict 涉及重大财报、停复牌、交易日历、持仓/风险约束。
- 敏感日志或权限事件可能污染过程档案。
- DevOps 建议改变数据源策略、服务降级策略或执行参数。

Risk notification 最小字段：

```yaml
notification_id: string
incident_ref: string
affected_workflows: string[]
affected_stage_or_artifact_refs: string[]
technical_status: string
business_question_for_risk: string
recommended_hold_or_reopen: string
evidence_refs: string[]
```

## 6. Observability

结构化日志必须包含：

- trace_id、workflow_id、attempt_no、stage。
- agent_run_id、artifact_id、command_id。
- context_snapshot_id、skill_package_versions。
- latency、token、cost、model_profile。

Prometheus 指标：

- workflow_stage_duration_seconds。
- agent_run_duration_seconds/status。
- collaboration_command_accepted_total / rejected_total。
- data_quality_score_distribution。
- execution_core_block_total。
- model_token_total / cost_estimate_total。
- runner_write_denial_total。
- sensitive_field_access_denial_total。
- incident_open_total by type/severity。

普通日志、错误日志、LLM trace 默认脱敏；raw process transcript 若保存，进入加密/受限 process archive。

## 7. Sensitive Log Finding

触发：

- 财务敏感原始字段出现在普通日志、错误日志、LLM trace 或 process archive 非授权区域。
- 非 CFO AgentRun 获取明文字段。
- runner 尝试直接写业务表。

处理：

- 写 `security_finding`。
- 写 `sensitive_field_access_event` 或 `runner_write_denial`。
- 生成 incident，severity 由字段类型和传播范围决定。
- 通知 DevOps；涉及业务影响时交 Risk。
- 不自动删除审计证据；用受控修复/脱敏 artifact 保留追溯。

## 8. 验证映射

`devops_incident_report.json` 必须证明：

- 数据源故障、服务超时、纸面执行环境异常和 Token 成本异常 fixture 都能生成正确 incident。
- DevOps 输出 IncidentReport、DegradationPlan、RecoveryPlan。
- 需要业务判断时生成 Risk notification。
- execution_core 数据恢复后不会直接放行投资执行。
- 成本/Token 仅为观测，不作为 V1 验收 pass/fail。
- 敏感日志发现能生成安全事件和审计记录。

## 9. R8 DevOps Operating Runbook

本附件必须让实现者和 DevOps Agent 知道日常看什么、异常如何分级、怎么恢复、何时交给 Risk。指标存在不等于可运维。

### 9.1 日常巡检节奏

| 时段 | 检查项 | 目标 | View |
|---|---|---|---|
| 开盘前 | 数据源可用性、交易日历、分钟线、停复牌、费用税费参数、worker/runner health | 确认 S1/S6 基础条件 | Governance Health、Owner attention 摘要 |
| 盘中 | DataRequest 错误率、fallback、execution_core blocked、AgentRun timeout、service latency、outbox backlog | 发现影响 active workflow 的异常 | Dossier blocker、Trace incident |
| 收盘后 | PaperExecutionReceipt、归因任务、持仓监控、异常订单、数据延迟 | 确保 S7 和次日风险输入 | DevOpsHealth、Attribution status |
| 每日运维 | token/cost、日志脱敏、sensitive access denial、runner write denial、trace archive 访问 | 发现运营和安全异常 | Governance Health、Audit Trail |

Owner 首屏只展示需要注意的 degraded、blocked、incident 和 Risk handoff 状态，不展示完整指标墙。

### 9.2 Severity 默认口径

| severity | 条件 | 默认动作 |
|---|---|---|
| P0 | 影响 execution_core、Risk Review 输入、安全泄露、runner 直接写入、可能导致错误执行 | 立即 incident，相关 workflow blocked，交 Risk 或安全处理 |
| P1 | 影响 decision_core、active IC、CIO/Risk/Execution 必需服务结果 | incident，stage waiting/blocked，必要时 request_reopen |
| P2 | 影响研究、展示、非关键数据且有 fallback | degraded，保留 workflow 推进限制 |
| P3 | 成本、延迟、单次失败或非阻塞告警 | 观测记录，不影响 P0 验收 pass/fail |

### 9.3 Incident 处理流程

```text
1. health probe、workflow guard、AgentRun failure 或 log scan 生成 incident candidate。
2. Workflow 创建 system_task 或 incident record；必要时创建 DevOps AgentRun。
3. DevOps 读取 logs、metrics、trace、只读 DB diagnostic view，不修改现场。
4. DevOps 分类 incident_type 和 severity。
5. DevOps 识别 affected_workflows、affected_stage、affected_data_domains、affected_artifacts、affected_agent_runs。
6. DevOps 提交 IncidentReport。
7. 若存在安全降级路径，提交 DegradationPlan。
8. 若需要技术恢复，提交 RecoveryPlan 和 validation checks。
9. 若影响 decision_core、execution_core、CIO/Risk/Execution 输入、敏感日志或权限，提交 Risk notification。
10. Workflow 根据影响范围让相关 stage waiting/blocked，或仅投影 degraded 展示。
11. 技术恢复后，DevOps 只能提交 recovery validation。
12. Risk/workflow guard 决定 resume、reopen、继续 blocked 或关闭。
```

### 9.4 分类 runbook

source health：

- trigger：source timeout、限频、schema 变化、critical field 缺失、多源冲突。
- output：SourceHealthReport、DataConflictReport 或 IncidentReport。
- guard：不得自动改变 source priority；数据源策略变化走 governance。

service health：

- trigger：服务超时、schema fail、latency 超阈值、output_quality 低于输入质量。
- output：ServiceHealthReport、DegradationPlan。
- guard：不得伪造 service result；不直接做投资判断。

runner health：

- trigger：AgentRun timeout、tool error、ContextSnapshot mismatch、direct write denial。
- output：RunnerDiagnostic、CollaborationEvent、必要时 security incident。
- guard：重试创建新 AgentRun，不覆盖旧 run。

execution environment：

- trigger：交易日历异常、分钟线缺失、停复牌/涨跌停状态缺失、费用参数缺失。
- output：ExecutionPrecheck、IncidentReport。
- guard：execution_core blocked 时纸面执行严格阻断。

log/security：

- trigger：财务敏感字段出现在普通日志/trace、非 CFO 访问明文、runner 写业务表。
- output：SensitiveLogFinding、security incident、audit event。
- guard：不删除审计证据；修复通过受控脱敏 artifact。

cost/token：

- trigger：token/cost 异常增长、模型 profile budget trend 异常。
- output：CostTokenObservabilityReport。
- guard：只作运营观测；若建议改 model route/budget，走 governance。

### 9.5 Risk Handoff View

Risk notification 必须能被 Dossier、Governance Health 和 Trace/Debug 同时解释：

- Dossier：显示技术状态、业务问题、建议 hold/reopen、影响 artifact。
- Governance Health：显示 incident severity、current_status、Risk handoff status。
- Trace/Debug：显示 incident -> affected workflow -> DevOps evidence -> Risk decision -> workflow guard。

### 9.6 R8 Verification

`devops_incident_report.json` 必须证明：

- 数据源故障导致 DataReadiness degraded/blocked，不伪造正常数据。
- 服务 timeout 不生成完整 ServiceResult。
- execution_core 恢复后不能自动执行，必须经 Risk/workflow guard。
- sensitive log finding 生成 security incident 和审计记录。
- token/cost 异常只进入 observability，不作为 P0 pass/fail。
- DevOps RecoveryPlan 的 `investment_resume_allowed=false`。
