from __future__ import annotations

import contextlib
import socket
import subprocess
import time

import psycopg
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from velentrade.api.app import ApiRuntime, build_app
from velentrade.db.seed import apply_wi001_seed


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def _postgres_container():
    port = _find_free_port()
    name = f"velentrade-api-db-{port}"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_USER=velentrade",
            "-e",
            "POSTGRES_PASSWORD=velentrade",
            "-e",
            "POSTGRES_DB=velentrade",
            "-p",
            f"127.0.0.1:{port}:5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        deadline = time.time() + 40
        while time.time() < deadline:
            try:
                with psycopg.connect(
                    f"host=127.0.0.1 port={port} dbname=velentrade user=velentrade password=velentrade"
                ) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("select 1")
                        cursor.fetchone()
                    break
            except psycopg.Error:
                time.sleep(1)
        else:
            raise RuntimeError("PostgreSQL container did not become ready in time.")

        yield f"postgresql+psycopg://velentrade:velentrade@127.0.0.1:{port}/velentrade"
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


def test_api_writes_are_mirrored_into_postgres():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        apply_wi001_seed(engine)

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))

        command_response = client.post(
            "/api/collaboration/commands",
            json={
                "command_type": "request_evidence",
                "workflow_id": "wf-1",
                "attempt_no": 1,
                "stage": "S1",
                "source_agent_run_id": "run-investment_researcher",
                "target_agent_id_or_service": "macro_analyst",
                "payload": {"question": "补充证据", "expected_answer_format": "bullet"},
                "requested_admission_type": "auto_accept",
            },
        )
        assert command_response.status_code == 200

        artifact_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": "wf-1",
                "attempt_no": 1,
                "stage": "S1",
                "source_agent_run_id": "run-investment_researcher",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "ResearchPackage",
                "schema_version": "1.0.0",
                "payload": {"summary": "资料包", "source_refs": ["src-1"]},
                "source_refs": ["src-1"],
                "idempotency_key": "artifact-1",
            },
        )
        assert artifact_response.status_code == 200
        artifact_id = artifact_response.json()["data"]["object_id"]

        event_response = client.post(
            "/api/gateway/events",
            json={
                "workflow_id": "wf-1",
                "attempt_no": 1,
                "stage": "S1",
                "source_agent_run_id": "run-investment_researcher",
                "event_type": "artifact_submitted",
                "payload": {"artifact_type": "ResearchPackage"},
                "idempotency_key": "event-1",
            },
        )
        assert event_response.status_code == 200

        handoff_response = client.post(
            "/api/gateway/handoffs",
            json={
                "workflow_id": "wf-1",
                "attempt_no": 1,
                "from_stage": "S1",
                "to_stage_or_agent": "S2",
                "producer_agent_id_or_service": "investment_researcher",
                "source_artifact_refs": [artifact_id],
                "summary": "交接到下一阶段",
                "open_questions": [],
                "blockers": [],
                "decisions_made": [],
                "invalidated_artifacts": [],
                "preserved_artifacts": [artifact_id],
                "idempotency_key": "handoff-1",
            },
        )
        assert handoff_response.status_code == 200

        memory_response = client.post(
            "/api/gateway/memory-items",
            json={
                "source_agent_run_id": "run-investment_researcher",
                "context_snapshot_id": "ctx-v1",
                "operation": "capture",
                "content_markdown": "# 研究笔记\n- 只作背景",
                "payload": {"artifact_refs": [artifact_id], "symbol_refs": ["600000.SH"]},
                "source_refs": [artifact_id],
                "sensitivity": "public_internal",
                "idempotency_key": "memory-1",
            },
        )
        assert memory_response.status_code == 200
        memory_id = memory_response.json()["data"]["object_id"]

        memory_detail_response = client.get(f"/api/knowledge/memory-items/{memory_id}")
        assert memory_detail_response.status_code == 200
        current_version_id = memory_detail_response.json()["data"]["current_version_id"]

        relation_response = client.post(
            f"/api/knowledge/memory-items/{memory_id}/relations",
            json={
                "target_ref": artifact_id,
                "relation_type": "supports",
                "reason": "该笔记支持资料包结论",
                "evidence_refs": [artifact_id],
                "client_seen_version_id": current_version_id,
            },
        )
        assert relation_response.status_code == 200

        fresh_client = TestClient(build_app(ApiRuntime(database_url=database_url)))

        persisted_artifact_response = fresh_client.get(f"/api/artifacts/{artifact_id}")
        assert persisted_artifact_response.status_code == 200
        assert persisted_artifact_response.json()["data"]["artifact_id"] == artifact_id

        persisted_events_response = fresh_client.get("/api/workflows/wf-1/collaboration-events")
        assert persisted_events_response.status_code == 200
        assert [item["event_type"] for item in persisted_events_response.json()["data"]] == ["artifact_submitted"]

        persisted_handoffs_response = fresh_client.get("/api/workflows/wf-1/handoffs")
        assert persisted_handoffs_response.status_code == 200
        assert [item["summary"] for item in persisted_handoffs_response.json()["data"]] == ["交接到下一阶段"]

        persisted_memory_list_response = fresh_client.get("/api/knowledge/memory-items")
        assert persisted_memory_list_response.status_code == 200
        persisted_memory_ids = [item["memory_id"] for item in persisted_memory_list_response.json()["data"]]
        assert persisted_memory_ids == [memory_id]

        persisted_memory_detail_response = fresh_client.get(f"/api/knowledge/memory-items/{memory_id}")
        assert persisted_memory_detail_response.status_code == 200
        persisted_memory_detail = persisted_memory_detail_response.json()["data"]
        assert persisted_memory_detail["memory_id"] == memory_id
        assert persisted_memory_detail["relations"][0]["target_ref"] == artifact_id

        owner_memory_response = client.post(
            "/api/knowledge/memory-items",
            json={
                "source_type": "owner_note",
                "source_refs": ["note-1"],
                "content_markdown": "# 老板观察\n- 继续跟踪这个方向",
                "suggested_memory_type": "owner_observation",
                "tags": ["follow_up"],
                "sensitivity": "public_internal",
                "client_seen_context_snapshot_id": "ctx-v1",
            },
        )
        assert owner_memory_response.status_code == 200
        owner_memory_id = owner_memory_response.json()["data"]["memory_id"]

        persisted_owner_memory_response = fresh_client.get(f"/api/knowledge/memory-items/{owner_memory_id}")
        assert persisted_owner_memory_response.status_code == 200
        assert persisted_owner_memory_response.json()["data"]["memory_type"] == "owner_observation"

        brief_response = client.post(
            "/api/requests/briefs",
            json={
                "raw_text": "请正式研究浦发银行",
                "source": "owner_command",
                "requested_scope": {
                    "intent": "formal_investment_decision",
                    "asset_scope": "a_share_common_stock",
                    "target_action": "approve_trade",
                },
            },
        )
        brief = brief_response.json()["data"]
        task_response = client.post(
            f"/api/requests/briefs/{brief['brief_id']}/confirmation",
            json={"decision": "confirm", "client_seen_version": 1},
        )
        assert task_response.status_code == 200
        workflow_id = task_response.json()["data"]["workflow_id"]

        start_response = client.post(
            f"/api/workflows/{workflow_id}/commands",
            json={"command_type": "start_stage", "payload": {"stage": "S0"}, "client_seen_stage_version": 1},
        )
        assert start_response.status_code == 200

        persisted_workflow_response = fresh_client.get(f"/api/workflows/{workflow_id}")
        assert persisted_workflow_response.status_code == 200
        persisted_workflow = persisted_workflow_response.json()["data"]
        assert persisted_workflow["workflow_id"] == workflow_id
        assert persisted_workflow["stages"][0]["stage"] == "S0"
        assert persisted_workflow["stages"][0]["node_status"] == "running"

        persisted_dossier_response = fresh_client.get(f"/api/workflows/{workflow_id}/dossier")
        assert persisted_dossier_response.status_code == 200
        assert persisted_dossier_response.json()["data"]["stage_rail"][0]["node_status"] == "running"

        with engine.connect() as connection:
            counts = {
                "artifact": connection.execute(text("select count(*) from artifact")).scalar_one(),
                "command": connection.execute(text("select count(*) from collaboration_command")).scalar_one(),
                "event": connection.execute(text("select count(*) from collaboration_event")).scalar_one(),
                "handoff": connection.execute(text("select count(*) from handoff_packet")).scalar_one(),
                "memory_item": connection.execute(text("select count(*) from memory_item")).scalar_one(),
                "memory_version": connection.execute(text("select count(*) from memory_version")).scalar_one(),
                "memory_extraction_result": connection.execute(text("select count(*) from memory_extraction_result")).scalar_one(),
                "memory_relation": connection.execute(text("select count(*) from memory_relation")).scalar_one(),
                "task_envelope": connection.execute(text("select count(*) from task_envelope")).scalar_one(),
                "workflow": connection.execute(text("select count(*) from workflow")).scalar_one(),
                "workflow_stage": connection.execute(text("select count(*) from workflow_stage")).scalar_one(),
            }

        assert counts == {
            "artifact": 1,
            "command": 1,
            "event": 1,
            "handoff": 1,
            "memory_item": 2,
            "memory_version": 2,
            "memory_extraction_result": 2,
            "memory_relation": 1,
            "task_envelope": 1,
            "workflow": 1,
            "workflow_stage": 8,
        }


