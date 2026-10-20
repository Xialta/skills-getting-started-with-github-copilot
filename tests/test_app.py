from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)
client = TestClient(app_module.app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))


def activity_path(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_root_redirects_to_static_app():
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == INITIAL_ACTIVITIES


def test_signup_adds_participant():
    response = client.post(
        activity_path("Chess Club"),
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Chess Club"
    }
    assert "student@mergington.edu" in client.get("/activities").json()["Chess Club"][
        "participants"
    ]


def test_signup_rejects_duplicate_participant():
    email = INITIAL_ACTIVITIES["Chess Club"]["participants"][0]

    response = client.post(
        activity_path("Chess Club"),
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_returns_not_found_for_unknown_activity():
    response = client.post(
        activity_path("Unknown Club"),
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant():
    email = "student@mergington.edu"
    path = activity_path("Chess Club")
    client.post(path, params={"email": email})

    response = client.delete(path, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered student@mergington.edu from Chess Club"
    }
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unregistered_participant():
    response = client.delete(
        activity_path("Chess Club"),
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_returns_not_found_for_unknown_activity():
    response = client.delete(
        activity_path("Unknown Club"),
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
