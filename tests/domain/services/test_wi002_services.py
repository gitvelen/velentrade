from velentrade.domain.services.boundary import ServiceBoundaryChecker, ServiceOutput
from velentrade.domain.services.market_state import MarketStateEngine


def test_service_outputs_have_no_investment_governance_authority():
    checker = ServiceBoundaryChecker()
    allowed = ServiceOutput(
        service_name="portfolio_optimizer",
        payload={"target_weight": 0.12, "limitations": ["data_quality_degraded"]},
    )
    forbidden = ServiceOutput(
        service_name="risk_engine",
        payload={"risk_verdict": "approved", "final_investment_decision": "buy"},
    )

    assert checker.check(allowed).allowed is True
    denial = checker.check(forbidden)
    assert denial.allowed is False
    assert denial.reason_code == "service_forbidden_authority"
    assert set(denial.details["forbidden_fields"]) == {"risk_verdict", "final_investment_decision"}


def test_market_state_defaults_into_ic_context_and_macro_override_is_audited():
    engine = MarketStateEngine()

    states = {engine.classify(value).state for value in (-0.8, -0.2, 0.1, 0.5, 0.9)}
    assert states == {"stress", "risk_off", "neutral", "transition", "risk_on"}

    context = engine.build_ic_context(symbol="600000.SH", signal=0.9)
    assert context["market_state"] == "risk_on"
    assert context["factor_weight_effect"]["momentum"] > context["factor_weight_effect"]["defensive"]
    assert context["collaboration_mode"] == "default_effective"

    override = engine.apply_macro_override(context, macro_agent_id="macro_analyst", override_state="risk_off")
    assert override["market_state"] == "risk_off"
    assert override["macro_override_audit"]["previous_state"] == "risk_on"
    assert override["macro_override_audit"]["is_default_gate"] is False
