from __future__ import annotations

from hashlib import sha256

from fastapi.testclient import TestClient

from velentrade.api.app import ApiRuntime, build_app
from velentrade.domain.common import utc_now
from velentrade.domain.memory.models import (
    MemoryExtractionResult,
    MemoryItem,
    MemoryRelation,
    MemoryVersion,
)
from velentrade.domain.workflow.runtime import TaskEnvelope, Workflow, WorkflowStage


def test_devops_health_does_not_emit_fake_recovery_when_no_incident():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/devops/health")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["routine_checks"][0]["status"] == "observed"
    assert payload["incidents"] == []
    assert payload["recovery"] == []


def test_devops_health_emits_recovery_only_for_real_runner_incident():
    runtime = ApiRuntime()
    runtime.observability.record_metric("agent_run_duration_seconds", {"status": "timed_out"})
    client = TestClient(build_app(runtime))

    response = client.get("/api/devops/health")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["incidents"][0]["incident_type"] == "runner"
    assert payload["recovery"][0]["technical_recovery_status"] == "pending_validation"
    assert payload["recovery"][0]["investment_resume_allowed"] is False


def test_knowledge_endpoint_cleans_historical_garbage_and_test_relations():
    runtime = ApiRuntime()
    client = TestClient(build_app(runtime))

    valid_response = client.post(
        "/api/knowledge/memory-items",
        json={
            "source_type": "owner_note",
            "source_refs": ["owner-note-real-1"],
            "content_markdown": "# 银行研究复盘\n- 来源：业绩会纪要\n- 后续只作为研究背景。",
            "suggested_memory_type": "owner_observation",
            "tags": ["研究复盘"],
            "sensitivity": "public_internal",
            "client_seen_context_snapshot_id": "ctx-v1",
        },
    )
    assert valid_response.status_code == 200
    valid_id = valid_response.json()["data"]["memory_id"]

    _append_memory(runtime, "memory-dirty-test", "test", "test", source_refs=["test"])
    _append_memory(runtime, "memory-dirty-cn", "测试", "# 测试\n- 测试", source_refs=["测试"])
    _append_memory(
        runtime,
        "memory-dirty-untitled",
        "Untitled Memory",
        "# Untitled Memory\n- invalid",
        source_refs=[],
        sensitivity="invalid_value",
    )
    runtime.gateway.memory_relations.append(
        MemoryRelation(
            relation_id="memory-relation-3f819415149f",
            source_memory_id=valid_id,
            target_ref="knowledge-method-1",
            relation_type="supports",
            reason="Owner applied organize suggestion from Knowledge workspace",
            evidence_refs=["knowledge_memory_workspace"],
            created_by="owner",
            created_at=utc_now(),
        )
    )

    response = client.get("/api/knowledge/memory-items")

    assert response.status_code == 200
    items = response.json()["data"]
    titles = {item["title"] for item in items}
    assert "银行研究复盘" in titles
    assert "test" not in titles
    assert "测试" not in titles
    assert "Untitled Memory" not in titles
    assert all(item["sensitivity"] != "invalid_value" for item in items)
    assert all(item["source_refs"] and item["summary"].strip() for item in items)
    assert all(
        relation["target_ref"] != "knowledge-method-1"
        and relation["reason"] != "Owner applied organize suggestion from Knowledge workspace"
        for item in items
        for relation in item["relations"]
    )
    assert all(item.memory_id not in {"memory-dirty-test", "memory-dirty-cn", "memory-dirty-untitled"} for item in runtime.gateway.memory_items)
    assert all(relation.target_ref != "knowledge-method-1" for relation in runtime.gateway.memory_relations)


