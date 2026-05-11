# 02. Investment Pages

## 0. 页面目标

投资页回答三件事：

1. 哪些机会或正式 IC 正在排队。
2. 单个投资 workflow 到了 S0-S7 的哪一步，为什么行动或不行动。
3. Agent 协作、分歧、风控、执行和归因如何被审计。

主要路由：

- `/investment`
- `/investment/:workflowId`
- `/investment/:workflowId/trace`

页面归属：

- `/investment`、`/investment/:workflowId`、`/investment/:workflowId/trace` 均归属主菜单“投资”。
- Dossier 是投资 workflow 详情页，不是主菜单。
- Trace 是投资 workflow 审计详情页，不是主菜单；可从治理 Audit/Health 跳入，但 active 主菜单仍为“投资”。

## 1. 投资队列页

### 1.1 队列表格

| 编号 | 列 | 说明 | 交互 |
|---|---|---|---|
| INV-001 | priority | P0/P1/P2，P0 高亮 | 可筛选 |
| INV-002 | symbol | A 股代码和名称 | 点击进入 Dossier |
| INV-003 | title | 议题标题 | 点击进入 Dossier |
| INV-004 | task_type | candidate、formal_ic、holding_risk、research_task | 可筛选 |
| INV-005 | hard_gate | passed、failed、blocked 及 reason_code | 点击展开硬门槛 |
| INV-006 | score | 四维评分摘要 | 点击展开评分明细 |
| INV-007 | stage | 当前 S0-S7 阶段 | 点击进入对应 Dossier stage |
| INV-008 | owner_attention | 是否需要 Owner | 点击审批包或任务详情 |
| INV-009 | updated_at | 最近状态更新时间 | 默认排序 |

### 1.2 筛选器

| 编号 | 筛选 | 选项 |
|---|---|---|
| INV-010 | 阶段 | S0-S7、blocked、waiting、reopened |
| INV-011 | 优先级 | P0/P1/P2 |
| INV-012 | 类型 | candidate、formal_ic、holding_risk、research_task |
| INV-013 | 风控 | approved、conditional_pass、rejected、not_started |
| INV-014 | 数据状态 | normal、degraded、blocked、cache_only |
| INV-015 | Agent 分歧 | hard_dissent、debate_required、debate_skipped |

### 1.3 硬门槛展开

| 编号 | 门槛 | 展示 |
|---|---|---|
| INV-016 | A 股普通股范围 | passed/failed，失败时说明资产类型 |
| INV-017 | Request Brief 完整性 | 缺失字段 |
| INV-018 | 核心数据可用性 | decision_core quality |
| INV-019 | 研究资料非空 | Research Package refs |
| INV-020 | 合规/执行禁区 | reason_code |
| INV-021 | 同主题去重 | existing workflow refs |
| INV-022 | 并发槽 | formal IC 3 个、全局 workflow 5 个 |

规则：

- `INV-023`: supporting evidence only 只能进入候选或研究任务，不直入正式 IC。
- `INV-024`: P0 可抢占 active slot，但不可跳过 IC、风控或审计。
- `INV-024A`: 人工待办不作为投资队列类型；非 A 股或人工动作只在治理任务中心展示，投资页最多显示关联提示或跳转链接。

## 2. 投资档案首屏

canonical 路径：`投资 -> 投资队列 -> 投资档案`。

```text
顶部：任务摘要、标的、attempt、当前阶段、行动/阻断状态
左侧：S0-S7 StageRail + Reopen Events
中部：selected_stage 核心 artifact
右侧：数据质量、Risk、Approval、Execution、Evidence
底部：Handoff、Attribution、Reflection linkback
```

### 2.1 任务摘要条

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-025 | workflow_id | `WF-...` |
| INV-026 | symbol/name | 标的代码和名称 |
| INV-027 | attempt_no | 当前 attempt |
| INV-028 | current_stage | S0-S7 |
| INV-029 | decision_state | action、observe、no_action、blocked |
| INV-030 | highest_blocker | 最高阻断 reason_code |
| INV-031 | detail_actions | 查看证据、打开审计、返回来源 |

