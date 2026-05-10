from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass, replace
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from velentrade.core.settings import Settings
from velentrade.db.session import build_engine
from velentrade.db.store import SqlAlchemyGatewayMirror
from velentrade.domain.agents.registry import (
    build_agent_capability_profiles,
    build_agent_capability_config_read_model,
    build_agent_profile_read_model,
    build_team_read_model,
)
from velentrade.domain.collaboration.models import AgentRun, CollaborationCommand, CollaborationEvent, HandoffPacket
from velentrade.domain.common import new_id, utc_now
from velentrade.domain.devops.incident import DevOpsIncidentRuntime
from velentrade.domain.finance.boundary import FinanceAssetUpdate, FinanceProfileService
from velentrade.domain.gateway.authority import AuthorityGateway
from velentrade.domain.governance.runtime import GovernanceRuntime
from velentrade.domain.investment.owner_exception.approval import ApprovalRecord, OwnerExceptionService
from velentrade.domain.knowledge.hygiene import memory_capture_rejection_reason
from velentrade.domain.memory.models import MemoryCapture
from velentrade.domain.observability.health import ObservabilityCollector
from velentrade.domain.workflow.runtime import RequestBrief, TaskEnvelope, Workflow, WorkflowRuntime, WorkflowStage

from .schemas import (
    AgentCapabilityDraftRequest,
    ApprovalDecisionRequest,
    CollaborationCommandRequest,
    CreateRequestBriefRequest,
    CreateMemoryItemRequest,
    FinanceAssetUpdateRequest,
    GatewayArtifactWriteRequest,
    GatewayEventWriteRequest,
    GatewayHandoffWriteRequest,
    GatewayMemoryWriteRequest,
    MemoryRelationWriteRequest,
    RequestBriefConfirmationRequest,
    WorkflowCommandRequest,
)


FRONTEND_DIST_DIR = Path(__file__).resolve().parents[3] / "frontend" / "dist"


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _success(payload: Any) -> dict[str, Any]:
    return {
        "data": _serialize(payload),
        "meta": {"trace_id": new_id("trace"), "generated_at": utc_now()},
    }


def _error(status_code: int, code: str, message: str, *, reason_code: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "trace_id": new_id("trace"),
                "retryable": False,
                "reason_code": reason_code,
                "details": None,
            }
        },
    )


