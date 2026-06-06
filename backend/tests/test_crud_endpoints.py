from fastapi.testclient import TestClient

from tests.fixtures.sample_data import SAMPLE_CHARACTER, SAMPLE_TIMELINE, SAMPLE_UNIVERSE


def test_postgres_health_with_test_database(db_client: TestClient) -> None:
    response = db_client.get("/api/v1/health/postgres")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "postgres"}


def test_universe_character_and_timeline_crud(db_client: TestClient) -> None:
    universe_response = db_client.post("/api/v1/universes", json=SAMPLE_UNIVERSE)
    assert universe_response.status_code == 201
    universe = universe_response.json()
    assert universe["title"] == SAMPLE_UNIVERSE["title"]

    character_response = db_client.post(
        f"/api/v1/universes/{universe['id']}/characters",
        json=SAMPLE_CHARACTER,
    )
    assert character_response.status_code == 201
    character = character_response.json()
    assert character["canonical_name"] == SAMPLE_CHARACTER["canonical_name"]
    assert character["universe_id"] == universe["id"]

    state_response = db_client.get(f"/api/v1/characters/{character['id']}/state")
    assert state_response.status_code == 200
    assert state_response.json()["latest"]["current_status"] == character["status"]

    context_response = db_client.get(f"/api/v1/characters/{character['id']}/context-pack")
    assert context_response.status_code == 200
    context_pack = context_response.json()
    assert context_pack["character"]["id"] == character["id"]
    assert context_pack["current_status"] == character["status"]

    timeline_response = db_client.post(
        f"/api/v1/universes/{universe['id']}/timelines",
        json=SAMPLE_TIMELINE,
    )
    assert timeline_response.status_code == 201
    timeline = timeline_response.json()
    assert timeline["name"] == SAMPLE_TIMELINE["name"]
    assert timeline["universe_id"] == universe["id"]

    universes_response = db_client.get("/api/v1/universes")
    assert universes_response.status_code == 200
    assert len(universes_response.json()) == 1

    characters_response = db_client.get(f"/api/v1/universes/{universe['id']}/characters")
    assert characters_response.status_code == 200
    assert len(characters_response.json()) == 1

    timelines_response = db_client.get(f"/api/v1/universes/{universe['id']}/timelines")
    assert timelines_response.status_code == 200
    assert len(timelines_response.json()) == 1
