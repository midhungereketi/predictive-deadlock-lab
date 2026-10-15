"""Tests for vulnerable deadlock experiment mode.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import pytest
from member2_backend.vulnerable_experiment import run_vulnerable_experiment
from member2_backend.experiment_runner import run_experiment


def test_vulnerable_deadlock_detection_and_cycle():
    """Verify that vulnerable mode creates conflicting requests and detects circular wait."""
    result = run_vulnerable_experiment(
        trial_id="test-vuln-001",
        timeout_seconds=3.0,
        lock_timeout_seconds=0.5,
    )

    assert result.trial_id == "test-vuln-001"
    assert result.mode == "vulnerable"
    assert result.status == "deadlock"
    assert result.deadlock_detected is True
    assert result.metrics.deadlock_cycle == ["T1", "T2", "T1"]
    assert result.metrics.threads_started == 2

    # Verify event stream
    events = result.events
    assert len(events) >= 5

    # Check for start and deadlock_detected actions
    actions = [e.action for e in events]
    assert "start" in actions
    assert "deadlock_detected" in actions

    # Verify shared event schema fields on all events
    for e in events:
        assert isinstance(e.time, float)
        assert e.thread in ("T1", "T2", "system")
        assert isinstance(e.action, str)
        assert e.resource in ("A", "B", None)
        assert e.owner in ("T1", "T2", None)
        assert isinstance(e.wait_ms, int)
        assert e.wait_ms >= 0


def test_vulnerable_safe_cleanup_and_thread_termination():
    """Verify that all worker threads terminate and no locks remain held."""
    initial_threads = threading.active_count()

    result = run_experiment(mode="vulnerable", timeout_seconds=3.0)

    assert result.deadlock_detected is True
    assert result.completion_time_ms < 3000

    # Ensure no leftover background worker threads remain running
    final_threads = threading.active_count()
    assert final_threads <= initial_threads + 1

    # Verify releases occurred in metrics
    assert result.metrics.lock_releases >= 2


def test_vulnerable_repeated_trials_independence():
    """Verify that multiple consecutive vulnerable runs run independently without state pollution."""
    for i in range(3):
        res = run_experiment(mode="vulnerable", trial_id=f"rep-vuln-{i}", timeout_seconds=2.5)
        assert res.deadlock_detected is True
        assert res.status == "deadlock"
        assert res.metrics.deadlock_cycle == ["T1", "T2", "T1"]
