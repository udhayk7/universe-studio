"use client";

import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Clapperboard, MapPin, Quote, Users } from "lucide-react";
import Link from "next/link";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import { useEpisode, useEpisodeScenes } from "@/hooks/use-universes";
import type { EpisodeScene } from "@/types/universe";

type EpisodeViewerProps = {
  universeId: string;
  episodeId: string;
};

export function EpisodeViewer({ universeId, episodeId }: EpisodeViewerProps) {
  const episodeQuery = useEpisode(episodeId);
  const scenesQuery = useEpisodeScenes(episodeId);

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
        <ButtonLink href={`/universes/${universeId}/episodes/new`} variant="ghost" size="sm">
          <Clapperboard className="h-4 w-4" />
          Generate another
        </ButtonLink>
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

      <section className="mt-6 grid gap-5">
        {scenes.map((scene) => (
          <SceneReader key={scene.id} universeId={universeId} scene={scene} />
        ))}
      </section>
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
      initial={{ opacity: 0, y: 14 }}
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
