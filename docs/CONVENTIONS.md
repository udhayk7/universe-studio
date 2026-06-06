# Universe Studio Conventions

## Naming Conventions

### Frontend

- Route folders use Next.js App Router naming: `[id]`, `(studio)`, and lowercase nouns.
- React components use PascalCase filenames when the file exports one component, such as `TimelineView.tsx`.
- Hooks use kebab-case filenames and camelCase exports, such as `use-active-timeline.ts` and `useActiveTimeline`.
- Zustand stores use `*-store.ts`, such as `studio-store.ts`.
- API service modules use `*-client.ts` or bounded-context names, such as `universe-api.ts`.
- React Flow nodes use `*-node.tsx`; edges use `*-edge.tsx`.

### Backend

- Python modules use snake_case.
- Endpoint modules are plural nouns: `universes.py`, `episodes.py`.
- Services end in `_service.py`.
- Repositories end in `_repository.py`.
- Pydantic schema modules use singular bounded-context names: `universe.py`, `timeline.py`.
- SQLAlchemy model classes use singular PascalCase.
- Database table names use plural snake_case.
- Agent files use descriptive names: `world_architect_agent.py`, `timeline_agent.py`.

## Coding Conventions

### Frontend

- Prefer server components by default.
- Use client components only for interaction, browser APIs, React Flow, Zustand, TanStack Query, or animation.
- Keep ShadCN primitives in `components/ui`.
- Keep domain components outside `components/ui`.
- Use TanStack Query for API data.
- Use Zustand only for local UI state.
- Keep route components thin and delegate UI to components.
- Use `@/*` imports for source paths.

### Backend

- Endpoints validate input and call services.
- Services coordinate workflows and transactions.
- Repositories perform persistence operations.
- Agents emit structured proposals, not database writes.
- Memory engine modules convert validated proposals into commit-ready memory patches.
- Integration clients stay thin.
- Configuration comes from `app/core/config.py`.
- Use Alembic for schema changes.

## Branch Strategy

Use a lightweight hackathon-friendly trunk flow.

### Branches

- `main`: stable demo branch.
- `develop`: optional integration branch if the team is large.
- `feature/<scope>`: new features.
- `fix/<scope>`: bug fixes.
- `demo/<scenario>`: scripted demo polish.

Examples:

- `feature/universe-ingestion`
- `feature/timeline-branching`
- `feature/react-flow-graph`
- `fix/neo4j-connection`
- `demo/mira-survives-branch`

## Git Workflow

1. Pull latest `main` before starting.
2. Create a focused branch.
3. Keep changes scoped to one bounded context.
4. Run frontend lint/typecheck for frontend work.
5. Run backend tests/lint for backend work.
6. Open PR with a short summary and verification notes.
7. Squash merge for feature branches.

## Commit Message Format

Use concise conventional commits:

- `feat(frontend): add timeline shell`
- `feat(backend): add universe repository`
- `chore(docker): add neo4j service`
- `docs(architecture): document memory engine`
- `fix(api): correct cors settings`

## PR Checklist

- No business logic in routers.
- No direct database writes from agents.
- No secrets committed.
- Migration added for database schema changes.
- Frontend server state uses TanStack Query.
- Branch-specific memory changes preserve timeline context.
- Demo path still works.
