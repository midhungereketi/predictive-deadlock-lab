/* Built-in browser scenarios; live trials are loaded through the FastAPI endpoints below. */
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
  updateMultiThreadLabel();
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

  // Show the observed inputs. Weighted points need not equal the displayed
  // score when the controlled structural warning rule applies.
  if (els.fBlocked) {
    const splitOwners = Object.keys(frame.owners).length === 2 && new Set(Object.values(frame.owners)).size === 2;
    els.fBlocked.textContent = "Blocked: " + blocked + "/2";
    els.fWait.textContent = "Peak wait: " + frame.waitMs + " ms";
    els.fCont.textContent = "Conflicts: " + frame.heat;
    els.fOrder.textContent = "Split locks: " + (splitOwners ? "yes" : "no");
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
      if (els.bannerDesc) els.bannerDesc.textContent = "Threat score (" + frame.score + ") crossed warning threshold (" + scoringConfig.threshold + ") before a cycle was confirmed.";
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
  els.timeline.innerHTML = sequence().slice(1, step + 1).map((event, index) => {
    const symbol = event.kind === "danger" ? "×" : event.kind === "warning" ? "!" : event.kind === "safe" ? "✓" : "•";
    return '<div class="event is-' + event.kind + (index === step - 1 ? ' is-new' : '') + '"><span class="event-time">' + String(event.ms).padStart(4, "0") + 'ms</span><span class="event-symbol">' + symbol + '</span><div class="event-copy"><strong>' + escapeHtml(event.title) + '</strong><span>' + escapeHtml(event.detail) + '</span></div></div>';
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
  const thresholdY = 174 - (scoringConfig.threshold / 100) * 160;
  const thresholdLine = document.querySelector("#risk-chart .threshold-line");
  const thresholdLabel = document.querySelector("#risk-chart .threshold-label");
  thresholdLine.setAttribute("y1", String(thresholdY));
  thresholdLine.setAttribute("y2", String(thresholdY));
  thresholdLabel.setAttribute("y", String(Math.max(12, thresholdY - 8)));
  thresholdLabel.textContent = "WARNING THRESHOLD · " + scoringConfig.threshold;
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
  els.heatDescription.textContent = value === 0 ? "Opposite-order requests make a resource pair stand out." : DeadlockTrialData.hasCycle(frame) ? "A ↔ B forms a confirmed circular wait in this run." : mode === "protected" ? "The pair contends, but both threads follow a common order." : "A and B are being requested in conflicting orders.";

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

function render() {
  const frame = current();
  renderControls();
  renderMetrics(frame);
  renderGraph(frame);
  renderTimeline();
  renderChart();
  renderHeatmap(frame);
  renderAnalysisTab();
  renderCompare();
  const source = trialMeta[mode];
  els.sourceBadge.textContent = source.source === "demo" ? "DEMO DATA" : source.source === "live" ? "LIVE TRIAL" : "IMPORTED TRIAL";
  els.sourceLabel.textContent = source.source === "demo" ? "Built-in demonstration" : (source.source === "live" ? "Backend trial · " : "Imported trial · ") + source.runId;
  els.sourceDetail.textContent = source.source === "demo" ? "Scenario events are generated in this browser." : source.source === "live" ? "Recorded from real threads by the FastAPI backend." : "Events loaded from your JSON file; no server request was made.";
  els.restoreButton.hidden = source.source === "demo";
  els.scenarioOutcome.textContent = source.source !== "demo" ? "Viewing recorded trial " + source.runId :
    mode === "protected" ? "Common order applied before lock acquisition" : "Unordered acquisition can create a circular wait";
  const last = step === sequence().length - 1;
  const cycle = DeadlockTrialData.hasCycle(frame);
  document.dispatchEvent(new CustomEvent("lab:frame", { detail: {
    frame, mode, step, last, threshold: scoringConfig.threshold,
    state: cycle || (trialMeta[mode].status === "deadlock" && last) ? "danger"
      : trialMeta[mode].status === "completed" && last ? "safe"
      : frame.score >= scoringConfig.threshold ? "warning" : "calm"
  } }));
}

const viewNames = { lab: "SIMULATION LAB", analysis: "ANALYSIS", compare: "COMPARE RUNS", method: "HOW IT WORKS" };
function showView(name) {
  if (!viewNames[name]) return;
  if (document.startViewTransition && !showView.inTransition && !document.getElementById("view-" + name).classList.contains("is-visible")) {
    showView.inTransition = true;
    const transition = document.startViewTransition(() => applyView(name));
    // A skipped transition (fast clicks, background tab) rejects `ready`; the view still switches.
    transition.ready.catch(() => {});
    transition.finished.finally(() => { showView.inTransition = false; });
  } else {
    applyView(name);
  }
}

function applyView(name) {
  document.querySelectorAll(".view").forEach(section => section.classList.toggle("is-visible", section.id === "view-" + name));
  document.querySelectorAll(".nav-item").forEach(button => {
    const active = button.dataset.view === name;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  });
  document.getElementById("breadcrumb-current").textContent = viewNames[name];
  if (name === "compare") {
    const sources = [trialMeta.vulnerable.source, trialMeta.protected.source];
    els.sourceBadge.textContent = !els.batchSection.hidden ? "MEASURED BATCH" :
      sources.every(source => source === "demo") ? "DEMO DATA" :
      sources.every(source => source === "imported") ? "IMPORTED TRIALS" :
      sources.every(source => source === "live") ? "LIVE TRIALS" : "MIXED SOURCES";
  } else {
    els.sourceBadge.textContent = trialMeta[mode].source === "demo" ? "DEMO DATA" : trialMeta[mode].source === "live" ? "LIVE TRIAL" : "IMPORTED TRIAL";
  }
  window.scrollTo({ top: 0, behavior: "instant" });
  document.dispatchEvent(new CustomEvent("lab:view", { detail: { name } }));
}

function showImportFeedback(message, success) {
  els.importFeedback.hidden = false;
  els.importFeedback.classList.toggle("is-success", success);
  els.importFeedback.textContent = message;
}

function loadTrial(data, source = "imported") {
  if (!["imported", "live"].includes(source)) throw new Error("Unsupported trial source.");
  stopPlayback();
  const imported = storeTrial(data, source);
  analysisState.mode = imported.mode;
  analysisState.selected = null;
  mode = imported.mode;
  step = 0;
  document.querySelectorAll("[data-mode]").forEach(button => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  render();
  updateMultiThreadLabel();
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
    loadTrial(trialData, "live");
    showImportFeedback("Loaded real thread trial " + trialData.run_id + " from Member 2 backend. " + (trialData.status === "deadlock" ? "Circular wait confirmed!" : "Protected run complete!"), true);
  } catch (err) {
    const msg = err.name === "AbortError"
      ? "Experiment request timed out after 8s."
      : "Could not reach the experiment backend at /api/trials/" + targetMode + " (" + err.message + "). For local use, start FastAPI; otherwise import a saved trial.";
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

let isRunningMultiThread = false;
const MULTI_THREAD_MIN = 2;
const MULTI_THREAD_MAX = 32;
const multiCountInput = document.getElementById("multi-thread-count");
const multiRangeInput = document.getElementById("multi-thread-range");
const multiRunButton = document.getElementById("multi-thread-run-button");

function readThreadCount() {
  const value = Math.round(Number(multiCountInput.value));
  return Number.isFinite(value) ? Math.min(MULTI_THREAD_MAX, Math.max(MULTI_THREAD_MIN, value)) : 6;
}

function updateMultiThreadLabel() {
  if (!isRunningMultiThread) multiRunButton.textContent = "⚡ Run " + readThreadCount() + " threads · " + mode;
}

multiRangeInput.addEventListener("input", () => { multiCountInput.value = multiRangeInput.value; updateMultiThreadLabel(); });
multiCountInput.addEventListener("input", () => {
  if (multiCountInput.value !== "") multiRangeInput.value = readThreadCount();
  updateMultiThreadLabel();
});
multiCountInput.addEventListener("change", () => {
  multiCountInput.value = readThreadCount();
  multiRangeInput.value = multiCountInput.value;
  updateMultiThreadLabel();
});

// ---------- Animated replay of a multi-thread run ----------
// The backend's event log is turned into steps; each step is a full state
// (lock owners, waits, per-thread status). A persistent SVG scene is built
// once and only its attributes change between steps, so CSS transitions
// animate lock tokens flying between threads and nodes changing state.
//
// Layout (no two layers share space): threads on a ring of radius R, wait
// arrows as arcs on that ring, lock tokens on an inner ring, thread details
// outside the ring, and the status in the centre.
const replay = { frames: [], index: 0, timer: null, scene: null, result: null };
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function describeStep(event, merged, state) {
  const t = event.thread, r = event.resource;
  switch (event.action) {
    case "start": return "Run started: " + state.count + " real threads, " + state.count + " locks";
    case "requested": return t + " requests " + r;
    case "waiting": return (merged ? t + " requests " + r + " → " : t + " ") + "must wait: " + r + " is held by " + event.owner;
    case "acquired": return (merged ? t + " requests " + r + " → takes it" : t + " takes " + r + (event.wait_ms ? " after waiting " + event.wait_ms + " ms" : ""));
    case "released": return t + " releases " + r;
    case "aborted": return t + " is aborted: its wait for " + r + " is cancelled";
    case "timeout": return t + " gave up waiting for " + r;
    case "deadlock_detected": return "Deadlock detected: every thread waits for the next one";
    case "recovery": return "Recovery: abort " + (replay.result.victim || "a victim") + " to break the cycle";
    case "complete": return "All " + state.count + " threads finished";
    default: return t + " " + event.action + (r ? " " + r : "");
  }
}

function buildReplayFrames(result) {
  const workers = result.workers || [];
  const outcome = Object.fromEntries(workers.map(worker => [worker.thread, worker.outcome]));
  const owners = {}, waits = {}, status = {}, worked = {};
  workers.forEach(worker => { status[worker.thread] = "idle"; });
  let cycleOn = false, recovered = false;
  const frames = [];
  const events = result.events;
  const heldCount = thread => Object.values(owners).filter(owner => owner === thread).length;

  for (let index = 0; index < events.length; index += 1) {
    let event = events[index];
    let merged = false;
    // Fold "requested" into the wait/acquire that immediately follows it.
    const next = events[index + 1];
    if (event.action === "requested" && next && next.thread === event.thread && next.resource === event.resource &&
        (next.action === "waiting" || next.action === "acquired")) {
      event = next;
      merged = true;
      index += 1;
    }
    const t = event.thread, r = event.resource;
    if (event.action === "requested") status[t] = "requesting";
    if (event.action === "waiting") { waits[t] = r; status[t] = "waiting"; }
    if (event.action === "acquired") {
      owners[r] = t;
      delete waits[t];
      status[t] = heldCount(t) >= 2 ? "working" : "holding";
      if (heldCount(t) >= 2) worked[t] = true;
    }
    if (event.action === "released" && owners[r] === t) {
      delete owners[r];
      if (heldCount(t) === 0) status[t] = status[t] === "aborted" ? "aborted" : worked[t] && outcome[t] === "completed" ? "finished" : "idle";
      else if (status[t] === "working") status[t] = "releasing";
    }
    // Aborting the victim breaks the circular wait.
    if (event.action === "aborted") { delete waits[t]; status[t] = "aborted"; cycleOn = false; }
    if (event.action === "timeout") { delete waits[t]; status[t] = "aborted"; }
    if (event.action === "deadlock_detected") cycleOn = true;
    if (event.action === "recovery") recovered = true;
    // The cycle highlight lasts while the threads in it are still waiting.
    if (cycleOn && Object.keys(waits).length === 0) cycleOn = false;
    frames.push({
      event, merged, cycleOn, recovered,
      owners: { ...owners }, waits: { ...waits }, status: { ...status },
      caption: describeStep(event, merged, { count: workers.length }),
      timeMs: event.time * 1000
    });
  }
  return frames;
}

function buildReplayScene(result) {
  const graph = document.getElementById("multi-thread-graph");
  const workers = result.workers || [];
  const resources = result.resources || [];
  const count = workers.length;
  const viewWidth = Math.max(300, Math.min(960, Math.round(graph.getBoundingClientRect().width) || 720));
  const viewHeight = Math.round(Math.min(560, Math.max(320, viewWidth * 0.62)));
  const showNodeLabels = count <= 12 && viewWidth >= 520;
  const centerX = viewWidth / 2, centerY = viewHeight / 2;
  const step = Math.PI * 2 / count;
  // Vertical room fits up to three label lines below the bottom node.
  const available = Math.min(centerX - (showNodeLabels ? 100 : 8), centerY - (showNodeLabels ? 62 : 8));
  const nodeSize = ringRadius => Math.max(9, Math.min(24, (2 * ringRadius * Math.sin(Math.PI / Math.max(count, 2)) - 24) / 2));
  const nodeRadius = nodeSize(available - 24);
  const radius = Math.max(60, available - nodeRadius - 4);
  // Lock tokens sit on an inner ring. Two limits size them: a token's spots
  // are half a step from any other token's spots (so width <= chord), and a
  // token must clear its node at any angle (node and token corners included).
  // Solving both: rT = R - 1.42*nodeR - 0.59*w - 6 and w <= 2*rT*sin(step/4) - 6.
  const sinQuarter = Math.sin(step / 4);
  // Tiles also stay small relative to the ring so the centre keeps room for the status.
  const tokenWidth = Math.max(8, Math.min(32, 0.4 * (radius - 1.42 * nodeRadius - 6), (2 * (radius - 1.42 * nodeRadius - 6) * sinQuarter - 6) / (1 + 1.18 * sinQuarter)));
  const tokenHeight = Math.max(8, Math.min(18, tokenWidth * 0.62));
  const tokenRadius = radius - 1.42 * nodeRadius - Math.hypot(tokenWidth, tokenHeight) / 2 - 6;
  const arrow = nodeRadius < 13 ? 6 : 8;
  const fmt = value => value.toFixed(1);
  const point = (angle, r = radius) => ({ x: centerX + Math.cos(angle) * r, y: centerY + Math.sin(angle) * r });
  const angleOf = {}, indexOf = {};
  workers.forEach((worker, index) => { indexOf[worker.thread] = index; angleOf[worker.thread] = -Math.PI / 2 + index * step; });
  const normalize = angle => Math.atan2(Math.sin(angle), Math.cos(angle));
  // Lock Rk rests between T(k-1) and Tk; a holder keeps it on the side facing that rest spot.
  const homeAngle = {};
  resources.forEach((resource, index) => { homeAngle[resource] = -Math.PI / 2 + index * step - step / 2; });
  const tokenSpot = (resource, owner) => {
    if (!owner || !(owner in angleOf)) return point(homeAngle[resource], tokenRadius);
    const side = normalize(homeAngle[resource] - angleOf[owner]) < 0 ? -1 : 1;
    return point(angleOf[owner] + side * step / 4, tokenRadius);
  };

  const arcPath = (fromIndex, direction) => {
    const fromAngle = -Math.PI / 2 + fromIndex * step;
    const a = point(fromAngle + direction * (nodeRadius + 3) / radius);
    const b = point(fromAngle + direction * (step - (nodeRadius + arrow) / radius));
    return "M " + fmt(a.x) + " " + fmt(a.y) + " A " + fmt(radius) + " " + fmt(radius) + " 0 0 " + (direction > 0 ? 1 : 0) + " " + fmt(b.x) + " " + fmt(b.y);
  };
  // One hidden arc per thread and direction; a step reveals the ones in use.
  let edgeMarkup = "";
  workers.forEach((worker, index) => {
    [1, -1].forEach(direction => {
      if (count === 2 && direction === -1) return;
      edgeMarkup += '<path class="multi-graph-edge mt-edge" data-from="' + worker.thread + '" data-dir="' + direction + '" d="' + arcPath(index, direction) + '"/>';
    });
  });

  const nodeMarkup = workers.map(worker => {
    const center = point(angleOf[worker.thread]);
    return '<g class="multi-graph-node mt-node st-idle" data-thread="' + worker.thread + '">' +
      '<title>' + escapeHtml(worker.thread + " · OS thread " + worker.native_id) + '</title>' +
      '<circle class="mt-spin" cx="' + fmt(center.x) + '" cy="' + fmt(center.y) + '" r="' + fmt(nodeRadius + 4) + '"/>' +
      '<circle class="mt-body" cx="' + fmt(center.x) + '" cy="' + fmt(center.y) + '" r="' + fmt(nodeRadius) + '"/>' +
      '<text class="multi-graph-id" x="' + fmt(center.x) + '" y="' + fmt(center.y + (nodeRadius < 13 ? 3 : 4)) + '" style="font-size:' + (nodeRadius < 13 ? 8 : nodeRadius < 18 ? 10 : 12) + 'px">' + worker.thread + '</text></g>';
  }).join("");

  const detailMarkup = showNodeLabels ? workers.map(worker => {
    const angle = angleOf[worker.thread];
    // Diagonal positions need extra clearance because the node's box corner sticks out further.
    const anchorPoint = point(angle, radius + nodeRadius * (1 + 0.42 * Math.abs(Math.sin(2 * angle))) + 8);
    const cos = Math.cos(angle);
    const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
    return '<text class="mt-node-detail" data-thread="' + worker.thread + '" data-x="' + fmt(anchorPoint.x) + '" data-y="' + fmt(anchorPoint.y) + '" data-sin="' + Math.sin(angle).toFixed(3) + '" text-anchor="' + anchor + '"></text>';
  }).join("") : "";

  const showTokenText = tokenWidth >= 18;
  const tokenMarkup = resources.map(resource => {
    const spot = tokenSpot(resource, null);
    return '<g class="mt-token" data-resource="' + resource + '" style="transform: translate(' + fmt(spot.x) + 'px, ' + fmt(spot.y) + 'px)">' +
      '<rect x="' + fmt(-tokenWidth / 2) + '" y="' + fmt(-tokenHeight / 2) + '" width="' + fmt(tokenWidth) + '" height="' + fmt(tokenHeight) + '" rx="' + fmt(Math.min(5, tokenHeight / 3)) + '"/>' +
      (showTokenText ? '<text y="' + fmt(tokenHeight * 0.3) + '" style="font-size:' + fmt(Math.min(11, tokenHeight * 0.62)) + 'px">' + resource + '</text>' : "") + '</g>';
  }).join("");

  // Centre text must clear the lock tiles on the inner ring, measured by tile width.
  const innerWidth = 2 * (tokenRadius - tokenWidth / 2 - 12);
  graph.setAttribute("viewBox", "0 0 " + viewWidth + " " + viewHeight);
  graph.innerHTML = '<defs>' +
    '<marker id="multi-arrow" markerUnits="userSpaceOnUse" markerWidth="' + arrow + '" markerHeight="' + arrow + '" refX="' + (arrow - 1) + '" refY="' + arrow / 2 + '" orient="auto"><path d="M0,0 L' + arrow + ',' + arrow / 2 + ' L0,' + arrow + ' z" fill="#ffb547"/></marker>' +
    '<marker id="multi-arrow-danger" markerUnits="userSpaceOnUse" markerWidth="' + arrow + '" markerHeight="' + arrow + '" refX="' + (arrow - 1) + '" refY="' + arrow / 2 + '" orient="auto"><path d="M0,0 L' + arrow + ',' + arrow / 2 + ' L0,' + arrow + ' z" fill="#ff4d6d"/></marker>' +
    '</defs>' +
    '<circle class="multi-graph-orbit" cx="' + fmt(centerX) + '" cy="' + fmt(centerY) + '" r="' + fmt(radius) + '"/>' +
    '<circle class="multi-graph-orbit mt-token-orbit" cx="' + fmt(centerX) + '" cy="' + fmt(centerY) + '" r="' + fmt(tokenRadius) + '"/>' +
    '<text class="mt-center-title" x="' + fmt(centerX) + '" y="' + fmt(centerY + 2) + '"></text>' +
    '<text class="mt-center-sub" x="' + fmt(centerX) + '" y="' + fmt(centerY + 20) + '"></text>' +
    edgeMarkup + tokenMarkup + nodeMarkup + detailMarkup;
  graph.classList.toggle("no-anim", reducedMotion);

  const byData = (selector, key) => Object.fromEntries([...graph.querySelectorAll(selector)].map(el => [el.dataset[key], el]));
  return {
    graph, workers, count, tokenSpot, indexOf, innerWidth, centerY,
    nodes: byData(".mt-node", "thread"),
    details: byData(".mt-node-detail", "thread"),
    tokens: byData(".mt-token", "resource"),
    edges: [...graph.querySelectorAll(".mt-edge")],
    title: graph.querySelector(".mt-center-title"),
    sub: graph.querySelector(".mt-center-sub")
  };
}

function setCenterText(scene, title, titleClass, sub) {
  const fitSize = scene.innerWidth / (Math.max(title.length, 4) * 0.75);
  // A small ring has no room in the middle; the caption above the graph carries the status then.
  if (fitSize < 9) title = sub = "";
  const titleSize = Math.min(28, fitSize);
  const subSize = Math.min(12.5, scene.innerWidth / (Math.max(sub.length, 1) * 0.62));
  scene.title.textContent = title;
  scene.title.setAttribute("class", "mt-center-title " + titleClass);
  scene.title.style.fontSize = titleSize.toFixed(1) + "px";
  scene.title.setAttribute("y", (scene.centerY + (subSize >= 8 ? 2 : titleSize * 0.35)).toFixed(1));
  scene.sub.textContent = subSize >= 8 ? sub : "";
  scene.sub.style.fontSize = subSize.toFixed(1) + "px";
  scene.sub.setAttribute("y", (scene.centerY + titleSize * 0.5 + 12).toFixed(1));
}

function renderReplayFrame(index) {
  const scene = replay.scene, frame = replay.frames[index], result = replay.result;
  if (!scene || !frame) return;
  replay.index = index;
  const cycle = new Set(result.metrics.deadlock_cycle || []);

  Object.entries(scene.tokens).forEach(([resource, token]) => {
    const owner = frame.owners[resource];
    const spot = scene.tokenSpot(resource, owner);
    token.style.transform = "translate(" + spot.x.toFixed(1) + "px, " + spot.y.toFixed(1) + "px)";
    const waitedOn = Object.values(frame.waits).includes(resource);
    token.setAttribute("class", "mt-token" + (owner ? " is-held" : " is-free") + (waitedOn ? " is-contended" : "") +
      (frame.cycleOn && owner && cycle.has(owner) ? " is-cycle" : "") + (frame.event.resource === resource ? " is-active" : ""));
  });

  scene.edges.forEach(edge => {
    const from = edge.dataset.from, direction = Number(edge.dataset.dir);
    const resource = frame.waits[from];
    const owner = resource ? frame.owners[resource] : null;
    const target = owner ? scene.indexOf[owner] : -1;
    const fromIndex = scene.indexOf[from];
    const matches = owner && (direction > 0 ? (fromIndex + 1) % scene.count === target : (target + 1) % scene.count === fromIndex);
    const isCycle = matches && frame.cycleOn && cycle.has(from) && cycle.has(owner);
    edge.setAttribute("class", "multi-graph-edge mt-edge" + (matches ? " is-live" : "") + (isCycle ? " is-cycle" : ""));
    edge.setAttribute("marker-end", matches ? "url(#" + (isCycle ? "multi-arrow-danger" : "multi-arrow") + ")" : "");
  });

  Object.entries(scene.nodes).forEach(([thread, node]) => {
    const state = frame.status[thread];
    const inCycle = frame.cycleOn && cycle.has(thread) && frame.waits[thread];
    node.setAttribute("class", "multi-graph-node mt-node st-" + state + (inCycle ? " is-cycle" : "") + (frame.event.thread === thread ? " is-active" : "") +
      (thread === result.victim && frame.recovered ? " is-victim" : ""));
    const detail = scene.details[thread];
    if (!detail) return;
    const held = Object.entries(frame.owners).filter(([, owner]) => owner === thread).map(([resource]) => resource);
    const lines = [];
    if (held.length) lines.push(['is-hold', "holds " + held.join("+")]);
    if (frame.waits[thread]) lines.push(['is-want', "wants " + frame.waits[thread]]);
    if (state === "finished") lines.push(['is-done', "finished ✓"]);
    if (state === "aborted") lines.push(['is-victim', "aborted ✕"]);
    const x = detail.dataset.x, y = Number(detail.dataset.y), sin = Number(detail.dataset.sin);
    const lineHeight = 12;
    const firstY = y + (sin < -0.3 ? -(lines.length - 1) * lineHeight - 2 : sin > 0.3 ? 10 : -((lines.length - 1) * lineHeight) / 2 + 4);
    detail.innerHTML = lines.map(([cls, text], line) =>
      '<tspan class="' + cls + '" x="' + x + '" y="' + (firstY + line * lineHeight).toFixed(1) + '">' + escapeHtml(text) + '</tspan>').join("");
  });

  const last = index === replay.frames.length - 1;
  const waitingCount = Object.keys(frame.waits).length;
  if (frame.cycleOn) setCenterText(scene, "DEADLOCK", "is-danger", waitingCount + " threads stuck in a cycle");
  else if (last) setCenterText(scene, result.status === "deadlock" ? "RECOVERED" : "NO CYCLE", "is-safe", Object.values(frame.status).filter(s => s === "finished").length + " of " + scene.count + " finished");
  else if (frame.recovered) setCenterText(scene, "RECOVERING", "is-warning", "aborted " + result.victim + " · unwinding");
  else setCenterText(scene, "RUNNING", "is-running", waitingCount ? waitingCount + " waiting" : Object.keys(frame.owners).length + " locks held");
  scene.graph.classList.toggle("is-flash", frame.event.action === "deadlock_detected" && !reducedMotion);

  document.getElementById("mt-caption-text").textContent = frame.caption;
  document.getElementById("mt-caption-time").textContent = frame.timeMs.toFixed(1) + " ms";
  document.getElementById("mt-caption").className = "mt-caption" +
    (["deadlock_detected", "aborted", "timeout"].includes(frame.event.action) ? " is-danger" : frame.event.action === "waiting" ? " is-warning" :
      ["acquired", "complete"].includes(frame.event.action) ? " is-safe" : frame.event.action === "recovery" ? " is-warning" : "");
  document.getElementById("mt-step").textContent = (index + 1) + " / " + replay.frames.length;
  document.getElementById("mt-scrub").value = index;
  document.getElementById("mt-log").innerHTML = replay.frames.slice(Math.max(0, index - 4), index + 1).reverse()
    .map((item, position) => '<li class="' + (position === 0 ? "is-current" : "") + '"><span>' + item.timeMs.toFixed(1) + ' ms</span>' + escapeHtml(item.caption) + '</li>').join("");
  moveTimelinePlayhead(frame.timeMs);
}

function stopReplay() {
  if (replay.timer !== null) { window.clearTimeout(replay.timer); replay.timer = null; }
  const play = document.getElementById("mt-play");
  if (play) { play.textContent = "▶"; play.setAttribute("aria-label", "Play replay"); }
}

function scheduleReplayStep() {
  const speed = Number(document.getElementById("mt-speed").value);
  const frame = replay.frames[replay.index];
  // Linger on the moments that matter so they can be read.
  const linger = frame && ["deadlock_detected", "recovery", "complete"].includes(frame.event.action) ? 3 : 1;
  replay.timer = window.setTimeout(() => {
    if (replay.index >= replay.frames.length - 1) { stopReplay(); return; }
    renderReplayFrame(replay.index + 1);
    scheduleReplayStep();
  }, 520 * linger / speed);
}

function playReplay() {
  if (replay.index >= replay.frames.length - 1) renderReplayFrame(0);
  stopReplay();
  const play = document.getElementById("mt-play");
  play.textContent = "❚❚";
  play.setAttribute("aria-label", "Pause replay");
  scheduleReplayStep();
}

function startReplay(result) {
  stopReplay();
  replay.result = result;
  replay.frames = buildReplayFrames(result);
  replay.scene = buildReplayScene(result);
  const scrub = document.getElementById("mt-scrub");
  scrub.max = String(replay.frames.length - 1);
  const count = (result.workers || []).length;
  document.getElementById("mt-speed").value = count <= 6 ? "1" : count <= 12 ? "2" : count <= 20 ? "4" : "8";
  const keyIndex = replay.frames.findIndex(frame => frame.event.action === "deadlock_detected");
  const jump = document.getElementById("mt-jump");
  jump.textContent = keyIndex >= 0 ? "Jump to deadlock" : "Jump to busiest moment";
  renderReplayFrame(0);
  if (!reducedMotion) playReplay();
}

function jumpToKeyMoment() {
  stopReplay();
  let target = replay.frames.findIndex(frame => frame.event.action === "deadlock_detected");
  if (target < 0) {
    let most = -1;
    replay.frames.forEach((frame, index) => { const waiting = Object.keys(frame.waits).length; if (waiting > most) { most = waiting; target = index; } });
  }
  renderReplayFrame(Math.max(0, target));
}

document.getElementById("mt-play").addEventListener("click", () => (replay.timer === null ? playReplay() : stopReplay()));
document.getElementById("mt-prev").addEventListener("click", () => { stopReplay(); renderReplayFrame(Math.max(0, replay.index - 1)); });
document.getElementById("mt-next").addEventListener("click", () => { stopReplay(); renderReplayFrame(Math.min(replay.frames.length - 1, replay.index + 1)); });
document.getElementById("mt-restart").addEventListener("click", () => { renderReplayFrame(0); playReplay(); });
document.getElementById("mt-jump").addEventListener("click", jumpToKeyMoment);
document.getElementById("mt-scrub").addEventListener("input", event => { stopReplay(); renderReplayFrame(Number(event.target.value)); });

let timelineScale = null;
function moveTimelinePlayhead(ms) {
  const playhead = document.getElementById("mt-playhead");
  if (!playhead || !timelineScale) return;
  const position = timelineScale.x(ms).toFixed(1);
  playhead.setAttribute("x1", position);
  playhead.setAttribute("x2", position);
}

function renderMultiThreadTimeline(result) {
  const svg = document.getElementById("multi-thread-timeline");
  const workers = result.workers || [];
  const total = Math.max(1, result.completion_time_ms);
  const rowHeight = workers.length <= 12 ? 22 : workers.length <= 20 ? 16 : 13;
  const labelSize = rowHeight < 16 ? 9 : 10;
  // Match the drawing width to the rendered width so labels stay legible on narrow screens.
  const viewWidth = Math.max(300, Math.round(svg.getBoundingClientRect().width) || 720);
  const left = 46, right = 14, top = 24, axis = 22;
  const width = viewWidth - left - right;
  const height = top + rowHeight * workers.length + axis;
  const x = ms => left + Math.min(1, Math.max(0, ms / total)) * width;
  const lanes = {};
  workers.forEach(worker => { lanes[worker.thread] = { held: 0, holdStart: null, waitStart: null, segments: [] }; });
  let deadlockMs = null;

  for (const event of result.events) {
    const ms = event.time * 1000;
    if (event.action === "deadlock_detected") deadlockMs = ms;
    const lane = lanes[event.thread];
    if (!lane) continue;
    if (event.action === "waiting") lane.waitStart = ms;
    if (["acquired", "timeout", "aborted"].includes(event.action) && lane.waitStart !== null) {
      lane.segments.push({ kind: "wait", from: lane.waitStart, to: ms });
      lane.waitStart = null;
    }
    if (event.action === "acquired") {
      if (lane.held === 0) lane.holdStart = ms;
      lane.held += 1;
    } else if (event.action === "released" && lane.held > 0) {
      lane.held -= 1;
      if (lane.held === 0) lane.segments.push({ kind: "hold", from: lane.holdStart, to: ms });
    }
  }

  const barHeight = Math.max(5, rowHeight - 7);
  let markup = "";
  workers.forEach((worker, index) => {
    const y = top + index * rowHeight;
    const lane = lanes[worker.thread];
    const isVictim = worker.thread === result.victim;
    markup += '<text class="timeline-label' + (isVictim ? " is-victim" : "") + '" x="' + (left - 8) + '" y="' + (y + rowHeight / 2 + labelSize * 0.35) + '" style="font-size:' + labelSize + 'px">' + worker.thread + '</text>';
    markup += '<line class="timeline-track" x1="' + left + '" x2="' + (left + width) + '" y1="' + (y + rowHeight / 2) + '" y2="' + (y + rowHeight / 2) + '"/>';
    // Threads keep their first lock while waiting for the second, so draw holds first and waits on top.
    lane.segments.sort((a, b) => (a.kind === "hold" ? 0 : 1) - (b.kind === "hold" ? 0 : 1)).forEach(segment => {
      const x1 = x(segment.from), x2 = Math.max(x(segment.to), x1 + 1.5);
      markup += '<rect class="timeline-' + segment.kind + '" x="' + x1.toFixed(1) + '" y="' + (y + (rowHeight - barHeight) / 2).toFixed(1) +
        '" width="' + (x2 - x1).toFixed(1) + '" height="' + barHeight + '" rx="2"/>';
    });
    if (worker.finished_ms !== null) {
      markup += '<circle class="timeline-end' + (worker.outcome === "completed" ? "" : " is-failed") + '" cx="' + x(worker.finished_ms).toFixed(1) +
        '" cy="' + (y + rowHeight / 2) + '" r="' + Math.min(4, barHeight / 2) + '"><title>' + escapeHtml(worker.thread + " " + worker.outcome + " at " + worker.finished_ms + " ms") + '</title></circle>';
    }
  });
  const chartBottom = top + rowHeight * workers.length;
  if (deadlockMs !== null) {
    // The marker label sits above the lanes so it never collides with the time axis.
    const markerX = x(deadlockMs);
    const nearRight = markerX > left + width * 0.6;
    markup += '<line class="timeline-marker" x1="' + markerX + '" x2="' + markerX + '" y1="' + (top - 6) + '" y2="' + chartBottom + '"/>' +
      '<text class="timeline-marker-label" text-anchor="' + (nearRight ? "end" : "start") + '" x="' + (markerX + (nearRight ? -5 : 5)) + '" y="' + (top - 9) + '">deadlock detected' +
      (result.victim ? " → abort " + result.victim : "") + '</text>';
  }
  for (let tick = 0; tick <= 4; tick += 1) {
    const tx = left + width * tick / 4;
    markup += '<text class="timeline-tick" text-anchor="' + (tick === 0 ? "start" : tick === 4 ? "end" : "middle") + '" x="' + tx + '" y="' + (chartBottom + 16) + '">' + Math.round(total * tick / 4) + ' ms</text>';
  }
  markup += '<line id="mt-playhead" class="timeline-playhead" x1="' + left + '" x2="' + left + '" y1="' + (top - 4) + '" y2="' + chartBottom + '"/>';
  timelineScale = { x };
  svg.setAttribute("viewBox", "0 0 " + viewWidth + " " + (height + 2));
  svg.innerHTML = markup;
}

function renderMultiThreadResult(result) {
  const panel = document.getElementById("multi-thread-results");
  const badge = document.getElementById("multi-thread-status");
  const metrics = result.metrics;
  const workers = result.workers || [];
  const cycle = metrics.deadlock_cycle || [];
  const cycleNodes = new Set(cycle);
  const count = workers.length;
  const completedCount = workers.filter(worker => worker.outcome === "completed").length;
  const abortedCount = workers.filter(worker => worker.outcome === "aborted").length;
  const osIds = new Set(workers.map(worker => worker.native_id).filter(id => id !== null));
  const peakQueued = result.snapshot ? Object.keys(result.snapshot.waits).length : 0;
  const isDeadlock = result.status === "deadlock";
  const isCompleted = result.status === "completed";

  panel.hidden = false;
  renderMultiThreadTimeline(result);
  startReplay(result);

  const verdict = document.getElementById("multi-thread-verdict");
  verdict.className = "mt-verdict " + (isDeadlock ? "is-danger" : isCompleted ? "is-safe" : "is-warning");
  document.getElementById("multi-thread-verdict-icon").textContent = isDeadlock ? "!" : isCompleted ? "✓" : "?";
  document.getElementById("multi-thread-verdict-title").textContent = isDeadlock
    ? "Deadlock: all " + count + " threads got stuck waiting in one circle"
    : isCompleted ? "No deadlock: all " + count + " threads finished" : "Run ended with status " + result.status;
  document.getElementById("multi-thread-verdict-detail").textContent = isDeadlock
    ? "Detected " + Number(result.snapshot.time_ms).toFixed(1) + " ms after start · recovered by aborting " + result.victim + " · " + completedCount + " of " + count + " then finished"
    : isCompleted ? "Global lock order (lower number first) · up to " + peakQueued + " threads queued at once · no circular wait"
      : result.error || "";

  const maxWait = Math.max(1, ...workers.map(worker => worker.waited_ms));
  document.getElementById("multi-thread-worker-list").innerHTML = workers.map(worker => {
    const ok = worker.outcome === "completed";
    const outcome = ok ? "Finished" : worker.outcome === "aborted" ? "Aborted" : worker.outcome === "timed_out" ? "Timed out" : "Error";
    return '<tr>' +
      '<td><span class="mt-dot' + (cycleNodes.has(worker.thread) ? " is-cycle" : "") + '" title="' + (cycleNodes.has(worker.thread) ? "In the deadlock cycle" : "Not in a cycle") + '"></span><strong>' + worker.thread + '</strong></td>' +
      '<td class="mt-muted">' + (worker.native_id ?? "—") + '</td>' +
      '<td>' + worker.lock_order.join(" → ") + '</td>' +
      '<td><div class="mt-wait"><span style="width:' + (worker.waited_ms / maxWait * 100).toFixed(0) + '%"></span></div><small>' + worker.waited_ms + ' ms</small></td>' +
      '<td><span class="mt-outcome ' + (ok ? "is-ok" : "is-failed") + '">' + outcome + '</span></td></tr>';
  }).join("");

  badge.textContent = isDeadlock ? "DEADLOCK" : result.status.toUpperCase();
  badge.className = "outline-badge" + (isDeadlock ? " is-danger" : isCompleted ? " is-safe" : " is-warning");

  document.getElementById("multi-thread-summary").textContent = isDeadlock
    ? "Each thread took its first lock, then waited for the next thread's lock: T1 waits for T2, T2 for T3, … and T" + count + " waits for T1. Nobody can move, which is a deadlock. The system breaks it by aborting " + result.victim + "."
    : isCompleted
      ? "Every thread took its two locks in the same global order, so the last thread could never close the circle. Threads only queued behind their neighbours and then finished."
      : "";

  document.getElementById("multi-thread-metric-workers").textContent = metrics.threads_started + " / " + count;
  document.getElementById("multi-thread-metric-os").textContent = osIds.size;
  document.getElementById("multi-thread-metric-cycle").textContent = cycle.length ? (cycle.length - 1) + " threads" : "none";
  document.getElementById("multi-thread-metric-completed").textContent = completedCount;
  document.getElementById("multi-thread-metric-aborted").textContent = abortedCount ? abortedCount + " (" + result.victim + ")" : "0";
  document.getElementById("multi-thread-metric-runtime").textContent = result.completion_time_ms + " ms";
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function runMultiThreadTrial() {
  if (isRunningMultiThread) return;
  const threadCount = readThreadCount();
  multiCountInput.value = threadCount;
  multiRangeInput.value = threadCount;
  isRunningMultiThread = true;
  multiRunButton.disabled = true;
  multiRunButton.textContent = "⏳ Running " + threadCount + " threads...";
  showImportFeedback("Starting " + threadCount + " real OS threads in " + mode + " mode on a ring of " + threadCount + " locks...", true);
  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 20000);
    const response = await fetch("/api/experiments/multi-thread", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, thread_count: threadCount, timeout_seconds: 5 }),
      signal: controller.signal
    });
    window.clearTimeout(timeoutId);
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const detail = Array.isArray(errorData?.detail) ? errorData.detail.map(item => item.msg).join("; ") : errorData?.detail;
      throw new Error(detail || "Backend returned status " + response.status);
    }
    const result = await response.json();
    renderMultiThreadResult(result);
    showImportFeedback(
      result.status === "deadlock"
        ? "Deadlock reproduced: all " + threadCount + " threads formed one cycle; " + result.victim + " was aborted to recover."
        : result.status === "completed"
          ? "Protected run: all " + threadCount + " threads finished with no cycle."
          : "Run ended with status " + result.status + ".",
      result.status === "deadlock" || result.status === "completed"
    );
  } catch (error) {
    const message = error.name === "AbortError" ? "Multi-thread request timed out." : error.message;
    showImportFeedback("Could not run the multi-thread simulation: " + message + ". Verify the FastAPI backend is running.", false);
  } finally {
    isRunningMultiThread = false;
    multiRunButton.disabled = false;
    updateMultiThreadLabel();
  }
}

