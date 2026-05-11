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


def test_ic_context_chair_and_position_disposal_are_first_class_persistent_artifacts():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        apply_wi001_seed(engine)

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))

        brief_response = client.post(
            "/api/requests/briefs",
            json={
                "raw_text": "请正式研究浦发银行并准备 IC 材料",
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
        workflow_id = task_response.json()["data"]["workflow_id"]

        ic_context_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S2",
                "source_agent_run_id": "run-investment_researcher",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "ICContextPackage",
                "schema_version": "1.0.0",
                "payload": {
                    "topic_id": "topic-wi010-ic",
                    "request_brief_ref": brief["brief_id"],
                    "data_readiness_ref": "data-readiness-wi010",
                    "market_state_ref": "market-state-wi010",
                    "service_result_refs": ["service-result-wi010"],
                    "portfolio_context_ref": "portfolio-context-wi010",
                    "risk_constraint_refs": ["risk-constraint-wi010"],
                    "research_package_refs": ["research-package-wi010"],
                    "reflection_hit_refs": [],
                    "role_attachment_refs": ["role-attachment-wi010"],
                    "context_snapshot_id": "ctx-v1",
                },
                "source_refs": [brief["brief_id"]],
                "idempotency_key": "wi010-ic-context",
            },
        )
        assert ic_context_response.status_code == 200
        ic_context_artifact_id = ic_context_response.json()["data"]["object_id"]

        chair_brief_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S2",
                "source_agent_run_id": "run-cio",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "ICChairBrief",
                "schema_version": "1.0.0",
                "payload": {
                    "decision_question": "是否将浦发银行纳入纸面组合观察买入候选？",
                    "scope_boundary": "仅 A 股纸面投研，不触发真实交易。",
                    "key_tensions": ["估值修复", "资产质量不确定"],
                    "must_answer_questions": ["数据是否足够", "风险是否可控"],
                    "time_budget": "T+0",
                    "action_standard": "证据充分且无 hard blocker 才能进入下一阶段",
                    "risk_constraints_to_respect": ["risk-constraint-wi010"],
                    "forbidden_assumptions": ["不得预设买入结论"],
                    "no_preset_decision_attestation": True,
                },
                "source_refs": [ic_context_artifact_id],
                "idempotency_key": "wi010-chair-brief",
            },
        )
        assert chair_brief_response.status_code == 200
        chair_brief_artifact_id = chair_brief_response.json()["data"]["object_id"]

        invalid_ic_context_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S2",
                "source_agent_run_id": "run-investment_researcher",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "ICContextPackage",
                "schema_version": "1.0.0",
                "payload": {
                    "request_brief_ref": brief["brief_id"],
                    "data_readiness_ref": "data-readiness-wi010",
                    "market_state_ref": "market-state-wi010",
                    "service_result_refs": ["service-result-wi010"],
                    "portfolio_context_ref": "portfolio-context-wi010",
                    "risk_constraint_refs": ["risk-constraint-wi010"],
                    "research_package_refs": ["research-package-wi010"],
                    "role_attachment_refs": ["role-attachment-wi010"],
                    "context_snapshot_id": "ctx-v1",
                },
                "source_refs": [brief["brief_id"]],
                "idempotency_key": "wi010-ic-context-missing-topic",
            },
        )
        assert invalid_ic_context_response.status_code == 403
        assert invalid_ic_context_response.json()["error"]["reason_code"] == "schema_validation_failed"

        preset_chair_brief_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S2",
                "source_agent_run_id": "run-cio",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "ICChairBrief",
                "schema_version": "1.0.0",
                "payload": {
                    "decision_question": "是否直接买入？",
                    "scope_boundary": "仅 A 股纸面投研。",
                    "key_tensions": [],
                    "must_answer_questions": [],
                    "time_budget": "T+0",
                    "action_standard": "直接执行",
                    "risk_constraints_to_respect": [],
                    "forbidden_assumptions": [],
                    "no_preset_decision_attestation": False,
                },
                "source_refs": [ic_context_artifact_id],
                "idempotency_key": "wi010-chair-brief-preset-denied",
            },
        )
        assert preset_chair_brief_response.status_code == 403
        assert preset_chair_brief_response.json()["error"]["reason_code"] == "schema_validation_failed"

        position_task_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S7",
                "producer_service": "trade_execution",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "PositionDisposalTask",
                "schema_version": "1.0.0",
                "payload": {
                    "task_id": "position-disposal-wi010",
                    "symbol": "600000.SH",
                    "triggers": ["drawdown_limit_hit", "risk_budget_breach"],
                    "priority": "P0",
                    "risk_gate_present": True,
                    "execution_core_guard_present": True,
                    "direct_execution_allowed": False,
                    "workflow_route": "S5_risk_review",
                    "reason_code": "position_disposal_requires_risk_review",
                },
                "source_refs": [chair_brief_artifact_id],
                "idempotency_key": "wi010-position-disposal",
            },
        )
        assert position_task_response.status_code == 200
        position_task_artifact_id = position_task_response.json()["data"]["object_id"]

        direct_execution_task_response = client.post(
            "/api/gateway/artifacts",
            json={
                "workflow_id": workflow_id,
                "attempt_no": 1,
                "stage": "S7",
                "producer_service": "trade_execution",
                "context_snapshot_id": "ctx-v1",
                "artifact_type": "PositionDisposalTask",
                "schema_version": "1.0.0",
                "payload": {
                    "task_id": "position-disposal-direct-denied",
                    "symbol": "600000.SH",
                    "triggers": ["drawdown_limit_hit"],
                    "priority": "P0",
                    "risk_gate_present": False,
                    "execution_core_guard_present": False,
                    "direct_execution_allowed": True,
                    "workflow_route": "S7_direct_execution",
                    "reason_code": "direct_execution_requested",
                },
                "source_refs": [chair_brief_artifact_id],
                "idempotency_key": "wi010-position-disposal-direct-denied",
            },
        )
        assert direct_execution_task_response.status_code == 403
        assert direct_execution_task_response.json()["error"]["reason_code"] == "position_disposal_requires_risk_review"

        fresh_client = TestClient(build_app(ApiRuntime(database_url=database_url)))

        for artifact_id, expected_type in (
            (ic_context_artifact_id, "ICContextPackage"),
            (chair_brief_artifact_id, "ICChairBrief"),
            (position_task_artifact_id, "PositionDisposalTask"),
        ):
            artifact_response = fresh_client.get(f"/api/artifacts/{artifact_id}")
            assert artifact_response.status_code == 200
            assert artifact_response.json()["data"]["artifact_type"] == expected_type

        dossier_response = fresh_client.get(f"/api/workflows/{workflow_id}/dossier")
        assert dossier_response.status_code == 200
        dossier = dossier_response.json()["data"]
        assert dossier["ic_context"]["artifact_ref"] == ic_context_artifact_id
        assert dossier["ic_context"]["topic_id"] == "topic-wi010-ic"
        assert dossier["ic_context"]["status"] == "ready"
        assert dossier["chair_brief"]["artifact_ref"] == chair_brief_artifact_id
        assert dossier["chair_brief"]["no_preset_decision_attestation"] is True
        assert dossier["position_disposal"]["artifact_ref"] == position_task_artifact_id
        assert dossier["position_disposal"]["task_id"] == "position-disposal-wi010"
        assert dossier["position_disposal"]["direct_execution_allowed"] is False
        assert dossier["position_disposal"]["workflow_route"] == "S5_risk_review"
        assert dossier["forbidden_actions"]["execution_core_blocked_no_trade"]["action_visible"] is False

        with engine.connect() as connection:
            row = connection.execute(
                text("select task_id, symbol, priority, direct_execution_allowed, workflow_route, reason_code from position_disposal_task")
            ).mappings().one()
        assert row["task_id"] == "position-disposal-wi010"
        assert row["symbol"] == "600000.SH"
        assert row["priority"] == "P0"
        assert row["direct_execution_allowed"] is False
        assert row["workflow_route"] == "S5_risk_review"
        assert row["reason_code"] == "position_disposal_requires_risk_review"

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


