# Predictive Deadlock Lab — frontend prototype

An interactive browser demonstration for the Operating Systems case study **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Run locally

Open `dist/index.html` in a browser, or serve `dist/` with any static HTTP server. No package installation or build step is required.

## What works

- Step, play, pause, reset, and switch between vulnerable and protected scenarios.
- Live Wait-For Graph, timeline, risk trend, contention heatmap, and metrics.
- Side-by-side outcome comparison and CSV export of demonstration events.
- Responsive desktop and mobile layouts.

The scenarios are deterministic **demo data generated in the browser**. This frontend does not yet run real threads or connect to the experiment backend.

## Backend handoff

The future backend should run real threads in isolated trials and stream events to this interface. A suggested event shape is:

```json
{
  "run_id": "trial-001",
  "mode": "vulnerable",
  "timestamp_ms": 600,
  "thread_id": "T1",
  "action": "wait",
  "resource_id": "B",
  "owner_thread_id": "T2",
  "wait_duration_ms": 200
}
```

Use actions `request`, `acquire`, `wait`, `release`, `warning`, `deadlock_detected`, and `complete`. Include a run summary with deadlock status, warning time, cycle detection time, completion time, and thread throughput. The UI's `app.js` currently contains snapshot arrays; replace those arrays with backend-derived state while retaining the render functions.

## Team sequence

1. **Midhun Gereketi:** frontend and event contract.
2. **P. Satya Mani Shraavanth:** real-thread experiment, repeatable baseline, protected lock order, and isolated trial runner.
3. **M. Lakshman Sai:** Wait-For Graph, contention metrics, scoring, heatmap, and comparison calculations.

## Important distinction

A risk threshold is an early warning, not proof of deadlock. A Wait-For Graph cycle confirms deadlock in the controlled two-thread, single-instance-lock scenario. Protected threads must choose the same lock order before acquiring their first lock.

