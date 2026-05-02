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


def test_stage_completion_rejects_memory_refs_as_formal_artifacts():
    runtime = WorkflowRuntime()
    brief = RequestBrief.create(
        brief_id="brief-memory",
        raw_input_ref="owner-input-memory",
        route_type="investment_workflow",
        route_confidence=0.9,
        asset_scope="a_share_common_stock",
        authorization_boundary="research_only_until_owner_approval",
    )
    task = runtime.confirm_request_brief(brief, owner_decision="confirmed")
    workflow = runtime.create_investment_workflow(task, context_snapshot_id="ctx-v1")
    runtime.start_stage(workflow.workflow_id, "S0")

    blocked = runtime.complete_stage(workflow.workflow_id, "S0", artifact_refs=["memory-1"])

    assert blocked.node_status == "blocked"
    assert blocked.reason_code == "memory_not_fact_source"


def test_request_brief_timeout_expires_draft_without_creating_workflow():
    runtime = WorkflowRuntime()
    brief = RequestBrief.create(
        brief_id="brief-timeout",
        raw_input_ref="owner-input-timeout",
        route_type="investment_workflow",
        route_confidence=0.9,
        asset_scope="a_share_common_stock",
        authorization_boundary="research_only_until_owner_approval",
    )

    task = runtime.expire_request_brief(brief)

    assert task.current_state == "expired"
    assert task.reason_code == "owner_timeout_request_brief_expired"


def test_request_brief_route_matrix_maps_research_governance_and_non_a_manual_todo():
    investment = RequestBrief.route_owner_request(
        brief_id="brief-investment",
        raw_input_ref="owner-investment",
        intent="formal_investment_decision",
        asset_scope="a_share_common_stock",
        target_action="start_ic",
        route_confidence=0.95,
        authorization_boundary="research_only_until_owner_approval",
    )
    research = RequestBrief.route_owner_request(
        brief_id="brief-research",
        raw_input_ref="owner-research",
        intent="learn_hot_event",
        asset_scope="a_share_common_stock",
        target_action="study",
        route_confidence=0.92,
        authorization_boundary="research_only",
    )
    governance = RequestBrief.route_owner_request(
        brief_id="brief-governance",
        raw_input_ref="owner-governance",
        intent="prompt_change",
        asset_scope="system",
        target_action="change_prompt",
        route_confidence=0.9,
        authorization_boundary="governance_only",
    )
    manual = RequestBrief.route_owner_request(
        brief_id="brief-manual",
        raw_input_ref="owner-manual",
        intent="trade_non_a_asset",
        asset_scope="gold",
        target_action="trade",
        route_confidence=0.91,
        authorization_boundary="manual_only",
    )

    assert investment.route_type == "investment_workflow"
    assert investment.suggested_semantic_lead == "cio"
    assert investment.process_authority == "workflow_scheduling_center"
    assert investment.creates_agent_run is True

    assert research.route_type == "research_task"
    assert research.suggested_semantic_lead == "investment_researcher"
    assert research.predicted_outputs == ["ResearchPackage", "MemoryCapture", "TopicProposalCandidate"]

    assert governance.route_type == "governance_task"
    assert governance.process_authority == "governance_runtime"

    assert manual.route_type == "manual_todo"
    assert manual.creates_agent_run is False
    assert manual.forbidden_action_reason_code == "non_a_asset_no_trade"


def test_request_brief_confirmation_allows_non_investment_ready_tasks_but_keeps_low_confidence_draft():
    runtime = WorkflowRuntime()
    research = RequestBrief.route_owner_request(
        brief_id="brief-research-confirm",
        raw_input_ref="owner-research-confirm",
        intent="learn_hot_event",
        asset_scope="a_share_common_stock",
        target_action="study",
        route_confidence=0.92,
        authorization_boundary="research_only",
    )
    manual = RequestBrief.route_owner_request(
        brief_id="brief-manual-confirm",
        raw_input_ref="owner-manual-confirm",
        intent="trade_non_a_asset",
        asset_scope="gold",
        target_action="trade",
        route_confidence=0.91,
        authorization_boundary="manual_only",
    )
    low_confidence = RequestBrief.route_owner_request(
        brief_id="brief-low-confidence",
        raw_input_ref="owner-low-confidence",
        intent="ambiguous_request",
        asset_scope="unknown",
        target_action="unclear",
        route_confidence=0.4,
        authorization_boundary="unknown",
    )

    research_task = runtime.confirm_request_brief(research, owner_decision="confirmed")
    manual_task = runtime.confirm_request_brief(manual, owner_decision="confirmed")
    low_confidence_task = runtime.confirm_request_brief(low_confidence, owner_decision="confirmed")

    assert research_task.current_state == "ready"
    assert research_task.task_type == "research_task"
    assert manual_task.current_state == "ready"
    assert manual_task.task_type == "manual_todo"
    assert low_confidence_task.current_state == "draft"
    assert low_confidence_task.reason_code == "request_brief_not_confirmed"
