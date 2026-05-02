from __future__ import annotations

from hashlib import sha256

from sqlalchemy.engine import Engine

from velentrade.db.base import Base
from velentrade.domain.agents.registry import build_agent_capability_profiles
from velentrade.domain.common import utc_now
from velentrade.model_gateway.profiles import build_model_profiles


def build_wi001_seed_bundle() -> dict:
    now = utc_now()
    profiles = build_agent_capability_profiles()
    model_profiles = build_model_profiles()

    skill_package_ids = sorted(
        {
            skill_package
            for profile in profiles.values()
            for skill_package in profile.default_skill_packages
        }
    )

    capability_profile_rows = [
        {
            "agent_id": profile.agent_id,
            "display_name": profile.display_name,
            "role": profile.role,
            "profile_version": profile.profile_version,
            "default_model_profile": profile.default_model_profile,
            "default_tool_profile_id": profile.default_tool_profile_id,
        }
        for profile in profiles.values()
    ]

    model_profile_rows = [
        {
            "model_profile_id": profile.model_profile_id,
            "provider_profile_id": profile.provider_profile_id,
            "purpose": profile.purpose,
            "model_name": profile.model_name,
            "status": profile.status,
        }
        for profile in model_profiles.values()
    ]

    tool_profile_rows = [
        {
            "tool_profile_id": "readonly-basic",
            "description": "Read-only DB/file/network/tool profile for WI-001 foundations.",
            "status": "active",
        }
    ]

    skill_package_rows = [
        {
            "package_id": package_id,
            "display_name": package_id.replace("-", " ").title(),
            "status": "active",
            "created_at": now,
        }
        for package_id in skill_package_ids
    ]
    skill_package_version_rows = [
        {
            "package_version_id": f"{package_id}@1.0.0",
            "package_id": package_id,
            "version": "1.0.0",
            "manifest_hash": sha256(package_id.encode("utf-8")).hexdigest(),
            "status": "active",
            "created_at": now,
        }
        for package_id in skill_package_ids
    ]

    context_snapshot = {
        "context_snapshot_id": "ctx-v1",
        "snapshot_version": "ctx-v1",
        "effective_scope": "test_fixture",
        "content_hash": sha256("ctx-v1".encode("utf-8")).hexdigest(),
        "payload": {
            "model_route_version": "fake_test",
            "tool_permission_versions": ["readonly-basic"],
            "skill_package_versions": [row["package_version_id"] for row in skill_package_version_rows],
            "registry_versions": {
                "agent_profiles": {row["agent_id"]: row["profile_version"] for row in capability_profile_rows}
            },
        },
        "frozen": True,
        "created_at": now,
        "effective_from": now,
    }
    data_domains = [
        {
            "domain_id": "a_share_market",
            "display_name": "A 股行情",
            "status": "active",
            "payload": {"required_fields": ["symbol", "trade_date", "close", "volume"]},
            "created_at": now,
        },
        {
            "domain_id": "corporate_announcement",
            "display_name": "上市公司公告",
            "status": "active",
            "payload": {"required_fields": ["symbol", "published_at", "title", "source_url"]},
            "created_at": now,
        },
        {
            "domain_id": "macro_calendar",
            "display_name": "宏观日历",
            "status": "active",
            "payload": {"required_fields": ["event_date", "indicator", "actual_or_forecast"]},
            "created_at": now,
        },
    ]
    data_sources = [
        {
            "source_id": "fixture-a-share-daily",
            "data_domain": "a_share_market",
            "usage_scope": "decision_core",
            "priority": "T4",
            "status": "fixture_only",
            "license_summary": "fixture contract only; not proof of live data collection",
            "rate_limit": {"requests_per_minute": 0},
            "adapter_kind": "fixture_contract",
            "payload": {"completion_level": "fixture_contract"},
            "created_at": now,
        },
        {
            "source_id": "tencent-public-kline",
            "data_domain": "a_share_market",
            "usage_scope": "research,decision_core",
            "priority": "T2",
            "status": "active",
            "license_summary": "Tencent public quote endpoint; no API key; review provider terms and rate limits before production use",
            "rate_limit": {"requests_per_minute": 20},
            "adapter_kind": "public_http_json_kline_daily_quote",
            "payload": {
                "endpoint_template": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,10,qfq",
                "cache_ttl_seconds": 86400,
                "symbol_mapper": "tencent_market_symbol",
                "completion_level": "in_memory_domain",
            },
            "created_at": now,
        },
        {
            "source_id": "fixture-announcement",
            "data_domain": "corporate_announcement",
            "usage_scope": "research",
            "priority": "T4",
            "status": "fixture_only",
            "license_summary": "fixture contract only; not proof of live data collection",
            "rate_limit": {"requests_per_minute": 0},
            "adapter_kind": "fixture_contract",
            "payload": {"completion_level": "fixture_contract"},
            "created_at": now,
        },
        {
            "source_id": "fixture-macro-calendar",
            "data_domain": "macro_calendar",
            "usage_scope": "research",
            "priority": "T4",
            "status": "fixture_only",
            "license_summary": "fixture contract only; not proof of live data collection",
            "rate_limit": {"requests_per_minute": 0},
            "adapter_kind": "fixture_contract",
            "payload": {"completion_level": "fixture_contract"},
            "created_at": now,
        },
    ]
    paper_account = {
        "account_id": "paper-account-v1",
        "base_currency": "CNY",
        "cash": 1_000_000,
        "total_value": 1_000_000,
        "payload": {"positions": [], "completion_level": "db_persistent"},
        "created_at": now,
    }
    owner_session = {
        "session_id": "owner-session-v1",
        "owner_role": "owner",
        "status": "active",
        "created_at": now,
        "expires_at": None,
    }
    owner_auth = {
        "user_id": "owner",
        "owner_role": "owner",
        "auth_provider": "local_v1",
        "status": "active",
        "created_at": now,
    }

    return {
        "context_snapshot": context_snapshot,
        "capability_profiles": capability_profile_rows,
        "model_profiles": model_profile_rows,
        "tool_profiles": tool_profile_rows,
        "skill_packages": skill_package_rows,
        "skill_package_versions": skill_package_version_rows,
        "data_domains": data_domains,
        "data_sources": data_sources,
        "paper_account": paper_account,
        "owner_session": owner_session,
        "owner_auth": owner_auth,
    }


def apply_wi001_seed(engine: Engine) -> None:
    bundle = build_wi001_seed_bundle()
    now = utc_now()
    tables = Base.metadata.tables

    with engine.begin() as connection:
        connection.execute(
            tables["context_snapshot"].insert(),
            [bundle["context_snapshot"]],
        )
        connection.execute(
            tables["model_profile"].insert(),
            [{**row, "created_at": now} for row in bundle["model_profiles"]],
        )
        connection.execute(
            tables["tool_profile"].insert(),
            [{**row, "created_at": now} for row in bundle["tool_profiles"]],
        )
        connection.execute(
            tables["skill_package"].insert(),
            bundle["skill_packages"],
        )
        connection.execute(
            tables["skill_package_version"].insert(),
            bundle["skill_package_versions"],
        )
        connection.execute(
            tables["data_domain_registry"].insert(),
            bundle["data_domains"],
        )
        connection.execute(
            tables["data_source_registry"].insert(),
            bundle["data_sources"],
        )
        connection.execute(
            tables["paper_account"].insert(),
            [bundle["paper_account"]],
        )
        connection.execute(
            tables["session"].insert(),
            [bundle["owner_session"]],
        )
        connection.execute(
            tables["user_auth"].insert(),
            [bundle["owner_auth"]],
        )
