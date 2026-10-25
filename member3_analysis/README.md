# Member 3: Contention Analysis, Scoring, Graph Detection & Evaluation

**Role 3 Owner:** M. Lakshman Sai  
**Course:** BCSE303L — Operating Systems  
**Project:** Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting  

---

## 1. Overview of Assigned Modules

Member 3 implements the analytical intelligence and statistical evaluation layer for the predictive deadlock prevention system:
1. **Dynamic Wait-For Graph (WFG):** Ingests real OS thread execution events and maintains dynamic directed dependencies between blocked and holding threads.
2. **Cycle Detection Algorithm:** Employs directed Depth-First Search (DFS) with recursion tracking to detect circular wait conditions ($T_1 \rightarrow T_2 \rightarrow T_1$), strictly distinguishing actual confirmed deadlocks from heuristic threat scores.
3. **Resource Contention Heatmap:** Maintains both a pairwise conflict matrix ($A \times B$) and a resource-by-thread contention table tracking acquisitions, blocked requests, and wait durations.
4. **Transparent Threat Scoring Engine:** Computes a normalized, configurable threat score ($0 - 100$) combining blocked threads, wait duration, contention frequency, and lock-order inversion risk.
5. **Trend Analysis & Early Warning:** Computes real-time slope ($\Delta \text{score} / 100\text{ms}$), trajectory classification (`RISING`, `STABLE`, `FALLING`, `INSUFFICIENT_DATA`), and calculates warning lead time ($t_{\text{deadlock}} - t_{\text{warning}}$).
6. **Experimental Comparator:** Executes repeated multithreaded trials ($N=5$) comparing Vulnerable vs. Protected modes across deadlock rate, completion rate, warning lead time, detection latency, average wait duration, and completion time.
7. **Full Dashboard & API Integration:** Integrates seamlessly into the dashboard with live metric breakdowns, alert banners, sensitivity sliders, and REST endpoints.

---

## 2. Threat Score Formula & Mathematical Documentation

### Transparent Normalization Formula
$$\text{ThreatScore}(t) = \min\left(100, \max\left(0, \text{round}\left(w_b \cdot B_{\text{norm}}(t) + w_w \cdot W_{\text{norm}}(t) + w_c \cdot C_{\text{norm}}(t) + w_r \cdot R_{\text{norm}}(t)\right)\right)\right)$$

In this controlled two-lock experiment, one additional **structural warning rule** applies: if A and B are held by different threads and one thread is already waiting for the other's lock, the pre-cycle score is raised to at least 72. This is a risk forecast, not a confirmed deadlock. A cycle is the only deadlock proof. Configured weights must sum to 1.00.

### Input Normalizations
| Observable | Variable | Ceiling | Normalization Formula | Description |
|---|---|---|---|---|
| Blocked Threads | $B_{\text{norm}}$ | $N_{\text{max}} = 2$ | $\min(100, \frac{N_{\text{blocked}}}{2} \times 100)$ | Fraction of worker threads currently blocked waiting for a lock. |
| Wait Duration | $W_{\text{norm}}$ | $T_{\text{max}} = 800\text{ ms}$ | $\min(100, \frac{\text{wait\_duration\_ms}}{800} \times 100)$ | Current longest wait duration relative to saturation horizon. |
| Contention Events | $C_{\text{norm}}$ | $C_{\text{max}} = 5$ | $\min(100, \frac{\text{conflict\_count}}{5} \times 100)$ | Cumulative conflict intensity observed across resource requests. |
| Lock Inversion / Conflict | $R_{\text{norm}}$ | $100\%$ | $100\%$ if both locks held by distinct threads; $40\%$ if both held by one thread; $20\%$ if one lock held; $0\%$ otherwise | Risk index for conflicting resource ownership paths. |

### Configurable Weights & Thresholds
- **$w_b = 0.35$** (35% weight on blocked thread ratio)
- **$w_w = 0.30$** (30% weight on wait duration)
- **$w_c = 0.20$** (20% weight on contention count)
- **$w_r = 0.15$** (15% weight on lock conflict / criticality)
- **Sum of weights:** $0.35 + 0.30 + 0.20 + 0.15 = 1.00$
- **Low Risk:** Score $0 - 39$ (Calm, normal concurrency)
- **Elevated Risk:** Score $40 - 69$ (Moderate contention observed)
- **High Risk (Early Warning):** Score $70 - 100$ (Warning triggered before deadlock)
- **Confirmed Deadlock:** Wait-For Graph cycle confirmed (Deadlock state, score $\ge 96$)

