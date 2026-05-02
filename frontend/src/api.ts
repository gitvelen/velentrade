import {
  AgentProfileReadModel,
  CapabilityConfigReadModel,
  KnowledgeReadModel,
  TeamReadModel,
  TraceDebugReadModel,
  buildKnowledgeReadModel,
  buildTeamReadModel,
  buildTraceDebugReadModel,
} from "./workbench";

type ApiEnvelope<T> = {
  data: T;
};

type ApiTeamReadModel = {
  team_health?: {
    healthy_agent_count?: number;
    active_agent_run_count?: number;
    pending_draft_count?: number;
    failed_or_denied_count?: number;
  };
  agent_cards?: Array<{
    agent_id?: string;
    display_name?: string;
    role?: string;
    profile_version?: string;
    skill_package_version?: string;
    prompt_version?: string;
    context_snapshot_version?: string;
    recent_quality_score?: number;
    failure_count?: number;
    denied_action_count?: number;
    config_draft_entry?: string;
    weakness_tags?: string[];
  }>;
};

type ApiAgentProfileReadModel = {
  agent_id?: string;
  display_name?: string;
  capability_summary?: string;
  can_do?: string[];
  cannot_do?: string[];
  quality_metrics?: {
    schema_pass_rate?: number;
    evidence_quality?: number;
  };
  denied_actions?: Array<{ reason_code?: string }>;
};

type ApiCapabilityConfigReadModel = {
  agent_id?: string;
  editable_fields?: Array<string | { field?: string }>;
  forbidden_direct_update_reason?: string;
  effective_scope_options?: string[];
};

type ApiMemoryReadModel = {
  memory_id?: string;
  title?: string;
  why_included?: string;
  current_version_id?: string;
  sensitivity?: string;
  relations?: Array<{
    target_ref?: string;
    relation_type?: string;
  }>;
};

type ApiAgentRunReadModel = {
  agent_run_id?: string;
  parent_run_id?: string | null;
  stage?: string;
  profile_version?: string;
  context_snapshot_id?: string;
};

type ApiCollaborationEventReadModel = {
  event_type?: string;
  summary?: string;
};

type ApiHandoffReadModel = {
  from_stage?: string;
  to_stage_or_agent?: string;
  blockers?: string[];
  open_questions?: string[];
};

async function fetchEnvelope<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`request failed: ${path}`);
  }
  const payload = await response.json() as ApiEnvelope<T>;
  return payload.data;
}

export async function loadTeamReadModel(): Promise<TeamReadModel> {
  const fallback = buildTeamReadModel();
  const payload = await fetchEnvelope<ApiTeamReadModel>("/api/team");

  return {
    ...fallback,
    teamHealth: {
      healthyAgentCount: payload.team_health?.healthy_agent_count ?? fallback.teamHealth.healthyAgentCount,
      activeAgentRunCount: payload.team_health?.active_agent_run_count ?? fallback.teamHealth.activeAgentRunCount,
      pendingDraftCount: payload.team_health?.pending_draft_count ?? fallback.teamHealth.pendingDraftCount,
      failedOrDeniedCount: payload.team_health?.failed_or_denied_count ?? fallback.teamHealth.failedOrDeniedCount,
    },
    agentCards: (payload.agent_cards ?? []).map((card) => ({
      agentId: card.agent_id ?? "unknown",
      displayName: card.display_name ?? "未知 Agent",
      role: card.role ?? card.agent_id ?? "unknown",
      profileVersion: card.profile_version ?? "unknown",
      skillPackageVersion: card.skill_package_version ?? "unknown",
      promptVersion: card.prompt_version ?? "unknown",
      contextSnapshotVersion: card.context_snapshot_version ?? "unknown",
      recentQualityScore: card.recent_quality_score ?? 0,
      failureCount: card.failure_count ?? 0,
      deniedActionCount: card.denied_action_count ?? 0,
      configDraftEntry: card.config_draft_entry ?? "governance_draft_only",
      weaknessTags: card.weakness_tags ?? [],
    })),
  };
}

