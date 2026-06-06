"use client";

import { motion } from "framer-motion";
import {
  ArrowLeft,
  Brain,
  CircleDot,
  Flame,
  Link2,
  Shield,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import Link from "next/link";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import { useCharacterContextPack } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type {
  CharacterArcEvent,
  CharacterMemoryEntry,
  CharacterRelationship,
} from "@/types/universe";

type CharacterDossierProps = {
  universeId: string;
  characterId: string;
};

export function CharacterDossier({ universeId, characterId }: CharacterDossierProps) {
  const { data, isLoading, isError, error } = useCharacterContextPack(characterId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Opening character memory" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={error instanceof Error ? error.message : "Unable to open this character."}
        />
      </div>
    );
  }

  const character = data.character;
  const initials = character.canonical_name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div className="mx-auto max-w-7xl">
      <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
        <ArrowLeft className="h-4 w-4" />
        Back to universe
      </ButtonLink>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/35">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(56,189,248,0.14),transparent_38%),linear-gradient(45deg,rgba(244,114,182,0.1),transparent_58%)]" />
          <div className="relative z-10 grid gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-end">
            <div>
              <div className="flex items-center gap-5">
                <div className="flex h-20 w-20 items-center justify-center rounded-3xl border border-white/10 bg-white/[0.08] text-2xl font-semibold text-white shadow-[0_0_50px_rgba(56,189,248,0.16)]">
                  {initials || "?"}
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-sky-200">Dossier</p>
                  <h1 className="mt-2 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
                    {character.canonical_name}
                  </h1>
                </div>
              </div>
              <p className="mt-6 max-w-3xl text-base leading-7 text-slate-300 md:text-lg">
                {character.description || "No character description has been recorded yet."}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <Signal label="Status" value={data.current_status} accent="emerald" />
              <Signal
                label="Emotional State"
                value={data.emotional_state || "Unknown"}
                accent="rose"
              />
              <Signal
                label="Known Links"
                value={String(data.relationships.length)}
                accent="amber"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <Panel icon={Sparkles} title="Profile">
          <Definition label="Aliases" values={character.aliases} fallback="No aliases recorded" />
          <Definition label="Traits" values={data.traits} fallback="No traits recorded" />
          <Definition label="Fears" values={data.fears} fallback="No fears recorded" />
        </Panel>

        <Panel icon={Target} title="Motivations">
          {data.goals.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {data.goals.map((goal) => (
                <DossierPill key={goal} icon={Target} label={goal} tone="sky" />
              ))}
            </div>
          ) : (
            <EmptyLine>No active goals recorded.</EmptyLine>
          )}
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel icon={Users} title="Relationship Web">
          <RelationshipMap characterId={character.id} relationships={data.relationships} />
        </Panel>

        <Panel icon={Brain} title="Knowledge">
          <MemoryList memories={data.knowledge} empty="No private knowledge recorded yet." />
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel icon={Shield} title="Important Memories">
          <MemoryList
            memories={data.important_memories.slice(0, 8)}
            empty="No important memories recorded yet."
          />
        </Panel>

        <Panel icon={Flame} title="Life Events">
          <ArcTimeline events={data.arc} />
        </Panel>
      </section>
    </div>
  );
}

function Signal({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: "emerald" | "rose" | "amber";
}) {
  const accentClass = {
    emerald: "border-emerald-300/20 bg-emerald-300/[0.06] text-emerald-100",
    rose: "border-rose-300/20 bg-rose-300/[0.06] text-rose-100",
    amber: "border-amber-300/20 bg-amber-300/[0.06] text-amber-100",
  }[accent];

  return (
    <div className={cn("rounded-2xl border p-4", accentClass)}>
      <p className="text-xs uppercase tracking-[0.18em] opacity-70">{label}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  );
}

function Panel({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof Sparkles;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="cinematic-surface rounded-2xl p-5"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-sky-200">
          <Icon className="h-4 w-4" />
        </div>
        <h2 className="text-lg font-semibold tracking-[-0.01em] text-white">{title}</h2>
      </div>
      {children}
    </motion.div>
  );
}

