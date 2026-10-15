"""Experimental Comparison Engine for Vulnerable vs. Protected Runs.

Author: M. Lakshman Sai (Role 3)
Course: BCSE303L - Operating Systems
Project: Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting
"""

import statistics
import time
from typing import Any, Dict, List, Optional

from member2_backend.experiment_runner import run_experiment
from .graph import WaitForGraph
from .threat_scorer import ThreatScorer
from .trend_analyzer import ThreatTrendAnalyzer
from .heatmap import ContentionHeatmapTracker


def analyze_trial_events(
    events: List[Any],
    scorer: Optional[ThreatScorer] = None,
) -> Dict[str, Any]:
    """Execute rigorous offline/online analysis on a sequence of raw experiment events.

    Uses Member 3's WaitForGraph, ThreatScorer, ThreatTrendAnalyzer, and ContentionHeatmapTracker.
    """
    scorer = scorer or ThreatScorer()
    graph = WaitForGraph()
    trend = ThreatTrendAnalyzer(warning_threshold=scorer.config.threshold_high)
    heatmap = ContentionHeatmapTracker()

    cycle_detected_at_time = None
    detection_event_at_time = None
    observed_cycles = []
    first_warning_at_time = None
    peak_score = 0
    peak_wait_ms = 0
    total_wait_ms = 0
    wait_count = 0

    for ev in events:
        # Normalize event dict
        ev_dict = ev.to_dict() if hasattr(ev, "to_dict") else dict(ev)
        t_sec = float(ev_dict.get("time") or 0.0)
        t_ms = int(round(t_sec * 1000))
        thread = str(ev_dict.get("thread") or "")
        action = str(ev_dict.get("action") or "")
        resource = ev_dict.get("resource")
        owner = ev_dict.get("owner")
        wait_ms = int(ev_dict.get("wait_ms") or 0)

        # 1. Update graph
        snapshot = graph.process_raw_event(ev_dict)
        has_cycle = snapshot["has_cycle"]

        if has_cycle and cycle_detected_at_time is None:
            cycle_detected_at_time = t_ms
            observed_cycles = snapshot["cycles"]
        if action == "deadlock_detected" and has_cycle and detection_event_at_time is None:
            detection_event_at_time = t_ms

        if wait_ms > 0:
            total_wait_ms += wait_ms
            wait_count += 1
            if wait_ms > peak_wait_ms:
                peak_wait_ms = wait_ms

        # 2. Update heatmap
        heatmap.record_event(
            action=action,
            thread=thread,
            resource=resource,
            owner=owner,
            wait_ms=wait_ms,
            current_owners=snapshot["owners"],
        )

        # 3. Calculate threat score
        score_res = scorer.evaluate(
            num_blocked=snapshot["blocked_thread_count"],
            wait_duration_ms=peak_wait_ms,
            contention_count=heatmap.total_conflict_events,
            owners=snapshot["owners"],
            waits=snapshot["waits"],
            has_cycle=has_cycle,
        )

        if score_res.score > peak_score:
            peak_score = score_res.score

        if score_res.is_early_warning and first_warning_at_time is None:
            first_warning_at_time = t_ms

        # 4. Record trend sample
        trend.record_sample(
            timestamp_ms=t_ms,
            score=score_res.score,
            num_blocked=snapshot["blocked_thread_count"],
            has_cycle=has_cycle,
        )

    # Calculate warning lead time (time from early warning to cycle)
    warning_lead_time_ms = None
    if cycle_detected_at_time is not None and first_warning_at_time is not None:
        warning_lead_time_ms = max(0, cycle_detected_at_time - first_warning_at_time)

    # Detection latency comes from the event timestamps, not monitor frequency.
    detection_latency_ms = None
    if cycle_detected_at_time is not None and detection_event_at_time is not None:
        detection_latency_ms = max(0, detection_event_at_time - cycle_detected_at_time)

    trend_status = trend.get_trend_status()
    heatmap_summary = heatmap.get_summary()

    return {
        "final_graph": graph.get_snapshot(),
        "has_cycle": cycle_detected_at_time is not None,
        "cycles": observed_cycles,
        "peak_score": peak_score,
        "peak_wait_ms": peak_wait_ms,
        "avg_wait_ms": round(total_wait_ms / max(1, wait_count), 1),
        "first_warning_ms": first_warning_at_time,
        "cycle_detected_ms": cycle_detected_at_time,
        "warning_lead_time_ms": warning_lead_time_ms,
        "detection_latency_ms": detection_latency_ms,
        "trend": trend_status,
        "heatmap": heatmap_summary,
        "time_series": trend.get_time_series(),
    }


