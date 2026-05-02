from velentrade.domain.investment.context.builder import ICContextBuilder


def test_ic_context_package_and_chair_brief_are_complete_without_preset_decision():
    builder = ICContextBuilder()

    package = builder.build_context_package(
        topic_id="topic-1",
        request_brief_ref="brief-1",
        data_readiness_ref="data-ready-1",
        market_state_ref="market-risk-on",
        service_result_refs=["factor-1", "valuation-1", "optimizer-1"],
        portfolio_context_ref="portfolio-1",
        risk_constraint_refs=["risk-budget-1"],
        research_package_refs=["research-1"],
        reflection_hit_refs=["reflection-1"],
        context_snapshot_id="ctx-v1",
    )
    brief = builder.build_chair_brief(package, time_budget="30m")

    assert package.role_attachment_refs == {
        "macro": "topic-1:macro",
        "fundamental": "topic-1:fundamental",
        "quant": "topic-1:quant",
        "event": "topic-1:event",
    }
    assert brief.decision_question
    assert brief.no_preset_decision_attestation is True
    forbidden_words = {"buy", "sell", "hold", "买入", "卖出", "持有"}
    text = " ".join([brief.decision_question, *brief.key_tensions, *brief.must_answer_questions])
    assert forbidden_words.isdisjoint(text.split())
    assert builder.resolve_evidence(package)["missing_refs"] == []


def test_context_builder_marks_missing_sections_and_missing_evidence_refs():
    builder = ICContextBuilder()

    package = builder.build_context_package(
        topic_id="topic-missing",
        request_brief_ref="brief-1",
        data_readiness_ref="data-ready-1",
        market_state_ref="market-neutral",
        service_result_refs=[],
        portfolio_context_ref="portfolio-1",
        risk_constraint_refs=[],
        research_package_refs=[],
        reflection_hit_refs=[],
        context_snapshot_id="ctx-v1",
    )
    evidence = builder.resolve_evidence(package)

    assert builder.missing_sections(package) == ["service_result_refs", "risk_constraint_refs", "research_package_refs"]
    assert evidence["missing_refs"] == []
    assert evidence["missing_sections"] == ["service_result_refs", "risk_constraint_refs", "research_package_refs"]
