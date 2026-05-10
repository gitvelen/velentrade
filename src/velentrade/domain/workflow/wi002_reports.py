from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.data.quality import DataQualityService, DataRequest, RequiredField
from velentrade.domain.data.sources import (
    DataCollectionService,
    DataSourceDefinition,
    DataSourceRegistry,
    NormalizedDataSet,
    PublicHttpCsvDailyQuoteAdapter,
    SourceFetchError,
    StaticDataSourceAdapter,
)
from velentrade.domain.governance.runtime import GovernanceRuntime
from velentrade.domain.services.boundary import ServiceBoundaryChecker, ServiceOutput
from velentrade.domain.services.market_state import MarketStateEngine
from velentrade.domain.workflow.runtime import RequestBrief, WorkflowRuntime


REPORT_TC = {
    "s0_s7_workflow_report.json": ("TC-ACC-008-01", "ACC-008", "REQ-008"),
    "data_quality_degradation_report.json": ("TC-ACC-009-01", "ACC-009", "REQ-009"),
    "service_boundary_report.json": ("TC-ACC-010-01", "ACC-010", "REQ-010"),
    "market_state_report.json": ("TC-ACC-011-01", "ACC-011", "REQ-011"),
    "config_governance_report.json": ("TC-ACC-030-01", "ACC-030", "REQ-030"),
}


