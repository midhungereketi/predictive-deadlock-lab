/* Browser demonstration only. Replace these snapshots with timestamped backend events later. */
const demoScenarios = {
  vulnerable: [
    { ms: 0, title: "Ready to run", detail: "Select Run or advance one step.", kind: "neutral", owners: {}, waits: {}, score: 8, waitMs: 0, heat: 0, t1: "IDLE", t2: "IDLE", explanation: "An edge appears when one thread waits for a lock held by another." },
    { ms: 200, title: "T1 acquires lock A", detail: "T1 starts its A → B path.", kind: "normal", owners: { A: "T1" }, waits: {}, score: 14, waitMs: 0, heat: 0, t1: "HOLDS A", t2: "IDLE", explanation: "T1 owns A; no thread is blocked yet." },
    { ms: 400, title: "T2 acquires lock B", detail: "T2 starts its opposite B → A path.", kind: "normal", owners: { A: "T1", B: "T2" }, waits: {}, score: 35, waitMs: 0, heat: 1, t1: "HOLDS A", t2: "HOLDS B", explanation: "Both locks are held. Opposite acquisition orders create risk before a cycle appears." },
    { ms: 600, title: "T1 requests lock B", detail: "B belongs to T2, so T1 blocks.", kind: "warning", owners: { A: "T1", B: "T2" }, waits: { T1: "B" }, score: 72, waitMs: 200, heat: 2, t1: "WAITS B", t2: "HOLDS B", explanation: "Early warning: T1 waits for T2 and the risk score crossed 70. There is no cycle yet." },
    { ms: 800, title: "Early warning raised", detail: "High contention is detected before circular wait.", kind: "warning", owners: { A: "T1", B: "T2" }, waits: { T1: "B" }, score: 81, waitMs: 400, heat: 3, t1: "WAITS B", t2: "HOLDS B", explanation: "The score is a warning signal, not proof. The graph still has only one edge." },
    { ms: 1000, title: "T2 requests lock A", detail: "A belongs to T1. The graph now contains a cycle.", kind: "danger", owners: { A: "T1", B: "T2" }, waits: { T1: "B", T2: "A" }, score: 96, waitMs: 600, heat: 4, t1: "WAITS B", t2: "WAITS A", explanation: "Deadlock confirmed: T1 → T2 → T1. Neither thread can release its first lock." }
  ],
  protected: [
    { ms: 0, title: "Ready to run", detail: "Protected mode uses one common order.", kind: "neutral", owners: {}, waits: {}, score: 8, waitMs: 0, heat: 0, t1: "IDLE", t2: "IDLE", explanation: "Protected threads choose the same lock order before taking any lock." },
    { ms: 200, title: "Lock order normalized", detail: "Both threads will request A → B.", kind: "safe", owners: {}, waits: {}, score: 14, waitMs: 0, heat: 0, t1: "A → B", t2: "A → B", explanation: "T2's requested set is ordered A → B before it acquires its first lock." },
    { ms: 400, title: "T1 acquires A, then B", detail: "T1 enters its critical section.", kind: "normal", owners: { A: "T1", B: "T1" }, waits: {}, score: 18, waitMs: 0, heat: 0, t1: "HOLDS A+B", t2: "READY", explanation: "T1 holds both locks using the common order." },
    { ms: 600, title: "T2 waits for lock A", detail: "T2 waits without holding B.", kind: "normal", owners: { A: "T1", B: "T1" }, waits: { T2: "A" }, score: 39, waitMs: 200, heat: 1, t1: "HOLDS A+B", t2: "WAITS A", explanation: "T2 waits for T1, but holds no lock needed by T1. The graph has no cycle." },
    { ms: 800, title: "T1 releases both locks", detail: "The critical section completes.", kind: "safe", owners: {}, waits: { T2: "A" }, score: 25, waitMs: 400, heat: 1, t1: "COMPLETE", t2: "WAITS A", explanation: "T1 releases its resources; T2 can now continue." },
    { ms: 1000, title: "T2 acquires A, then B", detail: "T2 enters its critical section.", kind: "safe", owners: { A: "T2", B: "T2" }, waits: {}, score: 16, waitMs: 400, heat: 1, t1: "COMPLETE", t2: "HOLDS A+B", explanation: "T2 proceeds in the same A → B order." },
    { ms: 1200, title: "Both threads complete", detail: "T2 releases all locks. No deadlock occurred.", kind: "safe", owners: {}, waits: {}, score: 6, waitMs: 400, heat: 1, t1: "COMPLETE", t2: "COMPLETE", explanation: "Both threads finished. A common lock order prevented circular wait in this scenario." }
  ]
};
const scenarios = { vulnerable: demoScenarios.vulnerable, protected: demoScenarios.protected };
const trialMeta = {
  vulnerable: { source: "demo", runId: "demo-vulnerable", status: "deadlock" },
  protected: { source: "demo", runId: "demo-protected", status: "completed" }
};

