# Docker Architecture

Docker Compose is the local development runtime for Universe Studio.

## Services

- `frontend`: Next.js 15 development server.
- `backend`: FastAPI development server.
- `postgres`: PostgreSQL 16 with pgvector support.
- `neo4j`: Neo4j 5 Community for universe graph projection.

Supabase Storage is treated as an external managed service for the hackathon. Do not self-host Supabase locally unless the team explicitly changes this decision.

## Notes

- PostgreSQL initialization SQL lives in `docker/postgres/init`.
- Neo4j import and plugin mount points live in `docker/neo4j`.
- Application containers mount local source directories for fast iteration.
