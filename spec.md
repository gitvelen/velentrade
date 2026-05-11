# spec.md

<!-- CODESPEC:SPEC:READING -->
## 0. AI 阅读契约

- 本文件是 Requirement 阶段的权威需求正文；正式 `REQ-*`、`ACC-*`、`VO-*` 只在本文正文定义，不得依赖长对话记忆才能理解 V1。
- `testing.md` 是 `TC-*` 测试计划与后续 `RUN-*` 执行证据的权威账本；它只能细化如何验证本文 `REQ/ACC/VO`，不得新增、删除或放宽验收义务。
- `spec-appendices/*` 是本文的重要索引和强证据展开层；默认不一股脑读取全部附件，但任务命中第 7 节 `appendix_reading_matrix` 中的领域时，对应附件必须读取。
- 本文已根据 `/home/admin/velentrade/inputs` 原始材料、`../inputs/sessonlog.txt` 落盘讨论记录和 Requirement 阶段用户确认结论重写；其中 `../inputs/sessonlog.txt` 是当前仓库实际存在的讨论记录文件名。
- 若本文与原始 inputs 冲突，以本文“决策与来源”中的已确认决策为准；若 Design 发现无法自洽，必须回到 Requirement 补文档，不得自行拍板。
- `spec-appendices/*` 只承载展开矩阵、索引、来源归一化和领域证据，不能替代本文正文或新增正式需求；若附件与本文冲突，必须停止并回到 Requirement 修补冲突。
- 所有后续 `design.md`、`work-items/*.yaml`、实现与验证必须能追溯到本文 `REQ-* -> ACC-* -> VO-*`，并在 `testing.md` 中找到对应 `TC-*`。

<!-- CODESPEC:SPEC:OVERVIEW -->
## 1. 需求概览

- change_goal: 建设 V1 单老板 Web 工作台，覆盖 A 股个股 IC 决策与中等拟真纸面执行，同时覆盖完整财务档案、知识/研究、任务治理、Agent 能力契约、服务编排、归因反思和安全合规边界。
- success_standard: 冷启动 AI 先读本文、`testing.md` 和 `codespec readset`，再按第 7 节矩阵读取命中领域的附件，即可设计 V1：知道做什么、不做什么、谁负责什么、哪些服务自动计算、哪些事项进入 Owner 审批、哪些只进入 `manual_todo`。
- primary_users:
  - Owner: 人类监督者，负责授权边界、例外审批、Prompt/高影响治理变更批准和最终真实资金动作。
  - CIO: 投资语义收口者，负责 IC 议题决策、组合建议解释、正式投资结论形成，不承担路由器或服务操作员职责。
  - CFO: 财务治理与解释签发者，负责全资产财务规划、绩效解释、治理提案和反思分派中需要 LLM 判断的部分。
  - Risk Officer: 独立风控复核与否决主体，负责事前/事中/事后风险关口和业务异常升级。
  - IC Analysts: Macro、Fundamental、Quant、Event 四位分析师，独立并行产出结构化 Memo。
  - Investment Researcher: 研究资料、每日简报、知识检索、议题提案、Prompt 更新提案的支撑角色。
  - DevOps Engineer: 数据、系统、服务和执行环境异常处理支撑角色。
- official_v1_agents:
  - CIO
  - CFO
  - Macro Analyst
  - Fundamental Analyst
  - Quant Analyst
  - Event Analyst
  - Risk Officer
  - Investment Researcher
  - DevOps Engineer
- non_agent_roles:
  - Owner 是人类治理角色，不纳入 Agent 记忆与自动职责体系。
- automated_services:
  - Data Collection & Quality Service
  - Market State Evaluation Engine
  - Factor Engine
  - Valuation Engine
  - Portfolio Optimization Engine
  - Risk Engine
  - Trade Execution Service，V1 仅纸面执行。
  - Performance Attribution & Evaluation Service，替代 Performance Analyst Agent。
- orchestration_centers:
  - Request Distribution Center
  - Workflow Scheduling Center
  - Service Orchestration Center
- in_scope:
  - Web-only 单老板工作台，一级主导航为 `全景 / 投资 / 财务 / 知识 / 治理`；Agent 团队能力管理下沉为治理下的二级工作区。
  - 自由对话作为全局命令入口，但必须先标准化为 Request Brief 和任务卡。
  - A 股普通股正式 IC、风控、审批例外和纸面执行闭环。
  - 基金、黄金自动行情；房产默认手工估值或定期估值；非 A 股资产只进入财务规划、风险提示或 `manual_todo`。
  - 财务档案、收入支出、债务、税务提醒/估算、资产规划、压力测试、风险预算、财务健康。
  - 投研简报、研究资料包、经验库、反思、Prompt/知识晋升提案。
  - Agent 能力契约、组织透明读与受控写、共享知识晋升、CFO 治理签发能力。
- out_of_scope:
  - 策略经理、规则路径、双轨资金分配和 IC/规则路径对比。
  - Performance Analyst 作为 Agent。
  - 飞书、邮件、短信、移动端。
  - 真实券商 API、真实下单、真实账户同步、实盘自动交易。
  - Backtrader、因子回测、完整 IC 历史回放或 LLM 历史重跑。
  - 非 A 股资产的审批、执行、交易建议闭环。
  - 对外投顾产品、多用户权限/RBAC、细粒度财务访问审计。
- compliance_statement: 非公开投顾产品，仅个人使用，所有真实资金动作由人负责。

<!-- CODESPEC:SPEC:SOURCES -->
## 2. 决策与来源

- source_refs:
  - spec-appendices/source-normalization.md
- source_owner: Owner
- rigor_profile: evidence-rich
- approval_basis: Owner 已在 Requirement 讨论中确认 V1 范围、Agent 清单、Performance Analyst 取消、CFO 治理承接、Web-only、纸面执行、非 A 股资产边界、Owner 少量高质量审批、数据质量分级、无飞书/移动/真实券商/回测、全部验收 P0。
- normalization_note: `inputs/investagents.md` 中旧版 `data-strategy.md` 引用在当前落盘材料中不存在；V1 数据需求以 `data-flow.md` 与 `data-collection-service.md` 为来源。`frontend-design.md` 旧导航、策略经理、规则路径、飞书、移动端等内容仅作为废弃历史参考，不作为 V1 权威。

### 已确认决策

- decision_id: DEC-001
  decision: V1 是单老板 Web 工作台，不做飞书、邮件、短信、移动端。
  impact: 所有通知、审批、任务、告警、回放均在 Web 内完成。
- decision_id: DEC-002
  decision: 正式投资执行范围仅 A 股普通股；基金、黄金、房产只服务财务规划和风险提示。
  impact: 非 A 股任务若需要人工动作，进入任务中心并标记 `manual_todo`，不得进入审批/执行/交易链。
- decision_id: DEC-003
  decision: V1 不接真实券商，不真实下单，不同步真实账户，只做空仓 `1,000,000 CNY` 默认本金的纸面账户。
  impact: 交易服务仅输出纸面订单、模拟成交、费用、滑点、持仓与回执。
- decision_id: DEC-004
  decision: 删除/禁用策略经理和规则路径；只保留 IC 路径。
  impact: 需求、验收、测试不得出现规则路径或策略经理作为 V1 正式能力。
- decision_id: DEC-005
  decision: Performance Analyst Agent 取消；归因、评分和评价改由自动化 Performance Attribution & Evaluation Service 完成。
  impact: 需要 LLM 解释、治理提案或反思分派时由 CFO 承接。
- decision_id: DEC-006
  decision: CIO 是语义收口者，不是服务操作员、路由器或系统瓶颈。
  impact: 编排中心自动调用服务，CIO 消费 CIO Decision Packet 并形成语义决策。
- decision_id: DEC-007
  decision: 赋予 Agent 职责必须同时赋予足够系统能力；系统设计目标是造出能胜任岗位的 Agent，而不是假设招聘到真人专家。
  impact: 每个 Agent 必须具备上下文、工具、标准、记忆、产物、权限、失败处理和评价回路。
- decision_id: DEC-008
  decision: 正式 IC 议题由开放触发源注册，经硬门槛和评分进入正式队列；CIO 不审批“是否入池”，只做语义收口和必要例外说明。
  impact: 议题发现与议题决策解耦，P0 也不能跳过 IC、风控、审计。
- decision_id: DEC-009
  decision: 风控 `rejected` 是硬阻断；`conditional_pass` 才进入 Owner 例外审批；正常 approved IC 结论通知 Owner 但不默认审批。
  impact: Owner 审批必须减少且高质量，凡需 Owner 审批必须附详细对比分析、影响范围、替代方案和明确建议。
- decision_id: DEC-010
  decision: 全部验收优先级为 P0。
  impact: `ACC-*` 全部为 P0，`testing.md` 必须为每个 `ACC-*` 给出自动化 planned `TC-*`。
- decision_id: DEC-011
  decision: 工作流采用分层状态机：所有任务共享 Task Envelope；A 股投资主链严格执行 S0-S7；高影响治理使用独立审批生效状态机；系统异常使用 incident 状态机；研究、财务和 `manual_todo` 使用轻量生命周期。
  impact: Design 不得把所有任务硬套 S0-S7，也不得把投资主链降级为普通看板。
- decision_id: DEC-012
  decision: S0-S7 使用“阶段 + 节点状态”模型；阶段节点状态仅为 `not_started / running / waiting / blocked / completed / skipped / failed`，数据降级、风险拒绝、Owner 超时、执行未成交和重开均作为结果字段或事件记录。
  impact: 状态机保持可审计但不膨胀，业务结果不得混入节点状态枚举。
- decision_id: DEC-013
  decision: 重开采用 Reopen Event 模型；旧产物不可删除，只能标记 `superseded`，目标阶段及其下游重新计算。
  impact: 任何重开都必须保留历史论证路径、原因码、作废产物和新 attempt 编号。
