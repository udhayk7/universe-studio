"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  GitBranch,
  Globe2,
  Network,
  ShieldCheck,
  Users,
} from "lucide-react";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import { useConsistencyDashboard, useUniverse } from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type { ConsistencyCheck, ConsistencySeverity } from "@/types/universe";

type ConsistencyDashboardProps = {
  universeId: string;
};

const severityOrder: ConsistencySeverity[] = ["critical", "high", "medium", "low"];

const severityClass: Record<ConsistencySeverity, string> = {
  critical: "border-rose-300/25 bg-rose-400/[0.08] text-rose-100",
  high: "border-amber-300/25 bg-amber-300/[0.08] text-amber-100",
  medium: "border-sky-300/25 bg-sky-300/[0.08] text-sky-100",
  low: "border-white/10 bg-white/[0.05] text-slate-200",
};

export function ConsistencyDashboard({ universeId }: ConsistencyDashboardProps) {
  const universeQuery = useUniverse(universeId);
  const dashboardQuery = useConsistencyDashboard(universeId);

  if (universeQuery.isLoading || dashboardQuery.isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Loading continuity system" />
      </div>
    );
  }

  if (universeQuery.isError || !universeQuery.data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            universeQuery.error instanceof Error
              ? universeQuery.error.message
              : "Unable to open this universe."
          }
        />
      </div>
    );
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            dashboardQuery.error instanceof Error
              ? dashboardQuery.error.message
              : "Unable to load consistency dashboard."
          }
        />
      </div>
    );
  }

  const dashboard = dashboardQuery.data;
  const totalIssues = dashboard.open_issues + dashboard.resolved_issues;

  return (
    <div className="mx-auto max-w-7xl">
      <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
        <ArrowLeft className="h-4 w-4" />
        Back to universe
      </ButtonLink>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black/35">
        <div className="studio-grid relative p-6 md:p-10">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(14,165,233,0.16),transparent_42%),linear-gradient(35deg,rgba(244,63,94,0.12),transparent_66%)]" />
          <div className="relative z-10 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.07] text-sky-200">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <p className="text-xs uppercase tracking-[0.28em] text-sky-200">
                Consistency Engine
              </p>
              <h1 className="mt-3 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
                {universeQuery.data.title}
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-7 text-slate-300">
                Continuity issues, branch leakage, world-rule checks, and agent validation
                reports for this universe.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <MetricCard label="Open Issues" value={dashboard.open_issues} tone="warning" />
              <MetricCard label="Resolved" value={dashboard.resolved_issues} tone="success" />
              <MetricCard label="Total Reports" value={totalIssues} tone="neutral" />
              <MetricCard
                label="Critical"
                value={dashboard.severity_breakdown.critical ?? 0}
                tone="danger"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="grid gap-4">
          <div className="cinematic-surface rounded-2xl p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">
              Severity Breakdown
            </p>
            <div className="mt-5 grid gap-3">
              {severityOrder.map((severity) => (
                <SeverityRow
                  key={severity}
                  severity={severity}
                  count={dashboard.severity_breakdown[severity] ?? 0}
                  total={Math.max(totalIssues, 1)}
                />
              ))}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <ConflictCard icon={Users} label="Characters" value={dashboard.character_conflicts} />
            <ConflictCard
              icon={Network}
              label="Relationships"
              value={dashboard.relationship_conflicts}
            />
            <ConflictCard icon={GitBranch} label="Timelines" value={dashboard.timeline_conflicts} />
            <ConflictCard icon={Globe2} label="World Rules" value={dashboard.world_rule_violations} />
          </div>
        </div>

        <IssueList issues={dashboard.issues} />
      </section>
    </div>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "neutral" | "success" | "warning" | "danger";
}) {
  const toneClass = {
    neutral: "text-white",
    success: "text-emerald-100",
    warning: "text-amber-100",
    danger: "text-rose-100",
  }[tone];

  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 p-5">
      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className={cn("mt-3 text-3xl font-semibold tracking-[-0.02em]", toneClass)}>
        {value}
      </p>
    </div>
  );
}

function SeverityRow({
  severity,
  count,
  total,
}: {
  severity: ConsistencySeverity;
  count: number;
  total: number;
}) {
  const width = `${Math.round((count / total) * 100)}%`;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-4 text-sm">
        <span className="capitalize text-slate-300">{severity}</span>
        <span className="text-slate-500">{count}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className={cn(
            "h-full rounded-full",
            severity === "critical"
              ? "bg-rose-300"
              : severity === "high"
                ? "bg-amber-300"
                : severity === "medium"
                  ? "bg-sky-300"
                  : "bg-slate-400",
          )}
          style={{ width }}
        />
      </div>
    </div>
  );
}

function ConflictCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: number;
}) {
  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-black/25 text-sky-200">
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-2xl font-semibold text-white">{value}</p>
      </div>
      <p className="mt-4 text-sm text-slate-400">{label}</p>
    </div>
  );
}

function IssueList({ issues }: { issues: ConsistencyCheck[] }) {
  if (issues.length === 0) {
    return (
      <div className="cinematic-surface rounded-2xl p-8 text-center">
        <CheckCircle2 className="mx-auto h-9 w-9 text-emerald-300" />
        <h2 className="mt-4 text-xl font-semibold text-white">No continuity issues</h2>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">
          Generated episodes that pass validation will keep this panel clear.
        </p>
      </div>
    );
  }

  return (
    <div className="cinematic-surface rounded-2xl p-5">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Issue Queue</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Continuity Reports</h2>
        </div>
        <AlertTriangle className="h-6 w-6 text-amber-200" />
      </div>

      <div className="grid gap-3">
        {issues.map((issue) => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    </div>
  );
}

function IssueCard({ issue }: { issue: ConsistencyCheck }) {
  const severity = severityOrder.includes(issue.severity as ConsistencySeverity)
    ? (issue.severity as ConsistencySeverity)
    : "low";
  const [headline, ...rest] = issue.description.split("\n\n");
  const explanation = rest.join("\n\n").trim();

  return (
    <motion.article
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-black/25 p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded-full border px-3 py-1 text-xs font-medium capitalize",
            severityClass[severity],
          )}
        >
          {issue.severity}
        </span>
        <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
          {issue.issue_type.replace("_", " ")}
        </span>
        <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-slate-400">
          {issue.status}
        </span>
      </div>

      <h3 className="mt-4 text-base font-semibold text-white">{headline}</h3>
      {explanation ? (
        <p className="mt-2 text-sm leading-6 text-slate-400">{explanation}</p>
      ) : null}
      {issue.suggested_fix ? (
        <div className="mt-4 rounded-xl border border-sky-300/15 bg-sky-300/[0.055] p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-sky-100/70">Suggested Fix</p>
          <p className="mt-2 text-sm leading-6 text-sky-50">{issue.suggested_fix}</p>
        </div>
      ) : null}
    </motion.article>
  );
}