multiRunButton.addEventListener("click", runMultiThreadTrial);

// ---------- Analysis and Compare tabs ----------
// The browser re-scores recorded runs with the same formula as the backend
// scorer (member3_analysis/threat_scorer.py), so weight changes show at once.
const SCORE_DEFAULTS = { w_b: 0.35, w_w: 0.30, w_c: 0.20, w_r: 0.15, threshold: 70 };
const SCORE_LIMITS = { maxThreads: 2, maxWaitMs: 800, maxContention: 5, lowThreshold: 40, inversionFloor: 72, cycleFloor: 96 };
const CHART = { formula: "#3987e5", vulnerable: "#e66767", protected: "#199e70", warning: "#fab219", critical: "#d03b3b",
  factors: ["#3987e5", "#d95926", "#199e70", "#c98500"] };
const analysisState = { mode: "vulnerable", selected: null, runKey: "" };
const svgNS = "http://www.w3.org/2000/svg";

function readWeights() {
  return {
    w_b: parseFloat(els.inputWb.value), w_w: parseFloat(els.inputWw.value),
    w_c: parseFloat(els.inputWc.value), w_r: parseFloat(els.inputWr.value),
    threshold: parseInt(els.inputTh.value, 10)
  };
}

function scoreFrame(frame, cfg) {
  const blocked = Object.keys(frame.waits).length;
  const holders = Object.values(frame.owners);
  const held = holders.length, distinct = new Set(holders).size;
  const conflict = held >= 2 && distinct >= 2;
  const factors = [
    { label: "Blocked threads", weight: cfg.w_b, norm: Math.min(100, blocked / SCORE_LIMITS.maxThreads * 100), raw: blocked + " of " + SCORE_LIMITS.maxThreads + " threads blocked" },
    { label: "Wait duration", weight: cfg.w_w, norm: Math.min(100, frame.waitMs / SCORE_LIMITS.maxWaitMs * 100), raw: frame.waitMs + " ms longest wait (full at " + SCORE_LIMITS.maxWaitMs + " ms)" },
    { label: "Contention events", weight: cfg.w_c, norm: Math.min(100, frame.heat / SCORE_LIMITS.maxContention * 100), raw: frame.heat + " contention events (full at " + SCORE_LIMITS.maxContention + ")" },
    { label: "Lock conflict", weight: cfg.w_r, norm: conflict ? 100 : held >= 2 ? 40 : held === 1 ? 20 : 0,
      raw: conflict ? "A and B held by different threads" : held >= 2 ? "one thread holds both locks" : held === 1 ? "one lock held" : "no locks held" }
  ];
  factors.forEach(factor => { factor.points = factor.norm * factor.weight; });
  const total = factors.reduce((sum, factor) => sum + factor.points, 0);
  let score = Math.round(Math.max(0, Math.min(100, total)));
  let rule = "";
  const cycle = DeadlockTrialData.hasCycle(frame);
  if (!cycle && conflict && blocked >= 1 && score < SCORE_LIMITS.inversionFloor) {
    score = SCORE_LIMITS.inversionFloor;
    rule = "Lock-order rule: different threads hold A and B and one of them is waiting, so the score is raised to at least " + SCORE_LIMITS.inversionFloor + ".";
  }
  if (cycle) {
    if (score < SCORE_LIMITS.cycleFloor) rule = "Deadlock confirmed: the Wait-For Graph has a cycle, so the score is set to at least " + SCORE_LIMITS.cycleFloor + ".";
    score = Math.max(score, SCORE_LIMITS.cycleFloor);
  }
  const level = cycle ? "DEADLOCK" : score >= cfg.threshold ? "HIGH" : score >= SCORE_LIMITS.lowThreshold ? "ELEVATED" : "LOW";
  return { factors, total, score, rule, cycle, level, blocked };
}

