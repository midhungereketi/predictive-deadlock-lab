"""Tests for FastAPI backend REST endpoints and integration.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import pytest
from fastapi.testclient import TestClient
from member2_backend.api import app

client = TestClient(app)


def test_api_health_endpoint():
    """Verify health check returns service information."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "P. Satya Mani Shraavanth" in data["author"]


def test_api_vulnerable_experiment_endpoint():
    """Verify POST /api/experiments/vulnerable executes and detects deadlock."""
    response = client.post("/api/experiments/vulnerable?timeout=3.0")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "vulnerable"
    assert data["status"] == "deadlock"
    assert data["deadlock_detected"] is True
    assert data["metrics"]["deadlock_cycle"] == ["T1", "T2", "T1"]
    assert len(data["events"]) > 0


def test_api_protected_experiment_endpoint():
    """Verify POST /api/experiments/protected executes and completes safely."""
    response = client.post("/api/experiments/protected?timeout=3.0")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "protected"
    assert data["status"] == "completed"
    assert data["deadlock_detected"] is False
    assert data["metrics"]["deadlock_cycle"] is None
    assert data["metrics"]["threads_completed"] == 2


def test_api_run_custom_endpoint():
    """Verify POST /api/experiments/run handles parameterized runs."""
    payload = {"mode": "protected", "timeout_seconds": 2.5, "trial_id": "api-custom-01"}
    response = client.post("/api/experiments/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["trial_id"] == "api-custom-01"
    assert data["status"] == "completed"


def test_api_multi_thread_experiment_endpoint():
    vulnerable = client.post(
        "/api/experiments/multi-thread",
        json={"mode": "vulnerable", "thread_count": 5, "timeout_seconds": 3.0},
    )
    assert vulnerable.status_code == 200
    vulnerable_data = vulnerable.json()
    assert vulnerable_data["status"] == "deadlock"
    assert vulnerable_data["metrics"]["threads_started"] == 5
    assert vulnerable_data["metrics"]["deadlock_cycle"] == ["T1", "T2", "T1"]

    protected = client.post(
        "/api/experiments/multi-thread",
        json={"mode": "protected", "thread_count": 5, "timeout_seconds": 3.0},
    )
    assert protected.status_code == 200
    protected_data = protected.json()
    assert protected_data["status"] == "completed"
    assert protected_data["metrics"]["threads_completed"] == 5


def test_api_multi_thread_count_validation():
    response = client.post(
        "/api/experiments/multi-thread",
        json={"mode": "protected", "thread_count": 13},
    )
    assert response.status_code == 422


def test_api_trial_v1_endpoints():
    """Verify trial-v1 endpoints return schema-compliant JSON for frontend."""
    # Test POST /api/trials/vulnerable
    v_resp = client.post("/api/trials/vulnerable?timeout=2.5")
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["schema_version"] == 1
    assert v_data["mode"] == "vulnerable"
    assert v_data["status"] == "deadlock"

    # Test GET /api/trials/protected
    p_resp = client.get("/api/trials/protected?timeout=2.5")
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert p_data["schema_version"] == 1
    assert p_data["mode"] == "protected"
    assert p_data["status"] == "completed"
    actions = [event["action"] for event in p_data["events"]]
    assert "warning" in actions
    assert actions.index("warning") < actions.index("policy_applied") < actions.index("complete")
    assert all(not (event["waits"].get("T1") == "B" and event["waits"].get("T2") == "A")
               for event in p_data["events"])


def test_api_invalid_mode_handling():
    """Verify that invalid mode requests return appropriate HTTP 400 error."""
    resp = client.post("/api/trials/unknown_mode")
    assert resp.status_code == 400
