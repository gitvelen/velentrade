# design.md

<!-- CODESPEC:DESIGN:READING -->
## 0. AI 阅读契约

- 本文件与 `design-appendices/*` 是 Design 阶段权威设计输入；`spec.md` 仍是需求权威。
- 实现阶段默认读取本文件、当前 WI、`testing.md` 中对应 `TC-*`，以及 WI 明确引用的契约和命中领域的 appendix。
- `design-appendices/*` 与本文同属 Design 权威层：本文记录架构 spine、ADR、模块边界和 WI 切片；appendix 记录可实施的领域契约。
- `contracts/*.md` 是 Design 阶段 frozen contract；Implementation 读取当前 WI 明确引用的 contract，若共享边界需要改变，先回写 Design。
- 命中 Agent 协作、能力画像、运行存储、安全、检索、SkillPackage、前端工作台、workflow/data/service、投资主链、财务知识反思或 DevOps 观测时，必须读取对应 design appendix。
- 若实现需要改变本文架构、接口、状态机、安全边界、外部交互或已批准需求，必须停止并回写 Design 或 Requirement。

| 读取触发 | 必读 appendix | 权威边界 | 冲突处理 |
|---|---|---|---|
| 命中 Agent 能力、岗位画像、SkillPackage、可读写边界或 runner 行为 | `design-appendices/agent-capability-profiles.md` | 展开 Agent 能力、工具、上下文和输出契约；不新增正式 REQ/ACC/VO | 与本文 spine、contracts 或 `spec.md` 冲突时停止并回写 Design/Requirement |
| 命中 AgentRun、协作命令、Handoff、Authority Gateway 或过程档案 | `design-appendices/agent-collaboration-protocol.md` | 展开协作机制、准入、事件、交接和受控写入；不得改变业务事实源 | 与 frozen contract 或 workflow 权威冲突时停止并修复上游 |
| 命中 PostgreSQL、Memory/Knowledge、ContextSnapshot、安全、运行存储或只读/写入权限 | `design-appendices/runtime-storage-architecture.md` | 展开存储、权限、审计和上下文生效语义；不得替代 `contracts/*.md` schema | 与安全边界或 fact_source 冲突时停止并回写 Design |
| 命中 Web 工作台、导航、页面区块、状态、trace/debug 或浏览器验证 | `design-appendices/frontend-workbench-design.md` | 展开 Owner/Agent/DevOps 可见界面与状态；不新增后端能力 | 与 read model contract 冲突时先修 `contracts/api-read-models.md` |
| 命中 S0-S7、数据服务、质量门、外部数据、市场状态、治理配置或 Celery 调度 | `design-appendices/workflow-data-service-design.md` | 展开 workflow/data/service runbook 和 guard；不改变投资裁决职责 | 与 Decision/Risk/Owner 边界冲突时停止并回写 Design |
| 命中 Decision Service、优化偏离、CIO Decision Packet、Owner exception 或重开建议 | `design-appendices/decision-service-design.md` | 展开确定性决策服务输入输出与边界；不授予服务投资裁决权 | 与 CIO/Risk/Owner 职责冲突时以本文 spine 和 contracts 为准 |
| 命中机会、Topic Queue、IC Context、Analyst Memo、辩论、Risk Review、纸面执行或持仓处置 | `design-appendices/investment-chain-design.md` | 展开 A 股投资主链 runbook、artifact 和 guard；不新增真实交易或回测 | 与 Risk rejected、execution_core 或非 A 股边界冲突时停止 |
| 命中财务档案、归因、CFO、因子研究、Researcher、Knowledge/Prompt/Skill 提案或反思 | `design-appendices/finance-knowledge-reflection-design.md` | 展开财务知识反思链路；不把 Memory/Knowledge 变成事实源 | 与治理生效、审批或敏感字段边界冲突时回写 Design |
| 命中 DevOps health、incident、降级、恢复、成本/Token 或安全日志 | `design-appendices/devops-observability-design.md` | 展开技术运维与观测 runbook；不允许 DevOps 放行业务 Risk | 与投资恢复、Risk 放行或高影响配置冲突时停止 |

<!-- CODESPEC:DESIGN:OVERVIEW -->
## 1. 设计概览

- solution_summary: V1 采用 PostgreSQL 18 作为唯一业务事实源，FastAPI/Python 模块化单体承载 domain state machine、workflow、Agent 协作、数据质量、Decision Service、纸面执行、归因和治理；Celery/Redis 处理异步任务；独立 `agent-runner` 执行受控 Agent；React 19/TypeScript Web 工作台以简体中文、漂亮优先且护眼其次的高端浅色卡面展示 Owner Decision View、Investment Dossier、Trace/Debug 和治理下 Agent 团队工作区。
- design_spine: `design.md` 保留架构决策、模块边界、接口概览、数据流、环境配置和验证映射；领域细节进入 `design-appendices/*`，共享接口与 schema 进入 `contracts/*.md`。
- fact_source: 业务事实只来自 PostgreSQL domain tables、artifact ledger、workflow state、reason code、audit/event log。Memory、Knowledge、LangGraph/CrewAI、runner transcript、长聊天和子 Agent summary 都不能成为业务事实源。
- collaboration_model: Agent 可读文件、网络、只读 DB、知识库、组织记忆和过程档案；持久化写入只能通过 Authority Gateway 的 typed command/artifact/memory API。

### R8 设计完成标准

Design 阶段必须按 `../lessons_learned.md` 的 R8 交付运行语义，而不是只交付对象清单。任何领域 appendix、contract、WI 或测试计划只有在同时覆盖以下四层时，才可视为 Implementation-ready：

