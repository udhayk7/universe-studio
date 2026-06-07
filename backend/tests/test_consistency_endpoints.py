from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.agent_run import AgentRun
from app.db.models.character import Character
from app.db.models.episode import Episode
from app.db.models.job import Job
from app.db.models.timeline import Timeline
from app.db.models.universe import Universe
from app.schemas.consistency import ConsistencyIssue


def test_consistency_severity_normalizes_legacy_critical_to_blocker() -> None:
    issue = ConsistencyIssue(
        severity="critical",
        issue_type="timeline",
        issue="Timeline fact leaks between branches.",
        explanation="A Timeline A event is presented as true in Timeline B.",
    )

    assert issue.severity == "blocker"


def test_consistency_check_persists_character_issue(
    db_client: TestClient,
    db_session: Session,
) -> None:
    universe, timeline = _seed_universe_with_dead_character(db_session)

    response = db_client.post(
        "/api/v1/consistency/check",
        json={
            "universe_id": str(universe.id),
            "timeline_id": str(timeline.id),
            "content": "Mira Vale walks into the exchange alive and bargaining for memories.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["verdict"] == "fail"
    assert body["checks"]
    check = body["checks"][0]
    assert UUID(check["id"])
    assert check["severity"] == "high"
    assert check["issue_type"] == "character"
    assert "Mira Vale" in check["description"]

    dashboard_response = db_client.get(f"/api/v1/universes/{universe.id}/consistency")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["open_issues"] == 1
    assert dashboard["character_conflicts"] == 1
    assert dashboard["severity_breakdown"]["high"] == 1

    get_response = db_client.get(f"/api/v1/consistency/{check['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == check["id"]


def test_episode_and_job_trace_endpoints(
    db_client: TestClient,
    db_session: Session,
) -> None:
    universe, timeline = _seed_universe_with_dead_character(db_session)
    episode = Episode(
        universe_id=universe.id,
        timeline_id=timeline.id,
        title="The Continuity Trial",
        summary="The system proves its memory chain.",
        status="generated",
    )
    job = Job(
        universe_id=universe.id,
        job_type="episode_generation",
        status="completed",
        progress=100,
        message="Episode generated",
    )
    db_session.add_all([episode, job])
    db_session.flush()

    started_at = datetime.now(UTC)
    db_session.add(
        AgentRun(
            universe_id=universe.id,
            job_id=job.id,
            episode_id=episode.id,
            agent_name="Consistency Agent",
            input_summary="Generated scenes and memory context.",
            output_summary="Verdict pass; found 0 issues.",
            status="completed",
            started_at=started_at,
            completed_at=started_at,
            duration_ms=12,
        )
    )
    db_session.commit()

    episode_trace = db_client.get(f"/api/v1/episodes/{episode.id}/trace")
    assert episode_trace.status_code == 200
    episode_trace_body = episode_trace.json()
    assert episode_trace_body["episode_id"] == str(episode.id)
    assert episode_trace_body["steps"][0]["agent_name"] == "Consistency Agent"
    assert episode_trace_body["steps"][0]["duration_ms"] == 12

    job_trace = db_client.get(f"/api/v1/jobs/{job.id}/trace")
    assert job_trace.status_code == 200
    job_trace_body = job_trace.json()
    assert job_trace_body["job_id"] == str(job.id)
    assert job_trace_body["steps"][0]["episode_id"] == str(episode.id)


def _seed_universe_with_dead_character(db_session: Session) -> tuple[Universe, Timeline]:
    universe = Universe(
        title="Memory Market",
        premise="A city where memories are currency.",
        genre="science fiction",
        tone="noir",
        status="active",
    )
    db_session.add(universe)
    db_session.flush()

    timeline = Timeline(
        universe_id=universe.id,
        name="Canon Timeline",
        is_canon=True,
    )
    db_session.add(timeline)
    db_session.flush()
    universe.active_timeline_id = timeline.id

    db_session.add(
        Character(
            universe_id=universe.id,
            canonical_name="Mira Vale",
            aliases=["Mira"],
            description="A broker who paid the final price.",
            traits={"personality": ["guarded"]},
            goals={"items": ["protect the memory vault"]},
            fears={"items": ["being forgotten"]},
            status="dead",
        )
    )
    db_session.commit()
    return universe, timeline
