import pytest

from velentrade.domain.investment.intake.registry import TopicProposal
from velentrade.domain.investment.topic_queue.queue import TopicQueue, TopicScore


def _proposal(topic_id: str, priority: str | None = None, symbol: str = "600000.SH") -> TopicProposal:
    return TopicProposal(
        topic_proposal_id=topic_id,
        source_type="owner",
        symbol=symbol,
        raw_trigger_ref=f"raw-{topic_id}",
        supporting_evidence_refs=[f"evidence-{topic_id}"],
        requested_priority=priority,
        research_package_ref=f"research-{topic_id}",
        created_by="owner",
    )


def test_hard_gates_weighted_scoring_concurrency_and_p0_preemption():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)
    medium = TopicScore(3, 4, 2, 2)

    first = queue.submit(_proposal("topic-1", "P1", symbol="600000.SH"), high, request_brief_complete=True, decision_core_available=True)
    second = queue.submit(_proposal("topic-2", "P2", symbol="600001.SH"), medium, request_brief_complete=True, decision_core_available=True)
    third = queue.submit(_proposal("topic-3", "P1", symbol="600002.SH"), medium, request_brief_complete=True, decision_core_available=True)

    assert first.formal_ic_status == "active"
    assert round(first.priority_scores["weighted_total"], 2) == 4.60
    assert len(queue.active_entries()) == 3

    rejected = queue.submit(_proposal("topic-non-a", "P1", symbol="AAPL"), high, request_brief_complete=True, decision_core_available=True)
    assert rejected.formal_ic_status == "rejected"
    assert rejected.rejected_reason == "non_a_share_scope"

    p0 = queue.submit(
        _proposal("topic-p0", "P0", symbol="600003.SH"),
        high,
        request_brief_complete=True,
        decision_core_available=True,
        p0_trigger="holding_risk",
    )

    assert p0.formal_ic_status == "active"
    assert len(queue.active_entries()) == 3
    assert queue.preemption_events[0]["preempted_topic_id"] in {second.topic_id, third.topic_id}
    preempted_id = queue.preemption_events[0]["preempted_topic_id"]
    assert queue.entries[preempted_id].formal_ic_status == "deferred"
    assert queue.entries[preempted_id].rejected_reason == "preempted_waiting"
    assert queue.global_workflow_count == 4


def test_duplicate_topic_and_compliance_forbidden_fail_hard_gates():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)

    queue.submit(_proposal("topic-live", "P1"), high, request_brief_complete=True, decision_core_available=True)
    duplicate = queue.submit(
        _proposal("topic-live-duplicate", "P1"),
        high,
        request_brief_complete=True,
        decision_core_available=True,
        duplicate_symbols={"600000.SH"},
    )
    forbidden = queue.submit(
        _proposal("topic-forbidden", "P1", symbol="600001.SH"),
        high,
        request_brief_complete=True,
        decision_core_available=True,
        compliance_execution_clear=False,
    )

    assert duplicate.formal_ic_status == "rejected"
    assert duplicate.rejected_reason == "duplicate_topic_active"
    assert duplicate.hard_gate_results["topic_not_duplicate"] is False
    assert forbidden.formal_ic_status == "rejected"
    assert forbidden.rejected_reason == "compliance_or_execution_forbidden"
    assert forbidden.hard_gate_results["compliance_execution_clear"] is False


def test_a_share_hard_gate_accepts_beijing_exchange_symbol():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)

    entry = queue.submit(_proposal("topic-bj", "P1", symbol="430047.BJ"), high, request_brief_complete=True, decision_core_available=True)

    assert entry.formal_ic_status == "active"
    assert entry.hard_gate_results["a_share_common_stock"] is True


def test_a_share_hard_gate_rejects_non_numeric_symbol_with_exchange_suffix():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)

    rejected = queue.submit(_proposal("topic-fake-a", "P1", symbol="AAPL.SH"), high, request_brief_complete=True, decision_core_available=True)

    assert rejected.formal_ic_status == "rejected"
    assert rejected.rejected_reason == "non_a_share_scope"
    assert rejected.hard_gate_results["a_share_common_stock"] is False


