"use client";

import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Box,
  CalendarDays,
  CircleDot,
  GitBranch,
  MapPin,
  Network,
  Search,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { ButtonLink } from "@/components/ui/button";
import {
  useUniverseEvents,
  useUniverseGraph,
  useUniverseMemoryOverview,
  useUniverseRelationships,
} from "@/hooks/use-universes";
import { cn } from "@/lib/utils";
import type {
  MemoryEvent,
  MemoryGraphEdge,
  MemoryGraphNode,
  MemoryNodeType,
  MemoryRelationship,
  UniverseMemoryStats,
} from "@/types/universe";

type ExplorerTab = "graph" | "timeline" | "relationships";
type ExplorerNodeData = MemoryGraphNode & {
  active: boolean;
};
type ExplorerNode = Node<ExplorerNodeData>;

const nodeTypeLabels: Record<MemoryNodeType, string> = {
  character: "Characters",
  event: "Events",
  location: "Locations",
  object: "Objects",
};

const nodeTypeIcons: Record<MemoryNodeType, LucideIcon> = {
  character: Users,
  event: CalendarDays,
  location: MapPin,
  object: Box,
};

const edgePalette: Record<string, { color: string; dash?: string; animated?: boolean }> = {
  KNOWS: { color: "#38bdf8" },
  LOVES: { color: "#fb7185", animated: true },
  BETRAYED: { color: "#f43f5e", dash: "6 5" },
  ALLIED_WITH: { color: "#34d399" },
  PARTICIPATED_IN: { color: "#a78bfa" },
  OCCURRED_AT: { color: "#f59e0b" },
  OWNS: { color: "#f8fafc" },
};

const nodeTypes = {
  character: MemoryFlowNode,
  event: MemoryFlowNode,
  location: MemoryFlowNode,
  object: MemoryFlowNode,
};

const explorerTabs: Array<{ value: ExplorerTab; label: string; icon: LucideIcon }> = [
  { value: "graph", label: "Graph", icon: Network },
  { value: "timeline", label: "Timeline", icon: CalendarDays },
  { value: "relationships", label: "Relationships", icon: GitBranch },
];

