from velentrade.domain.workflow.wi002_reports import build_wi002_reports


def test_wi002_reports_include_contract_payloads_and_branch_local_evidence_fields():
    reports = build_wi002_reports()

    expected_fields = {
        "s0_s7_workflow_report.json": {
            "stage_outputs",
            "responsible_roles",
            "node_statuses",
            "reopen_events",
            "superseded_artifacts",
            "stop_conditions",
        },
        "data_quality_degradation_report.json": {
            "data_request_schema",
            "component_scores",
            "quality_band_actions",
            "critical_field_minimums",
            "fallback_attempts",
            "real_source_adapter",
            "source_registry_routing",
            "public_source_fallback",
            "cache_decision_policy",
            "conflict_resolution_report",
            "execution_core_freshness_gate",
            "blocked_decisions",
        },
        "service_boundary_report.json": {
            "service_outputs",
            "forbidden_authority_check",
            "governance_owner_check",
        },
        "market_state_report.json": {
            "default_effective_state",
            "ic_context_binding",
            "factor_weight_effect",
            "collaboration_mode",
            "macro_override_audit",
        },
        "config_governance_report.json": {
            "impact_levels",
            "auto_validation",
            "transition_guards",
            "governance_states",
            "governance_terminal_states",
            "timeout_no_effect",
            "activation_failed_no_effect",
            "context_snapshot_binding",
            "context_snapshot_hash",
            "default_context_bindings",
            "memory_collection_versions",
            "agent_capability_change_versions",
            "effective_scope",
            "in_flight_snapshot_unchanged",
        },
    }

    assert set(reports) == set(expected_fields)
    for name, fields in expected_fields.items():
        report = reports[name]
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-002"]
        assert report["failures"] == []
        assert set(report) >= fields
        assert report["guard_results"][0]["result"] == "pass"

    data_report = reports["data_quality_degradation_report.json"]
    assert data_report["real_source_adapter"]["adapter_kind"] == "public_http_csv_daily_quote"
    assert data_report["real_source_adapter"]["live_provider_smoke"] == "not_claimed"
    assert data_report["source_registry_routing"]["require_real_skips_fixture_only"] is True
    assert data_report["public_source_fallback"]["selected_source_id"] == "backup-public"
    assert data_report["public_source_fallback"]["quality_band"] == "normal"
