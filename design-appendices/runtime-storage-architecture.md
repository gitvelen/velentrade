# Runtime Storage Architecture Design

## 0. AI 阅读契约

- 本附件是 Design 阶段运行时、存储、安全、检索和可观测性的实现契约。
- 实现数据库、迁移、检索、Agent Runner、Authority Gateway、SkillPackage registry、测试基础设施或部署时必须读取本附件。
- 若本文与 `spec.md` 冲突，以 `spec.md` 为准并回到 Requirement 修补。

## 1. 技术栈

| 层 | 选择 |
|---|---|
| 后端 | Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、psycopg 3 |
| 业务数据库 | PostgreSQL 18 |
| 检索 | PostgreSQL full-text + pgvector |
| 异步任务 | Celery + Redis broker/cache |
| 前端 | React 19、TypeScript、Vite、pnpm、React Router library mode、TanStack Query、Tailwind、Radix、ECharts、React Flow |
| Agent runner | 独立 `agent-runner` 服务，受限网络/终端/文件/只读 DB，无业务写凭证 |
| 模型网关 | 自有 ModelGateway + LangChain ChatModel adapters |
| 可观测性 | structlog JSON、OpenTelemetry、Prometheus、PostgreSQL audit/trace facts |
| 测试 | pytest、Testcontainers(Postgres/Redis)、Alembic、Celery worker integration、fake LLM、Vitest、Playwright |

V1 不使用 MySQL、SQLite 作为应用持久化或测试替代；SQLite 只可作为第三方工具内部实现细节，不进入系统业务状态。

## 2. PostgreSQL 表域

### 2.1 Workflow 与状态

- `task_envelope`
- `workflow`
- `workflow_attempt`
- `workflow_stage`
- `reopen_event`
- `approval_record`
- `manual_todo`
- `outbox_event`

状态机由 domain command handlers 控制。LangGraph/CrewAI 不能作为业务事实源。

### 2.2 Artifact 与协作

- `artifact`
- `artifact_version`
- `artifact_relation`
- `collaboration_session`
- `agent_run`
- `collaboration_command`
- `collaboration_event`
- `handoff_packet`

旧 artifact 不删除；重开时标记 `superseded` 并保留 lineage。

### 2.3 Context、Memory、Skill

- `context_snapshot`
- `agent_run_context_slice`
- `memory_item`
- `memory_version`
- `memory_relation`
- `memory_collection`
- `memory_extraction_result`
- `default_context_binding`
- `process_archive`
- `knowledge_item`
- `reflection_record`
- `skill_package`
- `skill_package_version`
- `skill_activation`
- `prompt_version`
- `model_profile`
- `tool_profile`

记忆分层必须匹配本项目的高治理投资工作台，而不是照搬个人笔记产品：

| 层 | 用途 | 是否业务事实源 | 默认注入 |
|---|---|---:|---:|
| `Artifact` | 正式阶段产物和业务结论 | 是 | 按 stage/template 注入 |
| `ProcessArchive` | runner transcript 摘要、工具调用摘要、会议/协作过程档案 | 否 | 否，仅按需检索摘要 |
| `MemoryItem` | Owner 观察、Researcher 摘录、研究笔记、反思草稿、经验候选 | 否 | 否，按 collection/query 召回 |
| `KnowledgeItem` | 验证过、带适用条件和失效条件的可复用知识 | 否 | 按 ContextSnapshot policy 注入 |
| `DefaultContextBinding` | 经治理生效的默认上下文绑定 | 否，但影响新运行 | 仅新任务/新 attempt |
| `ContextSlice` | AgentRun 实际注入记录和拒绝记录 | 否，审计证据 | 当前 AgentRun 固定 |

代码分包口径：`memory_item`、`memory_version`、`memory_relation`、`memory_collection`、`memory_extraction_result`、`knowledge_item`、`default_context_binding` 和 ContextSlice 注入审计属于 `domain.memory` 基础上下文模型；`domain.knowledge` 只承接检索、知识晋升、Prompt/Skill proposal、reflection workflow 和知识页投影。WI-001 不应在 `src/velentrade/domain/knowledge/**` 下实现基础 schema。

可借鉴 `/home/admin/memos` 的是捕获、Markdown、payload 自动提取、tag、relation、filter/shortcut 和 organize 流程；不可借鉴 public/share/reaction/social inbox、自由覆盖更新、删除式整理或多用户 visibility 语义。V1 使用单 Owner 访问模型，边界来自 Authority Gateway、append-only version、redaction、ContextSnapshot 和 audit。

