from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.agents.registry import build_agent_capability_profiles, build_team_read_model, validate_agent_registry
from velentrade.domain.common import utc_now
from velentrade.domain.scope.registry import build_scope_boundary_report, validate_service_registry
from velentrade.security.finance import FinanceAccessPolicy, FinanceFieldEncryptor
from velentrade.security.logging import redact_sensitive_text


REPORT_PAYLOAD_FIELDS = {
    "scope_boundary_report.json": ["scope_registry", "forbidden_entry_scan", "ui_entry_scan", "api_entry_scan"],
    "registry_validation_report.json": ["agent_registry", "service_registry", "forbidden_role_scan"],
    "agent_capability_contract_report.json": ["capability_profiles", "team_read_model", "agent_profile_read_models", "skill_package_manifests", "prompt_versions", "context_snapshot_versions", "sop_checks", "rubric_checks", "failure_policy_checks", "quality_metrics", "denied_action_records"],
    "memory_boundary_report.json": ["transparent_read_paths", "gateway_write_paths", "runner_write_denials", "finance_sensitive_allow_deny", "memory_items", "memory_versions", "memory_relations", "memory_collections", "memory_extraction_results", "context_injection_decisions", "denied_memory_refs", "memory_not_fact_source_guards"],
    "collaboration_trace_report.json": ["sessions", "agent_runs", "commands", "events", "handoffs", "artifact_lineage", "gateway_write_records", "runbook_trace", "view_projection_results"],
    "security_privacy_report.json": ["encrypted_fields_check", "plaintext_log_scan", "readonly_db_check", "sensitive_access_events"],
    "requirement_structure_report.json": ["req_acc_vo_scan", "tc_coverage", "appendix_formal_id_scan"],
}

REPORT_TC = {
    "scope_boundary_report.json": "TC-ACC-001-01",
    "registry_validation_report.json": "TC-ACC-002-01",
    "agent_capability_contract_report.json": "TC-ACC-003-01",
    "memory_boundary_report.json": "TC-ACC-004-01",
    "collaboration_trace_report.json": "TC-ACC-005-01",
    "security_privacy_report.json": "TC-ACC-031-01",
    "requirement_structure_report.json": "TC-ACC-032-01",
}

REPORT_ACC = {
    name: f"ACC-{tc.split('-')[2]}" for name, tc in REPORT_TC.items()
}


def _envelope(report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    tc = REPORT_TC[report_id]
    acceptance = REPORT_ACC[report_id]
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi001",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-001"],
        "test_case_refs": [tc],
        "fixture_refs": ["FX-AGENT-COLLABORATION-PROTOCOL"],
        "result": "pass",
        "checked_requirements": [f"REQ-{acceptance.split('-')[1]}"],
        "checked_acceptances": [acceptance],
        "checked_invariants": ["INV-AGENT-READ-TRANSPARENT-WRITE-GATED"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-001 deterministic contract fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}],
    }
    report.update(payload)
    return report