| 层 | 必须回答的问题 | 典型落点 |
|---|---|---|
| Runbook | 真实场景从触发到结束怎么跑；谁在什么时候做什么；输入、输出、失败、超时、拒绝、重开、降级如何处理 | `design-appendices/*` |
| Contract | API、schema、artifact、state、error code、read model、guard 如何实现 | `contracts/*.md` |
| View | Owner、Agent、DevOps、审计者在哪个页面、Dossier 或 Trace/Debug 中看到什么 | `design-appendices/frontend-workbench-design.md`、`design-previews/frontend-workbench/`、`contracts/api-read-models.md` |
| Verification | 用哪些 TC、fixture、report、read model snapshot 或 Markdown 页面预览证明实现符合设计 | `testing.md`、`contracts/verification-report-schemas.md`、`reviews/design-review.yaml` |

冷启动判定：实现者不得依赖长对话记忆，只读 `codespec readset`、当前 WI、命中 appendix、contracts 和 `testing.md` 中的 TC，就必须能列出实现步骤、状态转换、Agent/服务动作、前端/Trace 展示、失败路径和 fixture。若只能列出对象、字段或报告名，Design 不得进入 Implementation。

### 运行主干 Spine

所有投资、财务、知识、DevOps 和治理任务复用同一运行主干；各领域只能定义自己的模板、参与者、artifact、guard 和 view projection，不得各自发明隐式流程。

```text
Request Brief
 -> TaskEnvelope
 -> workflow template selection
 -> stage guard / domain command
 -> DataRequest / ServiceResult / AgentRun admission
 -> ContextSnapshot + ContextSlice
 -> AgentRun or service execution
 -> CollaborationCommand loop when semantic coordination is needed
 -> Authority Gateway artifact/event/handoff submission
 -> HandoffPacket
 -> stage completed / waiting / blocked / skipped / failed / reopened
 -> read model projection
 -> verification report
```

责任分工固定如下：

- Workflow 是过程权威，负责阶段、状态转换、准入、阻断、重开、超时、并发和审计。
- Service 是确定性计算与数据处理层，输出数据质量、市场状态、因子、估值、组合优化、风险、执行、归因等结果，但不做投资裁决或审批。
- Agent 是语义岗位执行者，负责解释、判断、追问、综合和签发授权范围内的 artifact，但不能直接改 workflow state。
- Artifact 是业务事实源；Memory/Knowledge 只能提供上下文、证据线索和可复用经验；Trace/Event 是过程证据；runner transcript 和长聊天不得成为正式下游事实。
- Read model 是观察层；Owner 默认看决策摘要，Dossier 看业务链路，Trace/Debug 看过程与审计。

### Design 修复状态

Design 已根据人工走查和 R8 标准完成语义修复，并由 `reviews/design-review.yaml` 记录修复后的 Design 复审结论。Design->Implementation 仍必须按 `../phase-review-policy.md` 执行 fresh machine gates，并向 Owner 显示阶段切换确认；review approved 不等于已经进入 Implementation。

修复范围固定如下：

1. 本文已补充 R8 spine、Runbook / Contract / View / Verification 完成标准和设计预览索引。
2. `design-appendices/*` 已补充 Agent、workflow/service、投资主链、DevOps、财务知识反思和前端工作台 runbook。
3. `design-previews/frontend-workbench/` 已作为正式 Design 评审产物，采用 Markdown review pack 展示路由层级、首屏排布、页面状态、禁用入口和团队页 Agent 管理视角。
4. `contracts/*.md`、`testing.md`、`work-items/*.yaml` 已同步 R8 运行语义、view projection 和验证证据。
5. contract freeze review 已按 R8 修复后重新冻结。
6. 记忆机制已按本项目高治理投资工作台特点重写：借鉴 `/home/admin/memos` 的捕获、标签、关系、筛选和整理能力，但改造为 Authority Gateway 写入、append-only 版本、ContextSnapshot 生效、财务敏感字段例外和“记忆非事实源”的运行语义。
7. 当前设计已补充老板反馈的前端重设计：一级主导航变为 `全景 / 投资 / 财务 / 知识 / 治理`，团队能力管理下沉为治理下 Agent 团队工作区；左侧导航保持紧凑，不放长副标题和审批/阻断/草案数字；默认简体中文、漂亮优先、护眼其次的高端浅色卡面，采用暖瓷底色、墨色文字、玉绿主强调、靛蓝/暗金/胭脂红辅助色；老板默认卡片不展示非 A 股边界守卫、Prompt/Skill 版本、ContextSnapshot、trace_id、read model 等过程材料；治理页通过二级模块切换进入 Agent 团队工作区，并展示九个 Agent 画像、运行质量和能力配置草案入口。
8. 当前设计已将 Decision Service 独立成确定性服务附录，明确 CIO Decision Packet、偏离守卫、Owner 例外候选和重开建议的运行手册、边界、视图和验证。

## 2. 需求追溯

完整 Requirement 索引：REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-028, REQ-029, REQ-030, REQ-031, REQ-032。

requirement_refs:
  - REQ-001
  - REQ-002
  - REQ-003
  - REQ-004
  - REQ-005
  - REQ-006
  - REQ-007
  - REQ-008
  - REQ-009
  - REQ-010
  - REQ-011
  - REQ-012
  - REQ-013
  - REQ-014
  - REQ-015
  - REQ-016
  - REQ-017
  - REQ-018
  - REQ-019
  - REQ-020
  - REQ-021
  - REQ-022
  - REQ-023
  - REQ-024
  - REQ-025
  - REQ-026
  - REQ-027
  - REQ-028
  - REQ-029
  - REQ-030
  - REQ-031
  - REQ-032