`MemoryItem` 存储规则：

- 正文使用 Markdown，适合快速捕获观察、研究摘录和反思草稿。
- 派生 payload 由 `MemoryExtractionResult` 生成，至少包含 `title`、`tags`、`mentions`、`has_link`、`has_task_list`、`has_code`、`has_incomplete_tasks`、`symbol_refs`、`artifact_refs`、`agent_refs`、`stage_refs`、`source_refs`、`sensitivity`。
- `MemoryRelation` 只允许封闭关系：`references / comments / supports / contradicts / supersedes / derived_from / applies_to / duplicates / promotes_to`。
- `MemoryCollection` 是保存的筛选集合，使用受限 CEL 子集；用途包括知识页筛选、Researcher digest、ContextSlice 组装和 fixture 验证。
- `pinned` 只影响 UI/召回排序，不代表事实权威，不代表进入默认上下文。

写入和更新规则：

- Agent/Researcher/Owner 可通过 Gateway 捕获 memory、追加 comment/relation、提交 organize suggestion 或生成 promotion proposal。
- 任何正文修正都生成新 `MemoryVersion`，旧版本保留；不得覆盖或删除旧版本来改变历史论证。
- Memory 晋升为 Knowledge 或 DefaultContext 必须走 Researcher/CFO/Governance 链路；高影响必须 Owner 审批。
- Memory/Knowledge 召回进入 AgentRun 时必须 fenced 为 background，并写入 `ContextSlice.memory_refs_injected`、`retrieval_query_summary`、`redaction_policy_applied` 和 `denied_memory_refs`。
- 财务敏感原始字段不能进入普通 Memory payload 或非 CFO ContextSlice；只能进入加密财务表或 CFO/财务服务明文路径。

### 2.4 Data 与服务

- `data_domain_registry`
- `data_source_registry`
- `data_request`
- `data_lineage`
- `data_quality_report`
- `data_conflict_report`
- `market_state`
- `factor_result`
- `valuation_result`
- `portfolio_optimization_result`
- `risk_engine_result`
- `paper_account`
- `paper_order`
- `paper_execution_receipt`

Agent 和服务请求正式数据必须经 Data Collection & Quality Service。

字段级 schema 以 `contracts/domain-artifact-schemas.md` 为准；本附件只定义表域和存储边界。实现迁移时不得把 schema contract 中的业务结果混入节点状态枚举。

### 2.5 安全与审计

- `session`
- `user_auth`
- `audit_event`
- `sensitive_field_access_event`
- `security_finding`
- `runner_write_denial`

财务敏感字段采用应用层加密；普通日志和错误日志必须脱敏。

### 2.6 核心表列

字段级业务 payload 以 `contracts/domain-artifact-schemas.md` 为准；迁移实现必须至少包含以下可查询列，剩余复杂结构可进入 JSONB payload。

