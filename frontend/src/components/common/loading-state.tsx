import { cn } from "@/lib/utils";

type LoadingStateProps = {
  label?: string;
  className?: string;
};

export function LoadingState({ label = "Loading", className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        "cinematic-surface flex min-h-56 items-center justify-center rounded-2xl p-8",
        className,
      )}
    >
      <div className="flex items-center gap-3 text-sm text-slate-300">
        <span className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-300 opacity-60" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-300" />
        </span>
        {label}
      </div>
    </div>
  );
}
