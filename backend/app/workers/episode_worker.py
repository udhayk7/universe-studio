from __future__ import annotations

import uuid

from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.episode_generation import EpisodeGenerateRequest
from app.services.episode_generation_service import (
    ConsistencyBlockedEpisodeError,
    EpisodeGenerationService,
)
from app.services.job_service import JobService


def run_episode_generation_job(
    *,
    job_id: uuid.UUID,
    universe_id: uuid.UUID,
    payload_data: dict[str, object],
    timeline_id: uuid.UUID | None = None,
) -> None:
    db = SessionLocal()
    job_service = JobService(db)
    try:
        payload = EpisodeGenerateRequest.model_validate(payload_data)
        EpisodeGenerationService(db).generate(
            job_id=job_id,
            universe_id=universe_id,
            prompt=payload.prompt,
            timeline_id=timeline_id,
        )
    except ConsistencyBlockedEpisodeError as error:
        db.rollback()
        job_service.update(
            job_id,
            status="failed",
            progress=100,
            message=str(error),
            result_data=error.result_data(),
            completed=True,
        )
    except (RuntimeError, ValueError, ValidationError) as error:
        db.rollback()
        job_service.update(
            job_id,
            status="failed",
            progress=100,
            message=str(error),
            result_data={"error_type": error.__class__.__name__},
            completed=True,
        )
    except Exception as error:
        db.rollback()
        job_service.update(
            job_id,
            status="failed",
            progress=100,
            message=f"Episode generation failed: {error}",
            result_data={"error_type": error.__class__.__name__},
            completed=True,
        )
    finally:
        db.close()
