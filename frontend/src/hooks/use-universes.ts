"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createUniverse,
  createUniverseFromInput,
  createTimelineBranch,
  generateEpisode,
  generateTimelineFuture,
  getCharacter,
  getCharacterContextPack,
  getCharacters,
  getConsistencyDashboard,
  getEpisode,
  getEpisodeScenes,
  getEpisodeTrace,
  getJob,
  getJobTrace,
  getTimeline,
  getTimelineCommits,
  getTimelineDiff,
  getTimelineEvents,
  getTimelines,
  getUniverse,
  getUniverseEvents,
  getUniverseGraph,
  getUniverseLocations,
  getUniverseMemoryOverview,
  getUniverseObjects,
  getUniverseRelationships,
  getUniverses,
  setupDemo,
} from "@/services/api/universes";
import type {
  CreateUniversePayload,
  EpisodeGeneratePayload,
  TimelineBranchPayload,
} from "@/types/universe";

export const universeQueryKeys = {
  all: ["universes"] as const,
  detail: (id: string) => ["universes", id] as const,
  job: (id: string) => ["jobs", id] as const,
  jobTrace: (id: string) => ["jobs", id, "trace"] as const,
  characters: (universeId: string) => ["universes", universeId, "characters"] as const,
  character: (id: string) => ["characters", id] as const,
  characterContext: (id: string) => ["characters", id, "context-pack"] as const,
  memoryOverview: (id: string) => ["universes", id, "memory-overview"] as const,
  graph: (id: string) => ["universes", id, "graph"] as const,
  events: (id: string) => ["universes", id, "events"] as const,
  relationships: (id: string) => ["universes", id, "relationships"] as const,
  locations: (id: string) => ["universes", id, "locations"] as const,
  objects: (id: string) => ["universes", id, "objects"] as const,
  episode: (id: string) => ["episodes", id] as const,
  episodeScenes: (id: string) => ["episodes", id, "scenes"] as const,
  episodeTrace: (id: string) => ["episodes", id, "trace"] as const,
  consistency: (universeId: string) => ["universes", universeId, "consistency"] as const,
  timelines: (universeId: string) => ["universes", universeId, "timelines"] as const,
  timeline: (id: string) => ["timelines", id] as const,
  timelineCommits: (id: string) => ["timelines", id, "commits"] as const,
  timelineEvents: (id: string) => ["timelines", id, "events"] as const,
  timelineDiff: (baseId: string, compareId: string) =>
    ["timelines", "diff", baseId, compareId] as const,
};

export function useUniverses() {
  return useQuery({
    queryKey: universeQueryKeys.all,
    queryFn: getUniverses,
  });
}

export function useUniverse(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.detail(id),
    queryFn: () => getUniverse(id),
    enabled: Boolean(id),
  });
}

export function useCreateUniverse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateUniversePayload) => createUniverse(payload),
    onSuccess: (universe) => {
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.all });
      queryClient.setQueryData(universeQueryKeys.detail(universe.id), universe);
    },
  });
}

export function useCreateUniverseFromInput() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (formData: FormData) => createUniverseFromInput(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.all });
    },
  });
}

export function useSetupDemo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: setupDemo,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.all });
      queryClient.invalidateQueries({
        queryKey: universeQueryKeys.detail(result.universe_id),
      });
    },
  });
}

export function useJob(id: string | null) {
  return useQuery({
    queryKey: id ? universeQueryKeys.job(id) : ["jobs", "pending"],
    queryFn: () => getJob(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 1200;
    },
  });
}

export function useJobTrace(id: string | null) {
  return useQuery({
    queryKey: id ? universeQueryKeys.jobTrace(id) : ["jobs", "pending", "trace"],
    queryFn: () => getJobTrace(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const steps = query.state.data?.steps ?? [];
      return steps.some((step) => step.status === "running") ? 1200 : false;
    },
  });
}

export function useCharacters(universeId: string) {
  return useQuery({
    queryKey: universeQueryKeys.characters(universeId),
    queryFn: () => getCharacters(universeId),
    enabled: Boolean(universeId),
  });
}

export function useCharacter(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.character(id),
    queryFn: () => getCharacter(id),
    enabled: Boolean(id),
  });
}

