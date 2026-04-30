# 06. Governance Page

## 0. 页面目标

治理页回答：“所有任务、审批、Agent 团队、配置变更、系统健康和审计证据分别在哪里处理；哪些事项需要 Owner 真正审批，哪些只是 confirmation 或 manual_todo。”

主要路由：

- `/governance`
- `/governance/team`
- `/governance/team/:agentId`
- `/governance/team/:agentId/config`
- `/governance/approvals/:approvalId`

页面归属：

- `/governance`、Agent 团队相关 route 和 `/governance/approvals/:approvalId` 均归属主菜单“治理”。
- 治理页可以从 Task、Health、Audit 链接到投资 Dossier 或 workflow Trace，但不改变这些目标页面的 canonical parent menu。
- Governance Health/Audit 对非投资 incident 只展示 trace 摘要、trace_id、相关对象和恢复状态；V1 不新增独立 incident trace route。

主要 read model：

- `GovernanceReadModel`
- `TaskCenterReadModel`
- `ApprovalCenterReadModel`
- `ApprovalRecordReadModel`

## 1. 首屏布局

```text
顶部：治理总览、待审批、阻断、事故、草案数量
二级模块切换：任务 / 审批 / Agent 团队 / 变更 / 健康 / 审计
第一组：任务中心 / 审批中心
第二组：Agent 团队 / 变更管理
第三组：系统健康 / 审计记录
详情：Approval Packet 或 Task Detail 抽屉
```

进入 Agent 团队的主路径：点击治理页二级模块切换中的 `Agent 团队`，进入 `/governance/team`。治理页中的 Agent 团队卡片、全景团队草案卡和变更管理中的 Agent 能力变更记录都可以作为辅助入口，但不能替代二级模块切换。

## 2. 任务中心

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-001 | task_id | 可点击 |
| GOV-002 | task_type | investment、governance、incident、manual_todo、research、finance |
| GOV-003 | priority | P0/P1/P2 |
| GOV-004 | state | queued、running、waiting、blocked、completed、expired |
| GOV-005 | owner_role | Owner、Workflow、Agent、Service |
| GOV-006 | related_object | workflow、asset、agent、proposal、incident |
| GOV-007 | blocked_reason | reason_code |
| GOV-008 | due_at | 到期时间 |
| GOV-009 | next_action | 查看、补资料、等待、进入审批、打开相关详情或审计摘要 |

筛选：

| 编号 | 筛选 | 选项 |
|---|---|---|
| GOV-010 | task_type | investment、governance、incident、manual_todo、research、finance |
| GOV-011 | state | active、blocked、waiting、completed、expired |
| GOV-012 | priority | P0/P1/P2 |
| GOV-013 | owner_role | Owner、Agent、Service、Workflow |
| GOV-014 | reason_code | risk_rejected、execution_core_blocked、owner_timeout 等 |

规则：

- `GOV-015`: 人工待办在任务中心，不进入审批中心。
- `GOV-016`: investment task 绑定 S0-S7 和 reason code。
- `GOV-017`: incident 使用 incident 状态机，不伪装成审批。

## 3. 审批中心

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-018 | approval_id | 可点击 |
| GOV-019 | approval_type | owner_exception、high_impact_governance、agent_capability_high |
| GOV-020 | target | workflow、governance_change、agent_capability_change |
| GOV-021 | recommendation | 推荐结论 |
| GOV-022 | impact_scope | 影响范围 |
| GOV-023 | due_at | 超时默认 |
| GOV-024 | status | pending、approved、rejected、request_changes、expired |
| GOV-025 | evidence_refs | 证据引用 |

规则：

- `GOV-026`: 审批中心不包含请求确认。
- `GOV-027`: 审批中心不包含人工待办。
- `GOV-028`: Risk rejected 不生成审批包；若读到相关 approval，前端显示数据错误和 blocked。

## 4. Approval Packet

路由：`/governance/approvals/:approvalId`

| 编号 | 区块 | 必须展示 |
|---|---|---|
| GOV-029 | 审批对象 | 目标、类型、当前状态、client_seen_version |
| GOV-030 | 触发原因 | reason_code、来源事件 |
| GOV-031 | 推荐结论 | 推荐 approved/rejected/request_changes |
| GOV-032 | 对比方案 | 推荐方案、替代方案、不做方案 |
| GOV-033 | 风险与影响范围 | 资金、风控、上下文、任务范围 |
| GOV-034 | 证据引用 | artifact、read model、trace_id |
| GOV-035 | 生效边界 | new_task、new_attempt、当前 workflow 例外等 |
| GOV-036 | 超时默认 | 不执行、不生效、S6 blocked 或 expired |
| GOV-037 | 回滚方式 | rollback_plan_ref |
| GOV-038 | 决策历史 | previous decisions、request_changes |

Owner 动作：

| 编号 | 动作 | 行为 |
|---|---|---|
| GOV-039 | approved | 提交 approval action，等待后端返回 |
| GOV-040 | rejected | 提交拒绝，展示 no-effect |
| GOV-041 | request_changes | 提交修改要求，回到相关 workflow/governance task |

提交反馈：