- decision_id: DEC-014
  decision: Owner 审批坚持少量高质量原则；confirmation、approval 和 `manual_todo` 必须分离；审批超时默认不执行/不生效。
  impact: 前端和 workflow 不得把所有需要 Owner 查看事项都塞入审批中心。
- decision_id: DEC-015
  decision: 数据采集与治理采用 Data Domain Registry、Data Source Registry、Data Request Contract、关键项硬门槛、缓存/冲突策略和 lineage 审计；第三方数据源作为可替换默认 registry，不作为硬验收供应商。
  impact: Design 必须先定义数据域、可信层级、用途授权和质量门槛，再选择具体 SDK 或存储。
- decision_id: DEC-016
  decision: Web multi-agent 可视化采用三层模型：Owner Decision View、Investment Dossier View、Trace/Debug View。
  impact: Owner 默认看到任务、产物、决策和例外，不默认阅读长聊天或开发者级 trace。
- decision_id: DEC-017
  decision: 测试验收采用 fixture-driven 与 invariant-driven 策略；保留 32 条 TC 追溯结构，但关键复杂行为必须用场景 fixture、不变量和可复核 RUN 证据验证。
  impact: 后续测试不能只验证报告字段存在，必须验证状态转换、阻断动作、治理边界和禁止入口。
- decision_id: DEC-018
  decision: Agent 采用组织透明读、网关受控写：正式 Agent 可读取业务文件、数据库只读视图、历史 artifact、过程档案、组织记忆和共享知识；持久化业务写入必须经 Authority Gateway 的 typed command/artifact API。
  impact: V1 不再以 Agent 间私有读隔离作为协作边界；边界转为写入所有权、append-only 版本、财务原始敏感字段例外和审计。
- decision_id: DEC-019
  decision: Agent 协作采用 workflow-native collaboration；核心对象为 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket，正式事实仍来自 workflow state、artifact、reason code 和审计事件。
  impact: 自由聊天、runner transcript 或子 Agent summary 不能替代正式产物；协作请求必须使用封闭命令集并经过准入。
- decision_id: DEC-020
  decision: IC 采用“CIO 语义主席 + Workflow/Debate Manager 过程权威”的双层模型；CIO 可生成 IC Chair Brief、S3 agenda/synthesis 和 S4 Decision Memo，过程调度、轮次、状态、公式和审计由 workflow 管理。
  impact: 修复“CIO 只消费结果”导致的团队协调缺口，同时防止 CIO 成为状态机、服务操作或风控绕过入口。
- decision_id: DEC-021
  decision: 四位 IC Analyst 必须作为四套独立岗位能力设计；独立性指能力、职责、产物署名、SkillPackage、rubric 与归因独立，不指业务读隔离。
  impact: Macro、Fundamental、Quant、Event 不得只用同一模板换 role 参数；统一 Memo 外壳之外必须有 role-specific payload、工具默认域、技能库和失败状态。
- decision_id: DEC-022
  decision: Prompt、知识、SkillPackage、默认上下文和共享方法论采用低/中影响自动生效、高影响 Owner 审批；所有变更只绑定新任务或新 attempt，不热改在途 AgentRun。
  impact: 研究员或责任 Agent 只能提出 proposal；低/中影响可经自动验证和审计后生效，高影响仍进入 Owner 审批。
- decision_id: DEC-023
  decision: 财务敏感原始字段是组织透明读的例外；CFO 和财务服务可解密使用收入、负债、家庭、重大支出等原始明细，其他 Agent 默认只读取风险预算、流动性约束、财务规划结论和脱敏派生 artifact。
  impact: 保留跨角色财务约束协作，同时降低单 Owner V1 下的隐私和日志泄露风险。

### 待澄清事项

- clarification_id: CLAR-001
  question: 当前无 Requirement 阶段阻塞澄清项；Design 阶段仍需细化字段、接口、页面与实现参数。
  impact_if_unresolved: 无阻塞影响。

<!-- CODESPEC:SPEC:SCENARIOS -->
## 3. 场景与行为

- scenario_id: SCN-001
  actor: Owner
  trigger: 打开 Web 全景页。
  behavior: 查看总资产、纸面账户、风险、任务、审批、知识简报、系统状态；高风险项以 Web 内横幅和通知展示。
  expected_outcome: Owner 能知道今天该看什么、是否需要审批、哪些任务是人工待办、哪些决策已自动推进。
  requirement_refs: [REQ-001, REQ-006, REQ-007]
- scenario_id: SCN-002
  actor: Owner
  trigger: 在自由对话中提出“研究某只 A 股是否可以买入”。
  behavior: 系统先生成 Request Brief 和任务卡，进入 S0-S7 主链，自动调用数据与服务，四位分析师并行产出 Memo。
  expected_outcome: 自由对话不会直接触发交易或审批，而是形成可追溯 workflow。
  requirement_refs: [REQ-006, REQ-008, REQ-010, REQ-013, REQ-014, REQ-015]
- scenario_id: SCN-003
  actor: Investment Researcher
  trigger: 每日简报、持仓事件、研究资料或知识检索发现潜在机会。
  behavior: 研究员生成研究资料包或议题提案，进入开放议题注册和优先级评分，默认 P1，除非命中持仓/风险/Owner 显式紧急硬触发。
  expected_outcome: 研究员可正式发起议题，但不参与投资投票。
  requirement_refs: [REQ-012, REQ-013, REQ-027]
- scenario_id: SCN-004
  actor: CIO
  trigger: 一个正式 IC 已完成服务计算、四份 Analyst Memo、必要辩论和风控前置材料。
  behavior: CIO 消费 CIO Decision Packet，结合组合优化建议和硬约束，形成 CIO Decision Memo；若偏离优化器建议需解释。
  expected_outcome: CIO 做语义收口，不手工操作服务；重大偏离触发 Owner 例外或重新论证。
  requirement_refs: [REQ-016, REQ-018]
- scenario_id: SCN-005
  actor: Risk Officer
  trigger: CIO Decision Memo 进入 S5 风控复核。
  behavior: 风控官基于风险引擎、数据质量、仓位、流动性、合规和执行约束输出 `approved / conditional_pass / rejected`。
  expected_outcome: `rejected` 硬阻断；`conditional_pass` 进入 Owner 例外审批并附详细对比分析。
  requirement_refs: [REQ-019]
- scenario_id: SCN-006
  actor: Trade Execution Service
  trigger: 风控通过且无 Owner 阻塞的纸面执行指令。
  behavior: 按中等拟真规则执行模拟成交，记录执行窗口、1 分钟 VWAP/TWAP、滑点、费用、印花税、T+1 和未成交/过期。
  expected_outcome: 生成可归因的 Paper Execution Receipt。
  requirement_refs: [REQ-020, REQ-021]
- scenario_id: SCN-007
  actor: CFO
  trigger: 自动归因服务发现异常，或到达周/月/季解释窗口。
  behavior: CFO 读取自动归因结果，生成 CFO Interpretation、Governance Proposal 或 Reflection Assignment。
  expected_outcome: 日常归因自动发布；只有异常或周期解释需要 CFO LLM 判断。
  requirement_refs: [REQ-024, REQ-025]
- scenario_id: SCN-008
  actor: Owner
  trigger: 录入基金、黄金、房产、收入、负债或重大支出计划。
  behavior: 系统更新财务档案、规划、税务提醒和压力测试；基金/黄金可自动行情，房产默认手工或定期估值。
  expected_outcome: 非 A 股资产不会生成审批、执行、交易或投资主链任务，必要人工动作进入 `manual_todo`。
  requirement_refs: [REQ-007, REQ-023]
- scenario_id: SCN-009
  actor: DevOps Engineer
  trigger: 数据源异常、服务异常、执行服务异常或日志安全问题。
  behavior: DevOps 处理系统层异常、降级与恢复建议，向 Risk Officer 汇报；业务风险由 Risk Officer 处理。
  expected_outcome: 系统异常不被误当成投资判断，所有降级可追溯。
  requirement_refs: [REQ-009, REQ-029, REQ-031]
- scenario_id: SCN-010
  actor: Owner
  trigger: 在治理下打开 Agent 团队工作区查看或调整 Agent 能力。
  behavior: Agent 团队工作区以中文卡面展示九个正式 Agent 的画像、职责、工具、SkillPackage、Prompt/默认上下文、近期产物质量、失败/越权记录和运行状态；Owner 可编辑能力配置草案，但提交后必须进入治理变更，按影响等级自动验证或审批，只对新任务或新 attempt 生效。
  expected_outcome: Owner 能看清每个 Agent 是否胜任岗位，并能受控调整能力，不会热改在途 AgentRun 或绕过治理状态机。
  requirement_refs: [REQ-003, REQ-006, REQ-007, REQ-030]

<!-- CODESPEC:SPEC:REQUIREMENTS -->
## 4. 需求与验收

### 需求

- req_id: REQ-001
  summary: V1 必须明确产品范围、排除项和合规声明：单老板、Web-only、A 股普通股正式投资闭环、非公开投顾产品、仅个人使用、所有真实资金动作由人负责。
  source_ref: spec-appendices/source-normalization.md
  rationale: 防止需求从个人决策辅助滑向公开投顾、多端平台或实盘交易系统。
  priority: P0
- req_id: REQ-002
  summary: V1 必须维护官方角色/服务注册表：Owner 为人类治理角色；正式 Agent 仅 CIO、CFO、四位 IC 分析师、Risk Officer、Investment Researcher、DevOps Engineer；策略经理、规则路径、Performance Analyst Agent 禁用。
  source_ref: DEC-004, DEC-005
  rationale: 角色清单决定职责、记忆、产物、验收和后续设计边界。
  priority: P0