function analyzeRun(frames, cfg) {
  const scored = frames.map(frame => ({ frame, ...scoreFrame(frame, cfg) }));
  const deadIndex = scored.findIndex(item => item.cycle);
  const warnIndex = scored.findIndex((item, index) => !item.cycle && item.score >= cfg.threshold && (deadIndex < 0 || index < deadIndex));
  let peakIndex = 0;
  scored.forEach((item, index) => { if (item.score > scored[peakIndex].score) peakIndex = index; });
  const lead = warnIndex >= 0 && deadIndex >= 0 ? frames[deadIndex].ms - frames[warnIndex].ms : null;
  return { scored, deadIndex, warnIndex, peakIndex, lead,
    longestWait: Math.max(...frames.map(frame => frame.waitMs)), contention: frames[frames.length - 1].heat };
}

function el(tag, attrs, text) {
  const node = document.createElementNS(svgNS, tag);
  Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
  if (text !== undefined) node.textContent = text;
  return node;
}

function chartFrame(svg, height) {
  const width = Math.max(300, Math.round(svg.getBoundingClientRect().width) || 720);
  svg.setAttribute("viewBox", "0 0 " + width + " " + height);
  svg.replaceChildren();
  return width;
}

function placeTip(tip, wrap, x, y, html) {
  tip.innerHTML = html;
  tip.hidden = false;
  const box = wrap.getBoundingClientRect();
  const tipBox = tip.getBoundingClientRect();
  const left = Math.min(Math.max(4, x - tipBox.width / 2), box.width - tipBox.width - 4);
  const top = y - tipBox.height - 12 < 0 ? y + 14 : y - tipBox.height - 12;
  tip.style.left = left + "px";
  tip.style.top = top + "px";
}

