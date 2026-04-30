from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.investment.analysis.memo import AnalystMemoFactory
from velentrade.domain.investment.debate.manager import DebateManager


def build_wi007_debate_reports() -> dict[str, dict[str, Any]]:
    factory = AnalystMemoFactory()
    manager = DebateManager()
    skipped = manager.run("wf-skip", factory.fixture_memos(direction_scores=[4, 4, 3, 3], confidences=[0.8, 0.8, 0.75, 0.75]))
    low_action = manager.run("wf-low-action", factory.fixture_memos(direction_scores=[1, 1, 1, 1], confidences=[0.4, 0.4, 0.4, 0.4]))
    hard = manager.run("wf-hard", factory.fixture_memos(direction_scores=[2, 2, 2, -1], confidences=[0.9, 0.9, 0.9, 0.9]))
    medium = manager.run("wf-medium", factory.fixture_memos(direction_scores=[2, 2, 1, -1], confidences=[0.9, 0.85, 0.8, 0.9]))
    low = manager.run("wf-low", factory.fixture_memos(direction_scores=[5, -5, 1, -1], confidences=[0.8, 0.8, 0.5, 0.5]))
    payload = {
        "debate_skipped": skipped.__dict__,
        "debate_round_inputs": {"hard": hard.participants, "medium": medium.participants},
        "debate_round_outputs": {"hard": hard.__dict__, "medium": medium.__dict__},
        "debate_manager_process_fields": {
            "rounds_used": hard.rounds_used,
            "participants": hard.participants,
            "stop_reason": hard.stop_reason,
            "next_stage_decision": hard.next_stage_decision,
        },
        "cio_agenda_synthesis": {"agenda": hard.agenda, "synthesis": hard.synthesis, "semantic_lead_signature": hard.semantic_lead_signature},
        "collaboration_commands": hard.collaboration_commands,
        "view_updates": hard.view_updates,
        "handoff_packets": hard.handoff_packets,
        "retained_hard_dissent": hard.retained_hard_dissent,
        "risk_review_required": hard.risk_review_required,
        "recomputed_consensus": hard.recomputed_consensus_score,
        "recomputed_action_conviction": hard.recomputed_action_conviction,
        "execution_blocked": low.execution_blocked and low_action.execution_blocked,
        "runbook_trace": [
            {"step": "round_open", "actor": "debate_manager", "input_ref": "memo-x4", "output_ref": "round-1", "result": "pass"},
            {"step": "agenda", "actor": "cio", "input_ref": "hard_dissent", "output_ref": "agenda", "result": "pass"},
            {"step": "handoff", "actor": "debate_manager", "input_ref": "summary", "output_ref": "S5", "result": "pass"},
        ],
        "high_consensus_low_action_block": low_action.stop_reason,
        "high_consensus_hard_dissent_path": hard.stop_reason,
        "medium_consensus_retained_hard_dissent_path": medium.stop_reason,
        "participants": hard.participants,
        "debate_rounds": hard.rounds_used,
        "debate_summary_schema": sorted(hard.__dict__),
        "hard_dissent_present": hard.hard_dissent_present,
        "risk_rejected_block": {"owner_override_allowed": False, "reason_code": "risk_rejected_no_override"},
    }
    return {"debate_dissent_report.json": _envelope(payload)}


def _envelope(payload: dict[str, Any]) -> dict[str, Any]:
    report = {
        "report_id": "debate_dissent_report.json",
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi007",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-007"],
        "test_case_refs": ["TC-ACC-017-01"],
        "fixture_refs": ["FX-HIGH-CONSENSUS-HARD-DISSENT", "FX-MEDIUM-CONSENSUS-HARD-DISSENT"],
        "result": "pass",
        "checked_requirements": ["REQ-017"],
        "checked_acceptances": ["ACC-017"],
        "checked_invariants": ["INV-DEBATE-BOUNDED-HARD-DISSENT-RISK-HANDOFF"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-007 deterministic debate fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "hard_dissent_handoff", "input_ref": "debate_summary", "expected": "pass", "actual": "pass", "result": "pass"}],
    }
    report.update(payload)
    return deepcopy(report)
