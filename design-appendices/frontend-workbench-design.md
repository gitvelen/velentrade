# Frontend Workbench Design

## 0. AI 阅读契约

- 本附件是 Design 阶段 Web 工作台、高审美浅色主题、主导航、全局命令层、治理下 Agent 团队工作区、三层 multi-agent 可视化、任务中心和审批中心的实现契约。
- 实现 `frontend/**`、`tests/frontend/**`、`tests/e2e/**`、前端 read model 或 `TC-ACC-003/006/007/030` 时必须读取。
- 本附件承接 `spec.md`、`testing.md`、`spec-appendices/frontend-workbench-map.md` 和 `contracts/api-read-models.md`，不新增正式需求。
- 前端只调用 API/read model，不拥有业务状态推进权；若页面需要新后端字段，先回写 `contracts/api-read-models.md`。

## 1. 路由与页面结构

V1 只做桌面 Web 工作台。一级主菜单只允许 `全景 / 投资 / 财务 / 知识 / 治理`；`团队` 不作为一级菜单，Agent 团队能力管理下沉为治理下的二级工作区。其他 route 都是某个主菜单下的子页面、详情页或审计页，不得在主导航中单独出现。

| 主菜单 | route | 页面层级 | 主要 read model | Owner 默认层级 |
|---|---|---|---|---|
| 全景 | `/` | 全景页 | `OwnerDecisionReadModel` | 默认摘要页 |
| 投资 | `/investment` | 投资队列 | `InvestmentQueueReadModel` | 默认列表页 |
| 投资 | `/investment/:workflowId` | Investment Dossier，投资 workflow 详情页 | `InvestmentDossierReadModel` | drill-down 详情 |
| 投资 | `/investment/:workflowId/trace` | Workflow Trace，投资 workflow 审计详情页 | `TraceDebugReadModel` | 审计层，默认不在首屏正文出现 |
| 财务 | `/finance` | 财务页 | `FinanceOverviewReadModel` | 默认页面 |
| 知识 | `/knowledge` | 知识页 | `KnowledgeSearchReadModel` + proposal summaries | 默认页面 |
| 治理 | `/governance` | 治理页 | `GovernanceReadModel` | 默认页面 |
| 治理 | `/governance/team` | Agent 团队工作区 | `TeamReadModel` | 二级工作区 |
| 治理 | `/governance/team/:agentId` | Agent 画像详情页 | `AgentProfileReadModel` | drill-down 详情 |
| 治理 | `/governance/team/:agentId/config` | 能力配置草案编辑页 | `AgentCapabilityConfigReadModel` | drill-down 草案页 |
| 治理 | `/governance/approvals/:approvalId` | Approval Packet 审批详情页 | `ApprovalRecordReadModel` | drill-down 审批页 |

Shell 固定区域：

- 左侧或顶部主导航：`全景 / 投资 / 财务 / 知识 / 治理`；左侧导航紧凑展示品牌名和五个一级菜单，不写“单老板投研工作台”等长副标题，不展示审批/阻断/草案三项业务数字。
- 全局命令输入：只生成 Request Brief preview，不直接启动执行或审批。
- Attention badge：审批、manual_todo、数据降级、incident、Risk blocked。
- 当前页面内容区。

层级与来源规则：

- Owner Decision View 的 attention、task、approval、manual_todo、incident 卡片必须带明确目标：投资 workflow 跳 `/investment/:workflowId`，审批跳 `/governance/approvals/:approvalId`，系统健康跳 `/governance?panel=health`，manual_todo 跳 `/governance?task=:taskId`。
- Investment Dossier 的 canonical 面包屑固定为 `投资 -> 投资队列 -> Investment Dossier`；如果从全景或治理进入，只在标题区保留“返回来源”。
- Workflow Trace 的 canonical 面包屑固定为 `投资 -> 投资队列 -> Investment Dossier -> Workflow Trace`；如果从 Governance health/audit 进入，返回路径保留治理来源，但 active 主菜单仍为“投资”。
- Governance health/audit 可展示非投资 incident 的 `trace_id` 和摘要；V1 不新增独立 incident trace route。若未来需要通用 trace 详情页，必须回写 read model/route 设计。
- Trace/Debug 不出现在 Owner 首屏默认任务卡正文中；默认任务卡只显示“查看详情”，审计入口放在 Dossier、治理 Audit/Health 或更多操作中。
- URL 必须可恢复当前焦点：`/investment/:workflowId?stage=S3&artifact=:artifactId`；无 query 时默认选当前 active/blocked stage。

