# 05. Agent 团队工作区

## 0. 页面目标

治理下的 Agent 团队工作区回答：“九个正式 Agent 是否胜任岗位、短板在哪里、哪些改进正在验证，以及 Owner 如何受控调整能力而不影响在途任务。”

主要路由：

- `/governance/team`
- `/governance/team/:agentId`
- `/governance/team/:agentId/config`

页面归属：

- 三个 route 都归属主菜单“治理”。
- Agent 团队工作区负责看 Agent、看绩效与短板、编辑能力配置草案。
- 治理页只负责查看草案状态、自动验证、高影响审批和生效边界；不提供 Prompt/Skill/权限编辑器。

主要 read model：

- `TeamReadModel`
- `AgentProfileReadModel`
- `AgentCapabilityConfigReadModel`

## 1. 首屏布局

```text
顶部：团队健康总览 + 胜任度分布 + 待处理能力草案 + 最近失败/越权
左侧：九个 Agent roster 卡（胜任度、趋势、短板标签）
中部：选中 Agent 的画像、绩效拆解、能力矩阵、近期产物质量
右侧：CFO 归因引用、改进建议、草案入口
底部：能力短板、反思/改进链路、能力变更时间线、变更管理链接
```

## 2. 团队健康总览

| 编号 | 卡片 | 展示字段 |
|---|---|---|
| TEAM-001 | 运行状态 | active、idle、assessment、monitoring 数量 |
| TEAM-002 | 产物质量 | 平均质量分、schema pass rate、evidence completeness |
| TEAM-003 | 失败/越权 | failure_count、denied_write_count、timeout_count |
| TEAM-004 | 待治理草案 | draft_count、high_impact_count、auto_validation_count |
| TEAM-005 | 改进新鲜度 | 最近一次能力改进、验证状态和适用范围 |
| TEAM-005A | 胜任度分布 | 胜任、观察、需改进、待治理 Agent 数量 |
| TEAM-005B | CFO 归因关注 | 最新 CFOInterpretation 命中的 Agent、classification、ReflectionAssignment 状态 |

交互：

- `TEAM-006`: 点击失败/越权进入过滤后的 Agent 列表。
- `TEAM-007`: 点击草案进入 Agent Capability Change 表或治理页。

## 3. 九个 Agent roster

每张 roster 卡必须展示：

| 编号 | 字段 | 说明 |
|---|---|---|
| TEAM-008 | 中文岗位名 | 面向 Owner 的中文描述 |
| TEAM-009 | 英文 id | 稳定 id |
| TEAM-010 | status | active、idle、assessment、owner_pending、monitoring |
| TEAM-011 | current_tasks | 当前任务数 |
| TEAM-012 | recent_quality | 最近产物质量 |
| TEAM-012A | capability_score | 胜任度评分和趋势 |
| TEAM-012B | shortfall_tags | 能力短板标签，例如证据不足、反证处理弱、schema 不稳、协作慢、越权、方法论过期 |
| TEAM-012C | cfo_attribution_ref | 最近 CFO 归因解释或 ReflectionAssignment 引用 |
| TEAM-013 | active_capability_summary | 当前能力摘要，详情页可展开版本信息 |
| TEAM-014 | improvement_status | 无、验证中、待审批、已生效 |
| TEAM-015 | next_improvement | 下一步改进建议 |
| TEAM-016 | effective_scope | 只影响后续任务或后续尝试 |
| TEAM-017 | tool_permission_summary | 工具权限摘要 |
| TEAM-018 | service_permission_summary | 可请求服务摘要 |
| TEAM-019 | writable_artifact_summary | 可写 artifact 摘要 |
| TEAM-020 | risk_counts | 越权写入拒绝、schema fail、Owner/Risk 打回、超时 |
| TEAM-021 | draft_status | 无、验证中、待审批、blocked |

九个正式 Agent：

| 编号 | Agent | 中文岗位 | Owner 看它负责什么 |
|---|---|---|---|
| TEAM-022 | CIO | 投资收口 | 主席简报、CIO 决策、语义综合 |
| TEAM-023 | CFO | 财务治理 | 财务解释、治理提案、反思分派 |
| TEAM-024 | Macro Analyst | 宏观分析 | 市场状态、政策传导、流动性、行业风格 |
| TEAM-025 | Fundamental Analyst | 基本面分析 | 商业质量、财务质量、盈利情景、估值 |
| TEAM-026 | Quant Analyst | 量化分析 | 因子、趋势、拥挤、择时 |
| TEAM-027 | Event Analyst | 事件分析 | 公告、来源验证、催化窗口 |
| TEAM-028 | Risk Officer | 独立风控 | 三状态复核、重开、例外包 |
| TEAM-029 | Investment Researcher | 研究与知识 | 资料包、知识晋升、Prompt/Skill 提案 |
| TEAM-030 | DevOps Engineer | 系统可靠性 | 数据源、服务、执行环境、成本/Token |

