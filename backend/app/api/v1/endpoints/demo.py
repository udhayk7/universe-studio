from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.demo import DemoSeedRequest, DemoSeedResult
from app.services.demo_seed_service import DemoSeedService

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/setup", response_model=DemoSeedResult)
def setup_demo(
    payload: DemoSeedRequest,
    db: Annotated[Session, Depends(get_db)],
) -> DemoSeedResult:
    return DemoSeedService(db).seed(reset=payload.reset, sync_neo4j=payload.sync_neo4j)
