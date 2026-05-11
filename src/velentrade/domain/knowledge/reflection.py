from __future__ import annotations

from dataclasses import dataclass

from velentrade.domain.common import new_id


@dataclass(frozen=True)
class AgentFirstDraft:
    responsible_agent_id: str
    original_judgment_refs: list[str]
    evidence_refs: list[str]
    counter_evidence_refs: list[str]
    classification: str
    condition_findings: list[str]
    improvement_recommendation: str


@dataclass(frozen=True)
class ReflectionRecord:
    reflection_id: str
    trigger_source: str
    classification: str
    responsible_agent_id: str
    original_judgment_refs: list[str]
    memory_refs: list[str]
    knowledge_candidate_refs: list[str]
    evidence_gap: list[str]
    improvement_recommendation: str
    promotion_proposal_refs: list[str]


@dataclass(frozen=True)
class ReflectionOutcome:
    cfo_scope_confirmation: dict[str, str]
    responsible_agent_draft: AgentFirstDraft
    reflection_record: ReflectionRecord
    memory_item_ref: str
    knowledge_conflict_resolution: dict[str, str]
    knowledge_promotion_refs: list[str]
    researcher_promotion: dict[str, str]
    auto_validation_or_owner_approval: str
    new_task_or_attempt_only_effect: bool
    no_hot_patch_guard: dict[str, str]


class ReflectionLearningWorkflow:
    def execute(self, assignment_ref: str, trigger_source: str, draft: AgentFirstDraft, impact_level: str) -> ReflectionOutcome:
        memory_ref = new_id("memory")
        proposal_ref = new_id("knowledge-proposal")
        record = ReflectionRecord(
            reflection_id=new_id("reflection"),
            trigger_source=trigger_source,
            classification=draft.classification,
            responsible_agent_id=draft.responsible_agent_id,
            original_judgment_refs=draft.original_judgment_refs,
            memory_refs=[memory_ref],
            knowledge_candidate_refs=[new_id("candidate-knowledge")],
            evidence_gap=draft.counter_evidence_refs,
            improvement_recommendation=draft.improvement_recommendation,
            promotion_proposal_refs=[proposal_ref],
        )
        approval_mode = "owner_approval" if impact_level == "high" else "auto_validation"
        return ReflectionOutcome(
            cfo_scope_confirmation={"assignment_ref": assignment_ref, "trigger_source": trigger_source, "scope": "confirmed"},
            responsible_agent_draft=draft,
            reflection_record=record,
            memory_item_ref=memory_ref,
            knowledge_conflict_resolution={
                "fact_conflict": "artifact_priority",
                "methodology_conflict": "split_applicable_scenarios",
                "memory_classification": "gateway_relation_suggestion",
                "high_impact": "governance_proposal",
            },
            knowledge_promotion_refs=[proposal_ref],
            researcher_promotion={"proposal_ref": proposal_ref, "effective_scope": "new_task"},
            auto_validation_or_owner_approval=approval_mode,
            new_task_or_attempt_only_effect=True,
            no_hot_patch_guard={"prompt": "denied", "skill": "denied", "context_snapshot": "unchanged", "parameter": "denied"},
        )
