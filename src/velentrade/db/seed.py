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

    return {
        "context_snapshot": context_snapshot,
        "capability_profiles": capability_profile_rows,
        "model_profiles": model_profile_rows,
        "tool_profiles": tool_profile_rows,
        "skill_packages": skill_package_rows,
        "skill_package_versions": skill_package_version_rows,
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