- req_id: REQ-003
  summary: 每个正式 Agent 必须满足 Agent Capability Enablement Contract：角色定位、输入上下文、可调用工具/服务、判断标准、角色 SOP、rubric、记忆边界、标准产物、权限边界、失败处理、升级规则和评价回路齐全；治理下的 Agent 团队工作区必须让 Owner 以中文卡面查看这些画像、运行质量和配置草案入口。
  source_ref: DEC-007
  rationale: 赋予 Agent 职责必须同时赋予足以胜任职责的系统能力。
  priority: P0
- req_id: REQ-004
  summary: 系统必须采用组织透明读、网关受控写的记忆与上下文模型；正式 Agent 可读取业务文件、只读数据库视图、历史 artifact、过程档案、组织记忆、共享知识和其他 Agent 的正式产物/过程记录，但不得直接持有业务数据库写凭证；所有持久化写入必须通过 Authority Gateway 的 typed command/artifact API，按 owner_agent/producer 追加版本、评论、证据或 proposal。财务敏感原始字段是透明读例外，只向 CFO 和财务服务明文开放，其他 Agent 只读脱敏摘要、约束和派生 artifact。
  source_ref: DEC-007, DEC-018, DEC-023
  rationale: Agent 必须具备足够读取能力才能胜任岗位，同时用写入网关、append-only 所有权、快照和敏感字段例外控制污染、越权与隐私风险。
  priority: P0
- req_id: REQ-005
  summary: 所有关键协作必须以 workflow-native collaboration 承载：CollaborationSession 作为协作容器，AgentRun 作为受控岗位执行，CollaborationCommand 作为封闭协作请求，CollaborationEvent 作为 append-only 审计流，HandoffPacket 作为阶段/跨角色交接摘要；正式业务事实仍来自标准化 artifact、状态、reason code、Reopen Event 和审计记录，不得把原始长对话、runner transcript 或子 Agent summary 作为正式下游输入。S0-S7 核心 artifact 至少支持 Request Brief、Data Readiness Report、Analyst Memo、Debate Summary、CIO Decision Memo、Risk Review Report、Approval Record、Paper Execution Receipt、Attribution Report、Reflection Record；支撑 artifact 由所属 REQ/ACC/TC 覆盖，不要求逐一新增独立 ACC。
  source_ref: workflow-architecture.md, DEC-007, DEC-019
  rationale: 多 Agent 协作必须可追溯、可恢复、可复盘。
  priority: P0
- req_id: REQ-006
  summary: Web 工作台必须采用 `全景 / 投资 / 财务 / 知识 / 治理` 一级主导航，Agent 团队能力管理放在治理下；界面默认简体中文，采用漂亮优先、护眼其次、信息密度高的浅色高端卡面式投研工作台：主背景使用暖瓷/柔和中性色，卡片和控件用分层浅色表面、细边框、轻阴影和高质感语义强调色，主强调为玉绿，辅助使用靛蓝、暗金和胭脂红，避免纯白大底或深色大底造成疲劳；把结论、风险、审批、Agent 分歧、执行和团队能力放进可扫描中文卡片，而不是把后端表格、trace、非 A 股边界守卫、Prompt/Skill 版本或 ContextSnapshot 等过程材料原样摊给 Owner；全局自由对话是命令层，所有研究、审批、执行、规则、Prompt、Skill、Agent 能力配置或财务动作请求必须先转为 Request Brief、任务卡或治理变更草案；multi-agent 可视化必须按 Owner Decision View、Investment Dossier View、Trace/Debug View 分层呈现，默认不把长聊天作为老板视图。
  source_ref: DEC-001
  rationale: Web 是 V1 唯一主交互面，自由对话不能绕过 workflow。
  priority: P0
- req_id: REQ-007
  summary: 治理区必须包含任务中心、审批中心和 Agent 团队工作区；Agent 团队工作区产生的 Agent 能力、Prompt、SkillPackage、工具权限、模型路由或默认上下文配置草案必须转为 Governance Change，不得直接热改在途任务；任务中心使用统一 Task Envelope，投资主链绑定 S0-S7 与 reason code，高影响治理绑定治理状态机，系统异常绑定 incident 状态；非 A 股或系统外人工动作进入任务中心并标记 `manual_todo`，不得进入审批/执行/交易链。
  source_ref: DEC-001, DEC-002, DEC-009
  rationale: 保留完整任务追踪，同时防止非投资动作误入交易治理链。
  priority: P0
- req_id: REQ-008
  summary: V1 必须实现严格 S0-S7 投资主链：S0 请求受理、S1 数据就绪、S2 分析研判、S3 辩论收敛、S4 CIO 收口、S5 风控复核、S6 授权放行与纸面执行、S7 归因反思；每阶段使用最小节点状态集合，重开必须通过 Reopen Event 标记原因、目标阶段、作废产物和保留产物。
  source_ref: workflow-architecture.md
  rationale: 这是投资任务的最小可审计生命周期。
  priority: P0
- req_id: REQ-009
  summary: 数据权威来源为 `data-flow.md` 与 `data-collection-service.md`；所有正式数据访问必须经过 Data Domain Registry、Data Source Registry 和 Data Request Contract；`decision_core` 数据质量 `>=0.9` 正常，`0.7-0.9` 可研究但必须标记降级且 Risk Review 只能 `conditional_pass` 并需 Owner 例外，`<0.7` 必须自动切源/fallback 且仍不可恢复时阻断新决策和执行；`execution_core` 使用当前 workflow 配置快照中的生效阈值，默认 `0.9`，低于生效阈值时严格阻断纸面执行，阈值变更属于高影响治理且只对新任务生效。
  source_ref: DEC-009, data-flow.md, data-collection-service.md
  rationale: 数据质量是投资决策链的硬前提，必须可降级但不能掩盖风险。
  priority: P0
- req_id: REQ-010
  summary: 服务层必须自动提供数据质量、市场状态、因子、估值、组合优化、风险、纸面执行、绩效归因与评价能力；服务输出计算结果、约束和建议，不拥有投资判断、审批或否决权。
  source_ref: DEC-006
  rationale: 避免把 CIO 或任何 Agent 做成服务操作瓶颈，同时保持治理权清晰。
  priority: P0
- req_id: REQ-011
  summary: 市场状态评估引擎默认自动生效，并正式驱动协作模式、因子权重建议和 IC Context；Macro Analyst 可提出覆盖并留痕，但不作为市场状态生效前置门。
  source_ref: market-state-evaluation-engine.md
  rationale: 市场状态是运行时服务能力，不应让宏观分析师成为常规瓶颈。
  priority: P0
- req_id: REQ-012
  summary: 机会/议题来源必须开放注册，至少包括 Owner 请求、四位分析师发现、Investment Researcher 提案、自动行情/公告/持仓风险触发和服务层信号；新闻、舆情、资金流等 supporting evidence 只能触发候选机会、研究任务或资料包，注册不等于进入正式 IC。
  source_ref: core-mechanisms.md, DEC-008
  rationale: 机会发现不能只依赖单一角色或单一入口。
  priority: P0
- req_id: REQ-013
  summary: 正式 IC 队列必须由硬门槛和四维 0-5 优先级评分决定；硬门槛至少检查 A 股普通股范围、Request Brief 完整性、核心数据可用性、研究资料非空、合规/执行禁区、同主题去重和并发槽；四维为机会强度、数据/资料完备度、风险紧急度、组合/持仓相关性；正式 IC 最多 3 个并发，全局 workflow 最多 5 个并发；P0 可抢占但不能跳过 IC/风控/审计。
  source_ref: DEC-008
  rationale: 管住并发和优先级，防止 CIO 或分析师被无限议题拖垮。
  priority: P0
- req_id: REQ-014
  summary: 正式 IC 启动前必须生成 IC Context Package，并由 CIO 在 S1 后输出 IC Chair Brief；IC Context Package 包含共享事实包、服务计算结果、市场状态、组合上下文、风险约束、研究资料包、历史反思命中和四类分析师角色附件，IC Chair Brief 只能定义本次决策问题、关注边界、关键矛盾、必须回答的问题、时间预算和行动判定口径，不得预设买卖结论或替任何 Analyst 指定结论。
  source_ref: workflow-architecture.md, DEC-020
  rationale: 四位分析师必须基于同一事实底座和同一议题目标工作，同时避免 CIO 前置协调污染岗位责任判断。
  priority: P0
- req_id: REQ-015
  summary: Macro、Fundamental、Quant、Event 四位分析师必须作为四套独立 CapabilityProfile、SkillPackage、rubric 与权限默认域并行产出署名 Analyst Memo；每份 Memo 必含统一外壳字段 `direction_score(-5..+5)`、`confidence(0..1)`、`evidence_quality(0..1)`、`hard_dissent`、支持证据、反证/风险、适用条件、失效条件、对 IC 的行动含义和证据引用，并必须包含 role-specific payload。Macro payload 覆盖市场状态、政策传导、流动性和行业风格；Fundamental payload 覆盖商业质量、财务质量、盈利情景、估值和会计红旗；Quant payload 覆盖信号假设、因子、趋势、稳定性和择时含义；Event payload 覆盖事件类型、来源可靠性、验证状态、催化窗口、历史类比和反转风险。
  source_ref: core-mechanisms.md, DEC-021
  rationale: 统一 Memo 外壳支撑共识计算、辩论、CIO 收口和归因评价；role payload 保证四个岗位不是同一模板换名。
  priority: P0
- req_id: REQ-016
  summary: 系统必须自动计算 `consensus_score = 0.6*(1-std(direction_score/5)) + 0.4*dominant_direction_share` 与 `action_conviction = 0.35*abs(avg(direction_score/5)) + 0.25*avg(confidence) + 0.20*avg(evidence_quality) + 0.20*consensus_score`，默认行动阈值为 `0.65`；公式输入、`dominant_direction_share` 与 `std` 口径按第 6 节共识契约执行。`action_conviction < 0.65` 不得生成纸面执行授权，即使共识分较高也只能进入观察、补证、重开或不行动路径。
  source_ref: core-mechanisms.md
  rationale: 投委会结论需要可观测的共识和行动强度，而不是自然语言汇总。
  priority: P0
