# deployment.md

<!-- CODESPEC:DEPLOYMENT:READING -->
## 0. AI 阅读契约

- 本文件记录本次变更的真实交付、运行验证、回滚准备和人工验收结论。
- `release_mode=runtime` 表示需要运行部署；`artifact` 表示交付构建产物、文档或配置；`manual` 表示由人工执行交付步骤。
- 本文件不重复设计中的环境与安全要求，只引用并证明本次交付是否满足。
- `manual_verification_ready: pass` 只表示可以开始人工验收，不表示人工验收通过。

<!-- CODESPEC:DEPLOYMENT:TARGET -->
## 1. 发布对象与环境

release_mode: artifact
target_env: local-artifact
deployment_date: 2026-04-30
design_environment_ref: design.md#6-横切设计
release_artifact: frontend/dist + committed Python source and tests at deployed_revision

<!-- CODESPEC:DEPLOYMENT:PRECONDITIONS -->
## 2. 发布前条件

- [x] all required TC full-integration records passed
- [x] deployment-only/manual TC evidence plan prepared: no deployment-only TC in V1; manual acceptance remains pending
- [x] required migrations verified: no Alembic migration files in this implementation slice
- [x] rollback plan prepared
- [x] smoke checks prepared

<!-- CODESPEC:DEPLOYMENT:EXECUTION -->
## 3. 执行证据
status: pass
execution_ref: deploy-67ad4c06e807
deployment_method: local-artifact-build
deployed_at: 2026-05-05T03:47:06Z
deployed_revision: 67ad4c06e8077359316a5205f601578df1dc0f6a
source_revision: 67ad4c06e8077359316a5205f601578df1dc0f6a
restart_required: no
restart_reason: artifact release only; no running service restarted
runtime_observed_revision: 67ad4c06e8077359316a5205f601578df1dc0f6a
runtime_ready_evidence: frontend/dist artifact built and smoke-checked; runtime not applicable for artifact release
## 4. 运行验证
smoke_test: pass
runtime_ready: not-applicable
manual_verification_ready: pass
## 5. 回滚与监控

rollback_trigger_conditions:
  - frontend artifact build fails or cannot be opened from dist/index.html
  - Python domain verification fails under the deployed revision
  - codespec deployment readiness or verification gate fails
rollback_steps:
  1. Revert to the previous accepted git revision before this Deployment evidence commit.
  2. Remove regenerated frontend/dist artifact if it came from the failed revision.
  3. Re-run full-integration pytest, frontend test, frontend build, and codespec verification before retrying deployment.
monitoring_metrics:
  - pytest full-integration pass count
  - frontend Vitest pass count
  - Vite production build success and dist asset generation
  - codespec verification and deployment-readiness gate status
monitoring_alerts:
  - any automated verification command exits non-zero
  - frontend build omits dist/index.html or generated assets
  - manual_verification_ready is not pass after deploy script execution

## 5.1 人工验证案例步骤

manual_verification_scope: artifact/local-artifact only; this checklist validates the built Web artifact and documented deployment evidence, not production runtime or live external provider readiness.
manual_verification_entrypoint: http://127.0.0.1:4173 after running `python -m http.server 4173 -d frontend/dist` from the repository root.

