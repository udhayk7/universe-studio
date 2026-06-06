import { apiFormRequest, apiRequest } from "@/services/api/client";
import type {
  AgentTrace,
  Character,
  CharacterContextPack,
  ConsistencyDashboard,
  CreateUniversePayload,
  DemoSeedResult,
  Episode,
  EpisodeGeneratePayload,
  EpisodeScene,
  MemoryEvent,
  MemoryLocation,
  MemoryObject,
  MemoryRelationship,
  Timeline,
  TimelineBranchPayload,
  TimelineBranchResult,
  TimelineCommit,
  TimelineDiff,
  TimelineEvent,
  Universe,
  UniverseGraph,
  UniverseJob,
  UniverseMemoryOverview,
} from "@/types/universe";

export function getUniverses() {
  return apiRequest<Universe[]>("/universes");
}

export function getUniverse(id: string) {
  return apiRequest<Universe>(`/universes/${id}`);
}

export function createUniverse(payload: CreateUniversePayload) {
  return apiRequest<Universe>("/universes", {
    method: "POST",
    body: payload,
  });
}

export function createUniverseFromInput(formData: FormData) {
  return apiFormRequest<UniverseJob>("/universes/create-from-input", formData, {
    method: "POST",
  });
}

export function getJob(id: string) {
  return apiRequest<UniverseJob>(`/jobs/${id}`);
}

export function setupDemo() {
  return apiRequest<DemoSeedResult>("/demo/setup", {
    method: "POST",
    body: { reset: true, sync_neo4j: true },
  });
}

export function getJobTrace(id: string) {
  return apiRequest<AgentTrace>(`/jobs/${id}/trace`);
}

export function getCharacters(universeId: string) {
  return apiRequest<Character[]>(`/universes/${universeId}/characters`);
}

export function getCharacter(id: string) {
  return apiRequest<Character>(`/characters/${id}`);
}

export function getCharacterContextPack(id: string) {
  return apiRequest<CharacterContextPack>(`/characters/${id}/context-pack`);
}

export function getUniverseMemoryOverview(id: string) {
  return apiRequest<UniverseMemoryOverview>(`/universes/${id}/memory-overview`);
}

export function getUniverseGraph(id: string) {
  return apiRequest<UniverseGraph>(`/universes/${id}/graph`);
}

export function getUniverseEvents(id: string) {
  return apiRequest<MemoryEvent[]>(`/universes/${id}/events`);
}

export function getUniverseRelationships(id: string) {
  return apiRequest<MemoryRelationship[]>(`/universes/${id}/relationships`);
}

export function getUniverseLocations(id: string) {
  return apiRequest<MemoryLocation[]>(`/universes/${id}/locations`);
}

export function getUniverseObjects(id: string) {
  return apiRequest<MemoryObject[]>(`/universes/${id}/objects`);
}

export function generateEpisode(universeId: string, payload: EpisodeGeneratePayload) {
  return apiRequest<UniverseJob>(`/universes/${universeId}/episodes/generate`, {
    method: "POST",
    body: payload,
  });
}

export function getEpisode(id: string) {
  return apiRequest<Episode>(`/episodes/${id}`);
}

export function getEpisodeScenes(id: string) {
  return apiRequest<EpisodeScene[]>(`/episodes/${id}/scenes`);
}

export function getEpisodeTrace(id: string) {
  return apiRequest<AgentTrace>(`/episodes/${id}/trace`);
}

export function getConsistencyDashboard(universeId: string) {
  return apiRequest<ConsistencyDashboard>(`/universes/${universeId}/consistency`);
}

export function getTimelines(universeId: string) {
  return apiRequest<Timeline[]>(`/universes/${universeId}/timelines`);
}

export function getTimeline(id: string) {
  return apiRequest<Timeline>(`/timelines/${id}`);
}

export function getTimelineCommits(id: string) {
  return apiRequest<TimelineCommit[]>(`/timelines/${id}/commits`);
}

export function getTimelineEvents(id: string) {
  return apiRequest<TimelineEvent[]>(`/timelines/${id}/events`);
}

export function createTimelineBranch(timelineId: string, payload: TimelineBranchPayload) {
  return apiRequest<TimelineBranchResult>(`/timelines/${timelineId}/branch`, {
    method: "POST",
    body: payload,
  });
}

export function getTimelineDiff(baseTimelineId: string, compareTimelineId: string) {
  const params = new URLSearchParams({
    base_timeline_id: baseTimelineId,
    compare_timeline_id: compareTimelineId,
  });
  return apiRequest<TimelineDiff>(`/timelines/diff?${params.toString()}`);
}

export function generateTimelineFuture(timelineId: string, prompt?: string | null) {
  return apiRequest<UniverseJob>(`/timelines/${timelineId}/generate-future`, {
    method: "POST",
    body: { prompt: prompt || null },
  });
}
