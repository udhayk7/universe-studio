"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Clapperboard,
  GitBranch,
  History,
  Sparkles,
  Users,
} from "lucide-react";
import Image from "next/image";
import { Navbar } from "@/components/layout/navbar";
import { SectionHeader } from "@/components/common/section-header";
import { DemoTimelinePreview } from "@/components/studio/demo-timeline-preview";
import { FeatureCard } from "@/components/studio/feature-card";
import { ButtonLink } from "@/components/ui/button";

const features = [
  {
    title: "Persistent Characters",
    description: "Characters carry identity, motivation, emotional history, and relationship state.",
    icon: Users,
  },
  {
    title: "World Memory",
    description: "Universes remember places, objects, rules, events, and what each moment changed.",
    icon: Brain,
  },
  {
    title: "Timeline Branching",
    description: "Historical changes become alternate futures without erasing the original canon.",
    icon: GitBranch,
  },
  {
    title: "Episode Generation",
    description: "Future stories can begin from the universe state instead of a disconnected prompt.",
    icon: Clapperboard,
  },
  {
    title: "Alternate Futures",
    description: "Explore cause and effect across divergent paths with clear continuity anchors.",
    icon: History,
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-[#050507] text-white">
      <Navbar />

      <section className="relative flex min-h-[88svh] items-center overflow-hidden pt-16">
        <Image
          src="/images/universe-studio-hero.png"
          alt="Cinematic universe creation interface"
          fill
          priority
          className="object-cover opacity-70"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,#050507_0%,rgba(5,5,7,0.9)_28%,rgba(5,5,7,0.42)_68%,#050507_100%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(5,5,7,0)_0%,#050507_95%)]" />

        <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 22 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="max-w-3xl"
          >
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-xs text-slate-300 backdrop-blur-xl">
              <Sparkles className="h-3.5 w-3.5 text-sky-200" />
              Persistent cinematic universe engine
            </div>
            <h1 className="text-balance text-5xl font-semibold tracking-[-0.03em] text-white sm:text-6xl lg:text-8xl">
              Universe Studio
            </h1>
            <p className="mt-6 max-w-2xl text-balance text-xl leading-8 text-slate-200 sm:text-2xl">
              Create worlds, not clips.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <ButtonLink href="/universes/new" size="lg">
                Create Universe
              </ButtonLink>
              <ButtonLink href="#demo" variant="secondary" size="lg">
                View Demo
              </ButtonLink>
            </div>
          </motion.div>
        </div>
      </section>

      <main>
        <section id="problem" className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <SectionHeader
              eyebrow="The gap"
              title="Most AI tools create isolated clips."
              description="They can render a moment, but the next prompt starts cold. Characters forget, relationships flatten, and timelines collapse into vibes."
            />
            <div className="cinematic-surface rounded-3xl p-6 md:p-8">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5">
                  <p className="text-sm font-medium text-slate-500">Clip tools</p>
                  <p className="mt-4 text-2xl font-semibold text-white">Prompt in. Clip out.</p>
                  <p className="mt-3 text-sm leading-6 text-slate-400">
                    Each output is detached from the last.
                  </p>
                </div>
                <div className="rounded-2xl border border-sky-300/20 bg-sky-400/10 p-5">
                  <p className="text-sm font-medium text-sky-200">Universe Studio</p>
                  <p className="mt-4 text-2xl font-semibold text-white">History in. Future out.</p>
                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    Every episode begins from persistent world state.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <SectionHeader
              align="center"
              eyebrow="Foundation"
              title="A memory-first studio for cinematic universes."
              description="The product surface is built around continuity: characters, timelines, relationships, events, and alternate futures."
            />
            <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              {features.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section id="demo" className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <SectionHeader
              eyebrow="Demo preview"
              title="Continuity should be visible."
              description="A universe is easier to trust when characters, turning points, and future paths can be scanned at a glance."
            />
            <DemoTimelinePreview />
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-4 text-sm text-slate-500 sm:flex-row">
          <p>Universe Studio</p>
          <p>Create worlds, not clips.</p>
        </div>
      </footer>
    </div>
  );
}
