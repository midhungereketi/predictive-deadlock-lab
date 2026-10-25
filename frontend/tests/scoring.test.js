const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { DEFAULTS, isValid, scoreState } = require("../scoring.js");

const { cases } = JSON.parse(fs.readFileSync(path.join(__dirname, "../../shared/scoring_cases.json"), "utf8"));
const pythonLevel = { CRITICAL_DEADLOCK: "DEADLOCK", HIGH: "HIGH", ELEVATED: "ELEVATED", LOW: "LOW" };

test("browser scoring reproduces every shared Python case", () => {
  for (const item of cases) {
    const w = item.weights;
    const cfg = { w_b: w.w_blocked, w_w: w.w_wait, w_c: w.w_contention, w_r: w.w_resource, threshold: w.threshold_high };
    const s = item.state;
    const result = scoreState({ owners: s.owners, waits: s.waits, waitMs: s.wait_ms, contention: s.contention, cycle: s.cycle }, cfg);
    assert.equal(result.score, item.expected.score, item.name);
    assert.equal(result.level, pythonLevel[item.expected.level], item.name);
  }
});

test("weights are valid only when they total 1.00 and the threshold is an integer", () => {
  assert.ok(isValid(DEFAULTS));
  assert.ok(!isValid({ ...DEFAULTS, w_b: 0.6 }));
  assert.ok(!isValid({ ...DEFAULTS, threshold: 70.5 }));
});
