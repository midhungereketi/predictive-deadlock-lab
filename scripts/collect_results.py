"""Collect reproducible local measurements and frontend-importable trial samples.

Run from the repository root: python scripts/collect_results.py --trials 10
"""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from member2_backend.experiment_runner import run_experiment, to_trial_v1
from member3_analysis.comparator import ExperimentComparator


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=10, choices=range(1, 21), metavar="1..20")
    args = parser.parse_args()

    comparator = ExperimentComparator()
    comparison = comparator.run_comparison(trials_per_mode=args.trials, timeout_seconds=3.0)
    output = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "protocol": {
            "threads": 2,
            "resources": ["A", "B"],
            "vulnerable_order": {"T1": ["A", "B"], "T2": ["B", "A"]},
            "protected_policy": "Order derived from a cycle-free contention probe before main workers start",
            "vulnerable_observation_window_ms": 120,
            "per_trial_timeout_seconds": 3.0,
        },
        "comparison": comparison,
    }
    save(ROOT / "docs" / "results.json", output)

    for mode in ("vulnerable", "protected"):
        trial = run_experiment(mode=mode, timeout_seconds=3.0)
        if trial.status not in ("deadlock", "completed"):
            raise RuntimeError(f"{mode} sample failed: {trial.status}: {trial.error}")
        save(ROOT / "docs" / f"sample-{mode}.json", to_trial_v1(trial))

    print("Saved docs/results.json and both frontend-importable sample trials")
    for mode in ("vulnerable", "protected"):
        row = comparison[mode]
        print(f"{mode}: {row['deadlock_count']}/{row['total_trials']} deadlocks; "
              f"{row['completion_count']}/{row['total_trials']} completions; "
              f"{row['inconclusive_count']} inconclusive")


if __name__ == "__main__":
    main()