## 3. StageRail

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-032 | stage code | S0-S7 |
| INV-033 | stage title | 请求、数据、分析、辩论、CIO、风控、执行、归因 |
| INV-034 | node_status | not_started、running、waiting、blocked、completed、skipped、failed |
| INV-035 | responsible role | Workflow、Service、Agent 或 Owner |
| INV-036 | reason_code | blocked/waiting/failed 时必显 |
| INV-037 | artifact count | 产物数量 |
| INV-038 | reopen marker | 有重开事件时显示 |

交互：

- `INV-039`: 点击 stage chip 只改变 `selected_stage` 和 URL query，不推进 workflow。
- `INV-040`: hover 或展开显示 evidence_refs，不显示 raw transcript。
- `INV-041`: reopen marker 点击展示 superseded/preserved artifacts，只读展示旧 attempt。

## 4. S0-S7 阶段内容

| 编号 | 阶段 | 中部主内容 | 右侧 guard |
|---|---|---|---|
| INV-042 | S0 请求受理 | Request Brief、Owner confirmation、任务边界 | asset boundary、request completeness |
| INV-043 | S1 数据就绪 | Data Readiness、IC Context Package、CIO Chair Brief | decision_core、cache、fallback、conflict |
| INV-044 | S2 分析研判 | 四份 Analyst Memo、Role Payload Drilldown | memo schema、evidence quality |
| INV-045 | S3 辩论收敛 | Consensus、Dissent Board、Debate Timeline | hard_dissent、round limit、recomputed score |
| INV-046 | S4 CIO 收口 | CIO Decision Memo、Decision Packet、Optimizer Deviation | input guard、major deviation |
| INV-047 | S5 风控复核 | Risk Review Report | approved、conditional_pass、rejected、repairability |
| INV-048 | S6 授权与纸面执行 | 授权状态、例外审批可选、Paper Execution Receipt | owner decision、execution_core、T+1 |
| INV-049 | S7 归因反思 | Attribution、Reflection、Knowledge/Prompt Proposal | attribution trigger、CFO/Researcher handoff |

## 5. 关键卡片与表格

### 5.1 CIO Chair Brief

| 编号 | 字段 | 说明 |
|---|---|---|
| INV-050 | decision_question | 本次要回答的问题 |
| INV-051 | key_tensions | 关键矛盾 |
| INV-052 | must_answer | 分析师必须回答的问题 |
| INV-053 | time_budget | 时间预算 |
| INV-054 | action_criteria | 行动判定口径 |
| INV-055 | no_preset_attestation | 明确未预设买卖结论 |

### 5.2 Analyst Stance Matrix

| 编号 | 列 | 说明 |
|---|---|---|
| INV-056 | role | Macro、Fundamental、Quant、Event |
| INV-057 | direction_score | -5 到 +5 |
| INV-058 | confidence | 0 到 1 |
| INV-059 | evidence_quality | 0 到 1 |
| INV-060 | hard_dissent | 是/否，硬异议高亮 |
| INV-061 | view_update_refs | 辩论后观点更新引用 |
| INV-062 | memo_ref | 打开对应 Analyst Memo |

交互：

- `INV-063`: 点击角色行打开 Role Payload Drilldown。
- `INV-064`: hard_dissent 点击打开 Dissent Board 对应议题。

### 5.3 Role Payload Drilldown

| 编号 | 角色 | 专属内容 |
|---|---|---|
| INV-065 | Macro | 市场状态、政策传导、流动性、行业风格 |
| INV-066 | Fundamental | 商业质量、财务质量、盈利情景、估值、会计红旗 |
| INV-067 | Quant | 信号假设、因子、趋势、稳定性、择时含义 |
| INV-068 | Event | 事件类型、来源可靠性、验证状态、催化窗口、反转风险 |

规则：

- `INV-069`: 四份 Memo 不得压成同一通用模板。

### 5.4 Consensus Gauge

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-070 | consensus_score | 数值、阈值、计算输入 |
| INV-071 | action_conviction | 数值、`0.65` 阈值 |
| INV-072 | dominant_direction_share | 解释用 |
| INV-073 | score_std | 解释用 |
| INV-074 | result | action、observe、supplement_evidence、no_action |

