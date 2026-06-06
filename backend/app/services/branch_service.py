from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.agents.timeline_agents import TimelineAgentRunner
from app.core.exceptions import NotFoundError
from app.db.models.agent_run import AgentRun
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.schemas.timeline_branching import (
    TimelineBranchCreate,
    TimelineBranchRead,
    TimelineCommitRead,
    TimelineEventRead,
    TimelineImpactAnalysis,
)
from app.services.timeline_history_service import TimelineHistoryService


class BranchService:
    def __init__(
        self,
        db: Session,
        *,
        timeline_agent: TimelineAgentRunner | None = None,
    ) -> None:
        self._db = db
        self._history = TimelineHistoryService(db)
        self._timeline_agent = timeline_agent

    def create_branch(
        self,
        *,
        source_timeline_id: uuid.UUID,
        payload: TimelineBranchCreate,
    ) -> TimelineBranchRead:
        source_timeline = self._history.get_timeline(source_timeline_id)
        branch_point_commit = self._resolve_branch_commit(source_timeline, payload)
        source_event = self._resolve_source_event(source_timeline, payload, branch_point_commit)
        source_event = self._load_event(source_event.id) if source_event else None

        impact = self._analyze_impact(source_timeline, branch_point_commit, source_event, payload)

        branch = Timeline(
            universe_id=source_timeline.universe_id,
            parent_timeline_id=source_timeline.id,
            branch_from_commit_id=branch_point_commit.id,
            name=payload.name
            or self._default_branch_name(source_event, payload.new_outcome),
            is_canon=False,
        )
        self._db.add(branch)
        self._db.flush()

        branch_commit = TimelineCommit(
            timeline_id=branch.id,
            parent_commit_id=branch_point_commit.id,
            message=f"Branch divergence: {payload.new_outcome[:180]}",
            commit_type="timeline_branch",
            created_by="timeline_agent",
        )
        self._db.add(branch_commit)
        self._db.flush()

        self._copy_inherited_memory(
            source_timeline=source_timeline,
            branch=branch,
            branch_commit=branch_commit,
            branch_point_commit=branch_point_commit,
        )
        self._copy_relationships(source_timeline, branch)

        modified_event = self._create_modified_event(
            branch=branch,
            branch_commit=branch_commit,
            source_event=source_event,
            payload=payload,
        )
        self._store_branch_memory(
            branch=branch,
            branch_commit=branch_commit,
            modified_event=modified_event,
            impact=impact,
            new_outcome=payload.new_outcome,
        )
        self._apply_character_state_impacts(
            branch=branch,
            branch_commit=branch_commit,
            modified_event=modified_event,
            impact=impact,
            new_outcome=payload.new_outcome,
        )

        branch.head_commit_id = branch_commit.id
        self._db.add(branch)
        self._db.commit()
        self._db.refresh(branch)
        self._db.refresh(branch_commit)
        self._db.refresh(modified_event)

        return TimelineBranchRead(
            timeline=branch,
            branch_commit=self._commit_read(branch_commit),
            modified_event=self._event_read(modified_event, branch_commit),
            impact=impact,
        )

    def _resolve_branch_commit(
        self,
        source_timeline: Timeline,
        payload: TimelineBranchCreate,
    ) -> TimelineCommit:
        commit_ids = self._history.commit_ids(source_timeline.id)
        if payload.commit_id:
            if payload.commit_id not in commit_ids:
                raise NotFoundError("TimelineCommit", payload.commit_id)
            commit = self._db.get(TimelineCommit, payload.commit_id)
            if commit is None:
                raise NotFoundError("TimelineCommit", payload.commit_id)
            return commit

        if payload.event_id is None:
            raise ValueError("event_id or commit_id is required to create a branch.")

        link = self._db.scalar(
            select(TimelineCommitEvent)
            .where(
                TimelineCommitEvent.event_id == payload.event_id,
                TimelineCommitEvent.commit_id.in_(commit_ids),
            )
            .order_by(TimelineCommitEvent.created_at.desc())
            .limit(1)
        )
        if link is None:
            raise NotFoundError("TimelineEvent", payload.event_id)

        commit = self._db.get(TimelineCommit, link.commit_id)
        if commit is None:
            raise NotFoundError("TimelineCommit", link.commit_id)
        return commit

    def _resolve_source_event(
        self,
        source_timeline: Timeline,
        payload: TimelineBranchCreate,
        branch_point_commit: TimelineCommit,
    ) -> Event | None:
        if payload.event_id:
            event = self._db.get(Event, payload.event_id)
            if event is None:
                raise NotFoundError("Event", payload.event_id)
            visible_event_ids = {
                event_read.id for event_read in self._history.events(source_timeline.id)
            }
            if event.id not in visible_event_ids:
                raise NotFoundError("TimelineEvent", payload.event_id)
            return event

        link = self._db.scalar(
            select(TimelineCommitEvent)
            .where(TimelineCommitEvent.commit_id == branch_point_commit.id)
            .limit(1)
        )
        return self._db.get(Event, link.event_id) if link else None

    def _load_event(self, event_id: uuid.UUID) -> Event:
        event = self._db.scalar(
            select(Event)
            .where(Event.id == event_id)
            .options(
                joinedload(Event.location),
                joinedload(Event.participants).joinedload(EventParticipant.character),
            )
        )
        if event is None:
            raise NotFoundError("Event", event_id)
        return event

    def _analyze_impact(
        self,
        source_timeline: Timeline,
        branch_point_commit: TimelineCommit,
        source_event: Event | None,
        payload: TimelineBranchCreate,
    ) -> TimelineImpactAnalysis:
        agent_run = AgentRun(
            universe_id=source_timeline.universe_id,
            agent_name="Timeline Agent",
            input_summary="Analyze branch point and modified historical event.",
            status="running",
            started_at=datetime.now(UTC),
        )
        self._db.add(agent_run)
        self._db.commit()
        self._db.refresh(agent_run)

        try:
            runner = self._timeline_agent or TimelineAgentRunner()
            impact = runner.analyze(
                self._timeline_agent_input(
                    source_timeline=source_timeline,
                    branch_point_commit=branch_point_commit,
                    source_event=source_event,
                    new_outcome=payload.new_outcome,
                )
            )
        except Exception:
            impact = self._fallback_impact(source_event, payload.new_outcome)

        agent_run.status = "completed"
        agent_run.output_summary = impact.alternate_history_summary
        agent_run.completed_at = datetime.now(UTC)
        self._db.add(agent_run)
        self._db.commit()
        return impact

    def _timeline_agent_input(
        self,
        *,
        source_timeline: Timeline,
        branch_point_commit: TimelineCommit,
        source_event: Event | None,
        new_outcome: str,
    ) -> str:
        recent_events = self._history.events(source_timeline.id)[-12:]
        return (
            f"Original timeline: {source_timeline.name}\n"
            f"Branch point commit: {branch_point_commit.message}\n"
            f"Original event: {source_event.title if source_event else 'Commit-level branch'}\n"
            f"Original event summary: {source_event.summary if source_event else 'N/A'}\n"
            f"Modified outcome: {new_outcome}\n\n"
            "Visible future context:\n"
            + "\n".join(
                f"- {event.title}: {event.summary or 'No summary'}" for event in recent_events
            )
        )

    def _fallback_impact(
        self,
        source_event: Event | None,
        new_outcome: str,
    ) -> TimelineImpactAnalysis:
        participants = (
            [
                participant.character.canonical_name
                for participant in source_event.participants
                if participant.character is not None
            ]
            if source_event
            else []
        )
        return TimelineImpactAnalysis(
            alternate_history_summary=(
                "History diverges when "
                f"{source_event.title if source_event else 'the selected commit'} "
                f"changes outcome: {new_outcome}"
            ),
            impacted_characters=participants,
            impacted_relationships=[
                f"Relationships connected to {name} may change." for name in participants
            ],
            impacted_events=[
                source_event.title if source_event else "Commit-level divergence"
            ],
            memory_updates=[new_outcome],
        )

    def _copy_inherited_memory(
        self,
        *,
        source_timeline: Timeline,
        branch: Timeline,
        branch_commit: TimelineCommit,
        branch_point_commit: TimelineCommit,
    ) -> None:
        inherited_commit_ids = self._commit_ids_until(source_timeline.id, branch_point_commit.id)
        if not inherited_commit_ids:
            return

        entries = self._db.scalars(
            select(MemoryEntry).where(
                MemoryEntry.timeline_id == source_timeline.id,
                MemoryEntry.commit_id.in_(inherited_commit_ids),
            )
        ).all()
        for entry in entries:
            self._db.add(
                MemoryEntry(
                    universe_id=entry.universe_id,
                    timeline_id=branch.id,
                    commit_id=branch_commit.id,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    memory_type=entry.memory_type,
                    content=entry.content,
                    structured_value={
                        **entry.structured_value,
                        "inherited_from_timeline_id": str(source_timeline.id),
                    },
                    confidence=entry.confidence,
                    source="timeline_branch_inherited",
                    valid_from_event_id=entry.valid_from_event_id,
                    valid_to_event_id=entry.valid_to_event_id,
                )
            )

        states = self._latest_states(source_timeline.id, inherited_commit_ids)
        for state in states.values():
            self._db.add(
                CharacterStateHistory(
                    universe_id=state.universe_id,
                    character_id=state.character_id,
                    timeline_id=branch.id,
                    commit_id=branch_commit.id,
                    location_id=state.location_id,
                    current_status=state.current_status,
                    emotional_state=state.emotional_state,
                    physical_state=state.physical_state,
                    summary=state.summary,
                    source="timeline_branch_inherited",
                    confidence=state.confidence,
                )
            )

    def _copy_relationships(self, source_timeline: Timeline, branch: Timeline) -> None:
        relationships = self._db.scalars(
            select(Relationship).where(
                Relationship.timeline_id == source_timeline.id,
                Relationship.status == "active",
            )
        ).all()
        for relationship in relationships:
            self._db.add(
                Relationship(
                    universe_id=relationship.universe_id,
                    timeline_id=branch.id,
                    source_character_id=relationship.source_character_id,
                    target_character_id=relationship.target_character_id,
                    relationship_type=relationship.relationship_type,
                    strength=relationship.strength,
                    status=relationship.status,
                    valid_from_event_id=relationship.valid_from_event_id,
                    evidence=relationship.evidence,
                    confidence=relationship.confidence,
                )
            )

    def _create_modified_event(
        self,
        *,
        branch: Timeline,
        branch_commit: TimelineCommit,
        source_event: Event | None,
        payload: TimelineBranchCreate,
    ) -> Event:
        event = Event(
            universe_id=branch.universe_id,
            location_id=source_event.location_id if source_event else None,
            title=payload.modified_title
            or f"Alternate: {source_event.title if source_event else 'History changes'}",
            summary=payload.new_outcome,
            event_type="timeline_branch_modification",
            order_index=source_event.order_index if source_event else None,
            importance=source_event.importance if source_event else 9,
        )
        self._db.add(event)
        self._db.flush()
        self._db.add(
            TimelineCommitEvent(
                commit_id=branch_commit.id,
                event_id=event.id,
                change_type="modified",
            )
        )

        if source_event:
            for participant in source_event.participants:
                self._db.add(
                    EventParticipant(
                        event_id=event.id,
                        character_id=participant.character_id,
                        role=participant.role,
                    )
                )
        self._db.flush()
        return event

    def _store_branch_memory(
        self,
        *,
        branch: Timeline,
        branch_commit: TimelineCommit,
        modified_event: Event,
        impact: TimelineImpactAnalysis,
        new_outcome: str,
    ) -> None:
        self._db.add(
            MemoryEntry(
                universe_id=branch.universe_id,
                timeline_id=branch.id,
                commit_id=branch_commit.id,
                entity_type="timeline",
                entity_id=branch.id,
                memory_type="branch_divergence",
                content=impact.alternate_history_summary,
                structured_value={
                    "modified_event_id": str(modified_event.id),
                    "new_outcome": new_outcome,
                    "impacted_characters": impact.impacted_characters,
                    "impacted_events": impact.impacted_events,
                },
                confidence=0.85,
                source="timeline_agent",
                valid_from_event_id=modified_event.id,
            )
        )
        for update in impact.memory_updates:
            self._db.add(
                MemoryEntry(
                    universe_id=branch.universe_id,
                    timeline_id=branch.id,
                    commit_id=branch_commit.id,
                    entity_type="timeline",
                    entity_id=branch.id,
                    memory_type="alternate_history",
                    content=update,
                    structured_value={"modified_event_id": str(modified_event.id)},
                    confidence=0.8,
                    source="timeline_agent",
                    valid_from_event_id=modified_event.id,
                )
            )

    def _apply_character_state_impacts(
        self,
        *,
        branch: Timeline,
        branch_commit: TimelineCommit,
        modified_event: Event,
        impact: TimelineImpactAnalysis,
        new_outcome: str,
    ) -> None:
        characters = {
            self._normalize(character.canonical_name): character
            for character in self._db.scalars(
                select(Character).where(Character.universe_id == branch.universe_id)
            ).all()
        }
        impacted_names = impact.impacted_characters or [
            participant.character.canonical_name
            for participant in modified_event.participants
            if participant.character is not None
        ]
        for name in impacted_names:
            character = characters.get(self._normalize(name))
            if character is None:
                continue
            current_status = self._infer_status(character.canonical_name, new_outcome)
            self._db.add(
                CharacterStateHistory(
                    universe_id=branch.universe_id,
                    character_id=character.id,
                    timeline_id=branch.id,
                    commit_id=branch_commit.id,
                    location_id=modified_event.location_id,
                    current_status=current_status,
                    emotional_state="altered",
                    physical_state=current_status,
                    summary=(
                        f"In timeline '{branch.name}', {character.canonical_name}'s state "
                        f"changes because: {new_outcome}"
                    ),
                    source="timeline_branch",
                    confidence=0.78,
                )
            )
            self._db.add(
                MemoryEntry(
                    universe_id=branch.universe_id,
                    timeline_id=branch.id,
                    commit_id=branch_commit.id,
                    entity_type="character",
                    entity_id=character.id,
                    memory_type="branch_state_change",
                    content=(
                        f"{character.canonical_name} is now {current_status} in this branch: "
                        f"{new_outcome}"
                    ),
                    structured_value={
                        "modified_event_id": str(modified_event.id),
                        "current_status": current_status,
                    },
                    confidence=0.78,
                    source="timeline_branch",
                    valid_from_event_id=modified_event.id,
                )
            )

    def _commit_ids_until(
        self,
        timeline_id: uuid.UUID,
        stop_commit_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        commit_ids: list[uuid.UUID] = []
        for commit in self._history.commit_chain(timeline_id):
            commit_ids.append(commit.id)
            if commit.id == stop_commit_id:
                break
        return commit_ids

    def _latest_states(
        self,
        timeline_id: uuid.UUID,
        commit_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, CharacterStateHistory]:
        states = self._db.scalars(
            select(CharacterStateHistory)
            .where(
                CharacterStateHistory.timeline_id == timeline_id,
                CharacterStateHistory.commit_id.in_(commit_ids),
            )
            .order_by(CharacterStateHistory.created_at.asc())
        ).all()
        latest: dict[uuid.UUID, CharacterStateHistory] = {}
        for state in states:
            latest[state.character_id] = state
        return latest

    def _default_branch_name(self, source_event: Event | None, new_outcome: str) -> str:
        base = source_event.title if source_event else "Alternate Future"
        return f"{base}: {new_outcome[:48]}"

    def _infer_status(self, character_name: str, new_outcome: str) -> str:
        normalized = self._normalize(new_outcome)
        character_ref = self._normalize(character_name)
        death_words = {"dies", "dead", "killed", "murdered", "executed", "sacrificed"}
        survival_words = {"survives", "alive", "rescued", "saved"}
        if character_ref in normalized and any(word in normalized for word in death_words):
            return "dead"
        if character_ref in normalized and any(word in normalized for word in survival_words):
            return "alive"
        return "altered"

    def _event_read(self, event: Event, commit: TimelineCommit) -> TimelineEventRead:
        location = self._db.get(Location, event.location_id) if event.location_id else None
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
            location_name=location.name if location else None,
            participants=[
                participant.character.canonical_name
                for participant in event.participants
                if participant.character is not None
            ],
            commit_id=commit.id,
            commit_message=commit.message,
            commit_type=commit.commit_type,
            change_type="modified",
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

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").casefold().split())