- req_id: REQ-017
  summary: IC 辩论规则必须区分高共识、需辩论和不可执行，并采用“CIO 语义主席 + Workflow/Debate Manager 过程权威”的双层模型：`consensus >=0.8` 且无 hard dissent、且 `action_conviction >=0.65` 可跳过辩论；`consensus >=0.8` 但存在 hard dissent 不得跳过 S3，必须最多 2 轮有界辩论，若辩论后仍保留 hard dissent 则进入 Risk Review；`0.7 <= consensus < 0.8` 触发最多 2 轮有界辩论，若辩论后仍保留 hard dissent 也必须进入 Risk Review；辩论参与者为四位分析师，输入为 IC Context Package、IC Chair Brief、四份 Analyst Memo 和可引用补证；Workflow/Debate Manager 控制派发、轮次、超时、状态、公式重算和审计，CIO 负责 agenda、追问、语义综合和保留分歧说明；输出 Debate Summary，辩论后重算共识与行动强度；`consensus <0.7` 或 `action_conviction <0.65` 不允许纸面执行；hard dissent 相关 Risk `rejected` 仍硬阻断。
  source_ref: core-mechanisms.md, DEC-009, DEC-020
  rationale: 保留反证、异议和 CIO 主席能力，同时防止辩论无界、过程状态失控或绕过风控。
  priority: P0
- req_id: REQ-018
  summary: CIO 必须承担 IC 语义主席和投资收口职责：S1 后生成 IC Chair Brief，S3 需要时形成 Debate agenda/synthesis，S4 消费由编排层生成的 CIO Decision Packet 并形成 CIO Decision Memo；组合优化器只提供硬约束内的建议目标组合，CIO 可语义偏离但必须说明原因；单股目标权重偏离 `5pp` 或组合主动偏离 `20%` 及以上触发 Owner 例外或由编排中心重开论证，组合主动偏离按 `0.5 * Σ|CIO目标权重 - 优化器建议权重|` 计算。CIO 不得直接创建 AgentRun、操作服务、修改状态、下单、审批例外或覆盖 Risk rejected。
  source_ref: DEC-006, DEC-020
  rationale: 保持 CIO 的语义判断和团队协调价值，同时防止其成为服务、状态机或风控瓶颈。
  priority: P0
- req_id: REQ-019
  summary: Risk Officer 必须独立输出 Risk Review Report，状态仅可为 `approved / conditional_pass / rejected`；`rejected` 硬阻断当前 attempt，Risk Officer 必须在报告中判定 `repairable / unrepairable`，可修复时只能附 `reopen_target` 和 reason code 并通过 Reopen Event 回上游重做，不可修复时当前 attempt 终止且不得进入 Owner 例外审批；`conditional_pass` 进入 Owner 例外审批，Owner 审批必须附详细对比分析、影响范围、替代方案和明确建议；Owner 未在默认超时策略内响应时不执行/不生效，记录 `owner_timeout`，并按审批类型 `expired`、S6 blocked、重开 S4 或关闭。
  source_ref: DEC-009
  rationale: 风控独立性和 Owner 少量高质量审批是安全边界。
  priority: P0
- req_id: REQ-020
  summary: 纸面账户默认以 `1,000,000 CNY`、空仓、现金 100% 初始化；可重置但所有验收默认使用该本金；纸面账户必须记录现金、持仓、成本、收益、回撤、风险预算与基准。
  source_ref: DEC-003
  rationale: 纸面执行、绩效、风控和财务规划需要稳定基线。
  priority: P0
- req_id: REQ-021
  summary: Trade Execution Service V1 仅做中等拟真纸面执行：默认下个交易日执行，urgent 30 分钟、normal 2 小时、low 全日窗口；优先 1 分钟 VWAP，缺失时 TWAP；价格区间未命中则 unfilled/expired；记录滑点、佣金、印花税、过户费、T+1。
  source_ref: trade-execution-service.md, DEC-003
  rationale: 纸面执行必须足以支持归因，但不模拟复杂微观撮合。
  priority: P0
- req_id: REQ-022
  summary: 持仓监控和处置必须覆盖 A 股持仓异常波动、重大公告、风险阈值、执行失败和止损/暂停建议；紧急任务可提高优先级但不得取消 S5 风控和审计。
  source_ref: workflow-architecture.md
  rationale: 持仓风险处置是 V1 高优先级场景。
  priority: P0
- req_id: REQ-023
  summary: 财务模块必须覆盖全资产档案、收入支出、债务、税务提醒/估算、资产规划、压力测试、风险预算、财务健康；基金/黄金可自动行情，房产默认手工或定期估值；非 A 股资产不得生成审批、执行或交易任务。
  source_ref: DEC-002
  rationale: 完整财务模块与 A 股执行边界必须同时成立。
  priority: P0
- req_id: REQ-024
  summary: Performance Attribution & Evaluation Service 必须自动发布日度归因和角色/服务评价，覆盖收益、风险、成本、滑点、因子贡献、IC 决策质量、证据质量、反证质量、适用/失效条件命中情况。
  source_ref: DEC-005
  rationale: 归因评价是自动计算服务，不再由 Performance Analyst Agent 承担。
  priority: P0
- req_id: REQ-025
  summary: CFO 必须承接归因结果中需要 LLM 的解释、治理签发和反思分派，产物为 CFO Interpretation、Governance Proposal、Reflection Assignment；财务规划建议不作为独立正式 artifact，归入 Governance Proposal 的财务规划/风险预算子类型；低影响仅观察/报告，中影响通知相关 Agent/上下文，高影响涉及因子权重、风险预算、规则、Prompt、审批规则、执行参数时必须 Owner 审批。
  source_ref: DEC-005, DEC-007
  rationale: 取消 Performance Analyst 后，CFO 必须具备足够能力承担财务治理判断。
  priority: P0
- req_id: REQ-026
  summary: 因子研究允许新增因子，但必须走研究准入、样本与适用市场状态说明、独立验证、上线登记、持续监控和失效诊断；V1 不实现回测能力，不能把回测作为验收条件。
  source_ref: DEC-001, DEC-010
  rationale: 支持因子演进但避免把 V1 扩成回测平台。
  priority: P0
- req_id: REQ-027
  summary: Investment Researcher 必须支持每日简报、P0/P1 分类、会前资料包、知识检索、议题提案、知识晋升提案、Prompt 更新提案和 SkillPackage 更新提案；研究员是研究/知识任务的 semantic lead，可准备 diff、适用范围、验证结果和回滚方案，但不能直接改 Agent 能力、默认上下文、Prompt 或 SkillPackage，也不能参与投资投票。低/中影响知识、Prompt、Skill 更新可在自动验证和审计后只对新任务或新 attempt 生效；高影响变更必须 Owner 审批。
  source_ref: DEC-007, DEC-022
  rationale: 研究员是知识和议题入口，能力演进必须受控但不应把所有低/中影响优化都变成 Owner 审批负担。
  priority: P0
- req_id: REQ-028
  summary: 反思和学习闭环必须由服务触发、CFO 确认范围、责任 Agent 撰写一稿、Researcher 提出知识/Prompt/Skill 晋升或更新提案；低/中影响提案经自动验证、影响评级、版本快照和审计后可对新任务或新 attempt 生效，高影响知识、Prompt、Skill 或配置变更必须 Owner 审批；反思不得直接改运行参数或热改在途任务。
  source_ref: DEC-005, DEC-007, DEC-022
  rationale: 组织学习需要闭环，但不能绕过治理生效。
  priority: P0
- req_id: REQ-029
  summary: DevOps Engineer 必须处理系统层异常、数据源故障、服务降级、执行环境异常、成本/Token 观测和恢复建议，并向 Risk Officer 汇报；成本与 Token 预算是运营观测指标，不作为 V1 验收目标。
  source_ref: DEC-010
  rationale: 系统可靠性需要责任主体，但不能把成本预算做成需求验收硬条件。
  priority: P0
- req_id: REQ-030
  summary: 配置治理必须覆盖阈值、风控参数、审批规则、Prompt、SkillPackage、默认上下文、知识生效策略、服务降级策略、数据源路由策略和执行参数；低/中影响变更可经过自动 triage、schema/fixture 验证、影响评估、版本快照和审计后 `effective`，高影响变更必须经过 `draft -> triage -> assessment -> owner_pending -> approved -> effective` 状态机并包含 Owner 审批、对比分析、版本快照和回滚信息；所有变更只对新任务或新 attempt 生效，在途任务必须绑定旧 ContextSnapshot/配置快照，不能被热改。
  source_ref: DEC-007, DEC-009, DEC-022
  rationale: 运行规则变化会直接影响投资行为，必须可审计。
  priority: P0
- req_id: REQ-031
  summary: V1 按单 Owner 假设处理安全：财务档案必须加密存储，普通日志不得写敏感明文；财务敏感原始字段只向 CFO 和财务服务明文开放，其他 Agent 只能读取脱敏约束摘要和派生 artifact；不要求多用户 RBAC，但必须区分 runner 无业务写凭证、只读 DB 账号、Authority Gateway 写入和敏感字段解密边界；若未来多用户或云端协作必须重开安全需求。
  source_ref: DEC-001, DEC-018, DEC-023
  rationale: 在单用户 V1 控制复杂度，同时保留 Agent 足够读取能力、写入治理和财务隐私底线。
  priority: P0
- req_id: REQ-032
  summary: Requirement 正文必须保持自足，并通过 appendix 索引拆分详细矩阵；Design 阶段不得在 appendix 中新增正式需求，只能承接本文 `REQ/ACC/VO/TC`。
  source_ref: phase-review-policy.md
  rationale: 控制复杂项目上下文，同时保持需求主文档权威。
  priority: P0

