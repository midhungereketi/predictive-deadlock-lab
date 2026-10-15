# Predictive Deadlock Lab

Operating Systems case study: **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Current stage

- **Frontend (Member 1 — Midhun Gereketi):** Complete dashboard prototype located under [`frontend/`](frontend/). Open `frontend/index.html` for browser-based demo playback, Wait-For Graph, event timeline, threat score, contention heatmap, and side-by-side run comparisons.
- **Backend (Member 2 — P. Satya Mani Shraavanth):** Real-thread experiment engine under [`member2_backend/`](member2_backend/). It runs controlled vulnerable and protected trials with bounded lock waits and exposes local FastAPI endpoints.
- **Analysis & Evaluation (Member 3 — M. Lakshman Sai):** Analysis code under [`member3_analysis/`](member3_analysis/). It builds a Wait-For Graph, detects cycles, scores observed contention, and compares repeated trials. The warning uses a documented structural heuristic for this controlled two-lock experiment.

The live buttons require the local FastAPI server. The separately hosted static website cannot execute the Python backend. Batch results appear in the batch table; the side-by-side cards show the currently loaded individual trials.

## Quick Start & Running the Project

### 1. Install Backend Dependencies
```bash
pip install -r member2_backend/requirements.txt
```

### 2. Run Backend & Dashboard Server
```bash
python -m uvicorn member2_backend.api:app --reload --host 127.0.0.1 --port 8000
```
Open **http://127.0.0.1:8000/** in your browser. You can run the built-in demo, click **"⚡ Run live backend trial"** to execute real OS threads, or click **"⚡ Run Batch Trials (5 Each)"** in the Compare tab for empirical statistical evaluation!

### 3. Run Automated Tests
```bash
# Python Backend & Analysis Tests
python -m pytest member2_backend/tests/ member3_analysis/tests/ -v

# Member 3 Focused Analysis Tests
python -m pytest member3_analysis/tests/ -v

# Frontend Contract Tests (4 tests)
node --test frontend/tests/trial-data.test.js
```

## Shared Integration Contracts
- Shared event schema: [`shared/event_schema.md`](shared/event_schema.md)
- Member 1 trial contract: [`frontend/contract/README.md`](frontend/contract/README.md)
- Member 2 backend docs: [`member2_backend/README.md`](member2_backend/README.md)
- Member 3 analysis docs: [`member3_analysis/README.md`](member3_analysis/README.md)

## Team

1. **Midhun Gereketi** — frontend, visualization UI, import path, and event contract.
2. **P. Satya Mani Shraavanth** — multithreaded experiment engine, repeatable deadlock baseline, canonical lock ordering, and REST API.
3. **M. Lakshman Sai** — contention analysis, scoring, graph detection, and comparative evaluation.

