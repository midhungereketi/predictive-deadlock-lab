/* Motion layer for the lab. app.js owns state; this file only listens to
   "lab:frame" / "lab:view" events and animates what app.js has rendered. */
(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const easeOut = t => 1 - Math.pow(1 - t, 4);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- Intro (skipped on repeat visits in the same tab) ---------- */
  const intro = $(".intro");
  let seen = false;
  try { seen = sessionStorage.getItem("dl-intro") === "1"; sessionStorage.setItem("dl-intro", "1"); } catch (_) { /* storage unavailable */ }
  const introMs = reduce || seen ? 0 : 1750;
  if (introMs === 0) intro.remove();
  else window.setTimeout(() => { intro.classList.add("is-done"); window.setTimeout(() => intro.remove(), 1100); }, introMs);

  /* ---------- Split headings into masked words ---------- */
  $$(".split").forEach(heading => {
    let i = 0;
    const wrap = node => {
      [...node.childNodes].forEach(child => {
        if (child.nodeType === 3) {
          const frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach(part => {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.append(part); return; }
            const w = document.createElement("span"); w.className = "w";
            const inner = document.createElement("span"); inner.textContent = part; inner.style.setProperty("--i", i++);
            w.append(inner); frag.append(w);
          });
          child.replaceWith(frag);
        } else if (child.nodeType === 1) wrap(child);
      });
    };
    wrap(heading);
  });

  /* ---------- Scroll reveals with per-group stagger ---------- */
  const groups = new Map();
  $$("[data-reveal]").forEach(el => {
    const parent = el.parentElement;
    const n = groups.get(parent) || 0;
    el.style.setProperty("--d", n);
    groups.set(parent, n + 1);
  });
  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add("is-in"); io.unobserve(entry.target); }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
  window.setTimeout(() => $$("[data-reveal], .split").forEach(el => io.observe(el)), Math.max(0, introMs - 250));

  /* ---------- Nav glider ---------- */
  const glider = $(".nav-glider");
  const moveGlider = () => {
    const active = $(".nav-item.is-active");
    if (!active) return;
    glider.style.width = active.offsetWidth + "px";
    glider.style.transform = "translateX(" + (active.offsetLeft) + "px)";
  };
  moveGlider();
  document.fonts?.ready.then(moveGlider);
  window.addEventListener("resize", moveGlider);
  document.addEventListener("lab:view", moveGlider);

  /* ---------- Magnetic buttons + card spotlight (fine pointers only) ---------- */
  if (finePointer && !reduce) {
    $$(".magnetic").forEach(el => {
      el.addEventListener("pointermove", e => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) * 0.22;
        const y = (e.clientY - r.top - r.height / 2) * 0.3;
        el.style.transition = "transform .18s cubic-bezier(0.23, 1, 0.32, 1)";
        el.style.transform = "translate(" + x + "px," + y + "px)";
      });
      el.addEventListener("pointerleave", () => {
        el.style.transition = "transform .6s cubic-bezier(0.23, 1, 0.32, 1)";
        el.style.transform = "";
      });
    });
    document.addEventListener("pointermove", e => {
      const spot = e.target.closest?.(".spot");
      if (!spot) return;
      const r = spot.getBoundingClientRect();
      spot.style.setProperty("--mx", (e.clientX - r.left) + "px");
      spot.style.setProperty("--my", (e.clientY - r.top) + "px");
    }, { passive: true });
  }

  /* ---------- Number tweening ---------- */
  const tweens = new WeakMap();
  function tweenNumber(el, to, pad = 0) {
    const from = tweens.get(el)?.value ?? to;
    const state = { value: from };
    tweens.set(el, state);
    if (reduce || from === to) { el.textContent = String(to).padStart(pad, "0"); state.value = to; return; }
    el.classList.remove("tick"); void el.offsetWidth; el.classList.add("tick");
    const start = performance.now(), dur = 650;
    const frame = now => {
      if (tweens.get(el) !== state) return;
      const t = Math.min(1, (now - start) / dur);
      state.value = Math.round(from + (to - from) * easeOut(t));
      el.textContent = String(state.value).padStart(pad, "0");
      if (t < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  /* ---------- Chart: glide the newest point into place ---------- */
  const chartLine = $("#chart-line"), chartArea = $("#chart-area"), chartPoint = $("#chart-point");
  let prevPoints = [];
  function animateChart() {
    const pts = (chartLine.getAttribute("points") || "").trim().split(/\s+/).map(p => p.split(",").map(Number));
    const grew = pts.length === prevPoints.length + 1 && pts.length > 1;
    const before = prevPoints;
    prevPoints = pts;
    if (!grew || reduce) return;
    const target = pts[pts.length - 1], origin = before[before.length - 1];
    const start = performance.now(), dur = 520;
    const draw = now => {
      if (prevPoints !== pts) return;
      const t = easeOut(Math.min(1, (now - start) / dur));
      const cur = [origin[0] + (target[0] - origin[0]) * t, origin[1] + (target[1] - origin[1]) * t];
      const all = pts.slice(0, -1).concat([cur]);
      chartLine.setAttribute("points", all.map(p => p.join(",")).join(" "));
      chartArea.setAttribute("d", "M" + all[0][0] + " 174 L" + all.map(p => p.join(" ")).join(" L") + " L" + cur[0] + " 174 Z");
      chartPoint.setAttribute("cx", cur[0]); chartPoint.setAttribute("cy", cur[1]);
      if (t < 1) requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  }

  /* ---------- Frame reactions ---------- */
  const gaugeArc = $("#gauge-arc"), gaugeThreshold = $("#gauge-threshold");
  const C = 2 * Math.PI * 84;
  const flash = $(".flash");
  const graphPanel = $(".graph-panel");
  const pills = { A: $(".pill-a"), B: $(".pill-b") };
  let prevOwners = {};
  let prevState = "calm";
  let mood = "calm";

  document.addEventListener("lab:frame", ({ detail }) => {
    const { frame, state, threshold } = detail;
    tweenNumber($("#metric-score"), frame.score, 2);
    tweenNumber($("#metric-blocked"), Object.keys(frame.waits).length);
    tweenNumber($("#metric-wait"), frame.waitMs);
    gaugeArc.style.strokeDashoffset = String(C * (1 - frame.score / 100));
    gaugeThreshold.style.strokeDashoffset = String(-C * threshold / 100);

    for (const lock of ["A", "B"]) {
      const owner = frame.owners[lock];
      pills[lock].classList.toggle("is-held", Boolean(owner));
      if (owner !== prevOwners[lock] && !reduce) {
        pills[lock].classList.remove("bump"); void pills[lock].offsetWidth; pills[lock].classList.add("bump");
      }
    }
    prevOwners = { ...frame.owners };

    document.body.dataset.state = state;
    mood = state;
    if (state !== prevState && (state === "danger" || state === "safe")) {
      flash.classList.remove("is-on"); void flash.offsetWidth; flash.classList.add("is-on");
      if (state === "danger" && !reduce) {
        graphPanel.classList.remove("is-shaking"); void graphPanel.offsetWidth; graphPanel.classList.add("is-shaking");
      }
    }
    prevState = state;
    animateChart();
  });

  /* ---------- Sparks travelling along visible wait edges ---------- */
  const edges = [[$("#edge-t1-t2"), $(".edge-spark.s1")], [$("#edge-t2-t1"), $(".edge-spark.s2")]];
  if (!reduce) {
    const lens = edges.map(([path]) => path.getTotalLength());
    const loop = now => {
      edges.forEach(([path, spark], i) => {
        const on = path.classList.contains("is-visible");
        spark.style.opacity = on ? "1" : "0";
        if (!on) return;
        const t = ((now / (mood === "danger" ? 700 : 1300)) + i * 0.5) % 1;
        const p = path.getPointAtLength(lens[i] * t);
        spark.setAttribute("cx", p.x); spark.setAttribute("cy", p.y);
      });
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  /* ---------- Particle field: drift → converge → vortex (deadlock) / lanes (safe) ---------- */
  const canvas = $("#field");
  const ctx = canvas.getContext("2d");
  const COLORS = { calm: [110, 231, 255], warning: [255, 181, 71], danger: [255, 77, 109], safe: [74, 222, 128] };
  let W = 0, H = 0, dpr = 1, particles = [], color = [...COLORS.calm], running = true;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.round(Math.min(260, (W * H) / 6500));
    particles = Array.from({ length: count }, (_, i) => ({
      x: Math.random() * W, y: Math.random() * H, vx: 0, vy: 0,
      lane: i % 2, seed: Math.random() * 1000, r: Math.random() * 1.4 + 0.4
    }));
  }
  resize();
  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => { running = !document.hidden; if (running) requestAnimationFrame(tick); });

  function steer(p, t) {
    const cx = W * (W > 860 ? 0.74 : 0.5), cy = H * 0.42;
    const dx = p.x - cx, dy = p.y - cy;
    const dist = Math.hypot(dx, dy) || 1;
    let tx, ty;
    if (mood === "danger") {
      // Circular wait: everything is pulled into one rotating ring.
      const R = Math.min(W, H) * 0.24 + Math.sin(p.seed) * 26;
      const pull = (R - dist) * 0.02;
      tx = (-dy / dist) * 3.4 + (dx / dist) * pull;
      ty = (dx / dist) * 3.4 + (dy / dist) * pull;
    } else if (mood === "safe") {
      // Shared order: two calm, parallel lanes.
      const laneY = H * (p.lane ? 0.62 : 0.38) + Math.sin(p.seed) * 22;
      tx = 1.6 + (p.seed % 1); ty = (laneY - p.y) * 0.02;
    } else if (mood === "warning") {
      // Contention: two hubs compete for the same particles.
      const hx = cx + (p.lane ? 140 : -140);
      tx = (hx - p.x) * 0.004 + Math.cos(t * 0.0012 + p.seed) * 1.2;
      ty = (cy - p.y) * 0.004 + Math.sin(t * 0.0012 + p.seed) * 1.2;
    } else {
      const a = Math.sin(p.x * 0.004 + t * 0.0002 + p.seed) + Math.cos(p.y * 0.005 - t * 0.00015);
      tx = Math.cos(a) * 0.6 + 0.25; ty = Math.sin(a) * 0.6;
    }
    p.vx += (tx - p.vx) * 0.05;
    p.vy += (ty - p.vy) * 0.05;
  }

  function tick(t) {
    if (!running) return;
    const target = COLORS[mood];
    for (let i = 0; i < 3; i++) color[i] += (target[i] - color[i]) * 0.04;
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = "rgba(0,0,0,0.16)";
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter";
    const rgb = color.map(Math.round).join(",");
    for (const p of particles) {
      steer(p, t);
      const ox = p.x, oy = p.y;
      p.x += p.vx; p.y += p.vy;
      if (p.x > W + 20) p.x = -20; else if (p.x < -20) p.x = W + 20;
      if (p.y > H + 20) p.y = -20; else if (p.y < -20) p.y = H + 20;
      if (Math.abs(p.x - ox) > 40 || Math.abs(p.y - oy) > 40) continue;
      ctx.strokeStyle = "rgba(" + rgb + "," + (0.25 + p.r * 0.25) + ")";
      ctx.lineWidth = p.r;
      ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(p.x, p.y); ctx.stroke();
    }
    if (!reduce) requestAnimationFrame(tick);
  }
  if (reduce) { for (let i = 0; i < 40; i++) tick(i * 16); } else requestAnimationFrame(tick);
})();
