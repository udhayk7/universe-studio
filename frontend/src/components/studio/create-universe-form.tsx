"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Lightbulb,
  Loader2,
  Upload,
  WandSparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { ErrorState } from "@/components/common/error-state";
import { Button } from "@/components/ui/button";
import { useCreateUniverseFromInput, useJob } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import { useStudioStore, type CreateInputMode } from "@/state/studio-store";

const modes: Array<{
  value: CreateInputMode;
  label: string;
  icon: typeof Lightbulb;
}> = [
  { value: "idea", label: "Idea", icon: Lightbulb },
  { value: "script", label: "Script", icon: Upload },
  { value: "scene", label: "Scene", icon: FileText },
];

export function CreateUniverseForm() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const createInputMode = useStudioStore((state) => state.createInputMode);
  const setCreateInputMode = useStudioStore((state) => state.setCreateInputMode);
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");
  const [tone, setTone] = useState("");
  const [idea, setIdea] = useState("A city where memories are currency.");
  const [scene, setScene] = useState("");
  const [scriptFile, setScriptFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const createUniverse = useCreateUniverseFromInput();
  const jobQuery = useJob(jobId);

  const sourceText = useMemo(() => {
    if (createInputMode === "idea") return idea;
    if (createInputMode === "scene") return scene;
    return scriptFile ? `Source file: ${scriptFile.name}` : "";
  }, [createInputMode, idea, scene, scriptFile]);

  const hasSource =
    createInputMode === "script" ? scriptFile !== null : sourceText.trim().length > 0;
  const job = jobQuery.data;
  const isTerminal = job?.status === "completed" || job?.status === "failed";
  const isWorking = createUniverse.isPending || Boolean(jobId && !isTerminal);
  const canSubmit = hasSource && !isWorking;
  const progress = job?.progress ?? (createUniverse.isPending ? 8 : 0);
  const progressMessage =
    job?.message ?? (createUniverse.isPending ? "Starting extraction" : "Ready to extract");

  useEffect(() => {
    if (job?.status === "completed" && job.universe_id) {
      router.push(`/universes/${job.universe_id}`);
    }
  }, [job, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;

    setJobId(null);

    const formData = new FormData();
    formData.append("source_type", createInputMode === "script" ? "screenplay" : createInputMode);
    if (createInputMode === "script" && scriptFile) {
      formData.append("file", scriptFile);
    } else {
      formData.append("content", sourceText.trim());
    }
    if (title.trim()) formData.append("title_hint", title.trim());
    if (genre.trim()) formData.append("genre_hint", genre.trim());
    if (tone.trim()) formData.append("tone_hint", tone.trim());

    const queuedJob = await createUniverse.mutateAsync(formData);
    setJobId(queuedJob.id);
  }

  return (
    <form onSubmit={handleSubmit} className="cinematic-surface rounded-3xl p-5 md:p-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.06] text-sky-200">
            <WandSparkles className="h-5 w-5" />
          </div>
          <h2 className="text-2xl font-semibold tracking-[-0.01em] text-white">
            Shape the first truth.
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Start with the seed material that gives the world its identity, texture, and first
            constraints.
          </p>

          <div className="mt-8 grid gap-4">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-200">Title Hint</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="The Last Observatory"
                className="h-12 rounded-2xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/45"
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-200">Genre</span>
                <input
                  value={genre}
                  onChange={(event) => setGenre(event.target.value)}
                  placeholder="Science fiction"
                  className="h-12 rounded-2xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/45"
                />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-200">Tone</span>
                <input
                  value={tone}
                  onChange={(event) => setTone(event.target.value)}
                  placeholder="Cinematic mystery"
                  className="h-12 rounded-2xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/45"
                />
              </label>
            </div>
          </div>
        </div>

        <div>
          <div className="grid grid-cols-3 rounded-2xl border border-white/10 bg-black/25 p-1">
            {modes.map((mode) => {
              const Icon = mode.icon;
              const active = createInputMode === mode.value;

              return (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setCreateInputMode(mode.value)}
                  className={cn(
                    "flex h-11 items-center justify-center gap-2 rounded-xl text-sm transition",
                    active
                      ? "bg-white text-black"
                      : "text-slate-400 hover:bg-white/[0.06] hover:text-white",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {mode.label}
                </button>
              );
            })}
          </div>

          <div className="mt-5">
            {createInputMode === "idea" ? (
              <motion.label
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid gap-2"
              >
                <span className="text-sm font-medium text-slate-200">Idea</span>
                <textarea
                  value={idea}
                  onChange={(event) => setIdea(event.target.value)}
                  rows={9}
                  className="min-h-64 resize-none rounded-2xl border border-white/10 bg-black/30 p-4 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/45"
                />
              </motion.label>
            ) : null}

            {createInputMode === "script" ? (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.fdx,.fountain"
                  className="hidden"
                  onChange={(event) => setScriptFile(event.target.files?.[0] ?? null)}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex min-h-64 w-full flex-col items-center justify-center rounded-2xl border border-dashed border-white/15 bg-black/30 p-8 text-center transition hover:border-sky-300/35 hover:bg-white/[0.04]"
                >
                  <Upload className="h-8 w-8 text-sky-200" />
                  <span className="mt-4 text-sm font-medium text-white">
                    {scriptFile ? scriptFile.name : "Drop in a screenplay or script"}
                  </span>
                  <span className="mt-2 text-xs text-slate-500">TXT, FDX, Fountain</span>
                </button>
              </motion.div>
            ) : null}

            {createInputMode === "scene" ? (
              <motion.label
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid gap-2"
              >
                <span className="text-sm font-medium text-slate-200">Scene Text</span>
                <textarea
                  value={scene}
                  onChange={(event) => setScene(event.target.value)}
                  placeholder="Paste a scene here."
                  rows={9}
                  className="min-h-64 resize-none rounded-2xl border border-white/10 bg-black/30 p-4 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-sky-300/40 focus:bg-black/45"
                />
              </motion.label>
            ) : null}
          </div>

          {createUniverse.isError ? (
            <ErrorState
              className="mt-5"
              message={
                createUniverse.error instanceof Error
                  ? createUniverse.error.message
                  : "Unable to start extraction."
              }
            />
          ) : null}

          {jobQuery.isError ? (
            <ErrorState
              className="mt-5"
              message={
                jobQuery.error instanceof Error
                  ? jobQuery.error.message
                  : "Unable to read extraction status."
              }
            />
          ) : null}

          {job?.status === "failed" ? (
            <ErrorState
              className="mt-5"
              message={job.message || "Universe extraction failed."}
            />
          ) : null}

          {isWorking || job?.status === "completed" ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-5 rounded-2xl border border-sky-300/15 bg-sky-300/[0.04] p-4"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  {job?.status === "completed" ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-300" />
                  ) : (
                    <Loader2 className="h-5 w-5 animate-spin text-sky-200" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-white">
                      {job?.status === "completed" ? "Extraction complete" : "Extracting universe"}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">{progressMessage}</p>
                  </div>
                </div>
                <span className="text-xs font-medium text-slate-300">{progress}%</span>
              </div>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-sky-300 to-violet-300 transition-all duration-500"
                  style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
                />
              </div>
            </motion.div>
          ) : null}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-500">
              Status: {isWorking ? "extracting universe memory" : "ready for source"}
            </p>
            <Button type="submit" disabled={!canSubmit}>
              {isWorking ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
              {isWorking ? "Creating Universe" : "Create Universe"}
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}
