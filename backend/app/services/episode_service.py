from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.episode import Episode
from app.db.models.scene import Scene
from app.db.models.scene_participant import SceneParticipant
from app.schemas.episode_generation import (
    EpisodeParticipantRead,
    EpisodeRead,
    EpisodeSceneRead,
)


class EpisodeService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, episode_id: uuid.UUID) -> EpisodeRead:
        episode = self._db.get(Episode, episode_id)
        if episode is None:
            raise NotFoundError("Episode", episode_id)

        scene_count = self._db.scalar(
            select(func.count()).select_from(Scene).where(Scene.episode_id == episode.id)
        )
        return EpisodeRead(
            id=episode.id,
            created_at=episode.created_at,
            updated_at=episode.updated_at,
            universe_id=episode.universe_id,
            timeline_id=episode.timeline_id,
            commit_id=episode.commit_id,
            title=episode.title,
            logline=episode.logline,
            summary=episode.summary,
            status=episode.status,
            scene_count=int(scene_count or 0),
        )

    def scenes(self, episode_id: uuid.UUID) -> list[EpisodeSceneRead]:
        if self._db.get(Episode, episode_id) is None:
            raise NotFoundError("Episode", episode_id)

        statement = (
            select(Scene)
            .where(Scene.episode_id == episode_id)
            .options(
                joinedload(Scene.location),
                joinedload(Scene.participants).joinedload(SceneParticipant.character),
            )
            .order_by(Scene.scene_number.asc())
        )
        return [self._scene_read(scene) for scene in self._db.scalars(statement).unique()]

    def _scene_read(self, scene: Scene) -> EpisodeSceneRead:
        return EpisodeSceneRead(
            id=scene.id,
            created_at=scene.created_at,
            updated_at=scene.updated_at,
            episode_id=scene.episode_id,
            location_id=scene.location_id,
            location_name=scene.location.name if scene.location else None,
            scene_number=scene.scene_number,
            title=scene.title,
            summary=scene.summary,
            dialogue=scene.dialogue,
            visual_direction=scene.visual_direction,
            participants=[
                EpisodeParticipantRead(
                    character_id=participant.character_id,
                    character_name=participant.character.canonical_name,
                    role=participant.role,
                )
                for participant in scene.participants
            ],
        )