| table | 必备列 |
|---|---|
| `workflow` | `workflow_id pk`、`task_id fk`、`workflow_type`、`current_stage`、`current_attempt_no`、`status`、`context_snapshot_id`、`created_at`、`updated_at` |
| `workflow_attempt` | `workflow_id`、`attempt_no`、`context_snapshot_id`、`started_at`、`ended_at`、`status`、`superseded_by_attempt_no` |
| `workflow_stage` | `workflow_id`、`attempt_no`、`stage`、`node_status`、`responsible_role`、`reason_code`、`input_artifact_refs jsonb`、`output_artifact_refs jsonb`、`stage_version`、`started_at`、`completed_at` |
| `artifact` | `artifact_id pk`、`artifact_type`、`workflow_id`、`attempt_no`、`trace_id`、`producer`、`producer_type`、`status`、`schema_version`、`payload jsonb`、`created_at` |
| `collaboration_session` | `session_id pk`、`workflow_id`、`attempt_no`、`stage`、`mode`、`semantic_lead_agent_id`、`status`、`context_snapshot_id`、`opened_at`、`closed_at` |
| `agent_run` | `agent_run_id pk`、`workflow_id`、`attempt_no`、`stage`、`session_id`、`parent_run_id`、`agent_id`、`profile_version`、`context_snapshot_id`、`context_slice_id`、`status`、`output_artifact_schema`、`started_at`、`ended_at` |
| `context_snapshot` | `context_snapshot_id pk`、`snapshot_version`、`effective_scope`、`content_hash`、`payload jsonb`、`frozen boolean`、`created_at`、`effective_from` |
| `memory_item` | `memory_id pk`、`memory_type`、`owner_role`、`producer_agent_id`、`status`、`current_version_id`、`source_refs jsonb`、`sensitivity`、`pinned boolean`、`created_at`、`updated_at` |
| `memory_version` | `version_id pk`、`memory_id fk`、`version_no`、`content_markdown`、`payload jsonb`、`created_by`、`created_at`、`superseded_by_version_id` |
| `memory_relation` | `relation_id pk`、`source_memory_id`、`target_ref`、`relation_type`、`reason`、`evidence_refs jsonb`、`created_by`、`created_at` |
| `memory_collection` | `collection_id pk`、`title`、`filter_expression`、`scope`、`owner_agent_id`、`purpose`、`created_at`、`updated_at` |
| `memory_extraction_result` | `extraction_id pk`、`memory_version_id fk`、`extractor_version`、`payload jsonb`、`status`、`created_at` |
| `default_context_binding` | `binding_id pk`、`context_snapshot_id`、`source_ref`、`binding_type`、`effective_scope`、`impact_level`、`governance_change_ref`、`created_at` |
| `data_request` | `request_id pk`、`trace_id`、`data_domain`、`symbol_or_scope`、`required_usage`、`freshness_requirement`、`required_fields jsonb`、`requesting_stage`、`requesting_agent_or_service`、`created_at` |
| `data_quality_report` | `report_id pk`、`request_id fk`、`quality_score`、`quality_band`、`critical_field_results jsonb`、`decision_core_status`、`execution_core_status`、`created_at` |
| `governance_change` | `change_id pk`、`change_type`、`impact_level`、`state`、`proposal_ref`、`context_snapshot_id`、`effective_scope`、`state_reason`、`created_at`、`updated_at` |
| `paper_order` | `paper_order_id pk`、`workflow_id`、`decision_memo_ref`、`symbol`、`side`、`target_quantity_or_weight`、`price_range jsonb`、`urgency`、`execution_core_snapshot_ref`、`status`、`created_at` |
| `paper_execution_receipt` | `receipt_id pk`、`paper_order_id`、`pricing_method`、`execution_window jsonb`、`fill_status`、`fill_price`、`fill_quantity`、`fees jsonb`、`taxes jsonb`、`slippage jsonb`、`t_plus_one_state`、`created_at` |

唯一约束：

- `workflow_stage(workflow_id, attempt_no, stage)`。
- `agent_run(agent_run_id)` and `artifact(artifact_id)`。
- `memory_version(memory_id, version_no)`；`memory_relation(source_memory_id, target_ref, relation_type)`。
- outbox/idempotent 写入使用 `idempotency_key` 唯一约束。
- `context_snapshot.content_hash` 可重复，但同一 `snapshot_version` 只能指向一个 hash。

## 3. Authority Gateway

职责：

- 验证 source AgentRun 是否存在、状态是否允许、profile 是否授权。
- 验证 command/artifact/event/handoff schema。
- 验证 memory/version/relation/collection schema。
- 验证 workflow_id、attempt_no、stage 和 ContextSnapshot。
- 执行 append-only 写入。
- 写 audit_event 和 outbox_event。

拒绝场景：

- Runner 直接写业务表。
- Agent 写未授权 artifact 类型。
- Agent 修改他人 artifact 原版本。
- Agent 覆盖 Memory 原版本、删除历史 relation，或把 Memory 作为正式 artifact 写入。
- command_type 不在封闭集合。
- 访问财务敏感原始字段越权。
- 试图热改在途 ContextSnapshot。

Gateway 写入入口以 `contracts/api-read-models.md` 为准，必须统一执行：schema validation -> profile permission -> stage guard -> snapshot match -> append-only write -> audit_event -> outbox_event。任一步失败不得产生业务写入。

## 4. Agent Runner

运行边界：

- 独立 service/container。
- 无业务 DB 写凭证。
- 只读 DB 账号可读所有业务表视图，但财务敏感原始字段通过脱敏视图隐藏。
- CFO/财务服务使用单独解密路径，不经通用 Agent 只读视图泄露。
- 无 Docker socket。
- 只挂载已激活 SkillPackage 只读版本。
- 所有正式写入通过 Authority Gateway API。

Runner 可执行：

- 文件读取。
- 网络访问。
- 允许的终端/脚本。
- 只读 DB 查询。
- SkillPackage 脚本。

Runner 输出：

- artifact payload。
- command proposal。
- diagnostic。
- process archive。
- tool trace summary。

### 4.1 Agent Runner API