class ApiRuntime:
    def __init__(self, database_url: str | None = None) -> None:
        self.profiles = build_agent_capability_profiles()
        store = SqlAlchemyGatewayMirror(build_engine(database_url)) if database_url else None
        self.store = store
        self.gateway = AuthorityGateway(self.profiles, store=store)
        if hasattr(store, "cleanup_owner_knowledge_garbage"):
            store.cleanup_owner_knowledge_garbage()
        persisted_finance = store.load_finance_profile() if hasattr(store, "load_finance_profile") else None
        self.finance = (
            FinanceProfileService(profile=persisted_finance[0], manual_todos=persisted_finance[1])
            if persisted_finance is not None
            else FinanceProfileService()
        )
        self.observability = ObservabilityCollector()
        self.devops = DevOpsIncidentRuntime()
        self.governance = GovernanceRuntime()
        self.owner_exception = OwnerExceptionService()
        persisted_approvals = store.list_approval_records() if hasattr(store, "list_approval_records") else []
        self.approvals: dict[str, ApprovalRecord] = {
            approval.approval_id: approval for approval in persisted_approvals
        }
        self.workflow = WorkflowRuntime()
        self.workflow_titles: dict[str, str] = {}
        self.request_briefs: dict[str, RequestBrief] = {}
        self.confirmed_brief_ids: set[str] = set()
        self._seed_governance_and_approvals()
        self._seed_wf001_dossier()
        self.agent_runs = {
            f"run-{agent_id}": AgentRun.fake(
                agent_run_id=f"run-{agent_id}",
                agent_id=agent_id,
                workflow_id="wf-1",
                allowed_command_types=profile.write_policy.command_types,
                output_artifact_schema=profile.output_contracts[0].artifact_type,
            )
            for agent_id, profile in self.profiles.items()
        }
        self._seed_wf001_process()
        self.owner_memory_counter = 0

    def require_run(self, run_id: str) -> AgentRun | None:
        return self.agent_runs.get(run_id)

    def next_owner_capture_run(self) -> AgentRun:
        self.owner_memory_counter += 1
        run_id = f"run-owner-memory-{self.owner_memory_counter}"
        run = AgentRun.fake(
            agent_run_id=run_id,
            agent_id="investment_researcher",
            workflow_id="wf-owner-memory",
            allowed_command_types=["propose_knowledge_promotion"],
            output_artifact_schema="ResearchPackage",
            stage="capture",
        )
        self.agent_runs[run_id] = run
        return run

    def _seed_governance_and_approvals(self) -> None:
        self.governance.create_context_snapshot(
            snapshot_version="ctx-v1",
            source_change_ref="baseline",
            prompt_versions={"quant_analyst": "prompt-v1"},
            skill_package_versions={"quant_analyst": "skill-v1"},
            knowledge_item_versions=["knowledge-v1"],
            memory_collection_versions=["memory-collection-v1"],
            default_context_versions=["default-context-v1"],
            agent_capability_versions={"quant_analyst": "capability-v1"},
            effective_scope="new_task",
        )
        if "gov-change-001" not in self.governance.changes:
            self.governance.submit_change(
                change_id="gov-change-001",
                change_type="agent_capability",
                impact_level="high",
                proposal_ref="draft-quant-001",
                target_version_refs={"agent_capability_versions": {"quant_analyst": "capability-v2"}},
                effective_scope="new_task",
                rollback_plan_ref="rollback-quant-001",
            )
        packet = self.owner_exception.create_packet("candidate-001", "high_impact_agent_capability_change")
        if not self.approvals:
            approval = self.owner_exception.submit_for_approval(packet)
            self.approvals[approval.approval_id] = approval
            if hasattr(self.store, "mirror_approval_record"):
                self.store.mirror_approval_record(approval)

    def _seed_wf001_dossier(self) -> None:
        if "wf-001" in self.workflow.workflows:
            return
        now = utc_now()
        task = TaskEnvelope(
            task_id="task-wf-001",
            task_type="investment_workflow",
            priority="P0",
            owner_role="owner",
            current_state="ready",
            reason_code="request_brief_confirmed",
            artifact_refs=["brief-wf-001"],
            created_at=now,
            updated_at=now,
        )
        stage_outputs = {
            "S0": ["task-wf-001"],
            "S1": ["artifact-wf001-data-readiness"],
            "S2": [
                "artifact-wf001-macro-memo",
                "artifact-wf001-fundamental-memo",
                "artifact-wf001-quant-memo",
                "artifact-wf001-event-memo",
            ],
            "S3": ["artifact-wf001-debate-summary", "handoff-wf001-s3-risk-review"],
        }
        stages = [
            WorkflowStage(
                workflow_id="wf-001",
                attempt_no=1,
                stage=stage,
                node_status="blocked" if stage == "S3" else ("completed" if stage in stage_outputs and stage != "S3" else "not_started"),
                responsible_role={
                    "S0": "workflow_scheduling_center",
                    "S1": "data_collection_quality_service",
                    "S2": "analyst_team",
                    "S3": "cio_debate_manager",
                    "S4": "decision_service_and_cio",
                    "S5": "risk_officer",
                    "S6": "owner_and_paper_execution",
                    "S7": "attribution_and_reflection",
                }[stage],
                output_artifact_refs=stage_outputs.get(stage, []),
                reason_code="retained_hard_dissent_risk_review" if stage == "S3" else None,
                started_at=now if stage in stage_outputs else None,
                completed_at=now if stage in {"S0", "S1", "S2"} else None,
                stage_version=2 if stage in stage_outputs else 1,
            )
            for stage in [f"S{i}" for i in range(8)]
        ]
        workflow = Workflow(
            workflow_id="wf-001",
            task_id=task.task_id,
            workflow_type="investment_workflow",
            current_stage="S3",
            current_attempt_no=1,
            status="blocked",
            context_snapshot_id="ctx-v1",
            stages=stages,
            created_at=now,
            updated_at=now,
        )
        self.workflow.tasks[task.task_id] = task
        self.workflow.workflows[workflow.workflow_id] = workflow
        self.workflow_titles[workflow.workflow_id] = "浦发银行 A 股研究"
        self._seed_wf001_artifacts(now)
        if hasattr(self.store, "mirror_task"):
            self.store.mirror_task(task)
        if hasattr(self.store, "mirror_workflow"):
            self.store.mirror_workflow(workflow)

    def _seed_wf001_artifacts(self, now: str) -> None:
        existing = {artifact["artifact_id"] for artifact in self.gateway.artifact_ledger}
        artifacts = [
            _seed_artifact(
                "artifact-wf001-data-readiness",
                "DataReadinessReport",
                "data_collection_quality_service",
                "service",
                "S1",
                {
                    "quality_band": "partial",
                    "decision_core_status": "pass",
                    "execution_core_status": "blocked",
                    "reason_code": "execution_core_blocked_no_trade",
                    "issues": ["分钟级执行数据不足，S6 不允许成交。"],
                    "lineage_refs": ["tencent-public-kline:600000.SH"],
                    "data_requests": [
                        {
                            "request_id": "wf001-decision-daily",
                            "trace_id": "trace-wf001-decision-daily",
                            "data_domain": "a_share_market",
                            "symbol_or_scope": "600000.SH",
                            "required_usage": "decision_core",
                            "freshness_requirement": "same_trading_day",
                            "required_fields": [
                                {"name": "symbol", "present": True, "valid": True, "critical": True},
                                {"name": "trade_date", "present": True, "valid": True, "critical": True},
                                {"name": "close", "present": True, "valid": True, "critical": True},
                                {"name": "volume", "present": True, "valid": True, "critical": False},
                                {"name": "source_timestamp", "present": True, "valid": True, "critical": False},
                            ],
                            "requesting_stage": "S1",
                            "requesting_agent_or_service": "data_collection_quality_service",
                            "source_name": "腾讯公开日线行情",
                            "source_ref": "tencent-public-kline:600000.SH",
                        },
                        {
                            "request_id": "wf001-execution-realtime",
                            "trace_id": "trace-wf001-execution-realtime",
                            "data_domain": "execution_price",
                            "symbol_or_scope": "600000.SH",
                            "required_usage": "execution_core",
                            "freshness_requirement": "realtime",
                            "required_fields": [
                                {"name": "last_price", "present": False, "valid": False, "critical": True},
                                {"name": "order_book_depth", "present": False, "valid": False, "critical": True},
                                {"name": "execution_window", "present": False, "valid": False, "critical": True},
                            ],
                            "requesting_stage": "S6",
                            "requesting_agent_or_service": "execution_core",
                            "source_name": "实时执行行情",
                            "source_ref": "execution-core:600000.SH",
                        },
                    ],
                    "critical_field_results": {
                        "symbol": True,
                        "trade_date": True,
                        "close": True,
                        "last_price": False,
                        "order_book_depth": False,
                        "execution_window": False,
                    },
                    "fallback_attempts": [],
                    "cache_usage": {"cache_hit": False, "may_create_execution_authorization": False},
                },
                now,
            ),
            _seed_artifact("artifact-wf001-macro-memo", "AnalystMemo", "macro_analyst", "agent", "S2", _seed_memo("macro", "positive", 0.72, False), now),
            _seed_artifact("artifact-wf001-fundamental-memo", "AnalystMemo", "fundamental_analyst", "agent", "S2", _seed_memo("fundamental", "neutral", 0.68, True), now),
            _seed_artifact("artifact-wf001-quant-memo", "AnalystMemo", "quant_analyst", "agent", "S2", _seed_memo("quant", "positive", 0.74, False), now),
            _seed_artifact("artifact-wf001-event-memo", "AnalystMemo", "event_analyst", "agent", "S2", _seed_memo("event", "neutral", 0.61, False), now),
            _seed_artifact(
                "artifact-wf001-debate-summary",
                "DebateSummary",
                "cio",
                "agent",
                "S3",
                {
                    "rounds_used": 2,
                    "participants": ["cio", "macro", "fundamental", "quant", "event"],
                    "issues": ["资产质量修复是否足以抵消估值低位", "补证后是否能进入 S4"],
                    "new_evidence_refs": ["source-wf001-fundamental-npl", "source-wf001-fundamental-nim"],
                    "view_changes": ["量化观点由偏正面降为观察；基本面仍保留硬异议"],
                    "hard_dissent_present": True,
                    "retained_hard_dissent": True,
                    "risk_review_required": True,
                    "recomputed_consensus_score": 0.75,
                    "recomputed_action_conviction": 0.6,
                    "stop_reason": "hard_dissent_risk_handoff",
                    "next_stage_decision": "blocked_before_s4",
                    "agenda": ["核对资产质量证据", "判断估值修复是否足以进入 S4"],
                    "questions_asked": ["不良率、拨备覆盖率和息差趋势是否支持估值修复？"],
                    "synthesis": "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
                    "owner_summary": "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。",
                    "status_summary": {
                        "rounds_used": 2,
                        "retained_hard_dissent": True,
                        "risk_review_required": True,
                        "consensus_score": 0.75,
                        "action_conviction": 0.6,
                    },
                    "core_disputes": [
                        {
                            "title": "资产质量修复是否足以抵消估值低位",
                            "why_it_matters": "如果资产质量没有确认修复，低估值可能是价值陷阱，不能直接进入 S4 决策。",
                            "involved_roles": ["基本面分析师", "量化分析师", "CIO"],
                            "current_conclusion": "补证前不能进入 S4，先保留 S3 阻断。",
                            "required_evidence": ["不良率趋势", "拨备覆盖率趋势", "息差改善证据"],
                        }
                    ],
                    "view_change_details": [
                        {
                            "role": "量化分析师",
                            "before": "偏正面",
                            "after": "观察",
                            "reason": "基本面补证不足，量价信号不能单独推动 S4。",
                            "impact": "降低行动强度，等待基本面补证后再评估。",
                        },
                        {
                            "role": "基本面分析师",
                            "before": "中性",
                            "after": "维持硬异议",
                            "reason": "资产质量、拨备覆盖率和息差趋势证据不足。",
                            "impact": "保留 S3 阻断，不能进入 S4。",
                        },
                        {
                            "role": "宏观分析师",
                            "before": "偏正面",
                            "after": "不阻断",
                            "reason": "宏观环境未构成反对理由，但不能替代个股资产质量补证。",
                            "impact": "只作为支撑背景，不推动 S4。",
                        },
                        {
                            "role": "事件分析师",
                            "before": "中性",
                            "after": "维持中性",
                            "reason": "暂无强催化，公告和监管信息未形成放行依据。",
                            "impact": "继续跟踪公告，不推动 S4。",
                        },
                    ],
                    "retained_dissent_details": [
                        {
                            "source_role": "基本面分析师",
                            "dissent": "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。",
                            "counter_risks": ["不良率拐点未确认", "拨备覆盖率可能继续承压", "息差修复慢于预期"],
                            "handling": "保留硬异议，补证后交风控复核。",
                            "forbidden_actions": ["不能直接放行 S4", "不能进入 S6 执行"],
                        }
                    ],
                    "round_details": [
                        {
                            "round_no": 1,
                            "issue": "资产质量修复是否成立",
                            "participants": ["CIO", "基本面分析师", "量化分析师"],
                            "input_evidence": ["不良率趋势", "拨备覆盖率"],
                            "outcome": "要求补充不良率和拨备证据",
                            "unresolved_questions": ["资产质量修复证据是否足够"],
                        },
                        {
                            "round_no": 2,
                            "issue": "补证后是否能进入 S4",
                            "participants": ["CIO", "基本面分析师", "量化分析师"],
                            "input_evidence": ["息差趋势", "估值分位"],
                            "outcome": "CIO 维持 S3 受阻",
                            "unresolved_questions": ["补证后是否足以解除基本面硬异议"],
                        },
                    ],
                    "next_actions": [
                        {
                            "action": "补齐资产质量、拨备覆盖率和息差趋势证据",
                            "owner": "基本面分析师",
                            "completion_signal": "形成可复核补证包并更新硬异议判断",
                            "next_stage": "交风控复核后再判断是否进入 S4",
                        }
                    ],
                    "resolved_issues": ["执行数据不足仅作为 S6 成交门槛处理"],
                    "unresolved_dissent": ["基本面硬异议仍保留"],
                    "chair_recommendation_for_next_stage": "reopen_s3_with_evidence_then_risk_review",
                    "semantic_lead_signature": "cio",
                    "rounds": [
                        {"round_no": 1, "issue": "资产质量修复是否成立", "outcome": "要求补充不良率和拨备证据"},
                        {"round_no": 2, "issue": "补证后是否能进入 S4", "outcome": "CIO synthesis 维持 S3 受阻"},
                    ],
                    "summary": "S3 辩论保留基本面硬异议，需补齐资产质量证据并交风控复核。",
                },
                now,
            ),
            _seed_artifact(
                "artifact-wf001-decision-guard",
                "DecisionGuardResult",
                "risk_engine",
                "service",
                "S4",
                {
                    "major_deviation": False,
                    "low_action_conviction": False,
                    "retained_hard_dissent": True,
                    "reason_codes": ["retained_hard_dissent_risk_review"],
                    "owner_exception_candidate_ref": None,
                    "reopen_recommendation_ref": "reopen-wf001-s3",
                },
                now,
            ),
            _seed_artifact(
                "artifact-wf001-risk-review",
                "RiskReviewReport",
                "risk_officer",
                "agent",
                "S5",
                {
                    "review_result": "blocked",
                    "repairability": "reopen_s3_debate",
                    "owner_exception_required": False,
                    "reason_codes": ["retained_hard_dissent_risk_review", "execution_core_blocked_no_trade"],
                    "risk_summary": "S3 仍有硬异议，必须补证；执行数据不足只约束 S6 纸面成交。",
                },
                now,
            ),
            _seed_artifact(
                "artifact-wf001-paper-execution",
                "PaperExecutionReceipt",
                "trade_execution",
                "service",
                "S6",
                {
                    "paper_order_id": "paper-order-wf001",
                    "decision_memo_ref": "decision-wf001",
                    "pricing_method": "not_released",
                    "fill_status": "blocked",
                    "reason_code": "execution_core_blocked_no_trade",
                    "fees": {},
                    "taxes": {},
                    "slippage": {},
                    "t_plus_one_state": "not_started",
                },
                now,
            ),
        ]
        self.gateway.artifact_ledger.extend([artifact for artifact in artifacts if artifact["artifact_id"] not in existing])

    def _seed_wf001_process(self) -> None:
        if "wf-001" not in self.workflow.workflows:
            return
        now = utc_now()
        if "run-wf001-cio-s3" not in self.agent_runs:
            self.agent_runs["run-wf001-cio-s3"] = replace(
                AgentRun.fake(
                    agent_run_id="run-wf001-cio-s3",
                    agent_id="cio",
                    workflow_id="wf-001",
                    allowed_command_types=["request_evidence", "request_risk_impact_review"],
                    output_artifact_schema="DebateSummary",
                    stage="S3",
                ),
                run_goal="CIO 汇总四位分析师 Memo，追问基本面硬异议并形成 S3 辩论摘要。",
                status="completed",
            )
        if "run-wf001-fundamental-s3" not in self.agent_runs:
            self.agent_runs["run-wf001-fundamental-s3"] = replace(
                AgentRun.fake(
                    agent_run_id="run-wf001-fundamental-s3",
                    agent_id="fundamental_analyst",
                    workflow_id="wf-001",
                    allowed_command_types=["request_evidence"],
                    output_artifact_schema="AnalystMemo",
                    stage="S3",
                ),
                parent_run_id="run-wf001-cio-s3",
                run_goal="基本面分析师补充资产质量、拨备覆盖率和息差证据，说明硬异议依据。",
                status="completed",
            )
        existing_events = {event.event_id for event in self.gateway.event_ledger}
        events = [
            CollaborationEvent(
                event_id="event-wf001-s3-question",
                event_type="question_asked",
                workflow_id="wf-001",
                attempt_no=1,
                trace_id="trace-wf001-s3-question",
                payload={
                    "business_summary": "CIO 追问资产质量修复是否足以抵消估值低位。",
                    "issue": "资产质量修复是否足以抵消估值低位",
                },
                created_at=now,
                agent_run_id="run-wf001-cio-s3",
            ),
            CollaborationEvent(
                event_id="event-wf001-s3-view-change",
                event_type="view_update",
                workflow_id="wf-001",
                attempt_no=1,
                trace_id="trace-wf001-s3-view-change",
                payload={
                    "business_summary": "量化观点由偏正面降为观察；基本面硬异议仍保留。",
                    "view_change": "量化观点由偏正面降为观察",
                },
                created_at=now,
                agent_run_id="run-wf001-fundamental-s3",
                artifact_id="artifact-wf001-debate-summary",
            ),
            CollaborationEvent(
                event_id="event-wf001-s3-risk-handoff",
                event_type="handoff_created",
                workflow_id="wf-001",
                attempt_no=1,
                trace_id="trace-wf001-s3-risk-handoff",
                payload={
                    "business_summary": "CIO 将保留的基本面硬异议交给风控复核。",
                    "handoff_ref": "handoff-wf001-s3-risk-review",
                },
                created_at=now,
                agent_run_id="run-wf001-cio-s3",
                artifact_id="artifact-wf001-debate-summary",
            ),
        ]
        self.gateway.event_ledger.extend([event for event in events if event.event_id not in existing_events])
        existing_handoffs = {handoff.handoff_id for handoff in self.gateway.handoff_ledger}
        if "handoff-wf001-s3-risk-review" not in existing_handoffs:
            self.gateway.handoff_ledger.append(
                HandoffPacket(
                    handoff_id="handoff-wf001-s3-risk-review",
                    workflow_id="wf-001",
                    attempt_no=1,
                    from_stage="S3",
                    to_stage_or_agent="risk_officer",
                    producer_agent_id_or_service="cio",
                    source_artifact_refs=["artifact-wf001-debate-summary", "artifact-wf001-fundamental-memo"],
                    summary="基本面硬异议仍保留：资产质量修复证据不足，需要补齐不良率、拨备覆盖率和息差趋势后由风控复核。",
                    created_at=now,
                    open_questions=["资产质量修复是否足以抵消估值低位？"],
                    blockers=["基本面硬异议保留", "需补齐资产质量与息差证据"],
                    decisions_made=["S3 暂不放行到 S4", "S6 执行数据不足只作为成交门槛"],
                )
            )