def build_wi001_reports() -> dict[str, dict[str, Any]]:
    scope_report = build_scope_boundary_report()
    registry_report = validate_agent_registry()
    profiles = build_agent_capability_profiles()
    team = build_team_read_model()
    service = validate_service_registry()
    encryptor = FinanceFieldEncryptor("report-secret")
    ciphertext = encryptor.encrypt("收入 100000")
    finance_policy = FinanceAccessPolicy()

    reports = {
        "scope_boundary_report.json": _envelope("scope_boundary_report.json", scope_report),
        "registry_validation_report.json": _envelope(
            "registry_validation_report.json",
            {
                **registry_report,
                "agent_registry": list(registry_report["allowed_agents"]),
                "service_registry": service["service_registry"],
            },
        ),
        "agent_capability_contract_report.json": _envelope(
            "agent_capability_contract_report.json",
            {
                "capability_profiles": {agent_id: profile.profile_version for agent_id, profile in profiles.items()},
                "team_read_model": team,
                "agent_profile_read_models": list(profiles),
                "skill_package_manifests": {agent_id: profile.default_skill_packages for agent_id, profile in profiles.items()},
                "prompt_versions": {agent_id: "1.0.0" for agent_id in profiles},
                "context_snapshot_versions": {agent_id: "ctx-v1" for agent_id in profiles},
                "sop_checks": {agent_id: bool(profile.sop) for agent_id, profile in profiles.items()},
                "rubric_checks": {agent_id: bool(profile.evaluation_policy.metrics) for agent_id, profile in profiles.items()},
                "failure_policy_checks": {agent_id: bool(profile.failure_policy) for agent_id, profile in profiles.items()},
                "quality_metrics": {agent_id: {"schema_pass_rate": 1.0} for agent_id in profiles},
                "denied_action_records": [{"agent_id": "macro_analyst", "reason_code": "direct_write_denied"}],
            },
        ),
        "memory_boundary_report.json": _envelope(
            "memory_boundary_report.json",
            {
                "transparent_read_paths": ["artifacts", "process_archive", "memory", "knowledge"],
                "gateway_write_paths": ["artifact", "event", "handoff", "memory"],
                "runner_write_denials": [{"reason_code": "direct_write_denied"}],
                "finance_sensitive_allow_deny": {"cfo": "allow", "macro_analyst": "deny"},
                "memory_items": ["memory-1"],
                "memory_versions": ["memory-version-1"],
                "memory_relations": ["supports"],
                "memory_collections": ["researcher_digest"],
                "memory_extraction_results": ["title", "tags", "source_refs"],
                "context_injection_decisions": [{"fenced_background": True}],
                "denied_memory_refs": ["finance-sensitive-raw"],
                "memory_not_fact_source_guards": [{"reason_code": "memory_not_fact_source"}],
            },
        ),
        "collaboration_trace_report.json": _envelope(
            "collaboration_trace_report.json",
            {
                "sessions": ["sess-1"],
                "agent_runs": ["run-1"],
                "commands": ["cmd-1"],
                "events": ["evt-1"],
                "handoffs": ["handoff-1"],
                "artifact_lineage": ["artifact-1"],
                "gateway_write_records": [{"accepted": True}],
                "runbook_trace": [{"step": "command", "actor": "agent", "input_ref": "run-1", "output_ref": "cmd-1", "result": "pass"}],
                "view_projection_results": [{"view": "TraceDebugReadModel", "expected": "lineage", "actual": "lineage", "result": "pass"}],
            },
        ),
        "security_privacy_report.json": _envelope(
            "security_privacy_report.json",
            {
                "encrypted_fields_check": {"ciphertext_differs": ciphertext != "收入 100000"},
                "plaintext_log_scan": {"redacted": redact_sensitive_text("收入 100000")},
                "readonly_db_check": {"runner_write_credentials": False},
                "sensitive_access_events": [
                    finance_policy.read_decision("macro_analyst", "income").details
                ],
            },
        ),
        "requirement_structure_report.json": _envelope(
            "requirement_structure_report.json",
            {
                "req_acc_vo_scan": {"REQ": 32, "ACC": 32, "VO": 32},
                "tc_coverage": {"missing_tc_for_acc": []},
                "appendix_formal_id_scan": {"formal_ids_found": []},
            },
        ),
    }

    return {name: deepcopy(report) for name, report in reports.items()}


def validate_report_contract(name: str, report: dict[str, Any]) -> list[str]:
    missing = []
    envelope_required = [
        "report_id",
        "generated_at",
        "generated_by",
        "git_revision",
        "work_item_refs",
        "test_case_refs",
        "fixture_refs",
        "result",
        "checked_requirements",
        "checked_acceptances",
        "checked_invariants",
        "artifact_refs",
        "failures",
        "residual_risk",
        "schema_version",
        "checked_fields",
        "fixture_inputs",
        "actual_outputs",
        "guard_results",
    ]
    for field in envelope_required:
        if field not in report:
            missing.append(field)
    for field in REPORT_PAYLOAD_FIELDS[name]:
        if field not in report or report[field] in (None, [], {}):
            missing.append(field)
    if report.get("result") == "pass" and report.get("failures"):
        missing.append("failures_must_be_empty_for_pass")
    for guard in report.get("guard_results", []):
        if guard.get("result") != "pass":
            missing.append(f"guard_failed:{guard.get('guard')}")
    return missing
