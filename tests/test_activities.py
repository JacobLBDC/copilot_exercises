from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


CLIENT = TestClient(app_module.app)

# take a deep copy of the initial in-memory activities to restore between tests
INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # restore activities before each test to keep tests isolated
    app_module.activities.clear()
    app_module.activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    # ensure cleaned after test (optional)
    app_module.activities.clear()
    app_module.activities.update(deepcopy(INITIAL_ACTIVITIES))


def test_get_activities():
    resp = CLIENT.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # expected activity keys exist and participants is a list
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "test.user@example.com"

    # sign up
    resp = CLIENT.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email}" in resp.json().get("message", "")

    # ensure participant appears in the activity
    resp = CLIENT.get("/activities")
    assert resp.status_code == 200
    participants = resp.json()[activity]["participants"]
    assert email in participants

    # unregister
    resp = CLIENT.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 200
    assert f"Unregistered {email}" in resp.json().get("message", "")

    # ensure participant removed
    resp = CLIENT.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email not in participants


def test_signup_duplicate_returns_400():
    # use an existing participant from initial data
    activity = "Chess Club"
    existing = INITIAL_ACTIVITIES[activity]["participants"][0]

    resp = CLIENT.post(f"/activities/{activity}/signup?email={existing}")
    assert resp.status_code == 400
    assert "already signed up" in resp.json().get("detail", "")
