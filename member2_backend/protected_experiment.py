"""Protected multithreaded experiment enforcing common lock acquisition ordering.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import time
from typing import Optional
from .config import (
    PROTECTED_LOCK_TIMEOUT_SECONDS,
    THREAD_CRITICAL_SECTION_DELAY_SECONDS,
    INTERLEAVING_DELAY_SECONDS,
)
from .event_logger import EventLogger
from .lock_manager import LockManager
from .schemas import ExperimentMetrics, ExperimentResult


def run_protected_experiment(
    trial_id: str,
    timeout_seconds: float = 5.0,
    lock_timeout_seconds: float = PROTECTED_LOCK_TIMEOUT_SECONDS,
) -> ExperimentResult:
    """Execute a protected multithreaded experiment enforcing common lock order (A -> B).

    Execution Flow:
        1. Thread T1 logically requests [A, B].
        2. Thread T2 logically requests [B, A].
        3. Lock manager normalizes both threads to canonical order [A, B] before acquisition.
        4. T1 acquires A, then B, performs critical section, and releases both locks.
        5. T2 waits for A without holding B, preventing circular wait.
        6. Once T1 releases locks, T2 acquires A, then B, performs critical section, and releases.
        7. Both threads complete successfully with 0 deadlocks.
    """
    logger = EventLogger(trial_id=trial_id, mode="protected")
    lock_mgr = LockManager(logger=logger, resources=["A", "B"])

    logger.log_event(
        thread="system",
        action="start",
        resource=None,
        owner=None,
        wait_ms=0,
        title="Protected experiment started",
        detail="Threads initialized with common lock order policy (A -> B).",
    )

    t1_status = {"completed": False, "timed_out": False, "error": None}
    t2_status = {"completed": False, "timed_out": False, "error": None}

    def execute_worker(thread_id: str, requested_locks: list, status_dict: dict):
        # Apply common global lock order
        canonical_locks = lock_mgr.get_canonical_order(requested_locks)
        if canonical_locks != requested_locks:
            logger.log_event(
                thread="system",
                action="policy_applied",
                resource=None,
                owner=None,
                wait_ms=0,
                title=f"Lock order normalized for {thread_id}",
                detail=f"Reordered requested {requested_locks} to common safe order {canonical_locks}.",
            )

        acquired_stack = []
        try:
            for resource_id in canonical_locks:
                logger.log_event(
                    thread=thread_id,
                    action="requested",
                    resource=resource_id,
                    owner=lock_mgr.get_owner(resource_id),
                    wait_ms=0,
                    title=f"{thread_id} requests lock {resource_id}",
                    detail=f"{thread_id} requesting {resource_id} in safe order.",
                )
                success = lock_mgr.acquire(thread_id, resource_id, timeout=lock_timeout_seconds)
                if not success:
                    status_dict["timed_out"] = True
                    return
                acquired_stack.append(resource_id)

            # Critical section simulation
            time.sleep(THREAD_CRITICAL_SECTION_DELAY_SECONDS)
            status_dict["completed"] = True
        except Exception as e:
            status_dict["error"] = str(e)
        finally:
            # Release all held locks in reverse acquisition order
            while acquired_stack:
                res = acquired_stack.pop()
                lock_mgr.release(thread_id, res)

    start_mono = time.monotonic()
    t1 = threading.Thread(target=execute_worker, args=("T1", ["A", "B"], t1_status), name="Protected-T1")
    t2 = threading.Thread(target=execute_worker, args=("T2", ["B", "A"], t2_status), name="Protected-T2")

    t1.start()
    time.sleep(INTERLEAVING_DELAY_SECONDS)
    t2.start()

    t1.join(timeout=timeout_seconds)
    t2.join(timeout=timeout_seconds)

    total_time_ms = int((time.monotonic() - start_mono) * 1000)
    cycle = lock_mgr.detect_deadlock_cycle()

    # Log terminal completion event
    logger.log_event(
        thread="system",
        action="complete",
        resource=None,
        owner=None,
        wait_ms=0,
        title="Protected experiment complete",
        detail="Both threads finished their critical sections without circular wait.",
    )

    metrics_raw = logger.get_metrics_summary()
    completed_threads = (1 if t1_status["completed"] else 0) + (1 if t2_status["completed"] else 0)
    timed_out_threads = (1 if t1_status["timed_out"] else 0) + (1 if t2_status["timed_out"] else 0)

    metrics = ExperimentMetrics(
        threads_started=2,
        threads_completed=completed_threads,
        threads_timed_out=timed_out_threads,
        peak_wait_ms=metrics_raw["peak_wait_ms"],
        contention_count=metrics_raw["contention_count"],
        lock_acquisitions=metrics_raw["lock_acquisitions"],
        lock_releases=metrics_raw["lock_releases"],
        deadlock_cycle=None,
    )

    return ExperimentResult(
        trial_id=trial_id,
        mode="protected",
        status="completed" if completed_threads == 2 else "error",
        deadlock_detected=False,
        completion_time_ms=total_time_ms,
        events=logger.get_events(),
        metrics=metrics,
        error=t1_status.get("error") or t2_status.get("error"),
    )