export function useCharacterContextPack(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.characterContext(id),
    queryFn: () => getCharacterContextPack(id),
    enabled: Boolean(id),
  });
}

export function useUniverseMemoryOverview(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.memoryOverview(id),
    queryFn: () => getUniverseMemoryOverview(id),
    enabled: Boolean(id),
  });
}

export function useUniverseGraph(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.graph(id),
    queryFn: () => getUniverseGraph(id),
    enabled: Boolean(id),
  });
}

export function useUniverseEvents(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.events(id),
    queryFn: () => getUniverseEvents(id),
    enabled: Boolean(id),
  });
}

export function useUniverseRelationships(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.relationships(id),
    queryFn: () => getUniverseRelationships(id),
    enabled: Boolean(id),
  });
}

export function useUniverseLocations(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.locations(id),
    queryFn: () => getUniverseLocations(id),
    enabled: Boolean(id),
  });
}

export function useUniverseObjects(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.objects(id),
    queryFn: () => getUniverseObjects(id),
    enabled: Boolean(id),
  });
}

export function useGenerateEpisode(universeId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: EpisodeGeneratePayload) => generateEpisode(universeId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.detail(universeId) });
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.events(universeId) });
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.memoryOverview(universeId) });
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.graph(universeId) });
    },
  });
}

export function useEpisode(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.episode(id),
    queryFn: () => getEpisode(id),
    enabled: Boolean(id),
  });
}

export function useEpisodeScenes(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.episodeScenes(id),
    queryFn: () => getEpisodeScenes(id),
    enabled: Boolean(id),
  });
}

export function useEpisodeTrace(id: string) {
  return useQuery({
    queryKey: universeQueryKeys.episodeTrace(id),
    queryFn: () => getEpisodeTrace(id),
    enabled: Boolean(id),
  });
}

export function useConsistencyDashboard(universeId: string) {
  return useQuery({
    queryKey: universeQueryKeys.consistency(universeId),
    queryFn: () => getConsistencyDashboard(universeId),
    enabled: Boolean(universeId),
  });
}

export function useTimelines(universeId: string) {
  return useQuery({
    queryKey: universeQueryKeys.timelines(universeId),
    queryFn: () => getTimelines(universeId),
    enabled: Boolean(universeId),
  });
}

export function useTimeline(id: string | null) {
  return useQuery({
    queryKey: id ? universeQueryKeys.timeline(id) : ["timelines", "pending"],
    queryFn: () => getTimeline(id as string),
    enabled: Boolean(id),
  });
}

export function useTimelineCommits(id: string | null) {
  return useQuery({
    queryKey: id ? universeQueryKeys.timelineCommits(id) : ["timelines", "pending", "commits"],
    queryFn: () => getTimelineCommits(id as string),
    enabled: Boolean(id),
  });
}

export function useTimelineEvents(id: string | null) {
  return useQuery({
    queryKey: id ? universeQueryKeys.timelineEvents(id) : ["timelines", "pending", "events"],
    queryFn: () => getTimelineEvents(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateTimelineBranch(universeId: string, timelineId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TimelineBranchPayload) =>
      createTimelineBranch(timelineId as string, payload),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.timelines(universeId) });
      queryClient.invalidateQueries({
        queryKey: universeQueryKeys.timelineEvents(result.timeline.id),
      });
      queryClient.invalidateQueries({
        queryKey: universeQueryKeys.timelineCommits(result.timeline.id),
      });
      queryClient.invalidateQueries({ queryKey: universeQueryKeys.memoryOverview(universeId) });
    },
  });
}

export function useTimelineDiff(baseId: string | null, compareId: string | null) {
  return useQuery({
    queryKey:
      baseId && compareId
        ? universeQueryKeys.timelineDiff(baseId, compareId)
        : ["timelines", "diff", "pending"],
    queryFn: () => getTimelineDiff(baseId as string, compareId as string),
    enabled: Boolean(baseId && compareId && baseId !== compareId),
  });
}

export function useGenerateTimelineFuture(timelineId: string | null) {
  return useMutation({
    mutationFn: (prompt?: string | null) => generateTimelineFuture(timelineId as string, prompt),
  });
}
