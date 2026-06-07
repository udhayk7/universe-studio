export type Universe = {
  id: string;
  owner_id: string | null;
  active_timeline_id: string | null;
  title: string;
  tagline: string | null;
  premise: string | null;
  genre: string | null;
  tone: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CreateUniversePayload = {
  title: string;
  tagline?: string | null;
  premise?: string | null;
  genre?: string | null;
  tone?: string | null;
  status?: string;
};

export type UniverseJob = {
  id: string;
  universe_id: string | null;
  job_type: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  progress: number;
  message: string | null;
  result_data: Record<string, unknown>;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ConsistencySeverity = "low" | "medium" | "high" | "blocker" | "critical";

export type ConsistencyStatus = "open" | "resolved" | "ignored" | string;

export type ConsistencyCheck = {
  id: string;
  universe_id: string;
  timeline_id: string;
  episode_id: string | null;
  severity: ConsistencySeverity | string;
  issue_type: string;
  description: string;
  suggested_fix: string | null;
  affected_entities: Array<Record<string, unknown>>;
  status: ConsistencyStatus;
  created_at: string;
  updated_at: string;
};

export type ConsistencyAffectedEntity = {
  entity_type?: string;
  entity_id?: string;
  name?: string;
};

export type ConsistencyIssueResult = {
  severity?: ConsistencySeverity | string;
  issue_type?: string;
  issue?: string;
  explanation?: string;
  suggested_fix?: string | null;
  affected_entities?: ConsistencyAffectedEntity[];
};

export type ConsistencyDashboard = {
  universe_id: string;
  open_issues: number;
  resolved_issues: number;
  severity_breakdown: Record<ConsistencySeverity, number>;
  timeline_conflicts: number;
  character_conflicts: number;
  relationship_conflicts: number;
  world_rule_violations: number;
  branch_conflicts: number;
  issues: ConsistencyCheck[];
};

export type AgentTraceStep = {
  id: string;
  universe_id: string | null;
  job_id: string | null;
  episode_id: string | null;
  agent_name: string;
  input_summary: string | null;
  output_summary: string | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  created_at: string;
  updated_at: string;
};

export type AgentTrace = {
  trace_id: string | null;
  episode_id: string | null;
  job_id: string | null;
  steps: AgentTraceStep[];
};

export type DemoSeedSummary = {
  characters: number;
  locations: number;
  objects: number;
  relationships: number;
  events: number;
  memory_entries: number;
  timelines: number;
  episodes: number;
  scenes: number;
  agent_runs: number;
  consistency_checks: number;
};

export type DemoSeedResult = {
  universe_id: string;
  timeline_a_id: string;
  timeline_b_id: string;
  timeline_a_name: string;
  timeline_b_name: string;
  episode_ids: string[];
  branch_event_id: string;
  alternate_future_episode_id: string;
  summary: DemoSeedSummary;
  neo4j_synced: boolean;
  neo4j_message: string | null;
};

export type Character = {
  id: string;
  universe_id: string;
  canonical_name: string;
  aliases: string[];
  description: string | null;
  traits: Record<string, unknown>;
  goals: Record<string, unknown>;
  fears: Record<string, unknown>;
  voice_style: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CharacterMemoryEntry = {
  id: string;
  universe_id: string;
  timeline_id: string;
  commit_id: string;
  entity_type: string;
  entity_id: string | null;
  memory_type: string;
  content: string;
  structured_value: Record<string, unknown>;
  confidence: number | null;
  source: string;
  valid_from_event_id: string | null;
  valid_to_event_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CharacterRelationship = {
  id: string;
  universe_id: string;
  timeline_id: string;
  source_character_id: string;
  source_character_name: string;
  target_character_id: string;
  target_character_name: string;
  direction: string;
  relationship_type: string;
  strength: number | null;
  status: string;
  evidence: string | null;
  confidence: number | null;
  created_at: string;
  updated_at: string;
};

export type CharacterArcEvent = {
  event_id: string;
  title: string;
  summary: string | null;
  importance: number | null;
  order_index: number | null;
  location_name: string | null;
  memory_id: string | null;
  source: string;
  created_at: string | null;
};

export type CharacterContextPack = {
  character: Character;
  goals: string[];
  fears: string[];
  traits: string[];
  relationships: CharacterRelationship[];
  important_memories: CharacterMemoryEntry[];
  knowledge: CharacterMemoryEntry[];
  emotional_state: string | null;
  current_status: string;
  arc: CharacterArcEvent[];
};

export type UniverseMemoryStats = {
  characters: number;
  locations: number;
  events: number;
  objects: number;
  relationships: number;
  memory_entries: number;
  timelines: number;
};

export type UniverseMemoryOverview = {
  universe_id: string;
  stats: UniverseMemoryStats;
};

export type MemoryNodeType = "character" | "event" | "location" | "object";

export type MemoryGraphNode = {
  id: string;
  type: MemoryNodeType;
  label: string;
  subtitle: string | null;
  properties: Record<string, unknown>;
};

export type MemoryGraphEdge = {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
  strength: number | null;
  properties: Record<string, unknown>;
};

export type UniverseGraph = {
  universe_id: string;
  source: string;
  nodes: MemoryGraphNode[];
  edges: MemoryGraphEdge[];
  warnings: string[];
};

export type MemoryParticipant = {
  id: string;
  name: string;
};

export type MemoryEvent = {
  id: string;
  title: string;
  summary: string | null;
  importance: number | null;
  order_index: number | null;
  location_id: string | null;
  location_name: string | null;
  participants: MemoryParticipant[];
};

export type MemoryRelationship = {
  id: string;
  source_character_id: string;
  source_character_name: string;
  target_character_id: string;
  target_character_name: string;
  relationship_type: string;
  strength: number | null;
  status: string;
  evidence: string | null;
};

export type MemoryLocation = {
  id: string;
  name: string;
  description: string | null;
  location_type: string | null;
};

export type MemoryObject = {
  id: string;
  name: string;
  description: string | null;
  object_type: string | null;
  status: string;
  current_owner_character_id: string | null;
  current_location_id: string | null;
};

export type EpisodeGeneratePayload = {
  prompt?: string | null;
};

export type Episode = {
  id: string;
  universe_id: string;
  timeline_id: string;
  commit_id: string | null;
  title: string;
  logline: string | null;
  summary: string | null;
  status: string;
  scene_count: number;
  created_at: string;
  updated_at: string;
};

export type EpisodeParticipant = {
  character_id: string;
  character_name: string;
  role: string;
};

export type EpisodeScene = {
  id: string;
  episode_id: string;
  location_id: string | null;
  location_name: string | null;
  scene_number: number;
  title: string | null;
  summary: string | null;
  dialogue: string | null;
  visual_direction: string | null;
  participants: EpisodeParticipant[];
  created_at: string;
  updated_at: string;
};

export type StoryboardImage = {
  id: string;
  episode_id: string;
  scene_id: string;
  shot_id: string;
  provider: string;
  model: string | null;
  status: string;
  mime_type: string | null;
  image_data: string | null;
  image_url: string | null;
  prompt: string;
  revised_prompt: string | null;
  width: number | null;
  height: number | null;
  error: string | null;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Shot = {
  id: string;
  episode_id: string;
  scene_id: string;
  scene_number: number;
  scene_title: string | null;
  shot_number: number;
  shot_type: string;
  camera_angle: string;
  duration_seconds: number;
  visual_description: string;
  prompt: string | null;
  status: string;
  storyboard_image: StoryboardImage | null;
  created_at: string;
  updated_at: string;
};

export type StoryboardScene = {
  scene_id: string;
  scene_number: number;
  title: string | null;
  location_name: string | null;
  summary: string | null;
  visual_direction: string | null;
  participants: EpisodeParticipant[];
  shots: Shot[];
};

export type EpisodeStoryboard = {
  episode_id: string;
  universe_id: string;
  title: string;
  summary: string | null;
  scene_count: number;
  shot_count: number;
  generated_image_count: number;
  scenes: StoryboardScene[];
};

export type StoryboardRenderPayload = {
  regenerate_images?: boolean;
};

export type Timeline = {
  id: string;
  universe_id: string;
  parent_timeline_id: string | null;
  branch_from_commit_id: string | null;
  head_commit_id: string | null;
  name: string;
  is_canon: boolean;
  created_at: string;
  updated_at: string;
};

export type TimelineCommit = {
  id: string;
  timeline_id: string;
  parent_commit_id: string | null;
  message: string;
  commit_type: string;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type TimelineEvent = {
  id: string;
  title: string;
  summary: string | null;
  event_type: string | null;
  order_index: number | null;
  importance: number | null;
  location_id: string | null;
  location_name: string | null;
  participants: string[];
  commit_id: string | null;
  commit_message: string | null;
  commit_type: string | null;
  change_type: string | null;
  created_at: string;
  updated_at: string;
};

export type TimelineImpactAnalysis = {
  alternate_history_summary: string;
  impacted_characters: string[];
  impacted_relationships: string[];
  impacted_events: string[];
  memory_updates: string[];
};

export type TimelineBranchPayload = {
  name?: string | null;
  event_id?: string | null;
  commit_id?: string | null;
  modified_title?: string | null;
  new_outcome: string;
};

export type TimelineBranchResult = {
  timeline: Timeline;
  branch_commit: TimelineCommit;
  modified_event: TimelineEvent;
  impact: TimelineImpactAnalysis;
};

export type TimelineDiffEvent = {
  kind: string;
  title: string;
  base_summary: string | null;
  compare_summary: string | null;
  order_index: number | null;
};

export type TimelineDiffRelationship = {
  source_character: string;
  target_character: string;
  relationship_type: string;
  base_strength: number | null;
  compare_strength: number | null;
  base_status: string | null;
  compare_status: string | null;
};

export type TimelineDiffState = {
  character: string;
  base_status: string | null;
  compare_status: string | null;
  base_emotional_state: string | null;
  compare_emotional_state: string | null;
  base_summary: string | null;
  compare_summary: string | null;
};

export type TimelineDiff = {
  base_timeline_id: string;
  compare_timeline_id: string;
  base_timeline_name: string;
  compare_timeline_name: string;
  changed_events: TimelineDiffEvent[];
  relationship_differences: TimelineDiffRelationship[];
  state_differences: TimelineDiffState[];
};