| 需求 | 设计响应 | 详细契约 | WI / TC |
|---|---|---|---|
| REQ-001/002 | Scope registry、Agent/Service registry、禁用能力扫描 | `runtime-storage-architecture.md`、`agent-capability-profiles.md`、`verification-report-schemas.md` | WI-001 / TC-ACC-001-01, TC-ACC-002-01 |
| REQ-003/004/005 | Agent profile、团队页画像、组织透明读、Memory/Knowledge 分层、Authority Gateway、workflow-native collaboration | `agent-capability-profiles.md`、`agent-collaboration-protocol.md`、`frontend-workbench-design.md`、`runtime-storage-architecture.md`、`domain-artifact-schemas.md` | WI-001 / TC-ACC-003-01..005-01 |
| REQ-006/007 | Web 主导航、高审美浅色主题、治理下 Agent 团队工作区、能力配置草案治理、全局命令、三层视图、任务/审批/manual_todo 分离 | `frontend-workbench-design.md`、`api-read-models.md` | WI-004 / TC-ACC-006-01, TC-ACC-007-01 |
| REQ-008/009/010/011/030 | S0-S7、Data Request、质量门、服务边界、Market State、Decision Service 编排、治理快照 | `workflow-data-service-design.md`、`decision-service-design.md`、`domain-artifact-schemas.md`、`verification-report-schemas.md` | WI-002 / TC-ACC-008-01..011-01, TC-ACC-030-01 |
| REQ-012/013/014 | Opportunity、Topic Queue、IC Context、IC Chair Brief | `investment-chain-design.md`、`domain-artifact-schemas.md` | WI-003 + WI-010 repair / TC-ACC-012-01..014-01 |
| REQ-015/016/017 | Analyst Memo、共识/行动强度、辩论与 hard dissent | `investment-chain-design.md`、`agent-capability-profiles.md`、`agent-collaboration-protocol.md` | WI-007 / TC-ACC-015-01..017-01 |
| REQ-018/019 | Decision Service、CIO Decision Packet、优化器偏离、Risk、Owner 例外 | `decision-service-design.md`、`investment-chain-design.md`、`domain-artifact-schemas.md`、`api-read-models.md` | WI-008 / TC-ACC-018-01..019-01 |
| REQ-020/021/022 | 纸面账户、纸面执行、持仓监控与处置 | `investment-chain-design.md`、`domain-artifact-schemas.md`、`api-read-models.md` | WI-009 + WI-010 repair / TC-ACC-020-01..022-01 |
| REQ-023/024/025/026/027/028 | 财务、归因、CFO 治理、因子研究、Researcher、知识/Prompt/Skill、反思 | `finance-knowledge-reflection-design.md`、`agent-capability-profiles.md`、`domain-artifact-schemas.md` | WI-005 / TC-ACC-023-01..028-01 |
| REQ-029 | DevOps incident、health、degradation、recovery、Risk notification、成本/Token 观测 | `devops-observability-design.md`、`agent-capability-profiles.md`、`domain-artifact-schemas.md` | WI-006 / TC-ACC-029-01 |
| REQ-031 | 财务加密、日志脱敏、runner 无写凭证、只读 DB、敏感字段解密边界 | `runtime-storage-architecture.md`、`agent-capability-profiles.md`、`devops-observability-design.md` | WI-001 / TC-ACC-031-01 |
| REQ-032 | Appendix 分层、contract refs 和追溯 | 本文阅读契约、`verification-report-schemas.md` | WI-001 / TC-ACC-032-01 |

### 技术栈选择

| 层 | V1 选择 |
|---|---|
| 后端 | Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、psycopg 3 |
| 数据库 | PostgreSQL 18，含 full-text 与 pgvector |
| 异步 | Celery worker/beat + Redis broker/cache |
| 前端 | React 19、TypeScript、Vite、pnpm、React Router library mode、TanStack Query、Tailwind、Radix、ECharts、React Flow |
| Agent | 自有 ModelGateway + LangChain ChatModel adapters；独立 `agent-runner` 服务 |
| 可观测 | structlog JSON、OpenTelemetry、Prometheus、PostgreSQL audit/trace facts |
| 测试 | pytest、Testcontainers(Postgres/Redis)、Alembic、Celery integration、fake LLM、Vitest、Playwright |

明确不用：

- 不用 MySQL。
- 不用 SQLite 作为应用持久化或测试替代。
- V1 不接 Milvus；pgvector/full-text 是知识检索实现。
- V1 不使用 LiteLLM proxy 或 ccswitch runtime；只借鉴 provider profile、health、discovery、quota/cost 等概念。

## 3. 架构决策

- decision_id: ADR-001
  decision: 使用 FastAPI + React 的模块化单体，而不是微服务或纯前端原型。
  rationale: V1 是单 Owner 高治理系统，核心复杂度在状态机、数据质量、协作和审计；模块化单体更容易保持事务一致性、自动化测试和单节点部署。
  consequences: 必须用 package boundary、schema contract 和 lint/test 防止 domain 之间隐式耦合。

- decision_id: ADR-002
  decision: PostgreSQL 18 是唯一业务事实源；不使用 MySQL/SQLite。
  rationale: V1 需要事务、审计、全文检索、向量检索、JSONB、并发控制和 Testcontainers 一致性；SQLite 会掩盖迁移、并发和查询问题，MySQL 在 pgvector/full-text 一体化上不如 PostgreSQL 贴合。
  consequences: 本地、测试、CI 都使用 PostgreSQL；Alembic migration 是启动和验证必经路径。

- decision_id: ADR-003
  decision: V1 知识检索采用 PostgreSQL full-text + pgvector，不引入 Milvus。
  rationale: 知识库、过程档案、研究资料和反思均需与权限、artifact lineage、ContextSnapshot 和审计共处同一事实源；Milvus 作为独立向量库会增加一致性和运维成本。
  consequences: 未来可增加 Milvus 作为可重建索引，但不能成为权威存储。