def test_knowledge_write_validation_rejects_garbage_memory_and_ambiguous_relations():
    client = TestClient(build_app(ApiRuntime()))

    base_payload = {
        "source_type": "owner_note",
        "source_refs": ["owner-note-real-2"],
        "content_markdown": "# 有来源的研究经验\n- 来源：复盘记录\n- 只作为背景。",
        "suggested_memory_type": "owner_observation",
        "tags": ["研究复盘"],
        "sensitivity": "public_internal",
        "client_seen_context_snapshot_id": "ctx-v1",
    }
    valid_response = client.post("/api/knowledge/memory-items", json=base_payload)
    assert valid_response.status_code == 200
    valid_memory = valid_response.json()["data"]

    for patch in (
        {"content_markdown": ""},
        {"content_markdown": "test"},
        {"content_markdown": "# 测试\n- 测试"},
        {"content_markdown": "# Untitled Memory\n- 待补充"},
        {"source_refs": []},
        {"sensitivity": "invalid_value"},
    ):
        response = client.post("/api/knowledge/memory-items", json={**base_payload, **patch})
        assert response.status_code == 422
        assert response.json()["error"]["reason_code"].startswith("invalid_memory")

    for relation_patch in (
        {"target_ref": ""},
        {"relation_type": ""},
        {"reason": ""},
        {"evidence_refs": []},
    ):
        relation_response = client.post(
            f"/api/knowledge/memory-items/{valid_memory['memory_id']}/relations",
            json={
                "target_ref": "artifact-real-1",
                "relation_type": "supports",
                "reason": "这条经验支持 artifact-real-1 的复盘边界。",
                "evidence_refs": ["artifact-real-1"],
                "client_seen_version_id": valid_memory["current_version_id"],
                **relation_patch,
            },
        )
        assert relation_response.status_code == 422
        assert relation_response.json()["error"]["reason_code"].startswith("invalid_memory_relation")


def test_wf001_dossier_is_backend_seeded_and_separates_s3_blocker_from_s6_execution_guard():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/workflows/wf-001/dossier")

    assert response.status_code == 200
    dossier = response.json()["data"]
    assert dossier["workflow"]["workflow_id"] == "wf-001"
    assert dossier["workflow"]["title"] == "浦发银行 A 股研究"
    assert dossier["workflow"]["current_stage"] == "S3"
    assert dossier["workflow"]["state"] == "blocked"
    s3 = next(stage for stage in dossier["stage_rail"] if stage["stage"] == "S3")
    s6 = next(stage for stage in dossier["stage_rail"] if stage["stage"] == "S6")
    assert s3["node_status"] == "blocked"
    assert s3["reason_code"] == "retained_hard_dissent_risk_review"
    assert s6["node_status"] == "not_started"
    assert dossier["data_readiness"]["decision_core_status"] == "pass"
    assert dossier["data_readiness"]["execution_core_status"] == "blocked"
    assert "retained_hard_dissent_risk_review" in dossier["risk_review"]["reason_codes"]
    assert "execution_core_blocked_no_trade" in dossier["risk_review"]["reason_codes"]
    assert dossier["paper_execution"]["status"] == "blocked"