def test_finance_asset_updates_are_persisted_after_runtime_restart():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        for payload in [
            {
                "asset_id": "cash-persisted-1",
                "asset_type": "cash",
                "valuation": {"amount": 250000, "currency": "CNY"},
                "valuation_date": "2026-05-03",
                "source": "owner",
                "client_seen_version": 1,
            },
            {
                "asset_id": "fund-persisted-1",
                "asset_type": "fund",
                "valuation": {"amount": 90000, "currency": "CNY"},
                "valuation_date": "2026-05-03",
                "source": "auto_quote",
                "client_seen_version": 1,
            },
        ]:
            response = client.post("/api/finance/assets", json=payload)
            assert response.status_code == 200

        restarted_client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        overview_response = restarted_client.get("/api/finance/overview")
        assert overview_response.status_code == 200
        overview = overview_response.json()["data"]
        assets_by_id = {item["asset_id"]: item for item in overview["asset_profile"]}

        assert assets_by_id["cash-persisted-1"]["valuation"]["amount"] == 250000
        assert assets_by_id["fund-persisted-1"]["boundary_label"] == "finance_planning_only"
        assert overview["finance_health"]["liquidity"] == 250000


def test_owner_approval_decisions_are_persisted_after_runtime_restart():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        approvals_response = client.get("/api/approvals")
        assert approvals_response.status_code == 200
        approval_id = approvals_response.json()["data"]["approval_center"][0]["approval_id"]

        decision_response = client.post(
            f"/api/approvals/{approval_id}/decision",
            json={
                "decision": "approved",
                "comment": "认可例外审批材料",
                "accepted_risks": ["single_name_deviation"],
                "requested_changes": [],
                "client_seen_version": 1,
            },
        )
        assert decision_response.status_code == 200

        restarted_client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        persisted_response = restarted_client.get("/api/approvals")
        assert persisted_response.status_code == 200
        approvals_by_id = {
            item["approval_id"]: item for item in persisted_response.json()["data"]["approval_center"]
        }

        assert approvals_by_id[approval_id]["decision"] == "approved"
        assert approvals_by_id[approval_id]["effective_scope"] == "current_attempt_only"


