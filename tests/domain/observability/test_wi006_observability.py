from velentrade.domain.observability.health import ObservabilityCollector


def test_observability_collector_projects_devops_health_read_model():
    collector = ObservabilityCollector()
    collector.record_metric("workflow_stage_duration_seconds", {"workflow_id": "wf-1", "stage": "S1", "value": 12})
    collector.record_metric("agent_run_duration_seconds", {"agent_run_id": "run-1", "status": "timed_out", "value": 301})
    collector.record_metric("model_token_total", {"model_profile": "fake_test", "tokens": 20000, "cost": 3.2})
    collector.record_sensitive_denial("macro_analyst", "finance_sensitive_raw")

    read_model = collector.devops_health_read_model()

    assert read_model["routine_checks"][0]["status"] == "observed"
    assert read_model["incidents"][0]["incident_type"] == "runner"
    assert read_model["recovery"][0]["investment_resume_allowed"] is False
    assert collector.metrics["sensitive_field_access_denial_total"] == 1