## 1.1 视觉与卡面规范

前端默认使用高审美、高端、中文、信息密度高的投研工作台风格；漂亮是第一优先级，护眼是第二优先级。视觉设计必须服务扫描和决策，不做营销页。

原则：

- 页面首屏必须直接展示真实业务信息：关注事项、风险、审批、投资结论、Agent 能力或治理状态。
- 使用卡片承载结论、指标、状态和证据；卡片圆角不超过 8px，避免卡片套卡片。
- 主题采用暖瓷底色、墨色文字、非纯白卡片、细边框、轻阴影和克制高质感强调色；主强调为玉绿，辅助使用靛蓝、暗金和胭脂红，形成高级感而不是普通后台灰。风险、阻断、审批、成功、生效使用稳定语义色，但避免大面积纯白、纯黑和高饱和色块造成疲劳。
- 卡片内使用中文标签、紧凑数值、状态徽标、微型趋势、证据链接和清晰操作按钮；不得用大段说明文解释页面功能。
- Owner 默认页面不得展示实现或设计过程材料，例如 `ContextSnapshot`、`Prompt`、`SkillPackage`、`trace_id`、`read model`、非 A 股边界守卫说明、热改限制等；这些内容只允许进入审计、配置详情或开发调试层。默认卡片必须转译成老板能直接判断的业务语言，例如“近期现金流”“改进进度”“敏感信息保护”。
- 表格只用于高密度比较；长 trace、tool call、schema 错误和 raw transcript 默认折叠。
- 全局命令输入是命令层，不占据页面主叙事；主叙事由卡面、阶段轨、矩阵和 Dossier 承担。
- 所有按钮、筛选、tab、chip、卡片标题和空状态使用简体中文；专业对象名如 `AgentRun`、`DecisionPacket`、`ContextSnapshot` 只在审计或配置详情中保留英文术语，不作为老板默认卡片标题。
- 卡片排列按统一信息架构执行：优先处理事项在前，核心状态和关键决策在中，支撑证据、健康和审计在后；治理页使用二级模块切换条暴露任务、审批、Agent 团队、变更、健康和审计。

## 2. 全局命令层

流程：

```text
Owner natural language
 -> POST /api/requests/briefs
 -> RequestBrief preview
 -> Owner confirm / edit / cancel
 -> POST /api/requests/briefs/{id}/confirmation
 -> Task card / workflow created
```

交互规则：

- confirmation 只确认 Request Brief；approval 只发生在审批中心。
- 研究、审批、执行、规则、Prompt、Skill、Agent 能力配置和财务动作都必须走 Request Brief preview、任务卡或治理变更草案。
- Preview 必须展示：目标、范围、资产边界、任务类型、建议 semantic lead、过程权威、预期产物、优先级、授权边界、成功标准、阻断条件、是否可能触发 Owner approval。
- 超时或取消的 Request Brief 不创建 workflow。
- 输入“帮我下单”“绕过风控”等直接动作时，preview 必须显示将进入受控 workflow 或被拒绝。
- 低置信、多模板冲突、资产范围不明或授权边界不清时，Preview 显示需要老板补充的问题，不显示“已安排”或“执行中”。
- confirmed 后必须显示 Task card；卡片字段至少包含 task_type、current_state、semantic lead、下一步、reason_code、artifact_count 和详情链接。Trace link 只能出现在 Dossier 或治理审计层，不放在 Owner 默认任务卡正文中。
- “学习热点事件”默认展示为 research_task：首个负责人是 Investment Researcher，预期产物是 Research Package / MemoryCapture / 候选 TopicProposal；除非命中正式 IC 硬门槛，否则不显示投资审批、执行或交易入口。