def _seed_memo(role: str, direction: str, confidence: float, hard_dissent: bool) -> dict[str, Any]:
    role_copy = {
        "macro": {
            "thesis": "利率环境和信用扩张对银行估值有支撑，但宏观修复仍偏温和。",
            "supporting": ["source-wf001-macro-credit"],
            "counter": ["source-wf001-macro-demand"],
            "risks": ["信用扩张弱于预期"],
            "conditions": ["社融增速保持稳定", "地产信用风险不再扩散"],
            "invalidations": ["信用利差重新走阔"],
            "implication": "宏观观点支持继续论证，但不构成成交授权。",
            "payload": {"credit_cycle": "mild_support", "policy_bias": "supportive"},
            "highlights": ["宏观环境温和支持", "信用扩张仍需观察"],
        },
        "fundamental": {
            "thesis": "估值低位不能单独支持推进，需要看到资产质量和息差同时改善。",
            "supporting": ["artifact-wf001-data-readiness"],
            "counter": ["source-wf001-fundamental-npl", "source-wf001-fundamental-nim"],
            "risks": ["不良率拐点未确认", "息差修复慢于预期"],
            "conditions": ["补齐最近两个季度不良率、拨备覆盖率和息差趋势后再进入 S4"],
            "invalidations": ["不良率继续上行或拨备覆盖率继续下降"],
            "implication": "S3 先补证，保留硬异议并交风控复核。",
            "payload": {"asset_quality": "insufficient", "valuation_gap": "needs_confirmation"},
            "highlights": ["资产质量修复证据不足", "需要补充不良率、拨备覆盖率和息差趋势"],
        },
        "quant": {
            "thesis": "估值和量价因子偏正面，但硬异议存在时只能作为支撑证据。",
            "supporting": ["source-wf001-quant-factor"],
            "counter": ["source-wf001-quant-volatility"],
            "risks": ["短期波动放大"],
            "conditions": ["基本面补证后因子信号仍保持正向"],
            "invalidations": ["量价信号转弱且波动继续放大"],
            "implication": "量化观点降为观察，等待 S3 补证结果。",
            "payload": {"factor_signal": "positive", "volatility": "elevated"},
            "highlights": ["因子信号偏正面", "辩论后降为观察"],
        },
        "event": {
            "thesis": "近期事件未形成明确负面冲击，但仍需要跟踪公告和监管信息。",
            "supporting": ["source-wf001-event-announcement"],
            "counter": ["source-wf001-event-regulatory"],
            "risks": ["公告或监管信息带来短期扰动"],
            "conditions": ["公告风险未扩大"],
            "invalidations": ["新增重大负面公告"],
            "implication": "事件观点保持中性，配合基本面补证。",
            "payload": {"announcement_risk": "watch", "regulatory_signal": "neutral"},
            "highlights": ["事件冲击暂未扩大", "继续跟踪公告和监管信息"],
        },
    }[role]
    hard_dissent_reason = (
        "资产质量修复证据不足，拨备和息差改善还没有形成可执行结论。"
        if hard_dissent
        else None
    )
    direction_score = {"positive": 2, "neutral": 0, "negative": -2}.get(direction, 0)
    return {
        "memo_id": f"memo-wf001-{role}",
        "workflow_id": "wf-001",
        "attempt_no": 1,
        "analyst_id": f"{role}_analyst" if role != "event" else "event_analyst",
        "role": role,
        "context_snapshot_id": "ctx-v1",
        "decision_question": "是否值得围绕浦发银行进入完整 IC 论证",
        "direction": direction,
        "direction_score": direction_score,
        "confidence": confidence,
        "evidence_quality": 0.62 if role == "fundamental" else 0.76,
        "hard_dissent": hard_dissent,
        "hard_dissent_reason": hard_dissent_reason,
        "thesis": role_copy["thesis"],
        "supporting_evidence_refs": role_copy["supporting"],
        "counter_evidence_refs": role_copy["counter"],
        "key_risks": role_copy["risks"],
        "applicable_conditions": role_copy["conditions"],
        "invalidation_conditions": role_copy["invalidations"],
        "suggested_action_implication": role_copy["implication"],
        "role_payload": role_copy["payload"],
        "highlights": role_copy["highlights"],
        "summary": "保留硬异议，进入 S3 补证。" if hard_dissent else "可进入后续论证，但不构成成交授权。",
        "evidence_refs": [*role_copy["supporting"], *role_copy["counter"]],
    }


def _seed_artifact(
    artifact_id: str,
    artifact_type: str,
    producer: str,
    producer_type: str,
    stage: str,
    payload: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "workflow_id": "wf-001",
        "attempt_no": 1,
        "trace_id": f"trace-{artifact_id}",
        "producer": producer,
        "producer_type": producer_type,
        "status": "accepted",
        "schema_version": "1.0.0",
        "payload": payload,
        "source_refs": payload.get("evidence_refs", []),
        "summary": str(payload.get("summary") or payload.get("risk_summary") or payload.get("reason_code") or ""),
        "evidence_refs": payload.get("evidence_refs", []),
        "decision_refs": [],
        "created_at": created_at,
        "stage": stage,
    }


def _request_brief_read_model(brief: RequestBrief) -> dict[str, Any]:
    return {
        "brief_id": brief.brief_id,
        "raw_input_ref": brief.raw_input_ref,
        "route_type": brief.route_type,
        "route_confidence": brief.route_confidence,
        "asset_scope": brief.asset_scope,
        "authorization_boundary": brief.authorization_boundary,
        "owner_confirmation_status": brief.owner_confirmation_status,
        "route_reason": brief.route_reason,
        "created_at": brief.created_at,
        "suggested_semantic_lead": brief.suggested_semantic_lead,
        "process_authority": brief.process_authority,
        "predicted_outputs": list(brief.predicted_outputs),
        "creates_agent_run": brief.creates_agent_run,
        "forbidden_action_reason_code": brief.forbidden_action_reason_code,
        "version": 1,
    }


def _task_read_model(task, workflow_id: str | None = None) -> dict[str, Any]:
    payload = {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "priority": task.priority,
        "owner_role": task.owner_role,
        "current_state": task.current_state,
        "reason_code": task.reason_code,
        "artifact_refs": list(task.artifact_refs),
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "blocked_reason": task.blocked_reason,
        "closed_at": task.closed_at,
    }
    if workflow_id is not None:
        payload["workflow_id"] = workflow_id
    return payload


def _workflow_read_model(workflow) -> dict[str, Any]:
    return {
        "workflow_id": workflow.workflow_id,
        "task_id": workflow.task_id,
        "workflow_type": workflow.workflow_type,
        "current_stage": workflow.current_stage,
        "current_attempt_no": workflow.current_attempt_no,
        "status": workflow.status,
        "context_snapshot_id": workflow.context_snapshot_id,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "stages": [
            {
                "workflow_id": stage.workflow_id,
                "attempt_no": stage.attempt_no,
                "stage": stage.stage,
                "node_status": stage.node_status,
                "responsible_role": stage.responsible_role,
                "input_artifact_refs": list(stage.input_artifact_refs),
                "output_artifact_refs": list(stage.output_artifact_refs),
                "reason_code": stage.reason_code,
                "started_at": stage.started_at,
                "completed_at": stage.completed_at,
                "stage_version": stage.stage_version,
            }
            for stage in workflow.stages
        ],
    }