function niceMax(value) {
  if (value <= 0) return 1;
  const power = Math.pow(10, Math.floor(Math.log10(value)));
  const unit = [1, 2, 2.5, 5, 10].find(step => step * power >= value / 4) * power;
  return Math.ceil(value / unit) * unit;
}

function yAxis(svg, opts) {
  // Recessive grid with value labels on the left.
  opts.ticks.forEach(value => {
    const y = opts.y(value);
    svg.appendChild(el("line", { class: "ch-grid", x1: opts.left, x2: opts.right, y1: y, y2: y }));
    svg.appendChild(el("text", { class: "ch-axis-label", x: opts.left - 8, y: y + 3.5, "text-anchor": "end" }, opts.format(value)));
  });
}

function spreadLabels(labels, top, bottom) {
  // Keep right-margin labels at least their height apart, inside the plot.
  const sorted = labels.slice().sort((a, b) => a.y - b.y);
  sorted.forEach((label, index) => {
    if (index && label.y < sorted[index - 1].y + sorted[index - 1].gap) label.y = sorted[index - 1].y + sorted[index - 1].gap;
  });
  const overflow = sorted.length ? sorted[sorted.length - 1].y - bottom : 0;
  if (overflow > 0) sorted.forEach(label => { label.y = Math.max(top, label.y - overflow); });
  return labels;
}

