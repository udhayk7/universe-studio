"use client";

import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clapperboard,
  GitBranch,
  GitCommitHorizontal,
  Loader2,
  Network,
  Plus,
  Split,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { Button, ButtonLink } from "@/components/ui/button";
import {
  useCreateTimelineBranch,
  useGenerateTimelineFuture,
  useJob,
  useTimelineCommits,
  useTimelineDiff,
  useTimelineEvents,
  useTimelines,
  useUniverse,
} from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type { Timeline, TimelineEvent } from "@/types/universe";

type TimelineWorkbenchProps = {
  universeId: string;
};

export function TimelineWorkbench({ universeId }: TimelineWorkbenchProps) {
  const router = useRouter();
  const universeQuery = useUniverse(universeId);
  const timelinesQuery = useTimelines(universeId);
  const [selectedTimelineId, setSelectedTimelineId] = useState<string | null>(null);
  const [branchEvent, setBranchEvent] = useState<TimelineEvent | null>(null);
  const [futurePrompt, setFuturePrompt] = useState("");
  const [futureJobId, setFutureJobId] = useState<string | null>(null);
  const eventsQuery = useTimelineEvents(selectedTimelineId);
  const commitsQuery = useTimelineCommits(selectedTimelineId);
  const selectedTimeline = useMemo(
    () => timelinesQuery.data?.find((timeline) => timeline.id === selectedTimelineId) ?? null,
    [selectedTimelineId, timelinesQuery.data],
  );
  const baseTimelineId = selectedTimeline?.parent_timeline_id ?? null;
  const diffQuery = useTimelineDiff(baseTimelineId, selectedTimelineId);
  const createBranch = useCreateTimelineBranch(universeId, selectedTimelineId);
  const generateFuture = useGenerateTimelineFuture(selectedTimelineId);
  const jobQuery = useJob(futureJobId);

  useEffect(() => {
    if (selectedTimelineId || !timelinesQuery.data?.length) return;
    const activeId = universeQuery.data?.active_timeline_id;
    const initial =
      timelinesQuery.data.find((timeline) => timeline.id === activeId) ??
      timelinesQuery.data.find((timeline) => timeline.is_canon) ??
      timelinesQuery.data[0];
    if (initial) {
      setSelectedTimelineId(initial.id);
    }
  }, [selectedTimelineId, timelinesQuery.data, universeQuery.data?.active_timeline_id]);

  useEffect(() => {
    const episodeId = jobQuery.data?.result_data?.episode_id;
    if (jobQuery.data?.status === "completed" && typeof episodeId === "string") {
      router.push(`/universes/${universeId}/episodes/${episodeId}`);
    }
  }, [jobQuery.data, router, universeId]);

  if (universeQuery.isLoading || timelinesQuery.isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Loading timeline graph" />
      </div>
    );
  }

  if (universeQuery.isError || !universeQuery.data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            universeQuery.error instanceof Error
              ? universeQuery.error.message
              : "Unable to load universe."
          }
        />
      </div>
    );
  }

  if (timelinesQuery.isError) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            timelinesQuery.error instanceof Error
              ? timelinesQuery.error.message
              : "Unable to load timelines."
          }
        />
      </div>
    );
  }

  const timelines = timelinesQuery.data ?? [];
  const branches = timelines.filter((timeline) => timeline.parent_timeline_id);
  const events = eventsQuery.data ?? [];
  const commits = commitsQuery.data ?? [];
  const futureJob = jobQuery.data;
  const futureWorking =
    generateFuture.isPending ||
    Boolean(futureJobId && futureJob?.status !== "completed" && futureJob?.status !== "failed");

  async function handleGenerateFuture() {
    if (!selectedTimelineId || futureWorking) return;
    const job = await generateFuture.mutateAsync(futurePrompt.trim() || null);
    setFutureJobId(job.id);
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
          <ArrowLeft className="h-4 w-4" />
          Back to universe
        </ButtonLink>
        <ButtonLink href={`/universes/${universeId}/memory`} variant="ghost" size="sm">
          <Network className="h-4 w-4" />
          Memory Explorer
        </ButtonLink>
      </div>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/35">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(139,92,246,0.18),transparent_40%),linear-gradient(40deg,rgba(56,189,248,0.13),transparent_66%)]" />
          <div className="relative z-10 grid gap-8 lg:grid-cols-[1fr_0.8fr]">
            <div>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.07] text-sky-200">
                <GitBranch className="h-5 w-5" />
              </div>
              <p className="text-xs uppercase tracking-[0.28em] text-sky-200">
                Timeline Branching
              </p>
              <h1 className="mt-3 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
                {universeQuery.data.title}
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300">
                Select a historical event, rewrite its outcome, then generate the future that
                grows from that fork.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
                Alternate Future
              </p>
              <textarea
                value={futurePrompt}
                onChange={(event) => setFuturePrompt(event.target.value)}
                placeholder="Optional direction for this branch's next episode."
                rows={4}
                className="mt-4 min-h-28 w-full resize-none rounded-2xl border border-white/10 bg-black/35 p-4 text-sm leading-6 text-white outline-none placeholder:text-slate-600 focus:border-sky-300/40"
              />
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-slate-500">
                  {futureJob?.message ?? "Generate from the selected timeline only."}
                </p>
                <Button
                  type="button"
                  disabled={!selectedTimelineId || futureWorking}
                  onClick={handleGenerateFuture}
                >
                  {futureWorking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Clapperboard className="h-4 w-4" />
                  )}
                  Generate Future
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.35fr_0.65fr]">
        <TimelineSelector
          timelines={timelines}
          branches={branches}
          selectedTimelineId={selectedTimelineId}
          onSelect={setSelectedTimelineId}
        />

        <div className="grid gap-4">
          <TimelineRail
            timeline={selectedTimeline}
            events={events}
            isLoading={eventsQuery.isLoading}
            isError={eventsQuery.isError}
            onBranch={setBranchEvent}
          />
          <CommitHistory commits={commits} isLoading={commitsQuery.isLoading} />
        </div>
      </section>

      {selectedTimeline?.parent_timeline_id ? (
        <section className="mt-6">
          <TimelineComparison
            diffQuery={diffQuery}
            baseName={
              timelines.find((timeline) => timeline.id === selectedTimeline.parent_timeline_id)
                ?.name ?? "Source Timeline"
            }
            compareName={selectedTimeline.name}
          />
        </section>
      ) : null}

      {branchEvent ? (
        <BranchModal
          event={branchEvent}
          isPending={createBranch.isPending}
          error={createBranch.error}
          onClose={() => setBranchEvent(null)}
          onCreate={async (payload) => {
            const result = await createBranch.mutateAsync(payload);
            setSelectedTimelineId(result.timeline.id);
            setBranchEvent(null);
          }}
        />
      ) : null}
    </div>
  );
}

