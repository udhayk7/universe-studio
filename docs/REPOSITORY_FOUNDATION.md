# Universe Studio Repository Foundation

Tagline: Create worlds, not clips.

This document defines the monorepo structure for the Universe Studio hackathon project. It is intentionally limited to foundation, infrastructure, boundaries, and conventions. Business logic, domain APIs, memory commits, and agent workflows are deferred to implementation passes.

## Monorepo Layout

```text
universe-studio/
  frontend/
    public/
    src/
      app/
        (studio)/
          universes/
            new/
            [id]/
              memory/
              timeline/
              branches/
              graph/
              episodes/
                new/
                [episodeId]/
              characters/
                [characterId]/
        globals.css
        layout.tsx
        page.tsx
      components/
        ui/
        layout/
        studio/
        graph/
        timeline/
        memory/
        episodes/
        common/
        providers/
      hooks/
      lib/
      services/
        api/
        storage/
        graph/
      state/
      styles/
      types/
    components.json
    next.config.ts
    package.json
    postcss.config.mjs
    tsconfig.json
  backend/
    alembic/
      versions/
      env.py
    app/
      api/
        v1/
          endpoints/
          router.py
      agents/
        definitions/
        prompts/
        tools/
        orchestrator/
      core/
        config.py
      db/
        models/
        base.py
        session.py
      integrations/
        openai/
        neo4j/
        supabase/
      memory_engine/
      repositories/
      schemas/
      services/
      workers/
      main.py
    tests/
    alembic.ini
    pyproject.toml
  docker/
    backend/
      Dockerfile
    frontend/
      Dockerfile
    neo4j/
      import/
      plugins/
    postgres/
      init/
        001_extensions.sql
  docs/
    CONVENTIONS.md
    REPOSITORY_FOUNDATION.md
  scripts/
  docker-compose.yml
  package.json
  pnpm-workspace.yaml
```

## Frontend Architecture

### Framework Foundation

- Next.js 15 App Router
- TypeScript with strict mode
- TailwindCSS
- ShadCN UI configured through `components.json`
- Zustand for client-only UI state
- TanStack Query for server state
- React Flow through `@xyflow/react`
- Framer Motion for polished interaction states

### App Router Structure

The frontend route folders are present but intentionally do not implement product screens yet.

| Route | Future Purpose |
|---|---|
| `/` | Studio entry or universe selector |
| `/universes/new` | Universe creation from idea, screenplay, scene, or script |
| `/universes/[id]` | Universe dashboard |
| `/universes/[id]/memory` | Memory inspector |
| `/universes/[id]/timeline` | Timeline and commit view |
| `/universes/[id]/branches` | Timeline A vs Timeline B comparison |
| `/universes/[id]/graph` | React Flow relationship and causality graph |
| `/universes/[id]/episodes/new` | Episode generation surface |
| `/universes/[id]/episodes/[episodeId]` | Generated episode viewer |
| `/universes/[id]/characters/[characterId]` | Character dossier |

### Component Boundaries

| Folder | Responsibility |
|---|---|
| `components/ui` | ShadCN-generated primitives only |
| `components/layout` | App shell, navigation, headers, panes |
| `components/studio` | Universe creation and dashboard components |
| `components/graph` | React Flow nodes, edges, controls, adapters |
| `components/timeline` | Timeline, branch, commit, and diff UI |
| `components/memory` | Memory inspector and character memory surfaces |
| `components/episodes` | Episode generation and output surfaces |
| `components/common` | Shared presentational components |
| `components/providers` | Query, theme, and app providers |

### Hooks, Services, and State

| Folder | Responsibility |
|---|---|
| `hooks` | UI and workflow hooks such as `use-active-timeline` |
| `services/api` | Typed FastAPI client modules |
| `services/storage` | Supabase Storage frontend helpers |
| `services/graph` | React Flow graph data adapters |
| `state` | Zustand stores for UI state only |
| `types` | Shared frontend TypeScript types |
| `lib` | Small utilities and framework helpers |

Server state belongs in TanStack Query. Zustand should not mirror API data unless there is a deliberate UX reason.

## Backend Architecture

### Framework Foundation

- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic and Pydantic Settings
- OpenAI SDK
- OpenAI Agents SDK
- Neo4j Python driver
- Supabase Python client

### API Structure

| Folder | Responsibility |
|---|---|
| `app/api/v1/router.py` | API v1 aggregate router |
| `app/api/v1/endpoints` | Future domain endpoint modules |
| `app/schemas` | Pydantic request and response contracts |

Future endpoint modules:

- `universes.py`
- `sources.py`
- `memory.py`
- `characters.py`
- `timelines.py`
- `episodes.py`
- `graph.py`
- `agents.py`
- `jobs.py`
- `consistency.py`

Endpoint modules should stay thin. They validate request boundaries, call services, and return schemas.

### Services

Services own application workflows and transaction boundaries.

Future service modules:

- `universe_service.py`
- `source_ingestion_service.py`
- `memory_service.py`
- `graph_sync_service.py`
- `timeline_service.py`
- `branch_service.py`
- `episode_generation_service.py`
- `consistency_service.py`
- `agent_run_service.py`
- `asset_service.py`
- `job_service.py`

### Repositories

Repositories isolate persistence details.

Future repository modules:

- `universe_repository.py`
- `character_repository.py`
- `timeline_repository.py`
- `memory_repository.py`
- `episode_repository.py`
- `job_repository.py`
- `graph_repository.py`
- `asset_repository.py`

Repositories should not perform model calls, orchestration, or prompt construction.

### Agent Layer

| Folder | Responsibility |
|---|---|
| `agents/definitions` | Agent declarations |
| `agents/prompts` | Prompt templates and prompt versions |
| `agents/tools` | Tool wrappers exposed to agents |
| `agents/orchestrator` | Handoffs, guardrails, traces, and workflow composition |

Planned agents:

- World Architect Agent
- Character Agent
- Story Agent
- Timeline Agent
- Consistency Agent
- Historian Agent
- Director Agent

Agents should emit structured proposals. Services and the memory engine decide what becomes committed state.

### Database Structure

| Folder/File | Responsibility |
|---|---|
| `db/base.py` | SQLAlchemy declarative base |
| `db/session.py` | Session factory and DB dependency |
| `db/models` | SQLAlchemy models |
| `alembic/env.py` | Migration runtime |
| `alembic/versions` | Migration files |

Planned database tables should mirror the finalized architecture: users, universes, source inputs, assets, characters, locations, objects, relationships, events, timelines, commits, memory entries, episodes, scenes, agent runs, consistency checks, and jobs.

### Memory Engine Structure

The memory engine is separate from services and agents so it can become the core domain layer.

Future modules:

- `patches.py`
- `commit_builder.py`
- `character_memory.py`
- `event_memory.py`
- `relationship_memory.py`
- `timeline_memory.py`
- `conflicts.py`

## Docker Compose Architecture

| Service | Purpose | Port |
|---|---|---|
| `frontend` | Next.js development server | `3000` |
| `backend` | FastAPI development server | `8000` |
| `postgres` | PostgreSQL with pgvector | `5432` |
| `neo4j` | Neo4j graph database | `7474`, `7687` |

Supabase Storage is external for the hackathon. This avoids the complexity of local Supabase self-hosting and keeps storage credentials environment-driven.

## Environment Variables

### Root `.env`

Used by Docker Compose.

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `NEO4J_AUTH`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `BACKEND_PORT`
- `FRONTEND_PORT`
- `NEXT_PUBLIC_API_BASE_URL`

### Frontend `.env.local`

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_APP_NAME`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Backend `.env`

- `APP_ENV`
- `APP_NAME`
- `API_V1_PREFIX`
- `BACKEND_CORS_ORIGINS`
- `DATABASE_URL`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

## Local Development Setup

### Prerequisites

- Docker Desktop
- Node.js 22 or newer
- pnpm 9 or newer
- Python 3.12
- Supabase project and storage bucket
- OpenAI API key

### Installation

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
pnpm install
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run

Run everything through Compose:

```bash
docker compose up
```

Or run infrastructure through Compose and apps manually:

```bash
docker compose up -d postgres neo4j
pnpm dev:frontend
pnpm dev:backend
```

### Verify

```bash
curl http://localhost:8000/health
open http://localhost:3000
open http://localhost:7474
```

## Dependency List

### Frontend

- `next`
- `react`
- `react-dom`
- `@tanstack/react-query`
- `@xyflow/react`
- `zustand`
- `framer-motion`
- `lucide-react`
- `class-variance-authority`
- `clsx`
- `tailwind-merge`
- `tailwindcss`
- `@tailwindcss/postcss`
- `typescript`
- `eslint`
- `prettier`

### Backend

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic`
- `pydantic-settings`
- `psycopg`
- `neo4j`
- `supabase`
- `openai`
- `openai-agents`
- `httpx`
- `python-multipart`
- `structlog`
- `tenacity`
- `pytest`
- `ruff`
- `mypy`

## Implementation Guardrails

- Do not put business logic in endpoint modules.
- Do not let agents write directly to the database.
- Do not store server data in Zustand.
- Do not introduce a queue system until the simple job layer becomes insufficient.
- Do not self-host Supabase unless the hackathon scope changes.
- Keep generated media and uploads out of git.

## Official Setup References

- Next.js installation: https://nextjs.org/docs/app/getting-started/installation
- ShadCN Next.js installation: https://ui.shadcn.com/docs/installation/next
- TailwindCSS Next.js guide: https://tailwindcss.com/docs/installation/framework-guides/nextjs
- OpenAI Agents SDK quickstart: https://openai.github.io/openai-agents-python/quickstart/
- OpenAI Responses migration guide: https://developers.openai.com/api/docs/guides/migrate-to-responses
