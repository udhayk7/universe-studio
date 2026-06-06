"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  Camera,
  Clock,
  Film,
  Images,
  MapPin,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { Button, ButtonLink } from "@/components/ui/button";
import { useEpisodeStoryboard, useRenderEpisodeStoryboard } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type { Shot, StoryboardImage, StoryboardScene } from "@/types/universe";

type StoryboardViewerProps = {
  universeId: string;
  episodeId: string;
};

export function StoryboardViewer({ universeId, episodeId }: StoryboardViewerProps) {
  const storyboardQuery = useEpisodeStoryboard(episodeId);
  const renderMutation = useRenderEpisodeStoryboard(episodeId);

  if (storyboardQuery.isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Loading storyboard" />
      </div>
    );
  }

  if (storyboardQuery.isError || !storyboardQuery.data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            storyboardQuery.error instanceof Error
              ? storyboardQuery.error.message
              : "Unable to open storyboard."
          }
        />
      </div>
    );
  }

  const storyboard = renderMutation.data ?? storyboardQuery.data;
  const hasShots = storyboard.shot_count > 0;
  const isRendering = renderMutation.isPending;

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ButtonLink href={`/universes/${universeId}/episodes/${episodeId}`} variant="secondary" size="sm">
          <ArrowLeft className="h-4 w-4" />
          Back to episode
        </ButtonLink>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant={hasShots ? "secondary" : "primary"}
            size="sm"
            disabled={isRendering}
            onClick={() => renderMutation.mutate({ regenerate_images: false })}
          >
            {isRendering ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {hasShots ? "Render Missing" : "Render Storyboard"}
          </Button>
          {hasShots ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isRendering}
              onClick={() => renderMutation.mutate({ regenerate_images: true })}
            >
              <RefreshCw className={cn("h-4 w-4", isRendering && "animate-spin")} />
              Regenerate
            </Button>
          ) : null}
        </div>
      </div>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/40">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(115deg,rgba(14,165,233,0.16),transparent_42%),linear-gradient(35deg,rgba(168,85,247,0.18),transparent_60%)]" />
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/35 px-3 py-1.5 text-xs text-slate-300">
              <Film className="h-3.5 w-3.5 text-sky-200" />
              {storyboard.scene_count} scenes · {storyboard.shot_count} shots ·{" "}
              {storyboard.generated_image_count} frames
            </div>
            <h1 className="mt-5 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
              {storyboard.title}
            </h1>
            {storyboard.summary ? (
              <p className="mt-5 max-w-4xl text-base leading-7 text-slate-300">
                {storyboard.summary}
              </p>
            ) : null}
          </div>
        </div>
      </section>

      {renderMutation.isError ? (
        <div className="mt-5">
          <ErrorState
            message={
              renderMutation.error instanceof Error
                ? renderMutation.error.message
                : "Unable to render storyboard."
            }
          />
        </div>
      ) : null}

      {hasShots ? (
        <section className="mt-6 grid gap-6">
          {storyboard.scenes.map((scene) => (
            <StoryboardScenePanel key={scene.scene_id} universeId={universeId} scene={scene} />
          ))}
        </section>
      ) : (
        <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.04] p-10 text-center">
          <Images className="mx-auto h-10 w-10 text-slate-500" />
          <h2 className="mt-4 text-2xl font-semibold text-white">Storyboard not rendered</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
            Create the visual shot board for this episode.
          </p>
        </section>
      )}
    </div>
  );
}

function StoryboardScenePanel({
  universeId,
  scene,
}: {
  universeId: string;
  scene: StoryboardScene;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-3xl border border-white/10 bg-black/35"
    >
      <div className="border-b border-white/10 bg-white/[0.035] p-5 md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
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
                key={`${scene.scene_id}-${participant.character_id}`}
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

      <div className="grid gap-5 p-5 md:p-6">
        {scene.shots.map((shot) => (
          <ShotCard key={shot.id} shot={shot} />
        ))}
      </div>
    </motion.article>
  );
}

function ShotCard({ shot }: { shot: Shot }) {
  const image = shot.storyboard_image;
  const imageSrc = getStoryboardImageSrc(image);

  return (
    <div className="grid overflow-hidden rounded-2xl border border-white/10 bg-white/[0.035] lg:grid-cols-[1.25fr_0.75fr]">
      <div
        role="img"
        aria-label={shot.visual_description}
        className={cn(
          "min-h-[320px] bg-cover bg-center md:min-h-[460px]",
          !imageSrc && "bg-[radial-gradient(circle_at_30%_20%,rgba(56,189,248,0.24),transparent_32%),linear-gradient(135deg,#020617,#111827_52%,#312e81)]",
        )}
        style={imageSrc ? { backgroundImage: `url(${imageSrc})` } : undefined}
      >
        {!imageSrc ? (
          <div className="flex h-full min-h-[320px] items-center justify-center text-slate-500 md:min-h-[460px]">
            <Images className="h-10 w-10" />
          </div>
        ) : null}
      </div>

      <div className="flex flex-col justify-between gap-5 p-5">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1">
              Shot {shot.shot_number}
            </span>
            <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1">
              {image?.status || shot.status}
            </span>
          </div>
          <h3 className="mt-4 text-xl font-semibold tracking-[-0.015em] text-white">
            {shot.shot_type}
          </h3>
          <p className="mt-3 text-sm leading-6 text-slate-300">{shot.visual_description}</p>
        </div>

        <div className="grid gap-3">
          <ShotMeta icon={Camera} label="Camera" value={shot.camera_angle} />
          <ShotMeta icon={Clock} label="Duration" value={`${shot.duration_seconds}s`} />
          <ShotMeta
            icon={Film}
            label="Provider"
            value={image ? `${image.provider}${image.model ? ` · ${image.model}` : ""}` : "Pending"}
          />
          {image?.error ? (
            <div className="rounded-2xl border border-amber-300/20 bg-amber-300/[0.06] p-3">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-amber-100/80">
                <AlertTriangle className="h-3.5 w-3.5" />
                Notice
              </div>
              <p className="mt-2 text-xs leading-5 text-amber-50/85">{image.error}</p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ShotMeta({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Camera;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 p-3">
      <Icon className="h-4 w-4 text-sky-200" />
      <div>
        <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
        <p className="mt-1 text-sm text-slate-200">{value}</p>
      </div>
    </div>
  );
}

function getStoryboardImageSrc(image: StoryboardImage | null) {
  if (!image) return null;
  if (image.image_url) return image.image_url;
  if (image.image_data && image.mime_type) {
    return `data:${image.mime_type};base64,${image.image_data}`;
  }
  return null;
}
