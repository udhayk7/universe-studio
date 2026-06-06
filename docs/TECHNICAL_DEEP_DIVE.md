# Technical Deep Dive

## Backend Services

Universe creation:

- `SourceIngestionService`
- `WorldExtractionService`
- `UniversePersistenceService`
- `Neo4jSyncService`

Character memory:

- `CharacterMemoryService`
- `CharacterKnowledgeService`
- `CharacterArcService`

Memory explorer:

- `UniverseMemoryExplorerService`
- `Neo4jGraphAggregationService`
- PostgreSQL fallback graph generation

Episode generation:

- `EpisodeHistorianService`
- `EpisodeGenerationService`
- `EpisodePersistenceService`
- `EpisodeWorker`

Timeline branching:

- `TimelineService`
- `TimelineHistoryService`
- `BranchService`
- `TimelineDiffService`
- `FutureRegenerationService`

Continuity:

- `ConsistencyService`
- `ConsistencyAgentRunner`
- `AgentTraceService`

Demo:

- `DemoSeedService`
- `backend/scripts/seed_demo.py`
- `backend/scripts/seed_demo_neo4j.py`
- `backend/scripts/validate_demo.py`

## PostgreSQL Persistence

The system uses SQLAlchemy 2.0 models with UUID primary keys, timestamps, foreign
keys, and indexes. Timeline history is commit-based:

- `timelines`
- `timeline_commits`
- `timeline_commit_events`

Episodes are attached to timeline commits so generated content can be traced back
to the branch state that produced it.

Memory is stored in `memory_entries` with:

- `universe_id`
- `timeline_id`
- `commit_id`
- `entity_type`
- `entity_id`
- `memory_type`
- `content`
- `structured_value`
- optional pgvector embedding field

## Neo4j Graph

Neo4j is used as the primary graph-rendering source when available.

Node labels:

- `Universe`
- `Timeline`
- `Commit`
- `Character`
- `Event`
- `Location`
- `Object`

Relationship types:

- `KNOWS`
- `LOVES`
- `BETRAYED`
- `ALLIED_WITH`
- `CAUSED`
- `VISITED`
- `PARTICIPATED_IN`
- `OCCURRED_AT`
- `OWNS`

If Neo4j is unavailable, the Memory Explorer builds a graph from PostgreSQL so
the demo remains reliable.

## Agent Trace Storage

Every major generation step records:

- Agent name
- Input summary
- Output summary
- Status
- Start time
- Completion time
- Duration
- Related job
- Related episode

Stored in `agent_runs`.

Retrieval APIs:

```http
GET /api/v1/episodes/{episode_id}/trace
GET /api/v1/jobs/{job_id}/trace
```

## Consistency Pipeline

For generated episodes:

1. Historian builds branch-aware context.
2. Story Agent creates outline.
3. Director Agent creates scenes and memory changes.
4. Consistency Agent validates generated content.
5. Critical issues block persistence.
6. Non-critical issues are stored.
7. Memory Update commits scene outcomes, events, and memories.

Manual consistency API:

```http
POST /api/v1/consistency/check
GET /api/v1/consistency/{id}
GET /api/v1/universes/{id}/consistency
```

## Demo Determinism

The final hackathon demo does not depend on live AI calls. `DemoSeedService`
creates a complete universe state directly in PostgreSQL and syncs Neo4j when
available. This guarantees the demo always has:

- Graph data
- Character dossiers
- Timeline diffs
- Episodes
- Agent traces
- Consistency reports

Live AI integrations remain available for the non-seeded workflow when
`OPENAI_API_KEY` is configured.

## Validation Strategy

Static checks:

- Backend `ruff`
- Backend `compileall`
- Frontend `eslint`
- Frontend TypeScript
- Frontend production build

Demo checks:

- `pnpm demo:validate`
- Browser smoke tests
- Docker Compose config
- Environment file review

Database-dependent pytest tests require `TEST_DATABASE_URL`.
