"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Brain,
  CheckCircle2,
  Clapperboard,
  Database,
  Loader2,
  PenLine,
  ShieldCheck,
  WandSparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { Button, ButtonLink } from "@/components/ui/button";
import { useGenerateEpisode, useJob, useUniverse } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type { ConsistencyAffectedEntity, ConsistencyIssueResult, UniverseJob } from "@/types/universe";

type EpisodeGenerationProps = {
  universeId: string;
};

const steps = [
  {
    label: "Historian Agent",
    detail: "Universe memory",
    threshold: 8,
    completeAt: 32,
    icon: Brain,
  },
  {
    label: "Story Agent",
    detail: "Outline",
    threshold: 32,
    completeAt: 62,
    icon: PenLine,
  },
  {
    label: "Director Agent",
    detail: "Scenes",
    threshold: 62,
    completeAt: 78,
    icon: Clapperboard,
  },
  {
    label: "Consistency Agent",
    detail: "Continuity",
    threshold: 78,
    completeAt: 88,
    icon: ShieldCheck,
  },
  {
    label: "Memory Update",
    detail: "Consequences",
    threshold: 88,
    completeAt: 100,
    icon: Database,
  },
] as const;

export function EpisodeGeneration({ universeId }: EpisodeGenerationProps) {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const universeQuery = useUniverse(universeId);
  const generateEpisode = useGenerateEpisode(universeId);
  const jobQuery = useJob(jobId);
  const job = jobQuery.data;

  const episodeId = useMemo(() => {
    const value = job?.result_data?.episode_id;
    return typeof value === "string" ? value : null;
  }, [job]);
  const consistencyBlockers = useMemo(() => getConsistencyBlockers(job), [job]);

  useEffect(() => {
    if (job?.status === "completed" && episodeId) {
      router.push(`/universes/${universeId}/episodes/${episodeId}`);
    }
  }, [episodeId, job?.status, router, universeId]);

  if (universeQuery.isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Preparing generation room" />
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
              : "Unable to open this universe."
          }
        />
      </div>
    );
  }

  const progress = job?.progress ?? (generateEpisode.isPending ? 4 : 0);
  const status = job?.status ?? (generateEpisode.isPending ? "queued" : "idle");
  const isWorking =
    generateEpisode.isPending ||
    (Boolean(jobId) && status !== "completed" && status !== "failed");
  const message =
    job?.message ?? (generateEpisode.isPending ? "Episode generation queued" : "Ready");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isWorking) return;

    setJobId(null);
    const queuedJob = await generateEpisode.mutateAsync({
      prompt: prompt.trim() || null,
    });
    setJobId(queuedJob.id);
  }

  return (
    <div className="mx-auto max-w-7xl">
      <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
        <ArrowLeft className="h-4 w-4" />
        Back to universe
      </ButtonLink>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/35">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(139,92,246,0.18),transparent_42%),linear-gradient(40deg,rgba(56,189,248,0.12),transparent_62%)]" />
          <div className="relative z-10 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.07] text-sky-200">
                <WandSparkles className="h-5 w-5" />
              </div>
              <p className="text-xs uppercase tracking-[0.28em] text-sky-200">
                Generate Episode
              </p>
              <h1 className="mt-3 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
                {universeQuery.data.title}
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
                {universeQuery.data.premise ||
                  "The next episode will be written from this universe's stored memory."}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="rounded-2xl border border-white/10 bg-black/30 p-5">
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-200">Episode Request</span>
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder="Optional direction, conflict, theme, or character focus."
                  rows={8}
                  className="min-h-52 resize-none rounded-2xl border border-white/10 bg-black/35 p-4 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/50"
                />
              </label>

              {generateEpisode.isError ? (
                <ErrorState
                  className="mt-5"
                  message={
                    generateEpisode.error instanceof Error
                      ? generateEpisode.error.message
                      : "Unable to start episode generation."
                  }
                />
              ) : null}

              {jobQuery.isError ? (
                <ErrorState
                  className="mt-5"
                  message={
                    jobQuery.error instanceof Error
                      ? jobQuery.error.message
                      : "Unable to read generation status."
                  }
                />
              ) : null}

              {job?.status === "failed" ? (
                consistencyBlockers.length > 0 ? (
                  <ConsistencyFailurePanel
                    className="mt-5"
                    issues={consistencyBlockers}
                    fallbackMessage={job.message || "Episode generation failed."}
                  />
                ) : (
                  <ErrorState
                    className="mt-5"
                    message={job.message || "Episode generation failed."}
                  />
                )
              ) : null}

              <div className="mt-5 flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Status</p>
                  <p className="mt-1 text-sm text-slate-300">{message}</p>
                </div>
                <Button type="submit" disabled={isWorking}>
                  {isWorking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}
                  {isWorking ? "Generating" : "Generate Episode"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.75fr_1.25fr]">
        <div className="cinematic-surface rounded-2xl p-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Progress</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.02em] text-white">
                {Math.min(Math.max(progress, 0), 100)}%
              </p>
            </div>
            {job?.status === "completed" ? (
              <CheckCircle2 className="h-8 w-8 text-emerald-300" />
            ) : isWorking ? (
              <Loader2 className="h-8 w-8 animate-spin text-sky-200" />
            ) : (
              <WandSparkles className="h-8 w-8 text-slate-500" />
            )}
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-300 via-violet-300 to-fuchsia-300 transition-all duration-500"
              style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
            />
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-5">
          {steps.map((step) => (
            <StageCard
              key={step.label}
              label={step.label}
              detail={step.detail}
              progress={progress}
              status={status}
              threshold={step.threshold}
              completeAt={step.completeAt}
              icon={step.icon}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function ConsistencyFailurePanel({
  issues,
  fallbackMessage,
  className,
}: {
  issues: ConsistencyIssueResult[];
  fallbackMessage: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border border-rose-300/20 bg-rose-400/[0.07] p-4", className)}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-rose-300/20 bg-black/25 text-rose-100">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-rose-50">
            Consistency validation blocked persistence
          </p>
          <p className="mt-1 text-sm leading-6 text-rose-100/75">{fallbackMessage}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        {issues.map((issue, index) => (
          <ConsistencyIssueCard key={`${issue.issue ?? "issue"}-${index}`} issue={issue} />
        ))}
      </div>
    </div>
  );
}

function ConsistencyIssueCard({ issue }: { issue: ConsistencyIssueResult }) {
  const affectedEntities = formatAffectedEntities(issue.affected_entities);
  const severity = issue.severity ?? "blocker";
  const issueType = issue.issue_type?.replaceAll("_", " ") ?? "continuity";

  return (
    <div className="rounded-xl border border-white/10 bg-black/25 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
            severity === "blocker" || severity === "critical"
              ? "border-rose-300/25 bg-rose-300/[0.12] text-rose-50"
              : severity === "high"
                ? "border-amber-300/25 bg-amber-300/[0.12] text-amber-50"
                : "border-sky-300/25 bg-sky-300/[0.12] text-sky-50",
          )}
        >
          {severity}
        </span>
        <span className="rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1 text-[11px] font-medium capitalize text-slate-300">
          {issueType}
        </span>
      </div>

      <p className="mt-3 text-sm font-semibold leading-6 text-white">
        {issue.issue ?? "Continuity issue detected."}
      </p>
      {issue.explanation ? (
        <p className="mt-1 text-sm leading-6 text-slate-300">{issue.explanation}</p>
      ) : null}
      {affectedEntities ? (
        <p className="mt-3 text-xs leading-5 text-slate-400">
          <span className="font-medium uppercase tracking-[0.16em] text-slate-500">Entity</span>
          <span className="ml-2 text-slate-300">{affectedEntities}</span>
        </p>
      ) : null}
      {issue.suggested_fix ? (
        <div className="mt-3 rounded-lg border border-sky-300/15 bg-sky-300/[0.06] p-3">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-sky-100/70">
            Suggested Fix
          </p>
          <p className="mt-1 text-sm leading-6 text-sky-50">{issue.suggested_fix}</p>
        </div>
      ) : null}
    </div>
  );
}

function getConsistencyBlockers(job: UniverseJob | undefined): ConsistencyIssueResult[] {
  const blockers = job?.result_data?.consistency_blockers;
  if (!Array.isArray(blockers)) return [];

  return blockers.flatMap((blocker) => {
    if (!isRecord(blocker)) return [];
    return [
      {
        severity: asString(blocker.severity),
        issue_type: asString(blocker.issue_type),
        issue: asString(blocker.issue),
        explanation: asString(blocker.explanation),
        suggested_fix: asNullableString(blocker.suggested_fix),
        affected_entities: parseAffectedEntities(blocker.affected_entities),
      },
    ];
  });
}

function parseAffectedEntities(value: unknown): ConsistencyAffectedEntity[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((entity) => {
    if (!isRecord(entity)) return [];
    return [
      {
        entity_type: asString(entity.entity_type),
        entity_id: asString(entity.entity_id),
        name: asString(entity.name),
      },
    ];
  });
}

function formatAffectedEntities(entities: ConsistencyAffectedEntity[] | undefined) {
  if (!entities || entities.length === 0) return null;
  return entities
    .map((entity) => entity.name || entity.entity_id || entity.entity_type)
    .filter(Boolean)
    .join(", ");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function asNullableString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function StageCard({
  label,
  detail,
  progress,
  status,
  threshold,
  completeAt,
  icon: Icon,
}: {
  label: string;
  detail: string;
  progress: number;
  status: string;
  threshold: number;
  completeAt: number;
  icon: typeof Brain;
}) {
  const complete = status === "completed" || progress >= completeAt;
  const active = !complete && progress >= threshold;

  return (
    <motion.div
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "min-h-36 rounded-2xl border p-4 transition",
        complete
          ? "border-emerald-300/25 bg-emerald-300/[0.06]"
          : active
            ? "border-sky-300/25 bg-sky-300/[0.06]"
            : "border-white/10 bg-white/[0.04]",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-black/25 text-sky-200">
          <Icon className="h-4 w-4" />
        </div>
        {complete ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-300" />
        ) : active ? (
          <Loader2 className="h-5 w-5 animate-spin text-sky-200" />
        ) : null}
      </div>
      <h3 className="mt-5 text-sm font-semibold text-white">{label}</h3>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </motion.div>
  );
}
