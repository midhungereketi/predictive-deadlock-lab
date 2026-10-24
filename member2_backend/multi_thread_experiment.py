"""Configurable multi-thread deadlock simulation using two shared mutexes."""

import threading
import time
import uuid
from typing import Dict, List, Optional

from .event_logger import EventLogger
from .lock_manager import LockManager
from .schemas import ExperimentMetrics, ExperimentResult


def run_multi_thread_experiment(
    mode: str,
    thread_count: int = 6,
    timeout_seconds: float = 5.0,
    trial_id: Optional[str] = None,
) -> ExperimentResult:
    """Run 3–12 real worker threads against shared locks A and B.

    Vulnerable mode synchronizes T1 and T2 after taking opposite first locks,
    guaranteeing a real two-node cycle; other workers contend on the same locks.
    Protected mode has every worker acquire both locks in A → B order.
    """
    if mode not in ("vulnerable", "protected"):
        raise ValueError("Mode must be 'vulnerable' or 'protected'.")
    if not 3 <= thread_count <= 12:
        raise ValueError("Thread count must be between 3 and 12.")

    trial_id = trial_id or "multi-" + uuid.uuid4().hex[:12]
    thread_ids = [f"T{index}" for index in range(1, thread_count + 1)]
    logger = EventLogger(trial_id=trial_id, mode=mode)
    lock_mgr = LockManager(logger=logger, resources=["A", "B"])
    lock_timeout = 0.8
    statuses: Dict[str, Dict[str, object]] = {
        thread_id: {"completed": False, "timed_out": False, "error": None}
        for thread_id in thread_ids
    }
    worker_threads: List[threading.Thread] = []
    cycle: Optional[List[str]] = None
    start_mono = time.monotonic()

    logger.log_event(
        thread="system",
        action="start",
        title=f"{thread_count}-thread {mode} simulation started",
        detail=f"{thread_count} real worker threads share locks A and B.",
    )

    def execute_worker(
        thread_id: str,
        requested_locks: List[str],
        rendezvous: Optional[threading.Barrier] = None,
        worker_lock_timeout: float = lock_timeout,
    ) -> None:
        acquired: List[str] = []
        status = statuses[thread_id]
        try:
            for resource in requested_locks:
                logger.log_event(
                    thread=thread_id,
                    action="requested",
                    resource=resource,
                    owner=lock_mgr.get_owner(resource),
                    title=f"{thread_id} requests lock {resource}",
                    detail=f"{thread_id} requests {resource} in {mode} mode.",
                )
                if not lock_mgr.acquire(thread_id, resource, timeout=worker_lock_timeout):
                    status["timed_out"] = True
                    return
                acquired.append(resource)
                if rendezvous is not None and len(acquired) == 1:
                    rendezvous.wait(timeout=lock_timeout)
            time.sleep(0.02)
            status["completed"] = True
        except threading.BrokenBarrierError:
            status["error"] = "The vulnerable lock rendezvous did not complete."
        except Exception as exc:
            status["error"] = str(exc)
        finally:
            for resource in reversed(acquired):
                lock_mgr.release(thread_id, resource)

    def start_worker(
        thread_id: str,
        requested_locks: List[str],
        rendezvous: Optional[threading.Barrier] = None,
        worker_lock_timeout: float = lock_timeout,
    ) -> None:
        worker = threading.Thread(
            target=execute_worker,
            args=(thread_id, requested_locks, rendezvous, worker_lock_timeout),
            name=f"Multi-{thread_id}",
        )
        worker_threads.append(worker)
        worker.start()

    if mode == "vulnerable":
        rendezvous = threading.Barrier(2)
        start_worker("T1", ["A", "B"], rendezvous)
        start_worker("T2", ["B", "A"], rendezvous)
        detection_deadline = start_mono + timeout_seconds
        while time.monotonic() < detection_deadline:
            cycle = lock_mgr.detect_deadlock_cycle()
            if cycle:
                break
            if any(statuses[thread_id]["error"] for thread_id in ("T1", "T2")):
                break
            time.sleep(0.002)

        # Start remaining contending workers against the held locks
        for index, thread_id in enumerate(thread_ids[2:], start=3):
            requested = ["A"] if index % 2 else ["B"]
            start_worker(thread_id, requested, worker_lock_timeout=lock_timeout * 3)

        # Give contending workers a moment to contend and register wait states
        time.sleep(0.015)

        # Re-verify and log deadlock cycle with full multi-thread dependency context
        cycle = lock_mgr.detect_deadlock_cycle() or cycle
        if cycle:
            logger.log_event(
                thread="system",
                action="deadlock_detected",
                title="Deadlock detected",
                detail="Circular wait confirmed: " + " → ".join(cycle) + ".",
            )
    else:
        for thread_id in thread_ids:
            start_worker(thread_id, ["A", "B"])

    join_deadline = time.monotonic() + max(timeout_seconds, lock_timeout * 2 + 1.0)
    for worker in worker_threads:
        worker.join(timeout=max(0.0, join_deadline - time.monotonic()))

    still_running = any(worker.is_alive() for worker in worker_threads)
    completed_count = sum(bool(status["completed"]) for status in statuses.values())
    timed_out_count = sum(bool(status["timed_out"]) for status in statuses.values())
    metrics_raw = logger.get_metrics_summary()
    if mode == "protected" and completed_count == thread_count and not still_running:
        logger.log_event(
            thread="system",
            action="complete",
            title="All worker threads completed",
            detail=f"All {thread_count} workers completed without a circular wait.",
        )

    status = "deadlock" if cycle else (
        "completed" if mode == "protected" and completed_count == thread_count and not still_running
        else "timeout" if still_running or timed_out_count
        else "error"
    )
    errors = [str(item["error"]) for item in statuses.values() if item["error"]]
    return ExperimentResult(
        trial_id=trial_id,
        mode=mode,
        status=status,
        deadlock_detected=cycle is not None,
        completion_time_ms=int((time.monotonic() - start_mono) * 1000),
        events=logger.get_events(),
        metrics=ExperimentMetrics(
            threads_started=len(worker_threads),
            threads_completed=completed_count,
            threads_timed_out=timed_out_count,
            peak_wait_ms=metrics_raw["peak_wait_ms"],
            contention_count=metrics_raw["contention_count"],
            lock_acquisitions=metrics_raw["lock_acquisitions"],
            lock_releases=metrics_raw["lock_releases"],
            deadlock_cycle=cycle,
        ),
        error="; ".join(errors) if errors else (
            "One or more workers did not finish before the bounded deadline."
            if status in ("timeout", "error") else None
        ),
    )
