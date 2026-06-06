import { cn } from "@/lib/utils";

type LoadingStateProps = {
  label?: string;
  detail?: string;
  className?: string;
};

export function LoadingState({
  label = "Loading",
  detail = "Synchronizing universe memory",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "cinematic-surface relative flex min-h-56 items-center justify-center overflow-hidden rounded-2xl p-6 sm:p-8",
        className,
      )}
    >
      <div className="absolute inset-0 studio-grid opacity-35" />
      <div className="relative z-10 flex max-w-md flex-col items-center text-center">
        <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-300/20 bg-sky-300/[0.08]">
          <span className="absolute h-12 w-12 animate-ping rounded-2xl border border-sky-300/30" />
          <span className="h-3 w-3 rounded-full bg-sky-200 shadow-[0_0_28px_rgba(125,211,252,0.85)]" />
        </div>
        <p className="mt-5 text-sm font-medium text-white">{label}</p>
        <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p>
      </div>
    </div>
  );
}
