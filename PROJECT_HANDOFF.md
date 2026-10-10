# Predictive Deadlock Lab — project handoff

**Status as of 10 October 2026**  
**Owner / first team member:** Midhun Gereketi  
**GitHub repository:** https://github.com/midhungereketi/predictive-deadlock-lab  
**Private website preview:** https://predictive-deadlock-lab.sandybeech4.chatgpt.site

## Read this first

This is an Operating Systems case study titled **Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting**. The source brief is `Os_CaseStudy.pdf` (10 pages). The team chose a website to visualize a controlled two-thread, two-resource experiment. Midhun's frontend work is complete. The website currently runs deterministic browser demonstrations and can replay validated JSON trials. **The real multithreaded experiment, analysis pipeline, and backend/API have not been built yet.**

The source brief calls for: a vulnerable baseline, a deliberate A/B opposite-order lock scenario, Wait-For Graph detection, a contention heatmap, threat scoring and forecasting, adaptive lock ordering, and evaluation. Implement those as actual OS-thread experiments and derived analysis rather than treating the browser animation as experimental evidence.

## Where everything is

The team repository has the frontend under `frontend/`:

| Path | Purpose |
| --- | --- |
| `frontend/index.html` | Dashboard structure and views |
| `frontend/styles.css` | Responsive styling |
| `frontend/app.js` | Demo playback, visualizations, import flow, CSV export |
| `frontend/trial-data.js` | Trial validation, normalization, graph and summary calculations |
| `frontend/contract/README.md` | Human-readable integration contract |
| `frontend/contract/trial-v1.schema.json` | Version 1 JSON Schema |
| `frontend/contract/vulnerable.example.json` | Valid deadlocking example |
| `frontend/contract/protected.example.json` | Valid protected example |
| `frontend/tests/trial-data.test.js` | Contract behavior checks |

The separate local website source checkout is `D:\College\SEM 5\Operating Systems\Project\deadlock-lab`; its `dist/` files correspond to the GitHub `frontend/` files. **Treat the GitHub repository as the team handoff source.** A change to GitHub does not automatically redeploy the website. The preview is owner-private, so collaborators may need access to view it; they can always run the frontend locally from GitHub.

## What Midhun has finished

- Created the private team GitHub repository and pushed the frontend. Invited GitHub user `Shraavanth`; the invitation was pending when last checked. The GitHub username for Lakshman has not been provided.
- Built a responsive static website with no npm dependencies or build step.
- Added vulnerable and protected demo playback: step, play, pause, reset, and switch scenario.
- Added live Wait-For Graph, event timeline, risk trend, contention heatmap, outcome metrics, run comparison, method explanation, and CSV export.
- Added JSON import with validation and replay. A future API client can pass a parsed trial to `window.DeadlockLab.loadTrial(trial)`.
- Published a private website preview at the link above.
- Added the versioned event contract, schema, examples, and four passing contract tests.

The in-browser scenarios are **illustrative data**. Their scores, durations, and outcomes must not be cited as measured results. Use backend-generated trials for evaluation.

## Trial JSON contract (version 1)

Produce **one JSON object per trial**. The first implementation supports only threads `T1` and `T2` and single-instance mutex resources `A` and `B`. See `frontend/contract/README.md`, the JSON Schema, and the two complete examples before generating output.

```json
{
  "schema_version": 1,
  "run_id": "trial-001",
  "mode": "vulnerable",
  "status": "deadlock",
  "events": [
    {
      "timestamp_ms": 0,
      "thread_id": "system",
      "action": "start",
      "owners": {},
      "waits": {},
      "risk_score": 0,
      "wait_duration_ms": 0,
      "contention_count": 0
    }
  ]
}
```

