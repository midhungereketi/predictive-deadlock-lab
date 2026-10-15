"""Integration tests for Member 3 API endpoints.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
"""

import unittest
from starlette.testclient import TestClient
from member2_backend.api import app


class TestMember3ApiEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_get_scoring_config(self) -> None:
        resp = self.client.get("/api/analysis/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("weights", data)
        self.assertIn("parameters", data)
        self.assertIn("thresholds", data)
        self.assertIn("formula_documentation", data)

    def test_update_scoring_config(self) -> None:
        update_payload = {"w_blocked": 0.40, "threshold_high": 75}
        resp = self.client.put("/api/analysis/config", json=update_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "updated")
        self.assertEqual(data["config"]["weights"]["blocked"], 0.40)
        self.assertEqual(data["config"]["thresholds"]["high"], 75)

    def test_evaluate_event_stream(self) -> None:
        sample_events = [
            {"time": 0.0, "thread": "system", "action": "start", "resource": None, "owner": None, "wait_ms": 0},
            {"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0},
            {"time": 0.06, "thread": "T2", "action": "acquired", "resource": "B", "owner": "T2", "wait_ms": 0},
            {"time": 0.10, "thread": "T1", "action": "waiting", "resource": "B", "owner": "T2", "wait_ms": 100},
            {"time": 0.12, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 100},
        ]
        resp = self.client.post("/api/analysis/evaluate", json={"events": sample_events})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["has_cycle"])
        self.assertGreaterEqual(data["peak_score"], 70)
        self.assertIn("heatmap", data)
        self.assertIn("trend", data)

    def test_run_batch_comparison_endpoint(self) -> None:
        resp = self.client.post("/api/analysis/compare?trials_per_mode=1&timeout=2.0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["trials_per_mode"], 1)
        self.assertIn("vulnerable", data)
        self.assertIn("protected", data)
        self.assertIn("comparative_summary", data)


if __name__ == "__main__":
    unittest.main()
