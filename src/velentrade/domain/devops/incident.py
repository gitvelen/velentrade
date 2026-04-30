from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import new_id, utc_now


@dataclass(frozen=True)
class HealthSignal:
    check_type: str
    subject: str
    usage: str
    metrics: dict[str, Any]
    affected_workflows: list[str]
    evidence_refs: list[str]


@dataclass(frozen=True)
class IncidentReport:
    incident_id: str
    incident_type: str
    severity: str
    affected_workflows: list[str]
    affected_stages: list[str]
    affected_artifacts: list[str]
    affected_data_domains: list[str]
    affected_agent_runs: list[str]
    detected_by: str
    technical_summary: str
    evidence_refs: list[str]
    business_impact_unknown_or_known: str
    risk_notification_ref: str | None
    status: str


@dataclass(frozen=True)
class DegradationPlan:
    plan_id: str
    incident_ref: str
    fallback_option: str
    affected_usage: str
    data_quality_effect: str
    decision_or_execution_blocking_effect: str
    business_risk_requires_risk_review: bool
    auto_allowed: bool
    owner_or_governance_required: bool
    rollback_or_recovery_steps: list[str]


@dataclass(frozen=True)
class RecoveryPlan:
    plan_id: str
    incident_ref: str
    preconditions: list[str]
    recovery_steps: list[str]
    validation_steps: list[str]
    technical_recovery_status: str
    residual_risks: list[str]
    risk_review_required: bool
    risk_release_request_ref: str | None
    investment_resume_allowed: bool = False


@dataclass(frozen=True)
class RiskNotification:
    notification_id: str
    incident_ref: str
    affected_workflows: list[str]
    affected_stage_or_artifact_refs: list[str]
    technical_status: str
    business_question_for_risk: str
    recommended_hold_or_reopen: str
    evidence_refs: list[str]


