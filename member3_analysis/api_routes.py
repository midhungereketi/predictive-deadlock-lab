"""FastAPI router exposing Member 3 analytical endpoints.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting

Scoring weights are request-scoped. The server keeps no mutable scoring state:
every endpoint builds its own ThreatScorer from the weights sent with that
request (or the documented defaults), so one visitor's settings can never change
another visitor's results, and nothing depends on a serverless instance staying
alive between requests.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .comparator import ExperimentComparator, analyze_trial_events
from .threat_scorer import ThreatScoreConfig, ThreatScorer

router = APIRouter(prefix="/api/analysis", tags=["Role 3 Analysis & Forecasting"])

SCOPE_NOTE = (
    "Weights are applied per request and are never stored on the server. Send "
    "w_blocked, w_wait, w_contention, w_resource and threshold_high with each "
    "request (query parameters, or a 'scoring' object for /evaluate); omitted "
    "values use the defaults."
)


class ScoreConfigRequest(BaseModel):
    w_blocked: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_wait: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_contention: Optional[float] = Field(None, ge=0.0, le=1.0)
    w_resource: Optional[float] = Field(None, ge=0.0, le=1.0)
    threshold_high: Optional[int] = Field(None, ge=1, le=100)


class EvaluateEventsRequest(BaseModel):
    events: List[Dict[str, Any]]
    scoring: Optional[ScoreConfigRequest] = None


def build_scorer(overrides: Optional[ScoreConfigRequest] = None) -> ThreatScorer:
    """Create a fresh scorer for one request, rejecting invalid weights with 422."""
    values = overrides.model_dump() if overrides else {}
    try:
        return ThreatScorer.from_overrides(**values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def request_scorer(
    w_blocked: Optional[float] = Query(None, ge=0.0, le=1.0, description="Weight for blocked threads"),
    w_wait: Optional[float] = Query(None, ge=0.0, le=1.0, description="Weight for wait duration"),
    w_contention: Optional[float] = Query(None, ge=0.0, le=1.0, description="Weight for contention events"),
    w_resource: Optional[float] = Query(None, ge=0.0, le=1.0, description="Weight for lock conflict"),
    threshold_high: Optional[int] = Query(None, ge=1, le=100, description="Early-warning threshold"),
) -> ThreatScorer:
    """FastAPI dependency: the scorer for this request only."""
    return build_scorer(ScoreConfigRequest(
        w_blocked=w_blocked, w_wait=w_wait, w_contention=w_contention,
        w_resource=w_resource, threshold_high=threshold_high,
    ))


@router.get("/config", summary="Get the default threat scoring formula and weights")
def get_scoring_config() -> Dict[str, Any]:
    return {**ThreatScoreConfig().to_dict(), "scope": "request", "persisted": False, "usage": SCOPE_NOTE}


@router.put("/config", summary="Validate scoring weights (nothing is stored on the server)")
def validate_scoring_config(req: ScoreConfigRequest) -> Dict[str, Any]:
    scorer = build_scorer(req)
    return {
        "status": "validated",
        "scope": "request",
        "persisted": False,
        "config": scorer.config.to_dict(),
        "usage": SCOPE_NOTE,
    }


@router.post("/evaluate", summary="Run WFG, cycle detection, heatmap, and scoring on event stream")
def evaluate_stream(req: EvaluateEventsRequest) -> Dict[str, Any]:
    if not req.events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="events list cannot be empty.",
        )
    return analyze_trial_events(req.events, build_scorer(req.scoring))


@router.post("/compare", summary="Run repeated-trial empirical comparison between vulnerable and protected modes")
def run_batch_comparison(
    trials_per_mode: int = Query(5, ge=1, le=10, description="Number of trials per mode to run"),
    timeout: float = Query(3.0, ge=0.5, le=10.0, description="Per-trial execution timeout"),
    scorer: ThreatScorer = Depends(request_scorer),
) -> Dict[str, Any]:
    return ExperimentComparator(scorer).run_comparison(trials_per_mode=trials_per_mode, timeout_seconds=timeout)


@router.get("/compare", summary="Run repeated-trial empirical comparison via GET for quick testing")
def run_batch_comparison_get(
    trials_per_mode: int = Query(3, ge=1, le=10),
    timeout: float = Query(3.0, ge=0.5, le=10.0),
    scorer: ThreatScorer = Depends(request_scorer),
) -> Dict[str, Any]:
    return ExperimentComparator(scorer).run_comparison(trials_per_mode=trials_per_mode, timeout_seconds=timeout)
