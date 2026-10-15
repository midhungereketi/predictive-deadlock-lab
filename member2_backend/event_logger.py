"""Thread-safe event logger for multithreaded deadlock experiments.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import time
from typing import Any, Dict, List, Optional
from .schemas import Event


class EventLogger:
    """Thread-safe collector for experiment execution events and state snapshots.

    Adheres strictly to the shared schema:
        time, thread, action, resource, owner, wait_ms
    Also maintains internal thread-safe state to generate snapshots for Member 1's
    trial-v1 JSON contract and Member 3's analysis requirements.
    """

    def __init__(self, trial_id: str, mode: str):
        self.trial_id: str = trial_id
        self.mode: str = mode
        self._lock = threading.Lock()
        self._start_time: float = time.monotonic()
        self._events: List[Event] = []
        self._snapshots: List[Dict[str, Any]] = []

        # State tracking
        self._owners: Dict[str, str] = {}
        self._waits: Dict[str, str] = {}
        self._contention_count: int = 0
        self._peak_wait_ms: int = 0
        self._lock_acquisitions: int = 0
        self._lock_releases: int = 0

    def reset_timer(self) -> None:
        """Reset start timestamp to align exactly with experiment thread launch."""
        with self._lock:
            self._start_time = time.monotonic()

    def log_event(
        self,
        thread: str,
        action: str,
        resource: Optional[str] = None,
        owner: Optional[str] = None,
        wait_ms: int = 0,
        title: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> Event:
        """Log a single execution event in a thread-safe manner.

        Args:
            thread: Thread identifier ('T1', 'T2', 'system').
            action: Action string (e.g. 'start', 'requested', 'waiting', 'acquired', 'released', etc.).
            resource: Resource involved ('A', 'B', or None).
            owner: Current owner of resource at time of event.
            wait_ms: Observed waiting duration in milliseconds.
            title: Optional short human-readable title for UI.
            detail: Optional human-readable detail for UI.

        Returns:
            The recorded Event object.
        """
        with self._lock:
            elapsed_sec = max(0.0, time.monotonic() - self._start_time)
            rounded_sec = round(elapsed_sec, 4)
            wait_int = max(0, int(wait_ms))

            # Maintain lock ownership and waiting state
            if action in ("acquired", "acquire") and resource:
                self._owners[resource] = thread
                if thread in self._waits and self._waits[thread] == resource:
                    del self._waits[thread]
                self._lock_acquisitions += 1
            elif action in ("released", "release") and resource:
                if self._owners.get(resource) == thread:
                    del self._owners[resource]
                self._lock_releases += 1
            elif action in ("waiting", "wait") and resource:
                self._waits[thread] = resource
                self._contention_count += 1
            elif action in ("timeout",) and thread in self._waits:
                del self._waits[thread]

            if wait_int > self._peak_wait_ms:
                self._peak_wait_ms = wait_int

            # Resolve owner if not explicitly passed
            effective_owner = owner
            if effective_owner is None and resource and resource in self._owners:
                effective_owner = self._owners[resource]

            event = Event(
                time=rounded_sec,
                thread=thread,
                action=action,
                resource=resource,
                owner=effective_owner,
                wait_ms=wait_int,
            )
            self._events.append(event)

            # Store full state snapshot for Member 1/3 integrations
            # Calculate heuristic risk score based on observed conditions
            risk_score = self._compute_instantaneous_risk(action)
            snapshot = {
                "timestamp_ms": int(rounded_sec * 1000),
                "thread_id": thread,
                "action": action,
                "resource_id": resource,
                "owners": dict(self._owners),
                "waits": dict(self._waits),
                "risk_score": risk_score,
                "wait_duration_ms": self._peak_wait_ms,
                "contention_count": self._contention_count,
                "title": title,
                "detail": detail,
            }
            self._snapshots.append(snapshot)
            return event

    def _compute_instantaneous_risk(self, current_action: str) -> int:
        """Compute an honest 0-100 heuristic risk score at the current moment."""
        if current_action == "deadlock_detected":
            return 96
        if current_action == "complete":
            return 6
        if current_action == "policy_applied":
            return 14

        score = 8
        held_count = len(self._owners)
        blocked_count = len(self._waits)

        if held_count == 1:
            score += 6
        elif held_count >= 2:
            score += 25

        if blocked_count == 1:
            score += 35
        elif blocked_count >= 2:
            score += 60

        if self._contention_count > 0:
            score += min(self._contention_count * 5, 20)

        return min(max(score, 0), 100)

    def get_events(self) -> List[Event]:
        """Return a copy of all recorded events."""
        with self._lock:
            return list(self._events)

    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Return a copy of all recorded snapshots."""
        with self._lock:
            return [dict(s) for s in self._snapshots]

    def get_owners(self) -> Dict[str, str]:
        """Return current ownership mapping."""
        with self._lock:
            return dict(self._owners)

    def get_waits(self) -> Dict[str, str]:
        """Return current waiting mapping."""
        with self._lock:
            return dict(self._waits)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Return metrics accumulated during the run."""
        with self._lock:
            return {
                "peak_wait_ms": self._peak_wait_ms,
                "contention_count": self._contention_count,
                "lock_acquisitions": self._lock_acquisitions,
                "lock_releases": self._lock_releases,
            }

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Serialize events to raw JSON-compatible list."""
        with self._lock:
            return [e.model_dump() for e in self._events]
