"""Tests for EventLogger, schema enforcement, thread safety, and trial-v1 adapter.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

import json
from pathlib import Path
import threading
import jsonschema
import pytest

from member2_backend.event_logger import EventLogger
from member2_backend.experiment_runner import run_experiment, to_trial_v1
from member2_backend.schemas import Event


def test_event_schema_fields_and_monotonicity():
    """Verify that all events have exact schema fields and strictly non-decreasing times."""
    logger = EventLogger(trial_id="test-events", mode="vulnerable")

    e1 = logger.log_event("system", "start")
    e2 = logger.log_event("T1", "requested", resource="A")
    e3 = logger.log_event("T1", "acquired", resource="A", owner="T1")
    e4 = logger.log_event("T2", "waiting", resource="A", owner="T1", wait_ms=50)

    events = logger.get_events()
    assert len(events) == 4

    last_time = -1.0
    for e in events:
        d = e.model_dump()
        assert set(d.keys()) == {"time", "thread", "action", "resource", "owner", "wait_ms"}
        assert e.time >= last_time
        last_time = e.time


def test_event_logger_thread_safety_concurrent_writes():
    """Verify that concurrent writes from multiple threads do not corrupt the event list."""
    logger = EventLogger(trial_id="concurrent-test", mode="vulnerable")
    threads = []
    writes_per_thread = 50

    def writer(tid: str):
        for i in range(writes_per_thread):
            logger.log_event(thread=tid, action="requested", resource="A", wait_ms=i)

    for i in range(5):
        t = threading.Thread(target=writer, args=(f"T{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    events = logger.get_events()
    assert len(events) == 5 * writes_per_thread


def test_trial_v1_json_schema_compliance():
    """Verify that to_trial_v1 output passes Member 1's trial-v1.schema.json validation."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "contract" / "trial-v1.schema.json"
    assert schema_path.is_file(), f"Schema not found at {schema_path}"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Test vulnerable trial output
    vuln_res = run_experiment("vulnerable", timeout_seconds=2.5)
    vuln_v1 = to_trial_v1(vuln_res)
    jsonschema.validate(instance=vuln_v1, schema=schema)

    # Test protected trial output
    prot_res = run_experiment("protected", timeout_seconds=2.5)
    prot_v1 = to_trial_v1(prot_res)
    jsonschema.validate(instance=prot_v1, schema=schema)
