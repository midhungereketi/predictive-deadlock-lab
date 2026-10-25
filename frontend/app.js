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
  analysisStatus: document.getElementById("analysis-status"),
  analysisBars: document.getElementById("analysis-bars"),
  analysisOwnerA: document.getElementById("analysis-owner-a"),
  analysisOwnerB: document.getElementById("analysis-owner-b"),
  analysisWaits: document.getElementById("analysis-waits"),
  analysisT2Path: document.getElementById("analysis-t2-path"),
  analysisOrderNote: document.getElementById("analysis-order-note"),
  compareEmpty: document.getElementById("compare-empty"),
  compareResults: document.getElementById("compare-results"),
  compareRunBtn: document.getElementById("compare-run-button"),
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
    return '<div class="analysis-bar-wrap" style="--i:' + index + '"><span class="analysis-bar-value">' + item.score + '</span><span class="analysis-bar ' + state + '" style="--i:' + index + ';height:' + Math.max(item.score, 3) + '%"></span><span class="analysis-bar-label">' + String(index).padStart(2, "0") + '</span></div>';
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
  els.compareEmpty.hidden = show || !els.batchSection.hidden;
  els.compareResults.hidden = !show;
  els.compareRunBtn.disabled = !show;
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
        (trialMeta.vulnerable.source === "demo" && trialMeta.protected.source === "demo" ? "These are browser demonstration outcomes." : "Recorded trial values are shown as provided.")
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
    document.startViewTransition(() => applyView(name)).finished.finally(() => { showView.inTransition = false; });
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

