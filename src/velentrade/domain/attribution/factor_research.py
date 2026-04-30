from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FactorResearchResult:
    hypothesis: str
    sample_scope: dict[str, Any]
    independent_validation: dict[str, Any]
    registry_entry: dict[str, Any]
    monitoring_rule: dict[str, Any]
    monitoring_alerts: list[str]
    invalidation_diagnosis: dict[str, Any]
    governance_proposal: dict[str, Any]
    no_backtest_dependency: bool = True


class FactorResearchService:
    def admit_factor(
        self,
        factor_id: str,
        hypothesis: str,
        sample_scope: dict[str, Any],
        independent_validation: dict[str, Any],
        monitoring: dict[str, Any],
        affects_default_weight: bool,
    ) -> FactorResearchResult:
        validation_pass = independent_validation.get("leakage_check") == "pass" and independent_validation.get("direction_consistency") == "pass"
        alerts = []
        if monitoring.get("coverage", 1) < 0.80:
            alerts.append("coverage_below_threshold")
        if monitoring.get("data_quality", 1) < 0.85:
            alerts.append("data_quality_below_threshold")
        if monitoring.get("direction_failures", 0) >= 5:
            alerts.append("direction_consistency_failed")
        registry_entry = {
            "factor_id": factor_id,
            "version": "v1",
            "owner": "researcher",
            "formula_ref": f"formula-{factor_id}",
            "input_fields": ["price", "volume", "market_state"],
            "market_state_scope": sample_scope.get("applicable_market_state", []),
            "risk_notes": "not a standalone investment decision",
            "validation_refs": ["independent-validation-v1"],
            "monitoring_rule_ref": f"monitoring-{factor_id}",
            "rollback_ref": f"rollback-{factor_id}",
            "status": "validated" if validation_pass else "candidate",
        }
        governance = {
            "proposal_type": "factor_weight",
            "impact_level": "high" if affects_default_weight else "medium",
            "effective_scope": "new_task",
        }
        return FactorResearchResult(
            hypothesis=hypothesis,
            sample_scope=sample_scope,
            independent_validation=independent_validation,
            registry_entry=registry_entry,
            monitoring_rule={"coverage_min": 0.80, "data_quality_min": 0.85, "direction_failure_windows": 5},
            monitoring_alerts=alerts,
            invalidation_diagnosis={"alerts": alerts, "pause_default_weight": affects_default_weight and bool(alerts), "effective_scope": "new_task"},
            governance_proposal=governance,
        )