def test_gateway_paper_execution_artifacts_are_mirrored_to_dedicated_tables():
    with _postgres_container() as database_url:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        client = TestClient(build_app(ApiRuntime(database_url=database_url)))
        workflow_id = "workflow-paper-table-1"
        account_ref = _write_service_artifact(
            client,
            workflow_id,
            "S6",
            "trade_execution",
            "PaperAccount",
            {
                "paper_account_id": "paper-account-table-1",
                "cash": {"amount": 1_000_000, "currency": "CNY"},
                "positions": {},
                "total_value": {"amount": 1_000_000, "currency": "CNY"},
                "cost_basis": {},
                "return": {"amount": 0, "currency": "CNY"},
                "drawdown": 0,
                "risk_budget": {"cash_floor": {"amount": 50_000, "currency": "CNY"}},
                "benchmark_ref": "baseline-cash",
            },
        )
        order_ref = _write_service_artifact(
            client,
            workflow_id,
            "S6",
            "trade_execution",
            "PaperOrder",
            {
                "paper_order_id": "paper-order-table-1",
                "workflow_id": workflow_id,
                "decision_memo_ref": "cio-memo-1",
                "symbol": "600000.SH",
                "side": "buy",
                "target_quantity_or_weight": 1000,
                "price_range": {"max_price": 10.5},
                "urgency": "normal",
                "execution_core_snapshot_ref": "exec-core-1",
                "status": "released",
            },
        )
        receipt_ref = _write_service_artifact(
            client,
            workflow_id,
            "S6",
            "trade_execution",
            "PaperExecutionReceipt",
            {
                "paper_order_id": "paper-order-table-1",
                "decision_memo_ref": "cio-memo-1",
                "execution_window": "30m",
                "pricing_method": "minute_vwap",
                "market_data_refs": ["minute-bars-1"],
                "fill_status": "filled",
                "fill_price": 10.2,
                "fill_quantity": 1000,
                "fees": {"commission": 5},
                "taxes": {"stamp_tax": 0},
                "slippage": {"policy_bps": 5},
                "t_plus_one_state": "locked_until_next_trading_day",
            },
        )

        engine = create_engine(database_url, future=True)
        with engine.connect() as connection:
            paper_account = connection.execute(
                text("select account_id, cash, total_value from paper_account where account_id = 'paper-account-table-1'")
            ).mappings().first()
            paper_order = connection.execute(
                text("select paper_order_id, workflow_id, status from paper_order where paper_order_id = 'paper-order-table-1'")
            ).mappings().first()
            receipt = connection.execute(
                text("select receipt_id, paper_order_id, fill_status from paper_execution_receipt where paper_order_id = 'paper-order-table-1'")
            ).mappings().first()

        assert account_ref
        assert order_ref
        assert receipt_ref
        assert dict(paper_account) == {"account_id": "paper-account-table-1", "cash": 1_000_000, "total_value": 1_000_000}
        assert dict(paper_order) == {
            "paper_order_id": "paper-order-table-1",
            "workflow_id": workflow_id,
            "status": "released",
        }
        assert dict(receipt) == {
            "receipt_id": receipt_ref,
            "paper_order_id": "paper-order-table-1",
            "fill_status": "filled",
        }


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
