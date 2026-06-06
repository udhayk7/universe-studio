import type { LucideIcon } from "lucide-react";
import { Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  icon: Icon = Sparkles,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "cinematic-surface relative flex min-h-80 flex-col items-center justify-center overflow-hidden rounded-2xl p-6 text-center sm:p-8",
        className,
      )}
    >
      <div className="absolute inset-0 studio-grid opacity-25" />
      <div className="relative z-10 mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.06] text-sky-200 shadow-[0_0_36px_rgba(56,189,248,0.12)]">
        <Icon className="h-5 w-5" />
      </div>
      <h2 className="relative z-10 text-balance text-xl font-semibold text-white">{title}</h2>
      <p className="relative z-10 mt-2 max-w-md text-sm leading-6 text-slate-400">
        {description}
      </p>
      {action ? <div className="relative z-10 mt-6 flex flex-wrap justify-center gap-3">{action}</div> : null}
    </div>
  );
}
