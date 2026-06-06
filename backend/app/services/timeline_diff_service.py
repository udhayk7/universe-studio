from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.relationship import Relationship
from app.db.models.timeline import Timeline
from app.schemas.timeline_branching import (
    TimelineDiffEvent,
    TimelineDiffRelationship,
    TimelineDiffResponse,
    TimelineDiffState,
    TimelineEventRead,
)
from app.services.timeline_history_service import TimelineHistoryService


class TimelineDiffService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._history = TimelineHistoryService(db)

    def diff(
        self,
        *,
        base_timeline_id: uuid.UUID,
        compare_timeline_id: uuid.UUID,
    ) -> TimelineDiffResponse:
        base = self._get_timeline(base_timeline_id)
        compare = self._get_timeline(compare_timeline_id)
        if base.universe_id != compare.universe_id:
            raise ValueError("Timeline diff requires timelines from the same universe.")

        return TimelineDiffResponse(
            base_timeline_id=base.id,
            compare_timeline_id=compare.id,
            base_timeline_name=base.name,
            compare_timeline_name=compare.name,
            changed_events=self._event_diff(base.id, compare.id),
            relationship_differences=self._relationship_diff(base.id, compare.id),
            state_differences=self._state_diff(base.id, compare.id),
        )

    def _event_diff(
        self,
        base_timeline_id: uuid.UUID,
        compare_timeline_id: uuid.UUID,
    ) -> list[TimelineDiffEvent]:
        base_events = self._history.events(base_timeline_id)
        compare_events = self._history.events(compare_timeline_id)
        base_by_id = {event.id: event for event in base_events}
        compare_by_id = {event.id: event for event in compare_events}
        diffs: list[TimelineDiffEvent] = []

        for event in compare_events:
            if event.id in base_by_id:
                continue
            if event.event_type == "timeline_branch_modification":
                base_event = self._nearest_base_event(event, base_events)
                diffs.append(
                    TimelineDiffEvent(
                        kind="modified",
                        title=event.title,
                        base_summary=base_event.summary if base_event else None,
                        compare_summary=event.summary,
                        order_index=event.order_index,
                    )
                )
            else:
                diffs.append(
                    TimelineDiffEvent(
                        kind="added",
                        title=event.title,
                        compare_summary=event.summary,
                        order_index=event.order_index,
                    )
                )

        for event in base_events:
            if event.id not in compare_by_id and not self._has_matching_order(
                event,
                compare_events,
            ):
                diffs.append(
                    TimelineDiffEvent(
                        kind="removed",
                        title=event.title,
                        base_summary=event.summary,
                        order_index=event.order_index,
                    )
                )
        return diffs

    def _relationship_diff(
        self,
        base_timeline_id: uuid.UUID,
        compare_timeline_id: uuid.UUID,
    ) -> list[TimelineDiffRelationship]:
        base_relationships = self._relationships(base_timeline_id)
        compare_relationships = self._relationships(compare_timeline_id)
        keys = sorted(set(base_relationships) | set(compare_relationships))
        diffs: list[TimelineDiffRelationship] = []

        for key in keys:
            base = base_relationships.get(key)
            compare = compare_relationships.get(key)
            if (
                base
                and compare
                and base.strength == compare.strength
                and base.status == compare.status
            ):
                continue
            relationship = compare or base
            if relationship is None:
                continue
            diffs.append(
                TimelineDiffRelationship(
                    source_character=relationship.source_character.canonical_name,
                    target_character=relationship.target_character.canonical_name,
                    relationship_type=relationship.relationship_type,
                    base_strength=base.strength if base else None,
                    compare_strength=compare.strength if compare else None,
                    base_status=base.status if base else None,
                    compare_status=compare.status if compare else None,
                )
            )
        return diffs

    def _state_diff(
        self,
        base_timeline_id: uuid.UUID,
        compare_timeline_id: uuid.UUID,
    ) -> list[TimelineDiffState]:
        base_states = self._latest_states(base_timeline_id)
        compare_states = self._latest_states(compare_timeline_id)
        keys = sorted(set(base_states) | set(compare_states))
        diffs: list[TimelineDiffState] = []

        for character_id in keys:
            base = base_states.get(character_id)
            compare = compare_states.get(character_id)
            if (
                base
                and compare
                and base.current_status == compare.current_status
                and base.emotional_state == compare.emotional_state
                and base.summary == compare.summary
            ):
                continue
            state = compare or base
            if state is None:
                continue
            diffs.append(
                TimelineDiffState(
                    character=state.character.canonical_name,
                    base_status=base.current_status if base else None,
                    compare_status=compare.current_status if compare else None,
                    base_emotional_state=base.emotional_state if base else None,
                    compare_emotional_state=compare.emotional_state if compare else None,
                    base_summary=base.summary if base else None,
                    compare_summary=compare.summary if compare else None,
                )
            )
        return diffs

    def _relationships(
        self,
        timeline_id: uuid.UUID,
    ) -> dict[tuple[uuid.UUID, uuid.UUID, str], Relationship]:
        relationships = self._db.scalars(
            select(Relationship)
            .where(Relationship.timeline_id == timeline_id, Relationship.status == "active")
            .options(
                joinedload(Relationship.source_character),
                joinedload(Relationship.target_character),
            )
        ).all()
        return {
            (
                relationship.source_character_id,
                relationship.target_character_id,
                relationship.relationship_type,
            ): relationship
            for relationship in relationships
        }

    def _latest_states(self, timeline_id: uuid.UUID) -> dict[uuid.UUID, CharacterStateHistory]:
        states = self._db.scalars(
            select(CharacterStateHistory)
            .where(CharacterStateHistory.timeline_id == timeline_id)
            .options(joinedload(CharacterStateHistory.character))
            .order_by(CharacterStateHistory.created_at.asc())
        ).all()
        latest: dict[uuid.UUID, CharacterStateHistory] = {}
        for state in states:
            latest[state.character_id] = state
        return latest

    def _nearest_base_event(
        self,
        compare_event: TimelineEventRead,
        base_events: list[TimelineEventRead],
    ) -> TimelineEventRead | None:
        if compare_event.order_index is None:
            return None
        for event in base_events:
            if event.order_index == compare_event.order_index:
                return event
        return None

    def _has_matching_order(
        self,
        base_event: TimelineEventRead,
        compare_events: list[TimelineEventRead],
    ) -> bool:
        return (
            base_event.order_index is not None
            and any(event.order_index == base_event.order_index for event in compare_events)
        )

    def _get_timeline(self, timeline_id: uuid.UUID) -> Timeline:
        timeline = self._db.get(Timeline, timeline_id)
        if timeline is None:
            raise NotFoundError("Timeline", timeline_id)
        return timeline
