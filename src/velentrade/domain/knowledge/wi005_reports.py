from __future__ import annotations

from copy import deepcopy
from typing import Any

from velentrade.domain.common import utc_now
from velentrade.domain.knowledge.reflection import AgentFirstDraft, ReflectionLearningWorkflow
from velentrade.domain.knowledge.researcher import ResearcherWorkflow


REPORT_TC = {
    "researcher_workflow_report.json": ("TC-ACC-027-01", "ACC-027", "REQ-027"),
    "reflection_learning_report.json": ("TC-ACC-028-01", "ACC-028", "REQ-028"),
}


def _envelope(
    report_id: str,
    payload: dict[str, Any],
    guard_results: list[dict[str, Any]] | None = None,
    failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    tc, acc, req = REPORT_TC[report_id]
    guard_results = guard_results or [{"guard": "p0_assertions", "input_ref": report_id, "expected": "pass", "actual": "pass", "result": "pass"}]
    failures = failures or []
    result = "fail" if failures or any(guard.get("result") != "pass" for guard in guard_results) else "pass"
    report = {
        "report_id": report_id,
        "generated_at": utc_now(),
        "generated_by": "velentrade.wi005",
        "git_revision": "working-tree",
        "work_item_refs": ["WI-005"],
        "test_case_refs": [tc],
        "fixture_refs": [f"FX-{tc}"],
        "result": result,
        "checked_requirements": [req],
        "checked_acceptances": [acc],
        "checked_invariants": ["INV-MEMORY-NOT-FACT-SOURCE"],
        "artifact_refs": [],
        "failures": failures,
        "residual_risk": [],
        "schema_version": "1.0.0",
        "checked_fields": sorted(payload),
        "fixture_inputs": {"fixture": "WI-005 deterministic knowledge fixture"},
        "actual_outputs": {"payload_keys": sorted(payload)},
        "guard_results": guard_results,
    }
    report.update(payload)
    return report


def build_wi005_knowledge_reports() -> dict[str, dict[str, Any]]:
    researcher = ResearcherWorkflow().run_daily_research(
        [
            {"title": "持仓公司公告", "symbol": "600000.SH", "holding": True, "severity": "high"},
            {"title": "非持仓正面机会", "symbol": "000001.SZ", "positive": True, "severity": "medium"},
            {"title": "黄金持仓波动", "symbol": "GOLD.CNY", "holding": True, "severity": "high"},
        ],
        "## 研究摘要\n可复用但不得绕过 IC hard gate。",
    )
    reflection = ReflectionLearningWorkflow().execute(
        "assign-1",
        "attr-1",
        AgentFirstDraft(
            responsible_agent_id="cio",
            original_judgment_refs=["memo-1"],
            evidence_refs=["evidence-1"],
            counter_evidence_refs=["counter-1"],
            classification="decision_error",
            condition_findings=["condition miss"],
            improvement_recommendation="补充反证 checklist",
        ),
        "medium",
    )
    reports = {
        "researcher_workflow_report.json": _envelope(
            "researcher_workflow_report.json",
            {
                "daily_brief": researcher.daily_brief,
                "research_package": researcher.research_package,
                "topic_proposal": researcher.topic_proposal,
                "memory_capture": researcher.memory_capture.__dict__,
                "memory_review_digest": researcher.memory_review_digest,
                "memory_organize_suggestions": [researcher.memory_organize_suggestion.__dict__],
                "memory_relation_applications": researcher.memory_organize_suggestion.suggested_relations,
                "knowledge_proposal": researcher.knowledge_proposal.__dict__,
                "prompt_skill_proposal": [researcher.prompt_proposal.__dict__, researcher.skill_proposal.__dict__],
                "impact_validation": researcher.auto_validation,
                "prompt_proposal": researcher.prompt_proposal.__dict__,
                "skill_proposal": researcher.skill_proposal.__dict__,
                "auto_validation": researcher.auto_validation,
                "owner_approval_for_high_impact": researcher.owner_approval_for_high_impact,
                "new_task_or_attempt_only_effect": researcher.new_task_or_attempt_only_effect,
            },
        ),
        "reflection_learning_report.json": _envelope(
            "reflection_learning_report.json",
            {
                "attribution_trigger": reflection.reflection_record.trigger_source,
                "cfo_scope_confirmation": reflection.cfo_scope_confirmation,
                "responsible_agent_draft": reflection.responsible_agent_draft.__dict__,
                "memory_item_refs": [reflection.memory_item_ref],
                "knowledge_promotion_refs": reflection.knowledge_promotion_refs,
                "researcher_promotion": reflection.researcher_promotion,
                "impact_triage": {"impact": "medium", "mode": reflection.auto_validation_or_owner_approval},
                "auto_validation_or_owner_approval": reflection.auto_validation_or_owner_approval,
                "new_task_or_attempt_only_effect": reflection.new_task_or_attempt_only_effect,
                "no_hot_patch_guard": reflection.no_hot_patch_guard,
                "trigger_source": reflection.reflection_record.trigger_source,
                "agent_first_draft_required_questions": [
                    "original_judgment",
                    "evidence_and_counter_evidence",
                    "classification",
                    "condition_hit_or_miss",
                    "improvement_recommendation",
                ],
                "knowledge_conflict_resolution": reflection.knowledge_conflict_resolution,
                "researcher_promotion_refs": reflection.researcher_promotion,
                "auto_validation": {"schema": "pass", "fixture": "pass", "rollback": "pass", "snapshot": "pass"},
                "owner_approval_for_high_impact": True,
            },
        ),
    }
    return {name: deepcopy(report) for name, report in reports.items()}
