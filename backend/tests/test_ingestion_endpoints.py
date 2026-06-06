from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from app.api.v1.endpoints import ingestion


def test_create_from_input_enqueues_extraction_job(
    db_client: TestClient,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_extraction_job(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(ingestion, "run_extraction_job", fake_run_extraction_job)

    response = db_client.post(
        "/api/v1/universes/create-from-input",
        data={
            "source_type": "idea",
            "content": "A city where memories are currency.",
            "title_hint": "Memory City",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["progress"] == 0
    assert body["message"] == "Universe extraction queued"
    assert UUID(body["id"])
    assert captured["payload_data"]["content"] == "A city where memories are currency."

    job_response = db_client.get(f"/api/v1/jobs/{body['id']}")
    assert job_response.status_code == 200
    assert job_response.json()["id"] == body["id"]
