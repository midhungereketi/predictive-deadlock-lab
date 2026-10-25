# Demo and presentation guide

## Before the demo

Use the live app at <https://predictive-deadlock-lab.vercel.app/>, or run it locally from the repository root:

```text
pip install -r member2_backend/requirements.txt
python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` (check `/api/health` if the page does not load). Keep the server running while presenting. If the network fails, import `docs/sample-vulnerable.json` and `docs/sample-protected.json` with **Import trial JSON**; they are real saved trials. Never present the built-in browser demo values as measurements.

## Six-minute live demonstration

1. **Midhun – Lab (two threads).** Click **Run live backend trial** in vulnerable mode, then **▶ Run simulation**. T1 holds A, T2 holds B, T1 waits for B: the risk score crosses 70 *before* T2 waits for A and the Wait-For Graph closes the cycle. Switch to protected mode and run again: a cycle-free probe, the learned A → B order, both workers finish.
2. **Shraavanth – N-thread ring.** Set the thread slider to 8, vulnerable, **Run 8 threads**. Watch the replay: every thread takes its own lock, then waits for its neighbour; the cycle through all 8 threads flashes red; T8 is aborted and the others finish one after another. Point out the distinct OS thread ids in the table. Run protected with 32 threads: no cycle, all threads finish.
3. **Lakshman – Analysis.** Open **Analysis**: "warned 400 ms early" on the demo, or the live run's lead time. Click events to show the factor breakdown. Drag the threshold to 80: the verdict becomes "deadlock not foreseen" – the warning is a tunable heuristic, not proof. Note the status line: settings are temporary or saved *in this browser only*; other visitors are not affected.
4. **Lakshman – Compare.** **Run both modes on backend**, then **Run repeated trials** (5 each) for rates, then a **scaling test** (2–32 threads, 3 trials each). Explain that vulnerable time includes detection and recovery while protected time is completion only, and read the disclaimer.

## Suggested slide sequence (matches `docs/submission/Presentation_Submission.pptx`)

1. Title and team
2. Problem: four deadlock conditions; circular wait from opposite lock order
3. Architecture: browser → FastAPI → experiments → events → WFG, score, results
4. Two-thread experiment: vulnerable trace and Wait-For Graph cycle
5. Risk score: formula, rules, request-scoped weights; warning ≠ proof
6. Prevention: learned global lock order (two threads) and ordered ring
7. N-thread ring: cycle through all N threads and victim recovery
8. Dashboard: replay, Analysis and Compare views
9. Evaluation protocol
10. Results: saved set (15 Oct) and new set (26 Oct) side by side
11. Scaling results with spread
12. Literature review (2020–2025)
13. Limitations and conclusion
14. Team roles and testing

## Likely viva questions

**What proves a deadlock?** A cycle in the Wait-For Graph with single-instance locks. The score alone never does.

**Why does the warning come early?** In the staged schedule one cross-resource wait exists while T2 has not yet requested A; the lock-order rule raises the score to 72 at that moment, using only the current snapshot.

**Does the project predict deadlocks in any program?** No. The warning is a documented heuristic measured in a controlled experiment. Sound and complete prediction is intractable in general (Tunç et al., PLDI 2023).

**Why does a global lock order prevent deadlock?** If every thread acquires locks in the same order, no thread can hold a later lock while waiting for an earlier one, so the cycle's closing edge cannot form.

**How does the ring recover?** The supervisor finds the cycle in a consistent snapshot and cancels the blocked acquire of the highest-numbered thread; it releases its lock, which unblocks its neighbour, and the chain unwinds.

**Why does vulnerable time grow with N?** After recovery the threads finish one after another, each holding both locks for 30 ms, so the time grows by about 30 ms per thread.

**Can one visitor change another's weights?** No. Weights live in each browser and are sent with that visitor's own requests; the server stores nothing. This is covered by automated tests.
