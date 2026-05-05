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