export function UniverseMemoryExplorer({ universeId }: { universeId: string }) {
  const overviewQuery = useUniverseMemoryOverview(universeId);
  const graphQuery = useUniverseGraph(universeId);
  const eventsQuery = useUniverseEvents(universeId);
  const relationshipsQuery = useUniverseRelationships(universeId);
  const [activeTab, setActiveTab] = useState<ExplorerTab>("graph");
  const [search, setSearch] = useState("");
  const [enabledNodeTypes, setEnabledNodeTypes] = useState<Set<MemoryNodeType>>(
    () => new Set(["character", "event", "location", "object"]),
  );
  const [enabledEdgeTypes, setEnabledEdgeTypes] = useState<Set<string> | null>(null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  const graph = graphQuery.data;
  const edgeTypes = useMemo(
    () => Array.from(new Set((graph?.edges ?? []).map((edge) => edge.type))).sort(),
    [graph],
  );
  const activeEdgeTypes = useMemo(
    () => enabledEdgeTypes ?? new Set(edgeTypes),
    [edgeTypes, enabledEdgeTypes],
  );
  const focusedNode = graph?.nodes.find((node) => node.id === focusedNodeId) ?? null;

  const { nodes, edges } = useMemo(
    () =>
      buildFlowElements({
        graphNodes: graph?.nodes ?? [],
        graphEdges: graph?.edges ?? [],
        search,
        enabledNodeTypes,
        enabledEdgeTypes: activeEdgeTypes,
        focusedNodeId,
      }),
    [activeEdgeTypes, enabledNodeTypes, focusedNodeId, graph, search],
  );

  const isLoading = overviewQuery.isLoading || graphQuery.isLoading;
  const isError = overviewQuery.isError || graphQuery.isError;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl">
        <LoadingState label="Opening memory graph" />
      </div>
    );
  }

  if (isError || !overviewQuery.data || !graph) {
    return (
      <div className="mx-auto max-w-7xl">
        <ErrorState
          message={
            overviewQuery.error instanceof Error
              ? overviewQuery.error.message
              : graphQuery.error instanceof Error
                ? graphQuery.error.message
                : "Unable to open memory explorer."
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1500px]">
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <ButtonLink href={`/universes/${universeId}`} variant="secondary" size="sm">
            <ArrowLeft className="h-4 w-4" />
            Back to universe
          </ButtonLink>
          <p className="mt-6 text-xs uppercase tracking-[0.28em] text-sky-200">Memory Hub</p>
          <h1 className="mt-2 text-balance text-4xl font-semibold tracking-[-0.025em] text-white md:text-6xl">
            Universe Memory Explorer
          </h1>
        </div>
        <div className="inline-flex rounded-2xl border border-white/10 bg-white/[0.04] p-1">
          {explorerTabs.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => setActiveTab(value)}
              className={cn(
                "flex h-10 items-center gap-2 rounded-xl px-4 text-sm transition",
                activeTab === value
                  ? "bg-white text-black"
                  : "text-slate-400 hover:bg-white/[0.06] hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <StatsPanel stats={overviewQuery.data.stats} />

      {activeTab === "graph" ? (
        <section className="mt-5 grid gap-4 xl:grid-cols-[320px_1fr]">
          <div className="grid gap-4">
            <GraphControls
              search={search}
              setSearch={setSearch}
              enabledNodeTypes={enabledNodeTypes}
              setEnabledNodeTypes={setEnabledNodeTypes}
              edgeTypes={edgeTypes}
              enabledEdgeTypes={activeEdgeTypes}
              setEnabledEdgeTypes={setEnabledEdgeTypes}
            />
            <FocusPanel node={focusedNode} source={graph.source} warnings={graph.warnings} />
          </div>
          <div className="h-[720px] overflow-hidden rounded-3xl border border-white/10 bg-[#050507]">
            {nodes.length > 0 ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                minZoom={0.25}
                maxZoom={1.75}
                onNodeClick={(_, node) => setFocusedNodeId(node.id)}
                proOptions={{ hideAttribution: true }}
              >
                <Background color="rgba(148,163,184,0.16)" gap={28} />
                <Controls position="bottom-left" />
              </ReactFlow>
            ) : (
              <EmptyState
                icon={Network}
                title="No graph nodes"
                description="Memory nodes will appear after extraction syncs to the graph."
                className="h-full rounded-none border-0"
              />
            )}
          </div>
        </section>
      ) : null}

      {activeTab === "timeline" ? (
        <EventTimeline events={eventsQuery.data ?? []} isLoading={eventsQuery.isLoading} />
      ) : null}

      {activeTab === "relationships" ? (
        <RelationshipMatrix
          relationships={relationshipsQuery.data ?? []}
          isLoading={relationshipsQuery.isLoading}
        />
      ) : null}
    </div>
  );
}

function MemoryFlowNode({ data }: NodeProps<ExplorerNode>) {
  const Icon = nodeTypeIcons[data.type];
  return (
    <div
      className={cn(
        "min-w-56 rounded-2xl border bg-black/75 p-4 shadow-[0_18px_55px_rgba(0,0,0,0.38)] backdrop-blur-md",
        data.active ? "border-white/35" : "border-white/10",
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-white/70" />
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border"
          style={{
            borderColor: `${nodeColor(data.type)}55`,
            color: nodeColor(data.type),
            background: `${nodeColor(data.type)}18`,
          }}
        >
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="line-clamp-2 text-sm font-semibold leading-5 text-white">{data.label}</p>
          {data.subtitle ? <p className="mt-1 text-xs text-slate-400">{data.subtitle}</p> : null}
        </div>
      </div>
      <NodeMetadata data={data} />
      <Handle type="source" position={Position.Right} className="!bg-white/70" />
    </div>
  );
}

function NodeMetadata({ data }: { data: ExplorerNodeData }) {
  if (data.type === "character") {
    return (
      <p className="mt-3 text-xs text-slate-500">
        {String(data.properties.relationship_count ?? 0)} relationships
      </p>
    );
  }
  if (data.type === "event") {
    return (
      <p className="mt-3 text-xs text-slate-500">
        importance {String(data.properties.importance ?? "n/a")} ·{" "}
        {String(data.properties.participant_count ?? 0)} participants
      </p>
    );
  }
  return null;
}

function StatsPanel({ stats }: { stats: UniverseMemoryStats }) {
  const items: Array<[string, number, LucideIcon]> = [
    ["Characters", stats.characters, Users],
    ["Locations", stats.locations, MapPin],
    ["Events", stats.events, CalendarDays],
    ["Objects", stats.objects, Box],
    ["Relationships", stats.relationships, GitBranch],
    ["Memory Entries", stats.memory_entries, Sparkles],
    ["Timelines", stats.timelines, Network],
  ];

  return (
    <section className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
      {items.map(([label, value, Icon]) => (
        <div key={label as string} className="cinematic-surface rounded-2xl p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label as string}</p>
            <Icon className="h-4 w-4 text-sky-200" />
          </div>
          <p className="mt-3 text-2xl font-semibold text-white">{value as number}</p>
        </div>
      ))}
    </section>
  );
}

function GraphControls({
  search,
  setSearch,
  enabledNodeTypes,
  setEnabledNodeTypes,
  edgeTypes,
  enabledEdgeTypes,
  setEnabledEdgeTypes,
}: {
  search: string;
  setSearch: (value: string) => void;
  enabledNodeTypes: Set<MemoryNodeType>;
  setEnabledNodeTypes: (value: Set<MemoryNodeType>) => void;
  edgeTypes: string[];
  enabledEdgeTypes: Set<string>;
  setEnabledEdgeTypes: (value: Set<string> | null) => void;
}) {
  return (
    <aside className="cinematic-surface rounded-3xl p-5">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-500" />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search memory"
          className="h-11 w-full rounded-2xl border border-white/10 bg-black/35 pl-10 pr-4 text-sm text-white outline-none placeholder:text-slate-600 focus:border-sky-300/40"
        />
      </div>

      <FilterGroup title="Nodes">
        {(Object.keys(nodeTypeLabels) as MemoryNodeType[]).map((type) => (
          <FilterButton
            key={type}
            active={enabledNodeTypes.has(type)}
            label={nodeTypeLabels[type]}
            color={nodeColor(type)}
            onClick={() => {
              const next = new Set(enabledNodeTypes);
              if (next.has(type)) next.delete(type);
              else next.add(type);
              setEnabledNodeTypes(next);
            }}
          />
        ))}
      </FilterGroup>

      <FilterGroup title="Relationships">
        {edgeTypes.map((type) => (
          <FilterButton
            key={type}
            active={enabledEdgeTypes.has(type)}
            label={type.replaceAll("_", " ")}
            color={edgePalette[type]?.color ?? "#94a3b8"}
            onClick={() => {
              const next = new Set(enabledEdgeTypes);
              if (next.has(type)) next.delete(type);
              else next.add(type);
              setEnabledEdgeTypes(next);
            }}
          />
        ))}
        <button
          type="button"
          onClick={() => setEnabledEdgeTypes(null)}
          className="mt-2 text-xs text-slate-500 transition hover:text-white"
        >
          Reset relationship filters
        </button>
      </FilterGroup>
    </aside>
  );
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-6">
      <p className="mb-3 text-xs uppercase tracking-[0.22em] text-slate-500">{title}</p>
      <div className="grid gap-2">{children}</div>
    </div>
  );
}

function FilterButton({
  active,
  label,
  color,
  onClick,
}: {
  active: boolean;
  label: string;
  color: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition",
        active
          ? "border-white/15 bg-white/[0.08] text-white"
          : "border-white/8 bg-black/20 text-slate-500",
      )}
    >
      <span>{label}</span>
      <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
    </button>
  );
}

