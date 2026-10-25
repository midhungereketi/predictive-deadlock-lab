"""The Python scorer must reproduce every shared case that frontend/scoring.js also checks."""

import json
import math
import unittest
from pathlib import Path

from member3_analysis.threat_scorer import ThreatScorer

CASES = json.loads((Path(__file__).resolve().parents[2] / "shared" / "scoring_cases.json").read_text(encoding="utf-8"))["cases"]


class TestScoringMatchesSharedCases(unittest.TestCase):
    def test_every_shared_case(self) -> None:
        for case in CASES:
            with self.subTest(case["name"]):
                state = case["state"]
                result = ThreatScorer.from_overrides(**case["weights"]).evaluate(
                    num_blocked=len(state["waits"]),
                    wait_duration_ms=state["wait_ms"],
                    contention_count=state["contention"],
                    owners=state["owners"],
                    waits=state["waits"],
                    has_cycle=state["cycle"],
                )
                self.assertEqual(result.score, case["expected"]["score"])
                self.assertEqual(result.risk_level, case["expected"]["level"])

    def test_rounding_is_half_up_like_the_browser(self) -> None:
        # Python's round(2.5) is 2 (banker's rounding); Math.round(2.5) in the browser is 3.
        case = next(c for c in CASES if "half-way" in c["name"])
        self.assertEqual(round(2.5), 2)
        self.assertEqual(math.floor(2.5 + 0.5), case["expected"]["score"])


if __name__ == "__main__":
    unittest.main()