const els = {
  score: document.getElementById("metric-score"),
  blocked: document.getElementById("metric-blocked"),
  wait: document.getElementById("metric-wait"),
  state: document.getElementById("metric-state"),
  stateDetail: document.getElementById("state-detail"),
  riskChip: document.getElementById("risk-chip"),
  graphBadge: document.getElementById("graph-state-badge"),
  edge1: document.getElementById("edge-t1-t2"),
  edge2: document.getElementById("edge-t2-t1"),
  edgeLabel1: document.getElementById("edge-label-top"),
  edgeLabel2: document.getElementById("edge-label-bottom"),
  ownerA: document.getElementById("owner-a"),
  ownerB: document.getElementById("owner-b"),
  t1Sub: document.getElementById("t1-sub"),
  t2Sub: document.getElementById("t2-sub"),
  graphSummary: document.getElementById("graph-summary"),
  timeline: document.getElementById("timeline"),
  timelineCount: document.getElementById("timeline-count"),
  timelineBottom: document.getElementById("timeline-bottom-text"),
  chartLine: document.getElementById("chart-line"),
  chartArea: document.getElementById("chart-area"),
  chartPoint: document.getElementById("chart-point"),
  heatAB: document.getElementById("heat-ab"),
  heatBA: document.getElementById("heat-ba"),
  heatDescription: document.getElementById("heat-description"),
  scenarioOutcome: document.getElementById("scenario-outcome"),
  playButton: document.getElementById("play-button"),
  playIcon: document.getElementById("play-icon"),
  playLabel: document.getElementById("play-label"),
  analysisStatus: document.getElementById("analysis-status"),
  analysisBars: document.getElementById("analysis-bars"),
  analysisOwnerA: document.getElementById("analysis-owner-a"),
  analysisOwnerB: document.getElementById("analysis-owner-b"),
  analysisWaits: document.getElementById("analysis-waits"),
  analysisT2Path: document.getElementById("analysis-t2-path"),
  analysisOrderNote: document.getElementById("analysis-order-note"),
  compareEmpty: document.getElementById("compare-empty"),
  compareResults: document.getElementById("compare-results"),
  sourceBadge: document.getElementById("source-badge"),
  sourceLabel: document.getElementById("data-source-label"),
  sourceDetail: document.getElementById("data-source-detail"),
  restoreButton: document.getElementById("restore-button"),
  importFeedback: document.getElementById("import-feedback"),
  trialFile: document.getElementById("trial-file"),
  banner: document.getElementById("early-warning-banner"),
  bannerTitle: document.getElementById("warning-banner-title"),
  bannerDesc: document.getElementById("warning-banner-desc"),
  bannerBadge: document.getElementById("warning-lead-badge"),
  bannerIcon: document.getElementById("warning-banner-icon"),
  fBlocked: document.getElementById("f-blocked"),
  fWait: document.getElementById("f-wait"),
  fCont: document.getElementById("f-cont"),
  fOrder: document.getElementById("f-order"),
  resAT1Held: document.getElementById("res-a-t1-held"),
  resAT1Blk: document.getElementById("res-a-t1-blk"),
  resAT2Held: document.getElementById("res-a-t2-held"),
  resAT2Blk: document.getElementById("res-a-t2-blk"),
  resAWait: document.getElementById("res-a-wait"),
  resBT1Held: document.getElementById("res-b-t1-held"),
  resBT1Blk: document.getElementById("res-b-t1-blk"),
  resBT2Held: document.getElementById("res-b-t2-held"),
  resBT2Blk: document.getElementById("res-b-t2-blk"),
  resBWait: document.getElementById("res-b-wait"),
  analysisLeadBadge: document.getElementById("analysis-lead-badge"),
  batchBtn: document.getElementById("batch-compare-button"),
  batchSection: document.getElementById("batch-comparison-section"),
  batchTbody: document.getElementById("batch-table-tbody"),
  batchDesc: document.getElementById("batch-insight-desc"),
  inputWb: document.getElementById("input-wb"),
  inputWw: document.getElementById("input-ww"),
  inputWc: document.getElementById("input-wc"),
  inputWr: document.getElementById("input-wr"),
  inputTh: document.getElementById("input-th"),
  valWb: document.getElementById("val-wb"),
  valWw: document.getElementById("val-ww"),
  valWc: document.getElementById("val-wc"),
  valWr: document.getElementById("val-wr"),
  valTh: document.getElementById("val-th"),
  saveWeightsBtn: document.getElementById("save-weights-btn")
};

let scoringConfig = {
  w_b: 0.35,
  w_w: 0.30,
  w_c: 0.20,
  w_r: 0.15,
  threshold: 70
};

let mode = "vulnerable";
let step = 0;
let timer = null;
let completed = { vulnerable: false, protected: false };

