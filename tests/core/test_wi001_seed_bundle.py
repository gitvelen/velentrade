from __future__ import annotations

from velentrade.db.base import Base
from velentrade.db.seed import build_wi001_seed_bundle


def test_seed_bundle_covers_runtime_profiles_and_official_agents():
    bundle = build_wi001_seed_bundle()

    assert bundle["context_snapshot"]["context_snapshot_id"] == "ctx-v1"
    assert bundle["context_snapshot"]["effective_scope"] == "test_fixture"

    capability_profiles = bundle["capability_profiles"]
    assert len(capability_profiles) == 9
    assert {row["agent_id"] for row in capability_profiles} == {
        "cio",
        "cfo",
        "macro_analyst",
        "fundamental_analyst",
        "quant_analyst",
        "event_analyst",
        "risk_officer",
        "investment_researcher",
        "devops_engineer",
    }

    assert bundle["model_profiles"] == [
        {
            "model_profile_id": "fake_test",
            "provider_profile_id": "deterministic_local",
            "purpose": "fake_test",
            "model_name": "fake-test-deterministic",
            "status": "active",
        }
    ]

    assert bundle["tool_profiles"] == [
        {
            "tool_profile_id": "readonly-basic",
            "description": "Read-only DB/file/network/tool profile for WI-001 foundations.",
            "status": "active",
        }
    ]

    assert len(bundle["skill_packages"]) == len(bundle["skill_package_versions"])
    assert all(row["version"] == "1.0.0" for row in bundle["skill_package_versions"])
    assert {row["domain_id"] for row in bundle["data_domains"]} == {
        "a_share_market",
        "corporate_announcement",
        "macro_calendar",
    }
    assert bundle["data_sources"][0]["adapter_kind"] == "fixture_contract"
    assert bundle["paper_account"]["cash"] == 1_000_000
    assert bundle["owner_session"]["owner_role"] == "owner"


def test_db_metadata_includes_seeded_runtime_registry_tables():
    table_names = set(Base.metadata.tables)
    assert {
        "model_profile",
        "tool_profile",
        "skill_package",
        "skill_package_version",
        "data_domain_registry",
        "data_source_registry",
        "paper_account",
        "session",
        "user_auth",
    }.issubset(table_names)
