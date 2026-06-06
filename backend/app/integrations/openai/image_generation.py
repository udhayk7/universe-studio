from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.integrations.openai.client import get_openai_client
from openai import OpenAI


@dataclass(frozen=True)
class GeneratedStoryboardImage:
    provider: str
    model: str
    status: str
    mime_type: str
    image_data: str | None
    image_url: str | None
    revised_prompt: str | None
    width: int | None
    height: int | None
    error: str | None = None


class OpenAIStoryboardImageProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or get_openai_client(settings=self._settings)

    def generate(self, prompt: str) -> GeneratedStoryboardImage:
        response = self._client.images.generate(
            model=self._settings.openai_image_model,
            prompt=prompt,
            size=self._settings.openai_image_size,
            quality=self._settings.openai_image_quality,
            response_format="b64_json",
            output_format="png",
            n=1,
        )
        image = response.data[0]
        width, height = _parse_size(self._settings.openai_image_size)
        return GeneratedStoryboardImage(
            provider=self.provider_name,
            model=self._settings.openai_image_model,
            status="generated",
            mime_type="image/png",
            image_data=image.b64_json,
            image_url=image.url,
            revised_prompt=image.revised_prompt,
            width=width,
            height=height,
        )


def _parse_size(size: str) -> tuple[int | None, int | None]:
    try:
        width, height = size.lower().split("x", 1)
        return int(width), int(height)
    except ValueError:
        return None, None