function TimelineSelector({
  timelines,
  branches,
  selectedTimelineId,
  onSelect,
}: {
  timelines: Timeline[];
  branches: Timeline[];
  selectedTimelineId: string | null;
  onSelect: (id: string) => void;
}) {
  if (timelines.length === 0) {
    return (
      <EmptyState
        icon={GitBranch}
        title="No timelines yet"
        description="Create a universe first so the main timeline has somewhere to live."
      />
    );
  }

  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Branches</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Timeline graph</h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
          {branches.length} forks
        </span>
      </div>
      <div className="mt-5 grid gap-2">
        {timelines.map((timeline) => {
          const active = timeline.id === selectedTimelineId;
          return (
            <button
              key={timeline.id}
              type="button"
              onClick={() => onSelect(timeline.id)}
              className={cn(
                "rounded-2xl border p-4 text-left transition",
                active
                  ? "border-sky-300/35 bg-sky-300/[0.08]"
                  : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-white/[0.04]",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{timeline.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {timeline.is_canon ? "Main timeline" : "Branch timeline"}
                  </p>
                </div>
                {active ? <CheckCircle2 className="h-5 w-5 text-sky-200" /> : null}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function TimelineRail({
  timeline,
  events,
  isLoading,
  isError,
  onBranch,
}: {
  timeline: Timeline | null;
  events: TimelineEvent[];
  isLoading: boolean;
  isError: boolean;
  onBranch: (event: TimelineEvent) => void;
}) {
  if (isLoading) return <LoadingState label="Reading timeline events" />;
  if (isError) return <ErrorState message="Unable to read timeline events." />;
  if (!timeline) return null;
  if (events.length === 0) {
    return (
      <EmptyState
        icon={GitCommitHorizontal}
        title="No events on this timeline"
        description="Episode generation and branch changes will appear here."
      />
    );
  }

  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">History</p>
          <h2 className="mt-2 text-xl font-semibold text-white">{timeline.name}</h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
          {events.length} events
        </span>
      </div>
      <div className="relative grid gap-4 pl-6 before:absolute before:left-2 before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-white/10">
        {events.map((event) => (
          <motion.article
            key={`${event.id}-${event.commit_id ?? "commit"}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative rounded-2xl border border-white/10 bg-black/25 p-4"
          >
            <span className="absolute -left-[1.85rem] top-5 flex h-4 w-4 rounded-full border border-sky-200/40 bg-sky-300/20" />
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                  {event.change_type ?? "event"} · {event.commit_type ?? "commit"}
                </p>
                <h3 className="mt-2 text-lg font-semibold text-white">{event.title}</h3>
              </div>
              <Button type="button" variant="secondary" size="sm" onClick={() => onBranch(event)}>
                <Split className="h-4 w-4" />
                Branch
              </Button>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              {event.summary || "No event summary recorded."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-300">
              {event.location_name ? (
                <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1">
                  {event.location_name}
                </span>
              ) : null}
              {event.participants.slice(0, 4).map((participant) => (
                <span
                  key={`${event.id}-${participant}`}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1"
                >
                  <Users className="h-3.5 w-3.5 text-sky-200" />
                  {participant}
                </span>
              ))}
            </div>
          </motion.article>
        ))}
      </div>
    </div>
  );
}

function CommitHistory({
  commits,
  isLoading,
}: {
  commits: Array<{
    id: string;
    message: string;
    commit_type: string;
    created_by: string;
    created_at: string;
  }>;
  isLoading: boolean;
}) {
  if (isLoading) return <LoadingState label="Loading commit history" />;

  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Commits</p>
      <div className="mt-4 grid gap-2 md:grid-cols-2">
        {commits.slice(-6).map((commit) => (
          <div key={commit.id} className="rounded-2xl border border-white/10 bg-black/25 p-4">
            <div className="flex items-center gap-2 text-xs text-sky-200">
              <GitCommitHorizontal className="h-3.5 w-3.5" />
              {commit.commit_type}
            </div>
            <p className="mt-2 line-clamp-2 text-sm font-medium text-white">{commit.message}</p>
            <p className="mt-2 text-xs text-slate-500">{commit.created_by}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function BranchModal({
  event,
  isPending,
  error,
  onClose,
  onCreate,
}: {
  event: TimelineEvent;
  isPending: boolean;
  error: unknown;
  onClose: () => void;
  onCreate: (payload: {
    event_id: string;
    name: string | null;
    new_outcome: string;
  }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [outcome, setOutcome] = useState(
    event.participants[0] ? `${event.participants[0]} dies instead.` : "The event resolves differently.",
  );
  const canSubmit = outcome.trim().length > 0 && !isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-md">
      <motion.form
        initial={{ opacity: 0, y: 18, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        onSubmit={async (submitEvent) => {
          submitEvent.preventDefault();
          if (!canSubmit) return;
          await onCreate({
            event_id: event.id,
            name: name.trim() || null,
            new_outcome: outcome.trim(),
          });
        }}
        className="w-full max-w-2xl rounded-3xl border border-white/10 bg-[#080a12] p-5 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-sky-200">Create Branch</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">{event.title}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-slate-300 hover:bg-white/[0.06] hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Original Outcome</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            {event.summary || "No summary recorded."}
          </p>
        </div>

        <label className="mt-5 grid gap-2">
          <span className="text-sm font-medium text-slate-200">Branch Name</span>
          <input
            value={name}
            onChange={(changeEvent) => setName(changeEvent.target.value)}
            placeholder="Timeline B: The death at the exchange"
            className="h-12 rounded-2xl border border-white/10 bg-black/35 px-4 text-sm text-white outline-none placeholder:text-slate-600 focus:border-sky-300/40"
          />
        </label>

        <label className="mt-4 grid gap-2">
          <span className="text-sm font-medium text-slate-200">New Outcome</span>
          <textarea
            value={outcome}
            onChange={(changeEvent) => setOutcome(changeEvent.target.value)}
            rows={5}
            className="resize-none rounded-2xl border border-white/10 bg-black/35 p-4 text-sm leading-6 text-white outline-none placeholder:text-slate-600 focus:border-sky-300/40"
          />
        </label>

        {error ? (
          <ErrorState
            className="mt-4"
            message={error instanceof Error ? error.message : "Unable to create branch."}
          />
        ) : null}

        <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-slate-500">A new timeline will fork from this commit.</p>
          <Button type="submit" disabled={!canSubmit}>
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Create Branch
          </Button>
        </div>
      </motion.form>
    </div>
  );
}

function TimelineComparison({
  diffQuery,
  baseName,
  compareName,
}: {
  diffQuery: ReturnType<typeof useTimelineDiff>;
  baseName: string;
  compareName: string;
}) {
  if (diffQuery.isLoading) return <LoadingState label="Comparing timelines" />;
  if (diffQuery.isError || !diffQuery.data) {
    return <ErrorState message="Unable to compare these timelines." />;
  }

  const diff = diffQuery.data;
  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Timeline Diff</p>
          <h2 className="mt-2 text-xl font-semibold text-white">
            {baseName} <ArrowRight className="mx-2 inline h-4 w-4 text-slate-500" /> {compareName}
          </h2>
        </div>
        <Sparkles className="h-6 w-6 text-sky-200" />
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <DiffColumn
          title="Changed Events"
          items={diff.changed_events.map((event) => ({
            key: `${event.kind}-${event.title}`,
            label: event.title,
            value: event.compare_summary || event.base_summary || "No summary.",
            meta: event.kind,
          }))}
        />
        <DiffColumn
          title="Relationships"
          items={diff.relationship_differences.map((relationship) => ({
            key: `${relationship.source_character}-${relationship.target_character}-${relationship.relationship_type}`,
            label: `${relationship.source_character} -> ${relationship.target_character}`,
            value: `${relationship.base_strength ?? "none"} -> ${
              relationship.compare_strength ?? "none"
            }`,
            meta: relationship.relationship_type,
          }))}
        />
        <DiffColumn
          title="Character State"
          items={diff.state_differences.map((state) => ({
            key: state.character,
            label: state.character,
            value: `${state.base_status ?? "none"} -> ${state.compare_status ?? "none"}`,
            meta: state.compare_emotional_state || state.base_emotional_state || "state",
          }))}
        />
      </div>
    </div>
  );
}

function DiffColumn({
  title,
  items,
}: {
  title: string;
  items: Array<{ key: string; label: string; value: string; meta: string }>;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <div className="mt-3 grid gap-3">
        {items.length > 0 ? (
          items.map((item) => (
            <div key={item.key} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
              <p className="text-xs uppercase tracking-[0.18em] text-sky-200">{item.meta}</p>
              <p className="mt-2 text-sm font-medium text-white">{item.label}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">{item.value}</p>
            </div>
          ))
        ) : (
          <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-sm text-slate-500">
            No differences recorded.
          </p>
        )}
      </div>
    </div>
  );
}
