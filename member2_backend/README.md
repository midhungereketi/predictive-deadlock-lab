# Member 2 Backend — Real-Thread Deadlock Experiment Engine

**Component:** Experiment Backend & Lock Ordering Engine  
**Author:** P. Satya Mani Shraavanth (Member 2)  
**Project:** Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting  
**Course:** BCSE303L — Operating Systems  

---

## 1. Purpose of the Backend

The Member 2 backend is the core Operating Systems execution engine for the project. Its primary purpose is to provide **controlled, repeatable, multithreaded experiments using real OS threads and mutex locks**, comparing:
1. **A vulnerable execution baseline** that demonstrates a real circular wait between two threads competing for shared mutex locks in conflicting orders (`T1: A → B` and `T2: B → A`).
2. **A protected execution mode** that enforces a canonical global lock acquisition order (`Lock A → Lock B`) to systematically prevent the circular wait condition.

It logs fine-grained, timestamped execution events using the agreed shared schema so that **Member 3** can construct the Wait-For Graph, detect cycles, calculate contention heatmaps, compute threat scores, and perform predictive forecasting. It also integrates directly with **Member 1's** web dashboard for live trial execution and visualization.

---

## 2. How it Fits into the Project Architecture

The three-member architecture is partitioned as follows:

```
┌─────────────────────────────────────────────────────────────┐
│                 Member 1 — Midhun Gereketi                  │
│       Frontend Dashboard, Visualization UI & Replay         │
└──────────────────────────────▲──────────────────────────────┘
                               │ JSON Trial Contract (v1) / REST API
┌──────────────────────────────┴──────────────────────────────┐
│          Member 2 — P. Satya Mani Shraavanth (This Engine)  │
│  Real OS Threads · Conflicting Lock Order · Safe Ordering   │
│  Synchronization Barriers · Bounded Waits · Event Logger    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Raw Execution Events [time, thread, action, ...]
┌──────────────────────────────▼──────────────────────────────┐
│                 Member 3 — M. Lakshman Sai                  │
│    Wait-For Graph · Cycle Detection · Contention Heatmap    │
│       Threat Score Heuristic · Predictive Forecasting       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Explanation of Vulnerable Mode

File: `member2_backend/vulnerable_experiment.py`

In vulnerable mode, two worker threads compete for two shared mutex resources with conflicting lock acquisition paths:
- **Thread T1:** Attempts to acquire **Lock A**, then **Lock B**.
- **Thread T2:** Attempts to acquire **Lock B**, then **Lock A**.

### Synchronization & Repeatability Mechanism
To eliminate race conditions and avoid relying on arbitrary `sleep()` durations:
1. **Barrier Synchronization (`threading.Barrier(2)`):** 
   - T1 acquires Lock A.
   - T2 acquires Lock B.
   - Both threads wait on the barrier. This guarantees that T1 holds Lock A and T2 holds Lock B before either thread requests its second lock.
2. **Conflicting Acquisition:**
   - T1 attempts to acquire Lock B (currently held by T2).
   - T2 attempts to acquire Lock A (currently held by T1).
3. **Confirmed Circular Wait:**
   - Active supervisor monitor inspects the Wait-For Graph:
     - $T_1 \rightarrow T_2$ ($T_1$ waits for Lock B held by $T_2$)
     - $T_2 \rightarrow T_1$ ($T_2$ waits for Lock A held by $T_1$)
     - Cycle confirmed: $T_1 \rightarrow T_2 \rightarrow T_1$.
   - A `deadlock_detected` event is recorded.
4. **Bounded Waits & Safe Termination:**
   - Lock acquisitions use bounded timeouts (`VULNERABLE_LOCK_TIMEOUT_SECONDS = 0.8s`).
   - When the timeout expires, each thread gracefully releases its held lock (`T1` releases `A`, `T2` releases `B`).
   - Both threads join and terminate cleanly.
   - **No threads are left blocked in the background.**

---

## 4. Explanation of Protected Mode

File: `member2_backend/protected_experiment.py`

The protected experiment demonstrates deadlock prevention by eliminating the **Circular Wait** Coffman condition.

### Canonical Lock Ordering Rule
- Common global order: **`Lock A → Lock B`**.
- Every thread must acquire locks according to this total order, regardless of its original logical request sequence.
- When `T1` requests `[A, B]`: Canonical order remains `[A, B]`.
- When `T2` requests `[B, A]`: The lock manager normalizes the acquisition path to `[A, B]` *before* `T2` acquires its first lock.
- A `policy_applied` event is logged.

### Execution Flow & Invariants
1. `T1` acquires Lock A, then Lock B, enters its critical section, and releases both locks.
2. `T2` attempts to acquire Lock A. Because Lock A is held by `T1`, `T2` waits for Lock A. **Crucially, `T2` does not hold Lock B while waiting.**
3. The Wait-For Graph contains at most one directed edge ($T_2 \rightarrow T_1$). **No cycle is ever formed.**
4. Once `T1` releases the locks, `T2` acquires Lock A, then Lock B, finishes its critical section, and releases all locks.
5. Both threads finish successfully, and a `complete` event is logged.

> **Important Note:** This implementation enforces a static canonical global lock order as a reliable protected baseline. It is not yet the full runtime-adaptive lock-ordering research component.

---

## 5. Event Schema & Field Definitions

File: `member2_backend/event_logger.py`

Member 2 uses the exact shared event format agreed upon with Member 1 and Member 3:

`time, thread, action, resource, owner, wait_ms`

### Field Specifications
| Field | Type | Description |
|---|---|---|
| `time` | `float` | Monotonic elapsed time in seconds from trial start (e.g. `0.1250`). |
| `thread` | `string` | Thread identifier: `"T1"`, `"T2"`, or `"system"`. |
| `action` | `string` | Action name: `"start"`, `"requested"`, `"waiting"`, `"acquired"`, `"released"`, `"policy_applied"`, `"warning"`, `"deadlock_detected"`, `"timeout"`, `"complete"`. |
| `resource` | `string \| null` | Mutex name: `"A"`, `"B"`, or `null`. |
| `owner` | `string \| null` | Current owner of the lock at event creation: `"T1"`, `"T2"`, or `null`. |
| `wait_ms` | `integer` | Duration the thread was blocked in milliseconds (`0` if acquired immediately). |

---

## 6. Public Python Interface & REST API

### Python Interface (`experiment_runner.py`)
```python
from member2_backend import run_experiment, to_trial_v1

