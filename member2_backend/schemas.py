"""Data models and schemas for Member 2's multithreaded experiment engine.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExperimentMode(str, Enum):
    VULNERABLE = "vulnerable"
    PROTECTED = "protected"


class ExperimentStatus(str, Enum):
    COMPLETED = "completed"
    DEADLOCK = "deadlock"
    TIMEOUT = "timeout"
    ERROR = "error"


class EventAction(str, Enum):
    START = "start"
    REQUESTED = "requested"
    WAITING = "waiting"
    ACQUIRED = "acquired"
    RELEASED = "released"
    POLICY_APPLIED = "policy_applied"
    WARNING = "warning"
    DEADLOCK_DETECTED = "deadlock_detected"
    TIMEOUT = "timeout"
    COMPLETE = "complete"


class Event(BaseModel):
    """Shared execution event schema (Member 1 / Member 2 / Member 3 contract).

    Fields:
        time: Timestamp relative to the start of the experiment in seconds.
        thread: Thread identifier ('T1', 'T2', or 'system').
        action: Recorded action ('start', 'requested', 'waiting', 'acquired', 'released', etc.).
        resource: Resource identifier ('A', 'B', or None).
        owner: Current owner of the resource ('T1', 'T2', or None).
        wait_ms: Duration in milliseconds thread waited for the resource (0 if none).
    """
    time: float = Field(..., description="Monotonic elapsed time in seconds from trial start")
    thread: str = Field(..., description="Thread identifier: 'T1', 'T2', or 'system'")
    action: str = Field(..., description="Action name conforming to documented event types")
    resource: Optional[str] = Field(None, description="Resource name: 'A', 'B', or None")
    owner: Optional[str] = Field(None, description="Resource owner at time of event: 'T1', 'T2', or None")
    wait_ms: int = Field(0, description="Observed wait duration in milliseconds")

    model_config = ConfigDict(frozen=True)


class ExperimentMetrics(BaseModel):
    """Execution timing, thread counts, and contention metrics."""
    threads_started: int = Field(2, description="Number of worker threads started")
    threads_completed: int = Field(0, description="Number of worker threads successfully completed")
    threads_timed_out: int = Field(0, description="Number of worker threads that timed out")
    peak_wait_ms: int = Field(0, description="Peak duration any thread spent waiting in milliseconds")
    contention_count: int = Field(0, description="Cumulative conflict/contention occurrences")
    lock_acquisitions: int = Field(0, description="Total number of successful lock acquisitions")
    lock_releases: int = Field(0, description="Total number of lock releases")
    deadlock_cycle: Optional[List[str]] = Field(None, description="Confirmed cycle nodes in Wait-For Graph")


class ExperimentResult(BaseModel):
    """Complete response contract for experiment invocation (Section 10)."""
    trial_id: str = Field(..., description="Unique trial identifier")
    mode: str = Field(..., description="Execution mode: 'vulnerable' or 'protected'")
    status: str = Field(..., description="Outcome: 'completed', 'deadlock', 'timeout', or 'error'")
    deadlock_detected: bool = Field(..., description="True if a circular wait was formed")
    completion_time_ms: int = Field(..., description="Total execution duration in milliseconds")
    events: List[Event] = Field(default_factory=list, description="Chronological execution event stream")
    metrics: ExperimentMetrics = Field(..., description="Aggregate execution metrics")
    error: Optional[str] = Field(None, description="Error message if run failed or timed out")


class RunExperimentRequest(BaseModel):
    """Request payload for running an experiment trial."""
    mode: ExperimentMode = Field(ExperimentMode.VULNERABLE, description="Experiment mode to run")
    timeout_seconds: float = Field(5.0, ge=0.5, le=30.0, description="Maximum execution timeout in seconds")
    trial_id: Optional[str] = Field(None, max_length=80, description="Optional custom trial identifier")


class MultiThreadExperimentRequest(BaseModel):
    """Request payload for a configurable multi-thread experiment."""
    mode: ExperimentMode = Field(ExperimentMode.VULNERABLE, description="Experiment mode to run")
    thread_count: int = Field(6, ge=3, le=12, description="Number of worker threads to simulate")
    timeout_seconds: float = Field(5.0, ge=0.5, le=30.0, description="Maximum execution timeout in seconds")
    trial_id: Optional[str] = Field(None, max_length=80, description="Optional custom trial identifier")


# --- Schemas for Member 1's trial-v1 JSON contract adapter ---

class TrialV1Event(BaseModel):
    """Single event snapshot matching frontend/contract/trial-v1.schema.json."""
    timestamp_ms: int = Field(..., ge=0, le=3600000)
    thread_id: str = Field(..., pattern="^(T1|T2|system)$")
    action: str = Field(..., pattern="^(start|request|acquire|wait|release|warning|policy_applied|deadlock_detected|complete)$")
    resource_id: Optional[str] = Field(None, pattern="^(A|B)$")
    owners: Dict[str, str] = Field(default_factory=dict)
    waits: Dict[str, str] = Field(default_factory=dict)
    risk_score: int = Field(0, ge=0, le=100)
    wait_duration_ms: int = Field(0, ge=0, le=3600000)
    contention_count: int = Field(0, ge=0, le=100000)
    title: Optional[str] = Field(None, max_length=120)
    detail: Optional[str] = Field(None, max_length=300)


class TrialV1Output(BaseModel):
    """Full trial output conforming exactly to Member 1's trial-v1.schema.json."""
    schema_version: Literal[1] = 1
    run_id: str = Field(..., min_length=1, max_length=80)
    mode: str = Field(..., pattern="^(vulnerable|protected)$")
    status: str = Field(..., pattern="^(deadlock|completed)$")
    events: List[TrialV1Event] = Field(..., min_length=1, max_length=500)
