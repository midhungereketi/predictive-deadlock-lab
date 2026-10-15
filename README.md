# Predictive Deadlock Lab

Operating Systems case study: **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Current stage

- **Frontend (Member 1 — Midhun Gereketi):** Complete dashboard prototype located under [`frontend/`](frontend/). Open `frontend/index.html` for browser-based demo playback, Wait-For Graph, event timeline, threat score, contention heatmap, and side-by-side run comparisons.
- **Backend (Member 2 — P. Satya Mani Shraavanth):** Complete multithreaded experiment backend located under [`member2_backend/`](member2_backend/). Features controlled multithreaded vulnerable and protected trials, canonical lock ordering, barrier synchronization, bounded timeouts, thread-safe event logging, and FastAPI REST endpoints.
- **Analysis & Evaluation (Member 3 — M. Lakshman Sai):** Analysis modules consume the backend's shared event logs for Wait-For Graph evaluation, contention metrics, and forecasting.

## Quick Start & Running the Project

### 1. Install Backend Dependencies
```bash
pip install -r member2_backend/requirements.txt
```

### 2. Run Backend & Dashboard Server
```bash
python -m uvicorn member2_backend.api:app --reload --host 127.0.0.1 --port 8000
```
Open **http://127.0.0.1:8000/** in your browser. You can run the built-in demo or click **"⚡ Run live backend trial"** to execute real OS threads live on the backend!

### 3. Run Automated Tests
```bash
# Python Backend Tests (16 tests)
python -m pytest member2_backend/tests/ -v

# Frontend Contract Tests (4 tests)
node --test frontend/tests/trial-data.test.js
```

## Shared Integration Contracts
- Shared event schema: [`shared/event_schema.md`](shared/event_schema.md)
- Member 1 trial contract: [`frontend/contract/README.md`](frontend/contract/README.md)
- Member 2 backend docs: [`member2_backend/README.md`](member2_backend/README.md)

## Team

1. **Midhun Gereketi** — frontend, visualization UI, import path, and event contract.
2. **P. Satya Mani Shraavanth** — multithreaded experiment engine, repeatable deadlock baseline, canonical lock ordering, and REST API.
3. **M. Lakshman Sai** — contention analysis, scoring, graph detection, and comparative evaluation.