function FocusPanel({
  node,
  source,
  warnings,
}: {
  node: MemoryGraphNode | null;
  source: string;
  warnings: string[];
}) {
  return (
    <aside className="cinematic-surface rounded-3xl p-5">
      <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Focus</p>
      {node ? (
        <div className="mt-5">
          <div className="flex items-center gap-3">
            <span
              className="flex h-11 w-11 items-center justify-center rounded-xl border"
              style={{
                borderColor: `${nodeColor(node.type)}55`,
                color: nodeColor(node.type),
                background: `${nodeColor(node.type)}18`,
              }}
            >
              <CircleDot className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-white">{node.label}</h2>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                {node.type}
              </p>
            </div>
          </div>
          <div className="mt-5 grid gap-3">
            {Object.entries(node.properties)
              .filter(([, value]) => value !== null && value !== undefined && value !== "")
              .slice(0, 8)
              .map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-white/10 bg-black/25 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-600">
                    {key.replaceAll("_", " ")}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-200">
                    {Array.isArray(value) ? value.join(", ") : String(value)}
                  </p>
                </div>
              ))}
          </div>
        </div>
      ) : (
        <p className="mt-5 text-sm leading-6 text-slate-500">Select a node to inspect it.</p>
      )}
      <div className="mt-6 rounded-2xl border border-white/10 bg-black/25 p-3 text-xs text-slate-500">
        Graph source: {source}
      </div>
      {warnings.map((warning) => (
        <div key={warning} className="mt-3 rounded-2xl border border-amber-300/15 bg-amber-300/[0.06] p-3 text-xs text-amber-100">
          {warning}
        </div>
      ))}
    </aside>
  );
}