- decision_id: ADR-004
  decision: 自有 deterministic domain state machine 控制 S0-S7、Risk rejected、Owner timeout、Reopen Event、配置快照和治理状态机。
  rationale: 这些是强治理状态，不能交给 LangGraph/CrewAI 这类 Agent runtime 隐式决定。
  consequences: LangGraph 只可作为受控 Agent node 内部实现细节；workflow transition 只能由 domain command handlers 写入。

- decision_id: ADR-005
  decision: Agent 协作采用 workflow-native collaboration。
  rationale: 多 Agent 必须可审计、可恢复、可测，不能依赖自由聊天抽取事实。
  consequences: 引入 CollaborationSession、AgentRun、CollaborationCommand、CollaborationEvent、HandoffPacket；所有写入经 Authority Gateway。

- decision_id: ADR-006
  decision: IC 采用 CIO 语义主席 + Debate Manager 过程权威。
  rationale: 仅靠中介路由缺少投委会语义组织能力；让 CIO 全管又会破坏状态机和风控边界。
  consequences: CIO 生成 IC Chair Brief、S3 agenda/synthesis、S4 Decision Memo；Debate Manager 控制轮次、超时、公式、状态和过程字段。

- decision_id: ADR-007
  decision: 四位 Analyst 使用独立 CapabilityProfile、SkillPackage、rubric、权限默认域和 role_payload。
  rationale: “独立”是岗位能力和责任独立，不是业务读隔离；共享模板换 role 参数不能支撑投研分工。
  consequences: Macro/Fundamental/Quant/Event 共享 Memo 外壳，但各自有 role_payload、技能库和评价指标。

- decision_id: ADR-008
  decision: Agent 组织透明读、网关受控写；财务敏感原始字段例外。
  rationale: Agent 需要读取业务资料、过程档案和组织记忆才能胜任岗位；写入和隐私风险通过 Authority Gateway、append-only、ContextSnapshot 和敏感字段例外控制。
  consequences: runner 无业务写凭证；CFO/财务服务可解密原始财务字段，其他 Agent 只读脱敏摘要和派生 artifact。

- decision_id: ADR-009
  decision: Prompt、Skill、知识、默认上下文和配置按低/中影响自动验证生效，高影响 Owner 审批。
  rationale: 所有变更都让 Owner 审批会违背少量高质量原则；但高影响变更必须可审计、可回滚、只对新任务生效。
  consequences: Governance Impact Policy、ContextSnapshot、version registry 和 rollback refs 是核心实现。

- decision_id: ADR-010
  decision: Docker Compose 单节点部署，包含 postgres、redis、api、worker、beat、agent-runner。
  rationale: 单 Owner V1 不需要 Kubernetes 或多服务治理；Compose 足够覆盖真实依赖和可复核部署。
  consequences: api/worker 启动前必须执行 Alembic migration；FastAPI 服务 `/api` 和 built frontend static；Compose runtime 必须使用项目 Dockerfile、预构建镜像或本地 wheelhouse 预装 Python 依赖，禁止在 api/worker/beat/agent-runner 容器启动命令中临时 `pip install -e .`。

### 共享契约

| Contract | 用途 | 主要消费者 |
|---|---|---|
| `contracts/api-read-models.md` | REST endpoint、request/response DTO、分页、错误响应、Authority Gateway typed write API、前端 read model、禁用入口响应 | API、frontend、E2E |
| `contracts/domain-artifact-schemas.md` | Artifact envelope、Task/Workflow/Reopen/Data/Investment/Finance/DevOps、ContextSnapshot、GovernanceChange schema、stage guard 错误码 | domain、services、tests |
| `contracts/verification-report-schemas.md` | 32 个 P0 report JSON 的 envelope、report-specific payload、WI/TC/fixture 映射和 pass/fail 规则 | tests、review、Testing 阶段 |

## 4. 系统结构

| package | 实现路径 | 职责 |
|---|---|---|
| `core` | `src/velentrade/core/**` | settings、logging、auth/session、security、encryption、common errors |
| `domain.workflow` | `src/velentrade/domain/workflow/**` | Task Envelope、S0-S7、incident state machine、Reopen Event |
| `domain.governance` | `src/velentrade/domain/governance/**` | governance state machine、GovernanceChange、ContextSnapshot activation |
| `domain.artifacts` | `src/velentrade/domain/artifacts/**` | artifact ledger、version、relations、schema validation |
| `domain.collaboration` | `src/velentrade/domain/collaboration/**` | CollaborationSession、AgentRun、Command、Event、Handoff、Authority Gateway |
| `domain.agents` | `src/velentrade/domain/agents/**` | Agent registry、CapabilityProfile、SkillPackage registry、ContextSnapshot |
| `domain.memory` | `src/velentrade/domain/memory/**` | MemoryItem、MemoryVersion、MemoryRelation、MemoryCollection、MemoryExtractionResult、KnowledgeItem 基础 schema、DefaultContextBinding、ContextSlice injection evidence |
| `domain.data` | `src/velentrade/domain/data/**` | Data Domain/Source registry、Data Request、quality、lineage、conflict |
| `domain.services` | `src/velentrade/domain/services/**` | Market State、Factor、Valuation、Portfolio Optimization、Risk、execution、attribution 等确定性服务 I/O 与编排边界 |
| `domain.decision` | `src/velentrade/domain/decision/**` | DecisionPacket 装配、S4 输入校验、优化器偏离守卫、Owner 例外候选、重开建议 |
| `domain.investment` | `src/velentrade/domain/investment/**` | opportunity、topic queue、IC context、memo、consensus、debate、CIO、Risk、paper account/execution |
| `domain.finance` | `src/velentrade/domain/finance/**` | finance profile、sensitive field encryption, planning summary |
| `domain.attribution` | `src/velentrade/domain/attribution/**` | performance attribution、quality scoring、CFO interpretation trigger inputs |
| `domain.knowledge` | `src/velentrade/domain/knowledge/**` | full-text/pgvector retrieval、知识晋升、Prompt/Skill proposal、reflection workflow、process archive 查询投影 |
| `domain.devops` | `src/velentrade/domain/devops/**` | incident、health、recovery、cost/token observability |
| `domain.observability` | `src/velentrade/domain/observability/**` | OpenTelemetry/Prometheus/audit facts、runner/service health metrics |
| `model_gateway` | `src/velentrade/model_gateway/**` | provider profile、fake_test profile、模型调用路由和成本/限流边界 |
| `agent_runner` | `src/velentrade/agent_runner/**` | 独立 runner 服务入口、受限工具执行、AgentRun 输入输出适配 |
| `api` | `src/velentrade/api/**` | FastAPI routers、DTO、error mapping |
| `worker` | `src/velentrade/worker/**` | Celery tasks, outbox dispatcher, scheduled jobs |
| `frontend` | `frontend/**` | React workbench |

