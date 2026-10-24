/* Shared frontend data contract. This file also runs under Node for contract checks. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.DeadlockTrialData = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const actions = new Set(["start", "request", "acquire", "wait", "release", "warning", "policy_applied", "deadlock_detected", "complete"]);
  const resources = new Set(["A", "B"]);
  const threads = new Set(["T1", "T2"]);

  function fail(message) { throw new Error("Trial JSON: " + message); }
  function object(value) { return value && typeof value === "object" && !Array.isArray(value); }
  function integer(value, min, max) { return Number.isInteger(value) && value >= min && value <= max; }
  function text(value, max) { return typeof value === "string" && value.length > 0 && value.length <= max; }

  function checkedMap(value, allowedKeys, allowedValues, label) {
    if (!object(value)) fail(label + " must be an object.");
    const result = {};
    for (const [key, item] of Object.entries(value)) {
      if (!allowedKeys.has(key) || !allowedValues.has(item)) fail(label + " contains an invalid " + key + " value.");
      result[key] = item;
    }
    return result;
  }

  function hasCycle(frame) {
    return frame.waits.T1 === "B" && frame.owners.B === "T2" &&
      frame.waits.T2 === "A" && frame.owners.A === "T1" ||
      frame.waits.T1 === "A" && frame.owners.A === "T2" &&
      frame.waits.T2 === "B" && frame.owners.B === "T1";
  }

  function threadLabel(thread, owners, waits, completed) {
    if (completed) return "COMPLETE";
    if (waits[thread]) return "WAITS " + waits[thread];
    const held = Object.keys(owners).filter(resource => owners[resource] === thread);
    return held.length ? "HOLDS " + held.join("+") : "READY";
  }

  function derivedTitle(event) {
    const actor = event.thread_id === "system" ? "System" : event.thread_id;
    const resource = event.resource_id ? " lock " + event.resource_id : "";
    return {
      start: "Trial started",
      request: actor + " requests" + resource,
      acquire: actor + " acquires" + resource,
      wait: actor + " waits for" + resource,
      release: actor + " releases" + resource,
      warning: "Early warning raised",
      policy_applied: "Common lock order applied",
      deadlock_detected: "Deadlock detected",
      complete: "Trial completed"
    }[event.action];
  }

  function normalizeTrial(input) {
    if (!object(input)) fail("the root must be an object.");
    if (input.schema_version !== 1) fail("schema_version must be 1.");
    if (!text(input.run_id, 80)) fail("run_id must be a non-empty string of at most 80 characters.");
    if (!["vulnerable", "protected"].includes(input.mode)) fail("mode must be vulnerable or protected.");
    if (!["deadlock", "completed"].includes(input.status)) fail("status must be deadlock or completed.");
    if (!Array.isArray(input.events) || input.events.length < 1 || input.events.length > 500) fail("events must contain 1–500 entries.");

    let previousTime = -1;
    const frames = input.events.map((event, index) => {
      if (!object(event)) fail("event " + (index + 1) + " must be an object.");
      if (!integer(event.timestamp_ms, 0, 3600000) || event.timestamp_ms < previousTime) fail("timestamps must be non-decreasing integers from 0 to 3,600,000 ms.");
      previousTime = event.timestamp_ms;
      if (!actions.has(event.action)) fail("event " + (index + 1) + " has an unsupported action.");
      if (!["T1", "T2", "system"].includes(event.thread_id)) fail("event " + (index + 1) + " needs thread_id T1, T2, or system.");
      if (event.resource_id !== null && event.resource_id !== undefined && !resources.has(event.resource_id)) fail("resource_id must be A, B, or null.");
      if (!integer(event.risk_score, 0, 100)) fail("risk_score must be an integer from 0 to 100.");
      if (!integer(event.wait_duration_ms, 0, 3600000)) fail("wait_duration_ms must be a non-negative integer.");
      if (!integer(event.contention_count, 0, 100000)) fail("contention_count must be a non-negative integer.");
      const owners = checkedMap(event.owners, resources, threads, "owners");
      const waits = checkedMap(event.waits, threads, resources, "waits");
      for (const [thread, resource] of Object.entries(waits)) {
        if (!owners[resource] || owners[resource] === thread) fail(thread + " must wait for a resource held by the other thread.");
      }
      if (event.title !== undefined && !text(event.title, 120)) fail("title must be 1–120 characters.");
      if (event.detail !== undefined && !text(event.detail, 300)) fail("detail must be 1–300 characters.");
      const completed = event.action === "complete";
      const cycle = hasCycle({ owners, waits });
      const explanation = cycle ? "Circular wait confirmed by the Wait-For Graph." :
        Object.keys(waits).length ? "A waiting edge is present, but there is no cycle." :
        completed ? "Both threads finished without a circular wait." :
        "No thread-to-thread waiting edge is present.";
      return {
        ms: event.timestamp_ms,
        title: event.title || derivedTitle(event),
        detail: event.detail || explanation,
        kind: cycle || event.action === "deadlock_detected" ? "danger" :
          event.action === "warning" || event.risk_score >= 70 ? "warning" :
          event.action === "complete" || event.action === "policy_applied" ? "safe" : "normal",
        owners, waits,
        score: event.risk_score,
        waitMs: event.wait_duration_ms,
        heat: event.contention_count,
        t1: threadLabel("T1", owners, waits, completed),
        t2: threadLabel("T2", owners, waits, completed),
        explanation
      };
    });

    const last = frames[frames.length - 1];
    if (input.status === "deadlock" && (!hasCycle(last) || input.events[input.events.length - 1].action !== "deadlock_detected")) {
      fail("a deadlock trial must end with deadlock_detected and a Wait-For Graph cycle.");
    }
    if (input.status === "completed" && (input.events[input.events.length - 1].action !== "complete" || Object.keys(last.waits).length || Object.keys(last.owners).length)) {
      fail("a completed trial must end with complete and no owned or awaited locks.");
    }
    if (frames[0].ms !== 0 || input.events[0].action !== "start") {
      frames.unshift({
        ms: 0, title: "Ready to run", detail: "Imported experiment data.",
        kind: "neutral", owners: {}, waits: {}, score: 0, waitMs: 0, heat: 0,
        t1: "IDLE", t2: "IDLE", explanation: "An edge appears when a thread waits for a lock held by another."
      });
    }
    return { runId: input.run_id, mode: input.mode, status: input.status, frames };
  }

  function summarize(frames, status) {
    const last = frames[frames.length - 1];
    const peakScore = Math.max(...frames.map(frame => frame.score));
    const blockedPeak = Math.max(...frames.map(frame => Object.keys(frame.waits).length));
    const warning = frames.find(frame => frame.score >= 70 && frame.ms < last.ms);
    return {
      status,
      peakScore,
      blockedPeak,
      completedThreads: status === "completed" ? 2 : 0,
      durationMs: last.ms,
      warningLeadMs: status === "deadlock" && warning ? last.ms - warning.ms : null,
      cycle: hasCycle(last)
    };
  }

  return { normalizeTrial, summarize, hasCycle };
});