### 验收

- acc_id: ACC-001
  requirement_ref: REQ-001
  expected_outcome: 文档、配置和 UI 范围均表明 V1 是 Web-only、个人使用、非公开投顾、A 股普通股正式投资闭环，且没有飞书、移动端、真实券商、回测和非 A 股交易入口。
  priority: P0
  priority_rationale: 范围边界决定 V1 是否可实施，偏离会直接扩大项目风险。
  status: approved
- acc_id: ACC-002
  requirement_ref: REQ-002
  expected_outcome: 官方注册表只包含 V1 Agent 清单和自动化服务清单；策略经理、规则路径、Performance Analyst Agent 不作为可调度角色出现。
  priority: P0
  priority_rationale: 角色注册表决定职责、调度和后续设计边界。
  status: approved
- acc_id: ACC-003
  requirement_ref: REQ-003
  expected_outcome: 每个正式 Agent 都能回答它是谁、能做什么、不能做什么、读什么、写什么、能调什么、何时升级、如何失败处理、如何被评价；治理下的 Agent 团队工作区能以中文卡面展示 Agent 画像、运行质量、近期产物、权限/Skill/Prompt 版本和配置草案入口。
  priority: P0
  priority_rationale: Agent 被赋责必须具备足够能力，否则系统会在岗位职责处失效。
  status: approved
- acc_id: ACC-004
  requirement_ref: REQ-004
  expected_outcome: Agent 可组织透明读取业务资料、正式产物、过程档案、组织记忆和共享知识；runner 无业务数据库写凭证，所有持久化写入经 Authority Gateway 形成 append-only artifact、event、comment、proposal 或 typed command；财务敏感原始字段不向非 CFO/财务服务明文暴露。
  priority: P0
  priority_rationale: 读能力、写入治理和敏感字段例外共同决定 Agent 是否既能胜任岗位又不污染业务事实源。
  status: approved
- acc_id: ACC-005
  requirement_ref: REQ-005
  expected_outcome: 任一正式 workflow 都能从 CollaborationSession、AgentRun、封闭 CollaborationCommand、CollaborationEvent、HandoffPacket、核心/支撑 artifact、状态和 reason code 追溯输入、输出、责任主体、准入结果和审计记录，不依赖长对话、runner transcript 或子 Agent summary 作为下游事实源。
  priority: P0
  priority_rationale: 标准产物链是多 Agent 工作流可恢复、可复盘的基础。
  status: approved
- acc_id: ACC-006
  requirement_ref: REQ-006
  expected_outcome: Web 一级主导航包含 `全景 / 投资 / 财务 / 知识 / 治理`，不再把团队作为一级菜单；Agent 团队能力管理位于治理下，并可通过治理页二级模块切换进入；主界面默认简体中文并采用漂亮优先、护眼其次、高信息密度的高端浅色卡面，主题使用暖瓷底色、墨色文字、玉绿主强调、靛蓝/暗金/胭脂红辅助色；自由对话触发的研究、审批、执行、规则、Prompt、Skill、Agent 能力配置或财务动作均先形成 Request Brief、任务卡或治理变更草案。
  priority: P0
  priority_rationale: Web 是 V1 唯一交互面，自由对话必须受控进入 workflow。
  status: approved
- acc_id: ACC-007
  requirement_ref: REQ-007
  expected_outcome: 任务中心展示 S0-S7 状态和 reason code；`manual_todo` 任务不会进入审批、执行或交易链；Owner 审批项都包含详细对比分析和建议；Agent 团队工作区提交的 Agent 能力配置草案必须进入治理状态机，低/中影响自动验证后只对新任务或新 attempt 生效，高影响进入 Owner 审批。
  priority: P0
  priority_rationale: 任务和审批治理决定 Owner 负担与非 A 股动作隔离。
  status: approved
- acc_id: ACC-008
  requirement_ref: REQ-008
  expected_outcome: 投资任务可完整经过 S0-S7，每阶段都有责任主体、输入、输出、停止/重开条件和阶段产物。
  priority: P0
  priority_rationale: S0-S7 是 V1 投资决策闭环主链。
  status: approved
- acc_id: ACC-009
  requirement_ref: REQ-009
  expected_outcome: `decision_core` 数据质量在 `>=0.9`、`0.7-0.9`、`<0.7` 三档触发对应的正常、降级/Owner 例外、切源后不可恢复阻断行为；`execution_core` 低于当前生效阈值时严格阻断纸面执行。
  priority: P0
  priority_rationale: 数据质量是所有投资判断和执行的硬前提。
  status: approved
- acc_id: ACC-010
  requirement_ref: REQ-010
  expected_outcome: 服务层自动产出计算结果、约束和建议；任何服务都不能直接生成投资审批、风控否决或真实交易动作。
  priority: P0
  priority_rationale: 服务边界用于防止自动计算越权成投资治理主体。
  status: approved
- acc_id: ACC-011
  requirement_ref: REQ-011
  expected_outcome: 市场状态引擎结果默认进入 IC Context、协作模式和因子权重建议；Macro Analyst 覆盖必须留痕且不是默认前置门。
  priority: P0
  priority_rationale: 市场状态驱动 IC 行为和因子建议，必须明确生效边界。
  status: approved
- acc_id: ACC-012
  requirement_ref: REQ-012
  expected_outcome: Owner、分析师、研究员、自动触发和服务信号都能注册机会；注册记录与正式 IC 状态区分明确。
  priority: P0
  priority_rationale: 机会入口决定系统发现能力和议题治理质量。
  status: approved
- acc_id: ACC-013
  requirement_ref: REQ-013
  expected_outcome: 系统按明确硬门槛和四维评分确定队列优先级，正式 IC 并发不超过 3，全局 workflow 不超过 5，P0 抢占留痕且不跳关口。
  priority: P0
  priority_rationale: 并发和优先级直接影响 Agent 负载、上下文隔离和决策质量。
  status: approved
- acc_id: ACC-014
  requirement_ref: REQ-014
  expected_outcome: 正式 IC 启动时生成 IC Context Package 和 CIO IC Chair Brief；Context Package 包含共享事实包、服务结果、组合/风险上下文、研究资料和四类角色附件，Chair Brief 只给出议题焦点、关键矛盾、必须回答的问题和时间/行动口径，不预设结论。
  priority: P0
  priority_rationale: IC 上下文包决定四位分析师是否能在同一事实底座上独立判断。
  status: approved
- acc_id: ACC-015
  requirement_ref: REQ-015
  expected_outcome: 四位分析师以四套独立 CapabilityProfile、SkillPackage、rubric 与权限默认域并行产出署名 Analyst Memo；Memo 统一外壳满足评分范围、证据质量、hard dissent、证据引用、反证、适用/失效条件契约，并包含 Macro/Fundamental/Quant/Event 各自 role_payload。
  priority: P0
  priority_rationale: Analyst Memo 是共识、辩论、CIO 收口和归因评价的核心输入。
  status: approved
- acc_id: ACC-016
  requirement_ref: REQ-016
  expected_outcome: 系统能按公式计算 consensus_score 和 action_conviction，并基于默认 `0.65` 行动阈值输出可解释行动/不行动判定；行动强度不足时不生成纸面执行授权。
  priority: P0
  priority_rationale: 共识和行动强度公式让 IC 结论可观测、可比较。
  status: approved
- acc_id: ACC-017
  requirement_ref: REQ-017
  expected_outcome: 高共识、行动强度达标且无 hard dissent 可生成 debate_skipped；高共识但存在 hard dissent 必须先完成有界辩论，若异议仍保留则进入 Risk Review；中等共识进入有界辩论并产出 Debate Summary，辩论后保留 hard dissent 时也进入 Risk Review；低共识或行动强度不足不执行；Debate Summary 同时包含 Workflow/Debate Manager 的过程字段和 CIO 的 agenda/synthesis 语义字段；hard dissent 相关 Risk rejected 不可绕过。
  priority: P0
  priority_rationale: 分歧处理决定投委会是否能安全收敛。
  status: approved
- acc_id: ACC-018
  requirement_ref: REQ-018
  expected_outcome: CIO 能在 S1 后生成 Chair Brief、在 S3 必要时主持语义 agenda/synthesis、在 S4 使用 Decision Packet 形成 Memo；偏离组合优化建议必须说明，超过单股或组合主动偏离阈值时触发 Owner 例外或由编排中心重开论证；CIO 不能直接操作服务、创建 AgentRun、改状态、下单、审批例外或覆盖 Risk rejected。
  priority: P0
  priority_rationale: CIO 与服务的边界决定系统是否避免 CIO 瓶颈和任意偏离。
  status: approved
- acc_id: ACC-019
  requirement_ref: REQ-019
  expected_outcome: Risk Review 只输出三种状态；`rejected` 阻断并由 Risk Officer 判定可修复性，可修复只能重开，不可修复终止当前 attempt；`conditional_pass` 进入 Owner 例外审批且审批材料完整；Owner 超时按审批类型不执行/不生效并留痕。
  priority: P0
  priority_rationale: 独立风控和少量高质量审批是投资安全核心。
  status: approved
- acc_id: ACC-020
  requirement_ref: REQ-020
  expected_outcome: 纸面账户可按 `1,000,000 CNY` 空仓初始化，并产生现金、持仓、成本、收益、回撤和风险预算基线。
  priority: P0
  priority_rationale: 统一账户基线是执行、绩效和风控验证前提。
  status: approved
- acc_id: ACC-021
  requirement_ref: REQ-021
  expected_outcome: 纸面执行能按优先级窗口、VWAP/TWAP、价格区间、费用、滑点、印花税、T+1 生成成交或未成交回执。
  priority: P0
  priority_rationale: 中等拟真执行是后续归因和风控闭环的基础。
  status: approved