def test_task_center_merges_persisted_tasks_after_runtime_restart():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        first_client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        first_brief_response = first_client.post(
            "/api/requests/briefs",
            json={
                "raw_text": "第一次研究任务",
                "source": "owner_command",
                "requested_scope": {
                    "intent": "formal_investment_decision",
                    "asset_scope": "a_share_common_stock",
                    "target_action": "approve_trade",
                },
            },
        )
        first_brief = first_brief_response.json()["data"]
        first_task_response = first_client.post(
            f"/api/requests/briefs/{first_brief['brief_id']}/confirmation",
            json={"decision": "confirm", "client_seen_version": 1},
        )
        first_task_id = first_task_response.json()["data"]["task_id"]

        restarted_client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        assert [item["task_id"] for item in restarted_client.get("/api/tasks").json()["data"]["task_center"]] == [
            first_task_id
        ]

        second_brief_response = restarted_client.post(
            "/api/requests/briefs",
            json={
                "raw_text": "第二次研究任务",
                "source": "owner_command",
                "requested_scope": {
                    "intent": "formal_investment_decision",
                    "asset_scope": "a_share_common_stock",
                    "target_action": "approve_trade",
                },
            },
        )
        second_brief = second_brief_response.json()["data"]
        second_task_response = restarted_client.post(
            f"/api/requests/briefs/{second_brief['brief_id']}/confirmation",
            json={"decision": "confirm", "client_seen_version": 1},
        )
        second_task_id = second_task_response.json()["data"]["task_id"]

        task_ids = [item["task_id"] for item in restarted_client.get("/api/tasks").json()["data"]["task_center"]]

        assert task_ids == [first_task_id, second_task_id]