def test_topic_queue_rejects_priority_outside_contract_enum():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)

    with pytest.raises(ValueError, match="requested_priority"):
        queue.submit(_proposal("topic-invalid-priority", "P3"), high, request_brief_complete=True, decision_core_available=True)


def test_topic_queue_detects_duplicate_active_symbol_without_caller_supplied_set():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 4, 4)

    first = queue.submit(_proposal("topic-live", "P1"), high, request_brief_complete=True, decision_core_available=True)
    duplicate = queue.submit(_proposal("topic-live-implicit-duplicate", "P1"), high, request_brief_complete=True, decision_core_available=True)

    assert first.formal_ic_status == "active"
    assert duplicate.formal_ic_status == "rejected"
    assert duplicate.rejected_reason == "duplicate_topic_active"
    assert duplicate.hard_gate_results["topic_not_duplicate"] is False


def test_global_workflow_cap_prevents_admitting_more_formal_ic_workflows():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5, global_workflow_count=5)
    high = TopicScore(5, 5, 4, 4)

    blocked = queue.submit(_proposal("topic-global-cap", "P1"), high, request_brief_complete=True, decision_core_available=True)

    assert blocked.formal_ic_status == "queued"
    assert blocked.rejected_reason == "topic_concurrency_full"
    assert blocked.hard_gate_results["global_workflow_slot_available"] is False
    assert queue.global_workflow_count == 5


def test_priority_score_rejects_components_outside_contract_range():
    with pytest.raises(ValueError, match="opportunity_strength"):
        TopicScore(6, 5, 4, 4).as_dict()

    with pytest.raises(ValueError, match="portfolio_relevance"):
        TopicScore(5, 5, 4, -1).as_dict()


def test_p0_preempts_lowest_priority_score_slot_not_high_score_p1_slot():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    high = TopicScore(5, 5, 5, 5)
    medium = TopicScore(3, 3, 3, 3)
    low = TopicScore(1, 1, 1, 1)

    queue.submit(_proposal("topic-p1-high", "P1", symbol="600000.SH"), high, request_brief_complete=True, decision_core_available=True)
    queue.submit(_proposal("topic-p1-medium", "P1", symbol="600001.SH"), medium, request_brief_complete=True, decision_core_available=True)
    queue.submit(_proposal("topic-p2-low", "P2", symbol="600002.SH"), low, request_brief_complete=True, decision_core_available=True)

    queue.submit(
        _proposal("topic-p0-risk", "P0", symbol="600003.SH"),
        high,
        request_brief_complete=True,
        decision_core_available=True,
        p0_trigger="holding_risk",
    )

    assert queue.preemption_events[0]["preempted_topic_id"] == "topic-p2-low"
    assert queue.entries["topic-p1-high"].formal_ic_status == "active"
    assert queue.entries["topic-p2-low"].waiting_audit["preserved_artifacts"] == ["evidence-topic-p2-low", "research-topic-p2-low"]


def test_p0_preemption_tie_breaks_to_lower_priority_p2_slot():
    queue = TopicQueue(max_active_ic=3, max_global_workflows=5)
    same_score = TopicScore(3, 3, 3, 3)
    high = TopicScore(5, 5, 5, 5)

    queue.submit(_proposal("topic-p1-same", "P1", symbol="600000.SH"), same_score, request_brief_complete=True, decision_core_available=True)
    queue.submit(_proposal("topic-p2-same", "P2", symbol="600001.SH"), same_score, request_brief_complete=True, decision_core_available=True)
    queue.submit(_proposal("topic-p1-high", "P1", symbol="600002.SH"), high, request_brief_complete=True, decision_core_available=True)

    queue.submit(
        _proposal("topic-p0-tie", "P0", symbol="600003.SH"),
        high,
        request_brief_complete=True,
        decision_core_available=True,
        p0_trigger="holding_risk",
    )

    assert queue.preemption_events[0]["preempted_topic_id"] == "topic-p2-same"
    assert queue.entries["topic-p1-same"].formal_ic_status == "active"
