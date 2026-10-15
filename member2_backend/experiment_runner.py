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

def to_trial_v1(result: ExperimentResult, scorer=None) -> Dict[str, Any]:
    """Convert observed raw events to the frontend's version 1 trial format.

    A failed or timed-out experiment cannot be represented as a successful
    frontend trial. A deadlock must be supported by the observed wait-for graph;
    no ownership, wait, timing, or contention values are manufactured here.
    """
    from member3_analysis.graph import WaitForGraph
    from member3_analysis.threat_scorer import ThreatScorer
    from .schemas import TrialV1Output

    if result.mode not in ("vulnerable", "protected"):
        raise ValueError("Unsupported trial mode.")
    if result.status not in ("deadlock", "completed"):
        raise ValueError(f"Cannot display {result.status} experiment as a completed trial.")
    if result.deadlock_detected != (result.status == "deadlock"):
        raise ValueError("Experiment status and deadlock flag disagree.")

    graph = WaitForGraph()
    scorer = scorer or ThreatScorer()
    active_wait_since: Dict[str, int] = {}
    peak_wait_ms = 0
    contention_count = 0
    last_ts_ms = 0
    terminal_seen = False

    events: List[Dict[str, Any]] = [{
        "timestamp_ms": 0,
        "thread_id": "system",
        "action": "start",
        "owners": {},
        "waits": {},
        "risk_score": 0,
        "wait_duration_ms": 0,
        "contention_count": 0,
    }]
    action_map = {
        "requested": "request",
        "waiting": "wait",
        "acquired": "acquire",
        "released": "release",
        "policy_applied": "policy_applied",
        "warning": "warning",
        "deadlock_detected": "deadlock_detected",
        "complete": "complete",
    }

    for raw in result.events:
        if raw.action == "start":
            continue
        if raw.action == "timeout":
            raise ValueError("A timeout occurred before a valid terminal result.")
        action = action_map.get(raw.action)
        if action is None:
            raise ValueError(f"Unsupported raw action: {raw.action}")
        if raw.thread not in ("T1", "T2", "system"):
            raise ValueError(f"Unsupported thread: {raw.thread}")
        if raw.resource is not None and raw.resource not in ("A", "B"):
            raise ValueError(f"Unsupported resource: {raw.resource}")

        ts_ms = max(last_ts_ms, int(round(raw.time * 1000)))
        last_ts_ms = ts_ms
        previous_wait = graph.waits.get(raw.thread)
        snapshot = graph.process_raw_event(raw.model_dump())
        owners = snapshot["owners"]
        waits = snapshot["waits"]

        for thread, resource in waits.items():
            if owners.get(resource) not in ("T1", "T2") or owners[resource] == thread:
                raise ValueError("Raw events contain a wait without another lock owner.")

        if action == "wait" and previous_wait != raw.resource:
            if raw.thread not in waits:
                raise ValueError("A wait event has no observed lock dependency.")
            contention_count += 1

        for thread, started_at in list(active_wait_since.items()):
            peak_wait_ms = max(peak_wait_ms, ts_ms - started_at)
            if thread not in waits:
                del active_wait_since[thread]
        for thread in waits:
            active_wait_since.setdefault(thread, ts_ms)
        peak_wait_ms = max(peak_wait_ms, raw.wait_ms)

        if action == "deadlock_detected":
            if result.status != "deadlock" or not snapshot["has_cycle"]:
                raise ValueError("Deadlock notification lacks an observed Wait-For Graph cycle.")
            terminal_seen = True
        elif action == "complete":
            if result.status != "completed" or owners or waits or result.metrics.threads_completed != 2:
                raise ValueError("Completion event does not match two finished, unlocked threads.")
            terminal_seen = True

        score = scorer.evaluate(
            num_blocked=len(waits),
            wait_duration_ms=peak_wait_ms,
            contention_count=contention_count,
            owners=owners,
            waits=waits,
            has_cycle=snapshot["has_cycle"],
        ).score
        event: Dict[str, Any] = {
            "timestamp_ms": ts_ms,
            "thread_id": raw.thread,
            "action": action,
            "owners": dict(owners),
            "waits": dict(waits),
            "risk_score": score,
            "wait_duration_ms": peak_wait_ms,
            "contention_count": contention_count,
        }
        if raw.resource is not None:
            event["resource_id"] = raw.resource
        events.append(event)
        if terminal_seen:
            break

    if not terminal_seen:
        raise ValueError("Experiment has no observed terminal deadlock or completion event.")

    payload = {
        "schema_version": 1,
        "run_id": result.trial_id,
        "mode": result.mode,
        "status": result.status,
        "events": events,
    }
    TrialV1Output.model_validate(payload)
    return payload