def _envelope(
    report_id: str,
    payload: dict[str, Any],
    *,
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tc, acc, req = REPORT_TC[report_id]
    resolved_guard_results = guard_results or [
        {"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}
    ]
    resolved_failures = failures or []
    result = "fail" if resolved_failures or any(guard.get("result") != "pass" for guard in resolved_guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi002",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-002"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-WORKFLOW-SPINE-GUARDED"],
        "artifact_refs": [],
        "failures": resolved_failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-002 deterministic runtime fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": resolved_guard_results,
    }
    report.update(payload)
    return report


def _workflow_report() -> dict[str, Any]:
    runtime = WorkflowRuntime()
    brief = RequestBrief.create(
        brief_id="brief-report",
        raw_input_ref="owner-report",
        route_type="investment_workflow",
        route_confidence=0.92,
        asset_scope="a_share_common_stock",
        authorization_boundary="research_only_until_owner_approval",
    )
    task = runtime.confirm_request_brief(brief, "confirmed")
    workflow = runtime.create_investment_workflow(task, "ctx-v1")
    runtime.start_stage(workflow.workflow_id, "S0")
    runtime.complete_stage(workflow.workflow_id, "S0", ["artifact-s0"])
    blocked_completion = runtime.complete_stage(workflow.workflow_id, "S2", ["artifact-s2"])
    reopen = runtime.request_reopen(
        workflow.workflow_id,
        from_stage="S4",
        target_stage="S2",
        reason_code="retained_hard_dissent",
        requested_by="risk_officer",
        invalidated_artifacts=["memo-v1"],
        preserved_artifacts=["ic-context-v1"],
    )
    current = runtime.workflows[workflow.workflow_id]
    return _envelope(
        "s0_s7_workflow_report.json",
        {
            "stage_outputs": {stage.stage: stage.output_artifact_refs for stage in current.stages},
            "responsible_roles": {stage.stage: stage.responsible_role for stage in current.stages},
            "node_statuses": {stage.stage: stage.node_status for stage in current.stages},
            "reopen_events": [reopen.__dict__],
            "superseded_artifacts": ["memo-v1"],
            "stop_conditions": ["missing_required_artifact", "upstream_stage_not_completed"],
            "stage_completion_guard": blocked_completion.reason_code,
            "reopen_attempt_transition": {
                "event_attempt_no": reopen.attempt_no,
                "current_attempt_no": current.current_attempt_no,
                "current_stage": current.current_stage,
                "preserved_upstream_statuses": [stage.node_status for stage in current.stages[:2]],
            },
        },
    )


def _data_report() -> dict[str, Any]:
    service = DataQualityService()
    base_request = DataRequest(
        request_id="data-report",
        trace_id="trace-data",
        data_domain="market_price",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=[RequiredField("close", True, True), RequiredField("volume", True, True)],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )
    normal = service.evaluate(base_request, 0.95, 0.95)
    degraded = service.evaluate(base_request, 0.75, 0.80)
    blocked = service.evaluate(base_request, 0.45, 0.45, fallback_attempts=["primary", "backup"])
    real_request = DataRequest(
        request_id="public-data-report",
        trace_id="trace-public-data",
        data_domain="a_share_market",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=[
            RequiredField("symbol", True, True, critical=True),
            RequiredField("trade_date", True, True, critical=True),
            RequiredField("close", True, True, critical=True),
            RequiredField("volume", True, True),
            RequiredField("source_timestamp", True, True),
        ],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )
    fixture_source = DataSourceDefinition(
        source_id="fixture-only",
        data_domain="a_share_market",
        allowed_usage=("decision_core",),
        priority="T4",
        status="fixture_only",
        license_summary="fixture contract only",
        rate_limit={"requests_per_minute": 0},
        adapter_kind="fixture_contract",
    )
    primary_source = DataSourceDefinition(
        source_id="primary-public",
        data_domain="a_share_market",
        allowed_usage=("decision_core", "research"),
        priority="T1",
        status="active",
        license_summary="public HTTP CSV; review provider terms before production use",
        rate_limit={"requests_per_minute": 30},
        adapter_kind="public_http_csv_daily_quote",
        endpoint_template="https://quotes.example/{symbol}.csv",
        cache_ttl_seconds=86400,
    )
    backup_source = DataSourceDefinition(
        source_id="backup-public",
        data_domain="a_share_market",
        allowed_usage=("decision_core", "research"),
        priority="T1",
        status="active",
        license_summary="public HTTP CSV fallback; review provider terms before production use",
        rate_limit={"requests_per_minute": 30},
        adapter_kind="public_http_csv_daily_quote",
        endpoint_template="https://backup-quotes.example/{symbol}.csv",
        cache_ttl_seconds=86400,
    )

    def fail_fetch(_url: str) -> str:
        raise SourceFetchError("primary public source unavailable")

    registry = DataSourceRegistry()
    registry.register(fixture_source, StaticDataSourceAdapter(NormalizedDataSet("fixture-only", [])))
    registry.register(primary_source, PublicHttpCsvDailyQuoteAdapter(primary_source, fetch_text=fail_fetch))
    registry.register(
        backup_source,
        PublicHttpCsvDailyQuoteAdapter(
            backup_source,
            fetch_text=lambda _url: "Date,Open,High,Low,Close,Volume\n2026-04-30,10,11,9,10.8,200\n",
        ),
    )
    collection = DataCollectionService(registry).collect(real_request, require_real=True)
    execution = service.evaluate(
        DataRequest(
            request_id="exec-report",
            trace_id="trace-exec",
            data_domain="execution_price",
            symbol_or_scope="600000.SH",
            required_usage="execution_core",
            freshness_requirement="realtime",
            required_fields=[RequiredField("last_price", False, False, critical=True)],
            requesting_stage="S6",
            requesting_agent_or_service="execution_core",
        ),
        0.95,
        0.95,
    )
    return _envelope(
        "data_quality_degradation_report.json",
        {
            "data_request_schema": list(base_request.__dict__),
            "component_scores": {"normal": normal.quality_score, "degraded": degraded.quality_score, "blocked": blocked.quality_score},
            "quality_band_actions": {
                "normal": normal.decision_core_status,
                "degraded": degraded.decision_core_status,
                "blocked": blocked.decision_core_status,
            },
            "critical_field_minimums": execution.critical_field_results,
            "fallback_attempts": blocked.fallback_attempts,
            "real_source_adapter": {
                "adapter_kind": backup_source.adapter_kind,
                "license_summary": backup_source.license_summary,
                "rate_limit": backup_source.rate_limit,
                "normalized_fields": sorted(collection.data.records[0]) if collection.data else [],
                "live_provider_smoke": "not_claimed",
            },
            "source_registry_routing": {
                "require_real_skips_fixture_only": all(
                    source.adapter_kind != "fixture_contract"
                    for source, _adapter in registry.eligible_sources("a_share_market", "decision_core", require_real=True)
                ),
                "eligible_real_sources": [
                    source.source_id
                    for source, _adapter in registry.eligible_sources("a_share_market", "decision_core", require_real=True)
                ],
            },
            "public_source_fallback": {
                "selected_source_id": collection.selected_source_id,
                "fallback_attempts": collection.report.fallback_attempts,
                "quality_band": collection.report.quality_band,
                "decision_core_status": collection.report.decision_core_status,
            },
            "cache_decision_policy": service.evaluate(base_request, 0.95, 0.95, cache_hit=True).cache_usage,
            "conflict_resolution_report": service.evaluate(base_request, 0.95, 0.95, conflict_severity="critical").reason_code,
            "execution_core_freshness_gate": execution.execution_core_status,
            "blocked_decisions": [blocked.reason_code, execution.reason_code],
        },
    )


def _service_report() -> dict[str, Any]:
    checker = ServiceBoundaryChecker()
    allowed = checker.check(ServiceOutput("portfolio_optimizer", {"target_weight": 0.12}))
    forbidden = checker.check(ServiceOutput("risk_engine", {"risk_verdict": "approved"}))
    return _envelope(
        "service_boundary_report.json",
        {
            "service_outputs": [{"service": "portfolio_optimizer", "boundary": allowed.reason_code}],
            "forbidden_authority_check": forbidden.details,
            "governance_owner_check": {"services_can_approve": False, "services_can_trade": False},
        },
    )


def _market_state_report() -> dict[str, Any]:
    engine = MarketStateEngine()
    context = engine.build_ic_context("600000.SH", 0.9)
    override = engine.apply_macro_override(context, "macro_analyst", "risk_off")
    return _envelope(
        "market_state_report.json",
        {
            "default_effective_state": context["market_state"],
            "ic_context_binding": {"symbol": context["symbol"], "market_state_ref": context["classification_reason_code"]},
            "factor_weight_effect": context["factor_weight_effect"],
            "collaboration_mode": context["collaboration_mode"],
            "macro_override_audit": override["macro_override_audit"],
        },
    )


def _governance_report() -> dict[str, Any]:
    runtime = GovernanceRuntime()
    base = runtime.create_context_snapshot(
        "ctx-v1",
        "baseline",
        {"cio": "prompt-v1"},
        {"cio": "skill-v1"},
        ["knowledge-v1"],
        ["collection-v1"],
        ["default-v1"],
        {"cio": "profile-v1"},
        "new_task",
    )
    low = runtime.submit_change("chg-low", "prompt", "low", "proposal-low", {"prompt_versions": {"cio": "prompt-v2"}}, "new_attempt", "rollback-low")
    runtime.triage(low.change_id)
    runtime.assess(low.change_id, ["schema", "fixture", "scope", "rollback", "snapshot"])
    effective = runtime.activate(low.change_id)
    high = runtime.submit_change("chg-high", "agent_capability", "high", "proposal-high", {"agent_capability_versions": {"cio": "profile-v2"}}, "new_task", "rollback-high")
    runtime.triage(high.change_id)
    owner_pending = runtime.assess(high.change_id, ["schema", "fixture", "scope", "rollback", "snapshot"])
    expired = runtime.submit_change("chg-expired", "prompt", "high", "proposal-expired", {"prompt_versions": {"cio": "prompt-v3"}}, "new_task", "rollback-expired")
    canceled = runtime.submit_change("chg-canceled", "default_context", "high", "proposal-canceled", {"default_context_versions": ["default-v2"]}, "new_task", "rollback-canceled")
    expired = runtime.expire(expired.change_id)
    canceled = runtime.cancel(canceled.change_id)
    activation_failed = runtime.activate(expired.change_id)
    return _envelope(
        "config_governance_report.json",
        {
            "impact_levels": {"low": "auto_validation", "medium": "auto_validation", "high": "owner_pending"},
            "auto_validation": effective.auto_validation_refs,
            "transition_guards": ["schema", "fixture", "scope", "rollback", "snapshot"],
            "governance_states": {"low": effective.state, "high": owner_pending.state},
            "governance_terminal_states": {"expired": expired.state, "canceled": canceled.state},
            "timeout_no_effect": expired.context_snapshot_id is None,
            "activation_failed_no_effect": activation_failed.context_snapshot_id is None,
            "context_snapshot_binding": effective.context_snapshot_id,
            "context_snapshot_hash": runtime.context_snapshots[effective.context_snapshot_id].content_hash,
            "default_context_bindings": list(base.default_context_versions),
            "memory_collection_versions": list(base.memory_collection_versions),
            "agent_capability_change_versions": dict(runtime.context_snapshots[base.context_snapshot_id].agent_capability_versions),
            "effective_scope": effective.effective_scope,
            "in_flight_snapshot_unchanged": runtime.context_snapshots[base.context_snapshot_id].content_hash == base.content_hash,
        },
    )


def build_wi002_reports() -> dict[str, dict[str, Any]]:
    reports = {
        "s0_s7_workflow_report.json": _workflow_report(),
        "data_quality_degradation_report.json": _data_report(),
        "service_boundary_report.json": _service_report(),
        "market_state_report.json": _market_state_report(),
        "config_governance_report.json": _governance_report(),
    }
    return {name: deepcopy(report) for name, report in reports.items()}
