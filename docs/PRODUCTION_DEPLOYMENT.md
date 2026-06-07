# Universe Studio Production Deployment

This guide is based on the current repository structure:

- Frontend app: `frontend`
- Backend app: `backend`
- Frontend package manager: `pnpm`
- Backend package manager: Python packaging via `backend/pyproject.toml`
- Backend migration tool: Alembic

## Phase 1: Deployment Readiness Report

### Frontend

- Framework: Next.js 15
- Build command: `pnpm build`
- Development command: `pnpm dev`
- Production start command, if self-hosted: `pnpm start`
- Vercel output: Next.js managed output, no custom output directory required.
- Required production env:
  - `NEXT_PUBLIC_API_BASE_URL`
  - `NEXT_PUBLIC_APP_NAME`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Backend

- Framework: FastAPI
- App import path: `app.main:app`
- Local dev command: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Production command: `bash scripts/start_production.sh`
- Production script behavior:
  - runs `alembic upgrade head`
  - starts `uvicorn app.main:app --host 0.0.0.0 --port "$PORT"`
- Health endpoints:
  - `GET /health`
  - `GET /api/v1/health`
  - `GET /api/v1/health/postgres`
  - `GET /api/v1/health/neo4j`
  - `GET /api/v1/health/openai`

### PostgreSQL

- Required extension: `vector`
- Recommended provider for this deployment plan: Supabase Postgres
- Migration command: `cd backend && alembic upgrade head`
- SQLAlchemy URL format required by code:
  - `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`

### Neo4j

- Required provider for this deployment plan: Neo4j Aura
- Required environment variables:
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
- Aura URI format:
  - `neo4j+s://YOUR-AURA-INSTANCE.databases.neo4j.io`

### Supabase Storage

- Required bucket:
  - `universe-assets`
- Current implementation note:
  - Supabase settings and asset database schema exist.
  - Storyboard images are currently persisted in PostgreSQL as base64 payloads, not uploaded to Supabase Storage yet.

### OpenAI

- Required backend-only variables:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL=gpt-5`
  - `OPENAI_IMAGE_MODEL=gpt-image-1`
  - `OPENAI_IMAGE_SIZE=1536x1024`
  - `OPENAI_IMAGE_QUALITY=medium`
  - `OPENAI_TIMEOUT_SECONDS=90`

Never expose `OPENAI_API_KEY` in frontend or `NEXT_PUBLIC_*` variables.

## Phase 2: Vercel Frontend Deployment

Create a Vercel project from the GitHub repository.

Use these settings:

- Framework Preset: `Next.js`
- Root Directory: `frontend`
- Install Command: `cd .. && corepack enable && pnpm install --frozen-lockfile`
- Build Command: `pnpm build`
- Output Directory: leave empty / framework default

Production environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RAILWAY-DOMAIN.up.railway.app/api/v1
NEXT_PUBLIC_APP_NAME=Universe Studio
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

Deploy steps:

1. Open Vercel Dashboard.
2. Import `udhayk7/universe-studio`.
3. Set Root Directory to `frontend`.
4. Confirm the commands above.
5. Add production environment variables.
6. Deploy.
7. Copy the production URL.
8. Add the production URL to Railway `BACKEND_CORS_ORIGINS`.
9. Redeploy Railway backend after updating CORS.

## Phase 3: Railway Backend Deployment

Create a Railway service from the same GitHub repository.

Use these settings:

- Service Root Directory: `backend`
- Builder: Nixpacks
- Start Command: `bash scripts/start_production.sh`
- Healthcheck Path: `/health`

The checked-in `backend/railway.json` encodes these deployment settings.

Required Railway variables:

```text
APP_ENV=production
APP_NAME=Universe Studio API
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app

DATABASE_URL=postgresql+psycopg://postgres:[YOUR-PASSWORD]@YOUR-SUPABASE-POSTGRES-HOST:5432/postgres

NEO4J_URI=neo4j+s://YOUR-AURA-INSTANCE.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_AURA_PASSWORD

SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=universe-assets

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1536x1024
OPENAI_IMAGE_QUALITY=medium
OPENAI_TIMEOUT_SECONDS=90
UNIVERSE_EXTRACTION_MAX_CHARS=60000
```

Deploy steps:

1. Open Railway Dashboard.
2. New Project -> Deploy from GitHub repo.
3. Select `udhayk7/universe-studio`.
4. Set service root to `backend`.
5. Add variables above.
6. Deploy.
7. Confirm logs show `Running Alembic migrations...`.
8. Confirm logs show `Starting Universe Studio API on port ...`.
9. Open `https://YOUR-RAILWAY-DOMAIN/health`.
10. Open `https://YOUR-RAILWAY-DOMAIN/api/v1/health/postgres`.
11. Open `https://YOUR-RAILWAY-DOMAIN/api/v1/health/neo4j`.
12. Open `https://YOUR-RAILWAY-DOMAIN/api/v1/health/openai`.

## Phase 4: Supabase Production Setup

Create a Supabase project.

Postgres:

1. In Supabase, open Project Settings -> Database -> Connection string.
2. For Railway, prefer the direct connection string if Railway can reach IPv6, or the session pooler string if IPv4-only connectivity is required.
3. Convert the scheme for SQLAlchemy/psycopg:
   - Supabase gives: `postgresql://...`
   - Universe Studio expects: `postgresql+psycopg://...`
4. Set Railway `DATABASE_URL` to that converted string.

Extensions:

Run in Supabase SQL Editor before first deploy:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Storage:

1. Open Storage.
2. Create bucket: `universe-assets`.
3. Keep it private for production.
4. Copy:
   - Project URL -> `SUPABASE_URL`
   - anon/public key -> `SUPABASE_ANON_KEY`
   - service role key -> `SUPABASE_SERVICE_ROLE_KEY`

Migration verification:

```bash
cd backend
DATABASE_URL='postgresql+psycopg://...' alembic upgrade head
DATABASE_URL='postgresql+psycopg://...' alembic current
```

## Phase 5: Neo4j Aura Setup

Create a Neo4j AuraDB instance.

1. Create AuraDB project/instance.
2. Download or copy credentials.
3. Set Railway variables:
   - `NEO4J_URI=neo4j+s://YOUR-AURA-INSTANCE.databases.neo4j.io`
   - `NEO4J_USER=neo4j`
   - `NEO4J_PASSWORD=YOUR_AURA_PASSWORD`
4. Redeploy Railway.
5. Verify: `GET /api/v1/health/neo4j`.

## Phase 6: Production Verification Checklist

- [ ] Frontend deployed on Vercel.
- [ ] Backend deployed on Railway.
- [ ] `GET /health` returns `{ "status": "ok" }`.
- [ ] `GET /api/v1/health/postgres` returns `ok`.
- [ ] `GET /api/v1/health/neo4j` returns `ok`.
- [ ] `GET /api/v1/health/openai` returns `api_key_found: true`.
- [ ] Vercel `NEXT_PUBLIC_API_BASE_URL` points to Railway `/api/v1`.
- [ ] Railway `BACKEND_CORS_ORIGINS` includes the Vercel domain.
- [ ] Supabase bucket `universe-assets` exists.
- [ ] Universe creation works from Vercel UI.
- [ ] Character dossier loads.
- [ ] Memory Explorer graph loads.
- [ ] Episode generation works.
- [ ] Storyboard generation works.
- [ ] Timeline branching works.
- [ ] Alternate future generation works.
- [ ] Consistency dashboard loads.
- [ ] Agent trace tab loads on generated episodes.

## Known Deployment Constraints

- Remote deployment was not executed from this machine because Vercel, Railway, Supabase, and Neo4j Aura credentials are not available in the repository.
- Supabase Storage variables are required for future asset storage, but current storyboard images are stored in PostgreSQL.
- Running Alembic migrations on service start is acceptable for the hackathon deployment. For multi-instance production, move migrations to a single release/predeploy job.
