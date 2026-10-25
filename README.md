# Predictive Deadlock Lab

Operating Systems case study: **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

**Live app:** https://predictive-deadlock-lab.vercel.app/ (FastAPI backend and dashboard)

## What it does

- **Two-thread experiment:** real threads deadlock over locks A and B (T1: A→B, T2: B→A). A Wait-For Graph confirms the cycle, and a weighted 0–100 risk score warns before it forms. Protected mode learns one global lock order from a cycle-free probe and always completes.
- **N-thread ring (2–32 threads):** thread *Ti* needs locks *Ri* and *Ri+1*. Vulnerable mode forms one cycle through all N threads; a supervisor detects it and recovers by aborting the highest-numbered thread. Protected mode takes the lower-numbered lock first and always completes.
- **Replay:** every run is animated from its real event log (lock tiles move, waits appear, the deadlock flashes, recovery unwinds), with step controls and a narrated caption.
- **Analysis view:** peak score, first warning, deadlock time, warning lead time, a full-run risk chart and a per-event factor breakdown. Weight sliders re-score the run instantly.
- **Compare view:** both modes side by side, repeated two-thread trials (deadlock/completion rates), and a scaling test with repeated trials per thread count (rates, mean ± sd, min–max). CSV export everywhere.

The warning is a documented heuristic evaluated in a controlled experiment; it is **not** a predictor of deadlocks in arbitrary programs.

## Scoring settings are per visitor

Weights and threshold are applied in your browser immediately. They are kept in memory until you press **Save in this browser** (stored in that browser's local storage only), and they are sent with each backend request you start (`/api/trials/{mode}` and `/api/analysis/compare` accept `w_blocked`, `w_wait`, `w_contention`, `w_resource`, `threshold_high`). The server stores nothing, so one visitor cannot change another's results. `PUT /api/analysis/config` only validates values. `frontend/scoring.js` and `member3_analysis/threat_scorer.py` implement the same formula and are both tested against `shared/scoring_cases.json`.

## Run locally

```bash
pip install -r member2_backend/requirements.txt
python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/.

## Tests

```bash
pip install -r requirements-dev.txt          # adds Playwright for the browser tests
python -m pytest member2_backend/tests member3_analysis/tests tests/e2e
node --test frontend/tests/trial-data.test.js frontend/tests/scoring.test.js
```

The browser tests (`tests/e2e`) start a real FastAPI server and drive an installed Chrome. To use Playwright's bundled Chromium instead, run `python -m playwright install chromium` and set `E2E_BROWSER_CHANNEL=` (empty).

## Measurements

| File | What it is |
| --- | --- |
| [`docs/results.json`](docs/results.json) | **Saved** two-thread set, 10 trials per mode, collected 15 Oct 2026 |
| [`docs/results_2026-10-26_two_thread.json`](docs/results_2026-10-26_two_thread.json) | **New** two-thread re-run, 10 trials per mode, collected 26 Oct 2026 |
| [`docs/results_2026-10-26_scaling.json`](docs/results_2026-10-26_scaling.json) | **New** N-thread scaling set: 2, 4, 8, 16, 32 threads × 10 trials × both modes, with every raw run |
| `docs/sample-*.json` | Real trials you can import into the dashboard |

Collect a new set without overwriting the saved one:

```bash
python scripts/collect_results.py --trials 10 --output docs/<new-file>.json --skip-samples
python scripts/collect_scaling_results.py --sizes 2 4 8 16 32 --trials 10 --output docs/<new-file>.json
```

## Submission material

- [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) and [`docs/submission/Final_Report.pdf`](docs/submission/Final_Report.pdf): architecture, algorithms, workflow, evaluation protocol, results, limitations, literature review, team roles.
- [`docs/submission/Presentation_Submission.pptx`](docs/submission/Presentation_Submission.pptx): editable slides.
- [`docs/DEMO_AND_PRESENTATION.md`](docs/DEMO_AND_PRESENTATION.md): demo script and viva answers.
- Build scripts: `scripts/build_submission_pdf.py` and `scripts/build_submission_slides.py`.

## Project layout

- `frontend/`: dashboard, replay, Analysis and Compare views, `scoring.js`
- `member2_backend/`: threaded experiments, lock manager, N-thread ring, FastAPI app
- `member3_analysis/`: Wait-For Graph, risk score, trend, heatmap, comparison, analysis API
- `shared/`: event schema and shared scoring cases
- `tests/e2e/`: browser-level tests
- `scripts/`: measurement collection and document builders

## Team

1. **Midhun Gereketi**: frontend, replay and visualisation, Analysis/Compare views, integration and deployment.
2. **P. Satya Mani Shraavanth**: multithreaded experiments, lock ordering, N-thread ring and recovery, REST API.
3. **M. Lakshman Sai**: Wait-For Graph, risk scoring, contention analysis and comparative evaluation.
