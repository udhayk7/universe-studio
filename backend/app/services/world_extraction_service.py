from __future__ import annotations

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.integrations.openai import get_openai_client
from app.schemas.extraction import UniverseExtraction
from app.schemas.source import SourcePayload

WORLD_ARCHITECT_INSTRUCTIONS = """
You are the World Architect for Universe Studio.

Extract a persistent cinematic universe from the submitted source.
Return only the structured output requested by the schema.

Rules:
- Do not write episode scripts.
- Do not create timeline branches.
- Do not perform consistency checks.
- If the source is only a short idea, infer a strong starter universe.
- Create durable facts that can be persisted as world memory.
- Prefer specific names, concrete places, meaningful objects, and causally connected events.
- Relationship types should be concise uppercase labels such as KNOWS, LOVES, BETRAYED,
  RIVALS, MENTORS, PROTECTS, FEARS, or ALLIES.
- Strength is -100 to 100, where negative values indicate conflict or harm.
- Produce enough material for a demo: 3-6 characters, 2-5 locations, 2-5 objects,
  4-8 events, and 3-8 character relationships when possible.
"""


class WorldExtractionService:
    def __init__(self, client: OpenAI | None = None) -> None:
        self._settings = get_settings()
        self._client = client or get_openai_client()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def extract(self, payload: SourcePayload) -> UniverseExtraction:
        response = self._client.responses.parse(
            model=self._settings.openai_model,
            instructions=WORLD_ARCHITECT_INSTRUCTIONS,
            input=self._build_input(payload),
            text_format=UniverseExtraction,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("OpenAI response did not contain structured extraction data.")

        return UniverseExtraction.model_validate(parsed)

    def _build_input(self, payload: SourcePayload) -> str:
        hints = []
        if payload.title_hint:
            hints.append(f"Title hint: {payload.title_hint}")
        if payload.genre_hint:
            hints.append(f"Genre hint: {payload.genre_hint}")
        if payload.tone_hint:
            hints.append(f"Tone hint: {payload.tone_hint}")
        if payload.filename:
            hints.append(f"Uploaded filename: {payload.filename}")

        hints_text = "\n".join(hints) if hints else "No user hints provided."
        return (
            f"Source type: {payload.source_type}\n"
            f"{hints_text}\n\n"
            "Source content:\n"
            f"{payload.content}"
        )
