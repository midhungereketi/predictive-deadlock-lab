# Predictive Deadlock Lab

Operating Systems case study: **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Current stage

- **Frontend (Member 1 — Midhun Gereketi):** Complete dashboard prototype located under [`frontend/`](frontend/). Open `frontend/index.html` for browser-based demo playback, Wait-For Graph, event timeline, threat score, contention heatmap, and side-by-side run comparisons.
- **Backend (Member 2 — P. Satya Mani Shraavanth):** Real-thread experiment engine under [`member2_backend/`](member2_backend/). It runs controlled vulnerable and protected trials with bounded lock waits and exposes local FastAPI endpoints. The protected run first observes a cycle-free contention probe and derives a shared lock order from it.
- **Analysis & Evaluation (Member 3 — M. Lakshman Sai):** Analysis code under [`member3_analysis/`](member3_analysis/). It builds a Wait-For Graph, detects cycles, scores observed contention, and compares repeated trials. The warning uses a documented structural heuristic for this controlled two-lock experiment.

**Hosted integrated app:** https://predictive-deadlock-lab.vercel.app/ (FastAPI and frontend). The live buttons also work with the local FastAPI server. A separately hosted static preview cannot execute the Python backend. Batch results appear in the batch table; the side-by-side cards show the currently loaded individual trials.

**Submission material:** [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) contains the design, algorithm, measured 10-trial-per-mode results, and limitations. [`docs/DEMO_AND_PRESENTATION.md`](docs/DEMO_AND_PRESENTATION.md) has the demo steps, slide sequence, and viva answers. [`docs/results.json`](docs/results.json) contains the raw aggregate and per-trial measurements. The two `docs/sample-*.json` files can be imported into the dashboard.

**Final submission files:** [`docs/submission/Final_Report.pdf`](docs/submission/Final_Report.pdf) is the printable report, and [`docs/submission/Presentation_Submission.pptx`](docs/submission/Presentation_Submission.pptx) is the editable eight-slide presentation. Both use the saved measurements in `docs/results.json`.

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

For a configurable larger run, select **3–12 worker threads** beside the live-run button and click **"⚡ Run multi-thread trial"**. Vulnerable mode synchronizes two workers into a real circular wait while the remaining workers contend for the same locks; protected mode makes all selected workers acquire locks in the same A → B order. The dashboard shows the resulting wait-for graph and per-worker states. These trials use two shared mutexes and are bounded to prevent workers from hanging indefinitely.

### 3. Run Automated Tests
```bash
# Python Backend & Analysis Tests
python -m pytest member2_backend/tests/ member3_analysis/tests/ -v

# Member 3 Focused Analysis Tests
python -m pytest member3_analysis/tests/ -v

# Frontend Contract Tests (4 tests)
node --test frontend/tests/trial-data.test.js

# Repeat and replace the saved empirical comparison (10 trials per mode)
python scripts/collect_results.py --trials 10
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