function sourceText(meta) {
  return meta.source === "demo" ? "demo data" : meta.source === "live" ? "live backend trial" : "imported trial";
}

// ---------- Analysis ----------
function renderAnalysisTab() {
  const runMode = analysisState.mode;
  const frames = scenarios[runMode];
  const meta = trialMeta[runMode];
  const cfg = readWeights();
  const result = analyzeRun(frames, cfg);
  const runKey = runMode + ":" + meta.runId + ":" + frames.length;
  if (runKey !== analysisState.runKey || analysisState.selected === null || analysisState.selected >= frames.length) {
    analysisState.runKey = runKey;
    analysisState.selected = result.deadIndex >= 0 ? result.deadIndex : result.peakIndex;
  }
  const selected = analysisState.selected;
  const put = (id, value) => { document.getElementById(id).textContent = value; };

  put("an-run-label", (runMode === "vulnerable" ? "Vulnerable" : "Protected") + " · " + sourceText(meta));
  put("an-run-detail", (meta.source === "demo" ? "Built-in demonstration generated in the browser" : "Run " + meta.runId) + " · " + frames.length + " events · " + (meta.status === "deadlock" ? "ended in deadlock" : "completed"));
  document.querySelectorAll("[data-an-mode]").forEach(button => {
    const on = button.dataset.anMode === runMode;
    button.classList.toggle("is-selected", on);
    button.setAttribute("aria-pressed", String(on));
  });

  const peak = result.scored[result.peakIndex];
  put("an-f-peak", String(peak.score));
  put("an-f-peak-note", "event " + (result.peakIndex + 1) + " · " + frames[result.peakIndex].ms + " ms");
  put("an-f-warn", result.warnIndex >= 0 ? frames[result.warnIndex].ms + " ms" : "none");
  put("an-f-warn-note", result.warnIndex >= 0 ? "event " + (result.warnIndex + 1) + " · score " + result.scored[result.warnIndex].score + " ≥ " + cfg.threshold : "score never reached " + cfg.threshold + " before a cycle");
  put("an-f-dead", result.deadIndex >= 0 ? frames[result.deadIndex].ms + " ms" : "never");
  put("an-f-dead-note", result.deadIndex >= 0 ? "event " + (result.deadIndex + 1) + " · cycle T1 → T2 → T1" : "no cycle · the run finished");
  put("an-f-lead", result.lead !== null ? result.lead + " ms" : result.deadIndex >= 0 ? "0 ms" : "n/a");
  put("an-f-lead-note", result.lead !== null ? "warning came " + result.lead + " ms before the deadlock" : result.deadIndex >= 0 ? "no warning before the deadlock · try a lower threshold" : "no deadlock to warn about");
  put("an-f-wait", result.longestWait + " ms");
  put("an-f-wait-note", "longest time a thread was blocked");
  put("an-f-cont", String(result.contention));
  put("an-f-cont-note", "times a thread found its lock taken");

  const verdict = document.getElementById("an-verdict");
  const isDeadlock = result.deadIndex >= 0, warned = result.warnIndex >= 0;
  verdict.textContent = isDeadlock ? (warned ? "WARNED " + result.lead + " MS EARLY" : "DEADLOCK NOT FORESEEN") : (warned ? "FALSE ALARM" : "NO DEADLOCK · NO ALARM");
  verdict.className = "outline-badge " + (isDeadlock ? (warned ? "is-warning" : "is-danger") : (warned ? "is-warning" : "is-safe"));

  renderAnalysisChart(result, cfg, selected);
  renderBreakdown(result.scored[selected], selected, cfg);
  renderAnalysisTable(result, selected);

  const step = document.getElementById("an-step");
  step.max = String(frames.length - 1);
  step.value = String(selected);
  put("an-step-label", (selected + 1) + " / " + frames.length);

  const sum = cfg.w_b + cfg.w_w + cfg.w_c + cfg.w_r;
  const sumEl = document.getElementById("an-sum");
  const sumOk = Math.abs(sum - 1) <= 0.001;
  sumEl.textContent = "Weights total " + sum.toFixed(2) + (sumOk ? " ✓" : " · must be 1.00 to save (the chart still uses these values)");
  sumEl.className = "an-sum" + (sumOk ? "" : " is-bad");
}