def _stage_read_model(stage) -> dict[str, Any]:
    return {
        "workflow_id": stage.workflow_id,
        "attempt_no": stage.attempt_no,
        "stage": stage.stage,
        "node_status": stage.node_status,
        "responsible_role": stage.responsible_role,
        "input_artifact_refs": list(stage.input_artifact_refs),
        "output_artifact_refs": list(stage.output_artifact_refs),
        "reason_code": stage.reason_code,
        "started_at": stage.started_at,
        "completed_at": stage.completed_at,
        "stage_version": stage.stage_version,
    }


def _workflow_stage_by_name(workflow, stage_name: str):
    return next((stage for stage in workflow.stages if stage.stage == stage_name), None)


def _workflow_command_result(command_type: str, stage, *, object_type: str = "workflow_stage", object_id: str | None = None) -> dict[str, Any]:
    return {
        "accepted": True,
        "command_type": command_type,
        "object_type": object_type,
        "object_id": object_id or f"{stage.workflow_id}:{stage.stage}:{stage.stage_version}",
        "stage": _stage_read_model(stage),
        "reason_code": stage.reason_code,
        "trace_id": new_id("trace"),
    }


def _workflow_artifacts(api_runtime: ApiRuntime, workflow_id: str) -> list[dict[str, Any]]:
    artifacts_by_id: dict[str, dict[str, Any]] = {}
    if api_runtime.gateway.store is not None:
        for artifact in api_runtime.gateway.store.list_artifacts(workflow_id):
            artifacts_by_id[artifact["artifact_id"]] = artifact
    for artifact in api_runtime.gateway.artifact_ledger:
        if artifact.get("workflow_id") == workflow_id:
            artifacts_by_id[artifact["artifact_id"]] = artifact
    return list(artifacts_by_id.values())


def _first_payload(artifacts: list[dict[str, Any]], artifact_type: str) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_type") == artifact_type and isinstance(artifact.get("payload"), dict):
            return artifact["payload"]
    return None


def _first_artifact_payload_with_ref(artifacts: list[dict[str, Any]], artifact_type: str) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_type") == artifact_type and isinstance(artifact.get("payload"), dict):
            payload = dict(artifact["payload"])
            payload["artifact_ref"] = artifact["artifact_id"]
            return payload
    return None


