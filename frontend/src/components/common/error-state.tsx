import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type ErrorStateProps = {
  title?: string;
  message: string;
  className?: string;
};

export function ErrorState({
  title = "Something drifted off course",
  message,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-rose-400/20 bg-rose-500/10 p-5 text-rose-100",
        className,
      )}
    >
      <div className="flex gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <h3 className="font-medium">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-rose-100/80">{message}</p>
        </div>
      </div>
    </div>
  );
}
