"""Configurable N-thread deadlock experiment on a ring of N shared mutexes.

Every worker Ti needs two neighbouring locks, R_i and R_(i+1), with the last
worker wrapping around to R1 (the dining-philosophers arrangement).

* Vulnerable mode: each worker takes R_i first, all workers rendezvous while
  holding it, and then each requests R_(i+1). Every thread is now waiting for
  the next one, so the wait-for graph is a single cycle through all N threads.
  The supervisor detects the cycle and recovers by aborting one victim thread.
* Protected mode: every worker acquires its two locks in global index order
  (resource hierarchy). The last worker therefore takes R1 before RN, which
  breaks the circular-wait condition and lets all N workers complete.
"""

import threading
import time
import uuid
from typing import Dict, List, Optional

from .config import MULTI_THREAD_HOLD_SECONDS, MULTI_THREAD_MAX, MULTI_THREAD_MIN
from .event_logger import EventLogger
from .lock_manager import LockManager
from .schemas import ExperimentMetrics, ExperimentResult, WaitForSnapshot, WorkerReport


def ring_lock_order(index: int, thread_count: int, mode: str) -> List[str]:
    """Return the locks worker T<index> acquires, in acquisition order."""
    first = index
    second = index % thread_count + 1
    if mode == "protected":
        first, second = min(first, second), max(first, second)
    return [f"R{first}", f"R{second}"]


