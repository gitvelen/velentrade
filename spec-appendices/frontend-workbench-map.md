# Frontend Workbench Map

## 0. AI 阅读契约

- 本附件是 `spec.md` 中 Web 工作台信息架构、高审美浅色主题、治理下 Agent 团队工作区和 multi-agent 可视化的强证据展开层，不定义新的正式需求、验收或验证义务。
- 任务涉及 Web 工作台、主导航、全局命令层、任务中心、审批中心、治理下 Agent 团队工作区、Agent 能力配置草案、页面信息架构、multi-agent 协作展示或 Trace/Debug View 时，必须读取本附件。
- 若本附件与 `spec.md` 冲突，必须停止并回到 Requirement 修补冲突。
- V1 不做飞书、移动端、邮件、短信；旧前端稿中的移动端、飞书、策略经理、规则路径、路径对比和 CIO 第三轮介入口径不得进入 V1。

## 1. 前端定位

V1 前端是 artifact-centric 老板工作台，不是聊天中心，也不是纯监控仪表盘。默认视觉应是简体中文、漂亮优先、护眼其次、高端、信息密度高的浅色卡面式投研工作台：主背景采用暖瓷/柔和中性色，卡片和控件使用分层浅色表面、细边框、轻阴影和少量高质感语义强调色，主强调为玉绿，辅助使用靛蓝、暗金和胭脂红，不采用纯白大底或深色大底；把老板要看的结论、风险、审批、Agent 分歧、执行、团队能力和系统健康放进可扫描的卡片、矩阵、时间线和 Dossier，而不是把后端表格、长聊天或 trace 原样摊开。

默认阅读顺序：

1. Owner 先看今天需要处理什么。
2. 需要深入时进入 Investment Dossier。
3. 需要审计、排错或治理时打开 Trace/Debug View。

前端必须避免两种极端：

- 把长聊天 transcript 当作协作结果。
- 把后端所有表格和 trace 原样摊给 Owner。
- 用营销页、空洞大标题或低信息密度装饰替代真实工作台。

## 2. 主导航

| 导航 | 目标 | 关键内容 |
|---|---|---|
| 全景 | Owner 开屏判断今天是否需要关注 | 总资产、纸面账户、风险、任务、审批、manual_todo、简报、系统健康 |
| 投资 | A 股 IC 决策与纸面执行回放 | 机会池、IC 队列、投资 Dossier、分析师 Memo、CIO 决策、风控、纸面执行、归因 |
| 财务 | 全资产财务档案与规划 | 资产负债、收入支出、税务提醒、压力测试、风险预算、财务健康 |
| 知识 | 研究、经验和反思资产 | 每日简报、研究资料包、经验库、反思库、知识/能力改进提案 |
| 治理 | 任务、审批、Agent 团队、配置、系统状态 | 任务中心、审批中心、Agent 团队、变更管理、系统健康、审计记录 |

## 3. 卡面与信息密度

页面结构以卡片、矩阵、轨道和时间线为主，但卡片必须承载真实业务信息：

- 每张卡必须有明确决策用途，例如“是否要处理”“谁支持/反对”“当前风险”“下一步动作”“能力是否胜任”。
- 卡片排列必须先按业务优先级，再按证据深度组织：需要 Owner 处理或感知的事项在前，核心状态居中，支撑证据、健康和审计在后；同一页面内不得把审批、风险、账户、研究和系统健康随机混排。
- 卡片内优先使用中文标签、数值、状态徽标、迷你趋势、版本号和证据引用，避免空洞说明文。
- Owner 默认卡片不得暴露设计或实现过程材料，例如非 A 股边界守卫、Prompt/Skill 版本、ContextSnapshot、trace_id、read model 或工具调用；这些内容必须转译为老板可决策的业务信息，或下沉到审计/配置详情。
- 同页卡片应保持统一圆角、阴影、间距和色阶；风险、审批、阻断和生效状态用稳定语义色，不靠大段文字解释。
- 禁止卡片套卡片；需要分组时使用 full-width band、表格、segmented panel 或列表。
- Trace/Debug、raw event、schema 错误和 tool call 默认折叠在审计层，不污染 Owner 默认卡面。

## 4. 三层可视化模型

### 4.1 Owner Decision View

默认层，只回答：

- 现在要不要我处理？
- 这件事到哪一步了？
- 谁支持、谁反对？
- 为什么行动或不行动？
- 风险和例外是什么？
- 数据可信吗？
- 如果批准或不批准会怎样？

核心组件：

- Today Attention Strip：风险、审批、manual_todo、数据降级、系统 incident。
- S0-S7 Stage Rail：当前阶段、完成阶段、blocked、skipped、reopen 标记。
- Decision Card：CIO 行动/不行动结论、目标权重、价格区间、偏离说明。
- Risk Gate Card：approved、conditional_pass、rejected、阻断原因、Owner 例外。
- Approval Packet View：推荐、替代方案、风险、影响、生效边界。