- acc_id: ACC-022
  requirement_ref: REQ-022
  expected_outcome: 持仓异常、重大公告、风险阈值和执行失败可触发持仓处置任务，但仍保留风控和审计关口。
  priority: P0
  priority_rationale: 持仓处置是 V1 最关键的风险响应场景之一。
  status: approved
- acc_id: ACC-023
  requirement_ref: REQ-023
  expected_outcome: 财务模块可维护全资产档案和规划；基金/黄金自动行情、房产手工或定期估值；非 A 股不会生成交易或审批。
  priority: P0
  priority_rationale: 财务完整性和非 A 股交易隔离必须同时成立。
  status: approved
- acc_id: ACC-024
  requirement_ref: REQ-024
  expected_outcome: 自动归因服务发布日度归因与评价，覆盖收益、风险、成本、因子、IC 质量和证据/反证质量。
  priority: P0
  priority_rationale: 取消 Performance Analyst Agent 后，自动归因服务必须承担闭环评价。
  status: approved
- acc_id: ACC-025
  requirement_ref: REQ-025
  expected_outcome: CFO 可基于异常或周期归因生成 Interpretation、Governance Proposal、Reflection Assignment；财务规划建议归入 Governance Proposal 子类型；高影响治理提案必须 Owner 审批。
  priority: P0
  priority_rationale: CFO 被赋予治理签发职责后必须具备可验证能力和审批边界。
  status: approved
- acc_id: ACC-026
  requirement_ref: REQ-026
  expected_outcome: 新增因子走研究准入、独立验证、登记、监控、失效诊断；V1 测试不要求回测能力。
  priority: P0
  priority_rationale: 因子演进需要治理，且不得把 V1 扩展成回测平台。
  status: approved
- acc_id: ACC-027
  requirement_ref: REQ-027
  expected_outcome: 研究员能产出简报、资料包、检索、议题提案、知识晋升、Prompt 更新和 SkillPackage 更新提案；低/中影响提案经自动验证和审计后只影响新任务或新 attempt，高影响提案经 Owner 审批后才生效。
  priority: P0
  priority_rationale: 研究员是知识和议题入口，Prompt 生效必须受控。
  status: approved
- acc_id: ACC-028
  requirement_ref: REQ-028
  expected_outcome: 反思链路按服务触发、CFO 确认、责任 Agent 一稿、Researcher 晋升提案、低/中影响自动验证生效或高影响 Owner 审批推进，且不直接热改参数、Prompt、Skill 或在途上下文。
  priority: P0
  priority_rationale: 学习闭环必须能改进系统但不能绕过治理。
  status: approved
- acc_id: ACC-029
  requirement_ref: REQ-029
  expected_outcome: DevOps 能对数据源、服务、执行环境和成本/Token 观测产生异常处理与恢复建议，并向 Risk Officer 汇报。
  priority: P0
  priority_rationale: 系统可靠性和业务风险必须有清晰交接。
  status: approved
- acc_id: ACC-030
  requirement_ref: REQ-030
  expected_outcome: 低/中影响配置、Prompt、Skill、知识或默认上下文变更有自动 triage、验证、版本快照和审计；高影响变更必须有提案、对比分析、Owner 审批和新任务生效边界；在途任务与 AgentRun 绑定 ContextSnapshot/配置快照且不被热改。
  priority: P0
  priority_rationale: 配置治理直接影响投资行为和可审计性。
  status: approved
- acc_id: ACC-031
  requirement_ref: REQ-031
  expected_outcome: 财务档案加密存储，普通日志不含敏感明文；非 CFO/财务服务 Agent 不能读取财务敏感原始字段明文，只能读取脱敏摘要和派生 artifact；系统文档明确单 Owner 假设、runner 无业务写凭证、只读 DB 账号、Authority Gateway 写入和未来多用户需重开安全需求。
  priority: P0
  priority_rationale: 财务隐私是 V1 单用户假设下的最低安全边界。
  status: approved
- acc_id: ACC-032
  requirement_ref: REQ-032
  expected_outcome: 本文包含完整 `REQ/ACC/VO`，appendix 只展开矩阵；Design kickoff 读取指定附件，Implementation 按 WI on-demand 读取附件，任何阶段都不能依赖附件新增正式需求。
  priority: P0
  priority_rationale: 需求主文档自足是后续 Design 和 Implementation 不跑偏的前提。
  status: approved

### 验证义务

- vo_id: VO-001
  acceptance_ref: ACC-001
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证范围排除、合规声明、Web-only 与执行边界。
  artifact_expectation: scope_boundary_report.json
- vo_id: VO-002
  acceptance_ref: ACC-002
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 Agent 和 Service registry 不含禁用角色。
  artifact_expectation: registry_validation_report.json
- vo_id: VO-003
  acceptance_ref: ACC-003
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证每个 Agent 能力卡字段齐全，并验证治理下的 Agent 团队工作区中文卡面能展示 Agent 画像、运行质量、版本和配置草案入口。
  artifact_expectation: agent_capability_contract_report.json
- vo_id: VO-004
  acceptance_ref: ACC-004
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证组织透明读取、runner 无业务写凭证、Authority Gateway 受控写入、append-only 所有权、上下文快照和财务敏感原始字段例外。
  artifact_expectation: memory_boundary_report.json
- vo_id: VO-005
  acceptance_ref: ACC-005
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 CollaborationSession、AgentRun、封闭 CollaborationCommand、CollaborationEvent、HandoffPacket、核心/支撑 artifact、状态、reason code 和审计记录。
  artifact_expectation: collaboration_trace_report.json
- vo_id: VO-006
  acceptance_ref: ACC-006
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 Web 一级导航不包含团队菜单、Agent 团队工作区位于治理下、默认简体中文、漂亮优先且护眼其次的高端浅色卡面，以及自由对话转 Request Brief、任务卡或治理变更草案。
  artifact_expectation: web_command_routing_report.json
- vo_id: VO-007
  acceptance_ref: ACC-007
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 S0-S7 任务状态、manual_todo 隔离、审批材料完整性，以及治理下 Agent 团队工作区的 Agent 能力配置草案进入治理状态机且不热改在途 AgentRun。
  artifact_expectation: governance_task_report.json
- vo_id: VO-008
  acceptance_ref: ACC-008
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 S0-S7 投资主链阶段产物与重开条件。
  artifact_expectation: s0_s7_workflow_report.json
- vo_id: VO-009
  acceptance_ref: ACC-009
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 `decision_core` 三档数据质量降级、切源后不可恢复阻断、Owner 例外，以及 `execution_core` 当前生效阈值阻断。
  artifact_expectation: data_quality_degradation_report.json
- vo_id: VO-010
  acceptance_ref: ACC-010
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证服务层只输出计算结果、约束和建议，不越权决策。
  artifact_expectation: service_boundary_report.json
- vo_id: VO-011
  acceptance_ref: ACC-011
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证市场状态默认生效、驱动协作和宏观覆盖留痕。
  artifact_expectation: market_state_report.json
- vo_id: VO-012
  acceptance_ref: ACC-012
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证开放议题注册源与正式 IC 区分。
  artifact_expectation: topic_registration_report.json
- vo_id: VO-013
  acceptance_ref: ACC-013
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证硬门槛维度、四维评分、IC 并发 3、全局并发 5 和 P0 抢占。
  artifact_expectation: topic_queue_report.json
- vo_id: VO-014
  acceptance_ref: ACC-014
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 IC Context Package 共享包、角色附件和 CIO IC Chair Brief 不预设结论。
  artifact_expectation: ic_context_package_report.json
- vo_id: VO-015
  acceptance_ref: ACC-015
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证四位 Analyst 独立 CapabilityProfile、SkillPackage、rubric、权限默认域、Analyst Memo 统一外壳和 role-specific payload。
  artifact_expectation: analyst_memo_report.json
- vo_id: VO-016
  acceptance_ref: ACC-016
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 consensus_score 与 action_conviction 公式和阈值。
  artifact_expectation: consensus_action_report.json
- vo_id: VO-017
  acceptance_ref: ACC-017
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证高共识无异议跳过辩论、高共识 hard dissent 先有界辩论后风控、中等共识有界辩论、Debate Summary 过程字段与 CIO agenda/synthesis、低共识阻断和 hard dissent 风控序列。
  artifact_expectation: debate_dissent_report.json
- vo_id: VO-018
  acceptance_ref: ACC-018
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 CIO Chair Brief、S3 语义主席字段、Decision Packet、语义偏离说明、组合主动偏离计算、重大偏离例外/重开和 CIO 禁止越权动作。
  artifact_expectation: cio_optimizer_report.json
- vo_id: VO-019
  acceptance_ref: ACC-019
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 Risk Review 三状态、rejected 硬阻断与可修复性判定、conditional_pass Owner 例外材料和 Owner 超时按类型无效果。
  artifact_expectation: risk_owner_exception_report.json
- vo_id: VO-020
  acceptance_ref: ACC-020
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证纸面账户 100 万空仓初始化和基线指标。
  artifact_expectation: paper_account_report.json
- vo_id: VO-021
  acceptance_ref: ACC-021
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证中等拟真纸面执行、窗口、VWAP/TWAP、费用、T+1 和未成交。
  artifact_expectation: paper_execution_report.json
- vo_id: VO-022
  acceptance_ref: ACC-022
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证持仓异常和重大公告触发处置，且不跳过风控。
  artifact_expectation: position_disposal_report.json
- vo_id: VO-023
  acceptance_ref: ACC-023
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证全资产财务档案、非 A 股行情和估值、交易隔离。
  artifact_expectation: finance_asset_boundary_report.json
- vo_id: VO-024
  acceptance_ref: ACC-024
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证自动日度归因和评价维度。
  artifact_expectation: performance_attribution_report.json
