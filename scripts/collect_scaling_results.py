"""Collect repeated N-thread ring measurements for the scaling evaluation.

Run from the repository root:
    python scripts/collect_scaling_results.py --sizes 2 4 8 16 32 --trials 10 --output docs/<file>.json

Every run is a real, bounded execution of member2_backend.multi_thread_experiment.
Raw per-run values are saved alongside the summary so every number in the report
can be traced back to an individual run.
"""

import argparse
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from member2_backend.config import MULTI_THREAD_MAX, MULTI_THREAD_MIN  # noqa: E402
from member2_backend.multi_thread_experiment import run_multi_thread_experiment  # noqa: E402


def spread(values):
    if not values:
        return None
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 2),
        "sd": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "median": round(statistics.median(values), 2),
    }


def record(result, threads):
    cycle = result.metrics.deadlock_cycle
    return {
        "status": result.status,
        "runtime_ms": result.completion_time_ms,
        "cycle_length": len(cycle) - 1 if cycle else 0,
        "detected_ms": result.snapshot.time_ms if result.snapshot and result.snapshot.label == "deadlock" else None,
        "finished": result.metrics.threads_completed,
        "aborted": sum(1 for worker in result.workers if worker.outcome == "aborted"),
        "victim": result.victim,
        "peak_queued": len(result.snapshot.waits) if result.snapshot else 0,
        "distinct_os_threads": len({worker.native_id for worker in result.workers}),
        "error": result.error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[2, 4, 8, 16, 32])
    parser.add_argument("--trials", type=int, default=10, choices=range(1, 31), metavar="1..30")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if any(not MULTI_THREAD_MIN <= size <= MULTI_THREAD_MAX for size in args.sizes):
        parser.error(f"sizes must be between {MULTI_THREAD_MIN} and {MULTI_THREAD_MAX}")

    sizes = []
    for threads in args.sizes:
        runs = {"vulnerable": [], "protected": []}
        for _ in range(args.trials):
            for mode in ("vulnerable", "protected"):  # alternate so drift affects both modes
                runs[mode].append(record(run_multi_thread_experiment(mode=mode, thread_count=threads, timeout_seconds=args.timeout), threads))
        v, p = runs["vulnerable"], runs["protected"]
        sizes.append({
            "threads": threads,
            "vulnerable": {
                "runs": v,
                "deadlocked": sum(r["status"] == "deadlock" for r in v),
                "cycle_through_all_threads": sum(r["cycle_length"] == threads for r in v),
                "recovered_one_victim": sum(r["aborted"] == 1 and r["finished"] == threads - 1 for r in v),
                "detection_ms": spread([r["detected_ms"] for r in v if r["detected_ms"] is not None]),
                "detection_plus_recovery_runtime_ms": spread([r["runtime_ms"] for r in v]),
            },
            "protected": {
                "runs": p,
                "completed_all_threads": sum(r["status"] == "completed" and r["finished"] == threads for r in p),
                "peak_queued": spread([r["peak_queued"] for r in p]),
                "completion_runtime_ms": spread([r["runtime_ms"] for r in p]),
            },
        })
        print(f"{threads:>2} threads: vulnerable {sizes[-1]['vulnerable']['deadlocked']}/{args.trials} deadlocked, "
              f"protected {sizes[-1]['protected']['completed_all_threads']}/{args.trials} completed")

    output = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine()},
        "protocol": {
            "experiment": "N-thread resource ring: thread Ti needs locks Ri and R(i mod N)+1",
            "vulnerable": "each thread takes its own lock, all threads rendezvous, then each requests the next lock; the supervisor detects the cycle and aborts the highest-numbered thread",
            "protected": "each thread takes the lower-numbered lock first (global order); threads hold both locks for 30 ms",
            "sizes": args.sizes,
            "trials_per_size_per_mode": args.trials,
            "per_run_timeout_seconds": args.timeout,
            "runtime_meaning": {"vulnerable": "start to detection, victim abort and all other threads finishing", "protected": "start to every thread completing"},
            "clock": "time.perf_counter (high-resolution monotonic)",
        },
        "sizes": sizes,
    }
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("Saved " + args.output)


if __name__ == "__main__":
    main()
