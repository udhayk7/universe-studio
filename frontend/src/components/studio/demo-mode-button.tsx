"use client";

import { Loader2, Play, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useSetupDemo } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";

type DemoModeButtonProps = {
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
  showError?: boolean;
};

export function DemoModeButton({
  size = "lg",
  variant = "secondary",
  className,
  showError = true,
}: DemoModeButtonProps) {
  const router = useRouter();
  const setupDemo = useSetupDemo();

  async function handleClick() {
    const result = await setupDemo.mutateAsync();
    router.push(`/universes/${result.universe_id}`);
  }

  return (
    <div className={cn("flex w-full flex-col gap-2 sm:inline-flex sm:w-auto", className)}>
      <Button
        type="button"
        size={size}
        variant={variant}
        onClick={handleClick}
        disabled={setupDemo.isPending}
        className="w-full sm:w-auto"
      >
        {setupDemo.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        {setupDemo.isPending ? "Preparing Demo" : "Demo Mode"}
        {!setupDemo.isPending ? <Sparkles className="h-4 w-4" /> : null}
      </Button>
      {showError && setupDemo.isError ? (
        <p className="max-w-80 text-xs leading-5 text-rose-200">
          {setupDemo.error instanceof Error
            ? setupDemo.error.message
            : "Unable to set up the demo universe."}
        </p>
      ) : null}
    </div>
  );
}
