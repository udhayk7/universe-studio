"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, CalendarDays, Sparkles } from "lucide-react";
import Link from "next/link";
import type { Universe } from "@/types/universe";

type UniverseCardProps = {
  universe: Universe;
};

export function UniverseCard({ universe }: UniverseCardProps) {
  const createdAt = new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(universe.created_at));

  return (
    <motion.article
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="group cinematic-surface rounded-2xl p-5"
    >
      <Link href={`/universes/${universe.id}`} className="block">
        <div className="flex items-start justify-between gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-violet-200">
            <Sparkles className="h-5 w-5" />
          </div>
          <ArrowUpRight className="h-5 w-5 text-slate-500 transition group-hover:text-white" />
        </div>
        <div className="mt-6">
          <h2 className="line-clamp-2 text-xl font-semibold tracking-[-0.01em] text-white">
            {universe.title}
          </h2>
          <p className="mt-3 line-clamp-3 min-h-[72px] text-sm leading-6 text-slate-400">
            {universe.premise || universe.tagline || "A new universe is taking shape."}
          </p>
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          {universe.genre ? (
            <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1">
              {universe.genre}
            </span>
          ) : null}
          {universe.tone ? (
            <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1">
              {universe.tone}
            </span>
          ) : null}
          <span className="ml-auto inline-flex items-center gap-1.5 text-slate-500">
            <CalendarDays className="h-3.5 w-3.5" />
            {createdAt}
          </span>
        </div>
      </Link>
    </motion.article>
  );
}