def _artifact_projection(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    ic_context = _first_artifact_payload_with_ref(artifacts, "ICContextPackage")
    chair_brief = _first_artifact_payload_with_ref(artifacts, "ICChairBrief")
    data_readiness = _first_payload(artifacts, "DataReadinessReport")
    decision_guard = _first_payload(artifacts, "DecisionGuardResult")
    risk_review = _first_payload(artifacts, "RiskReviewReport")
    paper_execution = _first_payload(artifacts, "PaperExecutionReceipt")
    position_disposal = _first_artifact_payload_with_ref(artifacts, "PositionDisposalTask")
    attribution = _first_payload(artifacts, "AttributionReport")
    debate_summary = _first_payload(artifacts, "DebateSummary")
    analyst_memos = [
        {**artifact["payload"], "artifact_ref": artifact["artifact_id"]}
        for artifact in artifacts
        if artifact.get("artifact_type") == "AnalystMemo" and isinstance(artifact.get("payload"), dict)
    ]
    return {
        "artifact_refs": [artifact["artifact_id"] for artifact in artifacts],
        "ic_context": ic_context,
        "chair_brief": chair_brief,
        "data_readiness": data_readiness,
        "analyst_stance_matrix": [
            {
                "role": memo.get("role", "analyst"),
                "direction": memo.get("direction", str(memo.get("direction_score", "pending"))),
                "direction_score": memo.get("direction_score"),
                "confidence": memo.get("confidence", 0),
                "evidence_quality": memo.get("evidence_quality"),
                "hard_dissent": bool(memo.get("hard_dissent", False)),
                "hard_dissent_reason": memo.get("hard_dissent_reason"),
                "thesis": memo.get("thesis"),
                "view_update_refs": memo.get("supporting_evidence_refs", []) + memo.get("counter_evidence_refs", []),
                "artifact_ref": memo.get("artifact_ref"),
            }
            for memo in analyst_memos
        ],
        "role_payload_drilldowns": [
            {
                "role": memo.get("role", "analyst"),
                "highlights": memo.get("highlights") or [
                    value
                    for value in [
                        memo.get("thesis"),
                        memo.get("hard_dissent_reason"),
                        memo.get("suggested_action_implication"),
                    ]
                    if value
                ],
                "hard_dissent_reason": memo.get("hard_dissent_reason"),
                "thesis": memo.get("thesis"),
                "supporting_evidence_refs": memo.get("supporting_evidence_refs", []),
                "counter_evidence_refs": memo.get("counter_evidence_refs", []),
                "key_risks": memo.get("key_risks", []),
                "applicable_conditions": memo.get("applicable_conditions", []),
                "invalidation_conditions": memo.get("invalidation_conditions", []),
                "suggested_action_implication": memo.get("suggested_action_implication"),
                "role_payload": memo.get("role_payload", {}),
                "artifact_ref": memo.get("artifact_ref"),
            }
            for memo in analyst_memos
        ],
        "debate": debate_summary,
        "decision_guard": decision_guard,
        "risk_review": risk_review,
        "paper_execution": paper_execution,
        "position_disposal": position_disposal,
        "attribution": attribution,
    }


def _owner_source_quality(ref: str) -> dict[str, str]:
    if ref.startswith("tencent-public-kline"):
        return {
            "source": "腾讯公开日线行情",
            "used_for": "支持判断：是否值得继续分析浦发银行",
            "quality": "可用于研究判断",
        }
    return {
        "source": ref,
        "used_for": "支持当前研究判断",
        "quality": "已接入，需结合质量结果判断",
    }


def _owner_conflict_refs(data_readiness: dict[str, Any]) -> list[str]:
    conflicts: list[str] = []
    for issue in data_readiness.get("issues", []):
        if "分钟" in issue and "执行" in issue:
            conflicts.append("分钟级成交数据缺失")
        elif issue:
            conflicts.append(str(issue))
    return conflicts


_DATA_FIELD_LABELS = {
    "symbol": "标的代码",
    "trade_date": "交易日",
    "close": "收盘价",
    "volume": "成交量",
    "source_timestamp": "来源时间戳",
    "last_price": "最新成交价",
    "order_book_depth": "盘口深度",
    "execution_window": "可成交窗口",
}


def _owner_data_field_label(field_name: str) -> str:
    return _DATA_FIELD_LABELS.get(field_name, field_name)


def _owner_source_name(source_ref: str, usage: str) -> str:
    if source_ref.startswith("tencent-public-kline"):
        return "腾讯公开日线行情"
    if source_ref.startswith("execution-core"):
        return "实时执行行情"
    if usage == "execution_core":
        return "实时执行行情"
    return source_ref or "未返回数据来源"


def _owner_quality_label(status: str, usage: str) -> str:
    if status == "available":
        return "可用于成交判断" if usage == "execution_core" else "可用于研究判断"
    if status == "partial":
        return "部分字段可用，需补齐后复核"
    if usage == "execution_core":
        return "缺失，不能用于成交"
    return "采集失败"


def _owner_source_status_from_request(
    request: dict[str, Any],
    *,
    lineage_refs: list[str],
    index: int,
) -> dict[str, Any]:
    usage = str(request.get("required_usage") or "research")
    source_ref = str(request.get("source_ref") or (lineage_refs[index] if index < len(lineage_refs) else request.get("request_id") or ""))
    requested_fields: list[str] = []
    obtained_fields: list[str] = []
    missing_fields: list[str] = []
    for raw_field in request.get("required_fields", []):
        if isinstance(raw_field, dict):
            field_name = str(raw_field.get("name", ""))
            if not field_name:
                continue
            label = _owner_data_field_label(field_name)
            requested_fields.append(label)
            if bool(raw_field.get("present")) and bool(raw_field.get("valid")):
                obtained_fields.append(label)
            else:
                missing_fields.append(label)
        else:
            label = _owner_data_field_label(str(raw_field))
            requested_fields.append(label)
            obtained_fields.append(label)

    if requested_fields and not missing_fields:
        status = "available"
    elif obtained_fields:
        status = "partial"
    elif usage == "execution_core":
        status = "missing"
    else:
        status = "failed"

    return {
        "source_name": str(request.get("source_name") or _owner_source_name(source_ref, usage)),
        "source_ref": source_ref,
        "required_usage": usage,
        "requested_fields": requested_fields,
        "obtained_fields": obtained_fields,
        "missing_fields": missing_fields,
        "status": status,
        "quality_label": str(request.get("quality_label") or _owner_quality_label(status, usage)),
        "evidence_ref": str(request.get("evidence_ref") or source_ref or request.get("request_id") or ""),
    }


def _owner_source_status_from_lineage(ref: str) -> dict[str, Any]:
    return {
        "source_name": _owner_source_name(ref, "decision_core"),
        "source_ref": ref,
        "required_usage": "decision_core",
        "requested_fields": [],
        "obtained_fields": [],
        "missing_fields": [],
        "status": "available",
        "quality_label": "已接入，需结合质量结果判断",
        "evidence_ref": ref,
    }


def _owner_data_gap_from_source(source: dict[str, Any], issues: list[str]) -> dict[str, str] | None:
    if source["status"] == "available":
        return None
    usage = source["required_usage"]
    source_name = source["source_name"]
    if usage == "execution_core":
        return {
            "gap": "实时执行行情缺失",
            "affects_stage": "S6",
            "impact": "不能生成纸面成交授权，不影响当前 S3 硬异议判断。",
            "next_action": "进入 S6 前重新采集最新成交价、盘口深度和可成交窗口，并由风控复核。",
        }
    issue = str(issues[0]) if issues else f"{source_name}未返回可用数据。"
    return {
        "gap": issue,
        "affects_stage": "S1",
        "impact": "无法形成研究判断或进入后续分析。",
        "next_action": f"重试{source_name}，并补充公告/财报来源。",
    }


def _owner_data_readiness_projection(data_readiness: dict[str, Any]) -> dict[str, Any]:
    projected = dict(data_readiness)
    lineage_refs = [str(ref) for ref in projected.get("lineage_refs", [])]
    raw_requests = [item for item in projected.get("data_requests", []) if isinstance(item, dict)]
    source_status = [
        _owner_source_status_from_request(request, lineage_refs=lineage_refs, index=index)
        for index, request in enumerate(raw_requests)
    ]
    if not source_status:
        source_status = [_owner_source_status_from_lineage(ref) for ref in lineage_refs]

    issues = [str(issue) for issue in projected.get("issues", [])]
    data_gaps = [
        gap
        for source in source_status
        for gap in [_owner_data_gap_from_source(source, issues)]
        if gap is not None
    ]
    if not data_gaps:
        data_gaps = [
            {
                "gap": issue,
                "affects_stage": "S6" if "执行" in issue else "S1",
                "impact": "不能生成纸面成交授权，不影响当前 S3 硬异议判断。" if "执行" in issue else "需要补齐后才能形成研究判断。",
                "next_action": "进入 S6 前重新采集执行数据，并由风控复核。" if "执行" in issue else "重试数据源并补充可验证来源。",
            }
            for issue in issues
        ]

    usable_sources = [source for source in source_status if source["status"] in {"available", "partial"} and source["obtained_fields"]]
    if not usable_sources:
        owner_summary = "本轮 S1 没有成功获取可用数据。"
    elif projected.get("decision_core_status") == "pass" and projected.get("execution_core_status") == "blocked":
        owner_summary = "S1 已拿到可用于研究的数据；成交前还缺 S6 执行核心数据。"
    else:
        owner_summary = "S1 数据已形成后端复核结果，请按缺口继续补证。"

    projected["owner_summary"] = str(projected.get("owner_summary") or owner_summary)
    projected["source_status"] = projected.get("source_status") or source_status
    projected["data_gaps"] = projected.get("data_gaps") or data_gaps
    return projected


def _apply_artifact_projection(dossier: dict[str, Any], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    projection = _artifact_projection(artifacts)
    if projection["data_readiness"] is not None:
        raw_data_readiness = projection["data_readiness"]
        dossier["data_readiness"] = {
            **dossier["data_readiness"],
            **raw_data_readiness,
        }
        for owner_projection_key in ("owner_summary", "source_status", "data_gaps"):
            if owner_projection_key not in raw_data_readiness:
                dossier["data_readiness"].pop(owner_projection_key, None)
        dossier["data_readiness"] = _owner_data_readiness_projection(dossier["data_readiness"])
        lineage_refs = dossier["data_readiness"].get("lineage_refs", [])
        if lineage_refs:
            dossier["evidence_map"] = {
                **dossier["evidence_map"],
                "data_refs": list(dict.fromkeys([*dossier["evidence_map"].get("data_refs", []), *lineage_refs])),
                "source_quality": [_owner_source_quality(ref) for ref in lineage_refs],
                "conflict_refs": _owner_conflict_refs(dossier["data_readiness"]),
            }
    if projection["ic_context"] is not None:
        dossier["ic_context"] = {
            "status": "ready",
            **projection["ic_context"],
        }
    if projection["chair_brief"] is not None:
        dossier["chair_brief"] = {
            **dossier["chair_brief"],
            **projection["chair_brief"],
        }
    if projection["analyst_stance_matrix"]:
        dossier["analyst_stance_matrix"] = projection["analyst_stance_matrix"]
        dossier["role_payload_drilldowns"] = projection["role_payload_drilldowns"]
        hard_dissent = any(row["hard_dissent"] for row in projection["analyst_stance_matrix"])
        dossier["consensus"] = {
            "consensus_score": 1.0 if not hard_dissent else 0.75,
            "action_conviction": 0.6 if hard_dissent else 0.82,
            "status": "ready",
        }
        dossier["debate"] = {
            "debate_required": hard_dissent,
            "rounds": [],
            "retained_hard_dissent": hard_dissent,
        }
    if projection["debate"] is not None:
        dossier["debate"] = {
            "debate_required": bool(projection["debate"].get("hard_dissent_present", True)),
            "rounds": projection["debate"].get("rounds", []),
            "rounds_used": projection["debate"].get("rounds_used", 0),
            "issues": projection["debate"].get("issues", []),
            "view_changes": projection["debate"].get("view_changes", []),
            "cio_synthesis": projection["debate"].get("synthesis") or projection["debate"].get("cio_synthesis"),
            "retained_hard_dissent": bool(projection["debate"].get("retained_hard_dissent", False)),
            "unresolved_dissent": projection["debate"].get("unresolved_dissent", []),
            "risk_review_required": bool(projection["debate"].get("risk_review_required", False)),
            "new_evidence_refs": projection["debate"].get("new_evidence_refs", []),
            "chair_recommendation_for_next_stage": projection["debate"].get("chair_recommendation_for_next_stage"),
            "stop_reason": projection["debate"].get("stop_reason"),
            "owner_summary": projection["debate"].get("owner_summary") or projection["debate"].get("synthesis"),
            "status_summary": projection["debate"].get("status_summary") or {
                "rounds_used": projection["debate"].get("rounds_used", 0),
                "retained_hard_dissent": bool(projection["debate"].get("retained_hard_dissent", False)),
                "risk_review_required": bool(projection["debate"].get("risk_review_required", False)),
                "consensus_score": projection["debate"].get("recomputed_consensus_score"),
                "action_conviction": projection["debate"].get("recomputed_action_conviction"),
            },
            "core_disputes": projection["debate"].get("core_disputes", []),
            "view_change_details": projection["debate"].get("view_change_details", []),
            "retained_dissent_details": projection["debate"].get("retained_dissent_details", []),
            "round_details": projection["debate"].get("round_details", []),
            "next_actions": projection["debate"].get("next_actions", []),
        }
        dossier["consensus"] = {
            **dossier["consensus"],
            "consensus_score": projection["debate"].get("recomputed_consensus_score", dossier["consensus"].get("consensus_score")),
            "action_conviction": projection["debate"].get("recomputed_action_conviction", dossier["consensus"].get("action_conviction")),
            "status": "ready",
        }
    if projection["decision_guard"] is not None:
        reason_codes = projection["decision_guard"].get("reason_codes", [])
        dossier["decision_service"] = {"status": "pass" if not reason_codes else "blocked", "reason_codes": reason_codes}
        dossier["decision_guard"] = {
            "status": "pass" if not reason_codes else "blocked",
            "owner_exception_or_reopen": projection["decision_guard"].get("owner_exception_candidate_ref")
            or projection["decision_guard"].get("reopen_recommendation_ref"),
            **projection["decision_guard"],
        }
    if projection["risk_review"] is not None:
        dossier["risk_review"] = {
            "status": projection["risk_review"].get("review_result", "pending"),
            "verdict": projection["risk_review"].get("review_result"),
            **projection["risk_review"],
        }
    if projection["paper_execution"] is not None:
        dossier["paper_execution"] = {
            "status": projection["paper_execution"].get("fill_status", "pending"),
            "reason_code": projection["paper_execution"].get("reason_code"),
            **projection["paper_execution"],
        }
    if projection["position_disposal"] is not None:
        dossier["position_disposal"] = {
            "status": "requires_risk_review",
            **projection["position_disposal"],
        }
    if projection["attribution"] is not None:
        dossier["attribution"] = {
            "status": projection["attribution"].get("status", "completed"),
            **projection["attribution"],
        }
    if projection["artifact_refs"]:
        dossier["evidence_map"] = {
            **dossier["evidence_map"],
            "artifact_refs": sorted(set(dossier["evidence_map"]["artifact_refs"]) | set(projection["artifact_refs"])),
        }
    return dossier


def _investment_dossier_read_model(api_runtime: ApiRuntime, workflow) -> dict[str, Any]:
    task = api_runtime.workflow.tasks.get(workflow.task_id)
    handoffs = [
        _serialize(handoff)
        for handoff in api_runtime.gateway.handoff_ledger
        if handoff.workflow_id == workflow.workflow_id
    ]
    stage_rail = [
        {
            "stage": stage.stage,
            "node_status": stage.node_status,
            "responsible_role": stage.responsible_role,
            "reason_code": stage.reason_code,
            "artifact_count": len(stage.output_artifact_refs),
            "reopen_marker": any(event.target_stage == stage.stage for event in api_runtime.workflow.reopen_events),
            "stage_version": stage.stage_version,
        }
        for stage in workflow.stages
    ]
    dossier = {
        "workflow": {
            "workflow_id": workflow.workflow_id,
            "task_id": workflow.task_id,
            "workflow_type": workflow.workflow_type,
            "title": api_runtime.workflow_titles.get(workflow.workflow_id, "A 股投研流程"),
            "current_stage": workflow.current_stage,
            "state": workflow.status,
            "current_attempt_no": workflow.current_attempt_no,
            "context_snapshot_id": workflow.context_snapshot_id,
        },
        "stage_rail": stage_rail,
        "request_brief": _task_read_model(task) if task is not None else None,
        "data_readiness": {
            "quality_band": "pending",
            "decision_core_status": "pending",
            "execution_core_status": "blocked",
            "reason_code": "execution_core_blocked_no_trade",
            "issues": ["S1 尚未返回可用数据。"],
            "lineage_refs": [],
            "owner_summary": "本轮 S1 没有成功获取可用数据。",
            "source_status": [],
            "data_gaps": [
                {
                    "gap": "S1 尚未返回可用数据。",
                    "affects_stage": "S1",
                    "impact": "无法形成研究判断或进入后续分析。",
                    "next_action": "启动或重试 S1 数据采集，并补齐可验证来源。",
                }
            ],
        },
        "ic_context": {"context_snapshot_id": workflow.context_snapshot_id, "status": "pending"},
        "chair_brief": {
            "decision_question": "等待数据和分析师产物补齐后再形成正式研究问题",
            "key_tensions": [],
            "no_preset_decision_attestation": True,
        },
        "analyst_stance_matrix": [],
        "role_payload_drilldowns": [],
        "consensus": {"consensus_score": None, "action_conviction": None, "status": "pending"},
        "debate": {"debate_required": False, "rounds": [], "retained_hard_dissent": False},
        "decision_service": {"status": "pending", "reason_codes": []},
        "cio_decision": {"status": "pending"},
        "decision_packet": {"status": "pending", "evidence_refs": []},
        "decision_guard": {"status": "pending", "owner_exception_or_reopen": None},
        "optimizer_deviation": {"status": "pending"},
        "risk_review": {"status": "pending", "verdict": None},
        "approval": {"status": "not_required", "approval_id": None},
        "paper_execution": {"status": "blocked", "reason_code": "execution_core_blocked_no_trade"},
        "position_disposal": {"status": "not_required"},
        "attribution": {"status": "pending"},
        "handoffs": handoffs,
        "evidence_map": {
            "artifact_refs": [ref for stage in workflow.stages for ref in stage.output_artifact_refs],
            "data_refs": [],
            "source_quality": [],
            "conflict_refs": [],
            "supporting_evidence_only_refs": [],
        },
        "forbidden_actions": {
            "risk_rejected_no_override": {"action_visible": False, "reason_code": "risk_rejected_no_override"},
            "execution_core_blocked_no_trade": {"action_visible": False, "reason_code": "execution_core_blocked_no_trade"},
            "non_a_asset_no_trade": {"action_visible": False, "reason_code": "non_a_asset_no_trade"},
            "low_action_no_execution": {"action_visible": False, "reason_code": "low_action_no_execution"},
        },
    }
    return _apply_artifact_projection(dossier, _workflow_artifacts(api_runtime, workflow.workflow_id))


def _investment_dossier_from_workflow_payload(
    workflow: dict[str, Any],
    *,
    task: dict[str, Any] | None,
    handoffs: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    stages = workflow.get("stages", [])
    dossier = {
        "workflow": {
            "workflow_id": workflow["workflow_id"],
            "task_id": workflow["task_id"],
            "workflow_type": workflow["workflow_type"],
            "title": "A 股投研流程",
            "current_stage": workflow["current_stage"],
            "state": workflow["status"],
            "current_attempt_no": workflow["current_attempt_no"],
            "context_snapshot_id": workflow["context_snapshot_id"],
        },
        "stage_rail": [
            {
                "stage": stage["stage"],
                "node_status": stage["node_status"],
                "responsible_role": stage["responsible_role"],
                "reason_code": stage["reason_code"],
                "artifact_count": len(stage["output_artifact_refs"]),
                "reopen_marker": False,
                "stage_version": stage["stage_version"],
            }
            for stage in stages
        ],
        "request_brief": task,
        "data_readiness": {
            "quality_band": "pending",
            "decision_core_status": "pending",
            "execution_core_status": "blocked",
            "reason_code": "execution_core_blocked_no_trade",
            "issues": ["S1 尚未返回可用数据。"],
            "lineage_refs": [],
            "owner_summary": "本轮 S1 没有成功获取可用数据。",
            "source_status": [],
            "data_gaps": [
                {
                    "gap": "S1 尚未返回可用数据。",
                    "affects_stage": "S1",
                    "impact": "无法形成研究判断或进入后续分析。",
                    "next_action": "启动或重试 S1 数据采集，并补齐可验证来源。",
                }
            ],
        },
        "ic_context": {"context_snapshot_id": workflow["context_snapshot_id"], "status": "pending"},
        "chair_brief": {
            "decision_question": "等待数据和分析师产物补齐后再形成正式研究问题",
            "key_tensions": [],
            "no_preset_decision_attestation": True,
        },
        "analyst_stance_matrix": [],
        "role_payload_drilldowns": [],
        "consensus": {"consensus_score": None, "action_conviction": None, "status": "pending"},
        "debate": {"debate_required": False, "rounds": [], "retained_hard_dissent": False},
        "decision_service": {"status": "pending", "reason_codes": []},
        "cio_decision": {"status": "pending"},
        "decision_packet": {"status": "pending", "evidence_refs": []},
        "decision_guard": {"status": "pending", "owner_exception_or_reopen": None},
        "optimizer_deviation": {"status": "pending"},
        "risk_review": {"status": "pending", "verdict": None},
        "approval": {"status": "not_required", "approval_id": None},
        "paper_execution": {"status": "blocked", "reason_code": "execution_core_blocked_no_trade"},
        "position_disposal": {"status": "not_required"},
        "attribution": {"status": "pending"},
        "handoffs": handoffs,
        "evidence_map": {
            "artifact_refs": [ref for stage in stages for ref in stage["output_artifact_refs"]],
            "data_refs": [],
            "source_quality": [],
            "conflict_refs": [],
            "supporting_evidence_only_refs": [],
        },
        "forbidden_actions": {
            "risk_rejected_no_override": {"action_visible": False, "reason_code": "risk_rejected_no_override"},
            "execution_core_blocked_no_trade": {"action_visible": False, "reason_code": "execution_core_blocked_no_trade"},
            "non_a_asset_no_trade": {"action_visible": False, "reason_code": "non_a_asset_no_trade"},
            "low_action_no_execution": {"action_visible": False, "reason_code": "low_action_no_execution"},
        },
    }
    return _apply_artifact_projection(dossier, artifacts)


def _approval_read_model(approval: ApprovalRecord) -> dict[str, Any]:
    return {
        "approval_id": approval.approval_id,
        "approval_type": approval.approval_type,
        "approval_object_ref": approval.approval_object_ref,
        "trigger_reason": approval.trigger_reason,
        "comparison_options": approval.comparison_options,
        "recommended_decision": approval.recommended_decision,
        "risk_and_impact": approval.risk_and_impact,
        "evidence_refs": list(approval.evidence_refs),
        "effective_scope": approval.effective_scope,
        "timeout_policy": approval.timeout_policy,
        "decision": approval.decision,
        "decided_at": approval.decided_at,
        "version": 1,
    }


def _governance_change_read_model(change) -> dict[str, Any]:
    return {
        "change_id": change.change_id,
        "change_type": change.change_type,
        "impact_level": change.impact_level,
        "state": change.state,
        "proposal_ref": change.proposal_ref,
        "target_version_refs": change.target_version_refs,
        "effective_scope": change.effective_scope,
        "rollback_plan_ref": change.rollback_plan_ref,
        "created_at": change.created_at,
        "updated_at": change.updated_at,
        "comparison_analysis_ref": change.comparison_analysis_ref,
        "auto_validation_refs": list(change.auto_validation_refs),
        "owner_approval_ref": change.owner_approval_ref,
        "context_snapshot_id": change.context_snapshot_id,
        "state_reason": change.state_reason,
        "decided_at": change.decided_at,
        "effective_at": change.effective_at,
    }


def _install_frontend_static_routes(app: FastAPI) -> None:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        return
    assets_dir = FRONTEND_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str = ""):
        if full_path.startswith("api/") or full_path.startswith("internal/"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(index_file)


def build_app(runtime: ApiRuntime | None = None) -> FastAPI:
    app = FastAPI(title="velentrade-api", version="0.1.0")
    settings = Settings()
    database_url = os.environ.get(settings.database_url_env)
    api_runtime = runtime or ApiRuntime(database_url=database_url)
    app.state.api_runtime = api_runtime

    @app.get("/api/team")
    def get_team() -> dict[str, Any]:
        return _success(build_team_read_model())

    @app.get("/api/team/{agent_id}")
    def get_agent_profile(agent_id: str):
        try:
            return _success(build_agent_profile_read_model(agent_id))
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown agent: {agent_id}")

    @app.get("/api/team/{agent_id}/capability-config")
    def get_agent_capability_config(agent_id: str):
        try:
            return _success(build_agent_capability_config_read_model(agent_id))
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown agent: {agent_id}")

    @app.get("/api/finance/overview")
    def get_finance_overview():
        return _success(api_runtime.finance.finance_overview())

    @app.get("/api/devops/health")
    def get_devops_health():
        return _success(api_runtime.observability.devops_health_read_model())

    @app.get("/api/devops/incidents")
    def get_devops_incidents():
        report = api_runtime.devops.build_devops_incident_report()
        incidents_by_id = {item["incident_id"]: dict(item) for item in report["incidents"]}
        recovery_by_incident = {item["incident_ref"]: item for item in report["recovery_plan"]}
        return _success([
            {
                **incident,
                "investment_resume_allowed": recovery_by_incident.get(incident_id, {}).get("investment_resume_allowed", False),
                "risk_review_required": recovery_by_incident.get(incident_id, {}).get("risk_review_required", False),
            }
            for incident_id, incident in incidents_by_id.items()
        ])

    @app.post("/api/finance/assets")
    def update_finance_asset(request: FinanceAssetUpdateRequest):
        profile = api_runtime.finance.upsert_asset(
            FinanceAssetUpdate(
                asset_type=request.asset_type,
                valuation=request.valuation,
                valuation_date=request.valuation_date,
                source=request.source,
                asset_id=request.asset_id,
            )
        )
        if hasattr(api_runtime.store, "mirror_finance_profile"):
            api_runtime.store.mirror_finance_profile(profile, api_runtime.finance.manual_todos)
        asset_id = request.asset_id or (profile.assets + profile.liabilities)[-1]["asset_id"]
        asset = next(item for item in profile.assets + profile.liabilities if item["asset_id"] == asset_id)
        return _success(asset)

    @app.get("/api/knowledge/search")
    def search_knowledge(q: str | None = None):
        api_runtime.gateway.cleanup_owner_knowledge_garbage()
        if hasattr(api_runtime.store, "cleanup_owner_knowledge_garbage"):
            api_runtime.store.cleanup_owner_knowledge_garbage()
        memory_items = api_runtime.gateway.list_memory_read_models()
        if not memory_items and api_runtime.gateway.store is not None:
            memory_items = api_runtime.gateway.store.list_memory_read_models()
        query = (q or "").lower()
        results = [
            item for item in memory_items
            if not query or query in item.get("title", "").lower() or query in item.get("summary", "").lower()
        ]
        return _success({"results": results})

    @app.get("/api/governance/changes")
    def list_governance_changes():
        return _success([
            _governance_change_read_model(change)
            for change in api_runtime.governance.changes.values()
        ])

    @app.post("/api/governance/changes/{change_id}/decision")
    def decide_governance_change(change_id: str, request: ApprovalDecisionRequest):
        if change_id not in api_runtime.governance.changes:
            return _error(404, "NOT_FOUND", f"Unknown governance change: {change_id}")
        approved = request.decision == "approved"
        change = api_runtime.governance.owner_decide(change_id, approved=approved, approval_ref=new_id("approval"))
        if approved:
            change = api_runtime.governance.activate(change_id)
        return _success(_governance_change_read_model(change))

    @app.post("/api/team/{agent_id}/capability-drafts")
    def create_agent_capability_draft(agent_id: str, request: AgentCapabilityDraftRequest):
        if agent_id != request.agent_id:
            return _error(422, "VALIDATION_ERROR", "agent_id path/body mismatch.", reason_code="agent_id_mismatch")
        if agent_id not in api_runtime.profiles:
            return _error(404, "NOT_FOUND", f"Unknown agent: {agent_id}")
        change_id = new_id("gov-change")
        impact_level = request.impact_level_hint or "medium"
        change = api_runtime.governance.submit_change(
            change_id=change_id,
            change_type="agent_capability",
            impact_level=impact_level,
            proposal_ref=new_id("capability-draft"),
            target_version_refs={"agent_id": agent_id, "change_set": request.change_set},
            effective_scope=request.effective_scope,
            rollback_plan_ref=request.rollback_plan_ref or new_id("rollback"),
        )
        return _success({
            "draft_id": change.proposal_ref,
            "agent_id": agent_id,
            "change_set": request.change_set,
            "diff_summary": request.draft_title,
            "impact_level": change.impact_level,
            "state": change.state,
            "validation_status": "pending",
            "governance_change_ref": change.change_id,
            "owner_approval_ref": change.owner_approval_ref,
            "effective_scope": change.effective_scope,
            "rollback_plan_ref": change.rollback_plan_ref,
            "created_at": change.created_at,
            "updated_at": change.updated_at,
        })

    @app.get("/api/approvals")
    def list_approvals():
        return _success({"approval_center": [_approval_read_model(item) for item in api_runtime.approvals.values()]})

    @app.post("/api/approvals/{approval_id}/decision")
    def decide_approval(approval_id: str, request: ApprovalDecisionRequest):
        approval = api_runtime.approvals.get(approval_id)
        if approval is None:
            return _error(404, "NOT_FOUND", f"Unknown approval: {approval_id}")
        if request.decision not in {"approved", "rejected", "request_changes"}:
            return _error(422, "VALIDATION_ERROR", "Unsupported approval decision.", reason_code="invalid_decision")
        decided = replace(approval, decision=request.decision, decided_at=utc_now())
        api_runtime.approvals[approval_id] = decided
        if hasattr(api_runtime.store, "mirror_approval_record"):
            api_runtime.store.mirror_approval_record(decided)
        return _success(_approval_read_model(decided))

    @app.post("/api/requests/briefs")
    def create_request_brief(request: CreateRequestBriefRequest):
        scope = request.requested_scope or {}
        brief = RequestBrief.route_owner_request(
            brief_id=new_id("brief"),
            raw_input_ref=request.raw_text,
            intent=str(scope.get("intent", "learn_hot_event")),
            asset_scope=str(scope.get("asset_scope", "a_share_common_stock")),
            target_action=str(scope.get("target_action", "research")),
            route_confidence=float(scope.get("route_confidence", 0.95)),
            authorization_boundary=request.authorization_boundary or "request_brief_only",
        )
        api_runtime.request_briefs[brief.brief_id] = brief
        return _success(_request_brief_read_model(brief))

    @app.post("/api/requests/briefs/{brief_id}/confirmation")
    def confirm_request_brief(brief_id: str, request: RequestBriefConfirmationRequest):
        brief = api_runtime.request_briefs.get(brief_id)
        if brief is None:
            return _error(404, "NOT_FOUND", f"Unknown request brief: {brief_id}")
        if brief_id in api_runtime.confirmed_brief_ids:
            return _error(409, "CONFLICT", "Request brief has already been decided.", reason_code="brief_already_decided")
        if request.decision not in {"confirm", "edit", "cancel"}:
            return _error(422, "VALIDATION_ERROR", "Unsupported confirmation decision.", reason_code="invalid_decision")

        owner_decision = {"confirm": "confirmed", "cancel": "canceled", "edit": "edited"}[request.decision]
        task = api_runtime.workflow.confirm_request_brief(brief, owner_decision=owner_decision)
        api_runtime.confirmed_brief_ids.add(brief_id)
        workflow_id = None
        if api_runtime.gateway.store is not None:
            api_runtime.gateway.store.mirror_task(task)
        if task.current_state == "ready" and task.task_type == "investment_workflow":
            workflow = api_runtime.workflow.create_investment_workflow(task, context_snapshot_id="ctx-v1")
            workflow_id = workflow.workflow_id
            if api_runtime.gateway.store is not None:
                api_runtime.gateway.store.mirror_workflow(workflow)
        return _success(_task_read_model(task, workflow_id=workflow_id))

    @app.get("/api/tasks")
    def get_tasks():
        tasks_by_id = {}
        if api_runtime.gateway.store is not None:
            for task in api_runtime.gateway.store.list_task_read_models():
                tasks_by_id[task["task_id"]] = task
        for task in api_runtime.workflow.tasks.values():
            tasks_by_id[task.task_id] = _task_read_model(task)
        return _success({
            "task_center": list(tasks_by_id.values()),
        })

    @app.get("/api/workflows/{workflow_id}")
    def get_workflow(workflow_id: str):
        workflow = api_runtime.workflow.workflows.get(workflow_id)
        if workflow is None:
            if api_runtime.gateway.store is not None:
                persisted_workflow = api_runtime.gateway.store.get_workflow_read_model(workflow_id)
                if persisted_workflow is not None:
                    return _success(persisted_workflow)
            return _error(404, "NOT_FOUND", f"Unknown workflow: {workflow_id}")
        return _success(_workflow_read_model(workflow))

    @app.post("/api/workflows/{workflow_id}/commands")
    def run_workflow_command(workflow_id: str, request: WorkflowCommandRequest):
        workflow = api_runtime.workflow.workflows.get(workflow_id)
        if workflow is None:
            return _error(404, "NOT_FOUND", f"Unknown workflow: {workflow_id}")

        stage_name = str(request.payload.get("stage", workflow.current_stage))
        current_stage = _workflow_stage_by_name(workflow, stage_name)
        if current_stage is None:
            return _error(422, "VALIDATION_ERROR", f"Unknown stage: {stage_name}", reason_code="unknown_stage")
        if current_stage.stage_version != request.client_seen_stage_version:
            return _error(409, "SNAPSHOT_MISMATCH", "Workflow stage version changed.", reason_code="stage_version_mismatch")

        if request.command_type == "start_stage":
            stage = api_runtime.workflow.start_stage(workflow_id, stage_name)
            if api_runtime.gateway.store is not None:
                api_runtime.gateway.store.mirror_workflow(api_runtime.workflow.workflows[workflow_id])
            if stage.node_status == "blocked":
                return _error(409, "STAGE_GUARD_FAILED", "Workflow stage guard blocked command.", reason_code=stage.reason_code)
            return _success(_workflow_command_result(request.command_type, stage))
        if request.command_type == "complete_stage":
            raw_artifact_refs = request.payload.get("artifact_refs", [])
            artifact_refs = [str(ref) for ref in raw_artifact_refs] if isinstance(raw_artifact_refs, list) else []
            stage = api_runtime.workflow.complete_stage(workflow_id, stage_name, artifact_refs)
            if api_runtime.gateway.store is not None:
                api_runtime.gateway.store.mirror_workflow(api_runtime.workflow.workflows[workflow_id])
            if stage.node_status == "blocked":
                return _error(409, "STAGE_GUARD_FAILED", "Workflow stage guard blocked command.", reason_code=stage.reason_code)
            return _success(_workflow_command_result(request.command_type, stage))
        if request.command_type == "request_reopen":
            target_stage = str(request.payload.get("target_stage", stage_name))
            event = api_runtime.workflow.request_reopen(
                workflow_id=workflow_id,
                from_stage=stage_name,
                target_stage=target_stage,
                reason_code=request.reason_code or str(request.payload.get("reason_code", "owner_requested_reopen")),
                requested_by=str(request.payload.get("requested_by", "owner")),
                invalidated_artifacts=[str(ref) for ref in request.payload.get("invalidated_artifacts", [])],
                preserved_artifacts=[str(ref) for ref in request.payload.get("preserved_artifacts", [])],
            )
            if api_runtime.gateway.store is not None:
                api_runtime.gateway.store.mirror_reopen_event(event)
            return _success({
                "accepted": True,
                "command_type": request.command_type,
                "object_type": "reopen_event",
                "object_id": event.reopen_event_id,
                "reopen_event": event,
                "reason_code": event.reason_code,
                "trace_id": new_id("trace"),
            })
        return _error(403, "COMMAND_NOT_ALLOWED", "Unsupported workflow command.", reason_code="unsupported_workflow_command")

    @app.get("/api/workflows/{workflow_id}/dossier")
    def get_investment_dossier(workflow_id: str):
        workflow = api_runtime.workflow.workflows.get(workflow_id)
        if workflow is None:
            if api_runtime.gateway.store is not None:
                persisted_workflow = api_runtime.gateway.store.get_workflow_read_model(workflow_id)
                if persisted_workflow is not None:
                    return _success(_investment_dossier_from_workflow_payload(
                        persisted_workflow,
                        task=api_runtime.gateway.store.get_task_read_model(persisted_workflow["task_id"]),
                        handoffs=api_runtime.gateway.store.list_handoffs(workflow_id),
                        artifacts=api_runtime.gateway.store.list_artifacts(workflow_id),
                    ))
            return _error(404, "NOT_FOUND", f"Unknown workflow: {workflow_id}")
        return _success(_investment_dossier_read_model(api_runtime, workflow))

    @app.post("/api/collaboration/commands")
    def create_collaboration_command(request: CollaborationCommandRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        try:
            command = CollaborationCommand.request(
                command_id=new_id("command"),
                command_type=request.command_type,
                workflow_id=request.workflow_id,
                attempt_no=request.attempt_no,
                stage=request.stage,
                source_agent_run_id=request.source_agent_run_id,
                source_agent_id=run.agent_id,
                target_agent_id_or_service=request.target_agent_id_or_service,
                payload=request.payload,
                requested_admission_type=request.requested_admission_type,
            )
        except ValueError:
            return _error(
                403,
                "COMMAND_NOT_ALLOWED",
                "Command is not allowed for this AgentRun.",
                reason_code="unknown_command_type",
            )
        result = api_runtime.gateway.append_command(run, command, idempotency_key=command.command_id)
        if not result.accepted:
            return _error(403, "COMMAND_NOT_ALLOWED", "Command is not allowed for this AgentRun.", reason_code=result.reason_code)
        accepted = api_runtime.gateway.command_ledger[-1]
        return _success(accepted)

    @app.post("/api/gateway/artifacts")
    def write_artifact(request: GatewayArtifactWriteRequest):
        if bool(request.source_agent_run_id) == bool(request.producer_service):
            return _error(422, "VALIDATION_ERROR", "Exactly one artifact producer is required.", reason_code="invalid_artifact_producer")
        if request.producer_service is not None:
            result = api_runtime.gateway.append_service_artifact(
                workflow_id=request.workflow_id,
                attempt_no=request.attempt_no,
                producer_service=request.producer_service,
                artifact_type=request.artifact_type,
                payload=request.payload,
                idempotency_key=request.idempotency_key,
                schema_version=request.schema_version,
                source_refs=request.source_refs,
            )
            if not result.accepted:
                return _error(403, "PERMISSION_DENIED", "Artifact type is not allowed.", reason_code=result.reason_code)
            return _success(result)

        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        workflow_run = replace(
            run,
            workflow_id=request.workflow_id,
            attempt_no=request.attempt_no,
            stage=request.stage,
            context_snapshot_id=request.context_snapshot_id,
        )
        result = api_runtime.gateway.append_artifact(
            workflow_run,
            artifact_type=request.artifact_type,
            payload=request.payload,
            idempotency_key=request.idempotency_key,
            schema_version=request.schema_version,
            source_refs=request.source_refs,
        )
        if not result.accepted:
            return _error(403, "PERMISSION_DENIED", "Artifact type is not allowed.", reason_code=result.reason_code)
        return _success(result)

    @app.post("/api/gateway/events")
    def write_event(request: GatewayEventWriteRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        workflow_run = replace(run, workflow_id=request.workflow_id, attempt_no=request.attempt_no, stage=request.stage)
        result = api_runtime.gateway.append_event(
            workflow_run,
            event_type=request.event_type,
            payload=request.payload,
            idempotency_key=request.idempotency_key,
        )
        return _success(result)

    @app.post("/api/gateway/handoffs")
    def write_handoff(request: GatewayHandoffWriteRequest):
        handoff = HandoffPacket.create(
            handoff_id=new_id("handoff"),
            workflow_id=request.workflow_id,
            attempt_no=request.attempt_no,
            from_stage=request.from_stage,
            to_stage_or_agent=request.to_stage_or_agent,
            producer_agent_id_or_service=request.producer_agent_id_or_service,
            source_artifact_refs=request.source_artifact_refs,
            summary=request.summary,
        )
        if request.open_questions:
            handoff = HandoffPacket(
                **{
                    **handoff.__dict__,
                    "open_questions": request.open_questions,
                    "blockers": request.blockers,
                    "decisions_made": request.decisions_made,
                    "invalidated_artifacts": request.invalidated_artifacts,
                    "preserved_artifacts": request.preserved_artifacts,
                }
            )
        result = api_runtime.gateway.append_handoff(handoff, idempotency_key=request.idempotency_key)
        return _success(result)

    @app.post("/api/gateway/memory-items")
    def write_memory(request: GatewayMemoryWriteRequest):
        run = api_runtime.require_run(request.source_agent_run_id)
        if run is None:
            return _error(404, "NOT_FOUND", "Unknown source_agent_run_id")
        capture = MemoryCapture(
            capture_id=new_id("capture"),
            source_type=request.operation,
            source_refs=request.source_refs,
            content_markdown=request.content_markdown,
            payload=request.payload or {},
            suggested_memory_type="research_note",
            sensitivity=request.sensitivity,
            producer_agent_id=run.agent_id,
        )
        result = api_runtime.gateway.capture_memory(capture, idempotency_key=request.idempotency_key)
        return _success(result)

    @app.post("/api/knowledge/memory-items")
    def create_memory_item(request: CreateMemoryItemRequest):
        rejection_reason = memory_capture_rejection_reason(
            content_markdown=request.content_markdown,
            source_refs=request.source_refs,
            sensitivity=request.sensitivity,
        )
        if rejection_reason is not None:
            return _error(422, "VALIDATION_ERROR", "Memory item is not owner-readable or source-backed.", reason_code=rejection_reason)
        run = api_runtime.next_owner_capture_run()
        capture = MemoryCapture(
            capture_id=new_id("capture"),
            source_type=request.source_type,
            source_refs=request.source_refs,
            content_markdown=request.content_markdown,
            payload={"tags": request.tags},
            suggested_memory_type=request.suggested_memory_type,
            sensitivity=request.sensitivity,
            producer_agent_id=run.agent_id,
        )
        api_runtime.gateway.capture_memory(capture, idempotency_key=f"owner-memory-{run.agent_run_id}")
        memory = api_runtime.gateway.get_memory_read_model(api_runtime.gateway.memory_items[-1].memory_id)
        return _success(memory)

    @app.get("/api/artifacts/{artifact_id}")
    def get_artifact(artifact_id: str):
        artifact = next(
            (item for item in api_runtime.gateway.artifact_ledger if item["artifact_id"] == artifact_id),
            None,
        )
        if artifact is None and api_runtime.gateway.store is not None:
            artifact = api_runtime.gateway.store.get_artifact(artifact_id)
        if artifact is None:
            return _error(404, "NOT_FOUND", f"Unknown artifact: {artifact_id}")
        return _success(artifact)

    @app.get("/api/workflows/{workflow_id}/agent-runs")
    def get_agent_runs(workflow_id: str):
        runs = [run for run in api_runtime.agent_runs.values() if run.workflow_id == workflow_id]
        return _success(runs)

    @app.get("/api/workflows/{workflow_id}/collaboration-events")
    def get_collaboration_events(workflow_id: str):
        events = [event for event in api_runtime.gateway.event_ledger if event.workflow_id == workflow_id]
        if not events and api_runtime.gateway.store is not None:
            events = api_runtime.gateway.store.list_events(workflow_id)
        return _success(events)

    @app.get("/api/workflows/{workflow_id}/handoffs")
    def get_handoffs(workflow_id: str):
        handoffs = [handoff for handoff in api_runtime.gateway.handoff_ledger if handoff.workflow_id == workflow_id]
        if not handoffs and api_runtime.gateway.store is not None:
            handoffs = api_runtime.gateway.store.list_handoffs(workflow_id)
        return _success(handoffs)

    @app.get("/api/knowledge/memory-items")
    def list_memory_items():
        api_runtime.gateway.cleanup_owner_knowledge_garbage()
        if hasattr(api_runtime.store, "cleanup_owner_knowledge_garbage"):
            api_runtime.store.cleanup_owner_knowledge_garbage()
        memory_items = api_runtime.gateway.list_memory_read_models()
        if not memory_items and api_runtime.gateway.store is not None:
            memory_items = api_runtime.gateway.store.list_memory_read_models()
        return _success(memory_items)

    @app.get("/api/knowledge/memory-items/{memory_id}")
    def get_memory_item(memory_id: str):
        api_runtime.gateway.cleanup_owner_knowledge_garbage()
        if hasattr(api_runtime.store, "cleanup_owner_knowledge_garbage"):
            api_runtime.store.cleanup_owner_knowledge_garbage()
        memory = api_runtime.gateway.get_memory_read_model(memory_id)
        if memory is None and api_runtime.gateway.store is not None:
            memory = api_runtime.gateway.store.get_memory_read_model(memory_id)
        if memory is None:
            return _error(404, "NOT_FOUND", f"Unknown memory item: {memory_id}")
        return _success(memory)

    @app.post("/api/knowledge/memory-items/{memory_id}/relations")
    def create_memory_relation(memory_id: str, request: MemoryRelationWriteRequest):
        try:
            relation = api_runtime.gateway.append_memory_relation(
                memory_id=memory_id,
                target_ref=request.target_ref,
                relation_type=request.relation_type,
                reason=request.reason,
                evidence_refs=request.evidence_refs,
                client_seen_version_id=request.client_seen_version_id,
            )
        except KeyError:
            return _error(404, "NOT_FOUND", f"Unknown memory item: {memory_id}")
        except ValueError as error:
            reason_code = str(error)
            if reason_code.startswith("invalid_memory_relation"):
                return _error(422, "VALIDATION_ERROR", "Memory relation is missing a clear target, type, reason or evidence.", reason_code=reason_code)
            return _error(409, "CONFLICT", "Memory version mismatch.", reason_code="client_seen_version_mismatch")
        return _success(relation)

    _install_frontend_static_routes(app)

    return app
