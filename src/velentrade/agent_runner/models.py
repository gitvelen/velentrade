from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentRunStartRequest:
    agent_run_id: str
    workflow_id: str
    attempt_no: int
    stage: str
    agent_id: str
    profile_version: str
    context_snapshot_id: str
    context_slice_id: str
    tool_profile_id: str
    skill_package_versions: list[str]
    model_profile_id: str
    run_goal: str
    output_artifact_schema: str
    allowed_command_types: list[str]
    budget_tokens: int
    timeout_seconds: int


@dataclass(frozen=True)
class AgentRunResult:
    agent_run_id: str
    status: str
    artifact_payloads: list[dict[str, Any]]
    command_proposals: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    process_archive_ref: str
    tool_trace_summary_ref: str
    cost_tokens: int
    failure_code: str | None = None
    failure_reason: str | None = None
    business_fact_created: bool = False
    tool_usage_summary: dict[str, Any] = field(default_factory=dict)
