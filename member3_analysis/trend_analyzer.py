"""Time-Series Tracking, Trend Analysis, and Early Warning Engine.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ScoreObservation:
    """A timestamped score sample within an experimental run."""
    timestamp_ms: int
    score: int
    num_blocked: int
    has_cycle: bool


class ThreatTrendAnalyzer:
    """Performs time-series slope calculation, trajectory classification,

    and early warning detection over an experiment's score history.
    """

    def __init__(self, warning_threshold: int = 70, min_observations_for_trend: int = 2) -> None:
        self.warning_threshold = warning_threshold
        self.min_observations = min_observations_for_trend
        self.observations: List[ScoreObservation] = []
        self.first_warning_ms: Optional[int] = None
        self.deadlock_ms: Optional[int] = None

    def reset(self) -> None:
        """Reset state cleanly between experimental runs to avoid cross-trial contamination."""
        self.observations.clear()
        self.first_warning_ms = None
        self.deadlock_ms = None

    def record_sample(
        self,
        timestamp_ms: int,
        score: int,
        num_blocked: int = 0,
        has_cycle: bool = False,
    ) -> Dict[str, Any]:
        """Record a new observation and return current trend metrics."""
        obs = ScoreObservation(
            timestamp_ms=max(0, int(timestamp_ms)),
            score=max(0, min(100, int(score))),
            num_blocked=max(0, int(num_blocked)),
            has_cycle=bool(has_cycle),
        )
        self.observations.append(obs)

        # Detect early warning occurrence
        if obs.score >= self.warning_threshold and not obs.has_cycle:
            if self.first_warning_ms is None:
                self.first_warning_ms = obs.timestamp_ms

        # Detect confirmed deadlock
        if obs.has_cycle and self.deadlock_ms is None:
            self.deadlock_ms = obs.timestamp_ms

        return self.get_trend_status()

    def get_trend_status(self) -> Dict[str, Any]:
        """Calculate the current trajectory (RISING, STABLE, FALLING, INSUFFICIENT_DATA).

        Uses linear regression / moving difference over the last N observations.
        """
        n = len(self.observations)
        if n < self.min_observations:
            return {
                "trajectory": "INSUFFICIENT_DATA",
                "trajectory_symbol": "◌",
                "slope": 0.0,
                "observation_count": n,
                "current_score": self.observations[-1].score if n > 0 else 0,
                "peak_score": max((o.score for o in self.observations), default=0),
                "is_early_warning_active": False,
                "warning_lead_time_ms": None,
                "explanation": "Insufficient observations to compute score trajectory reliably.",
            }

        # Calculate slope over the recent window (up to last 5 observations)
        window = self.observations[-5:] if n >= 5 else self.observations
        t0 = window[0].timestamp_ms
        t1 = window[-1].timestamp_ms
        s0 = window[0].score
        s1 = window[-1].score

        dt = t1 - t0
        ds = s1 - s0

        # Rate of score change per 100ms
        slope_per_100ms = (ds / (dt / 100.0)) if dt > 0 else float(ds)

        # Thresholds for slope:
        # > +3.0 points per 100ms: RISING
        # < -3.0 points per 100ms: FALLING
        # Between -3.0 and +3.0: STABLE
        if slope_per_100ms > 3.0:
            trajectory = "RISING"
            symbol = "↗"
            expl = f"Threat score is increasing at +{slope_per_100ms:.1f} pts/100ms."
        elif slope_per_100ms < -3.0:
            trajectory = "FALLING"
            symbol = "↘"
            expl = f"Threat score is declining at {slope_per_100ms:.1f} pts/100ms."
        else:
            trajectory = "STABLE"
            symbol = "→"
            expl = "Threat score has stabilized."

        current_score = self.observations[-1].score
        peak_score = max(o.score for o in self.observations)
        last_has_cycle = self.observations[-1].has_cycle

        is_warning_active = current_score >= self.warning_threshold and not last_has_cycle

        # Calculate warning lead time if deadlock was reached
        lead_time_ms = None
        if self.deadlock_ms is not None and self.first_warning_ms is not None:
            lead_time_ms = max(0, self.deadlock_ms - self.first_warning_ms)

        return {
            "trajectory": trajectory,
            "trajectory_symbol": symbol,
            "slope_per_100ms": round(slope_per_100ms, 2),
            "observation_count": n,
            "current_score": current_score,
            "peak_score": peak_score,
            "is_early_warning_active": is_warning_active,
            "first_warning_ms": self.first_warning_ms,
            "deadlock_ms": self.deadlock_ms,
            "warning_lead_time_ms": lead_time_ms,
            "explanation": expl,
        }

    def get_time_series(self) -> List[Dict[str, Any]]:
        """Return array of timestamped points for visualization."""
        return [
            {
                "timestamp_ms": obs.timestamp_ms,
                "score": obs.score,
                "blocked": obs.num_blocked,
                "has_cycle": obs.has_cycle,
            }
            for obs in self.observations
        ]