function loadTrial(data, source = "imported") {
  const imported = DeadlockTrialData.normalizeTrial(data);
  if (!["imported", "live"].includes(source)) throw new Error("Unsupported trial source.");
  stopPlayback();
  scenarios[imported.mode] = imported.frames;
  trialMeta[imported.mode] = { source, runId: imported.runId, status: imported.status };
  completed[imported.mode] = false;
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
els.compareRunBtn.addEventListener("click", renderCompare);
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

function threadNumber(threadId) { return Number(String(threadId).slice(1)); }

function renderMultiThreadGraph(result, cycleNodes) {
  const graph = document.getElementById("multi-thread-graph");
  const workers = result.workers || [];
  const snapshot = result.snapshot || { owners: {}, waits: {}, label: "none" };
  const count = workers.length;
  // Size the drawing to its rendered width so node and edge labels stay legible on narrow screens.
  const viewWidth = Math.max(320, Math.min(720, Math.round(graph.getBoundingClientRect().width) || 720));
  const viewHeight = viewWidth >= 600 ? 420 : Math.round(viewWidth * 0.95);
  const narrow = viewWidth < 600;
  // Per-node "holds/wants" labels only fit when there is room; the table repeats them.
  const dense = count > 12 || (narrow && count > 5);
  const centerX = viewWidth / 2, centerY = viewHeight / 2;
  const nodeRadius = Math.round((count <= 8 ? 26 : count <= 16 ? 18 : 12) * (narrow ? 0.7 : 1));
  const radiusX = (count <= 2 ? 0.6 : 1) * (centerX - nodeRadius - 46);
  const radiusY = centerY - nodeRadius - 26;
  const positions = {};
  workers.forEach((worker, index) => {
    const angle = -Math.PI / 2 + index * Math.PI * 2 / count;
    positions[worker.thread] = { x: centerX + Math.cos(angle) * radiusX, y: centerY + Math.sin(angle) * radiusY };
  });

  const edges = Object.entries(snapshot.waits)
    .map(([waiter, resource]) => ({ waiter, resource, owner: snapshot.owners[resource] }))
    .filter(edge => edge.owner && positions[edge.waiter] && positions[edge.owner]);

  const edgeMarkup = edges.map(edge => {
    const from = positions[edge.waiter], to = positions[edge.owner];
    const mutual = edges.some(other => other.waiter === edge.owner && other.owner === edge.waiter);
    const isCycle = cycleNodes.has(edge.waiter) && cycleNodes.has(edge.owner);
    const dx = to.x - from.x, dy = to.y - from.y;
    const length = Math.hypot(dx, dy) || 1;
    // Bend edges outward from the ring centre so neighbouring arrows stay readable.
    const midX = (from.x + to.x) / 2, midY = (from.y + to.y) / 2;
    const outX = midX - centerX, outY = midY - centerY;
    const outLength = Math.hypot(outX, outY) || 1;
    const bend = mutual ? 46 : Math.min(28, length * 0.18);
    const ctrlX = midX + (mutual ? -dy / length : outX / outLength) * bend;
    const ctrlY = midY + (mutual ? dx / length : outY / outLength) * bend;
    const startLen = Math.hypot(ctrlX - from.x, ctrlY - from.y) || 1;
    const endLen = Math.hypot(to.x - ctrlX, to.y - ctrlY) || 1;
    const startX = from.x + (ctrlX - from.x) / startLen * (nodeRadius + 2);
    const startY = from.y + (ctrlY - from.y) / startLen * (nodeRadius + 2);
    const endX = to.x - (to.x - ctrlX) / endLen * (nodeRadius + 7);
    const endY = to.y - (to.y - ctrlY) / endLen * (nodeRadius + 7);
    const label = dense ? "" :
      '<text class="multi-graph-edge-label' + (isCycle ? " is-cycle" : "") + '" x="' + ctrlX.toFixed(1) + '" y="' + (ctrlY + 4).toFixed(1) + '">' + escapeHtml(edge.resource) + '</text>';
    return '<path class="multi-graph-edge' + (isCycle ? " is-cycle" : "") + '" d="M ' + startX.toFixed(1) + ' ' + startY.toFixed(1) +
      ' Q ' + ctrlX.toFixed(1) + ' ' + ctrlY.toFixed(1) + ' ' + endX.toFixed(1) + ' ' + endY.toFixed(1) +
      '" marker-end="url(#' + (isCycle ? "multi-arrow-danger" : "multi-arrow") + ')"/>' + label;
  }).join("");

  const nodeMarkup = workers.map(worker => {
    const position = positions[worker.thread];
    const held = Object.entries(snapshot.owners).filter(([, owner]) => owner === worker.thread).map(([resource]) => resource);
    const waiting = snapshot.waits[worker.thread];
    const isVictim = worker.thread === result.victim;
    const className = (cycleNodes.has(worker.thread) ? " is-cycle" : waiting ? " is-waiting" : held.length ? " is-holding" : "") + (isVictim ? " is-victim" : "");
    const state = dense ? "" :
      '<text class="multi-graph-state" y="' + (nodeRadius + 15) + '">' + escapeHtml((held.length ? "holds " + held.join("+") : "") + (waiting ? (held.length ? " · " : "") + "wants " + waiting : "")) + '</text>';
    return '<g class="multi-graph-node' + className + '" transform="translate(' + position.x.toFixed(1) + ' ' + position.y.toFixed(1) + ')">' +
      '<title>' + escapeHtml(worker.thread + " (OS thread " + worker.native_id + "): " + worker.outcome) + '</title>' +
      '<circle r="' + nodeRadius + '"/><text class="multi-graph-id" y="' + (count > 16 ? 3 : 4) + '">' + worker.thread + '</text>' + state + '</g>';
  }).join("");

  graph.innerHTML = '<defs>' +
    '<marker id="multi-arrow" markerWidth="9" markerHeight="9" refX="7" refY="3.5" orient="auto"><path d="M0,0 L0,7 L8,3.5 z" fill="#ffb547"/></marker>' +
    '<marker id="multi-arrow-danger" markerWidth="9" markerHeight="9" refX="7" refY="3.5" orient="auto"><path d="M0,0 L0,7 L8,3.5 z" fill="#ff4d6d"/></marker>' +
    '</defs>' + edgeMarkup + nodeMarkup;
  graph.setAttribute("viewBox", "0 0 " + viewWidth + " " + viewHeight);
  graph.classList.toggle("is-dense", count > 16);
  graph.setAttribute("aria-label", count + " worker threads and " + edges.length + " wait-for edges");
  document.getElementById("multi-thread-graph-heading").textContent = snapshot.label === "deadlock"
    ? "Wait-for graph at detection · " + edges.length + " threads waiting in a circle"
    : "Wait-for graph at peak contention · " + edges.length + " of " + count + " threads queued";
}

function renderMultiThreadTimeline(result) {
  const svg = document.getElementById("multi-thread-timeline");
  const workers = result.workers || [];
  const total = Math.max(1, result.completion_time_ms);
  const rowHeight = workers.length <= 12 ? 22 : workers.length <= 20 ? 15 : 11;
  // Match the drawing width to the rendered width so labels stay legible on narrow screens.
  const viewWidth = Math.max(340, Math.round(svg.getBoundingClientRect().width) || 720);
  const left = 46, right = 14, top = 8, axis = 24;
  const width = viewWidth - left - right;
  const height = top + rowHeight * workers.length + axis;
  const x = ms => left + Math.min(1, Math.max(0, ms / total)) * width;
  const lanes = {};
  workers.forEach(worker => { lanes[worker.thread] = { held: 0, holdStart: null, waitStart: null, segments: [] }; });
  let deadlockMs = null, recoveryMs = null;

  for (const event of result.events) {
    const ms = event.time * 1000;
    if (event.action === "deadlock_detected") deadlockMs = ms;
    if (event.action === "recovery") recoveryMs = ms;
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
    markup += '<text class="timeline-label' + (isVictim ? " is-victim" : "") + '" x="' + (left - 8) + '" y="' + (y + rowHeight / 2 + 3.5) + '">' + worker.thread + '</text>';
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
    markup += '<line class="timeline-marker" x1="' + x(deadlockMs) + '" x2="' + x(deadlockMs) + '" y1="' + top + '" y2="' + chartBottom + '"/>' +
      '<text class="timeline-marker-label" x="' + (x(deadlockMs) + 4) + '" y="' + (chartBottom + 18) + '">deadlock detected' + (recoveryMs !== null && result.victim ? " → abort " + result.victim : "") + '</text>';
  }
  for (let tick = 0; tick <= 4; tick += 1) {
    const tx = left + width * tick / 4;
    markup += '<text class="timeline-tick" x="' + tx + '" y="' + (chartBottom + (deadlockMs !== null ? 8 : 16)) + '">' + Math.round(total * tick / 4) + ' ms</text>';
  }
  svg.setAttribute("viewBox", "0 0 " + viewWidth + " " + (height + 4));
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

  panel.hidden = false;
  renderMultiThreadGraph(result, cycleNodes);
  renderMultiThreadTimeline(result);

  const outcomeLabels = { completed: "Completed", aborted: "Aborted (victim)", timed_out: "Timed out", error: "Error" };
  document.getElementById("multi-thread-worker-list").innerHTML = workers.map(worker => {
    const inCycle = cycleNodes.has(worker.thread);
    return '<tr class="' + (worker.outcome === "completed" ? "is-ok" : "is-failed") + '">' +
      '<td><strong>' + worker.thread + '</strong>' + (inCycle ? ' <span class="cycle-tag">in cycle</span>' : '') + '</td>' +
      '<td>' + (worker.native_id ?? "—") + '</td>' +
      '<td>' + worker.lock_order.join(" → ") + '</td>' +
      '<td>' + worker.waited_ms + ' ms</td>' +
      '<td class="outcome">' + (outcomeLabels[worker.outcome] || escapeHtml(worker.outcome)) + '</td></tr>';
  }).join("");

  badge.textContent = result.status === "deadlock" ? "DEADLOCK · " + (cycle.length - 1) + "-THREAD CYCLE" : result.status.toUpperCase();
  badge.className = "outline-badge" + (result.status === "deadlock" ? " is-danger" : result.status === "completed" ? " is-safe" : " is-warning");

  const ring = count > 4 ? "T1 → T2 → … → T" + count + " → T1" : cycle.join(" → ");
  document.getElementById("multi-thread-summary").textContent = result.status === "deadlock"
    ? "Each of the " + count + " threads took its first lock and then waited for the next thread's lock, forming one circular wait through all " +
      (cycle.length - 1) + " threads (" + ring + "). The supervisor detected the cycle " + Number(result.snapshot.time_ms).toFixed(1) + " ms after the threads started and aborted " +
      result.victim + "; the other " + completedCount + " threads then finished."
    : result.status === "completed"
      ? "All " + completedCount + " of " + count + " threads finished. Each took its two locks in global order (lower number first), so up to " +
        peakQueued + " threads queued at once but no circular wait could form."
      : result.error || "The run ended without a confirmed terminal outcome.";

  document.getElementById("multi-thread-metric-workers").textContent = metrics.threads_started + " / " + count;
  document.getElementById("multi-thread-metric-os").textContent = osIds.size + " distinct";
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
      if (els.compareEmpty) els.compareEmpty.hidden = true;
      els.sourceBadge.textContent = "MEASURED BATCH";
      const v = data.vulnerable;
      const p = data.protected;

      els.batchTbody.innerHTML = `
        <tr style="color:var(--red);">
          <td><strong>Vulnerable (Opposite A/B)</strong></td>
          <td>${v.total_trials}</td>
          <td><strong>${v.deadlock_rate_percent}%</strong> (${v.deadlock_count}/${v.total_trials})</td>
          <td>${v.completion_rate_percent}% (${v.completion_count}/${v.total_trials})</td>
          <td>${v.mean_warning_lead_time_ms == null ? "N/A" : v.mean_warning_lead_time_ms + " ms"}</td>
          <td>${v.mean_detection_latency_ms == null ? "N/A" : v.mean_detection_latency_ms + " ms"}</td>
          <td>${v.mean_peak_wait_ms} ms</td>
          <td>${v.mean_trial_runtime_ms} ms</td>
        </tr>
        <tr style="color:var(--green);">
          <td><strong>Protected (learned shared order)</strong></td>
          <td>${p.total_trials}</td>
          <td><strong>${p.deadlock_rate_percent}%</strong> (${p.deadlock_count}/${p.total_trials})</td>
          <td><strong>${p.completion_rate_percent}%</strong> (${p.completion_count}/${p.total_trials})</td>
          <td>N/A (No deadlock)</td>
          <td>N/A (No cycle)</td>
          <td>${p.mean_peak_wait_ms} ms</td>
          <td>${p.mean_trial_runtime_ms} ms</td>
        </tr>
      `;
      if (els.batchDesc && data.insight) {
        els.batchDesc.textContent = data.insight;
      }
    }
    showImportFeedback("Batch request finished. Review the measured rates and any inconclusive trials in the table below.", true);
  } catch (err) {
    showImportFeedback("Batch comparison failed: " + err.message + ". Check the FastAPI server or hosted deployment.", false);
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
      const proposed = {
        w_b: parseFloat(els.inputWb.value),
        w_w: parseFloat(els.inputWw.value),
        w_c: parseFloat(els.inputWc.value),
        w_r: parseFloat(els.inputWr.value),
        threshold: parseInt(els.inputTh.value, 10)
      };
      const weightSum = proposed.w_b + proposed.w_w + proposed.w_c + proposed.w_r;
      if (Math.abs(weightSum - 1) > 0.001) {
        showImportFeedback("The four scoring weights must add up to 1.00; current total is " + weightSum.toFixed(2) + ".", false);
        return;
      }
      try {
        const response = await fetch("/api/analysis/config", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            w_blocked: proposed.w_b,
            w_wait: proposed.w_w,
            w_contention: proposed.w_c,
            w_resource: proposed.w_r,
            threshold_high: proposed.threshold
          })
        });
        if (!response.ok) {
          const error = await response.json().catch(() => null);
          throw new Error(error?.detail || "Backend returned " + response.status);
        }
        Object.assign(scoringConfig, proposed);
        render();
        showImportFeedback("Saved scoring settings for future backend trials. Existing trial scores were not recalculated.", true);
      } catch (error) {
        showImportFeedback("Could not save scoring settings: " + error.message + ". Check the FastAPI server or hosted deployment.", false);
      }
    });
  }
}

setupWeightControls();

window.DeadlockLab = { loadTrial, restoreDemo, runLiveTrial, runBatchComparison };
render();
