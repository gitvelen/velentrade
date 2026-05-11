# deployment.md

<!-- CODESPEC:DEPLOYMENT:READING -->
## 0. AI 阅读契约

- 本文件记录本次变更的真实交付、运行验证、回滚准备和人工验收结论。
- `release_mode=runtime` 表示需要运行部署；`artifact` 表示交付构建产物、文档或配置；`manual` 表示由人工执行交付步骤。
- 本文件不重复设计中的环境与安全要求，只引用并证明本次交付是否满足。
- `manual_verification_ready: pass` 只表示可以开始人工验收，不表示人工验收通过。

<!-- CODESPEC:DEPLOYMENT:TARGET -->
## 1. 发布对象与环境

release_mode: runtime
target_env: local-runtime
deployment_date: 2026-05-10
design_environment_ref: design.md#6-横切设计
release_artifact: frontend/dist + committed Python source, tests, and docker-compose runtime at deployed_revision

<!-- CODESPEC:DEPLOYMENT:PRECONDITIONS -->
## 2. 发布前条件

- [x] all required TC full-integration records passed (150 tests: 36 backend + 17 E2E + 97 frontend)
- [x] deployment-only/manual TC evidence plan prepared: manual acceptance cases MANUAL-DEPLOY-001 through MANUAL-DEPLOY-008
- [x] required migrations verified: 20260506_0005 (scheduled data collection) and 20260506_0006 (knowledge cleanup) applied
- [x] rollback plan prepared
- [x] smoke checks prepared

<!-- CODESPEC:DEPLOYMENT:EXECUTION -->
## 3. 执行证据
status: pass
execution_ref: deploy-ce84d8e
deployment_method: docker-compose-runtime-rebuild
deployed_at: 2026-05-10T15:20:00Z
deployed_revision: ce84d8e1b39acfa33ca8faa7993887be7b3c6fd9
source_revision: ce84d8e1b39acfa33ca8faa7993887be7b3c6fd9
restart_required: yes
restart_reason: API image rebuilt with WI-011 implementation and WI-002 regression fix
runtime_observed_revision: ce84d8e1b39acfa33ca8faa7993887be7b3c6fd9
runtime_ready_evidence: docker compose up -d --build api worker agent-runner; containers restarted and healthy; curl /api/devops/health returns observed status with metric-collection check; all 150 full-integration tests pass against live API on 8443
## 4. 运行验证
smoke_test: pass
runtime_ready: pass
manual_verification_ready: pass
## 5. 回滚与监控

rollback_trigger_conditions:
  - frontend artifact build fails or cannot be opened from dist/index.html
  - Python domain verification fails under the deployed revision
  - API /api/devops/health returns error or unexpected recovery state
  - docker compose API container exits or becomes unhealthy
  - codespec deployment readiness or verification gate fails
rollback_steps:
  1. docker compose down api worker agent-runner
  2. git checkout previous accepted revision (e.g. b66c129 for pre-WI-011 baseline)
  3. docker compose up -d --build api worker agent-runner
  4. Re-run full-integration pytest, frontend test, frontend build, and codespec verification before retrying deployment.
monitoring_metrics:
  - docker compose ps: all containers healthy
  - pytest full-integration pass count (150 expected)
  - frontend Vitest pass count (97 expected)
  - Vite production build success and dist asset generation
  - /api/devops/health routine_checks status
  - codespec verification and deployment-readiness gate status
monitoring_alerts:
  - any automated verification command exits non-zero
  - frontend build omits dist/index.html or generated assets
  - API /api/devops/health returns recovery with no real incident
  - manual_verification_ready is not pass after deploy script execution

## 5.1 人工验证案例步骤

manual_verification_scope: runtime/local-runtime; this checklist validates the live docker-compose runtime with real PostgreSQL/Redis/API, not just a static artifact.
manual_verification_entrypoint: http://127.0.0.1:8443 after running `docker compose up -d --build api` from the repository root.

manual_cases:
  - case_id: MANUAL-DEPLOY-001
    title: 发布证据与验收范围核对
    steps:
      1. Open `deployment.md` and confirm `release_mode: artifact`, `target_env: local-artifact`, `status: pass`, `smoke_test: pass`, and `manual_verification_ready: pass`.
      2. Confirm `deployed_revision` equals `runtime_observed_revision` in `deployment.md`.
      3. Confirm the acceptance section records `status: pass` after Owner approval.
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
  - case_id: MANUAL-DEPLOY-008
    title: WI-011 Owner 工作台验收返工核心验证
    steps:
      1. Open http://127.0.0.1:8443 (live runtime with real API).
      2. Confirm 全景 shows unified 待办 card (merged approval + manual task), not separate "审批" and "人工待办" cards.
      3. Click 待办, confirm it navigates to governance with real approval ID from /api/approvals (not hardcoded ap-001).
      4. Navigate to /investment/wf-001, confirm S3 blocker (retained_hard_dissent) is separate from S6 execution guard.
      5. Confirm S3 middle card shows structured debate details (owner_summary, core disputes, view changes).
      6. Navigate to /finance, confirm summary, aggregated assets, reminders, and finance form exist.
      7. Submit a finance asset update via the form, confirm it calls /api/finance/assets.
      8. Navigate to /knowledge, confirm owner-readable projections (no raw memory/test/internal IDs visible).
      9. Navigate to 治理 > 团队, confirm agent cards use Chinese names (CIO, Macro Analyst etc.) not machine IDs.
      10. Navigate to 治理 > 健康, confirm no machine IDs visible in default view.
      11. Confirm /api/devops/health returns real status (no fake recovery without incident).
    pass_criteria: All WI-011 acceptance criteria are verified against live runtime with real API data.

<!-- CODESPEC:DEPLOYMENT:ACCEPTANCE -->
## 6. 人工验收与收口
status: pass
notes: Owner manually verified all 8 acceptance cases (MANUAL-DEPLOY-001 through MANUAL-DEPLOY-008) against live runtime at http://127.0.0.1:8443. Unified todo cards, real approval IDs, S3/S6 separation, structured debate details, finance form, knowledge projections, Chinese agent names, hidden machine IDs, and real health status all confirmed.
approved_by: owner
approved_at: 2026-05-10
## 7. 收口动作

post_deployment_actions:
  - [x] update related docs
  - [x] record lessons learned if needed
  - [ ] submit PR or archive stable version after manual acceptance
