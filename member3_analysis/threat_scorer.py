"""Threat Scoring Engine for Predictive Deadlock Lab.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ThreatScoreConfig:
    """Configurable weights and saturation parameters for the threat score formula.

    Formula:
        ThreatScore = w_b * B_norm + w_w * W_norm + w_c * C_norm + w_r * R_norm

    Weights sum to 1.00 (100%).
    """
    w_blocked: float = 0.35       # Weight for blocked threads ratio
    w_wait: float = 0.30          # Weight for wait duration
    w_contention: float = 0.20    # Weight for contention frequency
    w_resource: float = 0.15      # Weight for resource conflict & criticality

    # Normalization ceilings
    max_threads: int = 2          # Total worker threads in case study
    max_wait_ms: int = 800        # Wait duration saturation threshold (ms)
    max_contention: int = 5       # Contention count saturation ceiling

    # Risk thresholds
    threshold_low: int = 40       # Score < 40 is LOW RISK
    threshold_high: int = 70      # Score >= 70 is HIGH RISK / EARLY WARNING

    # Resource criticality weights (documented limitation: homogeneous locks in case study)
    criticality: Dict[str, float] = field(default_factory=lambda: {"A": 1.0, "B": 1.0})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": {
                "blocked": self.w_blocked,
                "wait": self.w_wait,
                "contention": self.w_contention,
                "resource": self.w_resource,
            },
            "parameters": {
                "max_threads": self.max_threads,
                "max_wait_ms": self.max_wait_ms,
                "max_contention": self.max_contention,
            },
            "thresholds": {
                "low": self.threshold_low,
                "high": self.threshold_high,
            },
            "criticality": dict(self.criticality),
            "formula_documentation": (
                "ThreatScore = round(w_b * B_norm + w_w * W_norm + w_c * C_norm + w_r * R_norm)\n"
                "Where:\n"
                "  B_norm = min(100, (num_blocked / max_threads) * 100)\n"
                "  W_norm = min(100, (wait_duration_ms / max_wait_ms) * 100)\n"
                "  C_norm = min(100, (contention_count / max_contention) * 100)\n"
                "  R_norm = min(100, (active_criticality / total_criticality) * 100)\n"
                "Risk Classification:\n"
                "  0 - 39: LOW RISK (Calm, normal concurrency)\n"
                "  40 - 69: ELEVATED RISK (Moderate contention observed)\n"
                "  70 - 100: HIGH RISK (Early warning triggered before circular wait)"
            ),
        }


@dataclass
class ThreatScoreResult:
    """Detailed calculation result including the composite score and factor breakdowns."""
    score: int
    risk_level: str  # "LOW", "ELEVATED", "HIGH", "CRITICAL_DEADLOCK"
    is_early_warning: bool
    is_cycle_detected: bool

    # Factor contributions (0 to 100 scale for each factor)
    b_norm: float
    w_norm: float
    c_norm: float
    r_norm: float

    # Weighted contribution points
    points_blocked: float
    points_wait: float
    points_contention: float
    points_resource: float

    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "risk_level": self.risk_level,
            "is_early_warning": self.is_early_warning,
            "is_cycle_detected": self.is_cycle_detected,
            "factors": {
                "blocked_threads_norm": round(self.b_norm, 1),
                "wait_duration_norm": round(self.w_norm, 1),
                "contention_count_norm": round(self.c_norm, 1),
                "resource_conflict_norm": round(self.r_norm, 1),
            },
            "contributions": {
                "blocked_threads": round(self.points_blocked, 1),
                "wait_duration": round(self.points_wait, 1),
                "contention": round(self.points_contention, 1),
                "resource_conflict": round(self.points_resource, 1),
            },
            "explanation": self.explanation,
        }


class ThreatScorer:
    """Computes a transparent, configurable threat score from system contention observables."""

    def __init__(self, config: Optional[ThreatScoreConfig] = None) -> None:
        self.config = config or ThreatScoreConfig()

    def update_config(
        self,
        w_blocked: Optional[float] = None,
        w_wait: Optional[float] = None,
        w_contention: Optional[float] = None,
        w_resource: Optional[float] = None,
        threshold_high: Optional[int] = None,
        threshold_low: Optional[int] = None,
        max_wait_ms: Optional[int] = None,
    ) -> None:
        """Update scoring configuration weights and thresholds."""
        if w_blocked is not None:
            self.config.w_blocked = max(0.0, float(w_blocked))
        if w_wait is not None:
            self.config.w_wait = max(0.0, float(w_wait))
        if w_contention is not None:
            self.config.w_contention = max(0.0, float(w_contention))
        if w_resource is not None:
            self.config.w_resource = max(0.0, float(w_resource))
        if threshold_high is not None:
            self.config.threshold_high = max(1, min(100, int(threshold_high)))
        if threshold_low is not None:
            self.config.threshold_low = max(0, min(self.config.threshold_high - 1, int(threshold_low)))
        if max_wait_ms is not None:
            self.config.max_wait_ms = max(50, int(max_wait_ms))

    def evaluate(
        self,
        num_blocked: int = 0,
        wait_duration_ms: int = 0,
        contention_count: int = 0,
        owners: Optional[Dict[str, str]] = None,
        waits: Optional[Dict[str, str]] = None,
        has_cycle: bool = False,
    ) -> ThreatScoreResult:
        """Calculate threat score from observed contention parameters.

        Handles zero values, missing inputs, and division-by-zero safely.
        Strictly distinguishes confirmed cycle deadlock from heuristic score.
        """
        owners = owners or {}
        waits = waits or {}

        # 1. Blocked threads ratio (0 to 100)
        blocked_count = max(0, num_blocked or len(waits))
        max_threads = max(1, self.config.max_threads)
        b_norm = min(100.0, (blocked_count / max_threads) * 100.0)

        # 2. Normalized waiting duration (0 to 100)
        wait_ms = max(0, int(wait_duration_ms))
        max_wait = max(1, self.config.max_wait_ms)
        w_norm = min(100.0, (wait_ms / max_wait) * 100.0)

        # 3. Normalized contention frequency (0 to 100)
        c_count = max(0, int(contention_count))
        max_cont = max(1, self.config.max_contention)
        c_norm = min(100.0, (c_count / max_cont) * 100.0)

        # 4. Resource conflict & criticality factor (0 to 100)
        # In our case study, resources A and B have neutral criticality (weight 1.0 each).
        # When both A and B are simultaneously held by distinct competing threads,
        # lock-inversion risk is maximized.
        held_distinct = len(set(owners.values())) if owners else 0
        held_locks = len(owners)
        if held_locks >= 2 and held_distinct >= 2:
            r_norm = 100.0
        elif held_locks >= 2:
            r_norm = 40.0
        elif held_locks == 1:
            r_norm = 20.0
        else:
            r_norm = 0.0

        # Weighted sum
        pts_blocked = self.config.w_blocked * b_norm
        pts_wait = self.config.w_wait * w_norm
        pts_contention = self.config.w_contention * c_norm
        pts_resource = self.config.w_resource * r_norm

        raw_sum = pts_blocked + pts_wait + pts_contention + pts_resource
        score = int(round(max(0.0, min(100.0, raw_sum))))

        # Determine risk classification
        is_early_warning = score >= self.config.threshold_high and not has_cycle

        if has_cycle:
            risk_level = "CRITICAL_DEADLOCK"
            explanation = "Deadlock confirmed: Circular wait detected in Wait-For Graph."
            # Ensure deadlock displays high score while maintaining distinction
            score = max(score, 96)
        elif score >= self.config.threshold_high:
            risk_level = "HIGH"
            explanation = f"High contention early warning: Threat score ({score}) crossed threshold ({self.config.threshold_high})."
        elif score >= self.config.threshold_low:
            risk_level = "ELEVATED"
            explanation = f"Elevated contention: Active resource requests or blocking detected (score {score})."
        else:
            risk_level = "LOW"
            explanation = f"Normal concurrency: Low contention risk (score {score})."

        return ThreatScoreResult(
            score=score,
            risk_level=risk_level,
            is_early_warning=is_early_warning,
            is_cycle_detected=has_cycle,
            b_norm=b_norm,
            w_norm=w_norm,
            c_norm=c_norm,
            r_norm=r_norm,
            points_blocked=pts_blocked,
            points_wait=pts_wait,
            points_contention=pts_contention,
            points_resource=pts_resource,
            explanation=explanation,
        )
