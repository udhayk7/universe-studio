from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.endpoints import timelines
from app.db.models.character import Character
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.db.models.universe import Universe


def test_timeline_branch_creation(db_client: TestClient, db_session: Session) -> None:
    universe = Universe(title="Memory City", premise="Memories are currency.", status="ready")
    db_session.add(universe)
    db_session.flush()

    timeline = Timeline(universe_id=universe.id, name="Timeline A", is_canon=True)
    db_session.add(timeline)
    db_session.flush()

    commit = TimelineCommit(
        timeline_id=timeline.id,
        message="Maya survives the exchange",
        commit_type="ingest",
        created_by="test",
    )
    db_session.add(commit)
    db_session.flush()

    character = Character(
        universe_id=universe.id,
        canonical_name="Maya",
        aliases=[],
        description="A memory broker.",
        traits={},
        goals={},
        fears={},
        status="alive",
    )
    event = Event(
        universe_id=universe.id,
        title="The Exchange",
        summary="Maya survives.",
        event_type="test_event",
        order_index=1,
        importance=8,
    )
    db_session.add_all([character, event])
    db_session.flush()
    db_session.add(
        TimelineCommitEvent(
            commit_id=commit.id,
            event_id=event.id,
            change_type="created",
        )
    )
    db_session.add(EventParticipant(event_id=event.id, character_id=character.id, role="primary"))
    timeline.head_commit_id = commit.id
    universe.active_timeline_id = timeline.id
    db_session.add_all([timeline, universe])
    db_session.commit()

    response = db_client.post(
        f"/api/v1/timelines/{timeline.id}/branch",
        json={
            "event_id": str(event.id),
            "name": "Timeline B",
            "new_outcome": "Maya dies instead.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["timeline"]["name"] == "Timeline B"
    assert body["timeline"]["parent_timeline_id"] == str(timeline.id)
    assert body["modified_event"]["summary"] == "Maya dies instead."
    assert "Maya" in body["impact"]["impacted_characters"]

    events_response = db_client.get(f"/api/v1/timelines/{body['timeline']['id']}/events")
    assert events_response.status_code == 200
    assert any(event["summary"] == "Maya dies instead." for event in events_response.json())


def test_generate_future_enqueues_timeline_job(
    db_client: TestClient,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_episode_generation_job(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(timelines, "run_episode_generation_job", fake_run_episode_generation_job)

    universe_response = db_client.post(
        "/api/v1/universes",
        json={"title": "Memory City", "premise": "Memories are currency."},
    )
    assert universe_response.status_code == 201
    universe = universe_response.json()
    timeline_response = db_client.post(
        f"/api/v1/universes/{universe['id']}/timelines",
        json={"name": "Timeline B", "is_canon": False},
    )
    assert timeline_response.status_code == 201
    timeline = timeline_response.json()

    response = db_client.post(
        f"/api/v1/timelines/{timeline['id']}/generate-future",
        json={"prompt": "Show the first consequence of the branch."},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["job_type"] == "alternate_future_generation"
    assert body["universe_id"] == universe["id"]
    assert str(captured["timeline_id"]) == timeline["id"]
    assert captured["payload_data"]["prompt"] == "Show the first consequence of the branch."
