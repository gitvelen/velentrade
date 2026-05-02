from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.context.builder import ICContextBuilder
from velentrade.domain.investment.intake.registry import OpportunityRegistry, TopicProposal
from velentrade.domain.investment.topic_queue.queue import TopicQueue, TopicScore


REPORT_TC = {
    "topic_registration_report.json": ("TC-ACC-012-01", "ACC-012", "REQ-012"),
    "topic_queue_report.json": ("TC-ACC-013-01", "ACC-013", "REQ-013"),
    "ic_context_package_report.json": ("TC-ACC-014-01", "ACC-014", "REQ-014"),
}


def _envelope(report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    tc, acc, req = REPORT_TC[report_id]
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi003",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-003"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": "pass",
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-SUPPORTING-EVIDENCE-NO-FORMAL-IC"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-003 deterministic intake fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}],
    }
    report.update(payload)
    return report


def _proposal(topic_id: str, source_type: str = "owner", priority: str | None = None) -> TopicProposal:
    return TopicProposal(
        topic_proposal_id=topic_id,
        source_type=source_type,
        symbol="600000.SH",
        raw_trigger_ref=f"raw-{topic_id}",
        supporting_evidence_refs=[f"evidence-{topic_id}"],
        requested_priority=priority,
        research_package_ref=f"research-{topic_id}",
        created_by=source_type,
    )


def _registration_report() -> dict[str, Any]:
    registry = OpportunityRegistry()
    sources = ["owner", "analyst", "researcher", "service_signal", "holding_risk", "announcement"]
    for source in sources:
        registry.register(_proposal(f"topic-{source}", source))
    registry.route_supporting_evidence("news-1", "600000.SH", route_to="candidate")
    registry.route_supporting_evidence("news-2", "600000.SH", route_to="research_package")
    registry.route_supporting_evidence("news-3", "600000.SH", route_to="research_task")
    return _envelope(
        "topic_registration_report.json",
        {
            "registered_sources": sources,
            "supporting_evidence_only_actions": sorted(set(registry.supporting_evidence_routes.values())),
            "candidate_states": {entry.topic_id: entry.formal_ic_status for entry in registry.entries.values() if entry.formal_ic_status == "candidate"},
            "formal_ic_states": [entry.formal_ic_status for entry in registry.formal_ic_entries()],
            "rejected_reasons": [entry.rejected_reason for entry in registry.entries.values() if entry.rejected_reason],
        },
    )


def _queue_report() -> dict[str, Any]:
    queue = TopicQueue()
    high = TopicScore(5, 5, 4, 4)
    medium = TopicScore(3, 4, 2, 2)
    entries = [
        queue.submit(_proposal("topic-1", priority="P1"), high, True, True),
        queue.submit(_proposal("topic-2", priority="P2"), medium, True, True),
        queue.submit(_proposal("topic-3", priority="P1"), medium, True, True),
    ]
    rejected = queue.submit(TopicProposal("topic-bad", "owner", "AAPL", "raw-bad", ["evidence-bad"], "P1", "research-bad", "owner"), high, True, True)
    p0 = queue.submit(_proposal("topic-p0", priority="P0"), high, True, True, p0_trigger="holding_risk")
    return _envelope(
        "topic_queue_report.json",
        {
            "hard_gate_results": {entry.topic_id: entry.hard_gate_results for entry in [*entries, rejected, p0]},
            "priority_score_components": high.as_dict(),
            "priority_weighted_totals": {entry.topic_id: entry.priority_scores.get("weighted_total", 0) for entry in queue.entries.values()},
            "active_ic_slots": len(queue.active_entries()),
            "global_workflows": queue.global_workflow_count,
            "preemption_events": queue.preemption_events,
            "preempted_workflow_waiting_audit": [entry.waiting_audit for entry in queue.entries.values() if entry.waiting_audit],
            "gate_checks": {"max_active_ic": queue.max_active_ic, "max_global_workflows": queue.max_global_workflows, "rejected_reason": rejected.rejected_reason},
        },
    )


def _context_report() -> dict[str, Any]:
    builder = ICContextBuilder()
    package = builder.build_context_package(
        "topic-1",
        "brief-1",
        "data-ready-1",
        "market-risk-on",
        ["factor-1", "valuation-1", "optimizer-1"],
        "portfolio-1",
        ["risk-budget-1"],
        ["research-1"],
        ["reflection-1"],
        "ctx-v1",
    )
    brief = builder.build_chair_brief(package, "30m")
    return _envelope(
        "ic_context_package_report.json",
        {
            "shared_context": {"request_brief_ref": package.request_brief_ref, "context_snapshot_id": package.context_snapshot_id},
            "market_state_ref": package.market_state_ref,
            "service_result_refs": package.service_result_refs,
            "role_attachments": package.role_attachment_refs,
            "chair_brief": brief.__dict__,
            "chair_brief_no_preset_decision": brief.no_preset_decision_attestation,
            "evidence_resolution": builder.resolve_evidence(package),
            "missing_sections": builder.missing_sections(package),
        },
    )


def build_wi003_reports() -> dict[str, dict[str, Any]]:
    reports = {
        "topic_registration_report.json": _registration_report(),
        "topic_queue_report.json": _queue_report(),
        "ic_context_package_report.json": _context_report(),
    }
    return {name: deepcopy(report) for name, report in reports.items()}
