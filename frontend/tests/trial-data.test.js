const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const trialDataPath = fs.existsSync(path.join(__dirname, "../dist/trial-data.js"))
  ? "../dist/trial-data.js"
  : "../trial-data.js";
const { normalizeTrial, summarize, hasCycle } = require(trialDataPath);

function example(name) {
  return JSON.parse(fs.readFileSync(path.join(__dirname, "../contract", name), "utf8"));
}

test("vulnerable trial records warning before a confirmed cycle", () => {
  const trial = normalizeTrial(example("vulnerable.example.json"));
  const result = summarize(trial.frames, trial.status);
  assert.equal(trial.mode, "vulnerable");
  assert.equal(trial.frames.length, 5);
  assert.equal(result.cycle, true);
  assert.equal(result.blockedPeak, 2);
  assert.equal(result.warningLeadMs, 400);
  assert.equal(result.peakScore, 96);
});

test("protected trial finishes without a circular wait", () => {
  const trial = normalizeTrial(example("protected.example.json"));
  const result = summarize(trial.frames, trial.status);
  assert.equal(result.cycle, false);
  assert.equal(result.completedThreads, 2);
  assert.equal(result.durationMs, 1200);
  assert.equal(result.peakScore, 39);
});

test("rejects an unowned wait and a false deadlock claim", () => {
  const invalidWait = example("vulnerable.example.json");
  invalidWait.events[3].owners = { A: "T1" };
  assert.throws(() => normalizeTrial(invalidWait), /wait for a resource held/);

  const falseDeadlock = example("vulnerable.example.json");
  falseDeadlock.events.at(-1).waits = { T1: "B" };
  assert.equal(hasCycle({ owners: falseDeadlock.events.at(-1).owners, waits: falseDeadlock.events.at(-1).waits }), false);
  assert.throws(() => normalizeTrial(falseDeadlock), /Wait-For Graph cycle/);
});

test("rejects out-of-order timestamps without modifying other trials", () => {
  const trial = example("protected.example.json");
  trial.events[3].timestamp_ms = 100;
  assert.throws(() => normalizeTrial(trial), /non-decreasing/);
});

