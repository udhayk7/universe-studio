"use client";

import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  Clapperboard,
  GitBranch,
  Library,
  ShieldCheck,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import { useCharacters, useUniverse } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/state/studio-store";
import type { Character } from "@/types/universe";

type UniverseDetailProps = {
  id: string;
};

const tabs = [
  { value: "overview", label: "Overview", icon: Library },
  { value: "characters", label: "Characters", icon: Users },
  { value: "timeline", label: "Timeline", icon: GitBranch },
  { value: "memory", label: "Memory", icon: BookOpen },
  { value: "consistency", label: "Consistency", icon: ShieldCheck },
] as const;

type TabValue = (typeof tabs)[number]["value"];

export function UniverseDetail({ id }: UniverseDetailProps) {
  const [activeTab, setActiveTab] = useState<TabValue>("overview");
  const setActiveUniverseId = useStudioStore((state) => state.setActiveUniverseId);
  const { data, isLoading, isError, error } = useUniverse(id);
  const charactersQuery = useCharacters(id);

  useEffect(() => {
    setActiveUniverseId(id);
    return () => setActiveUniverseId(null);
  }, [id, setActiveUniverseId]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Opening universe" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            error instanceof Error ? error.message : "Unable to open this universe."
          }
        />
      </div>
    );
  }

  const createdAt = new Intl.DateTimeFormat("en", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date(data.created_at));

  return (
    <div className="mx-auto max-w-7xl">
      <section className="cinematic-surface overflow-hidden rounded-3xl">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(115deg,rgba(139,92,246,0.18),transparent_40%),linear-gradient(180deg,rgba(255,255,255,0.05),transparent)]" />
          <div className="relative z-10 max-w-4xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-3 py-1.5 text-xs text-slate-300">
              <CalendarDays className="h-3.5 w-3.5 text-sky-200" />
              Created {createdAt}
            </div>
            <h1 className="text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
              {data.title}
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
              {data.premise || data.tagline || "This universe is ready for its first memory."}
            </p>
            <div className="mt-8 flex flex-wrap gap-2 text-xs text-slate-300">
              <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1">
                {data.status}
              </span>
              {data.genre ? (
                <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1">
                  {data.genre}
                </span>
              ) : null}
              {data.tone ? (
                <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1">
                  {data.tone}
                </span>
              ) : null}
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href={`/universes/${id}/episodes/new`}>
                <Clapperboard className="h-4 w-4" />
                Generate Episode
              </ButtonLink>
              <ButtonLink href={`/universes/${id}/memory`} variant="secondary">
                <BookOpen className="h-4 w-4" />
                Memory Explorer
              </ButtonLink>
              <ButtonLink href={`/universes/${id}/consistency`} variant="secondary">
                <ShieldCheck className="h-4 w-4" />
                Consistency
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6">
        <div className="flex gap-2 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.04] p-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.value;

            return (
              <button
                key={tab.value}
                type="button"
                onClick={() => setActiveTab(tab.value)}
                className={cn(
                  "flex h-11 min-w-32 items-center justify-center gap-2 rounded-xl px-4 text-sm transition",
                  active
                    ? "bg-white text-black"
                    : "text-slate-400 hover:bg-white/[0.06] hover:text-white",
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="mt-5"
        >
          {activeTab === "overview" ? (
            <div className="grid gap-4 md:grid-cols-3">
              <FactCard label="Premise" value={data.premise || "No premise recorded yet."} />
              <FactCard label="Genre" value={data.genre || "Unspecified"} />
              <FactCard label="Tone" value={data.tone || "Unspecified"} />
            </div>
          ) : null}

          {activeTab === "characters" ? (
            <CharactersPanel
              universeId={id}
              characters={charactersQuery.data ?? []}
              isLoading={charactersQuery.isLoading}
              isError={charactersQuery.isError}
              error={charactersQuery.error}
            />
          ) : null}

          {activeTab === "timeline" ? (
            <EmptyState
              icon={GitBranch}
              title="Open timeline history"
              description="Branch an event, compare alternate history, and generate a different future."
              action={
                <ButtonLink href={`/universes/${id}/timeline`}>
                  <GitBranch className="h-4 w-4" />
                  Timeline Workbench
                </ButtonLink>
              }
            />
          ) : null}

          {activeTab === "memory" ? (
            <EmptyState
              icon={BookOpen}
              title="Open the memory graph"
              description="Explore characters, events, locations, objects, and relationships in one visual system."
              action={
                <ButtonLink href={`/universes/${id}/memory`}>
                  <BookOpen className="h-4 w-4" />
                  Memory Explorer
                </ButtonLink>
              }
            />
          ) : null}

          {activeTab === "consistency" ? (
            <EmptyState
              icon={ShieldCheck}
              title="Open continuity checks"
              description="Review agent validation, unresolved contradictions, and branch leakage."
              action={
                <ButtonLink href={`/universes/${id}/consistency`}>
                  <ShieldCheck className="h-4 w-4" />
                  Consistency Dashboard
                </ButtonLink>
              }
            />
          ) : null}
        </motion.div>
      </section>

      <div className="mt-8">
        <ButtonLink href="/universes" variant="secondary">
          Back to universes
        </ButtonLink>
      </div>
    </div>
  );
}

function FactCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className="mt-4 text-sm leading-6 text-slate-200">{value}</p>
    </div>
  );
}

function CharactersPanel({
  universeId,
  characters,
  isLoading,
  isError,
  error,
}: {
  universeId: string;
  characters: Character[];
  isLoading: boolean;
  isError: boolean;
  error: unknown;
}) {
  if (isLoading) {
    return <LoadingState label="Loading cast memory" />;
  }

  if (isError) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "Unable to load characters."}
      />
    );
  }

  if (characters.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="No characters yet"
        description="The first cast members will appear here as this universe grows."
      />
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {characters.map((character) => (
        <CharacterCard key={character.id} universeId={universeId} character={character} />
      ))}
    </div>
  );
}

function CharacterCard({ universeId, character }: { universeId: string; character: Character }) {
  const initials = character.canonical_name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="group cinematic-surface rounded-2xl p-5"
    >
      <Link href={`/universes/${universeId}/characters/${character.id}`} className="block">
        <div className="flex items-start justify-between gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.07] text-sm font-semibold text-white">
            {initials || "?"}
          </div>
          <ArrowUpRight className="h-5 w-5 text-slate-500 transition group-hover:text-white" />
        </div>
        <h3 className="mt-5 line-clamp-2 text-xl font-semibold tracking-[-0.01em] text-white">
          {character.canonical_name}
        </h3>
        <p className="mt-3 line-clamp-3 min-h-[72px] text-sm leading-6 text-slate-400">
          {character.description || "A character profile is forming."}
        </p>
        <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-300">
          <span className="rounded-full border border-emerald-300/15 bg-emerald-300/[0.06] px-3 py-1 text-emerald-100">
            {character.status}
          </span>
          {character.aliases.slice(0, 2).map((alias) => (
            <span key={alias} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1">
              {alias}
            </span>
          ))}
        </div>
      </Link>
    </motion.article>
  );
}
