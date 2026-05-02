from velentrade.domain.data.quality import DataQualityService, DataRequest, RequiredField


def test_data_quality_three_bands_fallback_cache_conflict_and_execution_block():
    service = DataQualityService()
    request = DataRequest(
        request_id="data-1",
        trace_id="trace-1",
        data_domain="market_price",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=[
            RequiredField("close", present=True, valid=True),
            RequiredField("volume", present=True, valid=True),
        ],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )

    normal = service.evaluate(request, accuracy=0.95, timeliness=0.95)
    degraded = service.evaluate(request, accuracy=0.75, timeliness=0.80)
    blocked = service.evaluate(request, accuracy=0.45, timeliness=0.45, fallback_attempts=["primary", "backup"])

    assert normal.quality_score == 0.97
    assert normal.quality_band == "normal"
    assert normal.decision_core_status == "pass"
    assert degraded.quality_band == "degraded"
    assert degraded.decision_core_status == "conditional_pass_owner_exception_required"
    assert blocked.quality_band == "blocked"
    assert blocked.decision_core_status == "blocked"
    assert blocked.fallback_attempts == ["primary", "backup"]

    cached = service.evaluate(request, accuracy=0.95, timeliness=0.95, cache_hit=True)
    assert cached.cache_usage["may_create_execution_authorization"] is False

    conflict = service.evaluate(request, accuracy=0.95, timeliness=0.95, conflict_severity="critical")
    assert conflict.quality_band == "blocked"
    assert conflict.reason_code == "critical_conflict_blocked"

    execution_request = DataRequest(
        request_id="exec-1",
        trace_id="trace-2",
        data_domain="execution_price",
        symbol_or_scope="600000.SH",
        required_usage="execution_core",
        freshness_requirement="realtime",
        required_fields=[RequiredField("last_price", present=False, valid=False, critical=True)],
        requesting_stage="S6",
        requesting_agent_or_service="execution_core",
    )
    execution = service.evaluate(execution_request, accuracy=0.95, timeliness=0.95)
    assert execution.execution_core_status == "blocked"
    assert execution.reason_code == "critical_field_blocked"


def test_decision_core_score_at_point_75_is_degraded_not_blocked():
    service = DataQualityService()
    request = DataRequest(
        request_id="data-boundary",
        trace_id="trace-boundary",
        data_domain="market_price",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=[
            RequiredField("close", present=True, valid=True, weight=0.75),
            RequiredField("volume", present=False, valid=False, weight=0.25),
        ],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )

    report = service.evaluate(request, accuracy=0.75, timeliness=0.75)

    assert report.quality_score == 0.75
    assert report.quality_band == "degraded"
    assert report.decision_core_status == "conditional_pass_owner_exception_required"
