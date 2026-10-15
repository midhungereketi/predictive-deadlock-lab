"""FastAPI backend server for running multithreaded experiments and serving the dashboard.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import os
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import API_HOST, API_PORT, DEFAULT_OVERALL_TIMEOUT_SECONDS
from .experiment_runner import run_experiment, to_trial_v1
from .schemas import ExperimentResult, RunExperimentRequest

app = FastAPI(
    title="Predictive Deadlock Lab — Experiment Backend",
    description="Multithreaded trial execution engine for Operating Systems case study.",
    version="1.0.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", summary="Health check endpoint")
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "member2_backend",
        "author": "P. Satya Mani Shraavanth (Member 2)",
        "version": "1.0.0",
    }


@app.post(
    "/api/experiments/vulnerable",
    response_model=ExperimentResult,
    summary="Run vulnerable deadlock experiment",
)
def run_vulnerable_trial(
    timeout: float = Query(DEFAULT_OVERALL_TIMEOUT_SECONDS, ge=0.5, le=30.0),
) -> ExperimentResult:
    result = run_experiment(mode="vulnerable", timeout_seconds=timeout)
    return result


@app.post(
    "/api/experiments/protected",
    response_model=ExperimentResult,
    summary="Run protected lock-ordering experiment",
)
def run_protected_trial(
    timeout: float = Query(DEFAULT_OVERALL_TIMEOUT_SECONDS, ge=0.5, le=30.0),
) -> ExperimentResult:
    result = run_experiment(mode="protected", timeout_seconds=timeout)
    return result


@app.post(
    "/api/experiments/run",
    response_model=ExperimentResult,
    summary="Run parameterized experiment (vulnerable or protected)",
)
def run_custom_experiment(request: RunExperimentRequest) -> ExperimentResult:
    result = run_experiment(
        mode=request.mode.value,
        timeout_seconds=request.timeout_seconds,
        trial_id=request.trial_id,
    )
    if result.status == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Experiment failed.",
        )
    return result


@app.post(
    "/api/trials/{mode}",
    summary="Run experiment and return Member 1 trial-v1 JSON format",
)
def run_trial_v1_post(
    mode: str,
    timeout: float = Query(DEFAULT_OVERALL_TIMEOUT_SECONDS, ge=0.5, le=30.0),
) -> Dict[str, Any]:
    if mode not in ("vulnerable", "protected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{mode}'. Use 'vulnerable' or 'protected'.",
        )
    result = run_experiment(mode=mode, timeout_seconds=timeout)
    return to_trial_v1(result)


@app.get(
    "/api/trials/{mode}",
    summary="Execute experiment and fetch Member 1 trial-v1 JSON directly",
)
def run_trial_v1_get(
    mode: str,
    timeout: float = Query(DEFAULT_OVERALL_TIMEOUT_SECONDS, ge=0.5, le=30.0),
) -> Dict[str, Any]:
    if mode not in ("vulnerable", "protected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{mode}'. Use 'vulnerable' or 'protected'.",
        )
    result = run_experiment(mode=mode, timeout_seconds=timeout)
    return to_trial_v1(result)


# Mount frontend static files if available
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    print(f"Starting Predictive Deadlock Lab server on http://{API_HOST}:{API_PORT}")
    uvicorn.run("member2_backend.api:app", host=API_HOST, port=API_PORT, reload=True)