## 3. Owner Decision View

全景页回答“今天要不要我处理”。区块：

| 区块 | 展示字段 | 空状态 | 错误状态 |
|---|---|---|---|
| Today Attention Strip | risk_items、approval_items、manual_todo、data_quality_items、incident_items | “当前无待处理事项” | 显示 last_success_at 和 retry |
| Paper Account Summary | total_value、cash、position_value、return、drawdown | 初始 1,000,000 CNY 空仓 | 账户 read model 不可用时只阻断展示 |
| Risk Summary | concentration、risk_budget_used、blockers | 无阻断 | 风控数据不可用时标记 degraded |
| Approval Summary | pending approvals、到期时间、影响范围 | 无审批 | 审批列表失败不隐藏任务 badge |
| Manual Todo Summary | 人工动作、due_date、风险提示 | 无待办 | 显示 manual_todo stale 警告 |
| 每日简报摘要 | 高信号标题、priority | 无简报 | 简报失败不阻断投资 workflow |
| System Health | data/service health、成本 Token 观测 | 正常 | incident 摘要和 Risk 交接状态 |

全景页不得展示长聊天 transcript；需要追溯时进入 Dossier 或 Trace/Debug。

## 4. Investment Dossier View

详情布局：

```text
左：S0-S7 Stage Rail + Reopen Events
中：当前阶段核心 artifact 和行动结论
右：证据、数据质量、风险、审批、执行状态
底部：Handoff、Attribution、Reflection linkback
```

必须组件：

- `StageRail`：显示每阶段 `node_status`、responsible role、reason code、artifact count、reopen marker。
- `DataReadinessPanel`：quality band、fallback、cache、conflict、decision_core/execution_core 状态。
- `CIOChairBriefPanel`：decision question、key tensions、must answer、time budget、no preset attestation。
- `AnalystStanceMatrix`：四行 Macro/Fundamental/Quant/Event，展示 direction/confidence/evidence_quality/hard_dissent。
- `RolePayloadDrilldown`：按角色展示专属 payload，不压成一份通用 Memo。
- `ConsensusGauge`：consensus_score、action_conviction、阈值和行动/不行动解释。
- `DissentBoard`：hard dissent、关键分歧、保留异议、Risk handoff。
- `DebateTimeline`：最多 2 轮；显示 issue、补证、观点变化、过程字段和 CIO synthesis，不显示长对话。
- `OptimizerDeviationPanel`：优化器建议 vs CIO 目标，单股偏离和组合主动偏离。
- `RiskGateCard`：approved/conditional_pass/rejected、repairability、reopen target、Owner exception。
- `ExecutionReplay`：窗口、VWAP/TWAP、成交/未成交/过期、费用、滑点、T+1。
- `AttributionLinkback`：日度归因、角色评价、反思或知识提案链接。

StageRail 交互：

- 每个 stage chip 可点击，点击后只改变 Dossier 的 `selected_stage` 和 URL query，不推进 workflow。
- 中间面板按 `selected_stage` 展示该阶段核心 artifact：S1 展示 DataReadiness/ICContext/ChairBrief，S2 展示四 Memo 和 role_payload，S3 展示 DebateTimeline，S4 展示 CIO Decision，S5 展示 Risk Review，S6 展示 Approval/Execution，S7 展示 Attribution/Reflection。
- 右侧面板随阶段切换展示相关 guard：data quality、Risk、approval、execution_core、reopen 或 attribution trigger。
- blocked/waiting stage 必须在 chip 和右侧 guard 同时显示 reason_code；hover/详情可展示 evidence refs，但不展示 raw transcript。
- reopen marker 点击展示 superseded/preserved artifact 列表，只读展示旧 attempt，不允许在前端恢复旧 artifact。

