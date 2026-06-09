"""
Tests for the Mergington High School Activities API.
Uses the AAA (Arrange-Act-Assert) pattern to structure each test.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participant lists to their original state before each test."""
    original_participants = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, data in activities.items():
        data["participants"] = original_participants[name]


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        # Arrange - client is ready via fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200

    def test_returns_dict(self, client):
        # Arrange - client is ready via fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert isinstance(response.json(), dict)

    def test_contains_expected_activities(self, client):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        data = client.get("/activities").json()

        # Assert
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        data = client.get("/activities").json()

        # Assert
        for activity in data.values():
            for field in required_fields:
                assert field in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_participant_appears_in_activity_after_signup(self, client):
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        participants = client.get("/activities").json()[activity]["participants"]

        # Assert
        assert email in participants

    def test_signup_to_unknown_activity_returns_404(self, client):
        # Arrange
        email = "test@mergington.edu"
        activity = "Unknown Activity"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404

    def test_duplicate_signup_returns_400(self, client):
        # Arrange
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        client.post(f"/activities/{activity}/signup?email={email}")

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400

    def test_signup_decreases_spots_left(self, client):
        # Arrange
        activity = "Chess Club"
        before = client.get("/activities").json()[activity]
        spots_before = before["max_participants"] - len(before["participants"])

        # Act
        client.post(f"/activities/{activity}/signup?email=newstudent@mergington.edu")

        # Assert
        after = client.get("/activities").json()[activity]
        spots_after = after["max_participants"] - len(after["participants"])
        assert spots_after == spots_before - 1


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_participant_removed_after_unregister(self, client):
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        client.delete(f"/activities/{activity}/unregister?email={email}")
        participants = client.get("/activities").json()[activity]["participants"]

        # Assert
        assert email not in participants

    def test_unregister_from_unknown_activity_returns_404(self, client):
        # Arrange
        email = "michael@mergington.edu"
        activity = "Unknown Activity"

        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")

        # Assert
        assert response.status_code == 404

    def test_unregister_non_participant_returns_400(self, client):
        # Arrange
        email = "nobody@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")

        # Assert
        assert response.status_code == 400

    def test_unregister_increases_spots_left(self, client):
        # Arrange
        activity = "Chess Club"
        before = client.get("/activities").json()[activity]
        spots_before = before["max_participants"] - len(before["participants"])

        # Act
        client.delete(f"/activities/{activity}/unregister?email=michael@mergington.edu")

        # Assert
        after = client.get("/activities").json()[activity]
        spots_after = after["max_participants"] - len(after["participants"])
        assert spots_after == spots_before + 1


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects_to_index(self, client):
        # Arrange - client is ready via fixture

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/static/index.html"