function renderAnalysisChart(result, cfg, selected) {
  const svg = document.getElementById("an-chart");
  const wrap = svg.parentNode;
  const tip = document.getElementById("an-tip");
  const height = 290;
  const width = chartFrame(svg, height);
  const m = { l: 40, r: 78, t: 44, b: 34 };
  const plotW = width - m.l - m.r, plotH = height - m.t - m.b;
  const count = result.scored.length;
  const x = index => m.l + (count <= 1 ? plotW / 2 : index / (count - 1) * plotW);
  const y = value => m.t + (1 - value / 100) * plotH;

  // Risk bands: elevated (40 to threshold) and high (threshold to 100).
  svg.appendChild(el("rect", { class: "ch-band-elevated", x: m.l, width: plotW, y: y(cfg.threshold), height: y(SCORE_LIMITS.lowThreshold) - y(cfg.threshold) }));
  svg.appendChild(el("rect", { class: "ch-band-high", x: m.l, width: plotW, y: y(100), height: y(cfg.threshold) - y(100) }));
  yAxis(svg, { ticks: [0, 25, 50, 75, 100], y, left: m.l, right: m.l + plotW, format: String });

  if (result.warnIndex >= 0 && result.deadIndex >= 0 && result.deadIndex > result.warnIndex) {
    const x1 = x(result.warnIndex), x2 = x(result.deadIndex);
    svg.appendChild(el("rect", { class: "ch-lead-band", x: x1, width: x2 - x1, y: m.t, height: plotH }));
    const label = "lead " + result.lead + " ms";
    if (x2 - x1 >= label.length * 6.6 + 12) svg.appendChild(el("text", { class: "ch-lead-label", x: (x1 + x2) / 2, y: m.t + plotH - 10, "text-anchor": "middle" }, label));
  }
  svg.appendChild(el("line", { class: "ch-threshold", x1: m.l, x2: m.l + plotW, y1: y(cfg.threshold), y2: y(cfg.threshold) }));
  // The threshold label lives in the right margin, clear of every data mark.
  svg.appendChild(el("text", { class: "ch-threshold-label", x: m.l + plotW + 8, y: y(cfg.threshold) + 3 }, "threshold"));
  svg.appendChild(el("text", { class: "ch-threshold-label", x: m.l + plotW + 8, y: y(cfg.threshold) + 19 }, String(cfg.threshold)));

  // Event-number axis (time is shown in the tooltip and the markers).
  const every = Math.max(1, Math.ceil(count / Math.max(2, Math.floor(plotW / 46))));
  for (let index = 0; index < count; index += every) {
    svg.appendChild(el("text", { class: "ch-axis-label", x: x(index), y: m.t + plotH + 18, "text-anchor": "middle" }, String(index + 1)));
  }
  svg.appendChild(el("text", { class: "ch-axis-title", x: m.l + plotW + 8, y: m.t + plotH + 18 }, "event →"));

  // Markers sit on separate label rows above the plot so they never collide.
  const marker = (index, cls, row, text) => {
    const mx = x(index);
    svg.appendChild(el("line", { class: cls, x1: mx, x2: mx, y1: m.t - (row === 1 ? 26 : 12), y2: m.t + plotH }));
    const anchor = mx > m.l + plotW * 0.7 ? "end" : "start";
    svg.appendChild(el("text", { class: "ch-marker-label " + cls, x: mx + (anchor === "end" ? -5 : 5), y: m.t - (row === 1 ? 30 : 16) + 10, "text-anchor": anchor }, text));
  };
  if (result.warnIndex >= 0) marker(result.warnIndex, "ch-marker-warn", 1, "⚠ warning · " + result.scored[result.warnIndex].frame.ms + " ms");
  if (result.deadIndex >= 0) marker(result.deadIndex, "ch-marker-dead", 2, "■ deadlock · " + result.scored[result.deadIndex].frame.ms + " ms");

  svg.appendChild(el("line", { class: "ch-cross", x1: x(selected), x2: x(selected), y1: m.t, y2: m.t + plotH }));
  const pointsOf = values => values.map((value, index) => (index ? "L" : "M") + x(index).toFixed(1) + " " + y(value).toFixed(1)).join(" ");
  svg.appendChild(el("path", { class: "ch-line-recorded", d: pointsOf(result.scored.map(item => item.frame.score)) }));
  svg.appendChild(el("path", { class: "ch-line-formula", d: pointsOf(result.scored.map(item => item.score)) }));
  result.scored.forEach((item, index) => {
    svg.appendChild(el("circle", { class: "ch-point" + (index === selected ? " is-selected" : ""), cx: x(index), cy: y(item.score), r: index === selected ? 6 : 4 }));
  });
  // Hit targets larger than the marks.
  result.scored.forEach((item, index) => {
    const hit = el("rect", { class: "ch-hit", x: x(index) - Math.max(8, plotW / Math.max(count - 1, 1) / 2), y: m.t, width: Math.max(16, plotW / Math.max(count - 1, 1)), height: plotH, tabindex: "-1" });
    hit.addEventListener("mouseenter", () => {
      const box = svg.getBoundingClientRect(), scale = box.width / width;
      placeTip(tip, wrap, x(index) * scale, y(item.score) * scale,
        "<b>Event " + (index + 1) + " · " + item.frame.ms + " ms</b><br>" + escapeHtml(item.frame.title) +
        "<br>Score " + item.score + " (recorded " + item.frame.score + ") · " + item.level);
    });
    hit.addEventListener("mouseleave", () => { tip.hidden = true; });
    hit.addEventListener("click", () => { analysisState.selected = index; renderAnalysisTab(); });
    svg.appendChild(hit);
  });
}

function renderBreakdown(item, index, cfg) {
  const put = (id, value) => { document.getElementById(id).textContent = value; };
  put("an-b-title", "Event " + (index + 1) + " · " + item.frame.ms + " ms · " + item.frame.title);
  const owners = Object.entries(item.frame.owners).map(([lock, thread]) => thread + " holds " + lock);
  const waits = Object.entries(item.frame.waits).map(([thread, lock]) => thread + " waits for " + lock);
  put("an-b-state", owners.concat(waits).join(" · ") || "No locks held and nobody waiting.");
  put("an-b-score", String(item.score));
  const level = document.getElementById("an-b-level");
  level.textContent = item.level === "DEADLOCK" ? "■ DEADLOCK" : item.level === "HIGH" ? "⚠ HIGH RISK" : item.level === "ELEVATED" ? "ELEVATED" : "LOW RISK";
  level.className = "outline-badge " + (item.level === "DEADLOCK" ? "is-danger" : item.level === "HIGH" ? "is-warning" : item.level === "ELEVATED" ? "is-warning" : "is-safe");
  document.getElementById("an-b-rows").innerHTML = item.factors.map((factor, position) =>
    '<div class="an-b-row"><div class="an-b-head"><span><i class="an-key k' + (position + 1) + '"></i>' + factor.label + '</span><strong>' + factor.points.toFixed(1) + ' pts</strong></div>' +
    '<div class="an-b-track"><span style="width:' + Math.max(0, Math.min(100, factor.points)).toFixed(1) + '%;background:' + CHART.factors[position] + '"></span></div>' +
    '<small>' + escapeHtml(factor.raw) + ' · weight ' + factor.weight.toFixed(2) + ' · max ' + (factor.weight * 100).toFixed(0) + ' pts</small></div>').join("");
  put("an-b-rule", "Formula total " + item.total.toFixed(1) + " → score " + item.score + (item.rule ? ". " + item.rule : "."));
}

function renderAnalysisTable(result, selected) {
  document.getElementById("an-rows").innerHTML = result.scored.map((item, index) => {
    const flag = index === result.deadIndex ? '<span class="an-flag is-dead">■ deadlock</span>' : index === result.warnIndex ? '<span class="an-flag is-warn">⚠ warning</span>' : "";
    return '<tr data-index="' + index + '" class="' + (index === selected ? "is-selected" : "") + '">' +
      '<td>' + (index + 1) + '</td><td>' + item.frame.ms + ' ms</td><td>' + escapeHtml(item.frame.title) + flag + '</td>' +
      '<td>' + item.blocked + '</td><td>' + item.frame.waitMs + ' ms</td><td>' + item.frame.heat + '</td>' +
      '<td><span class="an-score lv-' + item.level.toLowerCase() + '">' + item.score + '</span></td></tr>';
  }).join("");
}

document.getElementById("an-rows").addEventListener("click", event => {
  const row = event.target.closest("tr[data-index]");
  if (!row) return;
  analysisState.selected = Number(row.dataset.index);
  renderAnalysisTab();
});
document.getElementById("an-step").addEventListener("input", event => { analysisState.selected = Number(event.target.value); renderAnalysisTab(); });
document.querySelectorAll("[data-an-mode]").forEach(button => button.addEventListener("click", () => {
  analysisState.mode = button.dataset.anMode;
  analysisState.selected = null;
  renderAnalysisTab();
}));

function storeTrial(data, source) {
  const imported = DeadlockTrialData.normalizeTrial(data);
  scenarios[imported.mode] = imported.frames;
  trialMeta[imported.mode] = { source, runId: imported.runId, status: imported.status };
  completed[imported.mode] = false;
  return imported;
}

async function fetchLiveTrial(runMode) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch("/api/trials/" + encodeURIComponent(runMode), { method: "POST", signal: controller.signal });
    if (!response.ok) throw new Error("backend returned " + response.status);
    return storeTrial(await response.json(), "live");
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function withBusy(button, label, task) {
  return async () => {
    if (button.disabled) return;
    const original = button.innerHTML;
    button.disabled = true;
    button.textContent = label;
    try { await task(); } finally { button.disabled = false; button.innerHTML = original; }
  };
}

const anRunLive = document.getElementById("an-run-live");
anRunLive.addEventListener("click", withBusy(anRunLive, "⏳ Running real threads...", async () => {
  try {
    await fetchLiveTrial(analysisState.mode);
    analysisState.selected = null;
    render();
  } catch (error) {
    document.getElementById("an-run-detail").textContent = "Could not run a backend trial (" + error.message + "). Start the FastAPI server and try again.";
  }
}));

function setWeights(values) {
  els.inputWb.value = values.w_b; els.inputWw.value = values.w_w; els.inputWc.value = values.w_c; els.inputWr.value = values.w_r;
  els.inputTh.value = values.threshold;
  syncWeightLabels();
  renderAnalysisTab();
}

function syncWeightLabels() {
  els.valWb.textContent = parseFloat(els.inputWb.value).toFixed(2);
  els.valWw.textContent = parseFloat(els.inputWw.value).toFixed(2);
  els.valWc.textContent = parseFloat(els.inputWc.value).toFixed(2);
  els.valWr.textContent = parseFloat(els.inputWr.value).toFixed(2);
  els.valTh.textContent = els.inputTh.value;
}

[els.inputWb, els.inputWw, els.inputWc, els.inputWr, els.inputTh].forEach(input =>
  input.addEventListener("input", () => { syncWeightLabels(); renderAnalysisTab(); }));
document.getElementById("an-reset").addEventListener("click", () => setWeights(SCORE_DEFAULTS));
document.getElementById("an-normalize").addEventListener("click", () => {
  const cfg = readWeights();
  const sum = cfg.w_b + cfg.w_w + cfg.w_c + cfg.w_r;
  if (sum <= 0) { setWeights(SCORE_DEFAULTS); return; }
  // Round to the slider step (0.05) and push any rounding remainder onto the largest weight.
  const keys = ["w_b", "w_w", "w_c", "w_r"];
  const scaled = keys.map(key => Math.round(cfg[key] / sum * 20) / 20);
  const remainder = Math.round((1 - scaled.reduce((a, b) => a + b, 0)) * 20) / 20;
  scaled[scaled.indexOf(Math.max(...scaled))] += remainder;
  const next = { threshold: cfg.threshold };
  keys.forEach((key, index) => { next[key] = Math.max(0, scaled[index]).toFixed(2); });
  setWeights(next);
});
els.saveWeightsBtn.addEventListener("click", async () => {
  const cfg = readWeights();
  const sum = cfg.w_b + cfg.w_w + cfg.w_c + cfg.w_r;
  const sumEl = document.getElementById("an-sum");
  if (Math.abs(sum - 1) > 0.001) {
    sumEl.textContent = "Weights total " + sum.toFixed(2) + " · press \"Make total 1.00\" before saving.";
    sumEl.className = "an-sum is-bad";
    return;
  }
  try {
    const response = await fetch("/api/analysis/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ w_blocked: cfg.w_b, w_wait: cfg.w_w, w_contention: cfg.w_c, w_resource: cfg.w_r, threshold_high: cfg.threshold })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new Error(error?.detail || "backend returned " + response.status);
    }
    Object.assign(scoringConfig, cfg);
    render();
    sumEl.textContent = "Saved ✓ New backend trials will use these weights and threshold " + cfg.threshold + ".";
    sumEl.className = "an-sum is-ok";
  } catch (error) {
    sumEl.textContent = "Could not save (" + error.message + "). Start the FastAPI server and try again.";
    sumEl.className = "an-sum is-bad";
  }
});

