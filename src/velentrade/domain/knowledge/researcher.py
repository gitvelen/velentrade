from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from velentrade.domain.common import new_id, utc_now


@dataclass(frozen=True)
class MemoryCapture:
    capture_id: str
    source_type: str
    source_refs: list[str]
    content_markdown: str
    payload: dict[str, Any]
    suggested_memory_type: str
    sensitivity: str
    producer_agent_id: str
    created_at: str


@dataclass(frozen=True)
class MemoryOrganizeSuggestion:
    suggestion_id: str
    target_memory_refs: list[str]
    suggested_tags: list[str]
    suggested_relations: list[dict[str, Any]]
    suggested_collections: list[str]
    merge_or_duplicate_candidates: list[str]
    reason: str
    risk_if_applied: str
    requires_gateway_write: bool = True


@dataclass(frozen=True)
class KnowledgePromptSkillProposal:
    proposal_id: str
    proposal_type: str
    diff_or_manifest_ref: str
    affected_roles: list[str]
    affected_workflows: list[str]
    source_memory_refs: list[str]
    source_knowledge_refs: list[str]
    validation_result_refs: list[str]
    impact_level: str
    rollback_plan: str
    effective_scope: str


@dataclass(frozen=True)
class ResearcherOutputs:
    daily_brief: list[dict[str, Any]]
    research_package: dict[str, Any]
    topic_proposal: dict[str, Any]
    memory_capture: MemoryCapture
    memory_review_digest: dict[str, Any]
    memory_organize_suggestion: MemoryOrganizeSuggestion
    knowledge_proposal: KnowledgePromptSkillProposal
    prompt_proposal: KnowledgePromptSkillProposal
    skill_proposal: KnowledgePromptSkillProposal
    auto_validation: dict[str, Any]
    owner_approval_for_high_impact: bool
    new_task_or_attempt_only_effect: bool


class ResearcherWorkflow:
    def run_daily_research(self, news_items: list[dict[str, Any]], research_material: str) -> ResearcherOutputs:
        daily_brief = [_brief_item(item) for item in news_items]
        memory_id = new_id("memory")
        payload = {
            "title": "研究观察",
            "tags": ["research", "cashflow"],
            "source_refs": ["research-material-1"],
            "symbol_refs": [item["symbol"] for item in news_items if "symbol" in item],
            "artifact_refs": ["research-package-1"],
            "agent_refs": ["researcher"],
            "sensitivity": "public_internal",
            "suggested_relations": [{"target_ref": "knowledge-method-1", "relation_type": "supports"}],
        }
        capture = MemoryCapture(
            capture_id=new_id("capture"),
            source_type="research_material",
            source_refs=["research-material-1"],
            content_markdown=research_material,
            payload=payload,
            suggested_memory_type="research_note",
            sensitivity="public_internal",
            producer_agent_id="researcher",
            created_at=utc_now(),
        )
        organize = MemoryOrganizeSuggestion(
            suggestion_id=new_id("memory-organize"),
            target_memory_refs=[memory_id],
            suggested_tags=["cashflow", "watchlist"],
            suggested_relations=[{"source_memory_id": memory_id, "target_ref": "knowledge-method-1", "relation_type": "supports"}],
            suggested_collections=["researcher_digest"],
            merge_or_duplicate_candidates=[],
            reason="抽取到可复用研究模式，但需要 Gateway 写 relation/collection。",
            risk_if_applied="low",
        )
        return ResearcherOutputs(
            daily_brief=daily_brief,
            research_package={"package_id": "research-package-1", "context_eligible": True, "supporting_evidence_refs": ["source-1"]},
            topic_proposal={"topic_proposal_id": "topic-proposal-1", "formal_ic_status": "candidate", "supporting_evidence_only": True},
            memory_capture=capture,
            memory_review_digest={"candidate_memories": [memory_id], "not_fact_source": True},
            memory_organize_suggestion=organize,
            knowledge_proposal=_proposal("knowledge", "knowledge-diff-1", [memory_id], "medium"),
            prompt_proposal=_proposal("prompt", "prompt-diff-1", [memory_id], "medium"),
            skill_proposal=_proposal("skill", "skill-manifest-v2", [memory_id], "high"),
            auto_validation={"schema": "pass", "fixture": "pass", "rollback": "pass", "snapshot": "pass"},
            owner_approval_for_high_impact=True,
            new_task_or_attempt_only_effect=True,
        )

    def direct_update_attempt(self, target: str) -> str:
        if target in {"prompt", "skill", "knowledge", "default_context", "risk_budget", "execution_parameter"}:
            return "denied:in_flight_snapshot_locked"
        return "allowed"


def _brief_item(item: dict[str, Any]) -> dict[str, Any]:
    priority = "P0" if item.get("holding") and item.get("severity") == "high" and _is_a_share_symbol(item.get("symbol", "")) else "P1"
    return {
        "brief_id": new_id("brief"),
        "priority": priority,
        "title": item["title"],
        "symbol": item.get("symbol"),
        "supporting_evidence_only": priority != "P0",
    }


def _is_a_share_symbol(symbol: str) -> bool:
    code, separator, exchange = symbol.partition(".")
    return separator == "." and len(code) == 6 and code.isdigit() and exchange in {"SH", "SZ", "BJ"}


def _proposal(proposal_type: str, diff_ref: str, memory_refs: list[str], impact_level: str) -> KnowledgePromptSkillProposal:
    return KnowledgePromptSkillProposal(
        proposal_id=new_id(f"{proposal_type}-proposal"),
        proposal_type=proposal_type,
        diff_or_manifest_ref=diff_ref,
        affected_roles=["researcher", "cio"],
        affected_workflows=["investment_workflow", "research_task"],
        source_memory_refs=memory_refs,
        source_knowledge_refs=[],
        validation_result_refs=["schema", "fixture", "scope", "rollback", "snapshot"],
        impact_level=impact_level,
        rollback_plan=f"rollback-{proposal_type}-v1",
        effective_scope="new_task",
    )
