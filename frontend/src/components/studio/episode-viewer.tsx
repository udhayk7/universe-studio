"use client";

import { motion } from "framer-motion";
import {
  Activity,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clapperboard,
  Clock,
  Database,
  Images,
  MapPin,
  PenLine,
  Quote,
  ShieldCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import { useEpisode, useEpisodeScenes, useEpisodeTrace } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type { AgentTraceStep, EpisodeScene } from "@/types/universe";

type EpisodeViewerProps = {
  universeId: string;
  episodeId: string;
};

export function EpisodeViewer({ universeId, episodeId }: EpisodeViewerProps) {
  const [activeView, setActiveView] = useState<"reader" | "trace">("reader");
  const episodeQuery = useEpisode(episodeId);
  const scenesQuery = useEpisodeScenes(episodeId);
  const traceQuery = useEpisodeTrace(episodeId);

  if (episodeQuery.isLoading || scenesQuery.isLoading) {
    return (
      <div className="mx-auto max-w-6xl">
        <LoadingState label="Opening episode" />
      </div>
    );
  }

  if (episodeQuery.isError || !episodeQuery.data) {
    return (
      <div className="mx-auto max-w-6xl">
        <ErrorState
          message={
            episodeQuery.error instanceof Error
              ? episodeQuery.error.message
              : "Unable to open this episode."
          }
        />
      </div>
    );
  }

  if (scenesQuery.isError) {
    return (
      <div className="mx-auto max-w-6xl">
        <ErrorState
          message={
            scenesQuery.error instanceof Error
              ? scenesQuery.error.message
              : "Unable to open episode scenes."
          }
        />
      </div>
    );
  }

  const episode = episodeQuery.data;
  const scenes = scenesQuery.data ?? [];
  const createdAt = new Intl.DateTimeFormat("en", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date(episode.created_at));

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
          <ArrowLeft className="h-4 w-4" />
          Back to universe
        </ButtonLink>
        <div className="flex flex-wrap gap-2">
          <ButtonLink
            href={`/universes/${universeId}/episodes/${episodeId}/storyboard`}
            variant="secondary"
            size="sm"
          >
            <Images className="h-4 w-4" />
            Storyboard
          </ButtonLink>
          <ButtonLink href={`/universes/${universeId}/episodes/new`} variant="ghost" size="sm">
            <Clapperboard className="h-4 w-4" />
            Generate another
          </ButtonLink>
        </div>
      </div>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/35">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(130deg,rgba(56,189,248,0.14),transparent_42%),linear-gradient(35deg,rgba(139,92,246,0.18),transparent_62%)]" />
          <div className="relative z-10">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-3 py-1.5 text-xs text-slate-300">
              <BookOpen className="h-3.5 w-3.5 text-sky-200" />
              {createdAt} · {episode.scene_count} scenes
            </div>
            <h1 className="text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
              {episode.title}
            </h1>
            {episode.logline ? (
              <p className="mt-5 max-w-3xl text-lg leading-8 text-sky-100">
                {episode.logline}
              </p>
            ) : null}
            <p className="mt-5 max-w-4xl text-base leading-7 text-slate-300">
              {episode.summary || "No episode summary recorded."}
            </p>
          </div>
        </div>
      </section>

      <div className="mt-6 flex gap-2 rounded-2xl border border-white/10 bg-white/[0.04] p-1">
        {[
          { value: "reader", label: "Screenplay", icon: BookOpen },
          { value: "trace", label: "Agent Trace", icon: Activity },
        ].map((item) => {
          const Icon = item.icon;
          const active = activeView === item.value;

          return (
            <button
              key={item.value}
              type="button"
              onClick={() => setActiveView(item.value as "reader" | "trace")}
              className={cn(
                "flex h-11 flex-1 items-center justify-center gap-2 rounded-xl px-4 text-sm transition md:flex-none",
                active
                  ? "bg-white text-black"
                  : "text-slate-400 hover:bg-white/[0.06] hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </div>

      {activeView === "reader" ? (
        <section className="mt-6 grid gap-5">
          {scenes.map((scene) => (
            <SceneReader key={scene.id} universeId={universeId} scene={scene} />
          ))}
        </section>
      ) : (
        <AgentTracePanel
          steps={traceQuery.data?.steps ?? []}
          isLoading={traceQuery.isLoading}
          isError={traceQuery.isError}
          error={traceQuery.error}
        />
      )}
    </div>
  );
}

function SceneReader({ universeId, scene }: { universeId: string; scene: EpisodeScene }) {
  const dialogueLines = (scene.dialogue || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return (
    <motion.article
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      className="cinematic-surface overflow-hidden rounded-2xl"
    >
      <div className="border-b border-white/10 bg-white/[0.035] p-5 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
              Scene {scene.scene_number}
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.015em] text-white">
              {scene.title || "Untitled Scene"}
            </h2>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-black/25 px-3 py-1.5 text-xs text-slate-300">
            <MapPin className="h-3.5 w-3.5 text-sky-200" />
            {scene.location_name || "Unspecified location"}
          </div>
        </div>

        {scene.participants.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {scene.participants.map((participant) => (
              <Link
                key={`${scene.id}-${participant.character_id}-${participant.role}`}
                href={`/universes/${universeId}/characters/${participant.character_id}`}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-200 transition hover:border-sky-300/30 hover:text-white"
              >
                <Users className="h-3.5 w-3.5 text-sky-200" />
                {participant.character_name}
              </Link>
            ))}
          </div>
        ) : null}
      </div>

      <div className="grid gap-5 p-5 md:p-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">
            Cinematic Description
          </p>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            {scene.visual_direction || "No visual direction recorded."}
          </p>
          {scene.summary ? (
            <div className="mt-5 rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.045] p-4">
              <p className="text-xs uppercase tracking-[0.22em] text-emerald-100/70">
                Outcome
              </p>
              <p className="mt-2 text-sm leading-6 text-emerald-50">{scene.summary}</p>
            </div>
          ) : null}
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
          <div className="mb-4 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-slate-500">
            <Quote className="h-3.5 w-3.5 text-sky-200" />
            Dialogue
          </div>
          {dialogueLines.length > 0 ? (
            <div className="grid gap-3">
              {dialogueLines.map((line, index) => (
                <DialogueLine key={`${scene.id}-${index}`} line={line} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No dialogue recorded.</p>
          )}
        </div>
      </div>
    </motion.article>
  );
}

function DialogueLine({ line }: { line: string }) {
  const [speaker, ...rest] = line.split(":");
  const hasSpeaker = rest.length > 0;

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
      {hasSpeaker ? (
        <>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">
            {speaker}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-200">{rest.join(":").trim()}</p>
        </>
      ) : (
        <p className="text-sm leading-6 text-slate-200">{line}</p>
      )}
    </div>
  );
}

function AgentTracePanel({
  steps,
  isLoading,
  isError,
  error,
}: {
  steps: AgentTraceStep[];
  isLoading: boolean;
  isError: boolean;
  error: unknown;
}) {
  if (isLoading) {
    return (
      <section className="mt-6">
        <LoadingState label="Loading agent trace" />
      </section>
    );
  }

  if (isError) {
    return (
      <section className="mt-6">
        <ErrorState
          message={error instanceof Error ? error.message : "Unable to load agent trace."}
        />
      </section>
    );
  }

  if (steps.length === 0) {
    return (
      <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.04] p-8 text-center">
        <Activity className="mx-auto h-8 w-8 text-slate-500" />
        <h2 className="mt-4 text-xl font-semibold text-white">No trace recorded</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
          Future generated episodes will show each cooperating agent and memory update here.
        </p>
      </section>
    );
  }

  const completed = steps.filter((step) => step.status === "completed").length;

  return (
    <section className="mt-6 grid gap-5 lg:grid-cols-[0.72fr_1.28fr]">
      <div className="cinematic-surface rounded-2xl p-5">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Trace Summary</p>
        <p className="mt-3 text-4xl font-semibold tracking-[-0.02em] text-white">
          {completed}/{steps.length}
        </p>
        <p className="mt-2 text-sm text-slate-400">agent steps completed</p>

        <div className="mt-6 grid gap-3">
          {steps.map((step, index) => (
            <a
              key={step.id}
              href={`#trace-${step.id}`}
              className="group flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.035] p-3 transition hover:border-sky-300/25 hover:bg-sky-300/[0.06]"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-black/30 text-xs text-slate-300">
                {index + 1}
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium text-white">
                  {step.agent_name}
                </span>
                <span className="block text-xs text-slate-500">{step.status}</span>
              </span>
            </a>
          ))}
        </div>
      </div>

      <div className="grid gap-4">
        {steps.map((step, index) => (
          <AgentTraceCard key={step.id} step={step} index={index} />
        ))}
      </div>
    </section>
  );
}

function AgentTraceCard({ step, index }: { step: AgentTraceStep; index: number }) {
  const Icon = iconForAgent(step.agent_name);
  const duration = formatDuration(step.duration_ms);

  return (
    <motion.article
      id={`trace-${step.id}`}
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      className="cinematic-surface overflow-hidden rounded-2xl"
    >
      <div className="border-b border-white/10 bg-white/[0.035] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-black/30 text-sky-200">
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">
                Step {index + 1}
              </p>
              <h2 className="mt-1 text-xl font-semibold text-white">{step.agent_name}</h2>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-3 py-1",
                step.status === "completed"
                  ? "border-emerald-300/20 bg-emerald-300/[0.06] text-emerald-100"
                  : "border-sky-300/20 bg-sky-300/[0.06] text-sky-100",
              )}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              {step.status}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-slate-300">
              <Clock className="h-3.5 w-3.5" />
              {duration}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 p-5 md:grid-cols-2">
        <TraceText label="Input" value={step.input_summary} />
        <TraceText label="Output" value={step.output_summary} />
      </div>
    </motion.article>
  );
}

function TraceText({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-3 text-sm leading-6 text-slate-300">{value || "Not recorded."}</p>
    </div>
  );
}

function iconForAgent(agentName: string) {
  if (agentName.includes("Story")) return PenLine;
  if (agentName.includes("Director")) return Clapperboard;
  if (agentName.includes("Consistency")) return ShieldCheck;
  if (agentName.includes("Memory")) return Database;
  return BookOpen;
}

function formatDuration(durationMs: number | null) {
  if (durationMs === null) return "pending";
  if (durationMs < 1000) return `${durationMs}ms`;
  return `${(durationMs / 1000).toFixed(1)}s`;
}
