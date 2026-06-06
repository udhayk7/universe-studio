# Universe Studio Demo Walkthrough

## Demo Universe

Name: Memory Market 2094

Premise: Memories are bought and sold as currency.

This deterministic seed is designed for hackathon judging. It does not require
AI calls to produce the demo state. It creates a full memory graph, character
dossiers, two completed episodes, two timelines, timeline differences,
consistency reports, and agent traces.

## One-Click Setup

From the repository root:

```bash
pnpm demo:setup
```

This command starts PostgreSQL and Neo4j, runs Alembic migrations, seeds the
demo universe, syncs Neo4j when available, and runs the validation checklist.

PostgreSQL-only seed:

```bash
cd backend
./.venv/bin/python scripts/seed_demo.py --skip-neo4j
```

Neo4j-only resync after the database is seeded:

```bash
cd backend
./.venv/bin/python scripts/seed_demo_neo4j.py
```

Validation only:

```bash
pnpm demo:validate
```

## Judge Demo Script

1. Open the app at `http://localhost:3000`.
2. Click `Demo Mode`.
3. Open `Memory Market 2094`.
4. Show the universe overview:
   - Premise
   - Genre
   - Tone
   - Character tab
5. Open a character dossier, preferably Maya Orin or Jax Vey:
   - Identity
   - Goals
   - Fears
   - Relationships
   - Knowledge
   - Arc history
6. Open Memory Explorer:
   - Show graph nodes for characters, events, locations, and objects.
   - Filter/search for Maya, Jax, Cassian, or the Black Receipt.
   - Switch to event timeline and relationship matrix.
7. Open Timeline Workbench:
   - Select Timeline A - Maya Survives.
   - Select Timeline B - Maya Dies.
   - Show changed events, relationship differences, and state differences.
8. Open the generated episode `The Price of Recall`.
   - Show screenplay scenes and dialogue.
   - Switch to Agent Trace.
   - Explain Historian -> Story -> Director -> Consistency -> Memory Update.
9. Open the alternate future episode `The City Without Maya`.
   - Show that Timeline B does not reuse Timeline A's post-survival facts.
   - Show the Agent Trace tab.
10. Open Consistency Dashboard:
    - Show resolved and open issues.
    - Explain that generation is validated before persistence.

## Seeded Data Summary

- 1 universe
- 8 major characters
- 6 locations
- 6 important world objects
- 48 timeline-specific relationships
- 29+ events across canon and alternate timelines
- 2 timelines
- 2 completed episodes
- 8 screenplay scenes
- 10 agent trace rows
- 2 consistency checks

## Timeline Summary

Timeline A - Maya Survives:

- Maya survives the Vault Collapse.
- Maya exposes Cassian's ledger.
- The market freezes memory prices.
- Jax returns stolen childhood memories.
- The city ratifies the Recall Accord.
- Episode: The Price of Recall.

Timeline B - Maya Dies:

- Maya dies in the Vault Collapse.
- Jax preserves Maya's echo shard.
- Cassian seizes the Recall Lattice.
- Rook betrays the Black Receipt route.
- Tessa sparks the Empty Name uprising.
- Episode: The City Without Maya.

## What To Emphasize

Universe Studio is not generating isolated clips. The demo shows a persistent
world state that supports:

- Character memory
- Relationship continuity
- World rules
- Timeline branching
- Alternate futures
- Agent orchestration
- Consistency validation before persistence

The strongest line for judges:

> We are not prompting for clips. We are maintaining a versioned cinematic
> universe, then generating from memory.
