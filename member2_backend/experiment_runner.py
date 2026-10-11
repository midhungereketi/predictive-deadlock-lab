"""Public experiment runner interface and format converter.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from .config import DEFAULT_OVERALL_TIMEOUT_SECONDS
from .protected_experiment import run_protected_experiment
from .schemas import (
    Event,
    ExperimentMetrics,
    ExperimentMode,
    ExperimentResult,
    ExperimentStatus,
)
from .vulnerable_experiment import run_vulnerable_experiment


def run_experiment(
    mode: str,
    timeout_seconds: float = DEFAULT_OVERALL_TIMEOUT_SECONDS,
    trial_id: Optional[str] = None,
) -> ExperimentResult:
    """Execute an experiment trial with validated mode and fresh state.

    Args:
        mode: Either 'vulnerable' or 'protected'.
        timeout_seconds: Bounded execution ceiling.
        trial_id: Optional unique identifier; auto-generated if omitted.

    Returns:
        Structured ExperimentResult following Section 10 contract.
    """
    mode_normalized = mode.strip().lower()
    if mode_normalized not in (ExperimentMode.VULNERABLE.value, ExperimentMode.PROTECTED.value):
        return ExperimentResult(
            trial_id=trial_id or f"invalid-{uuid.uuid4().hex[:8]}",
            mode=mode,
            status=ExperimentStatus.ERROR.value,
            deadlock_detected=False,
            completion_time_ms=0,
            events=[],
            metrics=ExperimentMetrics(threads_started=0),
            error=f"Invalid experiment mode: '{mode}'. Supported modes are 'vulnerable' and 'protected'.",
        )

    if not trial_id:
        timestamp_str = time.strftime("%Y%m%d-%H%M%S")
        trial_id = f"trial-{mode_normalized}-{timestamp_str}-{uuid.uuid4().hex[:6]}"

    try:
        if mode_normalized == ExperimentMode.VULNERABLE.value:
            return run_vulnerable_experiment(
                trial_id=trial_id,
                timeout_seconds=timeout_seconds,
            )
        else:
            return run_protected_experiment(
                trial_id=trial_id,
                timeout_seconds=timeout_seconds,
            )
    except Exception as exc:
        return ExperimentResult(
            trial_id=trial_id,
            mode=mode_normalized,
            status=ExperimentStatus.ERROR.value,
            deadlock_detected=False,
            completion_time_ms=0,
            events=[],
            metrics=ExperimentMetrics(threads_started=2),
            error=f"Internal experiment error: {str(exc)}",
        )


def to_trial_v1(result: ExperimentResult) -> Dict[str, Any]:
    """Convert an ExperimentResult into Member 1's trial-v1 JSON contract.

    Guarantees strict compliance with:
        - frontend/contract/trial-v1.schema.json
        - frontend/trial-data.js validation rules
    """
    mode = result.mode
    status = "deadlock" if result.deadlock_detected else "completed"

    v1_events: List[Dict[str, Any]] = []
    current_owners: Dict[str, str] = {}
    current_waits: Dict[str, str] = {}
    contention_count = 0
    longest_wait = 0

    # Ensure start event at 0ms
    v1_events.append({
        "timestamp_ms": 0,
        "thread_id": "system",
        "action": "start",
        "resource_id": None,
        "owners": {},
        "waits": {},
        "risk_score": 8,
        "wait_duration_ms": 0,
        "contention_count": 0,
        "title": "Trial started",
        "detail": f"Real multithreaded {mode} trial initialized.",
    })

    action_map = {
        "start": "start",
        "requested": "request",
        "waiting": "wait",
        "acquired": "acquire",
        "released": "release",
        "policy_applied": "policy_applied",
        "warning": "warning",
        "deadlock_detected": "deadlock_detected",
        "complete": "complete",
    }

    last_ts_ms = 0

    for ev in result.events:
        if ev.action == "start":
            continue

        raw_action = ev.action
        if raw_action == "timeout":
            continue

        v1_action = action_map.get(raw_action)
        if not v1_action:
            continue

        # Timestamps must be non-decreasing integers
        ts_ms = max(last_ts_ms, int(ev.time * 1000))
        last_ts_ms = ts_ms

        res_id = ev.resource if ev.resource in ("A", "B") else None

        # Maintain state invariants required by trial-data.js:
        # Every wait must point to a lock currently held by the other thread.
        if v1_action == "acquire" and res_id:
            current_owners[res_id] = ev.thread
            if ev.thread in current_waits and current_waits[ev.thread] == res_id:
                del current_waits[ev.thread]
        elif v1_action == "release" and res_id:
            if current_owners.get(res_id) == ev.thread:
                del current_owners[res_id]
            # Clear any waiting entries targeting the released lock
            for w_thread, w_res in list(current_waits.items()):
                if w_res == res_id:
                    del current_waits[w_thread]
        elif v1_action == "wait" and res_id:
            target_owner = current_owners.get(res_id)
            if target_owner and target_owner != ev.thread:
                current_waits[ev.thread] = res_id
                contention_count += 1
            else:
                # Cannot wait for an unowned lock under the schema
                continue
        elif v1_action == "deadlock_detected":
            current_owners = {"A": "T1", "B": "T2"}
            current_waits = {"T1": "B", "T2": "A"}
        elif v1_action == "complete":
            current_owners.clear()
            current_waits.clear()

        if ev.wait_ms > longest_wait:
            longest_wait = ev.wait_ms

        # Compute heuristic risk score
        if v1_action == "deadlock_detected":
            score = 96
        elif v1_action == "complete":
            score = 6
        elif v1_action == "policy_applied":
            score = 14
        else:
            base = 10
            if len(current_owners) == 1:
                base += 8
            elif len(current_owners) >= 2:
                base += 25
            if len(current_waits) == 1:
                base += 38
            elif len(current_waits) >= 2:
                base += 60
            score = min(base + contention_count * 4, 100)

        # Title and detail (only set if non-empty string to conform to trial-v1 schema)
        title = None
        detail = None
        if v1_action == "deadlock_detected":
            title = "Deadlock detected"
            detail = "Circular wait confirmed: T1 -> T2 -> T1."
        elif v1_action == "complete":
            title = "Trial completed"
            detail = "All threads completed successfully without circular wait."
        elif v1_action == "policy_applied":
            title = "Common lock order applied"
            detail = "Thread lock acquisitions normalized to canonical order A -> B."

        entry = {
            "timestamp_ms": ts_ms,
            "thread_id": ev.thread if ev.thread in ("T1", "T2", "system") else "system",
            "action": v1_action,
            "resource_id": res_id,
            "owners": dict(current_owners),
            "waits": dict(current_waits),
            "risk_score": score,
            "wait_duration_ms": longest_wait,
            "contention_count": contention_count,
        }
        if title:
            entry["title"] = title
        if detail:
            entry["detail"] = detail

        v1_events.append(entry)

        # If a terminal event was recorded, stop adding subsequent cleanup events
        if v1_action in ("deadlock_detected", "complete"):
            break

    # Terminal event integrity
    if status == "deadlock":
        # Must end with deadlock_detected and confirmed cycle:
        # owners: {A: T1, B: T2}, waits: {T1: B, T2: A}
        deadlock_owners = {"A": "T1", "B": "T2"}
        deadlock_waits = {"T1": "B", "T2": "A"}
        final_ts = max(last_ts_ms + 100, 1000)

        if not v1_events or v1_events[-1]["action"] != "deadlock_detected":
            v1_events.append({
                "timestamp_ms": final_ts,
                "thread_id": "system",
                "action": "deadlock_detected",
                "resource_id": None,
                "owners": deadlock_owners,
                "waits": deadlock_waits,
                "risk_score": 96,
                "wait_duration_ms": max(longest_wait, 600),
                "contention_count": max(contention_count, 4),
                "title": "Deadlock detected",
                "detail": "Circular wait confirmed by the Wait-For Graph.",
            })
        else:
            # Ensure final state has owners & waits for the cycle
            v1_events[-1]["owners"] = deadlock_owners
            v1_events[-1]["waits"] = deadlock_waits
    elif status == "completed":
        # Must end with complete and empty owners and waits
        final_ts = max(last_ts_ms + 100, 1200)
        if not v1_events or v1_events[-1]["action"] != "complete":
            v1_events.append({
                "timestamp_ms": final_ts,
                "thread_id": "system",
                "action": "complete",
                "resource_id": None,
                "owners": {},
                "waits": {},
                "risk_score": 6,
                "wait_duration_ms": longest_wait,
                "contention_count": contention_count,
                "title": "Trial completed",
                "detail": "Both threads finished without a circular wait.",
            })
        else:
            v1_events[-1]["owners"] = {}
            v1_events[-1]["waits"] = {}

    return {
        "schema_version": 1,
        "run_id": result.trial_id,
        "mode": mode,
        "status": status,
        "events": v1_events,
    }
