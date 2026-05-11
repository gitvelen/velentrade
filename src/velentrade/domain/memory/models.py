from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from velentrade.domain.common import utc_now


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
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    memory_type: str
    owner_role: str
    producer_agent_id: str
    status: str
    current_version_id: str
    source_refs: list[str]
    sensitivity: str
    pinned: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class MemoryVersion:
    version_id: str
    memory_id: str
    version_no: int
    content_markdown: str
    payload: dict[str, Any]
    created_by: str
    created_at: str
    content_hash: str
    superseded_by_version_id: str | None = None


@dataclass(frozen=True)
class MemoryExtractionResult:
    extraction_id: str
    memory_version_id: str
    extractor_version: str
    title: str
    tags: list[str]
    mentions: list[str]
    has_link: bool
    has_task_list: bool
    has_code: bool
    has_incomplete_tasks: bool
    symbol_refs: list[str]
    artifact_refs: list[str]
    agent_refs: list[str]
    stage_refs: list[str]
    source_refs: list[str]
    sensitivity: str
    status: str
    created_at: str


@dataclass(frozen=True)
class MemoryRelation:
    relation_id: str
    source_memory_id: str
    target_ref: str
    relation_type: str
    reason: str
    evidence_refs: list[str]
    created_by: str
    created_at: str


@dataclass(frozen=True)
class ContextSlice:
    context_slice_id: str
    context_snapshot_id: str
    agent_id: str
    profile_version: str
    artifact_refs_injected: list[str]
    memory_refs_injected: list[str]
    denied_memory_refs: list[str]
    retrieval_query_summary: str
    redaction_policy_applied: str
    fenced_background: bool = True