- vo_id: VO-025
  acceptance_ref: ACC-025
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 CFO 解释、治理提案、财务规划子类型、反思分派和高影响审批。
  artifact_expectation: cfo_governance_report.json
- vo_id: VO-026
  acceptance_ref: ACC-026
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证新增因子准入、独立验证、登记、监控和无回测验收。
  artifact_expectation: factor_research_report.json
- vo_id: VO-027
  acceptance_ref: ACC-027
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证研究员简报、资料包、议题、知识、Prompt 和 SkillPackage 提案链，以及低/中影响自动验证、高影响 Owner 审批和新任务生效。
  artifact_expectation: researcher_workflow_report.json
- vo_id: VO-028
  acceptance_ref: ACC-028
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证反思闭环责任、晋升提案、低/中影响自动验证、高影响审批和不直接热改参数/Prompt/Skill/在途上下文。
  artifact_expectation: reflection_learning_report.json
- vo_id: VO-029
  acceptance_ref: ACC-029
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证 DevOps 异常处理、降级恢复和向 Risk 汇报。
  artifact_expectation: devops_incident_report.json
- vo_id: VO-030
  acceptance_ref: ACC-030
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证低/中影响自动 triage/验证/版本快照/审计，高影响配置/Prompt/Skill/默认上下文提案、对比分析、Owner 审批、新任务生效和在途 ContextSnapshot/配置快照。
  artifact_expectation: config_governance_report.json
- vo_id: VO-031
  acceptance_ref: ACC-031
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证财务档案加密、日志脱敏、敏感原始字段读取例外、runner 无业务写凭证、只读 DB 账号、Authority Gateway 写入和单 Owner 安全声明。
  artifact_expectation: security_privacy_report.json
- vo_id: VO-032
  acceptance_ref: ACC-032
  verification_type: automated
  verification_profile: full
  obligations:
    - 验证主文档自足、appendix 无正式 ID 定义、Design/Implementation 附件读取规则、testing 有 TC 覆盖。
  artifact_expectation: requirement_structure_report.json

<!-- CODESPEC:SPEC:CONSTRAINTS -->
## 5. 运行约束

- execution_scope: V1 只允许纸面执行，不允许任何真实券商 API、真实订单、真实账户同步、真实资金自动动作。
- interface_scope: V1 只做 Web 桌面工作台；不做飞书、邮件、短信、移动端。
- asset_scope: 正式投资闭环只覆盖 A 股普通股；非 A 股资产只用于财务规划、估值、风险提示或 `manual_todo`。
- concurrency_limits:
  - formal_ic_max_concurrent: 3
  - global_workflow_max_concurrent: 5
- data_quality_policy:
  - decision_core_normal: `quality_score >= 0.9`
  - decision_core_degraded: `0.7 <= quality_score < 0.9`
  - decision_core_blocked_after_fallback: `quality_score < 0.7` 且自动切源/fallback 后仍不可恢复。
  - execution_core_blocked: 低于当前 workflow 配置快照中的生效阈值，默认 `0.9`。
- data_governance_policy: 正式数据访问必须声明 `data_domain`、`required_usage`、`freshness_requirement` 和 `required_fields`；单请求综合质量分用于诊断，`decision_core` 与 `execution_core` 放行必须按关键请求/关键字段最低有效分、freshness 和冲突等级聚合；缓存可用于展示和研究背景，但不得支持新的纸面执行；多源关键冲突必须生成 Data Conflict Report，并按字段重要性降级或阻断；影响 `decision_core` 或 `execution_core` 的源优先级、阈值或 fallback 变更属于高影响治理且只对新任务生效。
- execution_core_policy: `execution_core` 使用当前 workflow 配置快照中的生效阈值，默认 `0.9`；低于生效阈值时严格阻断纸面执行，Owner 不能例外批准使用降级执行数据成交。
- owner_approval_required: 仅 Risk `conditional_pass`、CIO 重大偏离组合优化建议、高影响治理变更、高影响 Prompt 或知识晋升、高风险财务规划或风险预算变更进入 Owner 审批中心。
- owner_notification_only: Risk `approved` 的正常 IC 结论、Daily Brief、Research Package、普通归因报告、低/中影响治理建议、无需高影响配置变更的系统恢复结果、纸面订单正常成交/未成交/过期只通知 Owner，不默认审批。
- owner_approval_policy: 凡需 Owner 审批，必须同时附详细对比分析、影响范围、替代方案和明确建议；confirmation、approval 和 `manual_todo` 必须分离；审批默认超时策略由附件展开，Design 可配置但不得改变超时无效果原则。
- owner_timeout_policy: Owner 超时必须记录 `owner_timeout`；Request Brief confirmation 超时为草稿过期且不创建 workflow；Risk `conditional_pass` 或 S6 投资例外超时为不执行并使 S6 blocked；CIO 重大偏离审批超时为不执行并重开 S4 或关闭；高影响治理、Prompt/知识晋升、财务风险预算/规划审批超时为不生效并进入 `expired`；`manual_todo` 超时只标记 `expired`，不得触发审批或执行。
- risk_policy: Risk `rejected` 不可被 CIO 或 Owner 绕过；`conditional_pass` 才允许 Owner 例外审批；Risk Officer 必须在 `rejected` 报告中判定 `repairable / unrepairable`，可修复时给出 `reopen_target` 与 reason code，不可修复时终止当前 attempt。
- memory_policy: Agent 采用组织透明读和网关受控写；正式 Agent 可读取业务文件、只读数据库视图、历史 artifact、过程档案、组织记忆和共享知识，但不得直接写业务数据库。所有持久化写入必须通过 Authority Gateway 形成 typed command、artifact、event、comment、proposal 或诊断记录，并按 owner_agent/producer append-only 版本化。
- finance_sensitive_policy: 财务敏感原始字段是组织透明读例外；收入、负债、家庭、重大支出、税务明细等仅 CFO 与财务服务可明文使用，其他 Agent 只读脱敏约束摘要、风险预算、流动性边界和派生 artifact。
- security_policy: 单 Owner 假设下财务档案加密存储、普通日志脱敏；V1 不要求多用户 RBAC，但必须区分 runner 无业务写凭证、只读 DB 账号、Authority Gateway 写入和敏感字段解密边界。

<!-- CODESPEC:SPEC:CONTRACTS -->
## 6. 业务契约

