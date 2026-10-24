"""Coverage for configurable real-thread experiments and multi-node cycles."""

from member2_backend.multi_thread_experiment import run_multi_thread_experiment


def test_vulnerable_multi_thread_run_detects_cycle_and_starts_every_worker():
    result = run_multi_thread_experiment(
        mode="vulnerable",
        thread_count=6,
        timeout_seconds=3.0,
        trial_id="multi-vulnerable-test",
    )

    assert result.status == "deadlock"
    assert result.deadlock_detected is True
    assert result.metrics.threads_started == 6
    assert result.metrics.threads_completed == 4
    assert result.metrics.deadlock_cycle == ["T1", "T2", "T1"]
    assert result.completion_time_ms < 3000
    assert any(event.action == "deadlock_detected" for event in result.events)
    assert {event.thread for event in result.events if event.thread != "system"} == {
        "T1", "T2", "T3", "T4", "T5", "T6"
    }


def test_protected_multi_thread_run_completes_all_workers_without_cycle():
    result = run_multi_thread_experiment(
        mode="protected",
        thread_count=8,
        timeout_seconds=3.0,
        trial_id="multi-protected-test",
    )

    assert result.status == "completed"
    assert result.deadlock_detected is False
    assert result.metrics.threads_started == 8
    assert result.metrics.threads_completed == 8
    assert result.metrics.deadlock_cycle is None
    assert result.events[-1].action == "complete"


def test_multi_thread_count_is_bounded():
    try:
        run_multi_thread_experiment(mode="protected", thread_count=13)
    except ValueError as exc:
        assert "between 3 and 12" in str(exc)
    else:
        raise AssertionError("Thread counts above the supported range must be rejected.")