禁用入口：

- Risk `rejected` 时不显示 Owner “批准继续”按钮。
- `execution_core_status=blocked` 时不显示继续成交入口。
- 非 A 股资产任务不显示审批/执行/交易入口。
- 低共识不显示纸面执行入口。

## 5. Trace/Debug View

用途：审计、排障、治理，不是老板默认视图，也不是一级主菜单。V1 前端只定义投资 workflow 的 Trace 详情页 `/investment/:workflowId/trace`；其他系统、数据或 incident trace 先在治理 Health/Audit 中以摘要和 `trace_id` 形式展示。

展示：

- AgentRun 树：parent_run_id、stage、attempt、profile_version、SkillPackage 版本、ContextSlice。
- CollaborationCommand：command_type、准入结果、拒绝原因、Owner approval link。
- CollaborationEvent 时间线：progress、artifact submitted、guard failed、handoff。
- HandoffPacket 生成和消费关系。
- Authority Gateway：合法写入、direct write denial、sensitive access denial。
- Service/Data routing：Data Request、source、fallback、cache、conflict。
- latency/token/cost：只作运营观测。

Trace/Debug 的 raw transcript 若存在，必须默认折叠，并标注“非正式事实源”。Trace 入口必须保留来源返回路径，但 canonical parent menu 由目标对象决定。

## 6. 治理页

治理页由六个治理模块组成，顶部必须展示二级模块切换条；卡片入口只能作为辅助入口，不能作为进入 Agent 团队的唯一方式。二级模块的显示文案固定为 `任务 / 审批 / Agent 团队 / 变更 / 健康 / 审计`：

- 任务中心：所有 TaskEnvelope；支持 task_type、priority、state、owner_role、blocked_reason 筛选。
- 审批中心：少量高质量审批；不包含 confirmation 和 manual_todo。
- Agent 团队：治理下二级工作区，查看九个 Agent 的胜任度、CFO 归因、短板、版本和草案入口。
- 变更管理：Prompt、Skill、Agent 能力、配置、数据源策略、风险预算和执行参数 diff、生效边界、回滚。
- 数据/服务健康：source health、data quality、conflict、degradation、incident。
- 审计记录：trace_id、artifact、Reopen Event、Approval Record。

治理页默认排序：

1. 顶部摘要：待处理任务、真正审批、Agent 草案、服务健康。
2. 第一组：任务中心和审批中心，先回答“现在谁要处理”。
3. 第二组：Agent 团队和变更管理，回答“系统能力怎么受控变化”。
4. 第三组：系统健康和审计记录，回答“运行是否可信、如何追溯”。

任务中心的任务卡必须回答“谁接住了、现在卡在哪、下一步是什么”：

- `investment_workflow`：显示 CIO、S0-S7 当前 stage、数据/Risk/Execution blocker、Dossier link。
- `research_task`：显示 Researcher、资料包/记忆/候选议题状态、是否请求 Event/Data 补证、Knowledge/Research 详情 link。
- `finance_task`：显示 CFO、规划/预算/税务/估值产物、敏感字段脱敏状态。
- `governance_task` / `agent_capability_change`：显示 impact level、validation status、effective scope、approval link。
- `system_task`：显示 DevOps、incident severity、affected workflow、Risk handoff。
- `manual_todo`：显示人工动作、原因、due_date、风险提示，并明确不连接审批/执行/交易链。

审批包必须展示：

- 审批对象、触发原因、推荐结论、对比方案、风险与影响范围、证据引用、生效边界、超时默认、回滚方式。
- Owner 动作只允许 `approved / rejected / request_changes`；超时由后端状态机写 `expired`。
- Risk `rejected` 不生成审批包；若读到相关 approval，前端必须视为数据错误并显示 blocked。

审批动作反馈：