function downloadCsv(filename, rows) {
  const quote = value => '"' + String(value ?? "").replaceAll('"', '""') + '"';
  const blob = new Blob([rows.map(row => row.map(quote).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportCsv() {
  const cfg = readWeights();
  const runMode = analysisState.mode;
  const result = analyzeRun(scenarios[runMode], cfg);
  const rows = [["mode", "run_id", "source", "event", "time_ms", "title", "owner_A", "owner_B", "waiting", "blocked", "longest_wait_ms", "contention", "recorded_score", "formula_score", "level"]];
  result.scored.forEach((item, index) => rows.push([runMode, trialMeta[runMode].runId, trialMeta[runMode].source, index + 1, item.frame.ms, item.frame.title,
    item.frame.owners.A || "", item.frame.owners.B || "", Object.entries(item.frame.waits).map(([t, r]) => t + "→" + r).join(" "),
    item.blocked, item.frame.waitMs, item.frame.heat, item.frame.score, item.score, item.level]));
  downloadCsv("deadlock-lab-" + runMode + "-events.csv", rows);
}

// ---------- Compare ----------
function renderCompare() {
  const vulnerable = DeadlockTrialData.summarize(scenarios.vulnerable, trialMeta.vulnerable.status);
  const protectedRun = DeadlockTrialData.summarize(scenarios.protected, trialMeta.protected.status);
  const put = (id, value) => { document.getElementById(id).textContent = value; };
  put("compare-v-source", trialMeta.vulnerable.source.toUpperCase());
  put("compare-p-source", trialMeta.protected.source.toUpperCase());
  put("compare-v-title", vulnerable.status === "deadlock" ? "Circular wait formed" : "Threads completed");
  put("compare-v-description", vulnerable.status === "deadlock" ? "T1 holds A and waits for B while T2 holds B and waits for A." : "This vulnerable trial finished without a cycle.");
  put("compare-v-result", vulnerable.status === "deadlock" ? "DEADLOCK" : "COMPLETE");
  put("compare-v-blocked", vulnerable.blockedPeak + " / 2");
  put("compare-v-cycle", vulnerable.cycle ? "Cycle found" : "No cycle");
  put("compare-v-score", vulnerable.peakScore + " / 100");
  put("compare-v-lead", vulnerable.warningLeadMs === null ? "—" : vulnerable.warningLeadMs + " ms");
  put("compare-p-title", protectedRun.status === "completed" ? "Both threads finished" : "Circular wait formed");
  put("compare-p-description", protectedRun.status === "completed" ? "Both threads take A before B, so neither can hold what the other needs." : "This trial still ended in deadlock; review its lock ordering.");
  put("compare-p-result", protectedRun.status === "completed" ? "COMPLETE" : "DEADLOCK");
  put("compare-p-completed", protectedRun.completedThreads + " / 2");
  put("compare-p-cycle", protectedRun.cycle ? "Cycle found" : "No cycle");
  put("compare-p-score", protectedRun.peakScore + " / 100");
  put("compare-p-duration", protectedRun.status === "completed" ? protectedRun.durationMs + " ms" : "—");
  document.getElementById("compare-v-result").className = "compare-big " + (vulnerable.status === "deadlock" ? "danger-text" : "safe-text");
  document.getElementById("compare-p-result").className = "compare-big " + (protectedRun.status === "deadlock" ? "danger-text" : "safe-text");
  const sources = [trialMeta.vulnerable, trialMeta.protected];
  put("cmp-source-note", sources.every(meta => meta.source === "demo")
    ? "Showing built-in demonstration runs. Run both modes on the backend for real measurements."
    : "Vulnerable: " + sourceText(trialMeta.vulnerable) + " · Protected: " + sourceText(trialMeta.protected) + ".");
  put("compare-insight-text", vulnerable.status === "deadlock" && protectedRun.status === "completed"
    ? "Same two threads, same two locks. Opposite lock order deadlocked (peak score " + vulnerable.peakScore + (vulnerable.warningLeadMs !== null ? ", warning " + vulnerable.warningLeadMs + " ms before the cycle" : "") +
      "); a common A → B order finished both threads with a peak score of " + protectedRun.peakScore + "." +
      (sources.every(meta => meta.source === "demo") ? " These are demonstration values." : "")
    : "These runs do not show the expected contrast. Check the event logs in the Analysis tab before drawing a conclusion.");
  renderCompareChart();
}

function renderCompareChart() {
  const svg = document.getElementById("cmp-chart");
  const wrap = svg.parentNode, tip = document.getElementById("cmp-tip");
  const height = 270;
  const width = chartFrame(svg, height);
  const m = { l: 40, r: 104, t: 16, b: 34 };
  const plotW = width - m.l - m.r, plotH = height - m.t - m.b;
  const y = value => m.t + (1 - value / 100) * plotH;
  yAxis(svg, { ticks: [0, 25, 50, 75, 100], y, left: m.l, right: m.l + plotW, format: String });
  const threshold = scoringConfig.threshold;
  svg.appendChild(el("line", { class: "ch-threshold", x1: m.l, x2: m.l + plotW, y1: y(threshold), y2: y(threshold) }));
  svg.appendChild(el("text", { class: "ch-axis-label", x: m.l, y: m.t + plotH + 18 }, "start"));
  svg.appendChild(el("text", { class: "ch-axis-label", x: m.l + plotW, y: m.t + plotH + 18, "text-anchor": "end" }, "end of run"));

  const series = ["vulnerable", "protected"].map(runMode => {
    const frames = scenarios[runMode];
    const x = index => m.l + (frames.length <= 1 ? 0 : index / (frames.length - 1) * plotW);
    return { runMode, frames, x, color: CHART[runMode] };
  });
  series.forEach(item => {
    svg.appendChild(el("path", { class: "ch-line-" + (item.runMode === "vulnerable" ? "vuln" : "prot"),
      d: item.frames.map((frame, index) => (index ? "L" : "M") + item.x(index).toFixed(1) + " " + y(frame.score).toFixed(1)).join(" ") }));
  });
  series.forEach(item => item.frames.forEach((frame, index) => {
    const cycle = DeadlockTrialData.hasCycle(frame);
    svg.appendChild(el("circle", { class: "ch-point-" + (item.runMode === "vulnerable" ? "vuln" : "prot") + (cycle ? " is-cycle" : ""), cx: item.x(index), cy: y(frame.score), r: cycle ? 6 : 4 }));
    const hit = el("circle", { class: "ch-hit", cx: item.x(index), cy: y(frame.score), r: 12 });
    hit.addEventListener("mouseenter", () => {
      const box = svg.getBoundingClientRect(), scale = box.width / width;
      placeTip(tip, wrap, item.x(index) * scale, y(frame.score) * scale,
        "<b>" + (item.runMode === "vulnerable" ? "Vulnerable" : "Protected") + " · " + frame.ms + " ms</b><br>" + escapeHtml(frame.title) + "<br>Score " + frame.score + (cycle ? " · deadlock" : ""));
    });
    hit.addEventListener("mouseleave", () => { tip.hidden = true; });
    svg.appendChild(hit);
  }));
  // Direct end labels, nudged apart vertically if the two runs end close together.
  const labels = series.map(item => ({ item, y: y(item.frames[item.frames.length - 1].score) - 2, gap: 30 }));
  labels.push({ threshold: true, y: y(threshold) + 4, gap: 18 });
  spreadLabels(labels, m.t + 8, m.t + plotH);
  labels.forEach(label => {
    if (label.threshold) { svg.appendChild(el("text", { class: "ch-threshold-label", x: m.l + plotW + 10, y: label.y }, "threshold " + threshold)); return; }
    const last = label.item.frames[label.item.frames.length - 1];
    svg.appendChild(el("text", { class: "ch-end-label", x: m.l + plotW + 10, y: label.y }, label.item.runMode === "vulnerable" ? "Vulnerable" : "Protected"));
    svg.appendChild(el("text", { class: "ch-end-sub", x: m.l + plotW + 10, y: label.y + 13 }, DeadlockTrialData.hasCycle(last) ? "deadlock" : "finished"));
  });
}

const cmpRunBoth = document.getElementById("cmp-run-both");
cmpRunBoth.addEventListener("click", withBusy(cmpRunBoth, "⏳ Running both modes...", async () => {
  try {
    await fetchLiveTrial("vulnerable");
    await fetchLiveTrial("protected");
    analysisState.selected = null;
    render();
  } catch (error) {
    document.getElementById("cmp-source-note").textContent = "Could not run backend trials (" + error.message + "). Start the FastAPI server and try again.";
  }
}));

// ---------- Repeated trials ----------
let lastBatch = null;
async function runBatchComparison() {
  const count = Number(document.getElementById("batch-count").value);
  const section = els.batchSection;
  const response = await fetch("/api/analysis/compare?trials_per_mode=" + count + "&timeout=3.0", { method: "POST" });
  if (!response.ok) throw new Error("backend returned " + response.status);
  const data = await response.json();
  lastBatch = data;
  section.hidden = false;
  const v = data.vulnerable, p = data.protected;
  const bar = (label, value, total, cls) =>
    '<div class="cmp-rate"><div class="cmp-rate-head"><span>' + label + '</span><strong>' + value + ' / ' + total + ' · ' + Math.round(value / Math.max(total, 1) * 100) + '%</strong></div>' +
    '<div class="cmp-rate-track"><span class="' + cls + '" style="width:' + (value / Math.max(total, 1) * 100).toFixed(1) + '%"></span></div></div>';
  const chips = trials => '<div class="cmp-trials">' + trials.map((trial, index) => {
    const dead = trial.deadlock_detected || trial.has_cycle;
    return '<span class="cmp-trial ' + (dead ? "is-dead" : trial.status === "completed" ? "is-ok" : "is-other") + '" title="Trial ' + (index + 1) + ': ' +
      (dead ? "deadlock" : trial.status) + ' · ' + trial.completion_time_ms + ' ms · peak score ' + trial.peak_score + '">' + (dead ? "■" : "✓") + '</span>';
  }).join("") + '</div>';
  document.getElementById("batch-rates").innerHTML =
    '<div class="cmp-rate-group"><h3>Vulnerable · opposite lock order</h3>' + bar("■ Deadlocked", v.deadlock_count, v.total_trials, "is-dead") + bar("✓ Completed", v.completion_count, v.total_trials, "is-ok") + chips(v.trials) + '</div>' +
    '<div class="cmp-rate-group"><h3>Protected · common lock order</h3>' + bar("■ Deadlocked", p.deadlock_count, p.total_trials, "is-dead") + bar("✓ Completed", p.completion_count, p.total_trials, "is-ok") + chips(p.trials) + '</div>';
  const row = (name, s) => '<tr><td><strong>' + name + '</strong></td><td>' + s.total_trials + '</td><td>' + s.deadlock_count + ' (' + s.deadlock_rate_percent + '%)</td><td>' +
    s.completion_count + ' (' + s.completion_rate_percent + '%)</td><td>' + (s.mean_warning_lead_time_ms == null ? "—" : s.mean_warning_lead_time_ms + " ms") + '</td><td>' +
    s.mean_peak_wait_ms + ' ms</td><td>' + s.mean_trial_runtime_ms + ' ms</td></tr>';
  els.batchTbody.innerHTML = row("Vulnerable", v) + row("Protected", p);
  els.batchDesc.textContent = data.insight + " " + (data.scientific_disclaimer || "");
  document.getElementById("batch-table-title").textContent = "Deadlock rate by mode · " + count + " trials each";
  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

els.batchBtn.addEventListener("click", withBusy(els.batchBtn, "⏳ Running trials...", async () => {
  try { await runBatchComparison(); }
  catch (error) { els.batchSection.hidden = false; els.batchDesc.textContent = "Repeated trials failed (" + error.message + "). Start the FastAPI server and try again."; }
}));
document.getElementById("batch-export").addEventListener("click", () => {
  if (!lastBatch) return;
  const rows = [["mode", "trial", "status", "deadlock", "run_time_ms", "peak_score", "peak_wait_ms", "warning_lead_ms"]];
  ["vulnerable", "protected"].forEach(runMode => lastBatch[runMode].trials.forEach((trial, index) => rows.push([runMode, index + 1, trial.status,
    trial.deadlock_detected || trial.has_cycle, trial.completion_time_ms, trial.peak_score, trial.peak_wait_ms, trial.warning_lead_time_ms ?? ""])));
  downloadCsv("deadlock-lab-repeated-trials.csv", rows);
});

// ---------- Scaling test ----------
const SCALE_COUNTS = [2, 4, 8, 16, 32];
const scaleSelected = new Set(SCALE_COUNTS);
let scaleResults = [];
document.getElementById("scale-counts").innerHTML = SCALE_COUNTS.map(count =>
  '<button type="button" class="cmp-count is-on" data-count="' + count + '" aria-pressed="true">' + count + '</button>').join("");
document.getElementById("scale-counts").addEventListener("click", event => {
  const button = event.target.closest("[data-count]");
  if (!button) return;
  const count = Number(button.dataset.count);
  if (scaleSelected.has(count) && scaleSelected.size > 1) scaleSelected.delete(count); else scaleSelected.add(count);
  button.classList.toggle("is-on", scaleSelected.has(count));
  button.setAttribute("aria-pressed", String(scaleSelected.has(count)));
});

function renderScaleChart() {
  const svg = document.getElementById("scale-chart");
  const wrap = svg.parentNode, tip = document.getElementById("scale-tip");
  const height = 270;
  const width = chartFrame(svg, height);
  const m = { l: 52, r: 104, t: 16, b: 38 };
  const plotW = width - m.l - m.r, plotH = height - m.t - m.b;
  const counts = scaleResults.map(item => item.threads);
  const maxValue = niceMax(Math.max(1, ...scaleResults.flatMap(item => [item.vulnerable.completion_time_ms, item.protected.completion_time_ms])));
  const x = index => m.l + (counts.length <= 1 ? plotW / 2 : index / (counts.length - 1) * plotW);
  const y = value => m.t + (1 - value / maxValue) * plotH;
  yAxis(svg, { ticks: [0, 0.25, 0.5, 0.75, 1].map(f => f * maxValue), y, left: m.l, right: m.l + plotW, format: value => Math.round(value) + " ms" });
  counts.forEach((count, index) => svg.appendChild(el("text", { class: "ch-axis-label", x: x(index), y: m.t + plotH + 18, "text-anchor": "middle" }, String(count))));
  svg.appendChild(el("text", { class: "ch-axis-title", x: m.l + plotW + 8, y: m.t + plotH + 18 }, "threads →"));
  const ends = [];
  ["vulnerable", "protected"].forEach(runMode => {
    const values = scaleResults.map(item => item[runMode].completion_time_ms);
    svg.appendChild(el("path", { class: "ch-line-" + (runMode === "vulnerable" ? "vuln" : "prot"),
      d: values.map((value, index) => (index ? "L" : "M") + x(index).toFixed(1) + " " + y(value).toFixed(1)).join(" ") }));
    values.forEach((value, index) => {
      svg.appendChild(el("circle", { class: "ch-point-" + (runMode === "vulnerable" ? "vuln" : "prot"), cx: x(index), cy: y(value), r: 4.5 }));
      const hit = el("circle", { class: "ch-hit", cx: x(index), cy: y(value), r: 12 });
      hit.addEventListener("mouseenter", () => {
        const item = scaleResults[index], run = item[runMode];
        const box = svg.getBoundingClientRect(), scale = box.width / width;
        placeTip(tip, wrap, x(index) * scale, y(value) * scale, "<b>" + item.threads + " threads · " + runMode + "</b><br>" + run.completion_time_ms + " ms · " +
          (runMode === "vulnerable" ? (run.metrics.deadlock_cycle ? (run.metrics.deadlock_cycle.length - 1) + "-thread cycle, " : "") + run.metrics.threads_completed + " finished" : run.metrics.threads_completed + " of " + item.threads + " finished"));
      });
      hit.addEventListener("mouseleave", () => { tip.hidden = true; });
      svg.appendChild(hit);
    });
    if (values.length) ends.push({ runMode, y: y(values[values.length - 1]) });
  });
  ends.forEach(end => { end.y += 4; end.gap = 18; });
  spreadLabels(ends, m.t + 8, m.t + plotH);
  ends.forEach(end => svg.appendChild(el("text", { class: "ch-end-label", x: m.l + plotW + 10, y: end.y }, end.runMode === "vulnerable" ? "Vulnerable" : "Protected")));
}

function renderScaleResults() {
  document.getElementById("scale-rows").innerHTML = scaleResults.map(item => {
    const v = item.vulnerable, p = item.protected;
    const cycle = v.metrics.deadlock_cycle ? v.metrics.deadlock_cycle.length - 1 : 0;
    const aborted = (v.workers || []).filter(worker => worker.outcome === "aborted").length;
    return '<tr><td><strong>' + item.threads + '</strong></td><td>' + (cycle ? cycle + " threads" : "none") + '</td><td>' + (v.snapshot && v.snapshot.label === "deadlock" ? Number(v.snapshot.time_ms).toFixed(1) + " ms" : "—") + '</td><td>' +
      v.metrics.threads_completed + ' / ' + aborted + '</td><td>' + v.completion_time_ms + ' ms</td><td>' + p.metrics.threads_completed + ' / ' + item.threads + '</td><td>' +
      (p.snapshot ? Object.keys(p.snapshot.waits).length : 0) + '</td><td>' + p.completion_time_ms + ' ms</td></tr>';
  }).join("");
  renderScaleChart();
  const allCycles = scaleResults.every(item => (item.vulnerable.metrics.deadlock_cycle || []).length - 1 === item.threads);
  const allProtected = scaleResults.every(item => item.protected.status === "completed" && item.protected.metrics.threads_completed === item.threads);
  const detect = scaleResults.map(item => item.vulnerable.snapshot && item.vulnerable.snapshot.label === "deadlock" ? item.vulnerable.snapshot.time_ms : null).filter(value => value !== null);
  const range = scaleResults.map(item => item.threads);
  document.getElementById("scale-insight").textContent = scaleResults.length
    ? (allCycles ? "In every vulnerable run the deadlock cycle went through all N threads (" + Math.min(...range) + "–" + Math.max(...range) + "), and it was detected within " + Math.max(...detect).toFixed(1) + " ms. " : "Not every vulnerable run formed a full-length cycle; check the table. ") +
      (allProtected ? "Every protected run finished all of its threads. " : "Some protected runs did not finish all threads; check the table. ") +
      "Vulnerable run time grows with thread count because, after the victim is aborted, the remaining threads finish one after another."
    : "Results appear here after the test.";
}

const scaleRun = document.getElementById("scale-run");
scaleRun.addEventListener("click", withBusy(scaleRun, "⏳ Running...", async () => {
  const counts = SCALE_COUNTS.filter(count => scaleSelected.has(count));
  const progress = document.getElementById("scale-progress");
  document.getElementById("scale-section").hidden = false;
  scaleResults = [];
  renderScaleResults();
  const total = counts.length * 2;
  let done = 0;
  try {
    for (const threads of counts) {
      const entry = { threads };
      for (const runMode of ["vulnerable", "protected"]) {
        progress.textContent = "Running " + threads + " threads · " + runMode + " (" + (done + 1) + " of " + total + ")…";
        const response = await fetch("/api/experiments/multi-thread", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: runMode, thread_count: threads, timeout_seconds: 5 }) });
        if (!response.ok) throw new Error("backend returned " + response.status);
        entry[runMode] = await response.json();
        done += 1;
      }
      scaleResults.push(entry);
      renderScaleResults();
    }
    progress.textContent = "Finished " + total + " runs on real threads.";
  } catch (error) {
    progress.textContent = "Scaling test stopped (" + error.message + "). Start the FastAPI server and try again.";
  }
}));
document.getElementById("scale-export").addEventListener("click", () => {
  if (!scaleResults.length) return;
  const rows = [["threads", "mode", "status", "cycle_length", "detected_ms", "finished", "aborted", "peak_queued", "run_time_ms"]];
  scaleResults.forEach(item => ["vulnerable", "protected"].forEach(runMode => {
    const run = item[runMode];
    rows.push([item.threads, runMode, run.status, run.metrics.deadlock_cycle ? run.metrics.deadlock_cycle.length - 1 : 0,
      run.snapshot && run.snapshot.label === "deadlock" ? run.snapshot.time_ms : "", run.metrics.threads_completed,
      (run.workers || []).filter(worker => worker.outcome === "aborted").length, run.snapshot ? Object.keys(run.snapshot.waits).length : 0, run.completion_time_ms]);
  }));
  downloadCsv("deadlock-lab-scaling-test.csv", rows);
});

// Charts are drawn at their rendered width, so redraw them when a tab opens or the window resizes.
document.addEventListener("lab:view", event => {
  if (event.detail.name === "analysis") renderAnalysisTab();
  if (event.detail.name === "compare") { renderCompare(); if (scaleResults.length) renderScaleChart(); }
});
let resizeTimer = null;
window.addEventListener("resize", () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(() => { renderAnalysisTab(); renderCompareChart(); if (scaleResults.length) renderScaleChart(); }, 150);
});
syncWeightLabels();

window.DeadlockLab = { loadTrial, restoreDemo, runLiveTrial, runBatchComparison };
render();
