"""Lock manager providing mutex tracking, ordering enforcement, and cycle detection.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from .config import COMMON_LOCK_ORDER
from .event_logger import EventLogger


class LockManager:
    """Manages shared mutex resources, ownership tracking, and acquisition ordering."""

    def __init__(self, logger: EventLogger, resources: Optional[List[str]] = None):
        self.logger = logger
        self.resource_names = resources or ["A", "B"]
        self._locks: Dict[str, threading.Lock] = {r: threading.Lock() for r in self.resource_names}
        self._meta_lock = threading.Lock()
        self._owners: Dict[str, str] = {}  # resource -> thread
        self._waiters: Dict[str, str] = {}  # thread -> resource

    def get_canonical_order(self, requested_resources: List[str]) -> List[str]:
        """Normalize resource acquisition to the common global order (A -> B)."""
        order_map = {res: idx for idx, res in enumerate(COMMON_LOCK_ORDER)}
        return sorted(requested_resources, key=lambda r: order_map.get(r, 999))

    def is_owned(self, resource_id: str) -> bool:
        """Check if resource is currently owned."""
        with self._meta_lock:
            return resource_id in self._owners

    def get_owner(self, resource_id: str) -> Optional[str]:
        """Get current owner of a resource."""
        with self._meta_lock:
            return self._owners.get(resource_id)

    def get_owners_copy(self) -> Dict[str, str]:
        """Return snapshot of current lock ownership."""
        with self._meta_lock:
            return dict(self._owners)

    def get_waits_copy(self) -> Dict[str, str]:
        """Return snapshot of threads currently waiting."""
        with self._meta_lock:
            return dict(self._waiters)

    def acquire(self, thread_id: str, resource_id: str, timeout: float = 1.0) -> bool:
        """Attempt to acquire a resource with bounded wait and event logging.

        Args:
            thread_id: Thread requesting the lock ('T1' or 'T2').
            resource_id: Mutex identifier ('A' or 'B').
            timeout: Maximum wait time in seconds.

        Returns:
            True if acquired successfully, False if timed out.
        """
        if resource_id not in self._locks:
            raise ValueError(f"Unknown resource: {resource_id}")

        lock = self._locks[resource_id]
        wait_start = time.monotonic()
        observed_wait_ms = 0

        # Step 1: Check initial status and register waiting if held
        with self._meta_lock:
            current_owner = self._owners.get(resource_id)
            if current_owner is not None and current_owner != thread_id:
                self._waiters[thread_id] = resource_id
                self.logger.log_event(
                    thread=thread_id,
                    action="waiting",
                    resource=resource_id,
                    owner=current_owner,
                    wait_ms=0,
                    title=f"{thread_id} waits for lock {resource_id}",
                    detail=f"Lock {resource_id} is held by {current_owner}.",
                )

        # Step 2: Attempt bounded lock acquisition
        acquired = lock.acquire(timeout=timeout)
        wait_elapsed = time.monotonic() - wait_start
        observed_wait_ms = int(wait_elapsed * 1000)

        # Step 3: Update state
        with self._meta_lock:
            if thread_id in self._waiters:
                del self._waiters[thread_id]

            if acquired:
                self._owners[resource_id] = thread_id
                self.logger.log_event(
                    thread=thread_id,
                    action="acquired",
                    resource=resource_id,
                    owner=thread_id,
                    wait_ms=observed_wait_ms,
                    title=f"{thread_id} acquires lock {resource_id}",
                    detail=f"{thread_id} successfully acquired {resource_id} after {observed_wait_ms} ms.",
                )
                return True
            else:
                current_owner = self._owners.get(resource_id)
                self.logger.log_event(
                    thread=thread_id,
                    action="timeout",
                    resource=resource_id,
                    owner=current_owner,
                    wait_ms=observed_wait_ms,
                    title=f"{thread_id} timed out on lock {resource_id}",
                    detail=f"Timed out after {observed_wait_ms} ms waiting for {resource_id}.",
                )
                return False

    def release(self, thread_id: str, resource_id: str) -> bool:
        """Release a held lock and record the release event."""
        if resource_id not in self._locks:
            return False

        lock = self._locks[resource_id]
        with self._meta_lock:
            current_owner = self._owners.get(resource_id)
            if current_owner != thread_id:
                return False
            del self._owners[resource_id]
            # Keep the release and its event ordered before another worker can
            # record an acquisition of the same lock.
            lock.release()
            self.logger.log_event(
                thread=thread_id,
                action="released",
                resource=resource_id,
                owner=None,
                wait_ms=0,
                title=f"{thread_id} releases lock {resource_id}",
                detail=f"Lock {resource_id} released and now available.",
            )
        return True

    def detect_deadlock_cycle(self) -> Optional[List[str]]:
        """Inspect Wait-For Graph and detect if a circular wait exists.

        Returns:
            List of thread IDs forming the cycle (e.g. ['T1', 'T2', 'T1']) or None.
        """
        with self._meta_lock:
            owners = dict(self._owners)
            waits = dict(self._waiters)

        # Build Wait-For Graph: waiter -> owner
        # An edge exists from T_wait to T_owner if T_wait is waiting for a resource held by T_owner
        wfg: Dict[str, str] = {}
        for waiter, resource in waits.items():
            holder = owners.get(resource)
            if holder and holder != waiter:
                wfg[waiter] = holder

        # Check for circular wait between T1 and T2
        if wfg.get("T1") == "T2" and wfg.get("T2") == "T1":
            return ["T1", "T2", "T1"]

        return None
