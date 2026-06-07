# Universe Studio

Create worlds, not clips.

Universe Studio is a memory-first cinematic universe platform built for a hackathon demo. Instead of generating isolated AI video prompts, it turns an idea or script into a persistent story world with characters, relationships, events, timelines, branch history, consistency checks, and agent traces.

## Final Demo

The deterministic judge demo is `Memory Market 2094`.

Premise: Memories are bought and sold as currency.

Seeded demo content:

- 8 major characters
- 6 locations
- 6 world objects
- 48 timeline-specific relationships
- 29+ events
- 2 completed episodes
- Timeline A: Maya survives
- Timeline B: Maya dies
- Agent traces for Historian, Story, Director, Consistency, and Memory Update
- Consistency dashboard issues and validation reports

## Quick Start

Install prerequisites:

- Docker Desktop
- Node.js 20+
- pnpm 9+
- Python 3.12

Set up environment files:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

Add your OpenAI key:

- Docker Compose: paste it into root `.env` as `OPENAI_API_KEY=sk-...`
- Local backend only: paste it into `backend/.env` as `OPENAI_API_KEY=sk-...`
- Do not put the OpenAI key in frontend env files or any `NEXT_PUBLIC_*` variable.

Verify OpenAI configuration:

```bash
pnpm openai:verify
```

Install dependencies:

```bash
pnpm install

cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..
```

Run the deterministic demo setup:

```bash
pnpm demo:setup
```

Start the app:

```bash
docker compose up
```

Run database migrations:

```bash
pnpm db:migrate
```

This uses the backend virtual environment directly. The equivalent raw command is:

```bash
cd backend
.venv/bin/alembic upgrade head
```

Verify backend dependencies, database connectivity, Neo4j connectivity, OpenAI config, and
Alembic status:

```bash
pnpm backend:verify
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## Demo Mode

On the landing page or Universes dashboard, click `Demo Mode`.

This calls:

```http
POST /api/v1/demo/setup
```

It seeds `Memory Market 2094`, syncs Neo4j when available, and redirects into the demo universe.

## Validation

Run:

```bash
pnpm demo:validate
```

The validator checks:

- Universe creation
- Graph generation
- Character dossiers
- Episode generation
- Timeline branching
- Alternate future generation
- Timeline differences
- Consistency checks
- Agent traces

## Core Features

- Universe creation from user input
- Structured extraction into durable world state
- Character Memory Engine
- Character dossier UI
- Universe Memory Explorer with React Flow
- Episode Generation Engine
- Timeline branching and alternate futures
- Branch-aware memory retrieval
- Consistency Engine
- Agent Trace System
- Deterministic hackathon demo seeder

## Stack

Frontend:

- Next.js 15
- TypeScript
- TailwindCSS
- ShadCN-style UI primitives
- Zustand
- TanStack Query
- React Flow
- Framer Motion

Backend:

- FastAPI
- Python 3.12
- SQLAlchemy 2.0
- Alembic
- Pydantic
- OpenAI SDK
- OpenAI Agents SDK

Data:

- PostgreSQL with pgvector
- Neo4j
- Supabase Storage foundation

Infrastructure:

- Docker
- Docker Compose

## Key Docs

- [Demo Walkthrough](docs/DEMO_WALKTHROUGH.md)
- [Demo Flow](docs/DEMO_FLOW.md)
- [Demo Validation Checklist](docs/DEMO_VALIDATION_CHECKLIST.md)
- [Judge Presentation Assets](docs/JUDGE_PRESENTATION_ASSETS.md)
- [Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md)
- [Architecture Summary](docs/ARCHITECTURE_SUMMARY.md)
- [Judge FAQ](docs/JUDGE_FAQ.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
- [Launch Readiness Report](docs/LAUNCH_READINESS_REPORT.md)

## Known Limitations

- No video or voice generation yet.
- The demo seeder is deterministic by design, so judges can reliably inspect the product.
- Full AI workflows require `OPENAI_API_KEY`.
- Storyboard image generation uses OpenAI Images and stores frames in PostgreSQL.
- Supabase Storage is scaffolded but not central to the current demo.
- Some integration tests require `TEST_DATABASE_URL`.

## Judge Narrative

Universe Studio is not another AI clip generator. It is a versioned memory engine for cinematic universes. The demo shows how persistent characters, relationships, events, timelines, and consistency agents make future generation causally connected to the world that came before.