> **Scientific Disclosure:** This threat scoring formula is a transparent heuristic designed for experimental evaluation, not an empirically validated universal law. It provides an early signal before circular wait forms.

---

## 3. Wait-For Graph & Cycle Detection Architecture

File: `member3_analysis/graph.py`

- **Nodes:** Active threads ($T_1, T_2$).
- **Directed Edges:** $T_i \xrightarrow{R} T_j$ indicates that thread $T_i$ is blocked waiting for lock $R$ currently held by $T_j$.
- **Dynamic Dependency Updates:**
  - `acquired`: Thread becomes owner; removes any waiting dependency for that lock.
  - `waiting`: If target lock is held by another thread, adds directed dependency $T_{\text{waiter}} \xrightarrow{R} T_{\text{holder}}$. If unowned, handles safely without inventing false dependencies.
  - `released`: Holder releases lock; removes all incoming dependency edges targeting the released resource.
  - `complete`: Resets all edges and owners.
- **Cycle Detection:** Directed DFS with recursion stack detects back-edges. Returns canonical cycle representations (e.g., `[['T1', 'T2', 'T1']]`) and participating edges.

---

## 4. Contention Heatmap Architecture

File: `member3_analysis/heatmap.py`

Tracks real, observed execution data without hardcoded values:
1. **Pairwise Conflict Matrix ($A \times B$):**
   - Tracks how frequently a thread holding Lock $A$ requests Lock $B$, and vice versa.
   - Highlights $A \leftrightarrow B$ as a contention hotspot during opposite-order acquisitions.
2. **Resource-by-Thread Matrix:**
   - Tracks per-thread acquisitions, blocked attempts, and total/maximum wait durations for Lock $A$ and Lock $B$.

---

## 5. Experimental Repeated-Trial Comparison

File: `member3_analysis/comparator.py`

Executes repeated trials (default $N=5$ per mode) on real threads via `member2_backend.experiment_runner.run_experiment`. Run the endpoint to obtain the values for the current machine and run; the table below defines what is measured and does not assert fixed outcomes:

| Metric | Vulnerable Mode (Opposite Orders) | Protected Mode (Order Derived from Probe) |
|---|---|---|
| **Lock Ordering** | $T_1: A \rightarrow B$, $T_2: B \rightarrow A$ | $T_1: A \rightarrow B$, $T_2: A \rightarrow B$ |
| **Deadlock Rate** | Cycle-confirmed trials ÷ trials run | Cycle-confirmed trials ÷ trials run |
| **Completion Rate** | Completed trials ÷ trials run | Completed trials ÷ trials run |
| **Mean Warning Lead Time** | First score crossing before cycle, measured from event timestamps | N/A if no cycle forms |
| **Detection Latency** | `deadlock_detected` event time minus first cycle event time | N/A if no cycle forms |
| **Peak Threat Score** | Maximum of time-local trial scores | Maximum of time-local trial scores |
| **Coffman Condition 4** | Circular wait confirmed | Circular wait eliminated |

> **Experimental Note:** A 120 ms staged observation window makes the warning lead time measurable in the vulnerable teaching scenario. Protected mode derives its common order from a cycle-free contention probe before the main workers. These controlled schedules do not establish predictive performance under arbitrary scheduling. The trial runner uses bounded waits in one Python process, not a separately isolated worker process.

---

## 6. REST API Endpoints

Mounted under `/api/analysis`. Scoring weights are **request-scoped**: the server stores no scoring state, so one caller's weights never change another caller's results.
- `GET /api/analysis/config` — The default formula weights, thresholds, and formula documentation.
- `PUT /api/analysis/config` — Validate proposed weights and threshold (returns `"persisted": false`; nothing is stored).
- `POST /api/analysis/evaluate` — Run WFG, cycle detection, heatmap, and scoring on any event stream; optional `"scoring": {...}` object with weights for this request.
- `POST /api/analysis/compare?trials_per_mode=5&timeout=3.0` — Execute repeated trials and return statistical comparison.
- `GET /api/analysis/compare?trials_per_mode=3` — Quick browser GET test.

`/api/analysis/compare` and `/api/trials/{mode}` accept the optional query parameters `w_blocked`, `w_wait`, `w_contention`, `w_resource` and `threshold_high`; invalid values (weights not summing to 1.00) return 422.

---

## 7. How to Run Tests

```bash
# Run Member 3 Analysis Unit & Integration Tests (18 tests)
python -m pytest member3_analysis/tests/ -v

# Run All Project Tests (Python + Node.js)
python -m pytest member2_backend/tests/ member3_analysis/tests/ -v
node --test frontend/tests/trial-data.test.js
```
