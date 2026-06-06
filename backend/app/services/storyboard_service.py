from __future__ import annotations

import base64
import html
import textwrap
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.episode import Episode
from app.db.models.scene import Scene
from app.db.models.scene_participant import SceneParticipant
from app.db.models.shot import Shot
from app.db.models.storyboard_image import StoryboardImage
from app.integrations.openai.image_generation import (
    GeneratedStoryboardImage,
    OpenAIStoryboardImageProvider,
)
from app.schemas.episode_generation import EpisodeParticipantRead
from app.schemas.storyboard import (
    EpisodeStoryboardRead,
    ShotRead,
    StoryboardImageRead,
    StoryboardSceneRead,
)
from app.services.shot_planner_service import ShotPlannerService


class StoryboardService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._settings = get_settings()

    def get_shot(self, shot_id: uuid.UUID) -> ShotRead:
        statement = (
            select(Shot)
            .where(Shot.id == shot_id)
            .options(joinedload(Shot.scene), joinedload(Shot.storyboard_image))
        )
        shot = self._db.scalar(statement)
        if shot is None:
            raise NotFoundError("Shot", shot_id)
        return self._shot_read(shot)

    def get_storyboard(self, episode_id: uuid.UUID) -> EpisodeStoryboardRead:
        episode = self._db.get(Episode, episode_id)
        if episode is None:
            raise NotFoundError("Episode", episode_id)

        scenes = self._load_storyboard_scenes(episode_id)
        shot_count = self._db.scalar(
            select(func.count()).select_from(Shot).where(Shot.episode_id == episode_id)
        )
        image_count = self._db.scalar(
            select(func.count())
            .select_from(StoryboardImage)
            .where(
                StoryboardImage.episode_id == episode_id,
                StoryboardImage.image_data.is_not(None) | StoryboardImage.image_url.is_not(None),
            )
        )
        return EpisodeStoryboardRead(
            episode_id=episode.id,
            universe_id=episode.universe_id,
            title=episode.title,
            summary=episode.summary,
            scene_count=len(scenes),
            shot_count=int(shot_count or 0),
            generated_image_count=int(image_count or 0),
            scenes=[self._scene_read(scene) for scene in scenes],
        )

    def render_episode(
        self,
        episode_id: uuid.UUID,
        *,
        regenerate_images: bool = False,
    ) -> EpisodeStoryboardRead:
        if self._db.get(Episode, episode_id) is None:
            raise NotFoundError("Episode", episode_id)

        ShotPlannerService(self._db).plan_episode(episode_id)
        shots = self._load_shots(episode_id)
        for shot in shots:
            prompt = self._build_prompt(shot)
            shot.prompt = prompt
            if shot.storyboard_image is not None and not regenerate_images:
                continue

            result = self._generate_image(prompt=prompt, shot=shot)
            self._upsert_storyboard_image(shot=shot, prompt=prompt, result=result)
            shot.status = "storyboarded"
            self._db.add(shot)

        self._db.commit()
        return self.get_storyboard(episode_id)

    def _load_storyboard_scenes(self, episode_id: uuid.UUID) -> list[Scene]:
        statement = (
            select(Scene)
            .where(Scene.episode_id == episode_id)
            .options(
                joinedload(Scene.location),
                joinedload(Scene.participants).joinedload(SceneParticipant.character),
                joinedload(Scene.shots).joinedload(Shot.storyboard_image),
            )
            .order_by(Scene.scene_number.asc())
        )
        return list(self._db.scalars(statement).unique())

    def _load_shots(self, episode_id: uuid.UUID) -> list[Shot]:
        statement = (
            select(Shot)
            .join(Shot.scene)
            .where(Shot.episode_id == episode_id)
            .options(
                joinedload(Shot.episode),
                joinedload(Shot.scene).joinedload(Scene.location),
                joinedload(Shot.scene)
                .joinedload(Scene.participants)
                .joinedload(SceneParticipant.character),
                joinedload(Shot.storyboard_image),
            )
            .order_by(Scene.scene_number.asc(), Shot.shot_number.asc())
        )
        return list(self._db.scalars(statement).unique())

    def _generate_image(self, *, prompt: str, shot: Shot) -> GeneratedStoryboardImage:
        if not self._settings.openai_api_key:
            return self._placeholder_image(
                shot=shot,
                prompt=prompt,
                error="OPENAI_API_KEY is missing; stored storyboard placeholder.",
            )

        try:
            return OpenAIStoryboardImageProvider(settings=self._settings).generate(prompt)
        except Exception as error:
            return self._placeholder_image(
                shot=shot,
                prompt=prompt,
                error=f"OpenAI image generation failed: {error}",
            )

    def _upsert_storyboard_image(
        self,
        *,
        shot: Shot,
        prompt: str,
        result: GeneratedStoryboardImage,
    ) -> None:
        image = shot.storyboard_image
        if image is None:
            image = StoryboardImage(
                episode_id=shot.episode_id,
                scene_id=shot.scene_id,
                shot_id=shot.id,
                provider=result.provider,
                prompt=prompt,
            )

        image.provider = result.provider
        image.model = result.model
        image.status = result.status
        image.mime_type = result.mime_type
        image.image_data = result.image_data
        image.image_url = result.image_url
        image.prompt = prompt
        image.revised_prompt = result.revised_prompt
        image.width = result.width
        image.height = result.height
        image.error = result.error
        image.generated_at = datetime.now(UTC)
        self._db.add(image)

    def _build_prompt(self, shot: Shot) -> str:
        scene = shot.scene
        episode = shot.episode
        location = scene.location
        characters = [participant.character for participant in scene.participants]
        character_context = "\n".join(
            self._character_prompt_line(character) for character in characters
        )
        if not character_context:
            character_context = "- No named characters recorded; focus on the scene action."

        location_context = (
            f"{location.name}: "
            f"{location.description or location.location_type or 'cinematic setting'}"
            if location
            else "Unspecified location: preserve the scene's described environment."
        )
        return textwrap.dedent(
            f"""
            Create one cinematic storyboard frame for Universe Studio.

            Rules:
            - No captions, subtitles, watermarks, UI, speech bubbles, or visible text.
            - Preserve character identity and wardrobe cues from the prompt.
            - Preserve the location and story action.
            - Make it feel like a premium sci-fi film storyboard with dramatic lighting.
            - Compose as a landscape frame suitable for a director's board.

            Episode: {episode.title}
            Scene {scene.scene_number}: {scene.title or "Untitled Scene"}
            Location: {location_context}
            Shot type: {shot.shot_type}
            Camera angle: {shot.camera_angle}
            Duration: {shot.duration_seconds} seconds
            Visual description: {shot.visual_description}
            Scene outcome: {scene.summary or "No scene outcome recorded."}

            Characters:
            {character_context}
            """
        ).strip()

    def _character_prompt_line(self, character: Character) -> str:
        traits = self._flatten_json_strings(character.traits)
        goals = self._flatten_json_strings(character.goals)
        details = ", ".join(part for part in [character.description, traits, goals] if part)
        presence = details or "distinct cinematic presence"
        return f"- {character.canonical_name} ({character.status}): {presence}"

    def _flatten_json_strings(self, value: object) -> str | None:
        if isinstance(value, dict):
            parts: list[str] = []
            for item in value.values():
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, list):
                    parts.extend(str(entry) for entry in item if entry)
            return ", ".join(parts[:6]) or None
        if isinstance(value, list):
            return ", ".join(str(item) for item in value[:6] if item) or None
        return None

    def _placeholder_image(
        self,
        *,
        shot: Shot,
        prompt: str,
        error: str,
    ) -> GeneratedStoryboardImage:
        svg = self._placeholder_svg(shot)
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return GeneratedStoryboardImage(
            provider="fallback",
            model=self._settings.openai_image_model,
            status="placeholder",
            mime_type="image/svg+xml",
            image_data=encoded,
            image_url=None,
            revised_prompt=prompt,
            width=1536,
            height=1024,
            error=error,
        )

    def _placeholder_svg(self, shot: Shot) -> str:
        title = html.escape(shot.scene.title or f"Scene {shot.scene.scene_number}")
        shot_label = html.escape(f"{shot.shot_type} / {shot.camera_angle}")
        description = html.escape(shot.visual_description)
        lines = textwrap.wrap(description, width=72)[:5]
        text_lines = "\n".join(
            f'<text x="96" y="{430 + index * 44}" class="body">{line}</text>'
            for index, line in enumerate(lines)
        )
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024"
viewBox="0 0 1536 1024">
<defs>
<linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
<stop offset="0%" stop-color="#020617"/>
<stop offset="50%" stop-color="#111827"/>
<stop offset="100%" stop-color="#312e81"/>
</linearGradient>
<style>
.eyebrow {{ fill: #93c5fd; font-family: Inter, Arial, sans-serif; font-size: 28px;
letter-spacing: 8px; }}
.title {{ fill: #ffffff; font-family: Inter, Arial, sans-serif; font-size: 72px;
font-weight: 700; }}
.meta {{ fill: #d8b4fe; font-family: Inter, Arial, sans-serif; font-size: 32px; }}
.body {{ fill: #cbd5e1; font-family: Inter, Arial, sans-serif; font-size: 30px; }}
</style>
</defs>
<rect width="1536" height="1024" fill="url(#bg)"/>
<rect x="56" y="56" width="1424" height="912" rx="36" fill="none"
stroke="#ffffff" stroke-opacity="0.18" stroke-width="2"/>
<circle cx="1230" cy="250" r="260" fill="#38bdf8" fill-opacity="0.12"/>
<circle cx="1040" cy="780" r="320" fill="#8b5cf6" fill-opacity="0.16"/>
<text x="96" y="190" class="eyebrow">STORYBOARD FRAME</text>
<text x="96" y="292" class="title">{title}</text>
<text x="96" y="360" class="meta">{shot_label}</text>
{text_lines}
<text x="96" y="890" class="eyebrow">OPENAI IMAGE PLACEHOLDER</text>
</svg>"""

    def _scene_read(self, scene: Scene) -> StoryboardSceneRead:
        return StoryboardSceneRead(
            scene_id=scene.id,
            scene_number=scene.scene_number,
            title=scene.title,
            location_name=scene.location.name if scene.location else None,
            summary=scene.summary,
            visual_direction=scene.visual_direction,
            participants=[
                EpisodeParticipantRead(
                    character_id=participant.character_id,
                    character_name=participant.character.canonical_name,
                    role=participant.role,
                )
                for participant in scene.participants
            ],
            shots=[
                self._shot_read(shot)
                for shot in sorted(scene.shots, key=lambda item: item.shot_number)
            ],
        )

    def _shot_read(self, shot: Shot) -> ShotRead:
        return ShotRead(
            id=shot.id,
            created_at=shot.created_at,
            updated_at=shot.updated_at,
            episode_id=shot.episode_id,
            scene_id=shot.scene_id,
            scene_number=shot.scene.scene_number,
            scene_title=shot.scene.title,
            shot_number=shot.shot_number,
            shot_type=shot.shot_type,
            camera_angle=shot.camera_angle,
            duration_seconds=shot.duration_seconds,
            visual_description=shot.visual_description,
            prompt=shot.prompt,
            status=shot.status,
            storyboard_image=self._image_read(shot.storyboard_image),
        )

    def _image_read(self, image: StoryboardImage | None) -> StoryboardImageRead | None:
        if image is None:
            return None
        return StoryboardImageRead(
            id=image.id,
            created_at=image.created_at,
            updated_at=image.updated_at,
            episode_id=image.episode_id,
            scene_id=image.scene_id,
            shot_id=image.shot_id,
            provider=image.provider,
            model=image.model,
            status=image.status,
            mime_type=image.mime_type,
            image_data=image.image_data,
            image_url=image.image_url,
            prompt=image.prompt,
            revised_prompt=image.revised_prompt,
            width=image.width,
            height=image.height,
            error=image.error,
            generated_at=image.generated_at,
        )
