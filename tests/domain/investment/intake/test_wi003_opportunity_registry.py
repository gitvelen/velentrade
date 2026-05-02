from velentrade.domain.investment.intake.registry import OpportunityRegistry, TopicProposal


def test_open_sources_register_opportunities_without_entering_formal_ic_directly():
    registry = OpportunityRegistry()
    sources = ["owner", "analyst", "researcher", "service_signal", "holding_risk", "announcement"]

    proposals = [
        registry.register(
            TopicProposal(
                topic_proposal_id=f"topic-{source}",
                source_type=source,
                symbol="600000.SH",
                raw_trigger_ref=f"raw-{source}",
                supporting_evidence_refs=[f"evidence-{source}"],
                requested_priority=None,
                research_package_ref="research-pkg-1",
                created_by=source,
            )
        )
        for source in sources
    ]

    assert [proposal.source_type for proposal in proposals] == sources
    assert {entry.formal_ic_status for entry in registry.entries.values()} == {"candidate"}

    supporting_only = registry.route_supporting_evidence("news-1", symbol="600000.SH")
    assert supporting_only.formal_ic_status == "candidate"
    assert supporting_only.rejected_reason == "supporting_evidence_only"
    assert registry.formal_ic_entries() == []


def test_supporting_evidence_can_only_route_to_candidate_or_research_paths():
    registry = OpportunityRegistry()

    candidate = registry.route_supporting_evidence("news-1", symbol="600000.SH", route_to="candidate")
    research_package = registry.route_supporting_evidence("news-2", symbol="600000.SH", route_to="research_package")
    research_task = registry.route_supporting_evidence("news-3", symbol="600000.SH", route_to="research_task")

    assert candidate.formal_ic_status == "candidate"
    assert research_package.formal_ic_status == "candidate"
    assert research_task.formal_ic_status == "candidate"
    assert registry.supporting_evidence_routes[candidate.topic_id] == "candidate"
    assert registry.supporting_evidence_routes[research_package.topic_id] == "research_package"
    assert registry.supporting_evidence_routes[research_task.topic_id] == "research_task"
    assert registry.formal_ic_entries() == []
