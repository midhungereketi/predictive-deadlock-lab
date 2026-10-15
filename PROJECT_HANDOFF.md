# Predictive Deadlock Lab - current team handoff

**Team:** Midhun Gereketi (frontend/integration), P. Satya Mani Shraavanth (threaded backend), M. Lakshman Sai (analysis/evaluation)

**GitHub:** https://github.com/midhungereketi/predictive-deadlock-lab

**Local live application:** `http://127.0.0.1:8000/` after starting FastAPI

The integrated project contains the dashboard, real threaded vulnerable/protected experiments, Wait-For Graph cycle detector, contention heatmap, score/trend analysis, adaptive ordering from a cycle-free probe, batch comparison, tests, and measured evaluation data. Read the root `README.md` for setup, `ARCHITECTURE.md` for module flow, `docs/FINAL_REPORT.md` for methods/results/limitations, and `docs/DEMO_AND_PRESENTATION.md` for the live demonstration.

## To run

```text
pip install -r member2_backend/requirements.txt
python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The live buttons call local FastAPI. The separately hosted static preview has no Python backend; use it for built-in playback or import a saved `docs/sample-*.json` trial. Do not cite built-in browser demo values as measured evidence.

## To verify and reproduce results

```text
python -m pytest member2_backend/tests member3_analysis/tests -q
node --test frontend/tests/trial-data.test.js
python scripts/collect_results.py --trials 10
```

The collection script replaces `docs/results.json` and both sample trial files with a new measurement set. Timing varies by computer. Explain the controlled 120 ms vulnerable observation interval and the protected probe when presenting. The scorer's early warning is a risk heuristic; a WFG cycle is the deadlock proof. The protected policy is learned before main-worker acquisition and is not a general runtime repair mechanism for already held locks.