交互：

- `TEAM-031`: 点击 roster 卡进入 `/governance/team/:agentId`。
- `TEAM-032`: roster 卡不提供直接保存 Prompt/Skill/权限的按钮。

## 4. Agent 画像详情

| 编号 | 区块 | 展示 |
|---|---|---|
| TEAM-033 | 角色定位 | 它是谁、对谁负责、成功标准 |
| TEAM-034 | 能做什么 | 正向能力 |
| TEAM-035 | 不能做什么 | 禁止动作 |
| TEAM-036 | 读什么 | 组织透明读、敏感字段例外 |
| TEAM-037 | 写什么 | Authority Gateway artifact/command/memory API |
| TEAM-038 | 能调什么 | 工具、服务、CollaborationCommand |
| TEAM-039 | SOP | 默认工作步骤 |
| TEAM-040 | rubric | 评价指标 |
| TEAM-041 | 失败处理 | schema fail、证据不足、越权、超时 |
| TEAM-042 | 升级规则 | 何时交给 Owner、Risk、CFO、DevOps |
| TEAM-043 | 运行质量 | recent artifacts、schema pass、evidence refs、failure records |
| TEAM-044 | 版本与上下文 | Prompt、SkillPackage、model route、budget、timeout、ContextSnapshot |

## 5. Capability Matrix

| 编号 | 列 | 说明 |
|---|---|---|
| TEAM-045 | capability | 能力项 |
| TEAM-046 | tools_enabled | 可用工具 |
| TEAM-047 | service_permissions | 可请求服务 |
| TEAM-048 | collaboration_commands | 可提交协作命令 |
| TEAM-049 | writable_artifacts | 可写产物 |
| TEAM-050 | default_data_domains | 默认数据域 |
| TEAM-051 | finance_sensitive_boundary | 财务敏感字段边界 |
| TEAM-052 | guard_reason | 不允许项 reason_code |

规则：

- `TEAM-053`: Capability Matrix 是 Owner 可读管理视图，不是后端权限表原样摊开。

## 6. Prompt / Skill / Context Panel

| 编号 | 字段 | 展示 |
|---|---|---|
| TEAM-054 | prompt_version | 当前 Prompt 版本和最近验证 |
| TEAM-055 | skill_package_version | SkillPackage 版本、适用范围 |
| TEAM-056 | default_context_binding | 默认上下文绑定 |
| TEAM-057 | model_route | 模型路由摘要 |
| TEAM-058 | budget | Token/成本预算 |
| TEAM-059 | timeout | 超时设置 |
| TEAM-060 | context_snapshot_version | 当前生效快照 |
| TEAM-061 | rollback_ref | 可回滚版本引用 |

## 7. 质量面板

| 编号 | 指标 | 说明 |
|---|---|---|
| TEAM-062 | artifact_quality | Memo/Decision/Review/Proposal 质量 |
| TEAM-063 | schema_pass_rate | schema pass |
| TEAM-064 | evidence_completeness | 证据引用完整性 |
| TEAM-065 | collaboration_response | 协作响应质量 |
| TEAM-066 | owner_risk_returns | Owner/Risk 打回原因 |
| TEAM-067 | denied_actions | 越权写入拒绝 |
| TEAM-068 | timeout_records | 超时记录 |

## 7.1 胜任度与 CFO 归因面板

胜任度评分不是收益排名，也不是把亏损简单归咎于 Agent。它把自动归因服务、CFO 解释、反思分派和运行质量合并为 Owner 可读结论。

| 编号 | 区块 | 展示 |
|---|---|---|
| TEAM-068A | 胜任度评分 | 总分、趋势、样本窗口、可信度；样本少于 3 个时只显示 observation |
| TEAM-068B | 评分拆解 | 产物质量、证据完整性、schema pass、协作响应、时效、角色边界合规 |
| TEAM-068C | CFO 归因引用 | AttributionReport、CFOInterpretation、classification、responsible_agent_id |
| TEAM-068D | 归因解释 | market / decision / execution / data / risk / evidence 贡献，不把市场结果误写成 Agent 错误 |
| TEAM-068E | ReflectionAssignment | questions_to_answer、due_at、first_draft_status、Researcher promotion refs |
| TEAM-068F | 近期样本 | 最近产物、相关 workflow、Owner/Risk 打回、evidence refs、trace_id |

