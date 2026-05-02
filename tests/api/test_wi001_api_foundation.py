from __future__ import annotations

from fastapi.testclient import TestClient

from velentrade.api.app import build_app


def test_team_and_agent_profile_endpoints_expose_wi001_read_models():
    client = TestClient(build_app())

    team_response = client.get("/api/team")
    assert team_response.status_code == 200
    team_payload = team_response.json()["data"]
    assert team_payload["team_health"]["healthy_agent_count"] == 9
    assert len(team_payload["agent_cards"]) == 9

    profile_response = client.get("/api/team/macro_analyst")
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()["data"]
    assert profile_payload["agent_id"] == "macro_analyst"
    assert profile_payload["display_name"] == "Macro Analyst"
    assert "finance_sensitive_raw" in profile_payload["cannot_do"]
    assert "request_data" in profile_payload["collaboration_commands"]
    assert profile_payload["config_draft_entry"] == "governance_draft_only"

    config_response = client.get("/api/team/macro_analyst/capability-config")
    assert config_response.status_code == 200
    config_payload = config_response.json()["data"]
    assert config_payload["agent_id"] == "macro_analyst"
    assert config_payload["forbidden_direct_update_reason"] == "governance_draft_only"
    assert config_payload["effective_scope_options"] == ["new_task", "new_attempt"]


def test_gateway_and_collaboration_endpoints_accept_append_only_requests():
    client = TestClient(build_app())

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
    command_payload = command_response.json()["data"]
    assert command_payload["admission_status"] == "accepted"
    assert command_payload["command_type"] == "request_evidence"

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
    artifact_payload = artifact_response.json()["data"]
    assert artifact_payload["accepted"] is True
    assert artifact_payload["object_type"] == "artifact"
    artifact_id = artifact_payload["object_id"]

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
    assert event_response.json()["data"]["object_type"] == "event"

    handoff_response = client.post(
        "/api/gateway/handoffs",
        json={
            "workflow_id": "wf-1",
            "attempt_no": 1,
            "from_stage": "S1",
            "to_stage_or_agent": "S2",
            "producer_agent_id_or_service": "investment_researcher",
            "source_artifact_refs": ["artifact-1"],
            "summary": "交接到下一阶段",
            "open_questions": [],
            "blockers": [],
            "decisions_made": [],
            "invalidated_artifacts": [],
            "preserved_artifacts": ["artifact-1"],
            "idempotency_key": "handoff-1",
        },
    )
    assert handoff_response.status_code == 200
    assert handoff_response.json()["data"]["object_type"] == "handoff"

    memory_response = client.post(
        "/api/gateway/memory-items",
        json={
            "source_agent_run_id": "run-investment_researcher",
            "context_snapshot_id": "ctx-v1",
            "operation": "capture",
            "content_markdown": "# 研究笔记\n- 只作背景",
            "payload": {"symbol_refs": ["600000.SH"]},
            "source_refs": ["artifact-1"],
            "sensitivity": "public_internal",
            "idempotency_key": "memory-1",
        },
    )
    assert memory_response.status_code == 200
    memory_payload = memory_response.json()["data"]
    assert memory_payload["object_type"] == "memory_item"
    memory_id = memory_payload["object_id"]

    artifact_read_response = client.get(f"/api/artifacts/{artifact_id}")
    assert artifact_read_response.status_code == 200
    assert artifact_read_response.json()["data"]["artifact_type"] == "ResearchPackage"

    agent_runs_response = client.get("/api/workflows/wf-1/agent-runs")
    assert agent_runs_response.status_code == 200
    run_ids = [item["agent_run_id"] for item in agent_runs_response.json()["data"]]
    assert "run-investment_researcher" in run_ids

    event_read_response = client.get("/api/workflows/wf-1/collaboration-events")
    assert event_read_response.status_code == 200
    event_types = [item["event_type"] for item in event_read_response.json()["data"]]
    assert "artifact_submitted" in event_types

    handoff_read_response = client.get("/api/workflows/wf-1/handoffs")
    assert handoff_read_response.status_code == 200
    summaries = [item["summary"] for item in handoff_read_response.json()["data"]]
    assert "交接到下一阶段" in summaries

    memory_list_response = client.get("/api/knowledge/memory-items")
    assert memory_list_response.status_code == 200
    memory_list_payload = memory_list_response.json()["data"]
    assert any(item["memory_id"] == memory_id for item in memory_list_payload)

    memory_detail_response = client.get(f"/api/knowledge/memory-items/{memory_id}")
    assert memory_detail_response.status_code == 200
    memory_detail_payload = memory_detail_response.json()["data"]
    assert memory_detail_payload["memory_id"] == memory_id
    assert memory_detail_payload["memory_type"] == "research_note"
    assert memory_detail_payload["why_included"] == "fenced_background_context_only"
    assert memory_detail_payload["promotion_state"] == "validated_context"

    relation_response = client.post(
        f"/api/knowledge/memory-items/{memory_id}/relations",
        json={
            "target_ref": artifact_id,
            "relation_type": "supports",
            "reason": "该笔记支持资料包结论",
            "evidence_refs": [artifact_id],
            "client_seen_version_id": memory_detail_payload["current_version_id"],
        },
    )
    assert relation_response.status_code == 200
    relation_payload = relation_response.json()["data"]
    assert relation_payload["source_memory_id"] == memory_id
    assert relation_payload["target_ref"] == artifact_id
    assert relation_payload["relation_type"] == "supports"