### 数据流

### 6.1 A 股 IC 主链

```text
Owner/trigger
 -> Request Brief
 -> Topic Queue hard gates
 -> S1 Data Request / Data Readiness
 -> IC Context Package + CIO Chair Brief
 -> S2 four Analyst AgentRuns
 -> Analyst Memos with role_payload
 -> Consensus/action_conviction
 -> S3 Debate skipped or CollaborationSession
 -> Debate Summary (process fields + CIO synthesis)
 -> S4 CIO Decision Memo
 -> S5 Risk Review
 -> S6 Owner exception if required / Paper Execution
 -> S7 Attribution / Reflection / Knowledge-Prompt-Skill proposals
```

### 6.2 Agent 写入

```text
Agent Runner
 -> Authority Gateway API
 -> schema + permission + stage + ContextSnapshot validation
 -> PostgreSQL append-only write
 -> audit_event + outbox_event
 -> UI/API read models
```

### 6.3 Context 生效

```text
Governance proposal
 -> impact triage
 -> auto validation OR Owner approval
 -> version snapshot
 -> effective for new task/new attempt
 -> in-flight AgentRun keeps old ContextSlice
```

## 5. 契约设计

API 使用 REST + JSON，内部 domain command handlers 控制写入。完整 DTO、read model、错误响应和禁用入口响应见 `contracts/api-read-models.md`；本节只列接口面。

data_contracts:

- API/read model、错误响应、分页和禁用入口响应以 `contracts/api-read-models.md` 为准；前端只消费 read model，不直接推进 workflow、approval、governance 或 execution 状态。
- domain artifact、TaskEnvelope、Workflow、DataReadiness、ContextSnapshot、GovernanceChange、Memory/Knowledge 和 stage guard schema 以 `contracts/domain-artifact-schemas.md` 为准。
- 验证报告 envelope、report payload、WI/TC/fixture 映射和 pass/fail 规则以 `contracts/verification-report-schemas.md` 为准。
- 本节只声明 contract/data/storage 边界，不新增 frozen contract 字段；若实现发现字段不足，必须先回写 Design/contract freeze，而不是在 WI 内隐式扩展。

storage:

- PostgreSQL 18 是唯一业务事实源，承载 domain tables、workflow state、artifact ledger、Memory/Knowledge append-only 版本、governance change、audit/event log、session 和 outbox。
- Redis 只作为 Celery broker/cache，不保存业务事实；任何可审计事实必须落入 PostgreSQL 或 artifact/event ledger。
- Artifact、MemoryVersion、MemoryRelation、CollaborationEvent、HandoffPacket 和 Reopen Event 均 append-only；旧 artifact 只能 superseded，不删除、不覆盖。
- Read model 是观察层，可由 PostgreSQL 事实投影生成；Owner 默认视图只展示业务摘要，Trace/Debug 才展示过程审计材料。
- Alembic migration 是 schema 变更唯一入口；本地、测试和 CI 使用 PostgreSQL/Testcontainers，禁止用 SQLite 代替。

external_interactions:

- 浏览器只访问 FastAPI `/api` 和静态前端资源。
- 外部行情、公告、新闻和宏观数据只通过 Data Collection & Quality Service adapter 访问。
- 模型调用只通过 ModelGateway，不在业务代码中直连供应商 SDK。
- Agent runner 对业务状态的所有写入只通过 Authority Gateway。

| Endpoint | 用途 |
|---|---|
| `POST /api/requests/briefs` | 自由对话或页面动作生成 Request Brief |
| `POST /api/workflows/{id}/commands` | workflow command，例如 confirm、cancel、reopen |
| `GET /api/workflows/{id}` | workflow stage、attempt、artifact summary |
| `GET /api/workflows/{id}/dossier` | Investment Dossier 聚合视图 |
| `POST /api/collaboration/commands` | 提交 CollaborationCommand |
| `POST /api/gateway/artifacts` | 内部 runner/service 通过 Authority Gateway append-only 写 artifact |
| `POST /api/gateway/events` | 内部 runner/service 通过 Authority Gateway 写 collaboration/audit event |
| `POST /api/gateway/handoffs` | 内部 runner/service 通过 Authority Gateway 写 HandoffPacket |
| `POST /api/gateway/memory-items` | 内部 runner/service 通过 Authority Gateway 写 MemoryItem/Version/Relation，不写业务事实 |
| `GET /api/workflows/{id}/agent-runs` | AgentRun 列表和状态 |
| `GET /api/workflows/{id}/collaboration-events` | Trace/Debug 协作事件 |
| `GET /api/artifacts/{id}` | 产物详情 |
| `GET /api/approvals` | Owner 审批中心 |
| `POST /api/approvals/{id}/decision` | Owner 审批动作 |
| `GET /api/tasks` | 任务中心聚合视图 |
| `GET /api/finance/overview` | 财务页聚合视图 |
| `POST /api/finance/assets` | 财务资产受控写入 |
| `GET /api/knowledge/search` | 知识/过程档案检索 |
| `GET /api/team` | 治理下 Agent 团队工作区九个 Agent 画像与健康聚合 |
| `GET /api/team/{agentId}` | 单个 Agent 画像、能力、版本、运行质量 |
| `GET /api/team/{agentId}/capability-config` | Agent 能力配置草案表单 read model |
| `POST /api/team/{agentId}/capability-drafts` | 提交 Agent 能力配置草案，仅创建 Governance Change |
| `GET /api/governance/changes` | 治理变更列表 |
| `GET /api/devops/health` | 数据、服务、runner 和执行环境健康 |

