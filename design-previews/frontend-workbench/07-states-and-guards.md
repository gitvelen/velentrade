# 07. States And Guards

## 0. 目标

本文件统一定义所有页面都要遵守的加载、空、错误、stale、blocked 和禁止入口行为，防止不同页面各自发明口径。

## 1. 通用状态

| 编号 | 状态 | 展示 | 允许动作 | 禁止动作 |
|---|---|---|---|---|
| STATE-005 | page_loading | 页面 skeleton，Shell 保持可用 | 等待、切换菜单 | 提交业务动作 |
| STATE-006 | section_loading | 区块 skeleton，其他区块保留 | 查看已加载区块 | 清空旧业务状态 |
| STATE-007 | empty | 明确空状态文案和下一步 | 返回、切换筛选 | 隐藏整个业务区块 |
| STATE-008 | read_model_error | 错误卡、trace_id、retry | 重试、打开 Trace | 伪造结果 |
| STATE-009 | stale | generated_at、last_success_at、stale badge | 查看旧数据、刷新 | 基于旧数据提交审批或执行 |
| STATE-010 | degraded | yellow warning、影响说明 | 查看详情、补证 | 当作正常状态 |
| STATE-011 | blocked | red blocker、reason_code、evidence_refs | 查看原因、跳 Trace、重开建议 | 继续执行或审批绕过 |
| STATE-012 | expired | 超时处置和 no-effect | 查看审计 | 继续提交 |
| STATE-013 | conflict | 服务端最新版本提示 | 刷新 | 保留本地乐观结论 |

## 2. 卡片状态规范

| 编号 | 卡片状态 | 展示 |
|---|---|---|
| STATE-014 | normal | 标题、主数值、状态 badge、证据链接 |
| STATE-015 | warning | 黄色 badge、影响范围、建议 drill-down |
| STATE-016 | blocked | 红色 badge、reason_code、禁用动作 |
| STATE-017 | waiting | 等待对象、due_at、超时默认 |
| STATE-018 | completed | 结果、artifact_ref、generated_at |
| STATE-019 | skipped | skipped reason，不隐藏阶段 |
| STATE-020 | superseded | 旧版本只读，显示新 attempt 引用 |

## 3. 表格状态规范

| 编号 | 场景 | 展示 |
|---|---|---|
| STATE-021 | 无行 | 保留表头，显示空状态 |
| STATE-022 | 部分字段 redacted | 字段显示 `已脱敏` 和原因 |
| STATE-023 | 行级 blocked | reason_code 列高亮 |
| STATE-024 | 行级 stale | generated_at 列高亮 |
| STATE-025 | 筛选无结果 | 显示当前筛选条件和清除筛选 |
| STATE-026 | 分页加载失败 | 保留已加载行，显示重试 |

## 4. 表单状态规范

| 编号 | 表单 | 规则 |
|---|---|---|
| STATE-027 | Request Brief preview | confirm/edit/cancel 三种动作 |
| STATE-028 | Approval action | approved/rejected/request_changes 三种动作 |
| STATE-029 | Agent capability draft | 只能保存草案 |
| STATE-030 | Governance proposal | 显示 impact、validation、rollback、effective_scope |
| STATE-031 | conflict | 409 时丢弃本地乐观结果，刷新服务端 |
| STATE-032 | submitting | 禁用重复提交 |

## 5. 全局禁止入口清单

| 编号 | 禁止入口 | 应出现的替代展示 |
|---|---|---|
| GUARD-024 | 飞书、邮件、短信、移动端入口 | 不出现 |
| GUARD-025 | 真实券商、真实下单、真实账户同步 | 不出现 |
| GUARD-026 | Backtrader、回测、历史 IC 重跑 | 不出现 |
| GUARD-027 | 策略经理、规则路径、IC/规则路径对比 | 不出现 |
| GUARD-028 | Performance Analyst Agent | 不出现 |
| GUARD-029 | 非 A 股交易、审批、执行 | planning、risk、manual_todo |
| GUARD-030 | Risk rejected Owner 直接批准 | Risk blocker、repairability、reopen suggestion |
| GUARD-031 | execution_core blocked 继续成交 | blocked reason、数据/服务健康链接 |
| GUARD-032 | action_conviction < 0.65 执行 | observe、补证、重开或 no_action |
| GUARD-033 | Prompt/Skill/权限直接生效 | 治理变更草案 |
| GUARD-034 | 团队页热改在途 AgentRun | 显示旧 ContextSnapshot 仍绑定 |
| GUARD-035 | raw transcript 默认作为事实 | Trace 折叠，标注非正式事实源 |
| GUARD-036 | Memory/Knowledge 替代 artifact | fenced background、artifact 优先 |
| GUARD-037 | CFO 外角色读财务敏感明文 | redacted summary、denied refs |

## 6. Guard 展示字段

所有 blocked 或 denied 状态至少展示：

| 编号 | 字段 | 说明 |
|---|---|---|
| GUARD-038 | reason_code | 稳定机器码 |
| GUARD-039 | human_message | 简体中文说明 |
| GUARD-040 | evidence_refs | artifact、trace 或 read model 引用 |
| GUARD-041 | recoverability | 可重试、可重开、不可修复、等待 Owner |
| GUARD-042 | allowed_next_actions | 查看、补证、重开建议、等待、创建 manual_todo |
| GUARD-043 | forbidden_actions | 当前被禁用动作 |

## 7. 页面到 report 的断言映射

| 编号 | 页面/状态 | Report 字段 |
|---|---|---|
| STATE-033 | 五个一级主导航和中文高端浅色卡面 | `web_command_routing_report.nav_scan`、`chinese_ui_scan`、`premium_light_theme_assertions` |
| STATE-034 | Owner/Dossier/Trace 三层视图 | `web_command_routing_report.view_layers` |
| STATE-035 | Request Brief preview | `web_command_routing_report.request_brief_preview_flow` |
| STATE-036 | 治理下 Agent 团队九 Agent | `team_capability_config_report.agent_cards` |
| STATE-037 | 任务/审批/manual_todo 分离 | `governance_task_report.task_center_states`、`approval_center_items`、`manual_todo_isolation` |
| STATE-038 | Risk rejected UI guard | `governance_task_report.risk_rejected_ui_guard` |
| STATE-039 | execution_core UI guard | `governance_task_report.execution_core_ui_guard` |
| STATE-040 | 非 A 股 UI guard | `governance_task_report.non_a_asset_ui_guard` |
| STATE-041 | Agent 能力热改拒绝 | `team_capability_config_report.hot_patch_denials` |

## 8. Owner 确认检查表

| 编号 | 检查项 | 状态 |
|---|---|---|
| STATE-042 | 五个一级主菜单是否正确，团队是否已下沉到治理 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-043 | 所有 route 是否有唯一 canonical parent menu | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-044 | 全景页是否能回答今天该看什么 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-045 | 投资 Dossier 是否能看懂 S0-S7 和分歧，且不被当成主菜单 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-046 | Trace 是否只作为具体业务对象的审计层 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-047 | 财务页是否用老板视角表达资产提醒，而不是展示过程性边界卡片 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-048 | 知识页是否不把 Memory 当事实源 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-049 | 治理下 Agent 团队是否展示九个 Agent 的胜任度、CFO 归因和能力短板 | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-050 | 治理页是否清楚分离任务、审批、治理变更、Health 和 Audit | Design 语义复审通过；阶段切换仍需人工确认 |
| STATE-051 | 禁用入口是否覆盖关键风险 | Design 语义复审通过；阶段切换仍需人工确认 |
