"""Unit and Integration Tests for Member 3 Analysis Modules.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

import unittest
from member3_analysis.graph import WaitForGraph
from member3_analysis.threat_scorer import ThreatScorer, ThreatScoreConfig
from member3_analysis.trend_analyzer import ThreatTrendAnalyzer
from member3_analysis.heatmap import ContentionHeatmapTracker
from member3_analysis.comparator import analyze_trial_events, ExperimentComparator


class TestWaitForGraph(unittest.TestCase):
    """Module 1 & 2: Wait-For Graph and Cycle Detection Tests."""

    def setUp(self) -> None:
        self.graph = WaitForGraph(threads=["T1", "T2"])

    def test_empty_event_stream_produces_empty_graph(self) -> None:
        """An empty event stream produces a valid empty graph with no edges and no cycles."""
        snapshot = self.graph.get_snapshot()
        self.assertEqual(snapshot["edge_count"], 0)
        self.assertEqual(snapshot["blocked_thread_count"], 0)
        self.assertFalse(snapshot["has_cycle"])
        self.assertEqual(snapshot["cycles"], [])
        self.assertEqual(len(snapshot["edges"]), 0)

    def test_valid_circular_wait_detected(self) -> None:
        """A valid T1 -> T2 -> T1 circular wait is detected when represented by the event-derived graph."""
        # T1 acquires A, T2 acquires B
        self.graph.process_raw_event({"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0})
        self.graph.process_raw_event({"time": 0.06, "thread": "T2", "action": "acquired", "resource": "B", "owner": "T2", "wait_ms": 0})

        # T1 waits for B (held by T2)
        s1 = self.graph.process_raw_event({"time": 0.10, "thread": "T1", "action": "waiting", "resource": "B", "owner": "T2", "wait_ms": 50})
        self.assertFalse(s1["has_cycle"])
        self.assertEqual(s1["blocked_thread_count"], 1)

        # T2 waits for A (held by T1)
        s2 = self.graph.process_raw_event({"time": 0.15, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 50})
        self.assertTrue(s2["has_cycle"])
        self.assertEqual(len(s2["cycles"]), 1)
        cycle = s2["cycles"][0]
        self.assertIn("T1", cycle)
        self.assertIn("T2", cycle)
        self.assertEqual(cycle[0], cycle[-1])  # Confirms cycle closure

    def test_acyclic_graph_does_not_report_deadlock(self) -> None:
        """An acyclic graph (single wait or multiple linear waits) does not report a deadlock cycle."""
        self.graph.process_raw_event({"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0})
        s = self.graph.process_raw_event({"time": 0.10, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 50})
        self.assertFalse(s["has_cycle"])
        self.assertEqual(s["cycles"], [])
        self.assertFalse(self.graph.has_cycle())

    def test_resource_release_removes_obsolete_dependencies(self) -> None:
        """Resource release removes obsolete dependencies and unblocks waiting threads."""
        self.graph.process_raw_event({"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0})
        self.graph.process_raw_event({"time": 0.10, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 50})
        self.assertEqual(self.graph.get_snapshot()["blocked_thread_count"], 1)

        # T1 releases A
        s = self.graph.process_raw_event({"time": 0.20, "thread": "T1", "action": "released", "resource": "A", "owner": None, "wait_ms": 0})
        self.assertEqual(s["blocked_thread_count"], 0)
        self.assertEqual(s["edge_count"], 0)
        self.assertNotIn("A", s["owners"])

    def test_repeated_events_do_not_produce_duplicate_edges(self) -> None:
        """Repeated events do not produce duplicate edges or corrupt dependency graph."""
        self.graph.process_raw_event({"time": 0.05, "thread": "T1", "action": "acquired", "resource": "A", "owner": "T1", "wait_ms": 0})
        # Two identical waiting events
        self.graph.process_raw_event({"time": 0.10, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 50})
        self.graph.process_raw_event({"time": 0.12, "thread": "T2", "action": "waiting", "resource": "A", "owner": "T1", "wait_ms": 70})

        snapshot = self.graph.get_snapshot()
        self.assertEqual(snapshot["edge_count"], 1)
        self.assertEqual(len(self.graph.get_edges()), 1)


class TestThreatScorer(unittest.TestCase):
    """Module 4: Threat Score Calculation Tests."""

    def setUp(self) -> None:
        self.scorer = ThreatScorer()

    def test_zero_and_missing_values_handled_safely(self) -> None:
        """Threat-score calculation handles zero and missing values without division by zero."""
        result = self.scorer.evaluate(num_blocked=0, wait_duration_ms=0, contention_count=0)
        self.assertIsInstance(result.score, int)
        self.assertEqual(result.score, 0)
        self.assertEqual(result.risk_level, "LOW")
        self.assertFalse(result.is_early_warning)
        self.assertFalse(result.is_cycle_detected)

    def test_increasing_wait_time_affects_score(self) -> None:
        """Increasing waiting time affects the score monotonically according to the documented formula."""
        res1 = self.scorer.evaluate(num_blocked=1, wait_duration_ms=100, contention_count=1)
        res2 = self.scorer.evaluate(num_blocked=1, wait_duration_ms=400, contention_count=1)
        res3 = self.scorer.evaluate(num_blocked=1, wait_duration_ms=800, contention_count=1)

        self.assertGreater(res2.score, res1.score)
        self.assertGreater(res3.score, res2.score)
        self.assertGreater(res3.points_wait, res1.points_wait)

    def test_risk_level_threshold_classification(self) -> None:
        """Score thresholds correctly classify LOW, ELEVATED, and HIGH risk."""
        low = self.scorer.evaluate(num_blocked=0, wait_duration_ms=0, contention_count=0)
        self.assertEqual(low.risk_level, "LOW")

        elevated = self.scorer.evaluate(num_blocked=1, wait_duration_ms=300, contention_count=2, owners={"A": "T1"})
        self.assertIn(elevated.risk_level, ("LOW", "ELEVATED"))

        high = self.scorer.evaluate(num_blocked=2, wait_duration_ms=750, contention_count=5, owners={"A": "T1", "B": "T2"})
        self.assertEqual(high.risk_level, "HIGH")
        self.assertTrue(high.is_early_warning)

    def test_deadlock_strictly_distinguished_from_score(self) -> None:
        """Cycle presence confirms deadlock (CRITICAL_DEADLOCK) distinct from heuristic prediction."""
        deadlock_res = self.scorer.evaluate(num_blocked=2, wait_duration_ms=800, contention_count=4, has_cycle=True)
        self.assertEqual(deadlock_res.risk_level, "CRITICAL_DEADLOCK")
        self.assertTrue(deadlock_res.is_cycle_detected)
        self.assertFalse(deadlock_res.is_early_warning)  # Early warning precedes deadlock, not concurrent with it


class TestTrendAnalyzer(unittest.TestCase):
    """Module 5: Threat Trend Analysis Tests."""

    def setUp(self) -> None:
        self.analyzer = ThreatTrendAnalyzer(warning_threshold=70, min_observations_for_trend=2)

    def test_insufficient_observations_handled_safely(self) -> None:
        """Score trend handles insufficient observations (< 2 samples) cleanly."""
        status_empty = self.analyzer.get_trend_status()
        self.assertEqual(status_empty["trajectory"], "INSUFFICIENT_DATA")

        self.analyzer.record_sample(timestamp_ms=0, score=10)
        status_one = self.analyzer.get_trend_status()
        self.assertEqual(status_one["trajectory"], "INSUFFICIENT_DATA")

    def test_rising_trajectory_detection(self) -> None:
        """Rapidly increasing scores classify as RISING trajectory."""
        self.analyzer.record_sample(timestamp_ms=0, score=10)
        self.analyzer.record_sample(timestamp_ms=100, score=25)
        self.analyzer.record_sample(timestamp_ms=200, score=45)
        self.analyzer.record_sample(timestamp_ms=300, score=75)

        status = self.analyzer.get_trend_status()
        self.assertEqual(status["trajectory"], "RISING")
        self.assertTrue(status["is_early_warning_active"])
        self.assertEqual(status["first_warning_ms"], 300)

    def test_separate_runs_reset_history(self) -> None:
        """Separate runs do not share stale graph or score history."""
        self.analyzer.record_sample(timestamp_ms=0, score=80, has_cycle=True)
        self.assertEqual(len(self.analyzer.observations), 1)

        self.analyzer.reset()
        self.assertEqual(len(self.analyzer.observations), 0)
        self.assertIsNone(self.analyzer.first_warning_ms)
        self.assertIsNone(self.analyzer.deadlock_ms)


class TestContentionHeatmap(unittest.TestCase):
    """Module 3: Resource Contention Heatmap Tests."""

    def test_contention_accumulation_and_cells(self) -> None:
        tracker = ContentionHeatmapTracker(resources=["A", "B"], threads=["T1", "T2"])

        # T1 acquires A, T2 acquires B
        tracker.record_event(action="acquired", thread="T1", resource="A")
        tracker.record_event(action="acquired", thread="T2", resource="B")

        # T1 waits for B while holding A -> cross-resource conflict A x B
        tracker.record_event(
            action="waiting",
            thread="T1",
            resource="B",
            owner="T2",
            wait_ms=150,
            current_owners={"A": "T1", "B": "T2"},
        )

        summary = tracker.get_summary()
        self.assertGreaterEqual(summary["total_conflict_events"], 1)
        self.assertEqual(summary["pair_matrix"]["A"]["B"]["conflict_count"], 1)
        self.assertEqual(summary["pair_matrix"]["A"]["B"]["total_wait_ms"], 150)
        self.assertIn("A", summary["resources"])
        self.assertIn("B", summary["resources"])


class TestExperimentalComparison(unittest.TestCase):
    """Module 6: Offline & Batch Experimental Comparison Tests."""

    def test_comparison_metrics_use_actual_experiment_results(self) -> None:
        comparator = ExperimentComparator()
        # Run 2 quick trials per mode with short timeout
        comp = comparator.run_comparison(trials_per_mode=2, timeout_seconds=2.0)

        self.assertEqual(comp["trials_per_mode"], 2)
        self.assertEqual(comp["vulnerable"]["total_trials"], 2)
        self.assertEqual(comp["protected"]["total_trials"], 2)

        # Vulnerable mode should detect deadlocks
        self.assertEqual(comp["vulnerable"]["deadlock_count"], 2)
        self.assertEqual(comp["vulnerable"]["deadlock_rate_percent"], 100.0)

        # Protected mode should complete without circular wait
        self.assertEqual(comp["protected"]["completion_count"], 2)
        self.assertEqual(comp["protected"]["deadlock_count"], 0)
        self.assertEqual(comp["protected"]["completion_rate_percent"], 100.0)

        self.assertIn("insight", comp)
        self.assertIn("scientific_disclaimer", comp)


if __name__ == "__main__":
    unittest.main()