错误码分类：

- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `STAGE_GUARD_FAILED`
- `COMMAND_NOT_ALLOWED`
- `SENSITIVE_DATA_RESTRICTED`
- `DIRECT_WRITE_DENIED`
- `SNAPSHOT_MISMATCH`
- `CONFLICT`
- `SERVICE_UNAVAILABLE`

### 前端设计

前端详细设计见 `design-appendices/frontend-workbench-design.md` 和 `contracts/api-read-models.md`。前端默认采用简体中文、漂亮优先且护眼其次的高端浅色卡面，一级主导航为 `全景 / 投资 / 财务 / 知识 / 治理`，Agent 团队位于治理下并通过治理页二级模块切换进入，并保持三层：

- Owner Decision View：今天要不要处理、到哪一步、谁支持反对、风险和例外、数据是否可信。
- Investment Dossier View：S0-S7、CIO Chair Brief、四 Analyst Memo/role_payload、Stance Matrix、Debate Timeline、Handoff、Risk、Execution、Attribution。
- Trace/Debug View：AgentRun 树、ContextSlice、Command/Event、tool calls、service calls、data routing、latency/token/cost。
- Team View：九个正式 Agent 的画像、职责、版本、工具/Skill/Prompt/ContextSnapshot、近期产物质量、失败/越权记录和能力配置草案入口。

禁止：

- 用长聊天替代 Memo、Debate Summary 或 Decision Memo。
- Risk rejected 页面出现 Owner 覆盖按钮。
- 非 A 股资产出现审批/执行/交易入口。
- execution_core 不达标时不显示继续成交入口。
- 团队页直接热改在途 AgentRun、Prompt、SkillPackage、工具权限或 workflow state。

## 6. 横切设计

security_design:

- Argon2id password login。
- PostgreSQL session store。
- HttpOnly、SameSite=Strict cookie。
- 应用层加密财务敏感字段。
- 普通日志、错误日志、LLM trace 默认脱敏。
- Raw process transcript 若保存，进入加密/受限 process archive。
- Agent runner 无业务 DB 写凭证。
- 只读 DB 视图对非 CFO Agent 隐藏财务敏感原始字段。

reliability_design:

- 所有 workflow transition 通过 domain command handler，失败时返回 reason code，不做半写入。
- Celery 任务通过 outbox 驱动，失败可重试；重复消息由 idempotency key 和 PostgreSQL 唯一约束处理。
- Data Request 支持切源、fallback、Data Conflict Report 和 degraded 标记；execution_core 低于阈值严格阻断。
- AgentRun timeout、schema validation failed、command rejected、service_unavailable 都写 CollaborationEvent，并按 stage guard 决定 retry、blocked 或 reopen。
- Reopen Event 是唯一重开机制；旧 artifact 只标记 superseded，不删除。

environment_config:

| env | 用途 |
|---|---|
| `VELENTRADE_DATABASE_URL` | PostgreSQL 连接 |
| `VELENTRADE_REDIS_URL` | Redis broker/cache |
| `VELENTRADE_SECRET_KEY` | session/signing |
| `VELENTRADE_FIELD_ENCRYPTION_KEY` | 财务字段加密 |
| `VELENTRADE_MODEL_GATEWAY_CONFIG` | provider/model profile |
| `VELENTRADE_AGENT_RUNNER_URL` | runner API |
| `VELENTRADE_ENV` | dev/test/prod |
| `VELENTRADE_LOG_LEVEL` | JSON log level |

runtime_packaging:

- 本地 runtime foundation 允许 `Dockerfile`、预构建本地镜像或 `wheelhouse/` 离线依赖目录，目标是让 docker compose 启动阶段只执行 migration 和服务入口，不再依赖容器启动时访问 PyPI。
- `Dockerfile`、`.dockerignore`、`docker-compose.yml` 和 `wheelhouse/**` 由 WI-001 runtime foundation 拥有；非 WI-001 工作项不应把这些文件表述为“项目不引入 Dockerfile”的产品限制，只是在未被显式加入自身 `allowed_paths` 时不得修改。
- `Dockerfile` 必须把 Python 包、Alembic 配置、migration、脚本和已构建的 `frontend/dist` 固化进 runtime image；若使用 `wheelhouse/`，只能作为依赖安装输入，不作为业务事实源。
- `scripts/codespec-deploy` 在 `release_mode: runtime` 下必须先构建或复用 runtime image，再启动 postgres/redis/api/worker/beat/agent-runner 并执行 smoke。

### 设计附件索引