# Run vulnerable experiment
result = run_experiment(mode="vulnerable", timeout_seconds=5.0)
print(result.status)              # "deadlock"
print(result.deadlock_detected)   # True
print(result.metrics.deadlock_cycle)  # ['T1', 'T2', 'T1']

# Run protected experiment
result_prot = run_experiment(mode="protected", timeout_seconds=5.0)
print(result_prot.status)             # "completed"
print(result_prot.deadlock_detected)  # False

# Convert to Member 1 trial-v1 JSON format
trial_json = to_trial_v1(result)
```

### Response Contract (Section 10)
```json
{
  "trial_id": "trial-vulnerable-20261011-001",
  "mode": "vulnerable",
  "status": "deadlock",
  "deadlock_detected": true,
  "completion_time_ms": 1250,
  "events": [
    {
      "time": 0.052,
      "thread": "T1",
      "action": "acquired",
      "resource": "A",
      "owner": "T1",
      "wait_ms": 0
    }
  ],
  "metrics": {
    "threads_started": 2,
    "threads_completed": 0,
    "threads_timed_out": 2,
    "peak_wait_ms": 800,
    "contention_count": 2,
    "lock_acquisitions": 2,
    "lock_releases": 2,
    "deadlock_cycle": ["T1", "T2", "T1"]
  },
  "error": null
}
```

### REST API Endpoints (`api.py`)
- `GET /api/health` — Service health and metadata.
- `POST /api/experiments/vulnerable` — Execute real vulnerable experiment.
- `POST /api/experiments/protected` — Execute real protected experiment.
- `POST /api/experiments/run` — Parameterized execution with JSON body `{"mode": "vulnerable", "timeout_seconds": 5.0}`.
- `POST /api/trials/{mode}` — Execute trial and return Member 1's `trial-v1.schema.json` format directly.
- `GET /api/trials/{mode}` — Same as above for quick browser testing.
- `GET /` — Serves Member 1's frontend dashboard statically.

---

## 7. Installation & Startup Commands

### Prerequisites
- Python 3.10+ (tested on Python 3.11.9)
- Node.js (optional, for contract tests)

### Install Dependencies
```bash
pip install -r member2_backend/requirements.txt
```

### Launch the Backend & Dashboard Server
From the repository root:
```bash
python -m uvicorn member2_backend.api:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at:
`http://127.0.0.1:8000/`

---

## 8. How to Run Tests

### Python Backend Unit & Integration Tests (16 Tests)
```bash
python -m pytest member2_backend/tests/ -v
```

### Frontend Contract Validation Tests (Node.js)
```bash
node --test frontend/tests/trial-data.test.js
```

---

## 9. Integration with Member 1 & Member 3

### Member 1 (Frontend Website)
- Member 1's dashboard now has a **"⚡ Run live backend trial"** button.
- Clicking this triggers a fetch to `/api/trials/{mode}`.
- The returned data is passed directly to `window.DeadlockLab.loadTrial(trialData)`.
- The Wait-For Graph, Risk Chart, Timeline, and Heatmap instantly visualize real OS thread activity.

### Member 3 (Contention Analysis & Threat Forecasting)
- Member 3 consumes the raw `events` list from `result.events` or the trial snapshots.
- `time`, `thread`, `action`, `resource`, `owner`, and `wait_ms` provide all data required for:
  - Cycle detection algorithms.
  - Pairwise contention count calculations.
  - Threat score heuristics and regression/ARIMA forecasting.
  - Statistical comparison tables (lead time, completion time, deadlock rate).

---

## 10. Known Limitations & Troubleshooting

1. **Two-Thread, Two-Lock Scope:** The current implementation models single-instance mutex resources `A` and `B` with two threads `T1` and `T2`. Multi-resource Banker's algorithm scaling is a potential future extension.
2. **OS Thread Scheduling Variation:** Because Python threads are scheduled by the underlying OS kernel, minor timing jitter in elapsed milliseconds is normal. Barrier synchronization ensures deterministic state progression.
3. **Port Conflicts:** If port 8000 is occupied, run uvicorn on another port with `--port 8080`.