def test_api_persists_full_investment_runtime_artifacts_in_dossier_after_restart():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))

        brief_response = client.post(
            "/api/requests/briefs",
            json={
                "raw_text": "请正式研究浦发银行并走完纸面投资闭环",
                "source": "owner_command",
                "requested_scope": {
                    "intent": "formal_investment_decision",
                    "asset_scope": "a_share_common_stock",
                    "target_action": "approve_trade",
                },
            },
        )
        assert brief_response.status_code == 200
        brief = brief_response.json()["data"]
        task_response = client.post(
            f"/api/requests/briefs/{brief['brief_id']}/confirmation",
            json={"decision": "confirm", "client_seen_version": 1},
        )
        assert task_response.status_code == 200
        task = task_response.json()["data"]
        workflow_id = task["workflow_id"]

        data_readiness_ref = _write_service_artifact(
            client,
            workflow_id,
            "S1",
            "data_collection_quality",
            "DataReadinessReport",
            {
                "quality_band": "normal",
                "decision_core_status": "pass",
                "execution_core_status": "pass",
                "lineage_refs": ["lineage-600000"],
                "risk_constraints": ["risk-budget-1"],
            },
        )
        macro_ref = _write_agent_artifact(client, workflow_id, "S2", "run-macro_analyst", "AnalystMemo", _memo("macro", 2))
        fundamental_ref = _write_agent_artifact(
            client,
            workflow_id,
            "S2",
            "run-fundamental_analyst",
            "AnalystMemo",
            _memo("fundamental", 3),
        )
        quant_ref = _write_agent_artifact(client, workflow_id, "S2", "run-quant_analyst", "AnalystMemo", _memo("quant", 2))
        event_ref = _write_agent_artifact(client, workflow_id, "S2", "run-event_analyst", "AnalystMemo", _memo("event", 1))
        cio_ref = _write_agent_artifact(
            client,
            workflow_id,
            "S4",
            "run-cio",
            "CIODecisionMemo",
            {
                "decision": "buy",
                "target_symbol": "600000.SH",
                "target_weight": 0.10,
                "decision_rationale": "四位分析师意见收敛，执行数据可用。",
                "deviation_reason": "",
            },
        )
        guard_ref = _write_service_artifact(
            client,
            workflow_id,
            "S4",
            "risk_engine",
            "DecisionGuardResult",
            {
                "major_deviation": False,
                "low_action_conviction": False,
                "retained_hard_dissent": False,
                "reason_codes": [],
                "owner_exception_candidate_ref": None,
                "reopen_recommendation_ref": None,
            },
        )
        risk_ref = _write_agent_artifact(
            client,
            workflow_id,
            "S5",
            "run-risk_officer",
            "RiskReviewReport",
            {
                "review_result": "approved",
                "owner_exception_required": False,
                "reason_codes": [],
                "risk_summary": "risk accepted",
            },
        )
        execution_ref = _write_service_artifact(
            client,
            workflow_id,
            "S6",
            "trade_execution",
            "PaperExecutionReceipt",
            {
                "paper_order_id": "paper-order-runtime-1",
                "decision_memo_ref": cio_ref,
                "pricing_method": "minute_vwap",
                "fill_status": "filled",
                "fill_price": 10.2,
                "fill_quantity": 1000,
                "fees": {"commission": 5},
                "taxes": {"stamp_tax": 0},
                "slippage": {"policy_bps": 5},
                "t_plus_one_state": "locked_until_next_trading_day",
            },
        )
        attribution_ref = _write_service_artifact(
            client,
            workflow_id,
            "S7",
            "performance_attribution_evaluation",
            "AttributionReport",
            {
                "status": "completed",
                "period": "runtime-smoke",
                "decision_quality": "pass",
                "execution_quality": "pass",
                "needs_cfo_interpretation": False,
            },
        )
        cfo_ref = _write_agent_artifact(
            client,
            workflow_id,
            "S7",
            "run-cfo",
            "CFOInterpretation",
            {
                "summary_for_owner": "纸面执行已完成，归因无异常。",
                "attribution_ref": attribution_ref,
                "recommended_followups": [],
            },
        )
        handoff_response = client.post(
            "/api/gateway/handoffs",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "from_stage": "S3",
                "to_stage_or_agent": "S4",
                "producer_agent_id_or_service": "cio",
                "source_artifact_refs": [macro_ref, fundamental_ref, quant_ref, event_ref],
                "summary": "辩论收敛，无硬异议保留。",
                "open_questions": [],
                "blockers": [],
                "decisions_made": ["enter_s4"],
                "invalidated_artifacts": [],
                "preserved_artifacts": [macro_ref, fundamental_ref, quant_ref, event_ref],
                "idempotency_key": f"{workflow_id}-handoff-s3-s4",
            },
        )
        assert handoff_response.status_code == 200
        debate_handoff_ref = handoff_response.json()["data"]["object_id"]

        _complete_stage(client, workflow_id, "S0", [task["task_id"]])
        _complete_stage(client, workflow_id, "S1", [data_readiness_ref])
        _complete_stage(client, workflow_id, "S2", [macro_ref, fundamental_ref, quant_ref, event_ref])
        _complete_stage(client, workflow_id, "S3", [debate_handoff_ref])
        _complete_stage(client, workflow_id, "S4", [cio_ref, guard_ref])
        _complete_stage(client, workflow_id, "S5", [risk_ref])
        _complete_stage(client, workflow_id, "S6", [execution_ref])
        _complete_stage(client, workflow_id, "S7", [attribution_ref, cfo_ref])

        fresh_client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        dossier_response = fresh_client.get(f"/api/workflows/{workflow_id}/dossier")
        assert dossier_response.status_code == 200
        dossier = dossier_response.json()["data"]

        assert dossier["stage_rail"][-1]["stage"] == "S7"
        assert dossier["stage_rail"][-1]["node_status"] == "completed"
        assert dossier["data_readiness"]["decision_core_status"] == "pass"
        assert dossier["data_readiness"]["execution_core_status"] == "pass"
        assert {row["role"] for row in dossier["analyst_stance_matrix"]} == {"macro", "fundamental", "quant", "event"}
        assert dossier["decision_guard"]["status"] == "pass"
        assert dossier["risk_review"]["verdict"] == "approved"
        assert dossier["paper_execution"]["status"] == "filled"
        assert dossier["attribution"]["status"] == "completed"
        assert execution_ref in dossier["evidence_map"]["artifact_refs"]

        persisted_execution = fresh_client.get(f"/api/artifacts/{execution_ref}").json()["data"]
        assert persisted_execution["producer_type"] == "service"
        assert persisted_execution["workflow_id"] == workflow_id