def test_wf001_dossier_projects_structured_s3_debate_details_for_owner():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/workflows/wf-001/dossier")

    assert response.status_code == 200
    debate = response.json()["data"]["debate"]
    assert debate["owner_summary"] == "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。"
    assert debate["status_summary"]["rounds_used"] == 2
    assert debate["status_summary"]["retained_hard_dissent"] is True
    assert debate["status_summary"]["risk_review_required"] is True
    assert debate["status_summary"]["consensus_score"] == 0.75
    assert debate["status_summary"]["action_conviction"] == 0.6

    assert debate["core_disputes"] == [
        {
            "title": "资产质量修复是否足以抵消估值低位",
            "why_it_matters": "如果资产质量没有确认修复，低估值可能是价值陷阱，不能直接进入 S4 决策。",
            "involved_roles": ["基本面分析师", "量化分析师", "CIO"],
            "current_conclusion": "补证前不能进入 S4，先保留 S3 阻断。",
            "required_evidence": ["不良率趋势", "拨备覆盖率趋势", "息差改善证据"],
        }
    ]
    assert {
        "role": "量化分析师",
        "before": "偏正面",
        "after": "观察",
        "reason": "基本面补证不足，量价信号不能单独推动 S4。",
        "impact": "降低行动强度，等待基本面补证后再评估。",
    } in debate["view_change_details"]
    assert debate["retained_dissent_details"][0]["source_role"] == "基本面分析师"
    assert "不良率拐点未确认" in debate["retained_dissent_details"][0]["counter_risks"]
    assert "不能直接放行 S4" in debate["retained_dissent_details"][0]["forbidden_actions"]
    assert debate["round_details"][0]["input_evidence"] == ["不良率趋势", "拨备覆盖率"]
    assert debate["round_details"][1]["unresolved_questions"] == ["补证后是否足以解除基本面硬异议"]
    assert debate["next_actions"] == [
        {
            "action": "补齐资产质量、拨备覆盖率和息差趋势证据",
            "owner": "基本面分析师",
            "completion_signal": "形成可复核补证包并更新硬异议判断",
            "next_stage": "交风控复核后再判断是否进入 S4",
        }
    ]


def test_wf001_dossier_projects_data_sources_for_owner_s1_readability():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/workflows/wf-001/dossier")

    assert response.status_code == 200
    dossier = response.json()["data"]
    data_readiness = dossier["data_readiness"]
    evidence_map = dossier["evidence_map"]
    assert data_readiness["lineage_refs"] == ["tencent-public-kline:600000.SH"]
    assert data_readiness["owner_summary"] == "S1 已拿到可用于研究的数据；成交前还缺 S6 执行核心数据。"
    assert data_readiness["source_status"] == [
        {
            "source_name": "腾讯公开日线行情",
            "source_ref": "tencent-public-kline:600000.SH",
            "required_usage": "decision_core",
            "requested_fields": ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
            "obtained_fields": ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"],
            "missing_fields": [],
            "status": "available",
            "quality_label": "可用于研究判断",
            "evidence_ref": "tencent-public-kline:600000.SH",
        },
        {
            "source_name": "实时执行行情",
            "source_ref": "execution-core:600000.SH",
            "required_usage": "execution_core",
            "requested_fields": ["最新成交价", "盘口深度", "可成交窗口"],
            "obtained_fields": [],
            "missing_fields": ["最新成交价", "盘口深度", "可成交窗口"],
            "status": "missing",
            "quality_label": "缺失，不能用于成交",
            "evidence_ref": "execution-core:600000.SH",
        },
    ]
    assert {
        "gap": "实时执行行情缺失",
        "affects_stage": "S6",
        "impact": "不能生成纸面成交授权，不影响当前 S3 硬异议判断。",
        "next_action": "进入 S6 前重新采集最新成交价、盘口深度和可成交窗口，并由风控复核。",
    } in data_readiness["data_gaps"]
    assert evidence_map["data_refs"] == ["tencent-public-kline:600000.SH"]
    assert evidence_map["source_quality"] == [
        {
            "source": "腾讯公开日线行情",
            "used_for": "支持判断：是否值得继续分析浦发银行",
            "quality": "可用于研究判断",
        }
    ]
    assert evidence_map["conflict_refs"] == ["分钟级成交数据缺失"]