- `design-appendices/agent-collaboration-protocol.md`: CollaborationSession、AgentRun、Command、Event、Handoff、准入、IC 协作流、API 和错误处理。
- `design-appendices/agent-capability-profiles.md`: 九个正式 Agent 的 profile、权限、SkillPackage、产物和 rubric。
- `design-appendices/runtime-storage-architecture.md`: PostgreSQL 表域、Memory/Knowledge/DefaultContext 分层、Authority Gateway、runner、检索、SkillPackage、部署、可观测和测试基础设施。
- `design-appendices/frontend-workbench-design.md`: Web 路由、高审美浅色主题、治理下 Agent 团队工作区、页面区块、read model、三层可视化、禁用入口、E2E 验证。
- `design-appendices/workflow-data-service-design.md`: workflow/data/service/governance 状态机、domain command、Data Request、服务 I/O、降级和错误处理。
- `design-appendices/decision-service-design.md`: Decision Service、CIO Decision Packet、S4 输入校验、优化器偏离守卫、Owner 例外候选、重开建议、Dossier/Trace 投影。
- `design-appendices/investment-chain-design.md`: Opportunity、Topic Queue、IC Context、Memo、共识、辩论、CIO/Risk/Owner、纸面执行和持仓处置。
- `design-appendices/finance-knowledge-reflection-design.md`: 财务档案、归因评价、CFO 治理、Researcher、知识/Prompt/Skill 和反思闭环。
- `design-appendices/devops-observability-design.md`: incident、health、degradation/recovery、Risk notification、敏感日志和 observability。

### Contract 索引

- `contracts/api-read-models.md`: API/read model/错误响应/分页/Authority Gateway typed write/前端禁用入口。
- `contracts/domain-artifact-schemas.md`: domain object、artifact、Memory/Knowledge、状态、ContextSnapshot、GovernanceChange、stage guard 和跨 WI schema。
- `contracts/verification-report-schemas.md`: P0 自动化 report envelope、report payload、report 到 WI/TC/fixture 映射和 pass/fail 规则。

### Design 预览产物索引

- `design-previews/frontend-workbench/README.md`: Markdown review pack 总入口，定义五个一级主菜单、治理下 Agent 团队工作区、route canonical parent、来源入口、确认顺序和回写范围。
- `design-previews/frontend-workbench/00-shell-and-navigation.md`: 壳层、五个一级主导航、全局命令层、Attention badge、路由恢复和禁止入口。
- `design-previews/frontend-workbench/01-overview.md` 至 `06-governance.md`: 各菜单和详情页的首屏线框、字段、交互、状态和验收关联。
- `design-previews/frontend-workbench/07-states-and-guards.md`: 通用 loading/empty/error/stale/blocked 和全局禁用入口。

## 7. 工作项与验证

### 工作项派生

派生到当前 `work-items/*.yaml`：

- wi_id: WI-001
  requirement_refs: [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-031, REQ-032]
  covered_acceptance_refs: [ACC-001, ACC-002, ACC-003, ACC-004, ACC-005, ACC-031, ACC-032]
  verification_refs: [VO-001, VO-002, VO-003, VO-004, VO-005, VO-031, VO-032]
  test_case_refs: [TC-ACC-001-01, TC-ACC-002-01, TC-ACC-003-01, TC-ACC-004-01, TC-ACC-005-01, TC-ACC-031-01, TC-ACC-032-01]
  design_refs: [agent-capability-profiles, agent-collaboration-protocol, frontend-workbench-design, runtime-storage-architecture, api-read-models, domain-artifact-schemas, verification-report-schemas]
  summary: 基础 PostgreSQL/Alembic、scope registry、Agent/Service registry、Team Agent 画像 read model 基础、Agent collaboration 基础、Authority Gateway typed write、artifact ledger、agent-runner 基础执行壳、ModelGateway fake_test profile、安全/session 骨架和 Requirement 结构报告。
- wi_id: WI-002
  requirement_refs: [REQ-008, REQ-009, REQ-010, REQ-011, REQ-030]
  covered_acceptance_refs: [ACC-008, ACC-009, ACC-010, ACC-011, ACC-030]
  verification_refs: [VO-008, VO-009, VO-010, VO-011, VO-030]
  test_case_refs: [TC-ACC-008-01, TC-ACC-009-01, TC-ACC-010-01, TC-ACC-011-01, TC-ACC-030-01]
  design_refs: [workflow-data-service-design, decision-service-design, domain-artifact-schemas, verification-report-schemas]
  summary: Workflow/data/service/governance runtime，覆盖 S0-S7、数据质量算法、服务边界、市场状态、Decision Service 编排、Celery start_agent_run 调度、ContextSnapshot hash/immutability 和配置/Prompt/Skill/Agent 能力治理。
- wi_id: WI-003
  requirement_refs: [REQ-012, REQ-013, REQ-014]
  covered_acceptance_refs: [ACC-012, ACC-013, ACC-014]
  verification_refs: [VO-012, VO-013, VO-014]
  test_case_refs: [TC-ACC-012-01, TC-ACC-013-01, TC-ACC-014-01]
  design_refs: [investment-chain-design, domain-artifact-schemas, verification-report-schemas]
  summary: A 股投资准入链，覆盖机会注册、Topic Queue 加权评分/P0 抢占、IC Context Package 和 CIO IC Chair Brief。
- wi_id: WI-007
  requirement_refs: [REQ-015, REQ-016, REQ-017]
  covered_acceptance_refs: [ACC-015, ACC-016, ACC-017]
  verification_refs: [VO-015, VO-016, VO-017]
  test_case_refs: [TC-ACC-015-01, TC-ACC-016-01, TC-ACC-017-01]
  design_refs: [investment-chain-design, agent-capability-profiles, agent-collaboration-protocol, domain-artifact-schemas, api-read-models, verification-report-schemas]
  summary: IC 分析链，覆盖四 Analyst 独立 Memo、共识/行动强度计算、S3 最多两轮辩论和 hard dissent 风控交接。
- wi_id: WI-008
  requirement_refs: [REQ-018, REQ-019]
  covered_acceptance_refs: [ACC-018, ACC-019]
  verification_refs: [VO-018, VO-019]
  test_case_refs: [TC-ACC-018-01, TC-ACC-019-01]
  design_refs: [decision-service-design, investment-chain-design, agent-collaboration-protocol, domain-artifact-schemas, api-read-models, verification-report-schemas]
  summary: IC 决策链，覆盖 Decision Service、CIO Decision Packet、CIO Decision、优化器偏离、Risk Review、Owner 例外和 reopen/timeout 规则。