### 4.2 Investment Dossier View

投资详情页核心。建议布局：

```text
左侧：S0-S7 阶段轨迹 + Reopen Events
中间：当前阶段核心 artifact
右侧：证据、数据质量、审批/风险状态
```

multi-agent 协作组件：

- CIO Chair Brief：显示本次 IC 的决策问题、关键矛盾、必须回答的问题、时间预算和行动判定口径，并标记“未预设结论”。
- Analyst Stance Matrix：四位分析师的 `direction_score`、`confidence`、`evidence_quality`、`hard_dissent`。
- Analyst Role Payload Drilldown：按 Macro/Fundamental/Quant/Event 展开各自专属 payload，避免四份 Memo 被压成同一模板。
- Consensus Gauge：`consensus_score`、`action_conviction`、阈值解释。
- Dissent Board：hard dissent 和关键分歧。
- Debate Timeline：最多 2 轮，每轮显示 issue、补证、观点变化、结果、Workflow/Debate Manager 过程字段和 CIO agenda/synthesis，不显示长对话。
- Collaboration Handoff：显示阶段/跨角色 HandoffPacket 的来源、摘要、开放问题、阻塞项和下游消费方。
- Evidence Map：结论引用哪些 data/source/artifact，质量如何。
- Optimizer Deviation Panel：优化器建议 vs CIO 目标，单股偏离和组合主动偏离。
- Risk Gate：Risk Review 三状态、条件、阻断和重开目标。
- Execution Replay：执行窗口、VWAP/TWAP、成交/未成交、费用、滑点、T+1。
- Attribution Linkback：后续归因连接回 Memo、CIO、Risk、Execution。

### 4.3 Trace / Debug View

默认对 Owner 隐藏，供治理、DevOps、Design 或审计展开：

- Agent node sequence。
- tool calls。
- service calls。
- data source routing。
- raw trace ids。
- latency、token、cost。
- failed guard。
- schema validation errors。

Trace/Debug View 可以借鉴 multi-agent workflow visualization 的 graph、timeline、trace、node state、tool usage 和 evaluation，但不得替代 Owner 默认视图。

Trace/Debug View 对协作机制至少展示：

- CollaborationSession 运行标签。
- AgentRun 树、parent_run_id、stage、attempt、profile_version、SkillPackage 版本和 ContextSlice。
- CollaborationCommand 准入结果、接收者、拒绝原因或 Owner 审批链接。
- CollaborationEvent 时间线。
- HandoffPacket 生成和消费关系。
- Authority Gateway 写入记录、被拒绝的直接写入尝试和敏感字段访问拒绝。

## 5. 全局命令层

自由对话是命令入口，不是直接执行器。

```text
自然语言输入
 -> Intent classification
 -> Request Brief preview
 -> Owner confirm / edit / cancel
 -> Task created
 -> Workflow starts
```

规则：

- 研究、审批、执行、规则、Prompt、Skill、Agent 能力配置和财务动作都必须先生成 Request Brief、任务卡或治理变更草案。
- Owner 可确认、修改或取消 Request Brief。
- confirmation 不是 approval。
- 任何聊天输入不得绕过 S0-S7、治理状态机或 manual_todo 边界。

## 6. 全景页

全景页回答“今天我需要关注什么”。

建议区域：

- 今日关注：P0/P1 任务、持仓风险、数据降级、系统 incident。
- 纸面账户：总资产、现金、仓位、当日/累计收益、回撤。
- 风险摘要：VaR、回撤、集中度、风险预算使用。
- 审批摘要：Owner pending 高影响事项。
- manual_todo 摘要：线下动作、到期时间、风险提示。
- 每日简报摘要：只显示高信号标题。
- 系统健康：数据质量、源切换、服务状态、成本/Token 观察。

## 7. 投资页

投资页分三层：

- Opportunity/IC Queue：候选机会、正式 IC、优先级、硬门槛结果。
- Investment Workflow Detail：S0-S7 阶段轨迹、当前状态、重开事件、artifact 版本。
- Decision Dossier：单个标的或任务的完整决策包。

投资详情页按阶段展示：

- S0 Request Brief。
- S1 数据就绪与质量、Data Conflict Report、fallback/cache 标记。
- S2 四位 Analyst Memo 对比。
- S3 共识、行动强度、分歧、CIO agenda/synthesis、Debate Summary 或 debate_skipped。
- S4 CIO Decision Memo 和 Optimizer Deviation Panel。
- S5 Risk Review Report。
- S6 Owner 例外、Paper Execution Receipt。
- S7 Attribution 和 Reflection。

禁止：

- Risk rejected 页面出现 Owner 批准继续按钮。
- 非 A 股资产出现交易或投资审批入口。
- execution_core 不达标时显示“继续成交”入口。
- 用聊天 transcript 替代 Memo、Debate Summary 或 Decision Memo。

## 8. 财务页

财务页必须明确“规划”和“执行”的边界。

