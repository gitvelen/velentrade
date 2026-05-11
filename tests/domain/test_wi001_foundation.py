from velentrade.domain.agents.registry import (
    OFFICIAL_AGENT_IDS,
    build_agent_capability_profiles,
    build_team_read_model,
    validate_agent_registry,
)
from velentrade.domain.collaboration.models import (
    AgentRun,
    CollaborationCommand,
    CollaborationSession,
    HandoffPacket,
)
from velentrade.domain.gateway.authority import AuthorityGateway, DirectBusinessWrite
from velentrade.domain.memory.models import MemoryCapture
from velentrade.domain.scope.registry import build_scope_boundary_report, validate_service_registry
from velentrade.domain.verification.reports import _envelope, build_wi001_reports, validate_report_contract


def test_scope_and_service_registry_exclude_forbidden_capabilities():
    report = build_scope_boundary_report()
    assert report["result"] == "pass"
    assert report["scope_registry"]["formal_investment_scope"] == "a_share_common_stock"
    assert report["scope_registry"]["interaction_surface"] == "web_only"
    assert report["forbidden_entry_scan"]["forbidden_found"] == []
    assert "real_broker_api" in report["forbidden_entry_scan"]["excluded_capabilities"]

    service_report = validate_service_registry()
    assert service_report["result"] == "pass"
    assert len(service_report["allowed_services"]) == 8
    assert service_report["forbidden_role_scan"]["forbidden_found"] == []
    assert "performance_analyst" in service_report["forbidden_role_scan"]["blocked_roles"]


def test_scope_and_service_registry_reports_fail_when_forbidden_entries_are_found():
    scope_report = build_scope_boundary_report(forbidden_found=["real_broker_api"])
    service_report = validate_service_registry(forbidden_found=["performance_analyst"])

    assert scope_report["result"] == "fail"
    assert service_report["result"] == "fail"


def test_agent_profiles_are_complete_and_team_read_model_has_nine_agents():
    registry_report = validate_agent_registry()
    assert registry_report["result"] == "pass"
    assert registry_report["allowed_agents"] == list(OFFICIAL_AGENT_IDS)

    profiles = build_agent_capability_profiles()
    assert set(profiles) == set(OFFICIAL_AGENT_IDS)
    for profile in profiles.values():
        assert profile.mission
        assert profile.sop
        assert profile.failure_policy
        assert profile.evaluation_policy.metrics
        assert "direct_business_db_write" in profile.authority.forbidden_actions
        assert profile.write_policy.artifact_types or profile.write_policy.command_types

    analyst_payloads = {
        profiles[agent_id].output_contracts[0].role_payload_schema
        for agent_id in (
            "macro_analyst",
            "fundamental_analyst",
            "quant_analyst",
            "event_analyst",
        )
    }
    assert len(analyst_payloads) == 4

    team = build_team_read_model()
    assert team["team_health"]["healthy_agent_count"] == 9
    assert len(team["agent_cards"]) == 9
    assert all(card["config_draft_entry"] == "governance_draft_only" for card in team["agent_cards"])


def test_gateway_accepts_append_only_writes_and_rejects_direct_business_writes():
    profiles = build_agent_capability_profiles()
    gateway = AuthorityGateway(profiles)
    run = AgentRun.fake(
        agent_run_id="run-1",
        agent_id="investment_researcher",
        workflow_id="wf-1",
        allowed_command_types=["propose_knowledge_promotion", "request_evidence"],
    )

    artifact_result = gateway.append_artifact(
        run,
        artifact_type="ResearchPackage",
        payload={"summary": "research packet", "source_refs": ["src-1"]},
        idempotency_key="artifact-1",
    )
    assert artifact_result.accepted is True
    assert artifact_result.audit_event_id

    command = CollaborationCommand.request(
        command_id="cmd-1",
        command_type="request_evidence",
        workflow_id="wf-1",
        attempt_no=1,
        stage="S1",
        source_agent_run_id="run-1",
        source_agent_id="investment_researcher",
        target_agent_id_or_service="macro_analyst",
        payload={"question": "补充宏观证据", "expected_answer_format": "bullet"},
    )
    command_result = gateway.append_command(run, command, idempotency_key="cmd-1")
    assert command_result.accepted is True

    duplicate = gateway.append_command(run, command, idempotency_key="cmd-1")
    assert duplicate.object_id == command_result.object_id
    assert len(gateway.command_ledger) == 1

    denial = gateway.deny_direct_write(DirectBusinessWrite(actor="agent_runner", table="artifact"))
    assert denial.code == "DIRECT_WRITE_DENIED"
    assert gateway.denied_direct_writes[0]["actor"] == "agent_runner"