def test_dossier_projects_zero_success_s1_data_as_backend_owned_failure_state():
    runtime = ApiRuntime()
    now = utc_now()
    task = TaskEnvelope(
        task_id="task-wf-no-data",
        task_type="investment_workflow",
        priority="P0",
        owner_role="owner",
        current_state="ready",
        reason_code="request_brief_confirmed",
        artifact_refs=[],
        created_at=now,
        updated_at=now,
    )
    runtime.workflow.tasks[task.task_id] = task
    runtime.workflow_titles["wf-no-data"] = "零数据 A 股研究"
    runtime.workflow.workflows["wf-no-data"] = Workflow(
        workflow_id="wf-no-data",
        task_id=task.task_id,
        workflow_type="investment_workflow",
        current_stage="S1",
        current_attempt_no=1,
        status="running",
        context_snapshot_id="ctx-v1",
        stages=[
            WorkflowStage(
                workflow_id="wf-no-data",
                attempt_no=1,
                stage=f"S{index}",
                node_status="running" if index == 1 else ("completed" if index == 0 else "not_started"),
                responsible_role="data_collection_quality_service" if index == 1 else "workflow_scheduling_center",
                output_artifact_refs=["artifact-no-data-readiness"] if index == 1 else [],
                started_at=now if index <= 1 else None,
                completed_at=now if index == 0 else None,
            )
            for index in range(8)
        ],
        created_at=now,
        updated_at=now,
    )
    runtime.gateway.artifact_ledger.append(
        {
            "artifact_id": "artifact-no-data-readiness",
            "artifact_type": "DataReadinessReport",
            "workflow_id": "wf-no-data",
            "attempt_no": 1,
            "trace_id": "trace-no-data-readiness",
            "producer": "data_collection_quality_service",
            "producer_type": "service",
            "status": "accepted",
            "schema_version": "1.0.0",
            "payload": {
                "quality_band": "blocked",
                "decision_core_status": "blocked",
                "execution_core_status": "blocked",
                "reason_code": "data_quality_guard",
                "issues": ["日线行情源超时，公告源返回空结果。"],
                "lineage_refs": [],
                "data_requests": [
                    {
                        "request_id": "no-data-daily",
                        "data_domain": "a_share_market",
                        "symbol_or_scope": "600000.SH",
                        "required_usage": "decision_core",
                        "required_fields": [
                            {"name": "symbol", "present": False, "valid": False, "critical": True},
                            {"name": "trade_date", "present": False, "valid": False, "critical": True},
                            {"name": "close", "present": False, "valid": False, "critical": True},
                        ],
                    }
                ],
                "critical_field_results": {"symbol": False, "trade_date": False, "close": False},
                "fallback_attempts": ["primary-public", "backup-public"],
                "cache_usage": {"cache_hit": False, "may_create_execution_authorization": False},
            },
            "source_refs": [],
            "summary": "data_quality_guard",
            "evidence_refs": [],
            "decision_refs": [],
            "created_at": now,
            "stage": "S1",
        }
    )
    client = TestClient(build_app(runtime))

    response = client.get("/api/workflows/wf-no-data/dossier")

    assert response.status_code == 200
    data_readiness = response.json()["data"]["data_readiness"]
    assert data_readiness["owner_summary"] == "本轮 S1 没有成功获取可用数据。"
    assert data_readiness["source_status"][0]["status"] == "failed"
    assert data_readiness["source_status"][0]["obtained_fields"] == []
    assert data_readiness["source_status"][0]["missing_fields"] == ["标的代码", "交易日", "收盘价"]
    assert data_readiness["data_gaps"][0]["affects_stage"] == "S1"
    assert data_readiness["data_gaps"][0]["impact"] == "无法形成研究判断或进入后续分析。"


def test_wf001_dossier_projects_hard_dissent_and_debate_process_details():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/workflows/wf-001/dossier")

    assert response.status_code == 200
    dossier = response.json()["data"]
    fundamental = next(item for item in dossier["role_payload_drilldowns"] if item["role"] == "fundamental")
    assert fundamental["hard_dissent_reason"]
    assert fundamental["thesis"]
    assert fundamental["supporting_evidence_refs"]
    assert fundamental["counter_evidence_refs"]
    assert fundamental["key_risks"]
    assert fundamental["applicable_conditions"]
    assert fundamental["invalidation_conditions"]
    assert fundamental["suggested_action_implication"]
    assert fundamental["role_payload"]

    assert any(row["role"] == "fundamental" and row["hard_dissent_reason"] for row in dossier["analyst_stance_matrix"])
    assert dossier["debate"]["rounds_used"] == 2
    assert dossier["debate"]["issues"]
    assert dossier["debate"]["view_changes"]
    assert dossier["debate"]["cio_synthesis"]
    assert dossier["debate"]["unresolved_dissent"]
    assert dossier["debate"]["risk_review_required"] is True


