from __future__ import annotations

from typing import Any


ALLOWED_MEMORY_SENSITIVITIES = {"public_internal", "finance_sensitive_raw"}
TEST_TITLES = {"test", "测试", "untitled memory"}
TEST_CONTENT = {"test", "测试"}
DEFAULT_TEST_RELATION_REASON = "Owner applied organize suggestion from Knowledge workspace"
DEFAULT_TEST_RELATION_TARGET = "knowledge-method-1"
DEFAULT_TEST_RELATION_EVIDENCE = "knowledge_memory_workspace"


def extract_memory_title(content_markdown: str) -> str:
    for line in content_markdown.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("# ").strip()
    return ""


def memory_capture_rejection_reason(
    *,
    content_markdown: str,
    source_refs: list[str],
    sensitivity: str,
) -> str | None:
    title = extract_memory_title(content_markdown)
    normalized_title = title.strip().lower()
    normalized_content = content_markdown.strip().lower()
    if not content_markdown.strip() or not title:
        return "invalid_memory_empty_content"
    if normalized_title in TEST_TITLES or normalized_content in TEST_CONTENT:
        return "invalid_memory_test_content"
    if not source_refs or any(not str(ref).strip() for ref in source_refs):
        return "invalid_memory_missing_source"
    if sensitivity not in ALLOWED_MEMORY_SENSITIVITIES:
        return "invalid_memory_sensitivity"
    return None


def relation_rejection_reason(
    *,
    target_ref: str,
    relation_type: str,
    reason: str,
    evidence_refs: list[str],
) -> str | None:
    if not target_ref.strip():
        return "invalid_memory_relation_missing_target"
    if not relation_type.strip():
        return "invalid_memory_relation_missing_type"
    if not reason.strip():
        return "invalid_memory_relation_missing_reason"
    if not evidence_refs or any(not str(ref).strip() for ref in evidence_refs):
        return "invalid_memory_relation_missing_evidence"
    if target_ref == DEFAULT_TEST_RELATION_TARGET:
        return "invalid_memory_relation_test_target"
    return None


def memory_read_model_is_garbage(item: dict[str, Any]) -> bool:
    title = str(item.get("title") or "").strip()
    summary = str(item.get("summary") or "").strip()
    sensitivity = str(item.get("sensitivity") or "")
    source_refs = item.get("source_refs") or []
    if title.lower() in TEST_TITLES:
        return True
    if summary.lower() in TEST_CONTENT:
        return True
    if sensitivity not in ALLOWED_MEMORY_SENSITIVITIES:
        return True
    if not source_refs:
        return True
    if not summary:
        return True
    return False


def relation_read_model_is_garbage(relation: dict[str, Any]) -> bool:
    target_ref = str(relation.get("target_ref") or "")
    relation_type = str(relation.get("relation_type") or "")
    reason = str(relation.get("reason") or "")
    evidence_refs = relation.get("evidence_refs") or []
    if relation_rejection_reason(
        target_ref=target_ref,
        relation_type=relation_type,
        reason=reason,
        evidence_refs=[str(ref) for ref in evidence_refs],
    ):
        return True
    return target_ref == DEFAULT_TEST_RELATION_TARGET or DEFAULT_TEST_RELATION_EVIDENCE in evidence_refs