def test_memory_capture_is_append_only_context_not_fact_source():
    profiles = build_agent_capability_profiles()
    gateway = AuthorityGateway(profiles)
    capture = MemoryCapture(
        capture_id="cap-1",
        source_type="agent_observation",
        source_refs=["artifact-1"],
        content_markdown="# 经验\n- 只作为背景",
        payload={"symbol_refs": ["600000.SH"]},
        suggested_memory_type="research_note",
        sensitivity="public_internal",
        producer_agent_id="investment_researcher",
    )

    write = gateway.capture_memory(capture, idempotency_key="mem-1")
    assert write.accepted is True
    assert gateway.memory_items[0].current_version_id == gateway.memory_versions[0].version_id
    assert gateway.memory_versions[0].version_no == 1

    context = gateway.build_context_slice(
        agent_id="macro_analyst",
        context_snapshot_id="ctx-1",
        memory_refs=[gateway.memory_items[0].memory_id],
        artifact_refs=["artifact-1"],
    )
    assert context.memory_refs_injected == [gateway.memory_items[0].memory_id]
    assert context.fenced_background is True
    assert gateway.reject_memory_as_fact_source("mem-1").reason_code == "memory_not_fact_source"


def test_collaboration_objects_replay_command_event_handoff_lineage():
    session = CollaborationSession.open_session(
        session_id="sess-1",
        workflow_id="wf-1",
        stage="S3",
        semantic_lead_agent_id="cio",
        participant_agent_ids=["cio", "macro_analyst"],
    )
    run = AgentRun.fake(agent_run_id="run-2", agent_id="cio", workflow_id="wf-1")
    command = CollaborationCommand.request(
        command_id="cmd-2",
        command_type="ask_question",
        workflow_id="wf-1",
        attempt_no=1,
        stage="S3",
        source_agent_run_id="run-2",
        source_agent_id="cio",
        target_agent_id_or_service="macro_analyst",
        payload={"question": "核心分歧是什么", "expected_answer_format": "memo_update"},
    )
    event = command.to_event(event_id="evt-1", trace_id="trace-1")
    handoff = HandoffPacket.create(
        handoff_id="handoff-1",
        workflow_id="wf-1",
        from_stage="S3",
        to_stage_or_agent="S4",
        producer_agent_id_or_service="cio",
        source_artifact_refs=["artifact-1"],
        summary="辩论已收敛",
    )

    assert session.status == "open"
    assert event.event_type == "command_requested"
    assert handoff.source_artifact_refs == ["artifact-1"]
    assert handoff.summary == "辩论已收敛"


def test_wi001_reports_satisfy_frozen_report_contract():
    reports = build_wi001_reports()
    expected = {
        "scope_boundary_report.json",
        "registry_validation_report.json",
        "agent_capability_contract_report.json",
        "memory_boundary_report.json",
        "collaboration_trace_report.json",
        "security_privacy_report.json",
        "requirement_structure_report.json",
    }
    assert set(reports) == expected
    for name, report in reports.items():
        assert validate_report_contract(name, report) == []
        assert report["result"] == "pass"
        assert report["failures"] == []


def test_wi001_report_envelope_marks_fail_when_guard_or_failures_fail():
    report = _envelope(
        "scope_boundary_report.json",
        {"scope_registry": {"formal_investment_scope": "a_share_common_stock"}},
        guard_results=[
            {
                "guard": "forbidden_entry_scan",
                "input_ref": "scope",
                "expected": "none",
                "actual": "real_broker_api",
                "result": "fail",
            }
        ],
        failures=[{"code": "forbidden_scope_entry", "message": "real broker API appeared in scope"}],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "forbidden_scope_entry"