WI-001 必须交付 runner 基础执行壳和 fake LLM 路径；WI-002 只负责 worker 调度 `start_agent_run`，不在 worker 中实现 Agent 语义执行。

`POST /internal/agent-runner/runs/{agent_run_id}/start` 最小输入：

- `agent_run_id`
- `workflow_id`
- `attempt_no`
- `stage`
- `agent_id`
- `profile_version`
- `context_snapshot_id`
- `context_slice_id`
- `tool_profile_id`
- `skill_package_versions`
- `model_profile_id`
- `run_goal`
- `output_artifact_schema`
- `allowed_command_types`
- `budget_tokens`
- `timeout_seconds`

返回：

- `agent_run_id`
- `status`: `completed / failed / timed_out`
- `artifact_payloads`
- `command_proposals`
- `diagnostics`
- `process_archive_ref`
- `tool_trace_summary_ref`
- `cost_tokens`
- `failure_code`
- `failure_reason`

边界：

- runner 只能使用只读 DB 视图和 Authority Gateway API，不能持有业务表写凭证。
- `model_profile_id=fake_test` 时必须走 deterministic fake LLM，用于 P0 自动化；不得依赖 live LLM。
- runner 返回 artifact payload 不等于业务事实写入；只有 Authority Gateway 校验通过后才形成正式 artifact/event/handoff/memory 版本。
- worker 调用 runner 失败只能写 `runner_unavailable`、`budget_timeout` 或 incident/CollaborationEvent，不能伪造 Agent artifact。

### 4.2 ModelGateway

业务代码和 Agent Runner 只能调用 ModelGateway，不直接使用供应商 SDK。

`model_profile` 最小字段：

- `model_profile_id`
- `provider_profile_id`
- `purpose`: `high_reasoning / balanced / fast_summary / diagnostic / fake_test`
- `model_name`
- `max_input_tokens`
- `max_output_tokens`
- `default_temperature`
- `cost_budget_cny`
- `rate_limit_policy`
- `fallback_profile_ids`
- `status`: `active / degraded / disabled`

路由规则：

- Agent registry 的 `default_model_profile` 只绑定用途档位，实际 provider/model 由当前 ContextSnapshot 中的 ModelGateway config 决定。
- P0 自动化验证必须使用 `fake_test` profile，不依赖 live LLM 或付费模型。
- 单次 AgentRun 的 `budget_tokens` 与 `timeout_seconds` 是硬上限；超限写 `budget_timeout` failure code 和 CollaborationEvent。
- Provider timeout、rate limit 或 schema fail 先按 `fallback_profile_ids` 重试；全部失败时返回 `SERVICE_UNAVAILABLE`，不得伪造 Agent artifact。
- token、latency、cost、provider status 必须写入 observability 字段，不作为业务事实源。

## 5. 检索架构

V1 使用 PostgreSQL full-text + pgvector：

- full-text 用于中文/英文关键词、代码、标题、公告、历史 transcript 检索。
- pgvector 用于语义召回、经验库、研究资料、反思和过程档案摘要。
- 检索结果必须带 source refs、score、timestamp、visibility 和 redaction status。
- 检索内容注入上下文时必须 fenced 为 background，不是新指令。
- Memory 检索必须同时返回 `memory_type`、`status`、`version_id`、`relation_summary`、`collection_refs`、`sensitivity`、`promotion_state` 和 `why_included`。
- Context Engine 组装 ContextSlice 时必须按优先级处理：正式 artifact > verified KnowledgeItem > MemoryItem/ProcessArchive 摘要；同一事实冲突时不得用 Memory 覆盖 artifact。
- `MemoryCollection.filter_expression` 使用受限 CEL 子集，字段范围固定为 `content/tags/memory_type/status/producer_agent_id/symbol_refs/artifact_refs/created_at/updated_at/sensitivity/pinned`；不允许任意 SQL。
- metadata extraction 可异步执行，但写入 ContextSlice 前必须引用成功的 `MemoryExtractionResult` 或明确 `extraction_status=missing`，不得静默使用未解析正文。

Milvus 不进入 V1；未来可作为可重建向量索引，不作为业务事实源。

## 6. SkillPackage 存储

文件包存储：

```text
skills/{skill_id}/{version}/
  SKILL.md
  manifest.yaml
  permissions.yaml
  deps.lock
  scripts/
  templates/
  tests/
  fixtures/
```

PostgreSQL 记录：

- manifest。
- package hash。
- version。
- required permissions。
- deps hash。
- validation result。
- status: `draft / validated / active / retired / blocked`
- activation scope。
- rollback refs。