The snippet shows the shape, **not a complete valid trial**. Each event is a full state snapshot immediately after an action, with nondecreasing `timestamp_ms`. `owners` maps a held resource to its owning thread; `waits` maps a blocked thread to the resource it needs. Every wait must target a lock held by the other thread. `risk_score` is an integer from 0 to 100. `wait_duration_ms` is the longest wait observed so far and may remain nonzero after completion. `contention_count` is cumulative conflict intensity. Optional `resource_id`, `title`, and `detail` describe the action.

For a deadlock, the last action must be `deadlock_detected` and the final state must contain the two-thread Wait-For Graph cycle. For a successful protected run, the last action must be `complete`, with empty `owners` and `waits`. The UI's demo warning threshold is 70; crossing it signals risk, while a graph cycle confirms deadlock in this controlled model.

## Team order and next work

### 1. Midhun Gereketi — frontend and integration owner

Frontend and contract are ready. Review teammates' generated JSON against the contract, import representative trials into both modes, verify the visual story and comparison, and connect an API later if the team decides to run the backend through the website. Keep GitHub `frontend/` and the deployed site source synchronized when changing the UI.

### 2. P. Satya Mani Shraavanth — real-thread experiment

Build a repeatable command-line trial runner using real threads and mutexes (language choice is open). The vulnerable scenario should demonstrate opposite acquisition orders: `T1: A → B` and `T2: B → A`. Control interleaving enough to reproduce circular wait. The protected scenario should make both threads acquire resources in one common order **before either takes its first lock**. Emit precise timestamped ownership/wait events and the version 1 JSON trial output. Run deliberate deadlocks in an isolated process or with a supervisor timeout so an experiment cannot hang a web request or test suite. Document how to run both modes.

### 3. M. Lakshman Sai — detection, scoring, and evaluation

Consume the runner's events; build the Wait-For Graph from owners and waits and detect cycles. Calculate and document contention counts, wait duration, a 0–100 risk score, and a forecast/early-warning rule. Ensure scores use information available **at that timestamp**; do not calculate an early warning from future events. Produce data for heatmap and comparison through the same trial JSON. Run repeated vulnerable and protected trials, summarize deadlock frequency, warning lead time, waits, contention, and protected completion. Explain any limitations of a two-thread/two-resource experiment.

Shraavanth and Lakshman should agree on the event log and scoring semantics before coding separate modules. The existing JSON contract is the boundary the frontend already accepts.

## Recommended integration sequence

1. Clone the team repository and open `frontend/index.html` locally. Import both example JSON files to see the expected behavior.
2. Implement the CLI runner and produce one real vulnerable and one real protected JSON trial. Validate them with the schema and frontend importer.
3. Add graph detection, risk scoring, and repeated-trial evaluation. Keep raw measurements separate from the UI's demo values.
4. Import representative real outputs into the website and check graph edges, heatmap, warning timing, terminal state, comparison, and CSV export.
5. If live browser execution is needed, add an API/job layer that starts isolated trials and returns the **same JSON format**. The static website cannot execute native threads itself. Call `window.DeadlockLab.loadTrial(trial)` after fetching a completed trial.
6. Add reproducible run instructions and measured results to the repository before preparing the final presentation.

## Run and verify the current frontend

From the GitHub repository root, open `frontend/index.html` in a browser (or serve `frontend/` with a static HTTP server). No package installation is needed. If Node.js is available, run:

```sh
node --test frontend/tests/trial-data.test.js
```

All four tests passed at handoff: vulnerable warning precedes a cycle; protected example completes; invalid waiting/deadlock claims are rejected; timestamps must be ordered. Browser checks also covered both demos, imported vulnerable data, mixed-source comparison, mobile layout, and absence of JavaScript console errors.

## Definition of a finished project

The team can reproduce both real-thread modes from documented commands; deadlocked runs terminate safely; the analyzer detects an actual cycle and emits honest time-local risk scores; the website imports and explains real trial output; repeated trials support a measured comparison; and the README states setup, algorithms, metrics, and limitations. The existing frontend is a visualization and integration foundation, not the complete Operating Systems implementation.

