# Trial JSON contract — version 1

The frontend accepts one JSON file per trial through **Import trial JSON**. The backend may also pass a parsed object directly to `window.DeadlockLab.loadTrial(trial)` after fetching it. This lets the multithreading and analysis modules work independently of the UI.

Use [the JSON Schema](trial-v1.schema.json) and the [vulnerable](vulnerable.example.json) and [protected](protected.example.json) examples.

## Meaning of each event

Each entry is a **full state snapshot immediately after an action**, ordered by `timestamp_ms`. The first should be a `start` event at 0 ms. Every event must include:

| Field | Meaning |
| --- | --- |
| `thread_id`, `action`, `resource_id` | The action that produced this snapshot. Use `system` for global events. `resource_id` is optional when no single lock applies. |
| `owners` | Current owner of each held lock; omit a free lock. Example: `{"A":"T1","B":"T2"}`. |
| `waits` | The resource each blocked thread currently waits for; omit running threads. Example: `{"T1":"B"}`. A wait must point to a lock held by the other thread. |
| `risk_score` | Integer 0–100, calculated by the analysis module. The UI marks 70 as the demonstration warning threshold. |
| `wait_duration_ms` | Longest waiting duration observed so far in this trial. It may remain nonzero after all threads finish. |
| `contention_count` | Cumulative conflict intensity for the A/B pair at this point. |
| `title`, `detail` | Optional short human-readable event text. The frontend derives defaults when omitted. |

The root `status` must match the last event. For `deadlock`, end with `deadlock_detected` and a two-thread Wait-For Graph cycle. For `completed`, end with `complete` and empty `owners` and `waits`.

This first frontend supports exactly **T1, T2, A, and B**, matching the case study's initial experiment. The trial runner should enforce a timeout for deadlocked runs before it writes JSON, so the website never waits on a stuck thread.

## Try the integration

1. Open the website and choose **Import trial JSON**.
2. Load one of the example files.
3. Run or step through the events.
4. Import the other mode and open **Compare runs**.
5. Export CSV to inspect the displayed data.

The importer validates timestamps, states, score bounds, terminal outcome, and cycle consistency. Invalid files leave the current run unchanged and show an error.

