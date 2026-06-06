"use client";

import { Plus, Sparkles } from "lucide-react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { SectionHeader } from "@/components/common/section-header";
import { DemoModeButton } from "@/components/studio/demo-mode-button";
import { UniverseCard } from "@/components/studio/universe-card";
import { ButtonLink } from "@/components/ui/button";
import { useUniverses } from "@/hooks/use-universes";

export function UniversesDashboard() {
  const { data, isLoading, isError, error } = useUniverses();

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <SectionHeader
          eyebrow="Library"
          title="Universes"
          description="Every world you create becomes a persistent source of truth for future stories."
        />
        <div className="flex flex-wrap gap-3">
          <DemoModeButton size="md" variant="secondary" />
          <ButtonLink href="/universes/new">
            <Plus className="h-4 w-4" />
            Create Universe
          </ButtonLink>
        </div>
      </div>

      <div className="mt-10">
        {isLoading ? <LoadingState label="Loading universes" /> : null}

        {isError ? (
          <ErrorState
            message={
              error instanceof Error
                ? error.message
                : "Unable to load universes from the backend."
            }
          />
        ) : null}

        {!isLoading && !isError && data?.length === 0 ? (
          <EmptyState
            icon={Sparkles}
            title="No universes yet"
            description="Start with a premise, a scene, or a script fragment and give the studio its first world."
            action={
              <div className="flex flex-wrap justify-center gap-3">
                <DemoModeButton size="md" variant="secondary" />
                <ButtonLink href="/universes/new">
                  <Plus className="h-4 w-4" />
                  Create Universe
                </ButtonLink>
              </div>
            }
          />
        ) : null}

        {!isLoading && !isError && data && data.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.map((universe) => (
              <UniverseCard key={universe.id} universe={universe} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