def _write_agent_artifact(client: TestClient, workflow_id: str, stage: str, run_id: str, artifact_type: str, payload: dict) -> str:
    response = client.post(
        "/api/gateway/artifacts",
        json={
            "workflow_id": workflow_id,
            "attempt_no": 1,
            "stage": stage,
            "source_agent_run_id": run_id,
            "context_snapshot_id": "ctx-v1",
            "artifact_type": artifact_type,
            "schema_version": "1.0.0",
            "payload": payload,
            "source_refs": payload.get("evidence_refs", []),
            "idempotency_key": f"{workflow_id}-{stage}-{run_id}-{artifact_type}",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["object_id"]


def _write_service_artifact(
    client: TestClient,
    workflow_id: str,
    stage: str,
    producer_service: str,
    artifact_type: str,
    payload: dict,
) -> str:
    response = client.post(
        "/api/gateway/artifacts",
        json={
            "workflow_id": workflow_id,
            "attempt_no": 1,
            "stage": stage,
            "producer_service": producer_service,
            "context_snapshot_id": "ctx-v1",
            "artifact_type": artifact_type,
            "schema_version": "1.0.0",
            "payload": payload,
            "source_refs": payload.get("evidence_refs", []),
            "idempotency_key": f"{workflow_id}-{stage}-{producer_service}-{artifact_type}",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["object_id"]


def _complete_stage(client: TestClient, workflow_id: str, stage: str, artifact_refs: list[str]) -> None:
    workflow = client.get(f"/api/workflows/{workflow_id}").json()["data"]
    stage_version = next(item["stage_version"] for item in workflow["stages"] if item["stage"] == stage)
    start_response = client.post(
        f"/api/workflows/{workflow_id}/commands",
        json={"command_type": "start_stage", "payload": {"stage": stage}, "client_seen_stage_version": stage_version},
    )
    assert start_response.status_code == 200
    workflow = client.get(f"/api/workflows/{workflow_id}").json()["data"]
    stage_version = next(item["stage_version"] for item in workflow["stages"] if item["stage"] == stage)
    complete_response = client.post(
        f"/api/workflows/{workflow_id}/commands",
        json={
            "command_type": "complete_stage",
            "payload": {"stage": stage, "artifact_refs": artifact_refs},
            "client_seen_stage_version": stage_version,
        },
    )
    assert complete_response.status_code == 200


def _memo(role: str, direction_score: int) -> dict:
    return {
        "role": role,
        "direction": "positive",
        "direction_score": direction_score,
        "confidence": 0.82,
        "hard_dissent": False,
        "summary": f"{role} memo",
        "evidence_refs": [f"evidence-{role}"],
    }