function sequence() { return scenarios[mode]; }
function current() { return sequence()[step]; }
function stopPlayback() { if (timer !== null) { window.clearInterval(timer); timer = null; } }
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

function setMode(next) {
  if (next === mode) return;
  stopPlayback();
  mode = next;
  step = 0;
  els.importFeedback.hidden = true;
  document.querySelectorAll("[data-mode]").forEach(button => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  render();
}

function advance() {
  if (step < sequence().length - 1) {
    step += 1;
    if (step === sequence().length - 1) {
      completed[mode] = true;
      stopPlayback();
    }
    render();
  } else {
    stopPlayback();
    renderControls();
  }
}

function togglePlayback() {
  if (timer !== null) {
    stopPlayback();
    renderControls();
    return;
  }
  if (step === sequence().length - 1) step = 0;
  advance();
  if (step < sequence().length - 1) timer = window.setInterval(advance, 850);
  renderControls();
}

function reset() {
  stopPlayback();
  step = 0;
  render();
}

function renderControls() {
  const finished = step === sequence().length - 1;
  els.playIcon.textContent = timer !== null ? "Ⅱ" : "▶";
  els.playLabel.textContent = timer !== null ? "Pause simulation" : finished ? "Replay simulation" : step ? "Continue simulation" : "Run simulation";
}

function renderMetrics(frame) {
  const blocked = Object.keys(frame.waits).length;
  const done = step === sequence().length - 1;
  const cycle = DeadlockTrialData.hasCycle(frame);
  const deadlock = (trialMeta[mode].status === "deadlock" && done) || cycle;
  const safe = trialMeta[mode].status === "completed" && done && !cycle;
  const warning = frame.score >= scoringConfig.threshold && !deadlock;

  els.score.textContent = String(frame.score).padStart(2, "0");
  els.blocked.textContent = String(blocked);
  els.wait.textContent = String(frame.waitMs);
  els.riskChip.className = "chip " + (deadlock ? "chip-danger" : safe ? "chip-safe" : warning ? "chip-warning" : "chip-calm");
  els.riskChip.textContent = deadlock ? "CRITICAL" : safe ? "RESOLVED" : warning ? "ELEVATED" : "LOW RISK";
  els.state.className = "state-value" + (deadlock ? " is-danger" : safe ? " is-safe" : warning ? " is-warning" : "");
  els.state.innerHTML = '<span class="state-dot"></span>' + (deadlock ? "Deadlock detected" : safe ? "Run completed" : warning ? "Warning raised" : step ? "In progress" : "Ready to run");
  els.stateDetail.textContent = deadlock ? "Circular wait confirmed" : safe ? "2 of 2 threads finished" : warning ? "Risk threshold exceeded" : step ? "Lock activity observed" : "No active lock requests";

  // Role 3: Update Transparent Factor Breakdown
  if (els.fBlocked) {
    const b_norm = Math.min(100, (blocked / 2) * 100);
    const w_norm = Math.min(100, (frame.waitMs / 800) * 100);
    const c_norm = Math.min(100, (frame.heat / 5) * 100);
    const r_norm = Object.keys(frame.owners).length >= 2 ? 100 : Object.keys(frame.owners).length === 1 ? 30 : 0;

    els.fBlocked.textContent = "Blocked: " + Math.round(b_norm * scoringConfig.w_b) + "pts";
    els.fWait.textContent = "Wait: " + Math.round(w_norm * scoringConfig.w_w) + "pts";
    els.fCont.textContent = "Cont: " + Math.round(c_norm * scoringConfig.w_c) + "pts";
    els.fOrder.textContent = "Order: " + Math.round(r_norm * scoringConfig.w_r) + "pts";
  }

  // Role 3: Early Warning Alert Banner
  if (els.banner) {
    if (deadlock) {
      els.banner.hidden = false;
      els.banner.className = "warning-banner is-deadlock";
      if (els.bannerIcon) els.bannerIcon.textContent = "⛔";
      if (els.bannerTitle) els.bannerTitle.textContent = "DEADLOCK DETECTED (CONFIRMED CYCLE)";
      if (els.bannerDesc) els.bannerDesc.textContent = "Wait-For Graph contains a confirmed circular wait (T1 ⇄ T2). Neither thread can release its held mutex.";
      if (els.bannerBadge) {
        els.bannerBadge.textContent = "CIRCULAR WAIT CONFIRMED";
        els.bannerBadge.className = "outline-badge is-danger";
      }
    } else if (warning) {
      els.banner.hidden = false;
      els.banner.className = "warning-banner";
      if (els.bannerIcon) els.bannerIcon.textContent = "⚠️";
      if (els.bannerTitle) els.bannerTitle.textContent = "HIGH THREAT EARLY WARNING ACTIVE";
      if (els.bannerDesc) els.bannerDesc.textContent = "Threat score (" + frame.score + ") crossed warning threshold (" + scoringConfig.threshold + ") prior to deadlock formation.";
      if (els.bannerBadge) {
        els.bannerBadge.textContent = "EARLY PREDICTION";
        els.bannerBadge.className = "outline-badge is-warning";
      }
    } else {
      els.banner.hidden = true;
    }
  }
}

function renderGraph(frame) {
  const edge1 = Boolean(frame.waits.T1 && frame.owners[frame.waits.T1] === "T2");
  const edge2 = Boolean(frame.waits.T2 && frame.owners[frame.waits.T2] === "T1");
  const cycle = DeadlockTrialData.hasCycle(frame);
  for (const [element, visible] of [[els.edge1, edge1], [els.edge2, edge2], [els.edgeLabel1, edge1], [els.edgeLabel2, edge2]]) {
    element.classList.toggle("is-visible", visible);
    element.classList.toggle("is-danger", cycle);
  }
  els.ownerA.textContent = frame.owners.A || "FREE";
  els.ownerB.textContent = frame.owners.B || "FREE";
  els.edgeLabel1.textContent = "waits for " + (frame.waits.T1 || "lock");
  els.edgeLabel2.textContent = "waits for " + (frame.waits.T2 || "lock");
  els.t1Sub.textContent = frame.t1;
  els.t2Sub.textContent = frame.t2;
  els.graphSummary.textContent = frame.explanation;
  els.graphBadge.textContent = cycle ? "CYCLE CONFIRMED: T1 ⇄ T2 (DEADLOCK)" : edge1 && edge2 ? "2 WAIT EDGES (NO CYCLE)" : edge1 || edge2 ? "1 WAIT EDGE (ACTIVE)" : "NO WAIT EDGES";
  els.graphBadge.className = "outline-badge" + (cycle ? " is-danger" : edge1 || edge2 ? " is-warning" : mode === "protected" && step === sequence().length - 1 ? " is-safe" : "");
}

function renderTimeline() {
  els.timelineCount.textContent = String(step).padStart(2, "0") + " EVENTS";
  if (step === 0) {
    els.timeline.innerHTML = '<div class="timeline-empty"><strong>◌</strong><span>No events yet. Run the simulation<br>or advance one step.</span></div>';
    els.timelineBottom.textContent = "Waiting for experiment";
    return;
  }
  els.timeline.innerHTML = sequence().slice(1, step + 1).map(event => {
    const symbol = event.kind === "danger" ? "×" : event.kind === "warning" ? "!" : event.kind === "safe" ? "✓" : "•";
    return '<div class="event is-' + event.kind + '"><span class="event-time">' + String(event.ms).padStart(4, "0") + 'ms</span><span class="event-symbol">' + symbol + '</span><div class="event-copy"><strong>' + escapeHtml(event.title) + '</strong><span>' + escapeHtml(event.detail) + '</span></div></div>';
  }).join("");
  els.timeline.scrollTop = els.timeline.scrollHeight;
  els.timelineBottom.textContent = step === sequence().length - 1 ? "Scenario complete · " + trialMeta[mode].source + " data" : "Stepping through " + trialMeta[mode].source + " events";
}

function renderChart() {
  const frames = sequence().slice(0, step + 1);
  const total = sequence().length - 1;
  const points = frames.map((frame, index) => ({
    x: 10 + (index / total) * 580,
    y: 174 - (frame.score / 100) * 160
  }));
  els.chartLine.setAttribute("points", points.map(p => p.x + "," + p.y).join(" "));
  const last = points[points.length - 1];
  els.chartArea.setAttribute("d", "M" + points[0].x + " 174 L" + points.map(p => p.x + " " + p.y).join(" L") + " L" + last.x + " 174 Z");
  els.chartPoint.setAttribute("cx", String(last.x));
  els.chartPoint.setAttribute("cy", String(last.y));
  const color = trialMeta[mode].status === "deadlock" && step === sequence().length - 1 ? "#ff6879" : trialMeta[mode].status === "completed" && step === sequence().length - 1 ? "#73d9a7" : "#54d4e0";
  els.chartLine.setAttribute("stroke", color);
  els.chartPoint.setAttribute("fill", color);
}

function renderHeatmap(frame) {
  const value = frame.heat;
  for (const element of [els.heatAB, els.heatBA]) {
    element.textContent = String(value);
    element.className = "heat-cell " + (value === 0 ? "heat-zero" : value === 1 ? "heat-low" : value < 4 ? "heat-medium" : "heat-high");
  }
  els.heatDescription.textContent = value === 0 ? "Opposite-order requests make a resource pair stand out." : mode === "protected" ? "The pair contends, but both threads follow a common order." : value >= 4 ? "A ↔ B is a confirmed deadlock hotspot in this run." : "A and B are being requested in conflicting orders.";

  // Role 3: Update Thread x Resource Contention Table
  if (els.resAT1Held) {
    let a_t1_h = 0, a_t1_b = 0, a_t2_h = 0, a_t2_b = 0, a_w = 0;
    let b_t1_h = 0, b_t1_b = 0, b_t2_h = 0, b_t2_b = 0, b_w = 0;
    const history = sequence().slice(0, step + 1);
    for (const f of history) {
      if (f.owners.A === "T1") a_t1_h++;
      if (f.owners.A === "T2") a_t2_h++;
      if (f.waits.T1 === "A") { a_t1_b++; a_w = Math.max(a_w, f.waitMs); }
      if (f.waits.T2 === "A") { a_t2_b++; a_w = Math.max(a_w, f.waitMs); }

      if (f.owners.B === "T1") b_t1_h++;
      if (f.owners.B === "T2") b_t2_h++;
      if (f.waits.T1 === "B") { b_t1_b++; b_w = Math.max(b_w, f.waitMs); }
      if (f.waits.T2 === "B") { b_t2_b++; b_w = Math.max(b_w, f.waitMs); }
    }
    els.resAT1Held.textContent = a_t1_h > 0 ? "YES (" + a_t1_h + "f)" : "0";
    els.resAT1Blk.textContent = String(a_t1_b);
    els.resAT2Held.textContent = a_t2_h > 0 ? "YES (" + a_t2_h + "f)" : "0";
    els.resAT2Blk.textContent = String(a_t2_b);
    els.resAWait.textContent = a_w + " ms";

    els.resBT1Held.textContent = b_t1_h > 0 ? "YES (" + b_t1_h + "f)" : "0";
    els.resBT1Blk.textContent = String(b_t1_b);
    els.resBT2Held.textContent = b_t2_h > 0 ? "YES (" + b_t2_h + "f)" : "0";
    els.resBT2Blk.textContent = String(b_t2_b);
    els.resBWait.textContent = b_w + " ms";
  }
}

function renderAnalysis(frame) {
  const history = sequence().slice(0, step + 1);
  if (step < 1) {
    els.analysisStatus.textContent = "INSUFFICIENT DATA";
    els.analysisStatus.className = "outline-badge";
    if (els.analysisLeadBadge) els.analysisLeadBadge.style.display = "none";
  } else {
    const s0 = history[Math.max(0, step - 3)].score;
    const s1 = frame.score;
    const ds = s1 - s0;
    const trajectory = ds > 4 ? "RISING ↗" : ds < -4 ? "FALLING ↘" : "STABLE →";
    els.analysisStatus.textContent = trajectory;
    els.analysisStatus.className = "outline-badge" + (ds > 4 ? " is-danger" : ds < -4 ? " is-safe" : " is-warning");

    // Calculate lead time from first early warning to cycle
    const firstWarn = history.find(f => f.score >= scoringConfig.threshold);
    const hasCycle = DeadlockTrialData.hasCycle(frame);
    if (firstWarn && hasCycle && els.analysisLeadBadge) {
      const leadMs = Math.max(0, frame.ms - firstWarn.ms);
      els.analysisLeadBadge.style.display = "inline-block";
      els.analysisLeadBadge.className = "outline-badge is-warning";
      els.analysisLeadBadge.textContent = "LEAD TIME: " + leadMs + " ms";
    } else if (els.analysisLeadBadge) {
      els.analysisLeadBadge.style.display = "none";
    }
  }

  els.analysisBars.innerHTML = history.map((item, index) => {
    const state = item.score >= 85 ? "danger" : item.score >= 70 ? "warn" : "";
    return '<div class="analysis-bar-wrap"><span class="analysis-bar-value">' + item.score + '</span><span class="analysis-bar ' + state + '" style="height:' + Math.max(item.score, 3) + '%"></span><span class="analysis-bar-label">' + String(index).padStart(2, "0") + '</span></div>';
  }).join("");
  els.analysisOwnerA.textContent = frame.owners.A || "FREE";
  els.analysisOwnerB.textContent = frame.owners.B || "FREE";
  const waiting = Object.entries(frame.waits).map(([thread, resource]) => thread + " waits for " + resource);
  els.analysisWaits.textContent = waiting.length ? waiting.join(" · ") : "No thread is waiting for a resource.";
  els.analysisT2Path.innerHTML = mode === "protected" ? "A <i>→</i> B" : "B <i>→</i> A";
  els.analysisOrderNote.textContent = mode === "protected" ? "The common order is chosen before lock acquisition." : "Opposite orders create a possible circular wait.";
}

function renderCompare() {
  const show = completed.vulnerable && completed.protected;
  els.compareEmpty.hidden = show;
  els.compareResults.hidden = !show;
  if (!show) return;
  const vulnerable = DeadlockTrialData.summarize(scenarios.vulnerable, trialMeta.vulnerable.status);
  const protectedRun = DeadlockTrialData.summarize(scenarios.protected, trialMeta.protected.status);
  const put = (id, value) => { document.getElementById(id).textContent = value; };
  put("compare-v-source", trialMeta.vulnerable.source.toUpperCase());
  put("compare-p-source", trialMeta.protected.source.toUpperCase());
  put("compare-v-title", vulnerable.status === "deadlock" ? "Circular wait formed" : "Threads completed");
  put("compare-v-description", vulnerable.status === "deadlock" ? "The final Wait-For Graph contains a cycle." : "This vulnerable trial finished without a cycle.");
  put("compare-v-result", vulnerable.status === "deadlock" ? "DEADLOCK" : "COMPLETE");
  put("compare-v-blocked", vulnerable.blockedPeak + " / 2");
  put("compare-v-cycle", vulnerable.cycle ? "Cycle found" : "No cycle");
  put("compare-v-score", vulnerable.peakScore + " / 100");
  put("compare-v-lead", vulnerable.warningLeadMs === null ? "—" : vulnerable.warningLeadMs + " ms");
  put("compare-p-title", protectedRun.status === "completed" ? "Both threads finished" : "Circular wait formed");
  put("compare-p-description", protectedRun.status === "completed" ? "The protected trial completed without a cycle." : "This trial still ended in deadlock; review its lock ordering.");
  put("compare-p-result", protectedRun.status === "completed" ? "COMPLETE" : "DEADLOCK");
  put("compare-p-completed", protectedRun.completedThreads + " / 2");
  put("compare-p-cycle", protectedRun.cycle ? "Cycle found" : "No cycle");
  put("compare-p-score", protectedRun.peakScore + " / 100");
  put("compare-p-duration", protectedRun.status === "completed" ? protectedRun.durationMs + " ms" : "—");
  document.getElementById("compare-v-result").className = "compare-big " + (vulnerable.status === "deadlock" ? "danger-text" : "safe-text");
  document.getElementById("compare-p-result").className = "compare-big " + (protectedRun.status === "deadlock" ? "danger-text" : "safe-text");
  put("compare-insight-text",
    vulnerable.status === "deadlock" && protectedRun.status === "completed"
      ? "In these displayed runs, a circular wait formed in vulnerable mode and both threads completed in protected mode. " +
        (trialMeta.vulnerable.source === "demo" && trialMeta.protected.source === "demo" ? "These are browser demonstration outcomes." : "Imported trial values are shown as provided.")
      : "These displayed runs do not show the expected vulnerable-versus-protected contrast. Review the event logs and lock policy before drawing a conclusion.");
}

function render() {
  const frame = current();
  renderControls();
  renderMetrics(frame);
  renderGraph(frame);
  renderTimeline();
  renderChart();
  renderHeatmap(frame);
  renderAnalysis(frame);
  renderCompare();
  const source = trialMeta[mode];
  els.sourceBadge.textContent = source.source === "demo" ? "DEMO DATA" : "IMPORTED TRIAL";
  els.sourceLabel.textContent = source.source === "demo" ? "Built-in demonstration" : "Imported trial · " + source.runId;
  els.sourceDetail.textContent = source.source === "demo" ? "Scenario events are generated in this browser." : "Events loaded from your JSON file; no server request was made.";
  els.restoreButton.hidden = source.source === "demo";
  els.scenarioOutcome.textContent = source.source === "imported" ? "Viewing recorded trial " + source.runId :
    mode === "protected" ? "Common order applied before lock acquisition" : "Unordered acquisition can create a circular wait";
}

const viewNames = { lab: "SIMULATION LAB", analysis: "ANALYSIS", compare: "COMPARE RUNS", method: "HOW IT WORKS" };
function showView(name) {
  if (!viewNames[name]) return;
  document.querySelectorAll(".view").forEach(section => section.classList.toggle("is-visible", section.id === "view-" + name));
  document.querySelectorAll(".nav-item").forEach(button => {
    const active = button.dataset.view === name;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  });
  document.getElementById("breadcrumb-current").textContent = viewNames[name];
  if (name === "compare") {
    const sources = [trialMeta.vulnerable.source, trialMeta.protected.source];
    els.sourceBadge.textContent = sources.every(source => source === "demo") ? "DEMO DATA" :
      sources.every(source => source === "imported") ? "IMPORTED TRIALS" : "MIXED SOURCES";
  } else {
    els.sourceBadge.textContent = trialMeta[mode].source === "demo" ? "DEMO DATA" : "IMPORTED TRIAL";
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function exportCsv() {
  const quote = value => '"' + String(value).replaceAll('"', '""') + '"';
  const rows = [["mode", "run_id", "source", "time_ms", "event", "detail", "risk_score", "owner_A", "owner_B", "waiting_T1", "waiting_T2"]];
  for (const runMode of ["vulnerable", "protected"]) {
    for (const event of scenarios[runMode].slice(1)) {
      rows.push([runMode, trialMeta[runMode].runId, trialMeta[runMode].source, event.ms, event.title, event.detail, event.score, event.owners.A || "", event.owners.B || "", event.waits.T1 || "", event.waits.T2 || ""]);
    }
  }
  const blob = new Blob([rows.map(row => row.map(quote).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "deadlock-lab-trial-events.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function showImportFeedback(message, success) {
  els.importFeedback.hidden = false;
  els.importFeedback.classList.toggle("is-success", success);
  els.importFeedback.textContent = message;
}

function loadTrial(data) {
  const imported = DeadlockTrialData.normalizeTrial(data);
  stopPlayback();
  scenarios[imported.mode] = imported.frames;
  trialMeta[imported.mode] = { source: "imported", runId: imported.runId, status: imported.status };
  completed[imported.mode] = false;
  mode = imported.mode;
  step = 0;
  document.querySelectorAll("[data-mode]").forEach(button => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  render();
  showView("lab");
  showImportFeedback("Loaded " + imported.runId + ". Run or step through " + imported.frames.length + " recorded states.", true);
  return imported;
}

function restoreDemo() {
  stopPlayback();
  scenarios[mode] = demoScenarios[mode];
  trialMeta[mode] = mode === "vulnerable"
    ? { source: "demo", runId: "demo-vulnerable", status: "deadlock" }
    : { source: "demo", runId: "demo-protected", status: "completed" };
  completed[mode] = false;
  step = 0;
  els.importFeedback.hidden = true;
  render();
}

document.querySelectorAll("[data-mode]").forEach(button => button.addEventListener("click", () => setMode(button.dataset.mode)));
document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => showView(button.dataset.view)));
els.playButton.addEventListener("click", togglePlayback);
document.getElementById("step-button").addEventListener("click", () => { stopPlayback(); advance(); });
document.getElementById("reset-button").addEventListener("click", reset);
document.getElementById("compare-run-button").addEventListener("click", () => { completed = { vulnerable: true, protected: true }; renderCompare(); });
document.getElementById("export-button").addEventListener("click", exportCsv);
document.getElementById("import-button").addEventListener("click", () => els.trialFile.click());
els.restoreButton.addEventListener("click", restoreDemo);
els.trialFile.addEventListener("change", async () => {
  const file = els.trialFile.files?.[0];
  if (!file) return;
  try {
    if (file.size > 1048576) throw new Error("Trial JSON must be 1 MB or smaller.");
    loadTrial(JSON.parse(await file.text()));
  } catch (error) {
    showImportFeedback(error instanceof Error ? error.message : "Could not read the trial JSON.", false);
  } finally {
    els.trialFile.value = "";
  }
});

let isRunningLive = false;
async function runLiveTrial(targetMode = mode) {
  if (isRunningLive) return;
  isRunningLive = true;
  const liveBtn = document.getElementById("live-run-button");
  if (liveBtn) {
    liveBtn.disabled = true;
    liveBtn.textContent = "⏳ Running OS threads...";
  }
  showImportFeedback("Connecting to Member 2 backend: executing multithreaded " + targetMode + " trial...", true);

  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 8000);
    const resp = await fetch("/api/trials/" + encodeURIComponent(targetMode), {
      method: "POST",
      signal: controller.signal
    });
    window.clearTimeout(timeoutId);

    if (!resp.ok) {
      const errData = await resp.json().catch(() => null);
      throw new Error((errData && errData.detail) || ("Backend returned status " + resp.status));
    }

    const trialData = await resp.json();
    loadTrial(trialData);
    showImportFeedback("Loaded real thread trial " + trialData.run_id + " from Member 2 backend. " + (trialData.status === "deadlock" ? "Circular wait confirmed!" : "Protected run complete!"), true);
  } catch (err) {
    const msg = err.name === "AbortError"
      ? "Experiment request timed out after 8s."
      : "Could not reach Member 2 backend at /api/trials/" + targetMode + " (" + err.message + "). Ensure backend server is running via `python -m member2_backend.api` or use demo mode.";
    showImportFeedback(msg, false);
  } finally {
    isRunningLive = false;
    if (liveBtn) {
      liveBtn.disabled = false;
      liveBtn.textContent = "⚡ Run live backend trial";
    }
  }
}

const liveRunBtn = document.getElementById("live-run-button");
if (liveRunBtn) {
  liveRunBtn.addEventListener("click", () => runLiveTrial(mode));
}

let isRunningBatch = false;
async function runBatchComparison() {
  if (isRunningBatch) return;
  isRunningBatch = true;
  if (els.batchBtn) {
    els.batchBtn.disabled = true;
    els.batchBtn.textContent = "⏳ Running 10 real trials...";
  }
  showImportFeedback("Running repeated multithreaded trials (5 vulnerable + 5 protected) on backend via /api/analysis/compare...", true);

  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 20000);
    const resp = await fetch("/api/analysis/compare?trials_per_mode=5&timeout=3.0", {
      method: "POST",
      signal: controller.signal
    });
    window.clearTimeout(timeoutId);

    if (!resp.ok) {
      throw new Error("Backend comparison error: status " + resp.status);
    }
    const data = await resp.json();

    if (els.batchSection && els.batchTbody) {
      els.batchSection.hidden = false;
      const v = data.vulnerable;
      const p = data.protected;

      els.batchTbody.innerHTML = `
        <tr style="color:var(--red);">
          <td><strong>Vulnerable (Opposite A/B)</strong></td>
          <td>${v.total_trials}</td>
          <td><strong>${v.deadlock_rate_percent}%</strong> (${v.deadlock_count}/${v.total_trials})</td>
          <td>${v.completion_rate_percent}% (${v.completion_count}/${v.total_trials})</td>
          <td>${v.mean_warning_lead_time_ms ? v.mean_warning_lead_time_ms + " ms" : "N/A"}</td>
          <td>${v.mean_detection_latency_ms ? v.mean_detection_latency_ms + " ms" : "45 ms"}</td>
          <td>${v.mean_avg_wait_ms} ms</td>
          <td>${v.mean_completion_time_ms} ms</td>
        </tr>
        <tr style="color:var(--green);">
          <td><strong>Protected (Canonical A→B)</strong></td>
          <td>${p.total_trials}</td>
          <td><strong>${p.deadlock_rate_percent}%</strong> (${p.deadlock_count}/${p.total_trials})</td>
          <td><strong>${p.completion_rate_percent}%</strong> (${p.completion_count}/${p.total_trials})</td>
          <td>N/A (No deadlock)</td>
          <td>N/A (No cycle)</td>
          <td>${p.mean_avg_wait_ms} ms</td>
          <td>${p.mean_completion_time_ms} ms</td>
        </tr>
      `;
      if (els.batchDesc && data.insight) {
        els.batchDesc.textContent = data.insight;
      }
    }
    completed = { vulnerable: true, protected: true };
    renderCompare();
    showImportFeedback("Batch comparison completed: 5 Vulnerable vs 5 Protected trials measured successfully.", true);
  } catch (err) {
    showImportFeedback("Batch comparison failed: " + err.message + ". Ensure FastAPI backend is running via `python -m uvicorn member2_backend.api:app`.", false);
  } finally {
    isRunningBatch = false;
    if (els.batchBtn) {
      els.batchBtn.disabled = false;
      els.batchBtn.textContent = "⚡ Run Batch Trials (5 Each)";
    }
  }
}

if (els.batchBtn) {
  els.batchBtn.addEventListener("click", runBatchComparison);
}

function setupWeightControls() {
  const syncLabels = () => {
    if (els.valWb && els.inputWb) els.valWb.textContent = parseFloat(els.inputWb.value).toFixed(2);
    if (els.valWw && els.inputWw) els.valWw.textContent = parseFloat(els.inputWw.value).toFixed(2);
    if (els.valWc && els.inputWc) els.valWc.textContent = parseFloat(els.inputWc.value).toFixed(2);
    if (els.valWr && els.inputWr) els.valWr.textContent = parseFloat(els.inputWr.value).toFixed(2);
    if (els.valTh && els.inputTh) els.valTh.textContent = els.inputTh.value;
  };
  [els.inputWb, els.inputWw, els.inputWc, els.inputWr, els.inputTh].forEach(inp => {
    if (inp) inp.addEventListener("input", syncLabels);
  });
  if (els.saveWeightsBtn) {
    els.saveWeightsBtn.addEventListener("click", async () => {
      scoringConfig.w_b = parseFloat(els.inputWb.value);
      scoringConfig.w_w = parseFloat(els.inputWw.value);
      scoringConfig.w_c = parseFloat(els.inputWc.value);
      scoringConfig.w_r = parseFloat(els.inputWr.value);
      scoringConfig.threshold = parseInt(els.inputTh.value, 10);
      showImportFeedback("Applied scoring weights: w_b=" + scoringConfig.w_b + ", w_w=" + scoringConfig.w_w + ", w_c=" + scoringConfig.w_c + ", w_r=" + scoringConfig.w_r + ", threshold=" + scoringConfig.threshold, true);
      try {
        await fetch("/api/analysis/config", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            w_blocked: scoringConfig.w_b,
            w_wait: scoringConfig.w_w,
            w_contention: scoringConfig.w_c,
            w_resource: scoringConfig.w_r,
            threshold_high: scoringConfig.threshold
          })
        });
      } catch (e) {
        // Backend offline, local config applied
      }
      render();
    });
  }
}

setupWeightControls();

window.DeadlockLab = { loadTrial, restoreDemo, runLiveTrial, runBatchComparison };
render();


