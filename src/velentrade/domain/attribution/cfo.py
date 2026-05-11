from __future__ import annotations

from dataclasses import dataclass

from velentrade.domain.attribution.service import AttributionReport
from velentrade.domain.common import new_id
from velentrade.domain.governance.runtime import GovernanceChange, GovernanceRuntime


TRIGGER_PRIORITY = [
    "hard_blocker_hit",
    "single_dimension_low",
    "rolling_drop",
    "repeated_degradation",
    "condition_failure",
    "periodic_window",
]


@dataclass(frozen=True)
class CFOInterpretation:
    interpretation_id: str
    attribution_ref: str
    period: str
    summary_for_owner: str
    market_vs_decision_vs_execution: dict[str, float | None]
    finance_context_used: str
    sensitive_data_redaction_summary: str
    recommended_followups: list[str]


@dataclass(frozen=True)
class GovernanceProposal:
    proposal_id: str
    proposal_type: str
    impact_level: str
    problem_statement: str
    proposed_change: str
    comparison_analysis: str
    validation_result_refs: list[str]
    effective_scope: str
    rollback_plan: str
    owner_approval_ref: str | None = None


@dataclass(frozen=True)
class ReflectionAssignment:
    assignment_id: str
    trigger_ref: str
    responsible_agent_id: str
    classification: str
    questions_to_answer: list[str]
    due_policy: str
    semantic_lead_agent_id: str = "cfo"
    process_authority: str = "reflection_workflow"
    status: str = "assigned"


@dataclass(frozen=True)
class CFOGovernanceResult:
    trigger: str
    interpretation: CFOInterpretation
    governance_proposal: GovernanceProposal
    assignment: ReflectionAssignment
    governance_change: GovernanceChange
    owner_approval_required: bool


class CFOGovernanceService:
    def interpret(self, attribution: AttributionReport, governance_subtype: str, impact_level: str) -> CFOGovernanceResult:
        trigger = next((item for item in TRIGGER_PRIORITY if item in attribution.trigger_candidates), "periodic_window")
        assignment = _assignment_for_trigger(trigger, attribution.report_id)
        interpretation = CFOInterpretation(
            interpretation_id=new_id("cfo-interpretation"),
            attribution_ref=attribution.report_id,
            period=attribution.period,
            summary_for_owner="归因已按市场、决策、执行、风险、数据和证据拆分。",
            market_vs_decision_vs_execution={
                "decision_quality": attribution.decision_quality,
                "execution_quality": attribution.execution_quality,
                "risk_quality": attribution.risk_quality,
            },
            finance_context_used="authorized_or_redacted",
            sensitive_data_redaction_summary="非 CFO 角色只使用脱敏财务摘要。",
            recommended_followups=[trigger],
        )
        proposal = GovernanceProposal(
            proposal_id=new_id("governance-proposal"),
            proposal_type=governance_subtype,
            impact_level=impact_level,
            problem_statement=f"{trigger} requires governed change",
            proposed_change=f"update {governance_subtype} for new tasks only",
            comparison_analysis="current_vs_proposed",
            validation_result_refs=["schema", "fixture", "scope", "rollback", "snapshot"],
            effective_scope="new_task",
            rollback_plan="rollback-to-current-context",
        )
        runtime = GovernanceRuntime()
        runtime.create_context_snapshot("ctx-cfo-base", "baseline", {"cfo": "prompt-v1"}, {"cfo": "skill-v1"}, [], [], [], {"cfo": "profile-v1"}, "new_task")
        change = runtime.submit_change(
            change_id=new_id("chg"),
            change_type=governance_subtype if governance_subtype in {"prompt", "skill_package", "default_context", "risk_parameter", "execution_parameter"} else "risk_parameter",
            impact_level=impact_level,
            proposal_ref=proposal.proposal_id,
            target_version_refs={"risk_parameter_versions": ["risk-budget-v2"]},
            effective_scope="new_task",
            rollback_plan_ref=proposal.rollback_plan,
        )
        runtime.triage(change.change_id)
        assessed = runtime.assess(change.change_id, proposal.validation_result_refs)
        return CFOGovernanceResult(trigger, interpretation, proposal, assignment, assessed, assessed.state == "owner_pending")


def _assignment_for_trigger(trigger: str, attribution_ref: str) -> ReflectionAssignment:
    if trigger == "hard_blocker_hit":
        classification, responsible = "data_quality_problem", "devops_engineer"
    elif trigger in {"single_dimension_low", "condition_failure"}:
        classification, responsible = "decision_error", "cio"
    elif trigger == "rolling_drop":
        classification, responsible = "methodology_decay", "researcher"
    else:
        classification, responsible = "methodology_decay", "researcher"
    return ReflectionAssignment(
        assignment_id=new_id("reflection-assignment"),
        trigger_ref=attribution_ref,
        responsible_agent_id=responsible,
        classification=classification,
        questions_to_answer=[
            "原判断是什么，引用了哪些正式 artifact？",
            "关键证据、反证或失效条件是否被正确使用？",
            "下次新任务或新 attempt 应如何收紧口径？",
        ],
        due_policy="next_review_window",
    )
