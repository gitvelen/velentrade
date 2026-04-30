from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import new_id, utc_now


@dataclass
class ObservabilityCollector:
    metric_events: list[dict[str, Any]] = field(default_factory=list)
    sensitive_denials: list[dict[str, str]] = field(default_factory=list)
    metrics: dict[str, int] = field(
        default_factory=lambda: {
            "workflow_stage_duration_seconds": 0,
            "agent_run_duration_seconds": 0,
            "collaboration_command_accepted_total": 0,
            "collaboration_command_rejected_total": 0,
            "data_quality_score_distribution": 0,
            "execution_core_block_total": 0,
            "model_token_total": 0,
            "cost_estimate_total": 0,
            "runner_write_denial_total": 0,
            "sensitive_field_access_denial_total": 0,
            "incident_open_total": 0,
        }
    )

    def record_metric(self, metric_name: str, payload: dict[str, Any]) -> None:
        self.metric_events.append({"metric_name": metric_name, "payload": payload, "recorded_at": utc_now()})
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1
        if metric_name == "model_token_total":
            self.metrics["cost_estimate_total"] += 1

    def record_sensitive_denial(self, agent_id: str, field: str) -> None:
        self.sensitive_denials.append({"agent_id": agent_id, "field": field, "audit_event_ref": new_id("audit")})
        self.metrics["sensitive_field_access_denial_total"] += 1

    def devops_health_read_model(self) -> dict[str, Any]:
        now = utc_now()
        runner_incident = next((event for event in self.metric_events if event["metric_name"] == "agent_run_duration_seconds" and event["payload"].get("status") == "timed_out"), None)
        return {
            "routine_checks": [
                {"check_id": "metric-collection", "window": "intraday", "status": "observed", "last_success_at": now, "next_check_at": "next_probe"}
            ],
            "incidents": [
                {
                    "incident_id": new_id("incident"),
                    "severity": "P1",
                    "incident_type": "runner",
                    "affected_workflows": ["wf-1"],
                    "status": "triaged",
                    "risk_notification_ref": new_id("risk-notification"),
                }
            ] if runner_incident else [],
            "recovery": [
                {
                    "plan_id": new_id("recovery"),
                    "technical_recovery_status": "pending_validation",
                    "risk_review_required": True,
                    "investment_resume_allowed": False,
                }
            ],
            "audit_trail": self.sensitive_denials,
            "metrics": dict(self.metrics),
        }
