from velentrade.domain.investment.analysis.memo import AnalystMemoFactory
from velentrade.domain.investment.debate.manager import DebateManager
from velentrade.domain.investment.debate.wi007_reports import build_wi007_debate_reports


def test_debate_skips_high_consensus_without_hard_dissent_and_blocks_low_action():
    manager = DebateManager()
    high_no_dissent = AnalystMemoFactory().fixture_memos(direction_scores=[4, 4, 3, 3], confidences=[0.8, 0.8, 0.75, 0.75])
    low_action = AnalystMemoFactory().fixture_memos(direction_scores=[1, 1, 1, 1], confidences=[0.4, 0.4, 0.4, 0.4])

    skipped = manager.run("wf-1", high_no_dissent)
    blocked = manager.run("wf-2", low_action)

    assert skipped.stop_reason == "skipped_high_consensus"
    assert skipped.rounds_used == 0
    assert skipped.next_stage_decision == "enter_s4"
    assert blocked.stop_reason == "low_action_conviction_blocked"
    assert blocked.next_stage_decision == "observe_or_reopen"
    assert blocked.execution_blocked is True


def test_hard_dissent_enters_bounded_debate_and_handoff_to_risk_when_retained():
    manager = DebateManager(max_rounds=2)
    memos = AnalystMemoFactory().fixture_memos(direction_scores=[2, 2, 2, -1], confidences=[0.9, 0.9, 0.9, 0.9])

    summary = manager.run("wf-hard-dissent", memos)

    assert summary.rounds_used == 2
    assert summary.hard_dissent_present is True
    assert summary.retained_hard_dissent is True
    assert summary.risk_review_required is True
    assert summary.semantic_lead_signature == "cio"
    assert all(command["admission_status"] == "accepted" for command in summary.collaboration_commands)
    assert summary.handoff_packets[0]["to_stage_or_agent"] == "S5"


def test_low_consensus_blocks_execution_without_unbounded_debate():
    manager = DebateManager()
    memos = AnalystMemoFactory().fixture_memos(direction_scores=[5, -5, 1, -1], confidences=[0.8, 0.8, 0.5, 0.5])

    summary = manager.run("wf-low-consensus", memos)

    assert summary.stop_reason == "low_consensus_blocked"
    assert summary.rounds_used <= 2
    assert summary.execution_blocked is True
    assert summary.next_stage_decision == "blocked"


def test_wi007_debate_report_has_contract_payloads():
    report = build_wi007_debate_reports()["debate_dissent_report.json"]

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-007"]
    assert set(report) >= {
        "debate_skipped",
        "debate_round_inputs",
        "debate_round_outputs",
        "debate_manager_process_fields",
        "cio_agenda_synthesis",
        "collaboration_commands",
        "view_updates",
        "handoff_packets",
        "retained_hard_dissent",
        "risk_review_required",
        "recomputed_consensus",
        "recomputed_action_conviction",
        "execution_blocked",
        "runbook_trace",
        "high_consensus_hard_dissent_path",
        "medium_consensus_retained_hard_dissent_path",
        "risk_rejected_block",
    }