- 点击 `approved / rejected / request_changes` 后按钮进入 submitting，禁用重复提交，携带 `client_seen_version`。
- 成功返回后以后端 `ApprovalRecordReadModel.decision` 为准刷新页面；`approved` 展示生效边界，`rejected` 展示 no-effect，`request_changes` 展示 requested_changes 并回到相关 workflow/governance task。
- 409 `SNAPSHOT_MISMATCH` 或 `CONFLICT` 时提示刷新并展示服务端最新状态，不保留本地乐观结论。
- `expired` 状态不显示可提交按钮，只显示 timeout disposition；Risk conditional_pass 超时为不执行/S6 blocked，高影响治理超时为不生效。
- 所有审批反馈都必须保留 evidence_refs 和 trace_id 链接，便于进入 Trace/Debug。

## 7. 治理下 Agent 团队工作区

Agent 团队工作区回答“每个 Agent 是否胜任岗位、短板在哪里，以及能力怎么受控调整”。它位于治理主菜单下，是老板管理 AI 团队的页面，不是开发者配置表。进入方式以治理页二级模块切换条为主，治理页 Agent 团队卡片、全景团队草案卡和变更管理记录为辅助入口。Agent 团队工作区负责查看 Agent、绩效、短板和编辑草案；治理页的变更管理/审批中心负责草案状态、验证、高影响审批和生效边界。

### 7.1 页面结构

```text
顶部：团队健康总览 + 胜任度分布 + 待处理能力草案 + 最近失败/越权
左侧：九个 Agent roster 卡（胜任度、趋势、短板标签）
中部：选中 Agent 的画像、绩效拆解、能力矩阵、近期产物质量
右侧：CFO 归因引用、Prompt/Skill/ContextSnapshot 版本、工具权限、草案入口
底部：能力短板、反思/改进链路、能力变更时间线、治理变更链接
```

九个正式 Agent 必须出现在 roster：CIO、CFO、Macro Analyst、Fundamental Analyst、Quant Analyst、Event Analyst、Risk Officer、Investment Researcher、DevOps Engineer。每张 Agent 卡至少展示：

- 中文岗位名、英文 id、状态、当前任务数、胜任度评分、趋势、最近产物质量和短板标签。
- `profile_version`、`skill_package_version`、`prompt_version`、`context_snapshot_version`。
- 工具权限摘要、可请求服务摘要、可写 artifact 摘要。
- CFO 归因引用、越权写入拒绝、schema fail、Owner/Risk 打回、超时等风险计数。

### 7.2 Agent 画像详情

`AgentProfileReadModel` 页面必须分区展示：

- 角色定位：它是谁、对谁负责、成功标准是什么。
- 能做什么/不能做什么：能力边界和禁止动作。
- 读什么/写什么/能调什么：组织透明读、Authority Gateway 写入、工具/服务调用。
- SOP 与 rubric：默认工作步骤、评价指标、失败处理、升级规则。
- 运行质量与胜任度：近期产物、证据引用完整性、schema pass、协作响应、失败原因、短板标签和改进建议。
- CFO 归因与反思：AttributionReport、CFOInterpretation、classification、responsible_agent_id、ReflectionAssignment 和 questions_to_answer。
- 版本与上下文：Prompt、SkillPackage、默认上下文、模型路由、预算、超时和 ContextSnapshot。

胜任度口径：

- 胜任度评分不是收益排名；它结合自动归因服务、CFO 解释、反思分派和运行质量，判断 Agent 是否适合继续承担当前岗位。
- 必须区分 market / decision / execution / data / risk / evidence 贡献，不能把市场亏损简单归为 Agent 错误。
- 样本不足 3 个时只显示 observation，不给强结论。
- 能力短板必须直接展示，不能被总分折叠隐藏。短板类型包括证据不足、反证处理弱、schema 不稳、协作慢、角色越界、敏感字段拒绝、方法论过期、连续低分、预算/超时。
- 每个短板必须带 evidence refs、最近样本、影响范围和建议动作。建议动作只能进入反思、Knowledge/Prompt/Skill proposal 或能力配置草案；不得热改在途 AgentRun。