- artifact_contract: 所有正式阶段产物必须包含 `artifact_id`、`trace_id`、`producer`、`source_refs`、`created_at`、`status`、`summary`、`evidence_refs`、`decision_refs`。
- artifact_registry_contract: S0-S7 核心 artifact 为 Request Brief、Data Readiness Report、Analyst Memo、Debate Summary、CIO Decision Memo、Risk Review Report、Approval Record、Paper Execution Receipt、Attribution Report、Reflection Record；IC Context Package、IC Chair Brief、Decision Packet、Decision Guard Result、Decision Exception Candidate、Market State、Daily Brief、Research Package、Topic Proposal、Knowledge/Prompt/Skill Proposal、Agent Capability Change Draft、Governance Proposal、Incident/Degradation/Recovery 产物为支撑 artifact，由所属 REQ/ACC/TC 覆盖。
- collaboration_contract: 正式协作必须通过 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent 和 HandoffPacket 表达。CollaborationSession 只保留粗粒度运行标签 `open / active / waiting / synthesizing / closed / failed / canceled / expired`，不承载低共识、Risk rejected、Owner timeout 等业务判断；业务判断必须写入 workflow state、artifact、reason code 或 Reopen Event。
- collaboration_command_contract: V1 CollaborationCommand 为封闭集合：`ask_question / request_view_update / request_peer_review / request_agent_run / request_data / request_evidence / request_service_recompute / request_source_health_check / request_reopen / request_pause_or_hold / request_resume / request_owner_input / request_manual_todo / request_reflection / propose_knowledge_promotion / propose_prompt_update / propose_skill_update / propose_config_change / report_incident / request_degradation / request_recovery_validation / request_risk_impact_review`。新增命令类型属于治理变更，不允许 Agent 临时发明。
- agent_run_contract: AgentRun 必须绑定 `agent_id`、`profile_version`、`workflow_id`、`stage`、`attempt_no`、`run_goal`、`ContextSnapshot/ContextSlice`、工具权限、SkillPackage 版本、预算/超时、输出 artifact schema 和允许提交的 CollaborationCommand 类型；AgentRun 创建必须经过模板自动准入、semantic lead 接收、domain accept 或 Owner approval 之一，不允许 runner 直接写业务状态。
- request_contract: 任一可触发 workflow 的输入必须标准化为 Request Brief，含目标、范围、优先级、授权边界、时间预算、成功标准和阻断条件。
- approval_contract: Approval Record 必须记录审批对象、审批原因、审批类型、对比方案、推荐结论、审批人、时间、决定、影响范围、生效边界、默认超时和超时无效果处置。
- manual_todo_contract: `manual_todo` 必须记录人工动作、原因、建议、到期时间和风险提示；不得连接 S5/S6 投资审批或执行。
- memo_contract: Analyst Memo 使用通用外壳 + role-specific payload。通用外壳至少包含 `memo_id`、`workflow_id`、`attempt_no`、`analyst_id`、`role`、`context_snapshot_id`、`decision_question`、`direction_score`、`confidence`、`evidence_quality`、`hard_dissent`、`hard_dissent_reason`、`thesis`、`supporting_evidence_refs`、`counter_evidence_refs`、`key_risks`、`applicable_conditions`、`invalidation_conditions`、`suggested_action_implication`、`data_quality_notes`、`needs_reopen_or_escalation`、`collaboration_command_refs`；`evidence_quality` 为 0..1 评分，表示证据引用完整性、来源可靠性和反证覆盖质量；`hard_dissent` 为可机读布尔值，按 hard_dissent_contract 判定。
- analyst_role_payload_contract: Macro payload 覆盖 `engine_market_state`、`analyst_market_state_view`、`market_state_conflict`、`policy_stance`、`liquidity_condition`、`credit_cycle`、`industry_policy_alignment`、`style_bias`、`macro_tailwinds`、`macro_headwinds`、`transmission_path`、`macro_risk_triggers`；Fundamental payload 覆盖 `business_model_quality_score`、`moat_assessment`、`financial_quality`、`earnings_scenarios`、`valuation_methods_used`、`fair_value_range`、`valuation_percentile`、`safety_margin`、`sensitivity_factors`、`accounting_red_flags`、`key_kpi_watchlist`、`fundamental_catalysts`、`valuation_conclusion`；Quant payload 覆盖 `signal_hypothesis`、`trend_state`、`momentum_score`、`volume_price_confirmation`、`factor_exposures`、`factor_signal_scores`、`sample_context`、`signal_stability_score`、`regime_fit`、`timing_implication`、`overheat_or_crowding_risk`、`invalidating_price_or_signal_levels`；Event payload 覆盖 `event_type`、`event_timeline`、`source_reliability`、`verification_status`、`catalyst_strength_score`、`time_window_assessment`、`affected_fundamental_assumptions`、`sentiment_and_fund_flow`、`historical_analogues`、`reversal_risk`、`supporting_evidence_only`。`rumor_only` 或 `supporting_evidence_only` 不得作为 decision_core 单独推进。
- consensus_contract: `direction_sign` 按 `direction_score > 0`、`= 0`、`< 0` 分为 positive、neutral、negative；`dominant_direction_share = count(最多 direction_sign) / total_analysts`；`std(direction_score/5)` 使用四位分析师归一化方向分的总体标准差。
- hard_dissent_contract: 若某 analyst 的 `direction_sign` 与多数非 neutral 方向相反，且 `abs(direction_score) >= 4` 或 `confidence >= 0.7`，则 `hard_dissent = true`；若不存在多数非 neutral 方向，则按低共识/辩论规则处理，不自动生成 hard dissent。
- consensus_action_gate_contract: `consensus >=0.8`、无 hard dissent 且 `action_conviction >=0.65` 时才可跳过 S3；`0.7 <= consensus <0.8` 必须进入 S3；`consensus <0.7` 或 `action_conviction <0.65` 不得进入纸面执行授权，S4 只能形成 `observe / no_action / reopen` 或补证建议。
- debate_contract: S3 辩论采用 CIO 语义主席 + Workflow/Debate Manager 过程权威；四位分析师参与，最多 2 轮。每轮只能引用 IC Context Package、IC Chair Brief、既有 Memo 或补充 evidence_refs；Debate Summary 为联合产物，过程字段由 Debate Manager 生成，必须记录参与者、争议点、补证、观点变化、重算后的 consensus/action_conviction、`hard_dissent_present`、`retained_hard_dissent`、`risk_review_required`、是否进入 S4、Risk Review 或阻断；中等共识辩论后保留 hard dissent 时 `risk_review_required` 必须为 true；CIO 语义字段必须记录 `agenda`、`questions_asked`、`synthesis`、`resolved_issues`、`unresolved_dissent` 和 `chair_recommendation_for_next_stage`。
- risk_review_contract: Risk Review Report 必须记录 `review_result`、`repairability`、`reopen_target_if_any`、reason codes、hard blockers、conditional requirements、data quality、portfolio risk、liquidity/execution、CIO deviation 和 hard dissent assessment；`repairability` 仅在 `rejected` 时用于判定是否允许 Reopen Event。
- deviation_contract: 单股偏离为 `abs(CIO目标权重 - 优化器建议权重)`；组合主动偏离为 `0.5 * Σ|CIO目标权重 - 优化器建议权重|`；超过阈值后由编排中心生成 Owner 例外审批或重开论证任务，CIO 不自行裁决。
- cfo_governance_contract: CFO 的 Governance Proposal 必须标明影响等级；财务规划建议归入 Governance Proposal 的财务规划/风险预算子类型；高影响默认包括因子权重、风险预算、规则、Prompt、Skill、默认上下文、审批规则和执行参数。
- prompt_skill_contract: Prompt、SkillPackage、默认上下文和共享知识更新必须以 diff/proposal 形式提交，包含影响等级、验证结果、适用范围、回滚计划和只对新任务/新 attempt 生效的边界；低/中影响可自动验证后生效，高影响必须 Owner 批准。
- config_snapshot_contract: 每个在途 workflow 和 AgentRun 必须绑定阈值、风控参数、审批规则、Prompt、SkillPackage、默认上下文、模型路由、工具权限、服务降级策略和执行参数的 ContextSnapshot/配置快照；批准或自动生效后的变更只对新任务或新 attempt 生效。
- paper_execution_contract: 纸面执行回执必须包含订单意图、执行窗口、行情引用、成交/未成交状态、成交价、成交量、费用、税费、滑点、T+1 状态和归因引用。
- attribution_contract: 自动归因必须区分市场结果、决策质量、执行质量、数据质量、证据/反证质量、条件命中与可改进项。
- task_envelope_contract: 所有任务必须至少包含 `task_id`、`task_type`、`priority`、`owner_role`、`current_state`、`blocked_reason`、`reason_code`、`artifact_refs`、`created_at`、`updated_at`、`closed_at`；轻量任务使用通用生命周期，领域进展用 artifact 或 milestone 表达。
- workflow_stage_contract: 投资主链的 S0-S7 阶段节点状态仅可为 `not_started / running / waiting / blocked / completed / skipped / failed`；数据降级、风险拒绝、Owner 超时、执行未成交或过期必须作为结果字段或 reason code 记录，不得新增平行主状态。
- reopen_event_contract: 重开必须记录 `reopen_event_id`、`workflow_id`、`from_stage`、`target_stage`、`reason_code`、`requested_by`、`approved_by_or_guard`、`invalidated_artifacts`、`preserved_artifacts`、`attempt_no`、`created_at`；旧产物不得删除，只能标记 `superseded`。
- governance_state_contract: 高影响治理任务必须经过 `draft -> triage -> assessment -> owner_pending -> approved -> effective`；无效果终态为 `rejected / expired / canceled / activation_failed`；Governance Impact Policy 可配置但其变更本身永远属于高影响治理。
- data_source_registry_contract: 每个数据源条目必须声明 `source_id`、`data_domain`、`asset_scope`、`allowed_usage`、`freshness_expectation`、`coverage`、`historical_depth`、`normalization_required`、`cost_type`、`rate_limit`、`priority`、`fallback_order` 和 `quality_history`；影响 `decision_core` 或 `execution_core` 的源优先级、阈值或 fallback 变更属于高影响治理。
- data_request_contract: 任一 Agent 或服务请求正式数据时必须声明 `request_id`、`trace_id`、`data_domain`、`symbol_or_scope`、`time_range`、`required_usage`、`freshness_requirement`、`required_fields`、`requesting_stage`、`requesting_agent_or_service`，不得绕过 Data Collection & Quality Service。

<!-- CODESPEC:SPEC:HANDOFF -->
## 7. 设计交接

- default_reading:
  - `spec.md`
  - `testing.md`
  - `codespec readset` 输出的 default/work_item/phase 层材料。
- appendix_reading_matrix:
  - `spec-appendices/source-normalization.md`: 来源追溯、旧输入冲突、Requirement 重开、判断正文与原始材料关系时必须读取。
  - `spec-appendices/agent-capability-matrix.md`: Agent 注册表、角色职责、prompt、工具权限、上下文包、记忆边界、产物 schema、评价机制相关任务必须读取。
  - `spec-appendices/service-and-workflow-matrix.md`: 服务层、编排中心、S0-S7、阶段产物、状态机、降级、重试、责任边界相关任务必须读取。
  - `spec-appendices/frontend-workbench-map.md`: Web 工作台、主导航、高审美浅色主题、全局命令层、任务中心、审批中心、治理下 Agent 团队工作区、Agent 能力配置草案和页面信息架构相关任务必须读取。
  - `spec-appendices/investment-ic-risk-execution.md`: A 股 IC、机会注册、硬门槛、Memo、共识/辩论、CIO、风控、Owner 例外、纸面执行相关任务必须读取。
  - `spec-appendices/finance-knowledge-reflection.md`: 财务模块、自动归因、CFO 治理、研究员、知识晋升、Prompt 提案、反思闭环相关任务必须读取。
- appendix_usage:
  - 附件是本文的重要索引和强证据展开层；命中领域时必须读取，未命中领域时不默认全量读取。
  - Design、Implementation、Testing 阶段均按 `codespec readset`、当前 WI、问题定位和 `appendix_reading_matrix` 读取附件；不能凭附件新增正式 REQ/ACC/VO。
  - 若附件内容不足、为空或与本文冲突，停止当前阶段并回到 Requirement 修补本文、`testing.md` 或对应附件。
- design_focus:
  - 将 `REQ/ACC/VO/TC` 映射为模块、接口、状态机、数据结构、页面、工作项和验证命令。
  - 细化 Agent 能力如何实现，但不得削弱能力契约或越过记忆边界。
  - 细化服务编排如何避免 CIO/CFO 成为系统瓶颈。
  - 细化 Web 信息架构、高审美浅色主题、治理下 Agent 团队工作区、Agent 能力配置治理、任务/审批中心和全局命令层。
  - 细化纸面执行、财务加密、日志脱敏、降级、恢复和可观测性。
- explicit_non_goals_for_design:
  - 不设计飞书、移动端、真实券商、回测、规则路径、策略经理、Performance Analyst Agent。
  - 不把非 A 股资产接入审批/执行/交易链。
  - 不在 Design 中新增正式需求 ID；若发现需求缺失，回到 Requirement 更新本文和 `testing.md`。
