"""Wait-For Graph (WFG) Construction and Cycle Detection Engine.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class EdgeInfo:
    """Represents a directed dependency edge in the Wait-For Graph."""
    waiter: str
    holder: str
    resource: str
    wait_ms: int = 0
    created_at_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.waiter,
            "to": self.holder,
            "resource": self.resource,
            "wait_ms": self.wait_ms,
            "created_at_time": self.created_at_time,
        }


class WaitForGraph:
    """Dynamic Wait-For Graph (WFG) maintaining thread dependencies and detecting cycles.

    In an Operating System:
    - Vertices (Nodes) represent active threads.
    - A directed edge (u -> v) indicates that thread 'u' is blocked, waiting
      for a mutex/resource currently held by thread 'v'.
    - A directed cycle indicates circular wait (Coffman's 4th condition),
      confirming a deadlock among single-instance resources.
    """

    def __init__(self, threads: Optional[List[str]] = None) -> None:
        self.nodes: Set[str] = set(threads) if threads else {"T1", "T2"}
        # Adjacency list: waiter -> Dict[resource, EdgeInfo]
        self.adj: Dict[str, Dict[str, EdgeInfo]] = {t: {} for t in self.nodes}
        self.owners: Dict[str, str] = {}  # resource -> thread
        self.waits: Dict[str, str] = {}   # thread -> resource
        self.history_length: int = 0

    def reset(self) -> None:
        """Clear all dependencies and resource state for a fresh run."""
        for t in self.nodes:
            self.adj[t] = {}
        self.owners.clear()
        self.waits.clear()
        self.history_length = 0

    def add_thread(self, thread: str) -> None:
        """Register a thread node in the graph."""
        if thread and thread != "system":
            self.nodes.add(thread)
            if thread not in self.adj:
                self.adj[thread] = {}

    def add_dependency(
        self,
        waiter: str,
        holder: str,
        resource: str,
        wait_ms: int = 0,
        timestamp: float = 0.0,
    ) -> bool:
        """Add or update a directed edge: waiter -> holder for resource.

        Returns True if edge was added/updated, False if invalid (e.g. self-wait).
        """
        if not waiter or not holder or waiter == holder or not resource:
            return False

        self.add_thread(waiter)
        self.add_thread(holder)

        edge = EdgeInfo(
            waiter=waiter,
            holder=holder,
            resource=resource,
            wait_ms=wait_ms,
            created_at_time=timestamp,
        )
        self.adj[waiter][resource] = edge
        self.waits[waiter] = resource
        return True

    def remove_dependency(self, waiter: str, resource: Optional[str] = None) -> None:
        """Remove a dependency edge for a waiting thread."""
        if waiter in self.adj:
            if resource:
                self.adj[waiter].pop(resource, None)
                if self.waits.get(waiter) == resource:
                    self.waits.pop(waiter, None)
            else:
                self.adj[waiter].clear()
                self.waits.pop(waiter, None)

    def remove_dependencies_for_holder(self, holder: str, resource: Optional[str] = None) -> None:
        """Remove all waiting edges directed toward a holder when resource is released."""
        for waiter, edges in self.adj.items():
            to_remove = []
            for res, edge in edges.items():
                if edge.holder == holder and (resource is None or res == resource):
                    to_remove.append(res)
            for res in to_remove:
                edges.pop(res, None)
                if self.waits.get(waiter) == res:
                    self.waits.pop(waiter, None)

    def process_raw_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a raw execution event and incrementally update graph state.

        Expected fields:
            - time: float (seconds)
            - thread: str ("T1", "T2", "system")
            - action: str ("start", "requested", "waiting", "acquired", "released",
                           "policy_applied", "warning", "deadlock_detected", "timeout", "complete")
            - resource: str or None ("A", "B", None)
            - owner: str or None ("T1", "T2", None)
            - wait_ms: int
        """
        self.history_length += 1
        action = event.get("action", "")
        thread = event.get("thread", "")
        resource = event.get("resource")
        owner = event.get("owner")
        wait_ms = int(event.get("wait_ms") or 0)
        timestamp = float(event.get("time") or 0.0)

        if thread and thread != "system":
            self.add_thread(thread)

        if action == "start":
            self.reset()

        elif action in ("acquired", "acquire"):
            if resource and thread and thread != "system":
                self.owners[resource] = thread
                # Thread now owns resource, so it is no longer waiting for it
                self.remove_dependency(thread, resource)

        elif action in ("released", "release"):
            if resource:
                releasing_thread = thread if thread != "system" else self.owners.get(resource)
                if releasing_thread:
                    self.remove_dependencies_for_holder(releasing_thread, resource)
                self.owners.pop(resource, None)

        elif action in ("waiting", "wait"):
            if resource and thread and thread != "system":
                # Check target owner
                target_holder = owner or self.owners.get(resource)
                if target_holder and target_holder != thread:
                    self.add_dependency(
                        waiter=thread,
                        holder=target_holder,
                        resource=resource,
                        wait_ms=wait_ms,
                        timestamp=timestamp,
                    )

        elif action == "deadlock_detected":
            # Confirmed cycle state: T1 waits for B held by T2; T2 waits for A held by T1
            self.owners["A"] = "T1"
            self.owners["B"] = "T2"
            self.add_dependency("T1", "T2", "B", wait_ms=wait_ms, timestamp=timestamp)
            self.add_dependency("T2", "T1", "A", wait_ms=wait_ms, timestamp=timestamp)

        elif action == "complete":
            self.reset()

        return self.get_snapshot()

    def find_cycles(self) -> List[List[str]]:
        """Detect all directed cycles in the Wait-For Graph using DFS.

        Returns:
            List of cycles where each cycle is a list of thread names,
            e.g. [['T1', 'T2', 'T1']].
        """
        cycles: List[List[str]] = []
        visited: Dict[str, int] = {node: 0 for node in self.nodes}  # 0=unvisited, 1=visiting, 2=visited
        path: List[str] = []

        def dfs(u: str) -> None:
            visited[u] = 1
            path.append(u)

            # Look at all outgoing edges from u (threads u is waiting for)
            for edge in self.adj.get(u, {}).values():
                v = edge.holder
                if v not in visited:
                    continue
                if visited[v] == 1:
                    # Found back-edge! Cycle detected from v to u to v
                    try:
                        idx = path.index(v)
                        cycle = path[idx:] + [v]
                        # Avoid duplicate cycle rotations
                        canonical = min(cycle[:-1])
                        c_idx = cycle.index(canonical)
                        normalized = cycle[c_idx:-1] + cycle[:c_idx] + [canonical]
                        if normalized not in cycles:
                            cycles.append(normalized)
                    except ValueError:
                        pass
                elif visited[v] == 0:
                    dfs(v)

            path.pop()
            visited[u] = 2

        for node in sorted(self.nodes):
            if visited[node] == 0:
                dfs(node)

        return cycles

    def has_cycle(self) -> bool:
        """Check if any directed cycle exists in the graph."""
        return len(self.find_cycles()) > 0

    def get_cycle_edges(self) -> List[Dict[str, Any]]:
        """Return the list of edges forming any detected cycles."""
        cycles = self.find_cycles()
        cycle_edges: List[Dict[str, Any]] = []
        seen = set()

        for cycle in cycles:
            for i in range(len(cycle) - 1):
                u, v = cycle[i], cycle[i + 1]
                edge_key = (u, v)
                if edge_key not in seen:
                    seen.add(edge_key)
                    # Find matching edge in adj
                    for edge in self.adj.get(u, {}).values():
                        if edge.holder == v:
                            cycle_edges.append(edge.to_dict())
                            break

        return cycle_edges

    def get_edges(self) -> List[Dict[str, Any]]:
        """Get all current directed edges in the graph."""
        edges = []
        for waiter in sorted(self.adj.keys()):
            for edge in self.adj[waiter].values():
                edges.append(edge.to_dict())
        return edges

    def get_snapshot(self) -> Dict[str, Any]:
        """Return a complete dictionary snapshot of the current Wait-For Graph."""
        cycles = self.find_cycles()
        has_deadlock = len(cycles) > 0
        return {
            "nodes": sorted(list(self.nodes)),
            "edges": self.get_edges(),
            "owners": dict(self.owners),
            "waits": dict(self.waits),
            "has_cycle": has_deadlock,
            "cycles": cycles,
            "cycle_edges": self.get_cycle_edges() if has_deadlock else [],
            "blocked_thread_count": len([w for w in self.waits.keys() if self.waits[w]]),
            "edge_count": sum(len(e) for e in self.adj.values()),
        }