export async function loadAgentProfileReadModel(agentId: string): Promise<AgentProfileReadModel> {
  const fallback = buildTeamReadModel().agentProfileReadModels.find((item) => item.agentId === agentId);
  const payload = await fetchEnvelope<ApiAgentProfileReadModel>(`/api/team/${agentId}`);

  return {
    agentId: payload.agent_id ?? fallback?.agentId ?? agentId,
    displayName: payload.display_name ?? fallback?.displayName ?? agentId,
    capabilitySummary: payload.capability_summary ?? fallback?.capabilitySummary ?? "",
    canDo: payload.can_do ?? fallback?.canDo ?? [],
    cannotDo: payload.cannot_do ?? fallback?.cannotDo ?? [],
    qualityMetrics: {
      schemaPassRate: payload.quality_metrics?.schema_pass_rate ?? fallback?.qualityMetrics.schemaPassRate ?? 0,
      evidenceQuality: payload.quality_metrics?.evidence_quality ?? fallback?.qualityMetrics.evidenceQuality ?? 0,
    },
    cfoAttributionRefs: fallback?.cfoAttributionRefs ?? [],
    deniedActions: (payload.denied_actions ?? []).map((item) => ({ reasonCode: item.reason_code ?? "unknown" })),
  };
}

export async function loadAgentCapabilityConfigReadModel(agentId: string): Promise<CapabilityConfigReadModel> {
  const fallback = buildTeamReadModel().capabilityConfigReadModel;
  const payload = await fetchEnvelope<ApiCapabilityConfigReadModel>(`/api/team/${agentId}/capability-config`);

  return {
    agentId: payload.agent_id ?? fallback.agentId,
    editableFields: (payload.editable_fields ?? []).map((item) => typeof item === "string" ? item : item.field ?? "unknown"),
    forbiddenDirectUpdateReason: payload.forbidden_direct_update_reason ?? fallback.forbiddenDirectUpdateReason,
    effectiveScopeOptions: payload.effective_scope_options ?? fallback.effectiveScopeOptions,
  };
}

export async function loadKnowledgeReadModel(): Promise<KnowledgeReadModel> {
  const fallback = buildKnowledgeReadModel();
  const payload = await fetchEnvelope<ApiMemoryReadModel[]>("/api/knowledge/memory-items");

  return {
    ...fallback,
    memoryCollections: payload.length
      ? payload.map((item) => ({
          collectionId: item.memory_id ?? "memory",
          title: item.title ?? "未命名记忆",
          resultCount: Math.max(item.relations?.length ?? 0, 1),
        }))
      : fallback.memoryCollections,
    memoryResults: payload.length
      ? payload.map((item) => ({
          memoryId: item.memory_id ?? "memory",
          title: item.title ?? "未命名记忆",
          relationSummary: item.relations?.[0]
            ? `${item.relations[0].relation_type ?? "related_to"} ${item.relations[0].target_ref ?? "unknown"}`
            : "无关联",
          sensitivity: item.sensitivity ?? "public_internal",
        }))
      : fallback.memoryResults,
    relationGraph: payload.flatMap((item) =>
      (item.relations ?? []).map((relation) => ({
        sourceMemoryId: item.memory_id ?? "memory",
        targetRef: relation.target_ref ?? "unknown",
        relationType: relation.relation_type ?? "related_to",
      })),
    ),
    contextInjectionInspector: payload.length
      ? payload.map((item) => ({
          contextSnapshotId: item.current_version_id ?? "ctx-api",
          whyIncluded: item.why_included ?? "fenced_background_context_only",
          redactionStatus: "applied",
        }))
      : fallback.contextInjectionInspector,
  };
}

export async function loadTraceDebugReadModel(workflowId: string): Promise<TraceDebugReadModel> {
  const fallback = buildTraceDebugReadModel();
  const [agentRuns, events, handoffs] = await Promise.all([
    fetchEnvelope<ApiAgentRunReadModel[]>(`/api/workflows/${workflowId}/agent-runs`),
    fetchEnvelope<ApiCollaborationEventReadModel[]>(`/api/workflows/${workflowId}/collaboration-events`),
    fetchEnvelope<ApiHandoffReadModel[]>(`/api/workflows/${workflowId}/handoffs`),
  ]);

  return {
    ...fallback,
    workflowId,
    agentRunTree: agentRuns.length
      ? agentRuns.map((item) => ({
          runId: item.agent_run_id ?? "run",
          parentRunId: item.parent_run_id ?? null,
          stage: item.stage ?? "unknown",
          profileVersion: item.profile_version ?? "unknown",
          contextSlice: item.context_snapshot_id ?? "ctx-api",
        }))
      : fallback.agentRunTree,
    events: events.length
      ? events.map((item) => ({
          eventType: item.event_type ?? "event",
          summary: item.summary ?? "无摘要",
        }))
      : fallback.events,
    handoffs: handoffs.length
      ? handoffs.map((item) => ({
          from: item.from_stage ?? "unknown",
          to: item.to_stage_or_agent ?? "unknown",
          blockers: item.blockers ?? [],
          openQuestions: item.open_questions ?? [],
        }))
      : fallback.handoffs,
  };
}
