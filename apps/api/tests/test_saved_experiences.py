from __future__ import annotations

from tests.conftest import auth_header, register_traveler


def _save(client, headers: dict, experience_id: str, suffix: str = "1") -> None:
    response = client.post(
        "/api/v1/feedback/interactions",
        headers=headers,
        json={
            "experience_id": experience_id,
            "event_type": "SAVE",
            "client_event_id": f"{experience_id}-save-{suffix}",
        },
    )
    assert response.status_code == 200, response.text


def _unsave(client, headers: dict, experience_id: str, suffix: str = "1") -> None:
    response = client.post(
        "/api/v1/feedback/interactions",
        headers=headers,
        json={
            "experience_id": experience_id,
            "event_type": "UNSAVE",
            "client_event_id": f"{experience_id}-unsave-{suffix}",
        },
    )
    assert response.status_code == 200, response.text


def test_saved_list_empty_by_default(client, seeded_ids) -> None:
    body = register_traveler(client, "saved-1@example.com")
    response = client.get("/api/v1/experiences/saved", headers=auth_header(body))
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_save_then_appears_in_saved_list(client, seeded_ids) -> None:
    body = register_traveler(client, "saved-2@example.com")
    headers = auth_header(body)
    _save(client, headers, seeded_ids["experience_id"])

    response = client.get("/api/v1/experiences/saved", headers=headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert seeded_ids["experience_id"] in ids


def test_unsave_removes_from_saved_list(client, seeded_ids) -> None:
    body = register_traveler(client, "saved-3@example.com")
    headers = auth_header(body)
    _save(client, headers, seeded_ids["experience_id"])
    _unsave(client, headers, seeded_ids["experience_id"])

    response = client.get("/api/v1/experiences/saved", headers=headers)
    ids = [item["id"] for item in response.json()["items"]]
    assert seeded_ids["experience_id"] not in ids


def test_resave_after_unsave_reappears(client, seeded_ids) -> None:
    body = register_traveler(client, "saved-4@example.com")
    headers = auth_header(body)
    _save(client, headers, seeded_ids["experience_id"], suffix="a")
    _unsave(client, headers, seeded_ids["experience_id"], suffix="a")
    _save(client, headers, seeded_ids["experience_id"], suffix="b")

    response = client.get("/api/v1/experiences/saved", headers=headers)
    ids = [item["id"] for item in response.json()["items"]]
    assert seeded_ids["experience_id"] in ids


def test_saved_list_scoped_per_traveler(client, seeded_ids) -> None:
    body_a = register_traveler(client, "saved-5a@example.com")
    body_b = register_traveler(client, "saved-5b@example.com")
    _save(client, auth_header(body_a), seeded_ids["experience_id"])

    response_a = client.get("/api/v1/experiences/saved", headers=auth_header(body_a))
    response_b = client.get("/api/v1/experiences/saved", headers=auth_header(body_b))

    assert seeded_ids["experience_id"] in [item["id"] for item in response_a.json()["items"]]
    assert seeded_ids["experience_id"] not in [item["id"] for item in response_b.json()["items"]]


def test_saved_endpoint_requires_authentication(client, seeded_ids) -> None:
    response = client.get("/api/v1/experiences/saved")
    assert response.status_code == 401


def test_saved_path_not_treated_as_experience_id(client, seeded_ids) -> None:
    """GET /experiences/saved must resolve to the saved-list route, not
    fall through to GET /experiences/{experience_id} with id="saved"."""
    body = register_traveler(client, "saved-6@example.com")
    response = client.get("/api/v1/experiences/saved", headers=auth_header(body))
    assert response.status_code == 200
    assert "items" in response.json()