function Definition({
  label,
  values,
  fallback,
}: {
  label: string;
  values: string[];
  fallback: string;
}) {
  return (
    <div className="border-t border-white/10 py-4 first:border-t-0 first:pt-0 last:pb-0">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      {values.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {values.map((value) => (
            <span key={value} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-200">
              {value}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{fallback}</p>
      )}
    </div>
  );
}

function DossierPill({
  icon: Icon,
  label,
  tone,
}: {
  icon: typeof Target;
  label: string;
  tone: "sky" | "rose";
}) {
  const toneClass =
    tone === "sky"
      ? "border-sky-300/15 bg-sky-300/[0.06] text-sky-100"
      : "border-rose-300/15 bg-rose-300/[0.06] text-rose-100";
  return (
    <div className={cn("flex min-h-20 items-start gap-3 rounded-2xl border p-4", toneClass)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <p className="text-sm leading-6">{label}</p>
    </div>
  );
}

function RelationshipMap({
  characterId,
  relationships,
}: {
  characterId: string;
  relationships: CharacterRelationship[];
}) {
  if (relationships.length === 0) {
    return <EmptyLine>No relationships recorded yet.</EmptyLine>;
  }

  return (
    <div className="grid gap-3">
      {relationships.map((relationship) => {
        const otherName =
          relationship.source_character_id === characterId
            ? relationship.target_character_name
            : relationship.source_character_name;
        const strength = relationship.strength ?? 0;
        const width = `${Math.min(Math.abs(strength), 100)}%`;
        const positive = strength >= 0;

        return (
          <Link
            key={relationship.id}
            href={`/universes/${relationship.universe_id}/characters/${
              relationship.source_character_id === characterId
                ? relationship.target_character_id
                : relationship.source_character_id
            }`}
            className="rounded-2xl border border-white/10 bg-black/25 p-4 transition hover:border-white/20 hover:bg-white/[0.04]"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-white">{otherName}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {relationship.relationship_type.replaceAll("_", " ")}
                </p>
              </div>
              <span className={cn("rounded-full px-2.5 py-1 text-xs", positive ? "bg-emerald-300/10 text-emerald-100" : "bg-rose-300/10 text-rose-100")}>
                {strength}
              </span>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className={cn("h-full rounded-full", positive ? "bg-emerald-300" : "bg-rose-300")}
                style={{ width }}
              />
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function MemoryList({
  memories,
  empty,
}: {
  memories: CharacterMemoryEntry[];
  empty: string;
}) {
  if (memories.length === 0) {
    return <EmptyLine>{empty}</EmptyLine>;
  }

  return (
    <div className="grid gap-3">
      {memories.map((memory) => (
        <div key={memory.id} className="rounded-2xl border border-white/10 bg-black/25 p-4">
          <div className="flex items-start gap-3">
            <CircleDot className="mt-1 h-4 w-4 shrink-0 text-sky-200" />
            <div>
              <p className="text-sm leading-6 text-slate-200">{memory.content}</p>
              <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-600">
                {memory.memory_type.replaceAll("_", " ")}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ArcTimeline({ events }: { events: CharacterArcEvent[] }) {
  if (events.length === 0) {
    return <EmptyLine>No life events recorded yet.</EmptyLine>;
  }

  return (
    <div className="relative grid gap-4 pl-6 before:absolute before:left-2 before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-white/10">
      {events.map((event) => (
        <div key={`${event.event_id}-${event.memory_id ?? "event"}`} className="relative">
          <span className="absolute -left-[1.85rem] top-1 flex h-4 w-4 rounded-full border border-sky-200/40 bg-sky-300/20" />
          <div className="rounded-2xl border border-white/10 bg-black/25 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-white">{event.title}</h3>
              {event.importance ? (
                <span className="rounded-full border border-amber-300/15 bg-amber-300/[0.06] px-2.5 py-1 text-xs text-amber-100">
                  importance {event.importance}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {event.summary || "No event summary recorded."}
            </p>
            {event.location_name ? (
              <p className="mt-3 inline-flex items-center gap-2 text-xs text-slate-500">
                <Link2 className="h-3.5 w-3.5" />
                {event.location_name}
              </p>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyLine({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-500">
      {children}
    </div>
  );
}
