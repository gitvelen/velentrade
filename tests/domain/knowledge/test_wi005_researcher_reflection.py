from velentrade.domain.knowledge.reflection import AgentFirstDraft, ReflectionLearningWorkflow
from velentrade.domain.knowledge.researcher import ResearcherWorkflow
from velentrade.domain.knowledge.wi005_reports import _envelope, build_wi005_knowledge_reports


def test_researcher_capture_organize_and_proposals_are_gateway_bound():
    workflow = ResearcherWorkflow()

    outputs = workflow.run_daily_research(
        news_items=[
            {"title": "持仓公司公告", "symbol": "600000.SH", "holding": True, "severity": "high"},
            {"title": "非持仓机会", "symbol": "000001.SZ", "positive": True, "severity": "medium"},
            {"title": "黄金持仓波动", "symbol": "GOLD.CNY", "holding": True, "severity": "high"},
        ],
        research_material="## 观察\n现金流改善，但证据仍需验证。",
    )

    assert outputs.daily_brief[0]["priority"] == "P0"
    assert outputs.daily_brief[1]["priority"] == "P1"
    assert outputs.daily_brief[1]["supporting_evidence_only"] is True
    assert outputs.daily_brief[2]["priority"] == "P1"
    assert outputs.daily_brief[2]["supporting_evidence_only"] is True
    assert outputs.memory_capture.payload["title"]
    assert outputs.memory_capture.payload["tags"]
    assert outputs.memory_organize_suggestion.requires_gateway_write is True
    assert outputs.knowledge_proposal.effective_scope == "new_task"
    assert outputs.prompt_proposal.rollback_plan
    assert outputs.skill_proposal.diff_or_manifest_ref.startswith("skill-manifest")
    assert workflow.direct_update_attempt("prompt") == "denied:in_flight_snapshot_locked"


def test_reflection_workflow_promotes_learning_without_hot_patch():
    workflow = ReflectionLearningWorkflow()
    outcome = workflow.execute(
        assignment_ref="assign-1",
        trigger_source="attr-1",
        draft=AgentFirstDraft(
            responsible_agent_id="cio",
            original_judgment_refs=["memo-1"],
            evidence_refs=["evidence-1"],
            counter_evidence_refs=["counter-1"],
            classification="decision_error",
            condition_findings=["invalidation hit"],
            improvement_recommendation="收紧失效条件并补充反证 checklist",
        ),
        impact_level="medium",
    )

    assert outcome.reflection_record.responsible_agent_id == "cio"
    assert outcome.memory_item_ref.startswith("memory-")
    assert outcome.knowledge_promotion_refs
    assert outcome.auto_validation_or_owner_approval == "auto_validation"
    assert outcome.new_task_or_attempt_only_effect is True
    assert outcome.no_hot_patch_guard["prompt"] == "denied"


def test_wi005_knowledge_reports_have_contract_payloads():
    reports = build_wi005_knowledge_reports()

    assert set(reports) == {"researcher_workflow_report.json", "reflection_learning_report.json"}
    assert reports["researcher_workflow_report.json"]["memory_organize_suggestions"][0]["requires_gateway_write"] is True
    assert reports["reflection_learning_report.json"]["no_hot_patch_guard"]["context_snapshot"] == "unchanged"
    for report in reports.values():
        assert report["result"] == "pass"
        assert report["work_item_refs"] == ["WI-005"]
        assert report["failures"] == []


def test_knowledge_report_fails_when_guard_or_failure_fails():
    report = _envelope(
        "reflection_learning_report.json",
        {"probe": "negative"},
        guard_results=[
            {
                "guard": "no_hot_patch",
                "input_ref": "prompt-update",
                "expected": "new_task_only",
                "actual": "in_flight_context_changed",
                "result": "fail",
            }
        ],
        failures=[{"code": "hot_patch_detected", "message": "reflection changed an in-flight ContextSnapshot"}],
    )

    assert report["result"] == "fail"
    assert report["failures"][0]["code"] == "hot_patch_detected"
