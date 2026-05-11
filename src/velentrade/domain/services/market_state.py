from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketState:
    state: str
    reason_code: str
    factor_weight_effect: dict[str, float]
    collaboration_mode: str


class MarketStateEngine:
    def classify(self, risk_signal: float) -> MarketState:
        if risk_signal <= -0.6:
            state = "stress"
        elif risk_signal < 0:
            state = "risk_off"
        elif risk_signal < 0.4:
            state = "neutral"
        elif risk_signal < 0.75:
            state = "transition"
        else:
            state = "risk_on"
        return MarketState(
            state=state,
            reason_code=f"market_state_{state}",
            factor_weight_effect=self._weights_for(state),
            collaboration_mode="default_effective",
        )

    def _weights_for(self, state: str) -> dict[str, float]:
        if state == "risk_on":
            return {"momentum": 1.2, "quality": 1.0, "defensive": 0.8}
        if state in {"risk_off", "stress"}:
            return {"momentum": 0.7, "quality": 1.0, "defensive": 1.3}
        if state == "transition":
            return {"momentum": 0.9, "quality": 1.1, "defensive": 1.0}
        return {"momentum": 1.0, "quality": 1.0, "defensive": 1.0}

    def build_ic_context(self, symbol: str, signal: float) -> dict:
        market = self.classify(signal)
        return {
            "symbol": symbol,
            "market_state": market.state,
            "classification_reason_code": market.reason_code,
            "factor_weight_effect": market.factor_weight_effect,
            "collaboration_mode": market.collaboration_mode,
            "macro_override_audit": None,
        }

    def apply_macro_override(self, context: dict, macro_agent_id: str, override_state: str) -> dict:
        updated = dict(context)
        previous = context["market_state"]
        updated["market_state"] = override_state
        updated["factor_weight_effect"] = self._weights_for(override_state)
        updated["macro_override_audit"] = {
            "macro_agent_id": macro_agent_id,
            "previous_state": previous,
            "override_state": override_state,
            "is_default_gate": False,
        }
        return updated
