# Judge FAQ

## Why is this different from AI video generators?

AI video generators usually create isolated outputs. Universe Studio creates and
maintains a persistent universe. Characters, relationships, events, world rules,
and timelines are stored as durable memory. Future generation uses that memory
instead of starting from a blank prompt.

## How does memory work?

Memory is stored in PostgreSQL as structured entities and memory entries:

- Characters
- Relationships
- Locations
- Objects
- Events
- Timelines
- Commits
- Character state history
- Knowledge entries
- Arc events

Neo4j mirrors the graph so the Memory Explorer can visualize relationships and
event structure. pgvector support exists for future semantic retrieval.

## How do branches work?

Timelines behave like story branches. A branch points back to a parent timeline
and branch commit. Shared history is inherited up to the branch point. After the
branch event, new events, states, relationships, and episodes belong to the new
timeline.

In the demo:

- Timeline A: Maya survives.
- Timeline B: Maya dies.

Timeline B must not inherit facts from Timeline A after Maya survives.

## How do agents collaborate?

Episode generation uses a visible agent chain:

1. Historian Agent retrieves branch-aware memory.
2. Story Agent creates narrative structure.
3. Director Agent writes scenes and dialogue.
4. Consistency Agent validates continuity.
5. Memory Update stores consequences.

The Agent Trace tab stores and displays each step.

## How is consistency maintained?

The Consistency Engine checks generated content before persistence.

It validates:

- Dead characters appearing alive
- Knowledge a character never learned
- Uncaused relationship reversals
- Timeline causality errors
- World rule violations
- Branch leakage
- Impossible events

Critical issues block persistence. Warnings and resolved issues are stored in the
Consistency Dashboard.

## Does the demo require live OpenAI calls?

No. The final judge demo is deterministic. `Demo Mode` seeds the entire universe
so it always works. Live OpenAI workflows exist, but the deterministic seed is
recommended for judging reliability.

## Why use both PostgreSQL and Neo4j?

PostgreSQL is the durable source of truth for entities, commits, episodes, and
memory entries. Neo4j is optimized for graph exploration and relationship-heavy
queries. The Memory Explorer falls back to PostgreSQL if Neo4j is unavailable.

## What is the hardest technical problem?

Branch-aware continuity. Once a user changes history, future generation must use
the correct timeline state and avoid facts from sibling branches. Universe Studio
models this with timeline commits, branch commits, timeline-specific memory,
timeline-specific relationships, and consistency checks.

## What would you build next?

Next steps:

- Video generation on top of episode scenes
- Visual character/style consistency
- Voice generation
- Timeline merge and conflict resolution
- Collaborative writers room
- More advanced semantic retrieval with embeddings
- Production-grade auth, billing, and storage workflows
