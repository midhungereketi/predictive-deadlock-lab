"""Tests for bounded wait execution, timeout enforcement, and error handling.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import time
import pytest
from member2_backend.experiment_runner import run_experiment
from member2_backend.lock_manager import LockManager
from member2_backend.event_logger import EventLogger


def test_lock_manager_bounded_timeout():
    """Verify that LockManager bounded acquire exits within the specified timeout."""
    logger = EventLogger(trial_id="test-timeout-mgr", mode="vulnerable")
    mgr = LockManager(logger=logger)

    # Thread 1 acquires lock A
    assert mgr.acquire("T1", "A", timeout=1.0) is True

    # Thread 2 attempts to acquire lock A with bounded timeout 0.2s
    t0 = time.monotonic()
    success = mgr.acquire("T2", "A", timeout=0.2)
    elapsed = time.monotonic() - t0

    assert success is False
    assert 0.15 <= elapsed <= 0.6  # Bounded execution

    # Verify timeout event was logged
    events = logger.get_events()
    timeout_events = [e for e in events if e.action == "timeout"]
    assert len(timeout_events) == 1
    assert timeout_events[0].resource == "A"
    assert timeout_events[0].owner == "T1"

    # Cleanup
    mgr.release("T1", "A")


def test_invalid_experiment_mode_error_handling():
    """Verify that an invalid experiment mode returns structured error response without hanging."""
    res = run_experiment(mode="unknown_mode")
    assert res.status == "error"
    assert res.deadlock_detected is False
    assert "Invalid experiment mode" in str(res.error)
