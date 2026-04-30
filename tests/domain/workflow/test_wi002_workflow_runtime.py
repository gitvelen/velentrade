from velentrade.domain.workflow.runtime import RequestBrief, WorkflowRuntime


def test_s0_s7_workflow_uses_contract_statuses_and_reopen_is_event_not_node_status():
    runtime = WorkflowRuntime()
    brief = RequestBrief.create(
        brief_id="brief-1",
        raw_input_ref="owner-input-1",
        route_type="investment_workflow",
        route_confidence=0.92,
        asset_scope="a_share_common_stock",
        authorization_boundary="research_only_until_owner_approval",
    )

    task = runtime.confirm_request_brief(brief, owner_decision="confirmed")
    workflow = runtime.create_investment_workflow(task, context_snapshot_id="ctx-v1")

    assert [stage.stage for stage in workflow.stages] == [f"S{i}" for i in range(8)]
    assert {stage.node_status for stage in workflow.stages} == {"not_started"}
    assert workflow.current_stage == "S0"

    started = runtime.start_stage(workflow.workflow_id, "S0")
    assert started.node_status == "running"

    completed = runtime.complete_stage(workflow.workflow_id, "S0", artifact_refs=["artifact-s0"])
    assert completed.node_status == "completed"
    assert runtime.start_stage(workflow.workflow_id, "S1").node_status == "running"

    reopen = runtime.request_reopen(
        workflow.workflow_id,
        from_stage="S4",
        target_stage="S2",
        reason_code="retained_hard_dissent",
        requested_by="risk_officer",
        invalidated_artifacts=["memo-v1"],
        preserved_artifacts=["ic-context-v1"],
    )

    assert reopen.target_stage == "S2"
    assert reopen.invalidated_artifacts == ["memo-v1"]
    assert reopen.preserved_artifacts == ["ic-context-v1"]
    assert "reopened" not in {stage.node_status for stage in runtime.workflows[workflow.workflow_id].stages}
    assert runtime.artifact_status["memo-v1"] == "superseded"


def test_stage_guards_block_out_of_order_start_and_record_reason_code():
    runtime = WorkflowRuntime()
    brief = RequestBrief.create(
        brief_id="brief-2",
        raw_input_ref="owner-input-2",
        route_type="investment_workflow",
        route_confidence=0.9,
        asset_scope="a_share_common_stock",
        authorization_boundary="research_only_until_owner_approval",
    )
    task = runtime.confirm_request_brief(brief, owner_decision="confirmed")
    workflow = runtime.create_investment_workflow(task, context_snapshot_id="ctx-v1")

    blocked = runtime.start_stage(workflow.workflow_id, "S2")

    assert blocked.node_status == "blocked"
    assert blocked.reason_code == "upstream_stage_not_completed"
