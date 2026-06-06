# Universe Studio

Create worlds, not clips.

This repository is a production-quality hackathon foundation for a memory-first cinematic universe studio. It intentionally contains infrastructure, dependency manifests, app boundaries, and documentation only. Business logic, domain routes, memory writes, and agent workflows should be added in future implementation passes.

## Stack

- Frontend: Next.js 15, TypeScript, TailwindCSS, ShadCN UI, Zustand, TanStack Query, React Flow, Framer Motion
- Backend: FastAPI, Python 3.12, SQLAlchemy, Alembic, Pydantic
- AI: OpenAI SDK, OpenAI Agents SDK, OpenAI Responses API
- Data: PostgreSQL, Neo4j
- Storage: Supabase Storage
- Infrastructure: Docker, Docker Compose

## Local Setup

1. Install Docker Desktop, Node.js, pnpm, and Python 3.12.
2. Copy environment templates:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

3. Fill in `OPENAI_API_KEY` and Supabase values.
4. Install frontend dependencies:

```bash
pnpm install
```

5. Install backend dependencies:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

6. Start local infrastructure and apps:

```bash
docker compose up
```

Frontend: http://localhost:3000

Backend: http://localhost:8000

Backend health: http://localhost:8000/health

Neo4j Browser: http://localhost:7474

## Documentation

- Repository foundation: `docs/REPOSITORY_FOUNDATION.md`
- Coding and naming conventions: `docs/CONVENTIONS.md`
- Docker notes: `docker/README.md`
