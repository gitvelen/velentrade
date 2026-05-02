from velentrade.domain.investment.context.reports import _envelope, build_wi003_reports


def test_wi003_reports_include_contract_payload_fields():
    reports = build_wi003_reports()
    expected = {
        "topic_registration_report.json": {
            "registered_sources",
            "supporting_evidence_only_actions",
            "candidate_states",
            "formal_ic_states",
            "rejected_reasons",
        },
        "topic_queue_report.json": {
            "hard_gate_results",
            "priority_score_components",
            "priority_weighted_totals",
            "active_ic_slots",
            "global_workflows",
            "preemption_events",
            "preemption_tie_break",
            "duplicate_topic_auto_check",
            "a_share_scope_symbols",
            "gate_checks",
        },
        "ic_context_package_report.json": {
            "shared_context",
            "market_state_ref",
            "service_result_refs",
            "role_attachments",
            "chair_brief",
            "chair_brief_no_preset_decision",
            "evidence_resolution",
            "missing_sections",
        },
    }

    assert set(reports) == set(expected)
    for name, fields in expected.items():
        assert reports[name]["result"] == "pass"
        assert reports[name]["work_item_refs"] == ["WI-003"]
        assert reports[name]["failures"] == []
        assert set(reports[name]) >= fields
    assert reports["topic_registration_report.json"]["checked_invariants"] == ["INV-SUPPORTING-EVIDENCE-NO-FORMAL-IC"]
    assert set(reports["topic_registration_report.json"]["supporting_evidence_only_actions"]) == {
        "candidate",
        "research_package",
        "research_task",
    }
    assert reports["topic_queue_report.json"]["duplicate_topic_auto_check"] == "duplicate_topic_active"
    assert reports["topic_queue_report.json"]["a_share_scope_symbols"]["430047.BJ"] is True
    assert reports["topic_queue_report.json"]["preemption_tie_break"]["preempted_topic_id"] == "topic-p2-same"


def test_wi003_report_envelope_marks_fail_when_guard_or_failures_fail():
    report = _envelope(
        "topic_queue_report.json",
        {"probe": "negative"},
        guard_results=[
            {
                "guard": "p0_preemption_victim",
                "input_ref": "topic-p0-risk",
                "expected": "preempt_lowest_score",
                "actual": "preempt_high_score_p1",
                "result": "fail",
            }
        ],
        failures=[
            {
                "code": "wrong_preemption_victim",
                "message": "P0 preempted a higher score slot",
                "evidence_ref": "topic-p0-risk",
            }
        ],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "wrong_preemption_victim"
