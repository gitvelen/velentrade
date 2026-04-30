from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id
from velentrade.domain.investment.analysis.consensus import ConsensusCalculator
from velentrade.domain.investment.analysis.memo import AnalystMemo


@dataclass(frozen=True)
class DebateSummary:
    rounds_used: int
    participants: list[str]
    issues: list[str]
    new_evidence_refs: list[str]
    view_changes: list[dict[str, Any]]
    hard_dissent_present: bool
    retained_hard_dissent: bool
    risk_review_required: bool
    recomputed_consensus_score: float
    recomputed_action_conviction: float
    stop_reason: str
    next_stage_decision: str
    agenda: list[str]
    questions_asked: list[str]
    synthesis: str
    resolved_issues: list[str]
    unresolved_dissent: list[str]
    chair_recommendation_for_next_stage: str
    semantic_lead_signature: str
    collaboration_commands: list[dict[str, Any]]
    view_updates: list[dict[str, Any]]
    handoff_packets: list[dict[str, Any]]
    execution_blocked: bool


class DebateManager:
    def __init__(self, max_rounds: int = 2) -> None:
        self.max_rounds = max_rounds
        self.calculator = ConsensusCalculator()

    def run(self, workflow_id: str, memos: list[AnalystMemo]) -> DebateSummary:
        initial = self.calculator.calculate(memos)
        participants = [memo.analyst_id for memo in memos]
        if initial.consensus_score >= 0.8 and initial.action_conviction >= 0.65 and not initial.hard_dissent_present:
            return self._summary(workflow_id, 0, participants, memos, "skipped_high_consensus", "enter_s4", False, initial)
        if initial.consensus_score >= 0.8 and initial.action_conviction < 0.65 and not initial.hard_dissent_present:
            return self._summary(workflow_id, 0, participants, memos, "low_action_conviction_blocked", "observe_or_reopen", True, initial)
        if initial.consensus_score < 0.7:
            return self._summary(workflow_id, 0, participants, memos, "low_consensus_blocked", "blocked", True, initial)

        rounds = min(self.max_rounds, 2)
        retained = initial.hard_dissent_present
        stop = "retained_hard_dissent" if retained else "converged"
        next_stage = "enter_s4_with_s5_hard_dissent_review" if retained else "enter_s4"
        return self._summary(workflow_id, rounds, participants, memos, stop, next_stage, False, initial, retained_hard_dissent=retained)

    def _summary(
        self,
        workflow_id: str,
        rounds: int,
        participants: list[str],
        memos: list[AnalystMemo],
        stop_reason: str,
        next_stage: str,
        execution_blocked: bool,
        result: Any,
        retained_hard_dissent: bool = False,
    ) -> DebateSummary:
        questions = ["请解释 hard dissent 的证据和失效条件。"] if result.hard_dissent_present else ["请确认行动强度和证据质量。"]
        commands = [
            {
                "command_id": new_id("cmd"),
                "command_type": command_type,
                "workflow_id": workflow_id,
                "stage": "S3",
                "admission_status": "accepted",
            }
            for command_type in ["ask_question", "request_view_update", "request_evidence"]
        ]
        view_updates = [
            {"view_update_id": new_id("view-update"), "producer_agent_id": memo.analyst_id, "changed_fields": ["comment"], "evidence_refs": memo.supporting_evidence_refs}
            for memo in memos
        ] if rounds else []
        risk_review_required = retained_hard_dissent
        return DebateSummary(
            rounds_used=rounds,
            participants=participants,
            issues=["hard_dissent_evidence_gap"] if result.hard_dissent_present else ["action_conviction_check"],
            new_evidence_refs=["evidence-s3-accepted"] if rounds else [],
            view_changes=view_updates,
            hard_dissent_present=result.hard_dissent_present,
            retained_hard_dissent=retained_hard_dissent,
            risk_review_required=risk_review_required,
            recomputed_consensus_score=result.consensus_score,
            recomputed_action_conviction=result.action_conviction,
            stop_reason=stop_reason,
            next_stage_decision=next_stage,
            agenda=["聚焦异议、证据质量、适用条件和失效条件。"],
            questions_asked=questions,
            synthesis="CIO synthesis keeps process authority with Debate Manager.",
            resolved_issues=[] if retained_hard_dissent else ["no_unresolved_dissent"],
            unresolved_dissent=["event_analyst_hard_dissent"] if retained_hard_dissent else [],
            chair_recommendation_for_next_stage=next_stage,
            semantic_lead_signature="cio",
            collaboration_commands=commands if rounds else [],
            view_updates=view_updates,
            handoff_packets=[
                {
                    "handoff_id": new_id("handoff"),
                    "workflow_id": workflow_id,
                    "from_stage": "S3",
                    "to_stage_or_agent": "S5" if risk_review_required else "S4",
                    "source_artifact_refs": [memo.memo_id for memo in memos],
                    "summary": "retained hard dissent requires explicit Risk review" if risk_review_required else "debate complete",
                }
            ],
            execution_blocked=execution_blocked or stop_reason in {"low_consensus_blocked", "low_action_conviction_blocked"},
        )
