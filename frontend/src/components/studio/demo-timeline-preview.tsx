"use client";

import { motion } from "framer-motion";
import { GitBranch, HeartCrack, Shield, Sparkles } from "lucide-react";

const events = [
  { label: "Origin", detail: "The archive wakes", icon: Sparkles },
  { label: "Bond", detail: "Mira trusts Arun", icon: Shield },
  { label: "Rift", detail: "A secret is exposed", icon: HeartCrack },
  { label: "Branch", detail: "Two futures diverge", icon: GitBranch },
];

export function DemoTimelinePreview() {
  return (
    <div className="cinematic-surface overflow-hidden rounded-3xl p-5 md:p-8">
      <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-sky-300/80">Timeline A</p>
          <h3 className="mt-2 text-xl font-semibold text-white">The character survives</h3>
        </div>
        <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-100">
          Canon
        </span>
      </div>

      <div className="relative mt-8">
        <div className="absolute left-5 top-0 h-full w-px bg-gradient-to-b from-sky-300/70 via-violet-300/50 to-transparent md:left-1/2" />
        <div className="space-y-5">
          {events.map((event, index) => {
            const Icon = event.icon;
            const alignRight = index % 2 === 1;

            return (
              <motion.div
                key={event.label}
                initial={false}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08, duration: 0.35 }}
                className={`relative grid gap-4 md:grid-cols-2 ${
                  alignRight ? "md:[&>div]:col-start-2" : ""
                }`}
              >
                <div className="ml-12 rounded-2xl border border-white/10 bg-white/[0.055] p-4 md:ml-0">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.07] text-sky-200">
                      <Icon className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-medium text-white">{event.label}</p>
                      <p className="text-xs text-slate-400">{event.detail}</p>
                    </div>
                  </div>
                </div>
                <span className="absolute left-5 top-5 h-3 w-3 -translate-x-1/2 rounded-full border border-sky-100/70 bg-sky-300 shadow-[0_0_20px_rgba(56,189,248,0.5)] md:left-1/2" />
              </motion.div>
            );
          })}
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Timeline B</p>
            <p className="mt-2 text-sm text-slate-300">The character dies. The city fractures.</p>
          </div>
          <div className="rounded-2xl border border-violet-300/20 bg-violet-400/10 p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-violet-200">Future</p>
            <p className="mt-2 text-sm text-slate-200">Regenerated from memory, not a blank prompt.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
