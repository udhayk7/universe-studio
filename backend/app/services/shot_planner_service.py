from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.episode import Episode
from app.db.models.scene import Scene
from app.db.models.scene_participant import SceneParticipant
from app.db.models.shot import Shot


class ShotPlannerService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def plan_episode(self, episode_id: uuid.UUID) -> list[Shot]:
        if self._db.get(Episode, episode_id) is None:
            raise NotFoundError("Episode", episode_id)

        scenes = self._load_scenes(episode_id)
        shots: list[Shot] = []
        for scene in scenes:
            existing = self._db.scalar(
                select(Shot).where(Shot.scene_id == scene.id, Shot.shot_number == 1)
            )
            if existing is not None:
                shots.append(existing)
                continue

            shot = Shot(
                episode_id=episode_id,
                scene_id=scene.id,
                shot_number=1,
                shot_type=self._shot_type(scene),
                camera_angle=self._camera_angle(scene),
                duration_seconds=self._duration(scene),
                visual_description=self._visual_description(scene),
                status="planned",
            )
            self._db.add(shot)
            self._db.flush()
            shots.append(shot)
        return shots

    def _load_scenes(self, episode_id: uuid.UUID) -> list[Scene]:
        statement = (
            select(Scene)
            .where(Scene.episode_id == episode_id)
            .options(
                joinedload(Scene.location),
                joinedload(Scene.participants).joinedload(SceneParticipant.character),
            )
            .order_by(Scene.scene_number.asc())
        )
        return list(self._db.scalars(statement).unique())

    def _shot_type(self, scene: Scene) -> str:
        participant_count = len(scene.participants)
        if scene.scene_number == 1:
            return "establishing wide shot"
        if participant_count >= 3:
            return "ensemble medium-wide shot"
        if participant_count == 2:
            return "cinematic two-shot"
        if scene.summary and any(
            keyword in scene.summary.lower() for keyword in ("reveal", "secret", "realizes")
        ):
            return "intimate close-up"
        return "motivated medium shot"

    def _camera_angle(self, scene: Scene) -> str:
        text = f"{scene.summary or ''} {scene.visual_direction or ''}".lower()
        if any(keyword in text for keyword in ("power", "control", "threat", "betray")):
            return "low angle with controlled negative space"
        if any(keyword in text for keyword in ("lost", "broken", "isolated", "fear")):
            return "slight high angle with isolating composition"
        if scene.scene_number % 3 == 0:
            return "over-the-shoulder perspective"
        return "eye-level cinematic perspective"

    def _duration(self, scene: Scene) -> float:
        return round(min(14.0, max(6.0, 7.0 + len(scene.participants) * 1.25)), 2)

    def _visual_description(self, scene: Scene) -> str:
        location = scene.location.name if scene.location else "an unspecified location"
        participants = ", ".join(
            participant.character.canonical_name for participant in scene.participants
        )
        character_text = participants or "the scene's central characters"
        visual_direction = scene.visual_direction or scene.summary or "A tense cinematic moment."
        return (
            f"{visual_direction} The frame is set at {location}, centered on {character_text}, "
            "with a premium sci-fi cinematic mood and clear story action."
        )
