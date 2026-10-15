"""FastAPI router exposing Member 3 analytical endpoints.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from .comparator import ExperimentComparator, analyze_trial_events
from .threat_scorer import ThreatScoreConfig, ThreatScorer

router = APIRouter(prefix="/api/analysis", tags=["Role 3 Analysis & Forecasting"])

# Shared singleton scorer instance for runtime configuration
shared_scorer = ThreatScorer()
comparator = ExperimentComparator(shared_scorer)


class ScoreConfigRequest(BaseModel):
    w_blocked: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_wait: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_contention: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_resource: Optional[float] = Field(None, ge=0.0, le=1.0)
    threshold_high: Optional[int] = Field(None, ge=1, le=100)
    threshold_low: Optional[int] = Field(None, ge=0, le=99)
    max_wait_ms: Optional[int] = Field(None, ge=50, le=5000)


class EvaluateEventsRequest(BaseModel):
    events: List[Dict[str, Any]]


@router.get("/config", summary="Get threat scoring formula and weights")
def get_scoring_config() -> Dict[str, Any]:
    return shared_scorer.config.to_dict()


@router.put("/config", summary="Update threat scoring weights and thresholds")
def update_scoring_config(req: ScoreConfigRequest) -> Dict[str, Any]:
    shared_scorer.update_config(
        w_blocked=req.w_blocked,
        w_wait=req.w_wait,
        w_contention=req.w_contention,
        w_resource=req.w_resource,
        threshold_high=req.threshold_high,
        threshold_low=req.threshold_low,
        max_wait_ms=req.max_wait_ms,
    )
    return {
        "status": "updated",
        "config": shared_scorer.config.to_dict(),
    }


@router.post("/evaluate", summary="Run WFG, cycle detection, heatmap, and scoring on event stream")
def evaluate_stream(req: EvaluateEventsRequest) -> Dict[str, Any]:
    if not req.events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="events list cannot be empty.",
        )
    return analyze_trial_events(req.events, shared_scorer)


@router.post("/compare", summary="Run repeated-trial empirical comparison between vulnerable and protected modes")
def run_batch_comparison(
    trials_per_mode: int = Query(5, ge=1, le=10, description="Number of trials per mode to run"),
    timeout: float = Query(3.0, ge=0.5, le=10.0, description="Per-trial execution timeout"),
) -> Dict[str, Any]:
    return comparator.run_comparison(trials_per_mode=trials_per_mode, timeout_seconds=timeout)


@router.get("/compare", summary="Run repeated-trial empirical comparison via GET for quick testing")
def run_batch_comparison_get(
    trials_per_mode: int = Query(3, ge=1, le=10),
    timeout: float = Query(3.0, ge=0.5, le=10.0),
) -> Dict[str, Any]:
    return comparator.run_comparison(trials_per_mode=trials_per_mode, timeout_seconds=timeout)