### 7.3 能力配置草案

Owner 可从 `/governance/team/:agentId/config` 编辑草案，但页面只能提交治理变更草案，不能直接生效。

草案字段：

- tools_enabled、service_permissions、collaboration_commands。
- SkillPackage、Prompt、DefaultContextBinding、model_route、budget、timeout。
- SOP、rubric、escalation_rules、allowed_artifact_types。
- impact_level 候选、验证计划、回滚引用、生效范围。

交互规则：

- 点击“保存草案”后生成 `AgentCapabilityChangeDraft` 和治理变更记录，不改变当前 AgentRun。
- 低/中影响草案显示自动验证队列、验证结果和新任务/新 attempt 生效边界。
- 高影响草案跳转审批中心，展示 diff、影响范围、替代方案、回滚方式和超时不生效。
- 若草案影响审批规则、风险预算、执行参数、数据源策略或 Governance Impact Policy，必须强制 high impact。
- 在途 workflow/AgentRun 卡面继续显示旧 ContextSnapshot，不允许出现“已热更新”状态。
- Agent 团队工作区可编辑草案和查看上下文；变更管理/审批中心追踪草案状态、自动验证、高影响审批和生效边界。

### 7.4 Agent 团队禁用入口

- 不显示“立即更新在途 AgentRun”。
- 不显示绕过 Governance Change 的 Prompt/Skill/工具权限保存按钮。
- 不允许 Owner 在 Agent 团队工作区直接修改 workflow state、Risk verdict、ApprovalRecord 或 PaperExecution。
- 任何越权配置请求必须变成 blocked draft，并显示 reason_code。

## 8. 财务与知识页

财务页：

- 全资产档案、财务健康、投资财务、财务规划、现金流提醒和人工待办；非 A 股处理边界下沉为交互约束，不作为老板默认卡片标题。
- 基金/黄金可展示行情；房产手工或定期估值。
- 非 A 股动作只可生成 planning、risk提示或 manual_todo。
- 财务敏感字段默认不在非 CFO 视图明文展示。

财务敏感展示规则：

- Owner 打开 `/finance` 时是单 Owner 明文财务视图，可查看自己录入的收入、负债、税务和重大支出；该视图不得把明文字段复制到 Trace/Debug 默认区域。
- CFO/财务服务上下文可使用明文字段生成 CFO Interpretation 或 FinanceSummary。
- CIO、Risk、Analyst、Researcher、DevOps 和 Dossier/Trace 默认只显示脱敏摘要：现金约束、风险预算、重大支出影响、流动性边界、字段是否 redacted。
- V1 不提供角色切换器；展示差异由 read model/backend redaction policy 决定，前端不得通过隐藏 CSS 保存明文。

知识页：

- 每日简报、研究资料包、高价值经验、经验库、反思库。
- Memory capture/review/digest/organize 工作区：展示 `MemoryItem`、tag、relation、collection、extraction status、promotion state 和 sensitivity。
- Relations graph 只展示 `references / supports / contradicts / supersedes / derived_from / applies_to / duplicates / promotes_to` 等契约关系；不得用自由文本关系驱动下游 workflow。
- Organize suggestion 必须以待应用建议展示，Owner/Researcher 确认后走 Gateway；前端不得直接覆盖旧 MemoryVersion。
- Context injection inspector：在 Knowledge 或 Trace 中展示某次 AgentRun 注入了哪些 Memory/Knowledge、`why_included`、redaction status、denied refs；默认不展示 raw process archive。
- Knowledge/Prompt/Skill Proposal 展示 diff/manifest、影响等级、验证结果、适用范围、回滚。
- 知识页不直接使提案或 DefaultContext 生效；低/中影响展示自动验证结果，高影响跳转审批中心。

## 9. 加载、空、错状态