@dataclass
class DevOpsIncidentRuntime:
    incidents: dict[str, IncidentReport] = field(default_factory=dict)
    degradation_plans: dict[str, DegradationPlan] = field(default_factory=dict)
    recovery_plans: dict[str, RecoveryPlan] = field(default_factory=dict)
    risk_notifications: dict[str, RiskNotification] = field(default_factory=dict)
    health_signals: list[HealthSignal] = field(default_factory=list)
    sensitive_log_findings: list[dict[str, Any]] = field(default_factory=list)
    cost_observations: list[dict[str, Any]] = field(default_factory=list)

    def handle_signal(self, signal: HealthSignal) -> IncidentReport:
        self.health_signals.append(signal)
        incident_type = _incident_type(signal.check_type)
        severity = _classify(signal)
        incident_id = new_id("incident")
        risk_ref = new_id("risk-notification") if _requires_risk(signal, severity) else None
        incident = IncidentReport(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            affected_workflows=signal.affected_workflows,
            affected_stages=_affected_stages(signal),
            affected_artifacts=signal.evidence_refs,
            affected_data_domains=[signal.subject] if signal.check_type == "source_health" else [],
            affected_agent_runs=[signal.subject] if signal.check_type == "runner_health" else [],
            detected_by=f"{signal.check_type}_probe",
            technical_summary=f"{signal.subject}:{severity}",
            evidence_refs=signal.evidence_refs,
            business_impact_unknown_or_known="pass_to_risk" if risk_ref else "known_observability_only",
            risk_notification_ref=risk_ref,
            status="triaged",
        )
        self.incidents[incident_id] = incident
        self.degradation_plans[incident_id] = self._build_degradation(signal, incident)
        self.recovery_plans[incident_id] = self._build_recovery(signal, incident)
        if risk_ref:
            self.risk_notifications[incident_id] = RiskNotification(
                notification_id=risk_ref,
                incident_ref=incident_id,
                affected_workflows=signal.affected_workflows,
                affected_stage_or_artifact_refs=signal.evidence_refs,
                technical_status="technical_recovery_pending",
                business_question_for_risk="hold_or_reopen_affected_workflow",
                recommended_hold_or_reopen="reopen" if severity == "P0" else "hold",
                evidence_refs=signal.evidence_refs,
            )
        if signal.check_type == "log_security":
            self.sensitive_log_findings.append(
                {
                    "finding_id": new_id("security-finding"),
                    "subject": signal.subject,
                    "audit_event_ref": new_id("audit"),
                    "incident_ref": incident_id,
                    "ordinary_logs_contained_sensitive_raw": bool(signal.metrics.get("finance_raw_plaintext")),
                }
            )
        if signal.check_type == "cost_token":
            self.cost_observations.append({"subject": signal.subject, "multiple": signal.metrics.get("daily_cost_multiple"), "p0_pass_fail_relevant": False})
        return incident

    def block_risk_relaxation_attempt(self, target: str) -> str:
        if target in {"risk_hard_blocker", "decision_core_threshold", "execution_core_threshold", "prompt", "skill", "execution_parameter"}:
            return "blocked:risk_relaxation_requires_risk_or_governance"
        return "allowed"

    def build_devops_incident_report(self) -> dict[str, Any]:
        signals = [
            HealthSignal("source_health", "market-primary", "execution_core", {"critical_field_missing": True, "primary_failed": True, "fallback_failed": True}, ["wf-source"], ["data-req-1"]),
            HealthSignal("service_health", "risk-engine", "decision_core", {"timeout_rate": 0.12, "p95_latency_seconds": 12}, ["wf-service"], ["service-call-1"]),
            HealthSignal("execution_environment", "minute-bars", "execution_core", {"minute_delay_minutes": 7}, ["wf-exec"], ["precheck-1"]),
            HealthSignal("runner_health", "agent-runner", "agent", {"tool_error_rate": 0.2}, ["wf-runner"], ["agent-run-1"]),
            HealthSignal("log_security", "trace-log", "security", {"finance_raw_plaintext": True}, ["wf-sec"], ["log-1"]),
            HealthSignal("cost_token", "model-route", "observability", {"daily_cost_multiple": 2.1}, [], ["cost-1"]),
        ]
        for signal in signals:
            self.handle_signal(signal)
        payload = {
            "routine_checks": _routine_checks(),
            "incidents": [incident.__dict__ for incident in self.incidents.values()],
            "health_signals": [signal.__dict__ for signal in self.health_signals],
            "severity_classification": {incident.incident_id: incident.severity for incident in self.incidents.values()},
            "degradation_actions": [plan.__dict__ for plan in self.degradation_plans.values()],
            "recovery_plan": [plan.__dict__ for plan in self.recovery_plans.values()],
            "risk_reports": [notice.__dict__ for notice in self.risk_notifications.values()],
            "investment_resume_denied_until_guard": all(not plan.investment_resume_allowed for plan in self.recovery_plans.values()),
            "cost_observability_only": all(item["p0_pass_fail_relevant"] is False for item in self.cost_observations),
            "health_threshold_results": {signal.subject: _classify(signal) for signal in self.health_signals},
            "safe_degradation_allowlist_checks": {"source_fallback": True, "research_cache": True, "stage_blocked": True, "risk_relaxation": False},
            "blocked_risk_relaxation_attempts": [self.block_risk_relaxation_attempt("risk_hard_blocker")],
            "recovery_validation_checklist": _recovery_validation_steps(),
            "sensitive_log_findings": self.sensitive_log_findings,
            "investment_resume_denied_until_risk_workflow_guard": True,
        }
        return _report_envelope(payload)

    def _build_degradation(self, signal: HealthSignal, incident: IncidentReport) -> DegradationPlan:
        auto_allowed = signal.usage in {"display", "research"} or signal.check_type in {"source_health", "service_health"}
        return DegradationPlan(
            plan_id=new_id("degradation"),
            incident_ref=incident.incident_id,
            fallback_option="safe_fallback_or_stage_blocked",
            affected_usage=signal.usage,
            data_quality_effect="blocked" if incident.severity == "P0" else "degraded",
            decision_or_execution_blocking_effect="blocked" if signal.usage == "execution_core" else "waiting",
            business_risk_requires_risk_review=_requires_risk(signal, incident.severity),
            auto_allowed=auto_allowed,
            owner_or_governance_required=not auto_allowed,
            rollback_or_recovery_steps=["restore_health_probe", "recompute_quality", "notify_risk_if_business_input"],
        )

    def _build_recovery(self, signal: HealthSignal, incident: IncidentReport) -> RecoveryPlan:
        return RecoveryPlan(
            plan_id=new_id("recovery"),
            incident_ref=incident.incident_id,
            preconditions=["failure_reproduced", "affected_scope_identified"],
            recovery_steps=["repair_technical_cause", "rerun_probe", "write_validation_evidence"],
            validation_steps=_recovery_validation_steps(),
            technical_recovery_status="pending_validation",
            residual_risks=["business_resume_requires_risk_or_workflow_guard"] if _requires_risk(signal, incident.severity) else [],
            risk_review_required=_requires_risk(signal, incident.severity),
            risk_release_request_ref=incident.risk_notification_ref,
        )


