# Predictive Deadlock Lab

Operating Systems case study: **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**.

## Current stage

Midhun's [frontend](frontend/) is complete for the two-thread, two-resource case study scenario. Open `frontend/index.html` to run the built-in demonstration, inspect the Wait-For Graph, event timeline, threat score, contention heatmap, and compare vulnerable and protected outcomes.

The UI can also **import a validated trial JSON file** and replay results from the future backend. See the [frontend handoff](frontend/README.md), [trial contract](frontend/contract/README.md), [schema](frontend/contract/trial-v1.schema.json), and [sample files](frontend/contract/). Run the contract checks with `node --test frontend/tests/trial-data.test.js`.

The browser demo does not run real threads. The backend team should produce trials in the versioned JSON format; the frontend will display them without redesigning the dashboard.

## Team

1. Midhun Gereketi — frontend, visualization UI, import path, and event contract.
2. P. Satya Mani Shraavanth — multithreaded experiment and safe lock ordering.
3. M. Lakshman Sai — contention analysis, scoring, graph detection, and results.
