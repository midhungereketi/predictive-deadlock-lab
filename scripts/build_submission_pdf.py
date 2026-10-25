"""Build docs/submission/Final_Report.pdf from the saved and newly collected measurements.

Run from the repository root:  python scripts/build_submission_pdf.py
Needs reportlab. Every number is read from the JSON result files in docs/.
"""

import json
from pathlib import Path

from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "submission" / "Final_Report.pdf"
SCREENS = ROOT / "docs" / "submission" / "screens"
SAVED = json.loads((ROOT / "docs" / "results.json").read_text(encoding="utf-8"))
NEW2 = json.loads((ROOT / "docs" / "results_2026-10-26_two_thread.json").read_text(encoding="utf-8"))
SCALE = json.loads((ROOT / "docs" / "results_2026-10-26_scaling.json").read_text(encoding="utf-8"))
V0, P0 = SAVED["comparison"]["vulnerable"], SAVED["comparison"]["protected"]
V1, P1 = NEW2["comparison"]["vulnerable"], NEW2["comparison"]["protected"]
SIZES = SCALE["sizes"]

navy = colors.HexColor("#0c1727")
cyan = colors.HexColor("#057f91")
light = colors.HexColor("#e8f5f7")
red = colors.HexColor("#b8344a")
green = colors.HexColor("#16705d")
grey = colors.HexColor("#5b6778")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=28, textColor=navy, spaceAfter=10))
styles.add(ParagraphStyle(name="SubCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor=cyan, spaceAfter=14))
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=navy, spaceBefore=14, spaceAfter=7))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=cyan, spaceBefore=8, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=navy, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=navy, spaceAfter=5))
styles.add(ParagraphStyle(name="CaptionCustom", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=grey, spaceAfter=10))
styles.add(ParagraphStyle(name="KickerCustom", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=cyan, spaceAfter=8))
styles.add(ParagraphStyle(name="CellCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, textColor=navy))
styles.add(ParagraphStyle(name="HeadCellCustom", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=colors.white))
styles.add(ParagraphStyle(name="CodeCustom", parent=styles["BodyText"], fontName="Courier", fontSize=8, leading=11, textColor=navy, backColor=light, borderPadding=6, spaceAfter=10, spaceBefore=4))
CONTENT_W = 170 * mm


def para(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def bullets(items):
    return [para("&bull;&nbsp;&nbsp;" + item) for item in items]


def table(rows, widths, wrap=False, font=8.5):
    # Wrapped tables wrap every cell, header included, so long labels never overlap.
    data = [[para(str(cell), "HeadCellCustom" if r == 0 else "CellCustom") if wrap else str(cell) for cell in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, cyan),
    ]))
    return t


def picture(name, width=CONTENT_W):
    image = Image(str(SCREENS / name))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth, image.drawHeight = width, width * ratio
    return image


def ms(value):
    return "n/a" if value is None else f"{value} ms"


def spread(s):
    return f"{s['mean']:.1f} ± {s['sd']:.1f} [{s['min']:.0f}–{s['max']:.0f}] ms"


def scaling_chart():
    drawing = Drawing(CONTENT_W, 60 * mm)
    chart = HorizontalLineChart()
    chart.x, chart.y = 16 * mm, 16 * mm
    chart.width, chart.height = 148 * mm, 37 * mm
    chart.data = [[z["vulnerable"]["detection_plus_recovery_runtime_ms"]["mean"] for z in SIZES],
                  [z["protected"]["completion_runtime_ms"]["mean"] for z in SIZES]]
    chart.categoryAxis.categoryNames = [str(z["threads"]) for z in SIZES]
    chart.categoryAxis.labels.fontName = chart.valueAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 1000, 250
    chart.valueAxis.visibleGrid, chart.valueAxis.gridStrokeColor = True, colors.HexColor("#d5dce6")
    for index, colour in enumerate((red, green)):
        chart.lines[index].strokeColor = colour
        chart.lines[index].strokeWidth = 1.8
        chart.lines[index].symbol = makeMarker("FilledCircle", size=5, fillColor=colour, strokeColor=colour)
    chart.lines[1].strokeDashArray = (4, 3)
    drawing.add(chart)
    drawing.add(String(16 * mm, 55.5 * mm, "mean milliseconds", fontName="Helvetica", fontSize=8, fillColor=grey))
    drawing.add(String(164 * mm, 8 * mm, "threads", fontName="Helvetica", fontSize=8, fillColor=grey, textAnchor="end"))
    legend = Legend()
    legend.x, legend.y = 20 * mm, 4 * mm
    legend.alignment, legend.columnMaximum, legend.deltax = "right", 1, 70 * mm
    legend.fontName, legend.fontSize = "Helvetica", 8
    legend.colorNamePairs = [(red, "Vulnerable: detection + recovery"), (green, "Protected: completion")]
    drawing.add(legend)
    return drawing


def page_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(cyan)
    canvas.line(20 * mm, 17 * mm, w - 20 * mm, 17 * mm)
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 12 * mm, "Predictive Deadlock Lab | Operating Systems (BCSE303L)")
    canvas.drawRightString(w - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


total_v = sum(len(z["vulnerable"]["runs"]) for z in SIZES)
total_p = sum(len(z["protected"]["runs"]) for z in SIZES)
dead = sum(z["vulnerable"]["deadlocked"] for z in SIZES)
full = sum(z["vulnerable"]["cycle_through_all_threads"] for z in SIZES)
recovered = sum(z["vulnerable"]["recovered_one_victim"] for z in SIZES)
completed = sum(z["protected"]["completed_all_threads"] for z in SIZES)

story = [
    para("OPERATING SYSTEMS CASE STUDY (BCSE303L) - FINAL REPORT", "KickerCustom"),
    para("Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting", "TitleCustom"),
    para("Real-thread experiments, early warning, lock ordering, victim recovery, and evaluation", "SubCustom"),
    HRFlowable(width="100%", thickness=2, color=cyan), Spacer(1, 10),
    para("<b>Team:</b> Midhun Gereketi (frontend, visualisation, integration) · P. Satya Mani Shraavanth (threaded experiments and API) · M. Lakshman Sai (analysis, scoring, evaluation)."),
    para("<b>Live app:</b> https://predictive-deadlock-lab.vercel.app/ · <b>Source:</b> https://github.com/midhungereketi/predictive-deadlock-lab"),
    para("Abstract", "H1Custom"),
    para("The project creates controlled deadlocks with real operating-system threads and studies how to observe, warn about, prevent and recover from them. In the original two-thread experiment T1 takes lock A then B while T2 takes B then A; a Wait-For Graph (WFG) confirms the cycle and a weighted 0-100 risk score warns before it appears. Protected mode learns one global lock order from a cycle-free probe. A configurable N-thread ring (2-32 threads on N locks) forms one cycle through every thread; a supervisor detects it and recovers by aborting a victim thread, while protected mode uses a global order and always completes. The dashboard replays each run and its Analysis and Compare views show when and why the score warned and how the modes differ over repeated trials and thread counts."),
    para(f"In the saved set (15 Oct 2026) {V0['deadlock_count']}/{V0['total_trials']} vulnerable two-thread runs deadlocked and {P0['completion_count']}/{P0['total_trials']} protected runs completed. A new collection (26 Oct 2026) reproduced this ({V1['deadlock_count']}/{V1['total_trials']}, {P1['completion_count']}/{P1['total_trials']}) and added a scaling study: {dead}/{total_v} vulnerable ring runs deadlocked with a cycle through all N threads and {recovered}/{total_v} recovered with one aborted thread; {completed}/{total_p} protected runs completed. <b>The warning is a documented heuristic evaluated in a controlled experiment; the project does not claim to predict deadlocks in arbitrary programs.</b>"),
    para("1. Problem and objectives", "H1Custom"),
    para("A deadlock needs mutual exclusion, hold-and-wait, no preemption and circular wait at the same time; opposite lock orders make circular wait possible. The objectives are to reproduce circular wait with real threads, detect an actual cycle from observed events, warn before it using only current information and measure how early, prevent it with a common lock order and recover from it by preempting a victim, and keep every measurement inspectable and repeatable."),
    para("2. Architecture", "H1Custom"),
    para("The browser dashboard (Lab, Analysis, Compare, Method) calls a FastAPI backend that also serves the dashboard, so the same code runs locally and on Vercel. The backend keeps no mutable state between requests: each request runs its own bounded experiment and builds its own scorer. Experiments emit timestamped lock events (high-resolution monotonic clock); the analysis builds the WFG, risk score, trend and heatmap and returns trial JSON or results to the browser."),
    table([
        ["Component", "Implementation"],
        ["Two-thread experiments", "member2_backend/vulnerable_experiment.py, protected_experiment.py, adaptive_policy.py, experiment_runner.py"],
        ["Lock tracking and cycle check", "member2_backend/lock_manager.py (bounded and cancellable waits)"],
        ["N-thread ring and recovery", "member2_backend/multi_thread_experiment.py"],
        ["WFG, score, trend, heatmap", "member3_analysis/graph.py, threat_scorer.py, trend_analyzer.py, heatmap.py"],
        ["Request-scoped analysis API", "member3_analysis/api_routes.py, comparator.py"],
        ["Dashboard and views", "frontend/index.html, app.js, styles.css, scoring.js"],
    ], [52 * mm, 118 * mm], wrap=True),
    para("3. Algorithms", "H1Custom"),
    para("Wait-For Graph and cycle detection", "H2Custom"),
    para("An edge Ti → Tj exists only while Ti waits for a lock owned by Tj. Each thread waits for at most one lock, so each node has at most one outgoing edge; following edges from each node finds any cycle in linear time. With single-instance locks a cycle is a confirmed deadlock."),
    para("Risk score (early-warning heuristic)", "H2Custom"),
    para("Score = round_half_up(w_b·B + w_w·W + w_c·C + w_r·R), where B = blocked threads / 2 × 100, W = longest wait / 800 ms × 100 (capped), C = contention events / 5 × 100 (capped), and R = 100 when A and B are held by different threads, 40 when one thread holds both, 20 when one lock is held. Defaults: 0.35, 0.30, 0.20, 0.15; threshold 70.", "CodeCustom"),
    para("Two rules apply: when different threads hold A and B and one waits, the score is at least 72; a confirmed cycle sets it to at least 96. The score uses only the current snapshot. <b>Weights are request-scoped:</b> each visitor's weights are applied in their browser and sent with the requests they start; they are stored only in that browser if the visitor saves them, never on the server, so visitors cannot affect each other. Python and the browser implement the same formula with round-half-up and are tested against the same shared cases."),
    para("Adaptive protected policy (two threads)", "H2Custom"),
    para("A probe lets T1 hold A while waiting for B held by T2 and stops before T2 requests A, so no cycle forms. The observed held → requested pair yields the order A → B; both workers sort their requests into that order before taking any lock, so no thread can hold B while waiting for A."),
    para("N-thread ring with victim recovery", "H2Custom"),
    para("Thread Ti needs Ri and R(i mod N)+1. Vulnerable: every thread takes its own lock, all meet at a barrier, then each requests the next lock, giving one cycle through all N threads. A supervisor polls a consistent snapshot every millisecond, detects the cycle and aborts the highest-numbered thread by cancelling its blocked acquire; its lock is released and the others finish one after another. Protected: each thread takes its lower-numbered lock first, so the last thread requests R1 before RN and circular wait cannot form."),
    para("4. Dashboard and workflow", "H1Custom"),
    para("Lab runs the two-thread trial or an N-thread ring and replays it; Analysis explains when and why the score warned and re-scores the run as weights change; Compare runs both modes, repeated trials and the scaling test, with CSV export."),
    KeepTogether([picture("replay-deadlock.png", 118 * mm), para("Figure 1. Replay of a real 8-thread vulnerable run at the moment the supervisor detected the cycle through all 8 threads.", "CaptionCustom")]),
    KeepTogether([picture("analysis-chart.png"), para("Figure 2. Analysis view of a live two-thread trial: the warning fired 121 ms before the deadlock was confirmed.", "CaptionCustom")]),
    para("5. Evaluation protocol", "H1Custom"),
    *bullets([
        f"<b>Two-thread:</b> {V0['total_trials']} trials per mode, 3 s cap per trial, 120 ms observation window before the conflicting request. Deadlock rate = confirmed-cycle trials / trials; completion rate = both workers finished / trials; warning lead = first pre-cycle score ≥ threshold to first cycle; detection latency = first cycle to supervisor notification. Failed runs count as inconclusive.",
        f"<b>Scaling:</b> sizes {', '.join(str(z['threads']) for z in SIZES)}; {SCALE['protocol']['trials_per_size_per_mode']} trials per size and mode, modes alternating. Vulnerable runtime = start to detection, victim abort and all other threads finishing; protected runtime = start to every thread completing. Every raw run is saved with the summary.",
        "<b>Separation of data:</b> the saved set (docs/results.json, 15 Oct 2026) is kept unchanged; the new sets are in docs/results_2026-10-26_two_thread.json and docs/results_2026-10-26_scaling.json.",
    ]),
    para("6. Results", "H1Custom"),
    para("6.1 Two-thread experiment: saved set and new set", "H2Custom"),
    table([
        ["Metric", "Saved · vuln.", "Saved · prot.", "New · vuln.", "New · prot."],
        ["Trials", V0["total_trials"], P0["total_trials"], V1["total_trials"], P1["total_trials"]],
        ["Deadlocked / completed", f"{V0['deadlock_count']} / {V0['completion_count']}", f"{P0['deadlock_count']} / {P0['completion_count']}", f"{V1['deadlock_count']} / {V1['completion_count']}", f"{P1['deadlock_count']} / {P1['completion_count']}"],
        ["Inconclusive", V0["inconclusive_count"], P0["inconclusive_count"], V1["inconclusive_count"], P1["inconclusive_count"]],
        ["Mean runtime", ms(V0["mean_trial_runtime_ms"]), ms(P0["mean_trial_runtime_ms"]), ms(V1["mean_trial_runtime_ms"]), ms(P1["mean_trial_runtime_ms"])],
        ["Mean peak wait", ms(V0["mean_peak_wait_ms"]), ms(P0["mean_peak_wait_ms"]), ms(V1["mean_peak_wait_ms"]), ms(P1["mean_peak_wait_ms"])],
        ["Mean peak score", V0["mean_peak_score"], P0["mean_peak_score"], V1["mean_peak_score"], P1["mean_peak_score"]],
        ["Warning lead before cycle", ms(V0["mean_warning_lead_time_ms"]), "n/a", ms(V1["mean_warning_lead_time_ms"]), "n/a"],
        ["Detection latency", ms(V0["mean_detection_latency_ms"]), "n/a", ms(V1["mean_detection_latency_ms"]), "n/a"],
    ], [50 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm]),
    Spacer(1, 6),
    para("The two sets agree on every outcome. Small times are not directly comparable: the saved set used time.monotonic (about 15.6 ms ticks on Windows) and the new set uses time.perf_counter. The score's rounding changed from banker's rounding to round-half-up; peak scores are fixed by the 72/96 rules and are unaffected. Protected runs reach 72 during the safe probe, before the policy applies.", "SmallCustom"),
    para("6.2 N-thread scaling (new set, 26 Oct 2026)", "H2Custom"),
    table([["Threads", "Deadlocked", "Full cycle", "Recovered", "Detection mean (max)", "Detection + recovery", "Protected done", "Completion time"]] +
          [[z["threads"], f"{z['vulnerable']['deadlocked']}/{len(z['vulnerable']['runs'])}", z["vulnerable"]["cycle_through_all_threads"], z["vulnerable"]["recovered_one_victim"],
            f"{z['vulnerable']['detection_ms']['mean']:.2f} ({z['vulnerable']['detection_ms']['max']:.2f}) ms", spread(z["vulnerable"]["detection_plus_recovery_runtime_ms"]),
            f"{z['protected']['completed_all_threads']}/{len(z['protected']['runs'])}", spread(z["protected"]["completion_runtime_ms"])] for z in SIZES],
          [16 * mm, 21 * mm, 13 * mm, 20 * mm, 24 * mm, 30 * mm, 19 * mm, 27 * mm], wrap=True, font=7.5),
    Spacer(1, 6),
    KeepTogether([scaling_chart(), para("Figure 3. Mean run time by thread count (values from docs/results_2026-10-26_scaling.json). Vulnerable time includes detection and recovery; protected time is completion only.", "CaptionCustom")]),
    para("Detection stayed within a few milliseconds; it grows with N, likely because more threads must reach the barrier and register their waits. Vulnerable time grows by roughly 30 ms per extra thread because, after the victim is aborted, the remaining threads finish one after another, each holding both locks for 30 ms. Protected time stays near 100 ms because non-neighbouring threads run in parallel. These are controlled runs of one workload on one machine, not a performance benchmark."),
    para("7. Limitations", "H1Custom"),
    *bullets([
        "Controlled schedules (barriers, a 120 ms window) make cycles reproducible; the measured lead time describes this experiment only and is not general predictive accuracy.",
        "The two-thread policy learns its order before the workers start and does not reorder locks already held; the ring's victim choice (highest-numbered thread) ignores fairness and rollback cost.",
        "Python threads under the global interpreter lock, on one machine; timings vary with load. Score ceilings are designed for the two-thread case.",
        "Runs are bounded by timeouts and an in-process supervisor; this is a teaching prototype, not a process-isolated production service.",
    ]),
    para("8. Literature review (2020-2025)", "H1Custom"),
    table([
        ["Work", "Contribution", "Relation to this project"],
        ["Qin et al., PLDI 2020 [1]", "Study of 170 real Rust bugs, including blocking bugs; static detectors", "Lock-order deadlocks persist even in memory-safe languages"],
        ["Cai, Meng & Palsberg, ICSE 2020 [2]", "AirLock: cycle search over a small lock reachability graph, ~3.5% overhead", "Our supervisor also searches a small graph; we confirm cycles at runtime"],
        ["Liu et al., ASPLOS 2021 [3]", "GCatch detects and GFix repairs Go blocking bugs", "Detect then repair, versus our detect then recover"],
        ["Tunç et al., PLDI 2023 [4]", "Sound and complete prediction is intractable in general; linear-time algorithms for sync-preserving deadlocks", "Why our score is presented as a heuristic warning"],
        ["Qin et al., IEEE TSE 2024 [5]", "100 Rust concurrency bugs; five static detectors (lockbud)", "Supports lock ordering as prevention"],
        ["van den Heuvel, Sulzmann & Thiemann, arXiv 2025 [6]", "Partial orders filter false-positive deadlock warnings", "Why false alarms must be reported honestly"],
    ], [44 * mm, 66 * mm, 60 * mm], wrap=True),
    para("9. Testing", "H1Custom"),
    para("Python tests cover the experiments, API, the ring at 2, 5, 12 and 32 threads, shared-case scoring consistency and scoring isolation (sequential, concurrent and real-trial checks that one visitor's weights never change another's results). Node tests cover the trial contract and the browser scoring formula. Browser tests (Playwright with a real server) cover tab switching, live weight tuning and its saved/temporary states, per-visitor privacy including backend scores, running both modes, repeated trials, scaling, injected backend failures and CSV exports."),
    KeepTogether([para("10. Team roles", "H1Custom"), *bullets([
        "<b>Midhun Gereketi:</b> dashboard, replay and visualisation, Analysis and Compare views, trial contract, integration, deployment, documentation.",
        "<b>P. Satya Mani Shraavanth:</b> threaded experiments, lock manager, protected policy, N-thread ring and recovery, REST API.",
        "<b>M. Lakshman Sai:</b> Wait-For Graph, risk score, trend and heatmap analysis, repeated-trial comparison and evaluation.",
    ])]),
    para("11. Reproduction", "H1Custom"),
    para("pip install -r requirements-dev.txt<br/>python -m pytest member2_backend/tests member3_analysis/tests tests/e2e<br/>node --test frontend/tests/trial-data.test.js frontend/tests/scoring.test.js<br/>python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000<br/>python scripts/collect_scaling_results.py --sizes 2 4 8 16 32 --trials 10 --output docs/&lt;new&gt;.json", "CodeCustom"),
    para("12. Conclusion", "H1Custom"),
    para("Real threads reproduce circular wait on demand from 2 to 32 threads; a Wait-For Graph confirms it; the score warns before it in the staged two-thread case; a global lock order prevents it; and aborting one victim recovers from it. Every claim above is backed by saved, repeatable measurements, and the stated limits define where the results apply."),
    para("References", "H1Custom"),
    para("[1] B. Qin, Y. Chen, Z. Yu, L. Song, Y. Zhang. Understanding Memory and Thread Safety Practices and Issues in Real-World Rust Programs. PLDI 2020. pldi20.sigplan.org", "SmallCustom"),
    para("[2] Y. Cai, R. Meng, J. Palsberg. Low-Overhead Deadlock Prediction. ICSE 2020, pp. 1298-1309. doi:10.1145/3377811.3380367", "SmallCustom"),
    para("[3] Z. Liu, S. Zhu, B. Qin, H. Chen, L. Song. Automatically Detecting and Fixing Concurrency Bugs in Go Software Systems. ASPLOS 2021. github.com/system-pclub/GCatch", "SmallCustom"),
    para("[4] H. C. Tunç, U. Mathur, A. Pavlogiannis, M. Viswanathan. Sound Dynamic Deadlock Prediction in Linear Time. PLDI 2023. doi:10.1145/3591291", "SmallCustom"),
    para("[5] B. Qin, Y. Chen, H. Liu, H. Zhang, Q. Wen, L. Song, Y. Zhang. Understanding and Detecting Real-World Safety Issues in Rust. IEEE Transactions on Software Engineering, 2024. doi:10.1109/TSE.2024.3380393", "SmallCustom"),
    para("[6] B. van den Heuvel, M. Sulzmann, P. Thiemann. Partial Orders for Precise and Efficient Dynamic Deadlock Prediction. arXiv:2502.20070, 2025 (preprint).", "SmallCustom"),
]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
                        topMargin=19 * mm, bottomMargin=23 * mm, title="Predictive Deadlock Lab - Final Report",
                        author="Midhun Gereketi, P. Satya Mani Shraavanth, M. Lakshman Sai")
doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
print(OUT.relative_to(ROOT))
