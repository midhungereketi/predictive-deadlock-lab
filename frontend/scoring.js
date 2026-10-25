/* Threat score formula shared by the dashboard and Node tests.
 * Mirrors member3_analysis/threat_scorer.py exactly (same operation order and
 * round-half-up); shared/scoring_cases.json is checked against both. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.DeadlockScoring = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const DEFAULTS = Object.freeze({ w_b: 0.35, w_w: 0.30, w_c: 0.20, w_r: 0.15, threshold: 70 });
  const LIMITS = Object.freeze({ maxThreads: 2, maxWaitMs: 800, maxContention: 5, lowThreshold: 40, inversionFloor: 72, cycleFloor: 96 });

  function weightSum(cfg) {
    return cfg.w_b + cfg.w_w + cfg.w_c + cfg.w_r;
  }

  function isValid(cfg) {
    const weights = [cfg.w_b, cfg.w_w, cfg.w_c, cfg.w_r];
    return weights.every(value => Number.isFinite(value) && value >= 0 && value <= 1) &&
      Math.abs(weightSum(cfg) - 1) <= 0.001 &&
      Number.isInteger(cfg.threshold) && cfg.threshold >= 1 && cfg.threshold <= 100;
  }

  // state: { owners: {lock: thread}, waits: {thread: lock}, waitMs, contention, cycle }
  function scoreState(state, cfg) {
    const blocked = Object.keys(state.waits).length;
    const holders = Object.values(state.owners);
    const held = holders.length, distinct = new Set(holders).size;
    const conflict = held >= 2 && distinct >= 2;
    const factors = [
      { label: "Blocked threads", weight: cfg.w_b, norm: Math.min(100, blocked / LIMITS.maxThreads * 100), raw: blocked + " of " + LIMITS.maxThreads + " threads blocked" },
      { label: "Wait duration", weight: cfg.w_w, norm: Math.min(100, state.waitMs / LIMITS.maxWaitMs * 100), raw: state.waitMs + " ms longest wait (full at " + LIMITS.maxWaitMs + " ms)" },
      { label: "Contention events", weight: cfg.w_c, norm: Math.min(100, state.contention / LIMITS.maxContention * 100), raw: state.contention + " contention events (full at " + LIMITS.maxContention + ")" },
      { label: "Lock conflict", weight: cfg.w_r, norm: conflict ? 100 : held >= 2 ? 40 : held === 1 ? 20 : 0,
        raw: conflict ? "A and B held by different threads" : held >= 2 ? "one thread holds both locks" : held === 1 ? "one lock held" : "no locks held" }
    ];
    factors.forEach(factor => { factor.points = factor.weight * factor.norm; });
    const total = factors.reduce((sum, factor) => sum + factor.points, 0);
    // Round half up, as the Python scorer does.
    let score = Math.floor(Math.max(0, Math.min(100, total)) + 0.5);
    let rule = "";
    if (!state.cycle && conflict && blocked >= 1 && score < LIMITS.inversionFloor) {
      score = LIMITS.inversionFloor;
      rule = "Lock-order rule: different threads hold A and B and one of them is waiting, so the score is raised to at least " + LIMITS.inversionFloor + ".";
    }
    if (state.cycle) {
      if (score < LIMITS.cycleFloor) rule = "Deadlock confirmed: the Wait-For Graph has a cycle, so the score is set to at least " + LIMITS.cycleFloor + ".";
      score = Math.max(score, LIMITS.cycleFloor);
    }
    const level = state.cycle ? "DEADLOCK" : score >= cfg.threshold ? "HIGH" : score >= LIMITS.lowThreshold ? "ELEVATED" : "LOW";
    return { factors, total, score, rule, cycle: Boolean(state.cycle), level, blocked };
  }

  return { DEFAULTS, LIMITS, weightSum, isValid, scoreState };
});
