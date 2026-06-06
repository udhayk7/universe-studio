from __future__ import annotations

import uuid

from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.source import SourcePayload
from app.services.job_service import JobService
from app.services.neo4j_sync_service import Neo4jSyncService
from app.services.universe_persistence_service import UniversePersistenceService
from app.services.world_extraction_service import WorldExtractionService


def run_extraction_job(
    *,
    job_id: uuid.UUID,
    payload_data: dict[str, object],
    universe_id: uuid.UUID | None = None,
) -> None:
    db = SessionLocal()
    job_service = JobService(db)
    try:
        payload = SourcePayload.model_validate(payload_data)

        job_service.update(
            job_id,
            status="running",
            progress=10,
            message="Reading source material",
        )

        job_service.update(
            job_id,
            progress=30,
            message="Extracting universe structure",
        )
        extraction = WorldExtractionService().extract(payload)

        job_service.update(
            job_id,
            progress=65,
            message="Persisting universe memory",
        )
        persistence_result = UniversePersistenceService(db).persist_extraction(
            extraction=extraction,
            source=payload,
            universe_id=universe_id,
        )

        job_service.update(
            job_id,
            universe_id=persistence_result.universe.id,
            progress=85,
            message="Syncing universe graph",
        )
        Neo4jSyncService().sync_extraction(persistence_result)

        job_service.update(
            job_id,
            universe_id=persistence_result.universe.id,
            status="completed",
            progress=100,
            message="Universe created",
            completed=True,
        )
    except (RuntimeError, ValueError, ValidationError) as error:
        job_service.update(
            job_id,
            status="failed",
            progress=100,
            message=str(error),
            completed=True,
        )
    except Exception as error:
        job_service.update(
            job_id,
            status="failed",
            progress=100,
            message=f"Extraction failed: {error}",
            completed=True,
        )
    finally:
        db.close()