- `GOV-042`: 点击后按钮进入 submitting 并禁用重复提交。
- `GOV-043`: 请求必须携带 `client_seen_version`。
- `GOV-044`: 成功后以后端 `ApprovalRecordReadModel.decision` 为准刷新。
- `GOV-045`: 409 `SNAPSHOT_MISMATCH` 或 `CONFLICT` 时提示刷新并展示服务端最新状态。
- `GOV-046`: expired 状态不显示可提交按钮。

## 5. 变更管理

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-047 | change_id | 可点击 |
| GOV-048 | change_type | Prompt、Skill、Agent 能力、配置、数据源策略、风险预算、执行参数 |
| GOV-049 | impact_level | low、medium、high |
| GOV-050 | state | draft、validating、pending_approval、effective、rejected、expired |
| GOV-051 | diff_summary | 差异摘要 |
| GOV-052 | validation_status | queued、running、passed、failed |
| GOV-053 | effective_scope | new_task 或 new_attempt |
| GOV-054 | rollback_plan_ref | 回滚引用 |
| GOV-055 | owner_approval_ref | 高影响审批链接 |

规则：

- `GOV-056`: 低/中影响自动验证和审计后只对新任务或新 attempt 生效。
- `GOV-057`: 高影响必须进入审批中心。
- `GOV-058`: 在途 workflow 和 AgentRun 继续显示旧 ContextSnapshot。

## 6. Agent 团队

| 编号 | 区块 | 说明 |
|---|---|---|
| GOV-059 | Agent roster | 九个正式 Agent、胜任度、CFO 归因、短板和草案状态 |
| GOV-060 | Agent profile | `/governance/team/:agentId`，展示画像、权限、版本、质量和短板 |
| GOV-061 | Capability draft | `/governance/team/:agentId/config`，只保存草案，不直接生效 |
| GOV-062 | 治理联动 | 草案进入变更管理，低/中自动验证，高影响审批 |

规则：

- `GOV-063`: Agent 团队是治理下二级工作区，不出现在一级主导航。
- `GOV-064`: Agent 团队的主入口是治理页二级模块切换；卡片入口只是辅助入口。
- `GOV-064A`: Agent 团队可编辑草案；变更管理 / 审批中心负责追踪验证、审批和生效边界。

## 7. Agent Capability Change

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-065 | draft_id | 可点击 |
| GOV-066 | agent_id | 目标 Agent |
| GOV-067 | changed_fields | 工具、Skill、Prompt、上下文、rubric 等 |
| GOV-068 | impact_level | low、medium、high |
| GOV-069 | state | draft、validating、pending_approval、effective、blocked |
| GOV-070 | validation_result | 自动验证结果 |
| GOV-071 | governance_change_ref | 关联治理变更 |
| GOV-072 | effective_scope | new_task 或 new_attempt |

规则：

- `GOV-073`: 来自 Agent 团队的能力配置草案必须在此可见。
- `GOV-074`: 不显示热改在途 AgentRun 的状态。

## 8. 系统健康

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-069 | health_id | 可点击 |
| GOV-070 | domain/service | 数据域或服务名 |
| GOV-071 | severity | P0/P1/P2/P3 |
| GOV-072 | state | healthy、degraded、blocked、recovering、monitoring |
| GOV-073 | impacted_workflows | 影响对象 |
| GOV-074 | recovery_status | 恢复状态 |
| GOV-075 | risk_handoff | 是否已交给 Risk |
| GOV-076 | investment_resume_allowed | true/false |
| GOV-077 | trace_id | 投资 workflow 可跳 `/investment/:workflowId/trace`；其他 incident 展示治理内审计摘要 |

规则：

- `GOV-078`: 技术恢复不等于投资恢复；`investment_resume_allowed=false` 时继续显示风控守卫。
- `GOV-079`: Health 区可以打开投资 workflow Trace 或治理内 trace 摘要，但不推进业务状态。

## 9. 审计记录

| 编号 | 列 | 说明 |
|---|---|---|
| GOV-080 | event_id | 可点击 |
| GOV-081 | trace_id | 投资 workflow Trace 入口或治理内 trace 摘要 |
| GOV-082 | object_type | artifact、approval、reopen、command、gateway_write |
| GOV-083 | object_ref | 对象引用 |
| GOV-084 | actor | Owner、Agent、Service、Workflow |
| GOV-085 | event_type | created、submitted、denied、approved、reopened |
| GOV-086 | created_at | 时间 |

## 10. 治理页禁用入口

| 编号 | 场景 | UI 表现 |
|---|---|---|
| GUARD-018 | confirmation 混入审批中心 | 不展示 |
| GUARD-019 | manual_todo 混入审批中心 | 不展示 |
| GUARD-020 | Risk rejected 生成审批 | 显示数据错误和 blocked |
| GUARD-021 | Owner 超时仍可审批 | 不显示提交按钮 |
| GUARD-022 | 低/中影响直接热改在途 | 显示新任务/新 attempt 生效 |
| GUARD-023 | 409 冲突本地乐观保留 | 强制刷新服务端最新状态 |

## 10. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-006, REQ-007, REQ-019, REQ-029, REQ-030 |
| TC | TC-ACC-006-01, TC-ACC-007-01, TC-ACC-019-01, TC-ACC-029-01, TC-ACC-030-01 |
| Report | governance_task_report.json, team_capability_config_report.json |
