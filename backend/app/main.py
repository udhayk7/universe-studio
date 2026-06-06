import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.integrations.openai.status import get_openai_auth_status

logger = logging.getLogger("app.startup")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    openai_status = get_openai_auth_status(settings=settings, initialize_client=False)
    if openai_status.api_key_found:
        logger.info(
            "OpenAI API key found. model=%s timeout_seconds=%s",
            openai_status.model,
            openai_status.timeout_seconds,
        )
    else:
        logger.warning(openai_status.message)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
