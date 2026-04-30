from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    model_profile_id: str
    provider_profile_id: str
    purpose: str
    model_name: str
    max_input_tokens: int
    max_output_tokens: int
    default_temperature: float
    cost_budget_cny: float
    rate_limit_policy: str
    fallback_profile_ids: list[str]
    status: str


def build_model_profiles() -> dict[str, ModelProfile]:
    return {
        "fake_test": ModelProfile(
            model_profile_id="fake_test",
            provider_profile_id="deterministic_local",
            purpose="fake_test",
            model_name="fake-test-deterministic",
            max_input_tokens=8000,
            max_output_tokens=2000,
            default_temperature=0.0,
            cost_budget_cny=0.0,
            rate_limit_policy="local",
            fallback_profile_ids=[],
            status="active",
        )
    }


def route_model_profile(profile_id: str) -> ModelProfile:
    profiles = build_model_profiles()
    if profile_id not in profiles:
        raise KeyError(profile_id)
    return profiles[profile_id]