- 页面级 loading 使用 skeleton，不改变当前已加载业务状态。
- read model 加载失败显示错误卡片、trace_id 和重试按钮。
- artifact 缺失显示“等待阶段产物”，不虚构结果。
- 数据 degraded 显示 yellow warning；blocked 显示 red blocker 并禁用相关动作。
- stale 数据必须展示 `generated_at` 和 last known status。

## 10. E2E 验证设计

`web_command_routing_report.json` 必须断言：

- 主导航存在 `全景 / 投资 / 财务 / 知识 / 治理`，不包含团队，且无飞书/移动端入口。
- 页面默认简体中文，核心视图采用漂亮优先、护眼其次的高端浅色卡面。
- 自由对话生成 Request Brief preview，再确认创建任务。
- Owner Decision / Dossier / Trace 三层视图存在且默认层级正确。
- 直接交易、直接审批、直接 Prompt 生效被阻断或转为受控 workflow。
- 治理下 Agent 团队工作区存在九个 Agent 卡、画像详情、胜任度评分、CFO 归因引用、能力短板、版本/权限/质量信息和能力配置草案入口。

`governance_task_report.json` 必须断言：

- 任务中心中 investment/governance/incident/manual_todo 状态映射正确。
- 审批中心只包含真正 approval。
- manual_todo 不连接 S5/S6。
- Risk rejected、非 A 股交易、execution_core blocked 三类禁用入口在 UI/API/read model 三层一致。
- Agent 能力配置草案进入治理变更，低/中影响自动验证，高影响进入 Owner 审批，且不热改在途 AgentRun。

`agent_capability_contract_report.json` 必须断言：

- TeamReadModel 覆盖治理下 Agent 团队工作区的九个正式 Agent。
- AgentProfileReadModel 展示能力契约字段、胜任度、CFO 归因引用、能力短板、运行质量、版本和越权/失败记录。
- AgentCapabilityConfigReadModel 的可编辑字段只能提交 draft，不能直接改变有效版本。

## 11. R8 Markdown 预览契约

Design 阶段新增 `design-previews/frontend-workbench/` 作为正式评审产物。该目录不是生产 `frontend/**` 实现，不要求后续组件逐行复用；它用于在 Design 阶段走查信息架构、Agent 协作展示、状态可见性和视觉质量。

文件约定：

```text
design-previews/frontend-workbench/
  README.md
  00-shell-and-navigation.md
  01-overview.md
  02-investment.md
  03-finance.md
  04-knowledge.md
  05-team.md
  06-governance.md
  07-states-and-guards.md
```

Markdown 预览必须表达最终页面排布：主菜单归属、首屏线框、卡片/表格/侧栏位置、状态、禁用入口和 drill-down 路径。视觉风格要求漂亮优先、护眼其次的高端投研工作台：暖瓷底色、墨色文字、非纯白卡面、玉绿主强调、靛蓝/暗金/胭脂红辅助色、高密度、可扫描；不用营销 hero、大卡片堆叠或长聊天默认展示。

### 11.1 必须预览的页面

| 页面 | 必须回答的问题 | 关键 fixture |
|---|---|---|
| Shell / Navigation | 五个一级主菜单、治理下 Agent 团队工作区、route canonical parent、来源入口和返回路径是否清晰 | command triage、attention badge |
| Overview | Owner 今天要不要处理；风险、审批、manual_todo、incident 是否需要动作 | happy path、Risk rejected、incident |
| Investment Queue | 哪些 candidate/IC/P0 抢占；硬门槛为何通过或失败 | P0 holding risk、supporting evidence only |
| Investment Dossier | S0-S7、四 Analyst、CIO、Risk、Execution、Attribution 如何串联 | happy path、hard dissent、execution_core blocked |
| Trace/Debug | 协作如何被审计；AgentRun/Command/Event/Handoff/Gateway 如何回放 | collaboration protocol |
| Finance | 全资产、风险预算、现金流提醒、人工待办 | non-A asset manual task |
| Knowledge | 每日简报、研究资料包、反思、能力改进提案 | reflection learning |
| 治理 Agent 团队 | 九个 Agent 是否胜任岗位；能力配置如何受控进入治理 | agent capability matrix、prompt/skill/context versions、draft governance |
| Governance / Approval | 任务、审批、变更管理、系统健康、审批包 | high impact governance、Owner timeout |

