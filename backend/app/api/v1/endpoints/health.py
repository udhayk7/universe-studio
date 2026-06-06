from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.neo4j.connection import Neo4jConnectionManager, get_neo4j_manager
from app.integrations.neo4j.health import Neo4jHealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/postgres")
def postgres_health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgres"}


@router.get("/neo4j")
def neo4j_health(
    manager: Annotated[Neo4jConnectionManager, Depends(get_neo4j_manager)],
) -> dict[str, str]:
    try:
        if Neo4jHealthService(manager).is_healthy():
            return {"status": "ok", "database": "neo4j"}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Neo4j health check failed: {error}",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Neo4j health check failed",
    )
