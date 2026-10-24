"""Tests for protected experiment mode using common lock acquisition ordering.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import pytest
from member2_backend.protected_experiment import run_protected_experiment
from member2_backend.experiment_runner import run_experiment
from member2_backend.adaptive_policy import order_from_observation


def test_protected_completes_without_cycle():
    """Verify that protected mode completes both threads and never forms a circular wait."""
    result = run_protected_experiment(
        trial_id="test-prot-001",
        timeout_seconds=3.0,
        lock_timeout_seconds=1.5,
    )

    assert result.trial_id == "test-prot-001"
    assert result.mode == "protected"
    assert result.status == "completed"
    assert result.deadlock_detected is False
    assert result.metrics.deadlock_cycle is None
    assert result.metrics.threads_started == 2
    assert result.metrics.threads_completed == 2
    assert result.metrics.threads_timed_out == 0

    # Verify event stream
    events = result.events
    assert len(events) >= 6

    actions = [e.action for e in events]
    assert "start" in actions
    assert "complete" in actions
    assert "deadlock_detected" not in actions
    assert "warning" in actions
    assert actions.index("warning") < actions.index("policy_applied")
    assert result.events[actions.index("warning")].time < result.events[actions.index("complete")].time

    # Check that policy_applied was recorded for reordering T2
    assert "policy_applied" in actions

    # Verify all events follow the schema
    for e in events:
        assert isinstance(e.time, float)
        assert e.thread in ("T1", "T2", "system")
        assert isinstance(e.action, str)
        assert e.resource in ("A", "B", None)
        assert e.owner in ("T1", "T2", None)
        assert isinstance(e.wait_ms, int)


def test_adaptive_order_comes_from_observed_dependency():
    assert order_from_observation({"A": "T1", "B": "T2"}, {"T1": "B"}, ["A", "B"]) == ["A", "B"]
    assert order_from_observation({"A": "T1", "B": "T2"}, {"T2": "A"}, ["A", "B"]) == ["B", "A"]


def test_protected_repeated_runs_reliability():
    """Verify that protected mode consistently completes across multiple trials."""
    for i in range(3):
        res = run_experiment(mode="protected", trial_id=f"rep-prot-{i}", timeout_seconds=3.0)
        assert res.deadlock_detected is False
        assert res.status == "completed"
        assert res.metrics.threads_completed == 2