规则：

- `INV-075`: `action_conviction < 0.65` 时不显示纸面执行入口。

### 5.5 Debate Timeline

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-076 | round_no | 最多 2 轮 |
| INV-077 | issue | 本轮分歧 |
| INV-078 | requested_evidence | 补证请求 |
| INV-079 | view_changes | 观点变化 |
| INV-080 | cio_synthesis | CIO 语义综合 |
| INV-081 | manager_process | Debate Manager 过程字段 |
| INV-082 | result | retained_dissent、resolved、risk_handoff |

规则：

- `INV-083`: 不显示长聊天 transcript 作为辩论结果。

### 5.6 Risk Gate Card

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-084 | verdict | approved、conditional_pass、rejected |
| INV-085 | reason_codes | 风控理由 |
| INV-086 | repairability | repairable/unrepairable |
| INV-087 | reopen_target | 可修复时显示 |
| INV-088 | owner_exception_ref | conditional_pass 才显示 |

规则：

- `INV-089`: Risk rejected 时无 Owner 批准继续按钮。
- `INV-090`: rejected repairable 只能显示重开建议，不直接执行。

### 5.7 Execution Replay

| 编号 | 字段 | 展示 |
|---|---|---|
| INV-091 | execution_core_status | normal、degraded、blocked |
| INV-092 | order_window | 执行窗口 |
| INV-093 | algorithm | VWAP/TWAP |
| INV-094 | price_band | 价格区间 |
| INV-095 | fill_state | filled、partial、expired、blocked |
| INV-096 | fees/slippage/tax | 费用、滑点、印花税 |
| INV-097 | t_plus_1 | T+1 标记 |

规则：

- `INV-098`: `execution_core_status=blocked` 时无继续成交入口。

## 6. Trace/Debug View

canonical 路径：`投资 -> 投资队列 -> Investment Dossier -> Workflow Trace`。

用途：审计、排障、治理，不是 Owner 默认视图，也不是主菜单。

| 编号 | 区块 | 展示 |
|---|---|---|
| INV-099 | AgentRun tree | parent_run_id、stage、attempt、profile_version、SkillPackage、ContextSlice |
| INV-100 | CollaborationCommand table | command_type、source、target、admission result、reason |
| INV-101 | CollaborationEvent timeline | progress、artifact submitted、guard failed、handoff |
| INV-102 | HandoffPacket graph | source artifacts、open questions、blockers、downstream consumer |
| INV-103 | Authority Gateway | accepted writes、direct write denial、sensitive access denial |
| INV-104 | Service/Data routing | DataRequest、source、fallback、cache、conflict |
| INV-105 | latency/token/cost | 运营观测，不作为投资事实 |
| INV-106 | raw transcript | 默认折叠，标注非正式事实源 |

来源与返回：

- `INV-106A`: 从 Dossier 进入时返回 Dossier 的当前 `selected_stage`。
- `INV-106B`: 从治理 Audit/Health 进入时，页面仍高亮“投资”，但标题区显示“返回治理来源”。
- `INV-106C`: 非投资 incident 不使用本 route；治理页只展示 trace 摘要和相关对象链接。

## 7. 禁用入口

| 编号 | 场景 | UI 表现 |
|---|---|---|
| GUARD-006 | Risk rejected | 无 Owner 批准继续 |
| GUARD-007 | execution_core blocked | 无继续成交入口 |
| GUARD-008 | 非 A 股资产 | 无审批/执行/交易入口 |
| GUARD-009 | 低共识或行动强度不足 | 无纸面执行入口 |
| GUARD-010 | 旧 attempt artifact | 只读，不允许恢复旧产物 |

## 8. 验收关联

| 项目 | 关联 |
|---|---|
| Requirement | REQ-006, REQ-007, REQ-008, REQ-017, REQ-018, REQ-019 |
| TC | TC-ACC-006-01, TC-ACC-007-01, TC-ACC-017-01, TC-ACC-018-01, TC-ACC-019-01 |
| Report | web_command_routing_report.json, governance_task_report.json |
