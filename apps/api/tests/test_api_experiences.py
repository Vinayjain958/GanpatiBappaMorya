from __future__ import annotations

from tests.conftest import auth_header, register_traveler


def test_list_experiences_returns_seeded_row(client, seeded_ids) -> None:
    response = client.get("/api/v1/experiences")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == seeded_ids["experience_id"]
    assert body["items"][0]["category"]["slug"] == "food-drink"


def test_list_experiences_category_filter_matches(client) -> None:
    response = client.get("/api/v1/experiences", params={"category": "food-drink"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_experiences_category_filter_excludes_non_matching(client) -> None:
    response = client.get("/api/v1/experiences", params={"category": "wellness"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_list_experiences_pagination_params_respected(client) -> None:
    response = client.get("/api/v1/experiences", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert len(body["items"]) <= 1


def test_get_experience_by_id_returns_full_detail(client, seeded_ids) -> None:
    response = client.get(f"/api/v1/experiences/{seeded_ids['experience_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Test Experience"
    assert body["full_description"]
    assert body["is_price_estimated"] is True
    assert "opening_hours" in body


def test_get_experience_missing_id_returns_404(client) -> None:
    response = client.get("/api/v1/experiences/does-not-exist")
    assert response.status_code == 404


def test_experience_response_never_exposes_password_hash(client, seeded_ids) -> None:
    response = client.get(f"/api/v1/experiences/{seeded_ids['experience_id']}")
    assert "password_hash" not in response.text


def test_create_review_requires_auth(client, seeded_ids) -> None:
    response = client.post(
        f"/api/v1/experiences/{seeded_ids['experience_id']}/reviews",
        json={"rating_value": 5, "title": "Great!", "body": "Loved it."},
    )
    assert response.status_code == 401


def test_create_review_persists_and_updates_rating(client, seeded_ids) -> None:
    user = register_traveler(client, "reviewer1@example.com")
    response = client.post(
        f"/api/v1/experiences/{seeded_ids['experience_id']}/reviews",
        json={"rating_value": 4, "title": "Pretty good", "body": "Enjoyed the visit overall."},
        headers=auth_header(user),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["review"]["rating_value"] == 4
    assert body["review"]["is_synthetic"] is False
    assert body["review"]["author_display_name"]
    assert body["rating_summary"]["review_count"] >= 1

    detail = client.get(f"/api/v1/experiences/{seeded_ids['experience_id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["rating"] == body["rating_summary"]["average_rating"]
    assert detail_body["review_count"] == body["rating_summary"]["review_count"]


def test_create_review_rejects_invalid_rating_value(client, seeded_ids) -> None:
    user = register_traveler(client, "reviewer2@example.com")
    response = client.post(
        f"/api/v1/experiences/{seeded_ids['experience_id']}/reviews",
        json={"rating_value": 6, "title": "Too high", "body": "Not a valid rating."},
        headers=auth_header(user),
    )
    assert response.status_code == 422


def test_create_review_missing_experience_returns_404(client) -> None:
    user = register_traveler(client, "reviewer3@example.com")
    response = client.post(
        "/api/v1/experiences/does-not-exist/reviews",
        json={"rating_value": 5, "title": "N/A", "body": "N/A"},
        headers=auth_header(user),
    )
    assert response.status_code == 404


def test_create_multiple_reviews_from_same_experience_does_not_collide(client, seeded_ids) -> None:
    user = register_traveler(client, "reviewer4@example.com")
    for i in range(2):
        response = client.post(
            f"/api/v1/experiences/{seeded_ids['experience_id']}/reviews",
            json={"rating_value": 3, "title": f"Review {i}", "body": "Body text here."},
            headers=auth_header(user),
        )
        assert response.status_code == 201, response.text