### 11.2 Investment Dossier 第一屏

```text
顶部：任务摘要 + 当前阶段 + action/blocked 状态
左侧：S0-S7 Stage Rail + Reopen Events
中部：当前决策包
  - CIO Chair Brief
  - Analyst Stance Matrix
  - Consensus / Action Conviction
  - Dissent Board
  - Debate Timeline
右侧：Data Quality / Risk Gate / Optimizer Deviation / Execution Status
底部：Handoff / Evidence Map / Attribution / Reflection
```

必须展示两类状态：

- happy path：高共识、无 hard dissent、Risk approved、纸面执行完成。
- conflict path：hard dissent、辩论后保留异议、Risk conditional/rejected、Owner 不可绕过。

### 11.3 Team 第一屏

```text
顶部：团队健康、胜任度分布、失败/越权、待验证草案
左侧：Agent roster 卡面（胜任度、趋势、短板标签）
中部：选中 Agent 的能力画像、绩效拆解和质量指标
右侧：CFO 归因引用、Prompt/Skill/ContextSnapshot 版本、工具权限、保存草案
底部：能力短板、ReflectionAssignment、治理变更链路和验证记录
```

必须展示两类状态：

- 稳定 Agent：胜任度合格、最近产物质量合格、schema pass、无越权，配置只读展示。
- 待治理 Agent：存在 CFO 归因关注、能力短板、能力草案或高影响变更，显示 diff、impact、验证状态和 Owner 审批链接。

### 11.4 Trace/Debug 预览要求

Trace/Debug 不是 Owner 默认视图，但必须能审计：

- AgentRun tree：parent_run_id、profile_version、SkillPackage、ContextSlice。
- CollaborationCommand：requested、accepted、rejected、expired、admission reason。
- CollaborationEvent timeline：tool_progress、guard_failed、artifact_submitted、handoff_created。
- HandoffPacket：source artifacts、open questions、blockers、downstream consumer。
- Authority Gateway：合法写入、direct write denial、sensitive access denial。
- Service/Data routing：DataRequest、source、fallback、cache、conflict。
- Latency/token/cost：运营观测，不作为投资事实。

raw transcript 若存在，默认折叠，并标注“非正式事实源”。

### 11.5 UI 禁用入口

Markdown 预览和生产前端都必须证明：

- Risk `rejected` 时无 Owner “批准继续”按钮。
- `execution_core_status=blocked` 时无继续成交入口。
- 非 A 股资产无审批、执行或交易入口。
- `action_conviction < 0.65` 时无纸面执行入口。
- Prompt/Skill/配置热改请求转 Governance Proposal，不直接生效。
- 治理下 Agent 团队工作区的 Agent 能力配置保存只生成治理变更草案，不直接更新有效版本或在途 AgentRun。

### 11.6 预览与验证

Markdown review pack 用于 Design 语义复审证据。若后续另做 HTML/React 原型或截图，只能作为补充证据，不替代本目录的路由归属表、首屏线框和禁用入口清单。

`web_command_routing_report.json` 必须引用：

- Markdown review pack 路径。
- 主导航、中文高端浅色卡面和三层视图断言。
- 治理下 Agent 团队工作区 Markdown 预览。
- Request Brief preview flow。
- 禁用入口 UI/read model/API guard 对齐。

`governance_task_report.json` 必须引用：

- 任务中心/审批中心/manual_todo 分离 Markdown 预览或 read model snapshot。
- Risk rejected、execution_core blocked、非 A 股交易 denied 状态。
- Agent 能力配置草案进入治理状态机、低/中自动验证、高影响 Owner 审批和 in-flight ContextSnapshot 不变的 Markdown 预览或 read model snapshot。