建议区域：

- 全资产档案：现金、A 股纸面账户、基金、黄金、房产、负债、收入支出。
- 财务健康：负债率、流动性、风险预算、压力测试。
- 投资财务：收益、成本、滑点、风险预算、现金使用率。
- 财务规划：重大支出、税务提醒、资产规划建议。
- 非 A 股资产展示：基金、黄金、房产只展示行情、估值、规划或人工待办，不在老板默认卡片中展示“边界/守卫”过程文案，也不出现交易/审批按钮。

## 9. 知识页

知识页是研究资产和学习资产，不是文件仓库。

至少包括：

- 每日简报。
- Research Package。
- Experience Library。
- Reflection Library。
- Knowledge Promotion Proposal。
- Prompt Update Proposal。
- 检索命中与默认上下文状态。

高影响知识或 Prompt 提案可跳到治理审批，但知识页本身不直接生效。

## 10. 治理下 Agent 团队工作区

Agent 团队工作区回答“这些 Agent 是否胜任岗位，以及我要如何受控调整它们”。它位于治理主菜单下，不作为一级菜单。

页面必须以中文卡面展示九个正式 Agent：

- Agent roster：CIO、CFO、Macro Analyst、Fundamental Analyst、Quant Analyst、Event Analyst、Risk Officer、Investment Researcher、DevOps Engineer 的头像/代号、职责一句话、状态、当前 profile_version、SkillPackage 版本、最近产物质量和失败/越权计数。
- Agent profile card：角色定位、能做什么、不能做什么、读什么、写什么、能调什么、何时升级、失败处理、评价指标。
- Capability matrix：工具权限、可请求服务、可提交 CollaborationCommand、可产出 artifact、默认数据域和财务敏感字段边界。
- Prompt/Skill/Context panel：当前 Prompt、SkillPackage、默认上下文、模型路由、工具权限、预算/超时和 ContextSnapshot 版本；显示版本、适用范围、最近验证结果和回滚引用。
- Quality panel：近期 Memo/Decision/Review/Proposal 质量、schema pass、证据引用完整性、被 Risk/Owner 打回原因、越权写入拒绝记录和超时记录。
- Draft editor：Owner 可编辑能力配置草案，例如工具权限、SkillPackage、默认上下文、模型路由、预算、升级规则或 evaluation rubric。

配置生效规则：

- Agent 团队工作区不能直接热改 AgentRun、workflow state、Prompt、SkillPackage 或权限。
- 任一保存动作必须生成 Governance Change 草案，含 diff、影响等级、验证计划、回滚方式和生效边界。
- 低/中影响草案经自动 triage、验证和审计后只对新任务或新 attempt 生效。
- 高影响草案进入 Owner 审批中心，审批超时为不生效。
- 在途 workflow 和 AgentRun 继续绑定旧 ContextSnapshot/配置快照。

## 11. 治理页

治理页集中处理会改变系统行为或需要 Owner 例外的事项。

核心区域：

- 任务中心：展示所有 Task Envelope。
- 审批中心：少量高质量 Owner 审批。
- Agent 团队：治理下二级工作区，通过治理页二级模块切换进入；治理卡片可作为辅助入口，但不能作为唯一入口。
- 变更管理：Prompt、配置、规则、阈值、数据源策略的版本、diff 和生效边界。
- Agent Capability Change：来自 Agent 团队工作区的能力配置草案，进入 Governance Change 队列并展示影响等级、验证结果、适用范围和回滚方式。
- 数据/服务健康：数据源、质量、冲突、降级、incident。
- 审计记录：trace_id、artifact、Reopen Event、Approval Record。

审批中心中的审批包必须展示：

- 审批对象。
- 触发原因。
- 推荐结论。
- 对比方案。
- 风险和影响范围。
- 证据引用。
- 生效边界。
- 超时默认。
- 回滚方式。

## 12. 前端验收关注点

Design 和实现必须能验证：

- 一级主导航包含 `全景 / 投资 / 财务 / 知识 / 治理`，Agent 团队工作区位于治理下，界面默认简体中文且为漂亮优先、护眼其次的高端浅色卡面式工作台。
- confirmation、approval、manual_todo 分离。
- S0-S7、artifact、数据质量、Reopen Event 在投资详情页可见。
- multi-agent 协作以 stance matrix、dissent board、debate timeline 展示。
- CIO Chair Brief、Analyst role payload、CollaborationCommand、HandoffPacket 和 AgentRun trace 可在对应层级查看。
- Agent 团队工作区能展示九个正式 Agent 的画像、能力、版本、运行质量和越权/失败记录。
- Agent 团队工作区能力配置保存只能生成 Governance Change 草案，不直接热改在途 AgentRun。
- Trace/Debug View 默认不暴露给 Owner。
- 非 A 股资产没有交易/审批入口。
- Risk rejected 不能被 Owner 覆盖。
- 高影响治理审批显示 diff、影响范围、回滚和生效边界。
