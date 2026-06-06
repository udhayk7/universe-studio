# Deployment Guide

## Local Demo Deployment

Recommended for judging:

```bash
pnpm install
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..

cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env

pnpm demo:setup
docker compose up
```

Open `http://localhost:3000` and click `Demo Mode`.

## Required Environment Variables

Root `.env`:

```bash
POSTGRES_DB=universe_studio
POSTGRES_USER=universe
POSTGRES_PASSWORD=universe_dev_password
POSTGRES_PORT=5432
NEO4J_AUTH=neo4j/universe_dev_password
NEO4J_PASSWORD=universe_dev_password
BACKEND_PORT=8000
FRONTEND_PORT=3000
DATABASE_URL=postgresql+psycopg://universe:universe_dev_password@postgres:5432/universe_studio
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=universe_dev_password
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Frontend `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Backend `.env`:

```bash
DATABASE_URL=postgresql+psycopg://universe:universe_dev_password@localhost:5432/universe_studio
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=universe_dev_password
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5
```

## Docker Verification

Run:

```bash
docker compose config
docker compose up -d postgres neo4j
docker compose ps
```

Expected:

- `postgres` is healthy
- `neo4j` is healthy
- Backend starts after both are healthy
- Frontend starts after backend

## Database Migration

Inside the backend environment:

```bash
cd backend
./.venv/bin/python -m alembic upgrade head
```

Then seed:

```bash
./.venv/bin/python scripts/seed_demo.py
```

## Hosted Deployment Notes

Frontend:

- Deploy `frontend/` to Vercel or another Next.js host.
- Set `NEXT_PUBLIC_API_BASE_URL` to the hosted FastAPI API base.

Backend:

- Deploy `backend/` to a Python 3.12 host.
- Run Alembic migrations before first traffic.
- Set PostgreSQL, Neo4j, OpenAI, and Supabase environment variables.

PostgreSQL:

- Use a managed PostgreSQL database with pgvector enabled.
- Run `CREATE EXTENSION IF NOT EXISTS vector;`.

Neo4j:

- Use AuraDB or a managed Neo4j instance.
- Set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.

Supabase:

- Create a storage bucket for future media artifacts.
- The current demo does not depend on uploaded media to run.

## Demo Reliability Recommendation

For judging, prefer the deterministic seed flow over live AI calls:

```bash
pnpm demo:setup
pnpm demo:validate
```

This guarantees the same universe, timelines, episodes, traces, and consistency results every time.