## 7.2 能力短板面板

能力短板必须诚恳展示，不能被总分掩盖。每个短板都要有 evidence refs、最近样本、影响范围和建议动作。

| 编号 | 短板类型 | 展示 |
|---|---|---|
| TEAM-068G | 证据不足 | 缺失 evidence_refs、证据质量低、被 Risk/Owner 打回 |
| TEAM-068H | 反证处理弱 | hard dissent 未回应、反证质量低、debate 后仍无清晰 synthesis |
| TEAM-068I | schema 不稳 | schema_validation_failed、字段缺失、修正重试 |
| TEAM-068J | 协作慢 | request_* 响应超时、handoff 延迟、blocked 持续时间 |
| TEAM-068K | 角色越界 | 试图写禁止 artifact、直接改 workflow、越过 Gateway |
| TEAM-068L | 敏感字段拒绝 | 非 CFO 读取财务敏感明文被拒绝 |
| TEAM-068M | 方法论过期 | CFO 标记 methodology_decay、条件失效、连续低分 |
| TEAM-068N | 预算/超时 | token、成本或运行时间超限 |

建议动作：

- `TEAM-068O`: 低/中影响改进进入自动验证后的 Knowledge/Prompt/Skill proposal 或能力配置草案。
- `TEAM-068P`: 高影响改进进入治理审批。
- `TEAM-068Q`: 不显示“立即修复在途 AgentRun”或“直接更新 Prompt/Skill”。

## 8. 能力配置草案页

路由：`/governance/team/:agentId/config`

可编辑字段：

| 编号 | 字段 | 说明 |
|---|---|---|
| TEAM-069 | tools_enabled | 工具开关 |
| TEAM-070 | service_permissions | 服务权限 |
| TEAM-071 | collaboration_commands | 可提交协作命令 |
| TEAM-072 | SkillPackage | 技能包 |
| TEAM-073 | Prompt | 提示词 |
| TEAM-074 | DefaultContextBinding | 默认上下文 |
| TEAM-075 | model_route | 模型路由 |
| TEAM-076 | budget | 预算 |
| TEAM-077 | timeout | 超时 |
| TEAM-078 | SOP | 工作步骤 |
| TEAM-079 | rubric | 评价标准 |
| TEAM-080 | escalation_rules | 升级规则 |
| TEAM-081 | allowed_artifact_types | 允许产物类型 |
| TEAM-082 | impact_level_hint | 影响等级候选 |
| TEAM-083 | validation_plan_refs | 验证计划 |
| TEAM-084 | rollback_plan_ref | 回滚计划 |
| TEAM-085 | effective_scope | new_task 或 new_attempt |

交互：

- `TEAM-086`: 点击保存后生成能力配置草案并进入变更管理。
- `TEAM-087`: 保存成功后展示 draft_id、governance_change_ref、validation_status。
- `TEAM-088`: 低/中影响显示自动验证队列。
- `TEAM-089`: 高影响跳转审批中心。
- `TEAM-090`: 草案页始终显示当前有效版本未改变。
- `TEAM-090A`: 保存后的状态、验证结果和高影响审批可从治理页追踪；团队页保留编辑和查看上下文入口。

强制 high impact：

| 编号 | 触发 |
|---|---|
| TEAM-091 | 修改审批规则 |
| TEAM-092 | 修改风险预算 |
| TEAM-093 | 修改执行参数 |
| TEAM-094 | 修改数据源策略 |
| TEAM-095 | 修改 Governance Impact Policy |

## 9. 团队页禁用入口

| 编号 | 禁止入口 | UI 表现 |
|---|---|---|
| GUARD-011 | 立即更新在途 AgentRun | 不显示按钮 |
| GUARD-012 | 绕过变更管理保存提示词、技能或权限 | 只允许保存草案 |
| GUARD-013 | 直接修改 workflow state | 不提供入口 |
| GUARD-014 | 直接覆盖 Risk verdict | 不提供入口 |
| GUARD-015 | 直接改 ApprovalRecord | 不提供入口 |
| GUARD-016 | 直接改 PaperExecution | 不提供入口 |
| GUARD-017 | 越权配置请求 | blocked draft + reason_code |

## 10. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-003, REQ-006, REQ-007, REQ-030 |
| TC | TC-ACC-003-01, TC-ACC-006-01, TC-ACC-007-01, TC-ACC-030-01 |
| Report | agent_capability_contract_report.json, team_capability_config_report.json, governance_task_report.json |
