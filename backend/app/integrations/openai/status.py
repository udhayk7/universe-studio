from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import Settings, get_settings
from app.integrations.openai.client import get_openai_client

OPENAI_API_KEY_VARIABLE = "OPENAI_API_KEY"


@dataclass(frozen=True)
class OpenAIAuthStatus:
    status: str
    api_key_found: bool
    client_initialized: bool
    required_variable: str
    model: str
    timeout_seconds: float
    message: str

    def to_response(self) -> dict[str, str | bool | float]:
        return asdict(self)


def get_openai_auth_status(
    settings: Settings | None = None,
    *,
    initialize_client: bool = True,
) -> OpenAIAuthStatus:
    settings = settings or get_settings()
    api_key_found = bool(settings.openai_api_key and settings.openai_api_key.strip())

    if not api_key_found:
        return OpenAIAuthStatus(
            status="missing",
            api_key_found=False,
            client_initialized=False,
            required_variable=OPENAI_API_KEY_VARIABLE,
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            message=(
                "OpenAI API key missing. Set OPENAI_API_KEY in backend/.env for local "
                "backend runs or root .env for Docker Compose."
            ),
        )

    if not initialize_client:
        return OpenAIAuthStatus(
            status="configured",
            api_key_found=True,
            client_initialized=False,
            required_variable=OPENAI_API_KEY_VARIABLE,
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            message="OpenAI API key found.",
        )

    try:
        get_openai_client(settings=settings)
    except Exception as error:
        return OpenAIAuthStatus(
            status="error",
            api_key_found=True,
            client_initialized=False,
            required_variable=OPENAI_API_KEY_VARIABLE,
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            message=f"OpenAI API key found, but client initialization failed: {error}",
        )

    return OpenAIAuthStatus(
        status="ok",
        api_key_found=True,
        client_initialized=True,
        required_variable=OPENAI_API_KEY_VARIABLE,
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
        message="OpenAI API key found and SDK client initialized.",
    )