manual_cases:
  - case_id: MANUAL-DEPLOY-001
    title: 发布证据与验收范围核对
    steps:
      1. Open `deployment.md` and confirm `release_mode: artifact`, `target_env: local-artifact`, `status: pass`, `smoke_test: pass`, and `manual_verification_ready: pass`.
      2. Confirm `deployed_revision` equals `runtime_observed_revision` in `deployment.md`.
      3. Confirm the acceptance section still says `status: pending` before Owner approval.
    pass_criteria: The reviewer agrees this is an artifact acceptance, not a production runtime acceptance, and no wording implies `owner_verified` before manual approval.
  - case_id: MANUAL-DEPLOY-002
    title: Web artifact loads and approved shell is visible
    steps:
      1. Run `python -m http.server 4173 -d frontend/dist`.
      2. Open `http://127.0.0.1:4173`.
      3. Confirm the page loads without a blank screen.
      4. Confirm the top navigation shows `全景 / 投资 / 财务 / 知识 / 治理`.
      5. Confirm the global command button `自由对话` is visible.
    pass_criteria: The built artifact renders the approved Chinese workbench shell and primary navigation.
  - case_id: MANUAL-DEPLOY-003
    title: 自由对话生成任务卡路径
    steps:
      1. Click `自由对话`.
      2. Enter `学习热点事件`.
      3. Click `生成请求预览`.
      4. Confirm the preview says the task is research-oriented and does not enter approval or trading.
      5. Click `确认生成任务卡`.
      6. Confirm the UI shows `任务卡已生成` and exposes an `打开投资档案` entry.
    pass_criteria: Owner can create a visible task card from the artifact UI, and research-only boundaries are visible.
  - case_id: MANUAL-DEPLOY-004
    title: 投资档案与 Trace 业务面板
    steps:
      1. Open the generated investment dossier from the task card, or navigate to `/investment/wf-001`.
      2. Confirm the dossier shows Data Readiness, Analyst Memo, consensus/action strength, Risk, paper execution, and attribution-related panels.
      3. Confirm no real broker, real order, non-A trade, or direct Risk bypass action is exposed.
      4. Open the Trace/Debug entry from the investment dossier.
      5. Confirm Trace/Debug shows AgentRun, command, handoff, context, or artifact lineage rather than raw chat as the business fact source.
    pass_criteria: The artifact exposes the expected decision and trace surfaces without forbidden execution shortcuts.
  - case_id: MANUAL-DEPLOY-005
    title: 治理、审批、Agent 团队和能力草案边界
    steps:
      1. Navigate to `治理`.
      2. Confirm `审批中心` and `Agent 团队` are visible under Governance.
      3. Open `Agent 团队`.
      4. Confirm nine Agent cards are visible and capability changes are presented as drafts or governance changes.
      5. Open an approval packet if present.
      6. Confirm the approval page shows impact, rollback or state-change information, and does not silently apply high-impact changes.
    pass_criteria: Governance surfaces make Agent changes and approval state visible without hot-editing in-flight AgentRun or bypassing Owner approval.
  - case_id: MANUAL-DEPLOY-006
    title: 财务与知识边界
    steps:
      1. Navigate to `财务`.
      2. Confirm finance asset updates are described as finance-profile updates only, not approval, execution, or trading actions.
      3. Navigate to `知识`.
      4. Confirm Memory/Knowledge content is presented as context, evidence, reusable experience, or proposal material.
      5. Confirm Knowledge/Prompt/Skill changes are shown as proposals or governance paths, not immediate hot changes.
    pass_criteria: Finance and Knowledge pages preserve the approved boundaries around non-trading finance updates and memory-not-fact-source behavior.
  - case_id: MANUAL-DEPLOY-007
    title: 失败态、fallback 标识和剩余未完成项确认
    steps:
      1. Review `testing.md#HANDOFF-DEPLOYMENT-20260505`.
      2. Confirm the reviewer understands WI-004 rich surfaces, WI-010 independent full-integration, live external provider production readiness, and Owner acceptance are listed as residual or scoped items.
      3. During UI review, note any visible fallback/error labels, stale hints, trace hints, or retry affordances.
      4. Reject manual acceptance if the UI hides a backend failure as a successful real runtime result.
    pass_criteria: The manual conclusion explicitly accepts artifact scope and does not treat fallback, fixture, or provider smoke evidence as full production readiness.

<!-- CODESPEC:DEPLOYMENT:ACCEPTANCE -->
## 6. 人工验收与收口
status: pending
notes: pending manual acceptance
approved_by: pending
approved_at: pending
## 7. 收口动作

post_deployment_actions:
  - [ ] update related docs
  - [ ] record lessons learned if needed
  - [ ] submit PR or archive stable version after manual acceptance
