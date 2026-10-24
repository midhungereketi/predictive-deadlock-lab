"""Controlled multithreaded vulnerable experiment demonstrating circular wait.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import time
from typing import Optional
from .config import VULNERABLE_LOCK_TIMEOUT_SECONDS, VULNERABLE_OBSERVATION_WINDOW_SECONDS
from .event_logger import EventLogger
from .lock_manager import LockManager
from .schemas import ExperimentMetrics, ExperimentResult


def run_vulnerable_experiment(
    trial_id: str,
    timeout_seconds: float = 5.0,
    lock_timeout_seconds: float = VULNERABLE_LOCK_TIMEOUT_SECONDS,
) -> ExperimentResult:
    """Execute a controlled multithreaded experiment with conflicting lock orders.

    Execution Flow:
        1. Thread T1 starts and acquires Lock A.
        2. Thread T2 starts and acquires Lock B.
        3. Barrier synchronizes both threads so each holds one lock.
        4. T1 attempts to acquire Lock B (held by T2).
        5. T2 attempts to acquire Lock A (held by T1).
        6. Supervisor confirms the circular wait in the Wait-For Graph (T1 -> T2 -> T1).
        7. Bounded lock timeouts prevent indefinite blocking.
        8. Both threads release their held locks and terminate cleanly.
    """
    logger = EventLogger(trial_id=trial_id, mode="vulnerable")
    lock_mgr = LockManager(logger=logger, resources=["A", "B"])

    logger.log_event(
        thread="system",
        action="start",
        resource=None,
        owner=None,
        wait_ms=0,
        title="Vulnerable experiment started",
        detail="Threads T1 (A -> B) and T2 (B -> A) initialized.",
    )

    barrier = threading.Barrier(2)
    deadlock_detected_event = threading.Event()
    cycle_nodes: list = []

    t1_status = {"acquired_A": False, "acquired_B": False, "timed_out": False, "finished": False}
    t2_status = {"acquired_B": False, "acquired_A": False, "timed_out": False, "finished": False}

    def worker_t1():
        try:
            # Step 1: Acquire Lock A
            logger.log_event(
                thread="T1",
                action="requested",
                resource="A",
                owner=None,
                wait_ms=0,
                title="T1 requests lock A",
                detail="T1 begins acquisition sequence A -> B.",
            )
            if lock_mgr.acquire("T1", "A", timeout=1.0):
                t1_status["acquired_A"] = True

            # Synchronize with T2 so both hold their respective first lock
            barrier.wait(timeout=2.0)

            # Step 2: Attempt to acquire Lock B (held by T2)
            logger.log_event(
                thread="T1",
                action="requested",
                resource="B",
                owner=lock_mgr.get_owner("B"),
                wait_ms=0,
                title="T1 requests lock B",
                detail="Lock B is currently held by T2; T1 will block.",
            )
            acquired_b = lock_mgr.acquire("T1", "B", timeout=lock_timeout_seconds)
            if acquired_b:
                t1_status["acquired_B"] = True
            else:
                t1_status["timed_out"] = True
        except Exception as e:
            t1_status["error"] = str(e)
        finally:
            # Safe cleanup: Release held locks
            if t1_status["acquired_A"]:
                lock_mgr.release("T1", "A")
            if t1_status["acquired_B"]:
                lock_mgr.release("T1", "B")
            t1_status["finished"] = True

    def worker_t2():
        try:
            # Step 1: Acquire Lock B
            logger.log_event(
                thread="T2",
                action="requested",
                resource="B",
                owner=None,
                wait_ms=0,
                title="T2 requests lock B",
                detail="T2 begins conflicting sequence B -> A.",
            )
            if lock_mgr.acquire("T2", "B", timeout=1.0):
                t2_status["acquired_B"] = True

            # Synchronize with T1 so both hold their respective first lock
            barrier.wait(timeout=2.0)

            # Step 2: Attempt to acquire Lock A (held by T1)
            # Give the observer a measured interval after T1 begins waiting.
            # This staged schedule is part of the controlled case study, not a
            # claim about arbitrary OS scheduling in production systems.
            observation_deadline = time.monotonic() + 0.3
            while lock_mgr.get_waits_copy().get("T1") != "B":
                if time.monotonic() >= observation_deadline:
                    raise RuntimeError("T1 did not enter the expected wait state.")
                time.sleep(0.001)
            time.sleep(VULNERABLE_OBSERVATION_WINDOW_SECONDS)
            logger.log_event(
                thread="T2",
                action="requested",
                resource="A",
                owner=lock_mgr.get_owner("A"),
                wait_ms=0,
                title="T2 requests lock A",
                detail="Lock A is currently held by T1; T2 will block.",
            )
            acquired_a = lock_mgr.acquire("T2", "A", timeout=lock_timeout_seconds)
            if acquired_a:
                t2_status["acquired_A"] = True
            else:
                t2_status["timed_out"] = True
        except Exception as e:
            t2_status["error"] = str(e)
        finally:
            # Safe cleanup: Release held locks
            if t2_status["acquired_B"]:
                lock_mgr.release("T2", "B")
            if t2_status["acquired_A"]:
                lock_mgr.release("T2", "A")
            t2_status["finished"] = True

    start_mono = time.monotonic()
    t1 = threading.Thread(target=worker_t1, name="Worker-T1")
    t2 = threading.Thread(target=worker_t2, name="Worker-T2")

    t1.start()
    t2.start()

    # Active supervisor monitor: Check for circular wait in Wait-For Graph
    monitor_deadline = start_mono + timeout_seconds
    cycle_detected = False

    while time.monotonic() < monitor_deadline:
        cycle = lock_mgr.detect_deadlock_cycle()
        if cycle and not cycle_detected:
            cycle_detected = True
            cycle_nodes = cycle
            logger.log_event(
                thread="system",
                action="deadlock_detected",
                resource=None,
                owner=None,
                wait_ms=0,
                title="Deadlock detected",
                detail="Circular wait confirmed in Wait-For Graph: T1 -> T2 -> T1.",
            )
            deadlock_detected_event.set()

        # Check if both threads have finished their execution
        if t1_status["finished"] and t2_status["finished"]:
            break

        time.sleep(0.01)

    # Ensure both threads join and terminate cleanly within remaining timeout
    remaining_timeout = max(0.5, monitor_deadline - time.monotonic())
    t1.join(timeout=remaining_timeout)
    t2.join(timeout=remaining_timeout)

    total_time_ms = int((time.monotonic() - start_mono) * 1000)
    timed_out_threads = (1 if t1_status["timed_out"] else 0) + (1 if t2_status["timed_out"] else 0)
    completed_threads = (1 if t1_status["acquired_B"] else 0) + (1 if t2_status["acquired_A"] else 0)
    both_finished = not t1.is_alive() and not t2.is_alive()

    if not cycle_detected and completed_threads == 2 and both_finished:
        logger.log_event(thread="system", action="complete")

    metrics_raw = logger.get_metrics_summary()
    metrics = ExperimentMetrics(
        threads_started=2,
        threads_completed=completed_threads,
        threads_timed_out=timed_out_threads,
        peak_wait_ms=metrics_raw["peak_wait_ms"],
        contention_count=metrics_raw["contention_count"],
        lock_acquisitions=metrics_raw["lock_acquisitions"],
        lock_releases=metrics_raw["lock_releases"],
        deadlock_cycle=cycle_nodes if cycle_detected else None,
    )

    return ExperimentResult(
        trial_id=trial_id,
        mode="vulnerable",
        status="deadlock" if cycle_detected else (
            "completed" if completed_threads == 2 and both_finished else "timeout"
        ),
        deadlock_detected=cycle_detected,
        completion_time_ms=total_time_ms,
        events=logger.get_events(),
        metrics=metrics,
        error=None if cycle_detected or (completed_threads == 2 and both_finished) else (
            t1_status.get("error") or t2_status.get("error") or
            "Trial ended without a confirmed cycle or both threads completing."
        ),
    )