def run_multi_thread_experiment(
    mode: str,
    thread_count: int = 6,
    timeout_seconds: float = 5.0,
    trial_id: Optional[str] = None,
) -> ExperimentResult:
    """Run thread_count real worker threads against a ring of thread_count locks."""
    if mode not in ("vulnerable", "protected"):
        raise ValueError("Mode must be 'vulnerable' or 'protected'.")
    if not MULTI_THREAD_MIN <= thread_count <= MULTI_THREAD_MAX:
        raise ValueError(
            f"Thread count must be between {MULTI_THREAD_MIN} and {MULTI_THREAD_MAX}."
        )

    trial_id = trial_id or "multi-" + uuid.uuid4().hex[:12]
    thread_ids = [f"T{index}" for index in range(1, thread_count + 1)]
    resources = [f"R{index}" for index in range(1, thread_count + 1)]
    lock_orders = {
        thread_id: ring_lock_order(index, thread_count, mode)
        for index, thread_id in enumerate(thread_ids, start=1)
    }
    logger = EventLogger(trial_id=trial_id, mode=mode)
    lock_mgr = LockManager(logger=logger, resources=resources, order=resources)
    cancel_events = {thread_id: threading.Event() for thread_id in thread_ids}
    reports: Dict[str, Dict[str, object]] = {
        thread_id: {"native_id": None, "outcome": "error", "finished_ms": None, "error": None}
        for thread_id in thread_ids
    }
    # All workers start together; in vulnerable mode they also meet again while
    # each holds its first lock, which guarantees the full circular wait.
    start_barrier = threading.Barrier(thread_count)
    hold_barrier = threading.Barrier(thread_count)
    barrier_timeout = max(1.0, timeout_seconds / 2)
    start_clock = time.perf_counter()

    logger.log_event(
        thread="system",
        action="start",
        title=f"{thread_count}-thread {mode} ring started",
        detail=f"{thread_count} real worker threads share a ring of {thread_count} locks.",
    )

    def elapsed_ms() -> int:
        return int((time.perf_counter() - start_clock) * 1000)

    def execute_worker(thread_id: str) -> None:
        report = reports[thread_id]
        report["native_id"] = threading.get_native_id()
        acquired: List[str] = []
        try:
            start_barrier.wait(timeout=barrier_timeout)
            for position, resource in enumerate(lock_orders[thread_id]):
                logger.log_event(
                    thread=thread_id,
                    action="requested",
                    resource=resource,
                    owner=lock_mgr.get_owner(resource),
                    title=f"{thread_id} requests lock {resource}",
                    detail=f"{thread_id} requests {resource} in {mode} mode.",
                )
                if not lock_mgr.acquire(thread_id, resource, timeout=timeout_seconds,
                                        cancel_event=cancel_events[thread_id]):
                    report["outcome"] = "aborted" if cancel_events[thread_id].is_set() else "timed_out"
                    return
                acquired.append(resource)
                if mode == "vulnerable" and position == 0:
                    hold_barrier.wait(timeout=barrier_timeout)
            time.sleep(MULTI_THREAD_HOLD_SECONDS)
            report["outcome"] = "completed"
        except threading.BrokenBarrierError:
            report["error"] = "Worker rendezvous did not complete in time."
        except Exception as exc:
            report["error"] = str(exc)
        finally:
            for resource in reversed(acquired):
                lock_mgr.release(thread_id, resource)
            report["finished_ms"] = elapsed_ms()

    workers = [
        threading.Thread(target=execute_worker, args=(thread_id,), name=f"Ring-{thread_id}", daemon=True)
        for thread_id in thread_ids
    ]
    for worker in workers:
        worker.start()

    # Supervisor loop: watch the live wait-for graph until every worker exits.
    cycle: Optional[List[str]] = None
    victim: Optional[str] = None
    deadlock_snapshot: Optional[WaitForSnapshot] = None
    peak_snapshot: Optional[WaitForSnapshot] = None
    deadline = start_clock + timeout_seconds + 1.0
    while any(worker.is_alive() for worker in workers) and time.perf_counter() < deadline:
        owners, waits = lock_mgr.snapshot_state()
        if peak_snapshot is None or len(waits) > len(peak_snapshot.waits):
            peak_snapshot = WaitForSnapshot(label="peak_contention", time_ms=round((time.perf_counter() - start_clock) * 1000, 2),
                                            owners=owners, waits=waits)
        if mode == "vulnerable" and cycle is None:
            cycle = lock_mgr.detect_deadlock_cycle(owners, waits)
            if cycle:
                deadlock_snapshot = WaitForSnapshot(label="deadlock", time_ms=round((time.perf_counter() - start_clock) * 1000, 2),
                                                    owners=owners, waits=waits)
                logger.log_event(
                    thread="system",
                    action="deadlock_detected",
                    title="Deadlock detected",
                    detail=f"Circular wait through {len(cycle) - 1} threads: " + " → ".join(cycle) + ".",
                )
                # Recovery: preempt the highest-numbered (youngest) thread in the cycle.
                victim = max(cycle, key=lambda thread_id: int(thread_id[1:]))
                logger.log_event(
                    thread="system",
                    action="recovery",
                    title=f"Recovery: abort {victim}",
                    detail=f"{victim} is aborted and releases {lock_orders[victim][0]} so the other threads can finish.",
                )
                cancel_events[victim].set()
        time.sleep(0.001)

    for worker in workers:
        worker.join(timeout=0.5)
    still_running = any(worker.is_alive() for worker in workers)

    completed_count = sum(report["outcome"] == "completed" for report in reports.values())
    timed_out_count = sum(report["outcome"] == "timed_out" for report in reports.values())
    if mode == "protected" and completed_count == thread_count and not still_running:
        logger.log_event(
            thread="system",
            action="complete",
            title="All worker threads completed",
            detail=f"All {thread_count} workers completed; global lock order prevented a circular wait.",
        )

    events = logger.get_events()
    waited_ms = {thread_id: 0 for thread_id in thread_ids}
    for event in events:
        if event.thread in waited_ms and event.action in ("acquired", "timeout", "aborted"):
            waited_ms[event.thread] += event.wait_ms

    if cycle:
        status = "deadlock"
    elif mode == "protected" and completed_count == thread_count and not still_running:
        status = "completed"
    elif still_running or timed_out_count:
        status = "timeout"
    else:
        status = "error"
    errors = sorted({str(report["error"]) for report in reports.values() if report["error"]})
    metrics_raw = logger.get_metrics_summary()
    return ExperimentResult(
        trial_id=trial_id,
        mode=mode,
        status=status,
        deadlock_detected=cycle is not None,
        completion_time_ms=elapsed_ms(),
        events=events,
        metrics=ExperimentMetrics(
            threads_started=len(workers),
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
        resources=resources,
        workers=[
            WorkerReport(
                thread=thread_id,
                native_id=reports[thread_id]["native_id"],
                lock_order=lock_orders[thread_id],
                outcome=str(reports[thread_id]["outcome"]),
                waited_ms=waited_ms[thread_id],
                finished_ms=reports[thread_id]["finished_ms"],
            )
            for thread_id in thread_ids
        ],
        snapshot=deadlock_snapshot or peak_snapshot,
        victim=victim,
    )
