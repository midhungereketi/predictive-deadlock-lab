# Shared Event Schema & Integration Contract

## Operating Systems Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
**Course:** BCSE303L — Operating Systems  
**Team Members:**
1. **Member 1 (Midhun Gereketi):** Frontend Dashboard, Visualization UI, Trial JSON Contract (v1).
2. **Member 2 (P. Satya Mani Shraavanth):** Multithreaded Experiment Backend, Repeatable Deadlock Engine, Safe Ordering, Event Logging.
3. **Member 3 (M. Lakshman Sai):** Wait-For Graph Analysis, Cycle Detection, Contention Heatmap, Threat Scoring, Predictive Forecasting.

---

## 1. Raw Execution Event Schema (Backend → Analysis Engine)

Every execution event logged by Member 2's backend uses the exact shared schema:

| Field | Type | Description |
|---|---|---|
| `time` | `float` | Monotonic elapsed timestamp relative to the start of the experiment, measured in seconds (e.g., `0.1250`). |
| `thread` | `string` | Thread identifier: `"T1"`, `"T2"`, or `"system"`. |
| `action` | `string` | Observed execution action: `"start"`, `"requested"`, `"waiting"`, `"acquired"`, `"released"`, `"policy_applied"`, `"warning"`, `"deadlock_detected"`, `"timeout"`, `"complete"`. |
| `resource` | `string \| null` | Shared resource identifier: `"A"`, `"B"`, or `null` for global actions. |
| `owner` | `string \| null` | Current owner of the resource at the moment of the event (`"T1"`, `"T2"`, or `null`). |
| `wait_ms` | `integer` | Duration the thread was blocked waiting for this resource in milliseconds (`0` if acquired immediately or not waiting). |

### Example Raw Event
```json
{
  "time": 0.125,
  "thread": "T1",
  "action": "waiting",
  "resource": "B",
  "owner": "T2",
  "wait_ms": 125
}
```

---

## 2. Experiment Execution Response (Section 10 Contract)

Returned by Member 2's `run_experiment()` and the API endpoints (`POST /api/experiments/vulnerable`, `POST /api/experiments/protected`, `POST /api/experiments/run`):

```json
{
  "trial_id": "trial-vulnerable-20261011-001",
  "mode": "vulnerable",
  "status": "deadlock",
  "deadlock_detected": true,
  "completion_time_ms": 1245,
  "events": [
    {
      "time": 0.0,
      "thread": "system",
      "action": "start",
      "resource": null,
      "owner": null,
      "wait_ms": 0
    },
    {
      "time": 0.052,
      "thread": "T1",
      "action": "acquired",
      "resource": "A",
      "owner": "T1",
      "wait_ms": 0
    },
    {
      "time": 0.054,
      "thread": "T2",
      "action": "acquired",
      "resource": "B",
      "owner": "T2",
      "wait_ms": 0
    },
    {
      "time": 0.110,
      "thread": "T1",
      "action": "waiting",
      "resource": "B",
      "owner": "T2",
      "wait_ms": 50
    },
    {
      "time": 0.112,
      "thread": "T2",
      "action": "waiting",
      "resource": "A",
      "owner": "T1",
      "wait_ms": 50
    },
    {
      "time": 0.215,
      "thread": "system",
      "action": "deadlock_detected",
      "resource": null,
      "owner": null,
      "wait_ms": 150
    }
  ],
  "metrics": {
    "threads_started": 2,
    "threads_completed": 0,
    "threads_timed_out": 2,
    "peak_wait_ms": 1000,
    "contention_count": 4,
    "lock_acquisitions": 2,
    "lock_releases": 2,
    "deadlock_cycle": ["T1", "T2", "T1"]
  },
  "error": null
}
```

---

## 3. Frontend Trial v1 Adapter Schema (`trial-v1.schema.json`)

To display backend-executed trials directly inside Member 1's interactive dashboard without modifying its visualization architecture, Member 2's backend also provides an adapter that outputs Member 1's Trial JSON v1 schema:

```json
{
  "schema_version": 1,
  "run_id": "trial-vulnerable-20261011-001",
  "mode": "vulnerable",
  "status": "deadlock",
  "events": [
    {
      "timestamp_ms": 0,
      "thread_id": "system",
      "action": "start",
      "resource_id": null,
      "owners": {},
      "waits": {},
      "risk_score": 8,
      "wait_duration_ms": 0,
      "contention_count": 0,
      "title": "Trial started",
      "detail": "Real multithreaded trial initialized."
    }
  ]
}
```

Endpoints providing this format:
- `POST /api/trials/vulnerable`
- `POST /api/trials/protected`
- `GET /api/trials/{mode}`
