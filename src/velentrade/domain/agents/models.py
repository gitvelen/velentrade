from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthorityPolicy:
    decision_rights: list[str] = field(default_factory=list)
    proposal_rights: list[str] = field(default_factory=list)
    veto_or_blocking_rights: list[str] = field(default_factory=list)
    semantic_lead_domains: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ContextPolicy:
    always_include: list[str] = field(default_factory=list)
    stage_scoped: list[str] = field(default_factory=list)
    on_demand_retrieval: list[str] = field(default_factory=list)
    denied: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolPolicy:
    db_read_views: list[str] = field(default_factory=list)
    file_scopes: list[str] = field(default_factory=list)
    network_policy: list[str] = field(default_factory=list)
    terminal_policy: list[str] = field(default_factory=list)
    service_result_read: list[str] = field(default_factory=list)
    skill_packages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WritePolicy:
    artifact_types: list[str] = field(default_factory=list)
    command_types: list[str] = field(default_factory=list)
    comment_types: list[str] = field(default_factory=list)
    proposal_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OutputContract:
    artifact_type: str
    schema_ref: str
    role_payload_schema: str = "generic_payload"


@dataclass(frozen=True)
class FailurePolicy:
    code: str
    handling: str


@dataclass(frozen=True)
class EscalationPolicy:
    condition: str
    command_or_target: str


@dataclass(frozen=True)
class EvaluationPolicy:
    metrics: list[str]
    feedback_sources: list[str]


@dataclass(frozen=True)
class CapabilityProfile:
    agent_id: str
    display_name: str
    role: str
    profile_version: str
    status: str
    mission: str
    authority: AuthorityPolicy
    default_context_policy: ContextPolicy
    tool_policy: ToolPolicy
    write_policy: WritePolicy
    output_contracts: list[OutputContract]
    sop: list[str]
    failure_policy: list[FailurePolicy]
    escalation_policy: list[EscalationPolicy]
    evaluation_policy: EvaluationPolicy
    default_model_profile: str
    default_tool_profile_id: str
    default_skill_packages: list[str]