def test_wf001_trace_endpoints_return_business_process_summaries():
    client = TestClient(build_app(ApiRuntime()))

    runs = client.get("/api/workflows/wf-001/agent-runs").json()["data"]
    events = client.get("/api/workflows/wf-001/collaboration-events").json()["data"]
    handoffs = client.get("/api/workflows/wf-001/handoffs").json()["data"]

    assert runs
    assert events
    assert handoffs
    assert all(item["run_goal"] for item in runs)
    assert any(item["payload"].get("business_summary") for item in events)
    assert any("基本面硬异议" in item["summary"] for item in handoffs)


def test_unknown_workflow_dossier_returns_404_without_business_preview():
    client = TestClient(build_app(ApiRuntime()))

    response = client.get("/api/workflows/workflow-does-not-exist/dossier")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_non_a_trade_confirmation_preserves_manual_todo_route_reason():
    client = TestClient(build_app(ApiRuntime()))

    brief_response = client.post(
        "/api/requests/briefs",
        json={
            "raw_text": "帮我下单腾讯",
            "source": "owner_command",
            "requested_scope": {
                "intent": "formal_investment_decision",
                "asset_scope": "non_a_asset",
                "target_action": "trade",
            },
            "authorization_boundary": "request_brief_only",
        },
    )
    assert brief_response.status_code == 200
    brief = brief_response.json()["data"]
    assert brief["route_type"] == "manual_todo"
    assert brief["forbidden_action_reason_code"] == "non_a_asset_no_trade"

    confirmation_response = client.post(
        f"/api/requests/briefs/{brief['brief_id']}/confirmation",
        json={"decision": "confirm", "client_seen_version": brief["version"]},
    )

    assert confirmation_response.status_code == 200
    task = confirmation_response.json()["data"]
    assert task["task_type"] == "manual_todo"
    assert task["current_state"] == "ready"
    assert task["reason_code"] == "route_non_a_manual_todo"


def _append_memory(
    runtime: ApiRuntime,
    memory_id: str,
    title: str,
    content: str,
    *,
    source_refs: list[str],
    sensitivity: str = "public_internal",
) -> None:
    now = utc_now()
    version_id = f"{memory_id}-version"
    runtime.gateway.memory_items.append(
        MemoryItem(
            memory_id=memory_id,
            memory_type="owner_observation",
            owner_role="owner",
            producer_agent_id="investment_researcher",
            status="validated_context",
            current_version_id=version_id,
            source_refs=source_refs,
            sensitivity=sensitivity,
            pinned=False,
            created_at=now,
            updated_at=now,
        )
    )
    runtime.gateway.memory_versions.append(
        MemoryVersion(
            version_id=version_id,
            memory_id=memory_id,
            version_no=1,
            content_markdown=content,
            payload={},
            created_by="investment_researcher",
            created_at=now,
            content_hash=sha256(content.encode("utf-8")).hexdigest(),
        )
    )
    runtime.gateway.memory_extraction_results.append(
        MemoryExtractionResult(
            extraction_id=f"{memory_id}-extraction",
            memory_version_id=version_id,
            extractor_version="test",
            title=title,
            tags=[],
            mentions=[],
            has_link=False,
            has_task_list=False,
            has_code=False,
            has_incomplete_tasks=False,
            symbol_refs=[],
            artifact_refs=[],
            agent_refs=[],
            stage_refs=[],
            source_refs=source_refs,
            sensitivity=sensitivity,
            status="succeeded",
            created_at=now,
        )
    )
