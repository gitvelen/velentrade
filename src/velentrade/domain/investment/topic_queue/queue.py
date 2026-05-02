from __future__ import annotations

from dataclasses import dataclass, field

from velentrade.domain.common import utc_now
from velentrade.domain.investment.intake.registry import TopicProposal, TopicQueueEntry


WEIGHTS = {
    "opportunity_strength": 0.35,
    "data_completeness": 0.25,
    "risk_urgency": 0.25,
    "portfolio_relevance": 0.15,
}
P0_TRIGGERS = {"holding_risk", "major_announcement", "execution_failure", "risk_explicit", "owner_explicit"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, None: 3}


@dataclass(frozen=True)
class TopicScore:
    opportunity_strength: float
    data_completeness: float
    risk_urgency: float
    portfolio_relevance: float

    def as_dict(self) -> dict[str, float]:
        components = {
            "opportunity_strength": self.opportunity_strength,
            "data_completeness": self.data_completeness,
            "risk_urgency": self.risk_urgency,
            "portfolio_relevance": self.portfolio_relevance,
        }
        weighted = sum(components[key] * weight for key, weight in WEIGHTS.items())
        return {**components, "weighted_total": weighted}


@dataclass
class TopicQueue:
    max_active_ic: int = 3
    max_global_workflows: int = 5
    entries: dict[str, TopicQueueEntry] = field(default_factory=dict)
    preemption_events: list[dict] = field(default_factory=list)
    global_workflow_count: int = 0

    def active_entries(self) -> list[TopicQueueEntry]:
        return [entry for entry in self.entries.values() if entry.formal_ic_status == "active"]

    def submit(
        self,
        proposal: TopicProposal,
        score: TopicScore,
        request_brief_complete: bool,
        decision_core_available: bool,
        p0_trigger: str | None = None,
        compliance_execution_clear: bool = True,
        duplicate_symbols: set[str] | None = None,
    ) -> TopicQueueEntry:
        scores = score.as_dict()
        hard_gates = {
            "a_share_common_stock": proposal.symbol.endswith(".SH") or proposal.symbol.endswith(".SZ"),
            "request_brief_complete": request_brief_complete,
            "decision_core_available": decision_core_available,
            "research_package_non_empty": bool(proposal.research_package_ref),
            "compliance_execution_clear": compliance_execution_clear,
            "topic_not_duplicate": proposal.symbol not in set(duplicate_symbols or set()),
            "supporting_evidence_not_direct": True,
            "priority_scored": True,
            "global_workflow_slot_available": self.global_workflow_count < self.max_global_workflows,
        }
        priority = proposal.requested_priority or "P2"
        if priority == "P0" and p0_trigger not in P0_TRIGGERS:
            hard_gates["p0_trigger_allowed"] = False
        else:
            hard_gates["p0_trigger_allowed"] = True

        rejected_reason = None
        if not hard_gates["a_share_common_stock"]:
            rejected_reason = "non_a_share_scope"
        elif not request_brief_complete:
            rejected_reason = "request_brief_missing"
        elif not decision_core_available:
            rejected_reason = "decision_core_blocked"
        elif not hard_gates["research_package_non_empty"]:
            rejected_reason = "research_package_empty"
        elif not hard_gates["compliance_execution_clear"]:
            rejected_reason = "compliance_or_execution_forbidden"
        elif not hard_gates["topic_not_duplicate"]:
            rejected_reason = "duplicate_topic_active"
        elif not hard_gates["p0_trigger_allowed"]:
            rejected_reason = "p0_trigger_not_allowed"

        if rejected_reason:
            entry = self._entry(proposal, hard_gates, scores, "rejected", rejected_reason)
            self.entries[entry.topic_id] = entry
            return entry

        active = self.active_entries()
        if not hard_gates["global_workflow_slot_available"]:
            entry = self._entry(proposal, hard_gates, scores, "queued", "topic_concurrency_full")
            self.entries[entry.topic_id] = entry
            return entry

        if len(active) >= self.max_active_ic:
            if priority == "P0":
                preemptable = [entry for entry in active if entry.requested_priority != "P0"]
                if preemptable:
                    victim = min(preemptable, key=self._preemption_rank)
                    self._defer_for_preemption(victim, proposal.topic_proposal_id)
                    entry = self._entry(proposal, hard_gates, scores, "active")
                    self.entries[entry.topic_id] = entry
                    self.global_workflow_count = min(self.max_global_workflows, max(self.global_workflow_count, len(self.active_entries())))
                    return entry
            entry = self._entry(proposal, hard_gates, scores, "queued", "topic_concurrency_full")
            self.entries[entry.topic_id] = entry
            return entry

        entry = self._entry(proposal, hard_gates, scores, "active")
        self.entries[entry.topic_id] = entry
        self.global_workflow_count = min(self.max_global_workflows, self.global_workflow_count + 1)
        return entry

    def _entry(
        self,
        proposal: TopicProposal,
        hard_gates: dict[str, bool],
        scores: dict[str, float],
        status: str,
        rejected_reason: str | None = None,
    ) -> TopicQueueEntry:
        return TopicQueueEntry(
            topic_id=proposal.topic_proposal_id,
            source_type=proposal.source_type,
            symbol=proposal.symbol,
            hard_gate_results=hard_gates,
            priority_scores=scores,
            formal_ic_status=status,
            supporting_evidence_refs=list(proposal.supporting_evidence_refs),
            research_package_ref=proposal.research_package_ref,
            requested_priority=proposal.requested_priority,
            rejected_reason=rejected_reason,
            created_at=proposal.created_at,
        )

    def _defer_for_preemption(self, victim: TopicQueueEntry, preempting_topic_id: str) -> None:
        audit = {
            "preempted_topic_id": victim.topic_id,
            "preempted_by_topic_id": preempting_topic_id,
            "reason_code": "p0_preemption_waiting",
            "preserved_artifacts": victim.supporting_evidence_refs + ([victim.research_package_ref] if victim.research_package_ref else []),
            "resume_priority": victim.requested_priority or "P2",
            "created_at": utc_now(),
        }
        self.entries[victim.topic_id] = TopicQueueEntry(
            **{
                **victim.__dict__,
                "formal_ic_status": "deferred",
                "rejected_reason": "preempted_waiting",
                "waiting_audit": audit,
            }
        )
        self.preemption_events.append(audit)

    @staticmethod
    def _preemption_rank(item: TopicQueueEntry) -> tuple[float, int, str]:
        return (item.priority_scores["weighted_total"], PRIORITY_ORDER.get(item.requested_priority, 3), item.created_at)