def test_owner_memory_capture_endpoint_creates_append_only_memory_item():
    client = TestClient(build_app())

    response = client.post(
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

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["memory_type"] == "owner_observation"
    assert payload["promotion_state"] == "validated_context"
    assert payload["why_included"] == "fenced_background_context_only"
    assert payload["source_refs"] == ["note-1"]


def test_finance_overview_and_devops_health_endpoints_expose_read_models():
    client = TestClient(build_app())

    finance_response = client.get("/api/finance/overview")
    assert finance_response.status_code == 200
    finance_payload = finance_response.json()["data"]
    assert any(item["asset_type"] == "fund" for item in finance_payload["asset_profile"])
    assert finance_payload["finance_health"]["risk_budget"]["budget_ref"] == "risk-budget-finance-v1"
    assert finance_payload["sensitive_data_notice"]["redaction_applied"] is True

    health_response = client.get("/api/devops/health")
    assert health_response.status_code == 200
    health_payload = health_response.json()["data"]
    assert health_payload["routine_checks"][0]["status"] == "observed"
    assert "incident_open_total" in health_payload["metrics"]
    assert health_payload["recovery"][0]["investment_resume_allowed"] is False


def test_request_brief_confirmation_and_task_workflow_read_api():
    client = TestClient(build_app())

    brief_response = client.post(
        "/api/requests/briefs",
        json={
            "raw_text": "学习热点事件",
            "source": "owner_command",
            "requested_scope": {"intent": "learn_hot_event", "asset_scope": "a_share_common_stock", "target_action": "research"},
            "authorization_boundary": "research_only",
        },
    )
    assert brief_response.status_code == 200
    brief = brief_response.json()["data"]
    assert brief["owner_confirmation_status"] == "draft"
    assert brief["route_type"] == "research_task"
    assert brief["creates_agent_run"] is True

    tasks_before = client.get("/api/tasks").json()["data"]
    assert tasks_before["task_center"] == []

    confirmation_response = client.post(
        f"/api/requests/briefs/{brief['brief_id']}/confirmation",
        json={"decision": "confirm", "client_seen_version": 1},
    )
    assert confirmation_response.status_code == 200
    task = confirmation_response.json()["data"]
    assert task["task_type"] == "research_task"
    assert task["current_state"] == "ready"
    assert task["reason_code"] == "request_brief_confirmed"

    tasks_after = client.get("/api/tasks").json()["data"]
    assert [item["task_id"] for item in tasks_after["task_center"]] == [task["task_id"]]

    investment_brief_response = client.post(
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
    investment_brief = investment_brief_response.json()["data"]
    investment_task = client.post(
        f"/api/requests/briefs/{investment_brief['brief_id']}/confirmation",
        json={"decision": "confirm", "client_seen_version": 1},
    ).json()["data"]
    workflow_response = client.get(f"/api/workflows/{investment_task['workflow_id']}")
    assert workflow_response.status_code == 200
    workflow = workflow_response.json()["data"]
    assert workflow["workflow_id"] == investment_task["workflow_id"]
    assert workflow["current_stage"] == "S0"
    assert len(workflow["stages"]) == 8

    cancel_response = client.post(
        f"/api/requests/briefs/{investment_brief['brief_id']}/confirmation",
        json={"decision": "cancel", "client_seen_version": 1},
    )
    assert cancel_response.status_code == 409


def test_governance_finance_knowledge_devops_and_approval_api_surfaces():
    client = TestClient(build_app())

    asset_response = client.post(
        "/api/finance/assets",
        json={
            "asset_type": "fund",
            "valuation": {"amount": 12345, "currency": "CNY"},
            "valuation_date": "2026-05-02",
            "source": "owner",
            "client_seen_version": 1,
        },
    )
    assert asset_response.status_code == 200
    asset_payload = asset_response.json()["data"]
    assert asset_payload["asset_type"] == "fund"
    assert asset_payload["boundary_label"] == "finance_planning_only"

    memory_response = client.post(
        "/api/knowledge/memory-items",
        json={
            "source_type": "owner_note",
            "source_refs": ["note-search"],
            "content_markdown": "# API 检索笔记\n- 产业链线索",
            "suggested_memory_type": "owner_observation",
            "tags": ["searchable"],
            "sensitivity": "public_internal",
            "client_seen_context_snapshot_id": "ctx-v1",
        },
    )
    assert memory_response.status_code == 200
    search_response = client.get("/api/knowledge/search?q=API")
    assert search_response.status_code == 200
    search_payload = search_response.json()["data"]
    assert any(item["memory_id"] == memory_response.json()["data"]["memory_id"] for item in search_payload["results"])

    incidents_response = client.get("/api/devops/incidents")
    assert incidents_response.status_code == 200
    incidents_payload = incidents_response.json()["data"]
    assert len(incidents_payload) >= 1
    assert incidents_payload[0]["investment_resume_allowed"] is False

    changes_response = client.get("/api/governance/changes")
    assert changes_response.status_code == 200
    changes_payload = changes_response.json()["data"]
    assert any(item["change_id"] == "gov-change-001" for item in changes_payload)

    draft_response = client.post(
        "/api/team/quant_analyst/capability-drafts",
        json={
            "agent_id": "quant_analyst",
            "draft_title": "调整默认模型",
            "change_set": {"model_route": "balanced"},
            "impact_level_hint": "high",
            "validation_plan_refs": ["schema"],
            "rollback_plan_ref": "rollback-1",
            "effective_scope": "new_task",
            "client_seen_profile_version": "1.0.0",
            "client_seen_context_snapshot_id": "ctx-v1",
        },
    )
    assert draft_response.status_code == 200
    draft_payload = draft_response.json()["data"]
    assert draft_payload["agent_id"] == "quant_analyst"
    assert draft_payload["governance_change_ref"].startswith("gov-change-")
    assert draft_payload["effective_scope"] == "new_task"

    approvals_response = client.get("/api/approvals")
    assert approvals_response.status_code == 200
    approval_payload = approvals_response.json()["data"]
    assert approval_payload["approval_center"][0]["decision"] == "pending"

    decision_response = client.post(
        f"/api/approvals/{approval_payload['approval_center'][0]['approval_id']}/decision",
        json={"decision": "request_changes", "client_seen_version": 1, "comment": "补充影响说明"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["data"]["decision"] == "request_changes"
