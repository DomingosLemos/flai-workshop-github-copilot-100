"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to original state before each test."""
    original_participants = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, data in activities.items():
        data["participants"] = original_participants[name]


@pytest.fixture
def client():
    return TestClient(app)


# --- GET /activities ---

def test_get_activities_returns_200(client):
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict(client):
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)


def test_get_activities_contains_expected_activities(client):
    response = client.get("/activities")
    data = response.json()
    for name in ["Basketball Team", "Soccer Club", "Drama Club", "Chess Club", "Programming Class"]:
        assert name in data


def test_get_activities_activity_has_required_fields(client):
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# --- POST /activities/{activity_name}/signup ---

def test_signup_returns_200(client):
    response = client.post("/activities/Basketball Team/signup?email=new@mergington.edu")
    assert response.status_code == 200


def test_signup_adds_student_to_participants(client):
    client.post("/activities/Basketball Team/signup?email=new@mergington.edu")
    response = client.get("/activities")
    participants = response.json()["Basketball Team"]["participants"]
    assert "new@mergington.edu" in participants


def test_signup_returns_confirmation_message(client):
    response = client.post("/activities/Basketball Team/signup?email=new@mergington.edu")
    data = response.json()
    assert "message" in data
    assert "new@mergington.edu" in data["message"]
    assert "Basketball Team" in data["message"]


def test_signup_nonexistent_activity_returns_404(client):
    response = client.post("/activities/NonExistentActivity/signup?email=test@mergington.edu")
    assert response.status_code == 404


def test_signup_nonexistent_activity_error_detail(client):
    response = client.post("/activities/NonExistentActivity/signup?email=test@mergington.edu")
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client):
    # Chess Club already has michael@mergington.edu
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400


def test_signup_duplicate_error_detail(client):
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.json()["detail"] == "Student is already signed up"


# --- DELETE /activities/{activity_name}/unregister ---

def test_unregister_returns_200(client):
    # michael@mergington.edu is in Chess Club
    response = client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
    assert response.status_code == 200


def test_unregister_removes_student_from_participants(client):
    client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert "michael@mergington.edu" not in participants


def test_unregister_returns_confirmation_message(client):
    response = client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]


def test_unregister_nonexistent_activity_returns_404(client):
    response = client.delete("/activities/NonExistentActivity/unregister?email=test@mergington.edu")
    assert response.status_code == 404


def test_unregister_nonexistent_activity_error_detail(client):
    response = client.delete("/activities/NonExistentActivity/unregister?email=test@mergington.edu")
    assert response.json()["detail"] == "Activity not found"


def test_unregister_student_not_signed_up_returns_400(client):
    response = client.delete("/activities/Basketball Team/unregister?email=nothere@mergington.edu")
    assert response.status_code == 400


def test_unregister_student_not_signed_up_error_detail(client):
    response = client.delete("/activities/Basketball Team/unregister?email=nothere@mergington.edu")
    assert response.json()["detail"] == "Student is not signed up for this activity"


# --- GET / (redirect) ---

def test_root_redirects_to_static(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers["location"]
