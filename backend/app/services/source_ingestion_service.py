from __future__ import annotations

from app.core.config import get_settings
from app.schemas.source import SourcePayload, SourceType


class SourceIngestionService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def build_payload(
        self,
        *,
        source_type: SourceType,
        content: str | None = None,
        file_bytes: bytes | None = None,
        filename: str | None = None,
        mime_type: str | None = None,
        title_hint: str | None = None,
        genre_hint: str | None = None,
        tone_hint: str | None = None,
    ) -> SourcePayload:
        source_content = self._extract_file_text(file_bytes, filename) if file_bytes else content
        normalized = self._normalize_content(source_content)

        return SourcePayload(
            source_type=source_type,
            content=normalized,
            title_hint=self._blank_to_none(title_hint),
            genre_hint=self._blank_to_none(genre_hint),
            tone_hint=self._blank_to_none(tone_hint),
            filename=self._blank_to_none(filename),
            mime_type=self._blank_to_none(mime_type),
        )

    def _normalize_content(self, content: str | None) -> str:
        if not content or not content.strip():
            raise ValueError("Source content is required.")

        normalized = "\n".join(line.rstrip() for line in content.replace("\r\n", "\n").split("\n"))
        normalized = normalized.strip()
        max_chars = self._settings.universe_extraction_max_chars
        if len(normalized) > max_chars:
            normalized = normalized[:max_chars].rstrip()
        return normalized

    def _extract_file_text(self, file_bytes: bytes | None, filename: str | None) -> str:
        if not file_bytes:
            raise ValueError("Uploaded screenplay is empty.")

        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            name = filename or "uploaded file"
            raise ValueError(
                f"{name} could not be read as text. Upload TXT, Fountain, or FDX for this MVP."
            ) from error

    def _blank_to_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
