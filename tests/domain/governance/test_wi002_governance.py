from velentrade.domain.governance.runtime import GovernanceRuntime


def test_governance_low_medium_auto_effective_high_requires_owner_and_snapshots_are_immutable():
    runtime = GovernanceRuntime()
    base = runtime.create_context_snapshot(
        snapshot_version="ctx-v1",
        source_change_ref="baseline",
        prompt_versions={"cio": "prompt-v1"},
        skill_package_versions={"cio": "skill-v1"},
        knowledge_item_versions=["knowledge-v1"],
        memory_collection_versions=["collection-v1"],
        default_context_versions=["default-v1"],
        agent_capability_versions={"cio": "profile-v1"},
        effective_scope="new_task",
    )

    low = runtime.submit_change(
        change_id="chg-low",
        change_type="prompt",
        impact_level="low",
        proposal_ref="proposal-low",
        target_version_refs={"prompt_versions": {"cio": "prompt-v2"}},
        effective_scope="new_attempt",
        rollback_plan_ref="rollback-low",
    )
    runtime.triage(low.change_id)
    runtime.assess(low.change_id, validation_refs=["schema", "fixture", "scope", "rollback", "snapshot"])
    effective_low = runtime.activate(low.change_id)

    assert effective_low.state == "effective"
    assert effective_low.context_snapshot_id != base.context_snapshot_id
    assert runtime.context_snapshots[base.context_snapshot_id].content_hash == base.content_hash

    high = runtime.submit_change(
        change_id="chg-high",
        change_type="agent_capability",
        impact_level="high",
        proposal_ref="proposal-high",
        target_version_refs={"agent_capability_versions": {"cio": "profile-v2"}},
        effective_scope="new_task",
        rollback_plan_ref="rollback-high",
    )
    runtime.triage(high.change_id)
    assessed_high = runtime.assess(high.change_id, validation_refs=["schema", "fixture", "scope", "rollback", "snapshot"])
    assert assessed_high.state == "owner_pending"
    assert assessed_high.context_snapshot_id is None

    approved = runtime.owner_decide(high.change_id, approved=True, approval_ref="approval-1")
    assert approved.state == "approved"
    effective_high = runtime.activate(high.change_id)
    assert effective_high.state == "effective"
    assert runtime.context_snapshots[effective_high.context_snapshot_id].effective_scope == "new_task"

    rejected = runtime.submit_change(
        change_id="chg-rejected",
        change_type="default_context",
        impact_level="high",
        proposal_ref="proposal-rejected",
        target_version_refs={"default_context_versions": ["default-v2"]},
        effective_scope="new_task",
        rollback_plan_ref="rollback-rejected",
    )
    runtime.triage(rejected.change_id)
    runtime.assess(rejected.change_id, validation_refs=["schema", "fixture", "scope", "rollback", "snapshot"])
    rejected = runtime.owner_decide(rejected.change_id, approved=False, approval_ref="approval-2")
    assert rejected.state == "rejected"
    assert rejected.context_snapshot_id is None