function EventTimeline({ events, isLoading }: { events: MemoryEvent[]; isLoading: boolean }) {
  if (isLoading) return <LoadingState className="mt-5" label="Loading events" />;
  if (events.length === 0) {
    return (
      <EmptyState
        className="mt-5"
        icon={CalendarDays}
        title="No events yet"
        description="Extracted events will appear in chronological order."
      />
    );
  }

  return (
    <section className="mt-5 cinematic-surface rounded-3xl p-5 md:p-8">
      <div className="relative grid gap-5 pl-6 before:absolute before:left-2 before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-white/10">
        {events.map((event) => (
          <motion.article
            key={event.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative rounded-2xl border border-white/10 bg-black/25 p-5"
          >
            <span className="absolute -left-[1.85rem] top-6 flex h-4 w-4 rounded-full border border-sky-200/40 bg-sky-300/20" />
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">{event.title}</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                  {event.summary || "No event summary recorded."}
                </p>
              </div>
              {event.importance ? (
                <span className="rounded-full border border-amber-300/15 bg-amber-300/[0.06] px-3 py-1 text-xs text-amber-100">
                  importance {event.importance}
                </span>
              ) : null}
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-300">
              {event.location_name ? (
                <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1">
                  {event.location_name}
                </span>
              ) : null}
              {event.participants.map((participant) => (
                <span key={participant.id} className="rounded-full border border-sky-300/15 bg-sky-300/[0.06] px-3 py-1 text-sky-100">
                  {participant.name}
                </span>
              ))}
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  );
}

function RelationshipMatrix({
  relationships,
  isLoading,
}: {
  relationships: MemoryRelationship[];
  isLoading: boolean;
}) {
  if (isLoading) return <LoadingState className="mt-5" label="Loading relationships" />;
  if (relationships.length === 0) {
    return (
      <EmptyState
        className="mt-5"
        icon={GitBranch}
        title="No relationships yet"
        description="Character relationships will appear as the universe grows."
      />
    );
  }

  return (
    <section className="mt-5 cinematic-surface rounded-3xl p-5 md:p-8">
      <div className="grid gap-3">
        {relationships.map((relationship) => {
          const strength = relationship.strength ?? 0;
          const positive = strength >= 0;
          return (
            <div
              key={relationship.id}
              className="grid gap-4 rounded-2xl border border-white/10 bg-black/25 p-4 lg:grid-cols-[1fr_0.9fr_1fr]"
            >
              <MatrixPerson name={relationship.source_character_name} label="Source" />
              <div>
                <p className="text-center text-xs uppercase tracking-[0.2em] text-slate-500">
                  {relationship.relationship_type.replaceAll("_", " ")}
                </p>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                  <div
                    className={cn("h-full rounded-full", positive ? "bg-emerald-300" : "bg-rose-300")}
                    style={{ width: `${Math.min(Math.abs(strength), 100)}%` }}
                  />
                </div>
                <p className="mt-2 text-center text-sm font-semibold text-white">{strength}</p>
              </div>
              <MatrixPerson name={relationship.target_character_name} label="Target" />
            </div>
          );
        })}
      </div>
    </section>
  );
}

function MatrixPerson({ name, label }: { name: string; label: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-white">{name}</p>
    </div>
  );
}

function buildFlowElements({
  graphNodes,
  graphEdges,
  search,
  enabledNodeTypes,
  enabledEdgeTypes,
  focusedNodeId,
}: {
  graphNodes: MemoryGraphNode[];
  graphEdges: MemoryGraphEdge[];
  search: string;
  enabledNodeTypes: Set<MemoryNodeType>;
  enabledEdgeTypes: Set<string>;
  focusedNodeId: string | null;
}): { nodes: ExplorerNode[]; edges: Edge[] } {
  const query = search.trim().toLowerCase();
  const counters: Record<MemoryNodeType, number> = {
    character: 0,
    event: 0,
    location: 0,
    object: 0,
  };
  const xByType: Record<MemoryNodeType, number> = {
    character: 0,
    event: 320,
    location: 640,
    object: 960,
  };

  const nodes = graphNodes
    .filter((node) => enabledNodeTypes.has(node.type))
    .filter((node) => {
      if (!query) return true;
      const haystack = `${node.label} ${node.subtitle ?? ""} ${Object.values(node.properties).join(" ")}`;
      return haystack.toLowerCase().includes(query);
    })
    .map((node) => {
      const index = counters[node.type]++;
      return {
        id: node.id,
        type: node.type,
        position: {
          x: xByType[node.type],
          y: index * 138,
        },
        data: {
          ...node,
          active: focusedNodeId === node.id,
        },
      };
    });

  const visibleNodeIds = new Set(nodes.map((node) => node.id));
  const edges = graphEdges
    .filter((edge) => enabledEdgeTypes.has(edge.type))
    .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
    .map((edge) => {
      const style = edgePalette[edge.type] ?? { color: "#94a3b8" };
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: style.animated,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: style.color,
        },
        style: {
          stroke: style.color,
          strokeWidth: edge.strength ? Math.max(1.5, Math.abs(edge.strength) / 30) : 2,
          strokeDasharray: style.dash,
        },
        labelStyle: {
          fill: "#cbd5e1",
          fontSize: 11,
          fontWeight: 600,
        },
        labelBgStyle: {
          fill: "rgba(5,5,7,0.8)",
        },
      };
    });

  return { nodes, edges };
}

function nodeColor(type: MemoryNodeType) {
  return {
    character: "#38bdf8",
    event: "#a78bfa",
    location: "#f59e0b",
    object: "#f8fafc",
  }[type];
}
