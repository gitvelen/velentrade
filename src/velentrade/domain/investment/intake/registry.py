from __future__ import annotations

from dataclasses import dataclass, field

from velentrade.domain.common import utc_now


OPEN_SOURCE_TYPES = {"owner", "analyst", "researcher", "service_signal", "holding_risk", "announcement"}
SUPPORTING_EVIDENCE_ROUTES = {"candidate", "research_package", "research_task"}


@dataclass(frozen=True)
class TopicProposal:
    topic_proposal_id: str
    source_type: str
    symbol: str
    raw_trigger_ref: str
    supporting_evidence_refs: list[str]
    requested_priority: str | None
    research_package_ref: str | None
    created_by: str
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class TopicQueueEntry:
    topic_id: str
    source_type: str
    symbol: str
    hard_gate_results: dict[str, bool]
    priority_scores: dict[str, float]
    formal_ic_status: str
    supporting_evidence_refs: list[str]
    research_package_ref: str | None
    requested_priority: str | None
    created_at: str
    rejected_reason: str | None = None
    waiting_audit: dict | None = None


@dataclass
class OpportunityRegistry:
    entries: dict[str, TopicQueueEntry] = field(default_factory=dict)
    supporting_evidence_routes: dict[str, str] = field(default_factory=dict)

    def register(self, proposal: TopicProposal) -> TopicProposal:
        if proposal.source_type not in OPEN_SOURCE_TYPES:
            raise ValueError(f"Unsupported topic source_type: {proposal.source_type}")
        self.entries[proposal.topic_proposal_id] = TopicQueueEntry(
            topic_id=proposal.topic_proposal_id,
            source_type=proposal.source_type,
            symbol=proposal.symbol,
            hard_gate_results={"registered_open_source": True, "formal_ic_admitted": False},
            priority_scores={},
            formal_ic_status="candidate",
            supporting_evidence_refs=list(proposal.supporting_evidence_refs),
            research_package_ref=proposal.research_package_ref,
            requested_priority=proposal.requested_priority,
            created_at=proposal.created_at,
        )
        return proposal

    def route_supporting_evidence(self, raw_trigger_ref: str, symbol: str, route_to: str = "candidate") -> TopicQueueEntry:
        if route_to not in SUPPORTING_EVIDENCE_ROUTES:
            raise ValueError(f"Unsupported supporting evidence route: {route_to}")
        proposal = TopicProposal(
            topic_proposal_id=f"candidate-{raw_trigger_ref}",
            source_type="announcement",
            symbol=symbol,
            raw_trigger_ref=raw_trigger_ref,
            supporting_evidence_refs=[raw_trigger_ref],
            requested_priority=None,
            research_package_ref=None,
            created_by="supporting_evidence_router",
        )
        self.register(proposal)
        entry = self.entries[proposal.topic_proposal_id]
        routed = TopicQueueEntry(
            **{
                **entry.__dict__,
                "rejected_reason": "supporting_evidence_only",
                "hard_gate_results": {**entry.hard_gate_results, "supporting_evidence_only": True},
            }
        )
        self.entries[routed.topic_id] = routed
        self.supporting_evidence_routes[routed.topic_id] = route_to
        return routed

    def formal_ic_entries(self) -> list[TopicQueueEntry]:
        return [entry for entry in self.entries.values() if entry.formal_ic_status in {"queued", "active"}]
