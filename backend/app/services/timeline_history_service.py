from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.schemas.timeline_branching import TimelineCommitRead, TimelineEventRead


class TimelineHistoryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_timeline(self, timeline_id: uuid.UUID) -> Timeline:
        timeline = self._db.get(Timeline, timeline_id)
        if timeline is None:
            raise NotFoundError("Timeline", timeline_id)
        return timeline

    def commit_chain(self, timeline_id: uuid.UUID) -> list[TimelineCommit]:
        timeline = self.get_timeline(timeline_id)
        if timeline.head_commit_id is None:
            return []

        commits_by_id: dict[uuid.UUID, TimelineCommit] = {}
        current_id = timeline.head_commit_id
        seen: set[uuid.UUID] = set()
        while current_id is not None and current_id not in seen:
            seen.add(current_id)
            commit = self._db.get(TimelineCommit, current_id)
            if commit is None:
                break
            commits_by_id[commit.id] = commit
            current_id = commit.parent_commit_id

        return list(reversed(commits_by_id.values()))

    def commit_ids(self, timeline_id: uuid.UUID) -> list[uuid.UUID]:
        return [commit.id for commit in self.commit_chain(timeline_id)]

    def commits(self, timeline_id: uuid.UUID) -> list[TimelineCommitRead]:
        return [self._commit_read(commit) for commit in self.commit_chain(timeline_id)]

    def events(self, timeline_id: uuid.UUID) -> list[TimelineEventRead]:
        commit_ids = self.commit_ids(timeline_id)
        if not commit_ids:
            return []

        links = (
            self._db.scalars(
                select(TimelineCommitEvent)
                .where(TimelineCommitEvent.commit_id.in_(commit_ids))
                .options(
                    joinedload(TimelineCommitEvent.commit),
                    joinedload(TimelineCommitEvent.event)
                    .joinedload(Event.participants)
                    .joinedload(EventParticipant.character),
                    joinedload(TimelineCommitEvent.event).joinedload(Event.location),
                )
            )
            .unique()
            .all()
        )

        commit_rank = {commit_id: index for index, commit_id in enumerate(commit_ids)}
        ordered_links = sorted(
            links,
            key=lambda link: (
                link.event.order_index if link.event.order_index is not None else 10_000,
                commit_rank.get(link.commit_id, 10_000),
                link.event.created_at,
            ),
        )
        return [self._event_read(link) for link in ordered_links]

    def _event_read(self, link: TimelineCommitEvent) -> TimelineEventRead:
        event = link.event
        return TimelineEventRead(
            id=event.id,
            created_at=event.created_at,
            updated_at=event.updated_at,
            title=event.title,
            summary=event.summary,
            event_type=event.event_type,
            order_index=event.order_index,
            importance=event.importance,
            location_id=event.location_id,
            location_name=event.location.name if event.location else None,
            participants=[
                participant.character.canonical_name
                for participant in event.participants
                if participant.character is not None
            ],
            commit_id=link.commit_id,
            commit_message=link.commit.message,
            commit_type=link.commit.commit_type,
            change_type=link.change_type,
        )

    def _commit_read(self, commit: TimelineCommit) -> TimelineCommitRead:
        return TimelineCommitRead(
            id=commit.id,
            created_at=commit.created_at,
            updated_at=commit.updated_at,
            timeline_id=commit.timeline_id,
            parent_commit_id=commit.parent_commit_id,
            message=commit.message,
            commit_type=commit.commit_type,
            created_by=commit.created_by,
        )
