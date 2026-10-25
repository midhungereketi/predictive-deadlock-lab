"""One visitor's scoring weights must never change another visitor's results.

Weights are request-scoped: each request builds its own scorer, and nothing a
request sends is stored on the server.
"""

import unittest
from concurrent.futures import ThreadPoolExecutor

from starlette.testclient import TestClient

from member2_backend.api import app
from member3_analysis.threat_scorer import ThreatScorer

CUSTOM = {"w_blocked": 0.10, "w_wait": 0.60, "w_contention": 0.20, "w_resource": 0.10, "threshold_high": 50}
# One thread holds both locks while the other waits: no floor rule applies, so
# the weights alone decide the score.
EVENTS = [
    {"time": 0.0, "thread": "system", "action": "start", "resource": None, "owner": None, "wait_ms": 0},
    {"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0},
    {"time": 0.06, "thread": "T1", "action": "acquired", "resource": "B", "owner": "T1", "wait_ms": 0},
    {"time": 0.10, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 300},
    {"time": 0.40, "thread": "T1", "action": "released", "resource": "B", "owner": None, "wait_ms": 0},
]


def cycle_in(owners, waits):
    return any(owners.get(lock) and waits.get(owners[lock]) and owners.get(waits[owners[lock]]) == thread
               for thread, lock in waits.items())


def rescored(trial, scorer):
    return [scorer.evaluate(num_blocked=len(e["waits"]), wait_duration_ms=e["wait_duration_ms"],
                            contention_count=e["contention_count"], owners=e["owners"], waits=e["waits"],
                            has_cycle=cycle_in(e["owners"], e["waits"])).score
            for e in trial["events"][1:]]


class TestScoringIsolation(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def evaluate(self, scoring=None):
        body = {"events": EVENTS}
        if scoring:
            body["scoring"] = scoring
        response = self.client.post("/api/analysis/evaluate", json=body)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_custom_weights_do_not_leak_into_later_default_requests(self) -> None:
        baseline = self.evaluate()
        custom = self.evaluate(CUSTOM)
        after = self.evaluate()
        self.assertNotEqual(custom["peak_score"], baseline["peak_score"])
        self.assertEqual(after, baseline)

    def test_put_config_changes_nobody_elses_results(self) -> None:
        baseline = self.evaluate()
        self.assertEqual(self.client.put("/api/analysis/config", json=CUSTOM).status_code, 200)
        self.assertEqual(self.evaluate(), baseline)

    def test_concurrent_visitors_keep_their_own_weights(self) -> None:
        baseline, custom = self.evaluate(), self.evaluate(CUSTOM)
        def visit(index):
            client = TestClient(app)
            scoring = CUSTOM if index % 2 else None
            body = {"events": EVENTS, **({"scoring": scoring} if scoring else {})}
            return index, client.post("/api/analysis/evaluate", json=body).json()
        with ThreadPoolExecutor(max_workers=8) as pool:
            for index, result in pool.map(visit, range(24)):
                self.assertEqual(result, custom if index % 2 else baseline)

    def test_trial_scores_use_only_that_requests_weights(self) -> None:
        response = self.client.post("/api/trials/vulnerable?timeout=3.0", params=CUSTOM)
        self.assertEqual(response.status_code, 200)
        custom_trial = response.json()
        self.assertEqual([e["risk_score"] for e in custom_trial["events"][1:]],
                         rescored(custom_trial, ThreatScorer.from_overrides(**CUSTOM)))
        response = self.client.post("/api/trials/vulnerable?timeout=3.0")
        self.assertEqual(response.status_code, 200)
        default_trial = response.json()
        self.assertEqual([e["risk_score"] for e in default_trial["events"][1:]],
                         rescored(default_trial, ThreatScorer()))

    def test_invalid_request_weights_are_rejected(self) -> None:
        response = self.client.post("/api/trials/vulnerable", params={"w_blocked": 0.9})
        self.assertEqual(response.status_code, 422)
        response = self.client.post("/api/analysis/evaluate", json={"events": EVENTS, "scoring": {"w_blocked": 0.9}})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