低/中影响 Skill 更新可自动验证后激活；高影响需 Owner 审批。

## 7. 部署

Docker Compose 单节点：

- `postgres`
- `redis`
- `api`
- `worker`
- `beat`
- `agent-runner`

启动顺序：

1. postgres/redis healthcheck。
2. Alembic migration。
3. api/worker/beat/agent-runner。
4. FastAPI 服务 `/api` 和 built frontend static。

Dev frontend 使用 Vite proxy。

### 7.1 Auth 与 session

V1 单 Owner 仍必须有明确登录流程：

1. `POST /api/auth/login` 接收用户名/密码，使用 Argon2id 校验 `user_auth.password_hash`。
2. 登录成功后创建 `session` 行，生成随机 session id，保存 hash、`created_at`、`expires_at`、`last_seen_at`、`rotated_from_session_id`。
3. Cookie 使用 `HttpOnly`、`Secure`、`SameSite=Strict`；本地 dev 可允许 `Secure=false` 但必须由 `VELENTRADE_ENV=dev` 控制。
4. 每次写请求校验 session、CSRF token header 和 optimistic version。GET 只校验 session。
5. session 默认 12 小时 idle timeout、7 天 absolute timeout；敏感审批动作可要求最近 30 分钟内重新认证。
6. logout 删除 server session 并清 cookie；session rotation 不改变业务事实源。

### 7.2 Celery task contract

| task | 触发 | retry / timeout | 幂等键 |
|---|---|---|---|
| `dispatch_outbox_event` | outbox_event created | 5 retries, exponential backoff, 60s timeout | outbox_event_id |
| `run_data_request` | Data Request accepted | 3 retries, 120s timeout | request_id |
| `run_service_calculation` | service orchestration command | 2 retries, 180s timeout | service_call_id |
| `start_agent_run` | AgentRun queued | 1 retry for runner unavailable, timeout from AgentRun | agent_run_id |
| `apply_owner_timeout` | beat schedule | no retry beyond next beat, 30s timeout | approval_or_task_id + deadline |
| `evaluate_governance_change` | governance triage/assessment | 2 retries, 120s timeout | change_id + state_version |
| `activate_context_snapshot` | approved governance change | no silent retry after activation failure, 60s timeout | change_id + target_version |
| `publish_daily_attribution` | beat daily after market close | 2 retries, 300s timeout | trading_date |
| `health_probe_sources` | beat every 5 minutes | 1 retry, 30s timeout | source_id + probe_window |

Beat schedules are configuration, but V1 defaults are: owner timeout every minute, source health every 5 minutes, outbox dispatcher continuous worker, daily attribution once per trading day after close. Task failure writes incident or CollaborationEvent; no Celery task may directly bypass domain command handlers.

## 8. 可观测性

必须记录：

- `trace_id`
- `workflow_id`
- `attempt_no`
- `stage`
- `agent_run_id`
- `artifact_id`
- `command_id`
- `context_snapshot_id`
- `skill_package_versions`
- latency、token、cost、model profile。

Prometheus 指标：

- workflow stage duration。
- AgentRun duration/status。
- command accepted/rejected。
- data quality distribution。
- execution_core block count。
- LLM cost/token。
- runner write denial。
- sensitive field access denial。

LangSmith 可作为 dev-only 可选工具，不作为 V1 验收依赖。

## 9. 测试基础设施

P0 自动化默认使用：

- Testcontainers PostgreSQL/Redis。
- Alembic upgrade/downgrade smoke。
- Celery worker integration。
- fake LLM。
- fixture adapters for data sources。
- Playwright for frontend workflow and governance UI。

禁止：

- 用 SQLite 替代 PostgreSQL 测试业务持久化。
- 依赖 live LLM 或 live paid data source 作为 P0 pass 条件。
- 跳过 migration/schema 检查。

## 10. Design Contract 绑定

| contract | 存储/运行时影响 |
|---|---|
| `contracts/domain-artifact-schemas.md` | 表字段、artifact payload、stage guard reason code 和跨 WI schema 名称的来源 |
| `contracts/api-read-models.md` | read model 聚合、错误响应、前端禁用入口和 Trace/Debug 查询边界 |
| `contracts/verification-report-schemas.md` | report writer 输出结构、fixture 引用和 P0 pass/fail 判定 |

任一实现若需要新增业务状态、artifact 类型、错误码或 report 字段，先回写对应 contract；不得在实现中临时发明未登记的权威字段。