- wi_id: WI-009
  requirement_refs: [REQ-020, REQ-021, REQ-022]
  covered_acceptance_refs: [ACC-020, ACC-021, ACC-022]
  verification_refs: [VO-020, VO-021, VO-022]
  test_case_refs: [TC-ACC-020-01, TC-ACC-021-01, TC-ACC-022-01]
  design_refs: [investment-chain-design, domain-artifact-schemas, api-read-models, verification-report-schemas]
  summary: 纸面执行链，覆盖纸面账户、Paper Order/Execution、分钟线 VWAP/TWAP、execution_core 阻断和持仓监控处置。
- wi_id: WI-010
  requirement_refs: [REQ-014, REQ-022]
  covered_acceptance_refs: [ACC-014, ACC-022]
  verification_refs: [VO-014, VO-022]
  test_case_refs: [TC-ACC-014-01, TC-ACC-022-01]
  design_refs: [domain-artifact-schemas, api-read-models, verification-report-schemas]
  summary: Design/contract authority repair，最小补齐 ICContextPackage、ICChairBrief、PositionDisposalTask 的一等 artifact/read model/API/Gateway/PostgreSQL 持久化闭环，不新增交易、风控绕过、前端重设计或人工验收口径。
- wi_id: WI-004
  requirement_refs: [REQ-006, REQ-007]
  covered_acceptance_refs: [ACC-006, ACC-007]
  verification_refs: [VO-006, VO-007]
  test_case_refs: [TC-ACC-006-01, TC-ACC-007-01]
  design_refs: [frontend-workbench-design, api-read-models, domain-artifact-schemas, verification-report-schemas]
  summary: Web 工作台，覆盖简体中文高审美浅色主题、`全景 / 投资 / 财务 / 知识 / 治理` 一级主导航、治理下 Agent 团队工作区、全局命令层、Owner Decision View、Investment Dossier、Trace/Debug、任务中心、审批中心、能力配置草案治理和禁止入口；前端可先基于 frozen read model fixture 实现，真实后端 E2E 随各 domain WI 完成后接入。
- wi_id: WI-005
  requirement_refs: [REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-028]
  covered_acceptance_refs: [ACC-023, ACC-024, ACC-025, ACC-026, ACC-027, ACC-028]
  verification_refs: [VO-023, VO-024, VO-025, VO-026, VO-027, VO-028]
  test_case_refs: [TC-ACC-023-01, TC-ACC-024-01, TC-ACC-025-01, TC-ACC-026-01, TC-ACC-027-01, TC-ACC-028-01]
  design_refs: [finance-knowledge-reflection-design, agent-capability-profiles, api-read-models, domain-artifact-schemas, verification-report-schemas]
  summary: 财务档案、归因评价、CFO 治理、Researcher、知识/Prompt/Skill 提案和反思学习闭环；实施按 finance boundary、researcher/knowledge proposal、attribution/CFO/reflection 三个切片推进，避免全部依赖投资执行链后置。
- wi_id: WI-006
  requirement_refs: [REQ-029]
  covered_acceptance_refs: [ACC-029]
  verification_refs: [VO-029]
  test_case_refs: [TC-ACC-029-01]
  design_refs: [devops-observability-design, agent-capability-profiles, api-read-models, domain-artifact-schemas, verification-report-schemas]
  summary: DevOps incident、health、degradation、recovery、Risk notification 和成本/Token 观测。

每个 WI 必须明确 `allowed_paths`、`test_case_refs` 和 `required_verification`；若实现发现 WI 口径与本文或 `testing.md` 不一致，必须先回写 Design/WI。

### 验证策略

- 所有 P0 TC 默认自动化。
- 后端 contract/integration 使用 pytest + Testcontainers PostgreSQL/Redis。
- migration 必须执行 Alembic upgrade smoke。
- Celery 相关用真实 worker integration。
- Agent 相关用 fake LLM、fixture data 和 deterministic schema validation。
- 前端用 Vitest 做组件逻辑，Playwright 做 Owner/Dossier/Trace 关键路径。
- 禁止 live LLM、live data source 或 SQLite 替代作为 P0 pass 条件。

## 8. 实现阶段输入

runbook: 实现必须从第 1 节运行主干 Spine、当前 WI 的 `r8_runbook_scope`、命中领域的 `design-appendices/*` 和 `testing.md` 的对应 TC 冷启动；任何 S0-S7、AgentRun、Authority Gateway、Decision/Risk/Owner、纸面执行、财务知识反思或 DevOps 流程都按 appendix runbook 执行，不得用对象清单替代运行语义。

contract_summary: 共享接口和 schema 以 frozen `contracts/*.md` 为准，当前 WI 只读取其 `contract_refs`；API/read model、artifact/schema、verification report、Gateway allowlist、PostgreSQL mirror 和错误码若需要改变，必须先走 authority repair 或回写 Design，不得在实现中隐式扩大契约。

view_summary: Owner 默认看工作台摘要、Investment Dossier 和必要审批/任务状态；Agent/DevOps/审计者分别通过团队页、Trace/Debug、health/incident 和 artifact/event/handoff 视图追踪过程证据。前端实现以 `frontend-workbench-design.md`、`api-read-models.md` 和 `design-previews/frontend-workbench/` 为输入，不能把 fixture/fallback 伪装成真实完成。

verification_summary: 每个 WI 必须通过 `test_case_refs` 对应的 `TC-*`、`required_verification` 命令和 `testing.md` RUN 证据闭环；P0 默认自动化，branch-local、db_persistent、full-integration 和 owner_verified 必须按完成等级如实记录，不能用静态扫描、fixture 或 report 常量替代真实 runtime 行为。
