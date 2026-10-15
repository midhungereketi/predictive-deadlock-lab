# Demo and presentation guide

## Before the demo

From the repository root, install dependencies and start the server:

```text
pip install -r member2_backend/requirements.txt
python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` on the same computer. Check `http://127.0.0.1:8000/api/health` if the page does not load. Keep the server running while presenting. The hosted static preview can replay examples but cannot execute Python trials.

## Three-minute live demonstration

1. **Midhun:** Show the dashboard's timeline, Wait-For Graph, score trend, and heatmap. State that built-in playback is illustrative; click **Run live backend trial** for actual thread data.
2. **Shraavanth:** Select vulnerable mode and run a live trial. Point out T1 holding A, T2 holding B, then T1 waiting for B. The score rises before T2 waits for A. Once both waits exist, the graph has a cycle and the supervisor reports deadlock. Explain bounded waits prevent an indefinite hang.
3. **Lakshman:** Select protected mode and run a live trial. Show the warning during the safe probe, then policy activation, then both workers finishing under the derived common order. Run the batch comparison and explain rates, runtime, warning lead, and detection latency.

If live execution fails, import `docs/sample-vulnerable.json` and `docs/sample-protected.json` to demonstrate real saved trial output. Do not call the built-in browser demo measured evidence.

## Suggested slide sequence

1. **Problem:** Opposite lock orders permit circular wait and service disruption.
2. **Objective:** Observe contention, warn before a cycle in a controlled schedule, and remove circular wait through one shared lock order.
3. **Architecture:** Browser → FastAPI → threaded experiments → event stream → graph, score, heatmap, comparison.
4. **Vulnerable trace:** T1: A → B; T2: B → A; WFG cycle T1 → T2 → T1.
5. **Risk calculation:** Four normalized factors plus a documented structural warning floor; warning is distinct from confirmed cycle.
6. **Adaptive protected trace:** Cycle-free probe → observed A → B dependency → learned common A → B order → two completed workers.
7. **Results:** 10/10 vulnerable deadlocks, 0/10 protected deadlocks, 10/10 protected completions in the saved controlled sample. Show timing figures from `docs/FINAL_REPORT.md`.
8. **Limits and conclusion:** The schedule and two-lock scope explain why the result is a demonstration, not a universal predictor. A common total order prevents this case's circular wait.

## Likely viva questions

**What proves a deadlock?** A cycle in the Wait-For Graph while each waiting thread holds one of the two single-instance resources. A score alone does not prove it.

**Why is the warning early?** In the staged vulnerable schedule, one cross-resource wait exists while T2 still has not requested A. The structural rule crosses the warning threshold at that time.

**Why does common ordering work?** If every worker acquires A before B, no worker can hold B while waiting for A. The cycle's opposite edge cannot form.

**Is the policy learned during a deadlock?** No. The protected calibration probe stops before the second conflicting request and records a cycle-free wait. The learned order applies to the main protected phase.

**Can the static website run the backend?** No. Use the local FastAPI server for live experiments. The static page is useful for playback and importing recorded trials.
