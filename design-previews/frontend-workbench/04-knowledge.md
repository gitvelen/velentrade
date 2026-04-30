# 04. Knowledge Page

## 0. 页面目标

知识页回答：“哪些研究资料、记忆、经验和反思可以作为上下文或证据线索；哪些提案可以进入治理；哪些内容不能直接成为业务事实源。”

默认路由：`/knowledge`

主要 read model：`KnowledgeSearchReadModel`

页面归属：`/knowledge` 归属主菜单“知识”。知识页可以跳到治理提案或投资 Dossier 引用，但 Memory/Knowledge 不直接成为业务事实源或推进 workflow。

## 1. 首屏布局

```text
顶部：每日简报 / 研究资料包 / 待处理提案摘要
中部：高价值经验 / 经验库 / 反思库
右侧：敏感信息保护 / 提案状态
底部：知识、能力改进和上下文提案表
```

## 2. 每日简报

| 编号 | 列 | 说明 |
|---|---|---|
| KN-001 | brief_id | 可点击 |
| KN-002 | priority | P0/P1/P2 |
| KN-003 | title | 高信号标题 |
| KN-004 | source | Researcher、服务信号、公告、Owner |
| KN-005 | boundary | supporting evidence only、candidate、research_task |
| KN-006 | evidence_refs | 来源引用 |
| KN-007 | created_at | 创建时间 |

交互：

- `KN-008`: 点击 P0 简报可进入投资队列候选，不跳过硬门槛。
- `KN-009`: supporting evidence only 显示明确边界，不直入正式 IC。

## 3. Research Package

| 编号 | 字段 | 展示 |
|---|---|---|
| KN-010 | package_id | 可点击 |
| KN-011 | related_symbol/topic | 关联标的或主题 |
| KN-012 | source_summary | 来源摘要 |
| KN-013 | evidence_quality | 证据质量 |
| KN-014 | conflicts | 冲突数量和摘要 |
| KN-015 | used_by | 关联 workflow、Memo 或 Debate |
| KN-016 | freshness | 新鲜度 |

规则：

- `KN-017`: Research Package 可被 Dossier 引用，但不替代 DataReadinessReport。

## 4. 高价值经验

| 编号 | 字段 | 展示 |
|---|---|---|
| KN-018 | collection_id | 可点击 |
| KN-019 | title | 集合名 |
| KN-020 | scope | investment、finance、agent_quality、devops 等 |
| KN-021 | purpose | 用途 |
| KN-022 | filter_expression | 过滤条件摘要 |
| KN-023 | result_count | 命中数量 |
| KN-024 | sensitivity | 是否包含敏感字段 |
| KN-025 | default_context_binding | 是否已绑定默认上下文 |

交互：

- `KN-026`: 点击集合查看 MemoryItem 列表。
- `KN-027`: 修改 collection 规则生成 proposal，不直接覆盖旧版本。

## 5. Memory Item 列表与详情

| 编号 | 列 | 说明 |
|---|---|---|
| KN-028 | memory_id | 可点击 |
| KN-029 | title | 记忆标题 |
| KN-030 | tags | 标签 |
| KN-031 | relation_count | 关系数量 |
| KN-032 | extraction_status | extracted、pending、failed |
| KN-033 | promotion_state | candidate、validated、promoted、archived |
| KN-034 | sensitivity | normal、finance_sensitive_raw、redacted |
| KN-035 | latest_version | append-only 版本 |

详情页展示：

| 编号 | 区块 | 展示 |
|---|---|---|
| KN-036 | Markdown 正文 | 当前 MemoryVersion 正文，只读 |
| KN-037 | payload 抽取 | 结构化摘要和字段 |
| KN-038 | version history | append-only 版本链 |
| KN-039 | relation list | references、supports、contradicts、supersedes 等 |
| KN-040 | source refs | 原始来源和 artifact refs |
| KN-041 | audit | 创建、修改、Gateway 写入记录 |

规则：

- `KN-042`: Memory 不可覆盖旧版本，只能追加新版本。
- `KN-043`: Memory/Knowledge 不能替代 artifact、stage guard、workflow state 或 DataReadinessReport。

## 6. Relation Graph

| 编号 | 关系类型 | 说明 |
|---|---|---|
| KN-044 | references | 引用 |
| KN-045 | supports | 支持 |
| KN-046 | contradicts | 反证或冲突 |
| KN-047 | supersedes | 取代旧内容 |
| KN-048 | derived_from | 派生 |
| KN-049 | applies_to | 适用于 |
| KN-050 | duplicates | 重复 |
| KN-051 | promotes_to | 晋升为知识 |

交互：

- `KN-052`: 点击节点打开 Memory/Knowledge/Artifact 详情。
- `KN-053`: 新关系以待应用建议展示，经 Gateway 写入。
- `KN-054`: 自由文本关系不得驱动下游 workflow。

## 7. 敏感信息保护

| 编号 | 字段 | 展示 |
|---|---|---|
| KN-055 | agent_run_id | 可跳 Trace |
| KN-056 | context_snapshot_id | 当前快照 |
| KN-057 | source_ref | Memory/Knowledge 来源 |
| KN-058 | binding_type | default、task_specific、retrieved |
| KN-059 | why_included | 注入原因 |
| KN-060 | redaction_status | visible、redacted、denied |
| KN-061 | denied_memory_refs | 被拒绝的敏感引用 |

规则：

- `KN-062`: raw process archive 默认不展示。
- `KN-063`: 注入上下文只作为 fenced background。

## 8. Reflection Library

| 编号 | 字段 | 展示 |
|---|---|---|
| KN-064 | reflection_id | 可点击 |
| KN-065 | trigger | attribution anomaly、periodic review、owner feedback |
| KN-066 | responsible_agent | 责任 Agent |
| KN-067 | first_draft_status | 一稿状态 |
| KN-068 | researcher_promotion | Researcher 晋升建议 |
| KN-069 | effective_scope | new_task 或 new_attempt |
| KN-070 | linked_proposal | Prompt/Skill/Knowledge Proposal |

规则：

- `KN-071`: 正常日度归因自动发布；异常或周期归因才触发 CFO/反思链路。
- `KN-072`: responsible Agent 一稿不能热改运行参数、Prompt、Skill 或在途 ContextSnapshot。

## 9. 改进提案表

| 编号 | 列 | 说明 |
|---|---|---|
| KN-073 | proposal_id | 可点击 |
| KN-074 | proposal_type | Knowledge、Prompt、Skill、DefaultContext |
| KN-075 | impact_level | low、medium、high |
| KN-076 | diff/manifest | 变更摘要 |
| KN-077 | validation_result_refs | 自动验证结果 |
| KN-078 | effective_scope | new_task 或 new_attempt |
| KN-079 | rollback_plan | 回滚引用 |
| KN-080 | governance_link | 变更管理或审批 |

规则：

- `KN-081`: 低/中影响展示自动验证和审计后生效边界。
- `KN-082`: 高影响跳转审批中心。
- `KN-083`: 知识页不直接使提案或 DefaultContext 生效。

## 10. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-004, REQ-027, REQ-028, REQ-030 |
| TC | TC-ACC-004-01, TC-ACC-027-01, TC-ACC-028-01, TC-ACC-030-01 |
| Report | memory_boundary_report.json, governance_task_report.json |
