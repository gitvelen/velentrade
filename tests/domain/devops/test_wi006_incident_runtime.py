from velentrade.domain.devops.incident import DevOpsIncidentRuntime, HealthSignal


def test_devops_incident_runtime_classifies_health_and_never_resumes_investment():
    runtime = DevOpsIncidentRuntime()

    source = runtime.handle_signal(
        HealthSignal(
            check_type="source_health",
            subject="market-primary",
            usage="execution_core",
            metrics={"critical_field_missing": True, "primary_failed": True, "fallback_failed": True},
            affected_workflows=["wf-1"],
            evidence_refs=["data-request-1"],
        )
    )
    service = runtime.handle_signal(
        HealthSignal(
            check_type="service_health",
            subject="risk-engine",
            usage="decision_core",
            metrics={"timeout_rate": 0.12, "p95_latency_seconds": 12},
            affected_workflows=["wf-2"],
            evidence_refs=["service-call-1"],
        )
    )
    execution = runtime.handle_signal(
        HealthSignal(
            check_type="execution_environment",
            subject="minute-bars",
            usage="execution_core",
            metrics={"minute_delay_minutes": 7},
            affected_workflows=["wf-3"],
            evidence_refs=["execution-precheck-1"],
        )
    )

    assert source.severity == "P0"
    assert source.status == "triaged"
    assert service.incident_type == "service"
    assert execution.severity == "P1"
    assert runtime.recovery_plans[source.incident_id].investment_resume_allowed is False
    assert runtime.risk_notifications[source.incident_id].recommended_hold_or_reopen in {"hold", "reopen"}
    assert runtime.block_risk_relaxation_attempt("risk_hard_blocker") == "blocked:risk_relaxation_requires_risk_or_governance"


def test_sensitive_log_and_cost_token_paths_have_separate_severity_semantics():
    runtime = DevOpsIncidentRuntime()

    security = runtime.handle_signal(
        HealthSignal(
            check_type="log_security",
            subject="trace-log",
            usage="security",
            metrics={"finance_raw_plaintext": True},
            affected_workflows=["wf-sec"],
            evidence_refs=["log-line-1"],
        )
    )
    cost = runtime.handle_signal(
        HealthSignal(
            check_type="cost_token",
            subject="model-route",
            usage="observability",
            metrics={"daily_cost_multiple": 2.1},
            affected_workflows=[],
            evidence_refs=["cost-window-1"],
        )
    )

    assert security.incident_type == "security"
    assert security.severity == "P0"
    assert runtime.sensitive_log_findings[0]["audit_event_ref"].startswith("audit-")
    assert cost.incident_type == "cost_token"
    assert cost.severity == "P1"
    assert runtime.cost_observations[0]["p0_pass_fail_relevant"] is False


def test_devops_incident_report_has_contract_and_tc_fields():
    report = DevOpsIncidentRuntime().build_devops_incident_report()

    assert report["result"] == "pass"
    assert report["work_item_refs"] == ["WI-006"]
    assert report["test_case_refs"] == ["TC-ACC-029-01"]
    assert set(report) >= {
        "routine_checks",
        "incidents",
        "health_signals",
        "severity_classification",
        "degradation_actions",
        "recovery_plan",
        "risk_reports",
        "investment_resume_denied_until_guard",
        "cost_observability_only",
        "health_threshold_results",
        "safe_degradation_allowlist_checks",
        "blocked_risk_relaxation_attempts",
        "recovery_validation_checklist",
    }
    assert report["investment_resume_denied_until_guard"] is True
    assert report["cost_observability_only"] is True
