from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VideoRenderRequest:
    shot_id: str
    prompt: str
    image_url: str | None = None
    duration_seconds: float | None = None


@dataclass(frozen=True)
class VideoRenderResult:
    provider: str
    status: str
    video_url: str | None = None
    error: str | None = None


class VideoProvider(Protocol):
    provider_name: str

    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        raise NotImplementedError


class _FutureVideoProvider:
    provider_name = "future"

    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        return VideoRenderResult(
            provider=self.provider_name,
            status="not_implemented",
            error="Video generation provider adapter is reserved for a future media phase.",
        )


class RunwayVideoProvider(_FutureVideoProvider):
    provider_name = "runway"


class VeoVideoProvider(_FutureVideoProvider):
    provider_name = "veo"


class KlingVideoProvider(_FutureVideoProvider):
    provider_name = "kling"


class LumaVideoProvider(_FutureVideoProvider):
    provider_name = "luma"
