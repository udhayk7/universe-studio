from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.api.v1.endpoints import episodes
from tests.fixtures.sample_data import SAMPLE_UNIVERSE


def test_generate_episode_enqueues_job(
    db_client: TestClient,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_episode_generation_job(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        episodes,
        "run_episode_generation_job",
        fake_run_episode_generation_job,
    )

    universe_response = db_client.post("/api/v1/universes", json=SAMPLE_UNIVERSE)
    assert universe_response.status_code == 201
    universe = universe_response.json()

    response = db_client.post(
        f"/api/v1/universes/{universe['id']}/episodes/generate",
        json={"prompt": "Focus on the archivist's first impossible choice."},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["progress"] == 0
    assert body["message"] == "Episode generation queued"
    assert body["job_type"] == "episode_generation"
    assert body["universe_id"] == universe["id"]
    assert body["result_data"] == {}
    assert UUID(body["id"])
    assert str(captured["universe_id"]) == universe["id"]
    assert (
        captured["payload_data"]["prompt"]
        == "Focus on the archivist's first impossible choice."
    )
