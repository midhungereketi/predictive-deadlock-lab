"""Coverage for the configurable N-thread resource-ring experiment."""

import threading

import pytest

from member2_backend.config import MULTI_THREAD_MAX, MULTI_THREAD_MIN
from member2_backend.event_logger import EventLogger
from member2_backend.lock_manager import LockManager
from member2_backend.multi_thread_experiment import ring_lock_order, run_multi_thread_experiment


def test_ring_lock_orders():
    assert [ring_lock_order(i, 4, "vulnerable") for i in range(1, 5)] == [
        ["R1", "R2"], ["R2", "R3"], ["R3", "R4"], ["R4", "R1"]
    ]
    # Protected mode takes the lower-numbered lock first, so the last worker
    # acquires R1 before R4 and no circular wait is possible.
    assert ring_lock_order(4, 4, "protected") == ["R1", "R4"]


@pytest.mark.parametrize("thread_count", [MULTI_THREAD_MIN, 5, 12, MULTI_THREAD_MAX])
def test_vulnerable_run_forms_one_cycle_through_every_thread(thread_count):
    result = run_multi_thread_experiment(
        mode="vulnerable",
        thread_count=thread_count,
        timeout_seconds=5.0,
        trial_id=f"multi-vulnerable-{thread_count}",
    )
    thread_ids = [f"T{index}" for index in range(1, thread_count + 1)]

    assert result.status == "deadlock"
    assert result.deadlock_detected is True
    assert result.metrics.threads_started == thread_count
    assert result.metrics.deadlock_cycle == thread_ids + ["T1"]
    assert result.snapshot.label == "deadlock"
    assert len(result.snapshot.waits) == thread_count
    assert result.victim == f"T{thread_count}"
    outcomes = {worker.thread: worker.outcome for worker in result.workers}
    assert outcomes.pop(result.victim) == "aborted"
    assert set(outcomes.values()) == {"completed"}
    assert result.metrics.threads_completed == thread_count - 1
    assert len({worker.native_id for worker in result.workers}) == thread_count
    actions = [event.action for event in result.events]
    assert actions.index("deadlock_detected") < actions.index("recovery")


@pytest.mark.parametrize("thread_count", [MULTI_THREAD_MIN, 8, MULTI_THREAD_MAX])
def test_protected_run_completes_every_thread_without_cycle(thread_count):
    result = run_multi_thread_experiment(
        mode="protected",
        thread_count=thread_count,
        timeout_seconds=5.0,
        trial_id=f"multi-protected-{thread_count}",
    )

    assert result.status == "completed"
    assert result.deadlock_detected is False
    assert result.metrics.deadlock_cycle is None
    assert result.metrics.threads_started == thread_count
    assert result.metrics.threads_completed == thread_count
    assert all(worker.outcome == "completed" for worker in result.workers)
    assert len({worker.native_id for worker in result.workers}) == thread_count
    assert result.victim is None
    assert result.events[-1].action == "complete"


@pytest.mark.parametrize("thread_count", [MULTI_THREAD_MIN - 1, MULTI_THREAD_MAX + 1])
def test_thread_count_is_bounded(thread_count):
    with pytest.raises(ValueError, match=f"between {MULTI_THREAD_MIN} and {MULTI_THREAD_MAX}"):
        run_multi_thread_experiment(mode="protected", thread_count=thread_count)


def test_cancel_event_aborts_a_blocked_acquire():
    logger = EventLogger(trial_id="cancel-test", mode="vulnerable")
    manager = LockManager(logger=logger, resources=["R1"], order=["R1"])
    assert manager.acquire("T1", "R1")
    cancel = threading.Event()
    outcome = {}
    waiter = threading.Thread(
        target=lambda: outcome.update(acquired=manager.acquire("T2", "R1", timeout=5.0, cancel_event=cancel))
    )
    waiter.start()
    cancel.set()
    waiter.join(timeout=1.0)

    assert not waiter.is_alive()
    assert outcome["acquired"] is False
    assert logger.get_events()[-1].action == "aborted"
    assert manager.get_waits_copy() == {}
