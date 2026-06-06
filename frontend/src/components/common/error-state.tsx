import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type ErrorStateProps = {
  title?: string;
  message: string;
  detail?: string;
  className?: string;
};

export function ErrorState({
  title = "Connection needs attention",
  message,
  detail = "Check that the FastAPI backend is running and the environment variables are configured.",
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-rose-400/20 bg-rose-500/10 text-rose-100",
        className,
      )}
    >
      <div className="flex gap-3 p-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-rose-300/20 bg-rose-300/[0.08]">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <div>
          <h3 className="font-medium">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-rose-100/80">{message}</p>
          <p className="mt-2 text-xs leading-5 text-rose-100/55">{detail}</p>
        </div>
      </div>
    </div>
  );
}
