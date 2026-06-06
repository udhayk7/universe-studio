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
        "cinematic-surface flex min-h-80 flex-col items-center justify-center rounded-2xl p-8 text-center",
        className,
      )}
    >
      <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-full border border-white/10 bg-white/[0.06] text-sky-200">
        <Icon className="h-5 w-5" />
      </div>
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
