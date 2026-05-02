from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequiredField:
    name: str
    present: bool
    valid: bool
    critical: bool = False
    weight: float = 1.0


@dataclass(frozen=True)
class DataRequest:
    request_id: str
    trace_id: str
    data_domain: str
    symbol_or_scope: str
    required_usage: str
    freshness_requirement: str
    required_fields: list[RequiredField]
    requesting_stage: str
    requesting_agent_or_service: str
    time_range: str | None = None


@dataclass(frozen=True)
class DataQualityReport:
    request_id: str
    quality_score: float
    quality_band: str
    critical_field_results: dict[str, bool]
    fallback_attempts: list[str]
    cache_usage: dict[str, bool]
    conflict_report_refs: list[str]
    decision_core_status: str
    execution_core_status: str
    lineage_refs: list[str]
    risk_constraints: list[str]
    reason_code: str


@dataclass
class DataQualityService:
    normal_threshold: float = 0.9
    degraded_threshold: float = 0.7
    blocked_threshold: float = 0.7

    def _completeness(self, fields: list[RequiredField]) -> float:
        total = sum(field.weight for field in fields) or 1.0
        present = sum(field.weight for field in fields if field.present and field.valid)
        return present / total

    def evaluate(
        self,
        request: DataRequest,
        accuracy: float,
        timeliness: float,
        fallback_attempts: list[str] | None = None,
        cache_hit: bool = False,
        conflict_severity: str | None = None,
    ) -> DataQualityReport:
        critical_results = {field.name: field.present and field.valid for field in request.required_fields if field.critical}
        critical_blocked = any(not ok for ok in critical_results.values())
        completeness = self._completeness(request.required_fields)
        score = round(0.4 * completeness + 0.4 * accuracy + 0.2 * timeliness, 2)

        reason_code = "quality_normal"
        if conflict_severity == "critical":
            band = "blocked"
            reason_code = "critical_conflict_blocked"
        elif critical_blocked:
            band = "blocked"
            reason_code = "critical_field_blocked"
        elif score >= self.normal_threshold:
            band = "normal"
        elif score >= self.degraded_threshold:
            band = "degraded"
            reason_code = "quality_degraded_owner_exception_required"
        else:
            band = "blocked"
            reason_code = "data_quality_guard"

        decision_status = "pass"
        execution_status = "pass"
        risk_constraints: list[str] = []
        if band == "degraded":
            decision_status = "conditional_pass_owner_exception_required"
            risk_constraints.append("risk_review_constraint_required")
        if band == "blocked":
            decision_status = "blocked"
        if request.required_usage == "execution_core" and (band != "normal" or request.freshness_requirement == "realtime"):
            if critical_blocked or timeliness < self.normal_threshold or band != "normal":
                execution_status = "blocked"
                if critical_blocked:
                    reason_code = "critical_field_blocked"
                elif timeliness < self.normal_threshold:
                    reason_code = "execution_core_freshness_failed"
                else:
                    reason_code = "execution_core_quality_failed"

        return DataQualityReport(
            request_id=request.request_id,
            quality_score=score,
            quality_band=band,
            critical_field_results=critical_results,
            fallback_attempts=fallback_attempts or [],
            cache_usage={
                "cache_hit": cache_hit,
                "may_create_execution_authorization": False if cache_hit else execution_status == "pass",
            },
            conflict_report_refs=["conflict-critical"] if conflict_severity == "critical" else [],
            decision_core_status=decision_status,
            execution_core_status=execution_status,
            lineage_refs=[f"lineage-{request.request_id}"],
            risk_constraints=risk_constraints,
            reason_code=reason_code,
        )
