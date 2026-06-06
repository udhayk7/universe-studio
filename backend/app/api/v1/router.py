from fastapi import APIRouter

from app.api.v1.endpoints import (
    characters,
    consistency,
    demo,
    episodes,
    health,
    ingestion,
    jobs,
    memory_explorer,
    timelines,
    universes,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(ingestion.router)
api_router.include_router(universes.router)
api_router.include_router(memory_explorer.router)
api_router.include_router(characters.router)
api_router.include_router(timelines.router)
api_router.include_router(jobs.router)
api_router.include_router(episodes.router)
api_router.include_router(consistency.router)
api_router.include_router(demo.router)
