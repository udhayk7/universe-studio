from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.consistency import (
    AgentTraceResponse,
    ConsistencyCheckRead,
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyDashboardSummary,
)
from app.services.agent_trace_service import AgentTraceService
from app.services.consistency_service import ConsistencyService

router = APIRouter(tags=["consistency"])


def get_consistency_service(
    db: Annotated[Session, Depends(get_db)],
) -> ConsistencyService:
    return ConsistencyService(db)


def get_trace_service(db: Annotated[Session, Depends(get_db)]) -> AgentTraceService:
    return AgentTraceService(db)


@router.post("/consistency/check", response_model=ConsistencyCheckResult)
def check_consistency(
    payload: ConsistencyCheckRequest,
    service: Annotated[ConsistencyService, Depends(get_consistency_service)],
) -> ConsistencyCheckResult:
    try:
        return service.check(payload)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get("/consistency/{check_id}", response_model=ConsistencyCheckRead)
def get_consistency_check(
    check_id: uuid.UUID,
    service: Annotated[ConsistencyService, Depends(get_consistency_service)],
) -> ConsistencyCheckRead:
    try:
        return service.get_check(check_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get(
    "/universes/{universe_id}/consistency",
    response_model=ConsistencyDashboardSummary,
)
def get_consistency_dashboard(
    universe_id: uuid.UUID,
    service: Annotated[ConsistencyService, Depends(get_consistency_service)],
) -> ConsistencyDashboardSummary:
    try:
        return service.dashboard(universe_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get("/episodes/{episode_id}/trace", response_model=AgentTraceResponse)
def get_episode_trace(
    episode_id: uuid.UUID,
    service: Annotated[AgentTraceService, Depends(get_trace_service)],
) -> AgentTraceResponse:
    try:
        return service.get_episode_trace(episode_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get("/jobs/{job_id}/trace", response_model=AgentTraceResponse)
def get_job_trace(
    job_id: uuid.UUID,
    service: Annotated[AgentTraceService, Depends(get_trace_service)],
) -> AgentTraceResponse:
    try:
        return service.get_job_trace(job_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


def _not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
