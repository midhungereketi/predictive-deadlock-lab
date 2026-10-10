# Predictive Deadlock Lab — frontend prototype

An interactive browser demonstration for the Operating Systems case study **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Run locally

Open `dist/index.html` in a browser, or serve `dist/` with any static HTTP server. No package installation or build step is required.

## What works

- Step, play, pause, reset, and switch between vulnerable and protected scenarios.
- Live Wait-For Graph, timeline, risk trend, contention heatmap, and metrics.
- Import validated trial JSON, replay its events, and restore the built-in demo.
- Side-by-side outcome comparison and CSV export derived from current trial data.
- Responsive desktop and mobile layouts.

The built-in scenarios are deterministic **demo data generated in the browser**. Imported trial JSON can display backend results, but this frontend does not itself run real threads or call a backend API yet.

## Backend handoff

The future backend should run real threads in isolated trials and produce one versioned JSON file per trial. The frontend now has a validated importer, so the team can connect backend results without replacing the dashboard components. See [the trial contract](contract/README.md), [schema](contract/trial-v1.schema.json), and two example files.

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

The shortened snippet shows one event; a valid file needs a terminal event and consistent states. The backend can write JSON and users can import it, or a future API client can fetch the same object and call `window.DeadlockLab.loadTrial(trial)`. The UI derives graph edges and comparison metrics from imported snapshots.

Run the contract checks with:

```sh
node --test tests/trial-data.test.js
```

## Team sequence

1. **Midhun Gereketi:** frontend and event contract.
2. **P. Satya Mani Shraavanth:** real-thread experiment, repeatable baseline, protected lock order, and isolated trial runner.
3. **M. Lakshman Sai:** Wait-For Graph, contention metrics, scoring, heatmap, and comparison calculations.

## Important distinction

A risk threshold is an early warning, not proof of deadlock. A Wait-For Graph cycle confirms deadlock in the controlled two-thread, single-instance-lock scenario. Protected threads must choose the same lock order before acquiring their first lock.

