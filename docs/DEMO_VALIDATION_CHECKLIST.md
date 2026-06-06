# Demo Validation Checklist

Run:

```bash
pnpm demo:validate
```

The validator prints a JSON report with pass/fail results for each item below.

## Checklist

| Area | Verification |
| --- | --- |
| Universe creation | `Memory Market 2094` exists in PostgreSQL. |
| Graph generation | Memory graph has character, event, location, object nodes and edges. |
| Character dossiers | All 8 characters return context packs with relationships, memory, and arc events. |
| Episode generation | At least 2 completed episodes and 8 scenes exist. |
| Branching | Timeline A and Timeline B exist, and Timeline B has a parent timeline. |
| Alternate future | Timeline B has a completed episode. |
| Timeline differences | Timeline diff reports changed events, relationships, or states. |
| Consistency checks | Consistency check rows exist for the demo universe. |
| Agent traces | Episode/job traces include Historian, Story, Director, Consistency, and Memory Update steps. |

## Expected Validation Report Shape

```json
{
  "passed": true,
  "checks": [
    {
      "name": "universe creation",
      "passed": true,
      "detail": "Found Memory Market 2094 (...)."
    },
    {
      "name": "graph generation",
      "passed": true,
      "detail": "29 graph nodes, 80+ graph edges via postgres_fallback or neo4j."
    },
    {
      "name": "character dossiers",
      "passed": true,
      "detail": "8 characters with retrievable context packs."
    }
  ]
}
```

## Manual UI Validation

1. Click `Demo Mode`.
2. Confirm you land on `Memory Market 2094`.
3. Confirm Characters tab shows 8 characters.
4. Open Maya Orin and Jax Vey dossiers.
5. Open Memory Explorer and confirm the graph is populated.
6. Open Timeline Workbench and compare:
   - Timeline A - Maya Survives
   - Timeline B - Maya Dies
7. Open each completed episode:
   - The Price of Recall
   - The City Without Maya
8. Switch each episode to `Agent Trace`.
9. Open Consistency Dashboard.

## Troubleshooting

If validation fails because the demo universe is missing:

```bash
pnpm demo:setup
```

If Neo4j is unavailable, the Memory Explorer still works from the PostgreSQL
fallback graph. To retry Neo4j sync:

```bash
cd backend
./.venv/bin/python scripts/seed_demo_neo4j.py
```

If database-dependent backend tests are skipped, set `TEST_DATABASE_URL` before
running pytest.