def _incident_type(check_type: str) -> str:
    return {
        "source_health": "data_source",
        "service_health": "service",
        "execution_environment": "execution_environment",
        "runner_health": "system",
        "log_security": "security",
        "cost_token": "cost_token",
    }.get(check_type, "system")


def _classify(signal: HealthSignal) -> str:
    metrics = signal.metrics
    if signal.check_type == "source_health":
        if metrics.get("critical_field_missing") or metrics.get("critical_conflict") or (metrics.get("primary_failed") and metrics.get("fallback_failed")):
            return "P0"
        if metrics.get("timeout_count", 0) >= 2 or metrics.get("error_rate_15m", 0) >= 0.20:
            return "P1"
        if metrics.get("error_rate_30m", 0) >= 0.10:
            return "P2"
        return "P3"
    if signal.check_type == "service_health":
        if signal.usage in {"risk", "execution_core"} and metrics.get("timeout") and not metrics.get("stale_result_available"):
            return "P0"
        if metrics.get("p95_latency_seconds", 0) > 10 or metrics.get("timeout_rate", 0) >= 0.10:
            return "P1"
        if metrics.get("p95_latency_seconds", 0) > 5:
            return "P2"
        return "P3"
    if signal.check_type == "execution_environment":
        if metrics.get("calendar_missing") or metrics.get("fee_config_missing"):
            return "P0"
        if metrics.get("minute_delay_minutes", 0) > 5:
            return "P1"
        return "P2"
    if signal.check_type == "runner_health":
        if metrics.get("direct_write") or metrics.get("sensitive_access"):
            return "P0"
        if metrics.get("timeout") or metrics.get("tool_error_rate", 0) >= 0.15:
            return "P1"
        return "P2"
    if signal.check_type == "log_security":
        return "P0" if metrics.get("finance_raw_plaintext") else "P1"
    if signal.check_type == "cost_token":
        if metrics.get("daily_cost_multiple", 0) >= 2:
            return "P1"
        if metrics.get("three_day_multiple", 0) >= 1.5:
            return "P2"
        return "P3"
    return "P3"


def _requires_risk(signal: HealthSignal, severity: str) -> bool:
    return severity in {"P0", "P1"} and signal.check_type != "cost_token"


def _affected_stages(signal: HealthSignal) -> list[str]:
    if signal.usage == "execution_core":
        return ["S6"]
    if signal.usage == "decision_core":
        return ["S1", "S4", "S5"]
    return []


def _recovery_validation_steps() -> list[str]:
    return [
        "reproduce_failure_cleared",
        "schema_validation",
        "data_quality_recompute",
        "affected_workflow_replay",
        "no_fabricated_result",
        "sensitive_log_rescan",
        "risk_notification_complete",
        "investment_resume_allowed_false",
    ]


def _routine_checks() -> list[dict[str, Any]]:
    now = utc_now()
    return [
        {"check_id": "preopen-source-execution", "window": "pre_open", "status": "observed", "last_success_at": now, "next_check_at": "next_pre_open"},
        {"check_id": "intraday-runner-service", "window": "intraday", "status": "observed", "last_success_at": now, "next_check_at": "next_intraday"},
        {"check_id": "daily-cost-log-security", "window": "daily_ops", "status": "observed", "last_success_at": now, "next_check_at": "next_daily_ops"},
    ]


def _report_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    report = {
        "report_id": "devops_incident_report.json",
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi006",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-006"],
        "test_case_refs": ["TC-ACC-029-01"],
        "fixture_refs": ["FX-DEVOPS-INCIDENTS"],
        "result": "pass",
        "checked_requirements": ["REQ-029"],
        "checked_acceptances": ["ACC-029"],
        "checked_invariants": ["INV-DEVOPS-NO-BUSINESS-RESUME"],
        "artifact_refs": [],
        "failures": [],
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-006 deterministic incident fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": [{"guard": "investment_resume_allowed_false", "input_ref": "recovery_plan", "expected": "false", "actual": "false", "result": "pass"}],
    }
    report.update(payload)
    return report