class ExperimentComparator:
    """Runs and compares real repeated multithreaded trials in both modes."""

    def __init__(self, scorer: Optional[ThreatScorer] = None) -> None:
        self.scorer = scorer or ThreatScorer()

    def run_comparison(self, trials_per_mode: int = 5, timeout_seconds: float = 3.0) -> Dict[str, Any]:
        """Execute N repeated trials for both Vulnerable and Protected modes,

        then synthesize measured empirical comparison metrics.
        """
        trials_per_mode = max(1, min(20, int(trials_per_mode)))

        vulnerable_results = []
        protected_results = []

        # 1. Run Vulnerable Trials
        for i in range(trials_per_mode):
            trial_id = f"cmp-vuln-{int(time.time())}-{i+1}"
            exp_res = run_experiment(mode="vulnerable", timeout_seconds=timeout_seconds, trial_id=trial_id)
            analysis = analyze_trial_events(exp_res.events, self.scorer)
            vulnerable_results.append({
                "trial_id": trial_id,
                "status": exp_res.status,
                "deadlock_detected": exp_res.deadlock_detected or analysis["has_cycle"],
                "completion_time_ms": exp_res.completion_time_ms,
                "has_cycle": analysis["has_cycle"],
                "cycles": analysis["cycles"],
                "peak_score": analysis["peak_score"],
                "peak_wait_ms": analysis["peak_wait_ms"],
                "avg_wait_ms": analysis["avg_wait_ms"],
                "warning_lead_time_ms": analysis["warning_lead_time_ms"],
                "detection_latency_ms": analysis["detection_latency_ms"],
            })

        # 2. Run Protected Trials
        for i in range(trials_per_mode):
            trial_id = f"cmp-prot-{int(time.time())}-{i+1}"
            exp_res = run_experiment(mode="protected", timeout_seconds=timeout_seconds, trial_id=trial_id)
            analysis = analyze_trial_events(exp_res.events, self.scorer)
            protected_results.append({
                "trial_id": trial_id,
                "status": exp_res.status,
                "deadlock_detected": exp_res.deadlock_detected or analysis["has_cycle"],
                "completion_time_ms": exp_res.completion_time_ms,
                "has_cycle": analysis["has_cycle"],
                "cycles": analysis["cycles"],
                "peak_score": analysis["peak_score"],
                "peak_wait_ms": analysis["peak_wait_ms"],
                "avg_wait_ms": analysis["avg_wait_ms"],
                "warning_lead_time_ms": analysis["warning_lead_time_ms"],
                "detection_latency_ms": analysis["detection_latency_ms"],
            })

        # 3. Aggregate Statistical Metrics
        def aggregate_mode(data: List[Dict[str, Any]], mode_name: str) -> Dict[str, Any]:
            total = len(data)
            deadlocks = sum(1 for r in data if r["deadlock_detected"] or r["has_cycle"])
            completed = sum(1 for r in data if r["status"] == "completed" and not r["has_cycle"])
            inconclusive = total - deadlocks - completed
            completion_times = [r["completion_time_ms"] for r in data if r["status"] == "completed" and r["completion_time_ms"] > 0]
            runtimes = [r["completion_time_ms"] for r in data if r["completion_time_ms"] > 0]
            peak_scores = [r["peak_score"] for r in data]
            peak_waits = [r["peak_wait_ms"] for r in data]
            avg_waits = [r["avg_wait_ms"] for r in data]
            leads = [r["warning_lead_time_ms"] for r in data if r["warning_lead_time_ms"] is not None]
            latencies = [r["detection_latency_ms"] for r in data if r["detection_latency_ms"] is not None]

            deadlock_rate = round((deadlocks / total) * 100, 1)
            completion_rate = round((completed / total) * 100, 1)

            return {
                "mode": mode_name,
                "total_trials": total,
                "deadlock_count": deadlocks,
                "deadlock_rate_percent": deadlock_rate,
                "completion_count": completed,
                "completion_rate_percent": completion_rate,
                "inconclusive_count": inconclusive,
                "mean_completion_time_ms": round(statistics.mean(completion_times), 1) if completion_times else 0,
                "mean_trial_runtime_ms": round(statistics.mean(runtimes), 1) if runtimes else 0,
                "mean_peak_score": round(statistics.mean(peak_scores), 1) if peak_scores else 0,
                "mean_peak_wait_ms": round(statistics.mean(peak_waits), 1) if peak_waits else 0,
                "mean_avg_wait_ms": round(statistics.mean(avg_waits), 1) if avg_waits else 0,
                "mean_warning_lead_time_ms": round(statistics.mean(leads), 1) if leads else None,
                "mean_detection_latency_ms": round(statistics.mean(latencies), 1) if latencies else None,
                "trials": data,
            }

        vuln_summary = aggregate_mode(vulnerable_results, "vulnerable")
        prot_summary = aggregate_mode(protected_results, "protected")

        # 4. Comparative Synthesis
        insight = (
            f"Evaluated across {trials_per_mode} repeated real-thread trials per mode: "
            f"Vulnerable mode produced a {vuln_summary['deadlock_rate_percent']}% deadlock rate "
            f"({vuln_summary['deadlock_count']}/{vuln_summary['total_trials']} trials deadlocked with circular wait) "
            f"with an average warning lead time of {vuln_summary['mean_warning_lead_time_ms'] or 'N/A'} ms. "
            f"Protected mode achieved a {prot_summary['completion_rate_percent']}% completion rate "
            f"({prot_summary['completion_count']}/{prot_summary['total_trials']} trials completed successfully) "
            f"with {prot_summary['deadlock_count']} observed deadlocks and "
            f"{prot_summary['inconclusive_count']} inconclusive trials under common lock ordering A -> B."
        )

        return {
            "trials_per_mode": trials_per_mode,
            "vulnerable": vuln_summary,
            "protected": prot_summary,
            "comparative_summary": {
                "deadlock_reduction_percent": round(vuln_summary["deadlock_rate_percent"] - prot_summary["deadlock_rate_percent"], 1),
                "completion_increase_percent": round(prot_summary["completion_rate_percent"] - vuln_summary["completion_rate_percent"], 1),
                "vulnerable_warning_lead_ms": vuln_summary["mean_warning_lead_time_ms"],
                "vulnerable_detection_latency_ms": vuln_summary["mean_detection_latency_ms"],
            },
            "insight": insight,
            "scientific_disclaimer": (
                f"Protected mode had {prot_summary['deadlock_count']} observed deadlocks and "
                f"{prot_summary['inconclusive_count']} inconclusive runs in this controlled sample. "
                "Its order is derived from a short, cycle-free contention probe before the main workers start. "
                "A common total order removes circular wait for these two single-instance locks; "
                "the result does not establish performance on arbitrary programs or schedules."
            ),
        }
