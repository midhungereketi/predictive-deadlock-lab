# Predictive Deadlock Lab — frontend prototype

An interactive browser demonstration for the Operating Systems case study **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Run locally

Open `index.html` in a browser, or serve this `frontend/` directory with any static HTTP server. No package installation or build step is required for demo playback or JSON import. To run real trials, start the repository's FastAPI server as described in the root README or visit the integrated hosted app at https://predictive-deadlock-lab.vercel.app/.

## What works

- Step, play, pause, reset, and switch between vulnerable and protected scenarios.
- Live Wait-For Graph, timeline, risk trend, contention heatmap, and metrics.
- Configurable 3–12 real-worker backend experiments with a multi-node Wait-For Graph and per-worker states.
- Import validated trial JSON, replay its events, and restore the built-in demo.
- Side-by-side outcome comparison and CSV export derived from current trial data.
- Responsive desktop and mobile layouts.

The built-in scenarios are deterministic **demo data generated in the browser**. The frontend can import trial JSON or call FastAPI using **Run live backend trial** or the configurable **Run multi-thread trial**. The browser itself does not run OS threads. The separately hosted static preview has no Python backend.

## Backend handoff

The backend runs bounded real-thread trials and returns versioned JSON through `/api/trials/{mode}`. The importer still accepts saved files. See [the trial contract](contract/README.md), [schema](contract/trial-v1.schema.json), and two example files. The current runner bounds lock waits within one Python process; it does not isolate each trial in a separate OS process.

```json
{
  "schema_version": 1,
  "run_id": "trial-001",
  "mode": "vulnerable",
  "status": "deadlock",
  "events": [
    {
      "timestamp_ms": 600,
      "thread_id": "T1",
      "action": "wait",
      "resource_id": "B",
      "owners": { "A": "T1", "B": "T2" },
      "waits": { "T1": "B" },
      "risk_score": 72,
      "wait_duration_ms": 200,
      "contention_count": 2
    }
  ]
}
```

The shortened snippet shows one event; a valid file needs a terminal event and consistent states. The backend returns this format through the local or hosted API; users can also import saved JSON. The UI derives graph edges and comparison metrics from recorded snapshots.

The larger simulation uses `POST /api/experiments/multi-thread` with JSON such as `{"mode":"vulnerable","thread_count":6,"timeout_seconds":5}`. This endpoint accepts 3–12 workers and returns the raw experiment response; its visualizer is separate from the two-thread trial-v1 importer. Both modes use shared locks A and B. Vulnerable mode demonstrates a cycle among two synchronized workers while other workers contend; protected mode serializes acquisitions with a global A → B lock order.

Run the contract checks with:

```sh
node --test tests/trial-data.test.js
```

## Team sequence

1. **Midhun Gereketi:** frontend and event contract.
2. **P. Satya Mani Shraavanth:** real-thread experiment, repeatable baseline, protected lock order, and bounded trial runner.
3. **M. Lakshman Sai:** Wait-For Graph, contention metrics, scoring, heatmap, and comparison calculations.

## Important distinction

A risk threshold is an early warning, not proof of deadlock. A Wait-For Graph cycle confirms deadlock in the controlled two-thread, single-instance-lock scenario. Protected threads must choose the same lock order before acquiring their first lock.
