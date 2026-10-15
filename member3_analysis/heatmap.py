"""Resource Contention Heatmap Engine.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

from typing import Any, Dict, List, Optional


class ContentionHeatmapTracker:
    """Tracks measurable contention intensity between resource pairs and across threads.

    Maintains:
    1. Resource-Pair Contention Matrix (e.g., A x B, B x A):
       Measures how frequently threads attempt to acquire one resource while
       another is held, causing lock conflict.
    2. Resource-by-Thread Matrix (Resources A, B vs Threads T1, T2):
       Measures acquisition counts, blocked attempts, and accumulated wait milliseconds
       per resource-thread pair.
    """

    def __init__(self, resources: Optional[List[str]] = None, threads: Optional[List[str]] = None) -> None:
        self.resources = resources or ["A", "B"]
        self.threads = threads or ["T1", "T2"]
        self.reset()

    def reset(self) -> None:
        """Reset all contention counters for a clean trial run."""
        # Pairwise matrix: res1 -> res2 -> metrics
        self.pair_matrix: Dict[str, Dict[str, Dict[str, int]]] = {
            r1: {
                r2: {"conflict_count": 0, "total_wait_ms": 0, "max_wait_ms": 0}
                for r2 in self.resources
            }
            for r1 in self.resources
        }

        # Resource-Thread matrix: resource -> thread -> metrics
        self.thread_matrix: Dict[str, Dict[str, Dict[str, int]]] = {
            r: {
                t: {"acquisitions": 0, "blocked_requests": 0, "total_wait_ms": 0, "max_wait_ms": 0}
                for t in self.threads
            }
            for r in self.resources
        }

        self.total_conflict_events = 0

    def record_event(
        self,
        action: str,
        thread: str,
        resource: Optional[str],
        owner: Optional[str] = None,
        wait_ms: int = 0,
        current_owners: Optional[Dict[str, str]] = None,
    ) -> None:
        """Process an execution event and update measured contention tallies."""
        if not resource or resource not in self.resources:
            return

        current_owners = current_owners or {}

        if action in ("acquired", "acquire"):
            if thread in self.threads:
                self.thread_matrix[resource][thread]["acquisitions"] += 1

        elif action in ("waiting", "wait"):
            if thread in self.threads:
                self.thread_matrix[resource][thread]["blocked_requests"] += 1
                self.thread_matrix[resource][thread]["total_wait_ms"] += wait_ms
                if wait_ms > self.thread_matrix[resource][thread]["max_wait_ms"]:
                    self.thread_matrix[resource][thread]["max_wait_ms"] = wait_ms

            # Identify if thread currently holds another resource, creating cross-resource contention
            held_by_thread = [r for r, o in current_owners.items() if o == thread and r != resource]
            for held_res in held_by_thread:
                if held_res in self.resources:
                    self.pair_matrix[held_res][resource]["conflict_count"] += 1
                    self.pair_matrix[held_res][resource]["total_wait_ms"] += wait_ms
                    if wait_ms > self.pair_matrix[held_res][resource]["max_wait_ms"]:
                        self.pair_matrix[held_res][resource]["max_wait_ms"] = wait_ms
                    self.total_conflict_events += 1

            # If no other lock held by thread, check opposite lock status
            if not held_by_thread:
                other_res = "B" if resource == "A" else "A"
                if other_res in self.resources and other_res in current_owners:
                    self.pair_matrix[other_res][resource]["conflict_count"] += 1
                    self.total_conflict_events += 1

    def get_summary(self) -> Dict[str, Any]:
        """Produce structured heatmap data ready for dashboard rendering and API consumption."""
        # Find peak conflict pair
        max_conflict = 0
        hotspot_pair = None
        for r1 in self.resources:
            for r2 in self.resources:
                if r1 != r2:
                    cnt = self.pair_matrix[r1][r2]["conflict_count"]
                    if cnt > max_conflict:
                        max_conflict = cnt
                        hotspot_pair = f"{r1} → {r2}"

        return {
            "resources": self.resources,
            "threads": self.threads,
            "total_conflict_events": self.total_conflict_events,
            "hotspot_pair": hotspot_pair or "None",
            "pair_matrix": self.pair_matrix,
            "thread_matrix": self.thread_matrix,
            # Flattened cells for easy web visualization
            "pairwise_cells": [
                {
                    "row": r1,
                    "col": r2,
                    "is_diagonal": r1 == r2,
                    "conflict_count": self.pair_matrix[r1][r2]["conflict_count"],
                    "total_wait_ms": self.pair_matrix[r1][r2]["total_wait_ms"],
                    "intensity": (
                        "diagonal" if r1 == r2 else
                        "high" if self.pair_matrix[r1][r2]["conflict_count"] >= 3 else
                        "medium" if self.pair_matrix[r1][r2]["conflict_count"] >= 2 else
                        "low" if self.pair_matrix[r1][r2]["conflict_count"] >= 1 else
                        "zero"
                    ),
                }
                for r1 in self.resources
                for r2 in self.resources
            ],
            "thread_cells": [
                {
                    "resource": r,
                    "thread": t,
                    "acquisitions": self.thread_matrix[r][t]["acquisitions"],
                    "blocked_requests": self.thread_matrix[r][t]["blocked_requests"],
                    "total_wait_ms": self.thread_matrix[r][t]["total_wait_ms"],
                    "max_wait_ms": self.thread_matrix[r][t]["max_wait_ms"],
                }
                for r in self.resources
                for t in self.threads
            ],
            "limitation_note": (
                "Heatmap values reflect real observed thread request conflicts. "
                "In a 2-resource system (A, B), the pair A x B and B x A measures opposite-order lock contention."
            ),
        }
