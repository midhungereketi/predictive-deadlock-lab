"""Build docs/submission/Presentation_Submission.pptx from the saved and new measurements.

Run from the repository root:  python scripts/build_submission_slides.py
Needs python-pptx. Every number comes from the JSON result files in docs/.
"""

import json
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "submission" / "Presentation_Submission.pptx"
SCREENS = DOCS / "submission" / "screens"
SAVED = json.loads((DOCS / "results.json").read_text(encoding="utf-8"))
NEW2 = json.loads((DOCS / "results_2026-10-26_two_thread.json").read_text(encoding="utf-8"))
SCALE = json.loads((DOCS / "results_2026-10-26_scaling.json").read_text(encoding="utf-8"))
TESTS = {"python": 59, "node": 6, "browser": 8}

INK = RGBColor(0x0E, 0x14, 0x20)      # dark navy background
TEXT = RGBColor(0x1B, 0x24, 0x33)     # body text on light slides
MUTED = RGBColor(0x5B, 0x67, 0x78)
CARD = RGBColor(0xF1, 0xF4, 0xF8)
LINE = RGBColor(0xD5, 0xDC, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xB8, 0xC4, 0xD4)     # muted text on dark slides
RED = RGBColor(0xC8, 0x3A, 0x50)      # deadlock
TEAL = RGBColor(0x17, 0x8F, 0x6E)     # safe / protected
AMBER = RGBColor(0xC7, 0x84, 0x14)    # warning
BLUE = RGBColor(0x2F, 0x6F, 0xC4)
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
slide_no = 0


def text(slide, value, x, y, w, h, size=16, color=TEXT, bold=False, font=BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    lines = value if isinstance(value, list) else [value]
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        runs = line if isinstance(line, list) else [(line, {})] if isinstance(line, str) else [line]
        for run_text, opts in runs:
            run = paragraph.add_run()
            run.text = run_text
            run.font.name = opts.get("font", font)
            run.font.size = Pt(opts.get("size", size))
            run.font.bold = opts.get("bold", bold)
            run.font.italic = opts.get("italic", italic)
            run.font.color.rgb = opts.get("color", color)
        if index:
            paragraph.space_before = Pt(opts.get("gap", 6) if runs else 6)
    return box


def bullets(slide, items, x, y, w, h, size=16, color=TEXT, mark=TEAL, gap=10):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        if index:
            paragraph.space_before = Pt(gap)
        props = paragraph._p.get_or_add_pPr()
        props.set("marL", str(int(Inches(0.28))))
        props.set("indent", str(-int(Inches(0.28))))
        colour = props.makeelement(qn("a:buClr"), {})
        colour.append(colour.makeelement(qn("a:srgbClr"), {"val": str(mark)}))
        props.append(colour)
        props.append(props.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
        props.append(props.makeelement(qn("a:buChar"), {"char": "•"}))
        run = paragraph.add_run()
        run.text = item
        run.font.name, run.font.size, run.font.color.rgb = BODY, Pt(size), color
    return box


def card(slide, x, y, w, h, fill=CARD, line=None, radius=0.08):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
    shape.shadow.inherit = False
    return shape


def badge(slide, x, y, d, label, fill, color=WHITE, size=14):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    shape.shadow.inherit = False
    frame = shape.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER
    run = paragraph.add_run()
    run.text = label
    run.font.name, run.font.size, run.font.bold, run.font.color.rgb = BODY, Pt(size), True, color
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    return shape


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=2.0):
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    line = connector.line._get_or_add_ln()
    tail = line.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    line.append(tail)
    return connector


def new_slide(title=None, kicker=None, dark=False, notes=""):
    global slide_no
    slide_no += 1
    slide = prs.slides.add_slide(BLANK)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = INK if dark else WHITE
    if title:
        text(slide, kicker or "", 0.6, 0.38, 12.1, 0.3, 12, TEAL if not dark else SOFT, True)
        text(slide, title, 0.6, 0.68, 12.1, 0.8, 32, WHITE if dark else TEXT, True, HEAD)
    text(slide, "Predictive Deadlock Lab · Operating Systems case study", 0.6, 7.02, 8, 0.3, 10, SOFT if dark else MUTED)
    text(slide, str(slide_no), 12.23, 7.02, 0.5, 0.3, 10, SOFT if dark else MUTED, align=PP_ALIGN.RIGHT)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def table(slide, rows, x, y, w, col_widths, size=13, header_fill=INK, row_h=0.42, left=False):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = shape.table
    for index, width in enumerate(col_widths):
        tbl.columns[index].width = Inches(width)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (CARD if r % 2 == 0 else WHITE)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            frame = cell.text_frame
            frame.word_wrap = True
            paragraph = frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.LEFT if c == 0 or left else PP_ALIGN.CENTER
            run = paragraph.add_run()
            run.text = str(value)
            run.font.name, run.font.size = BODY, Pt(size)
            run.font.bold = r == 0 or c == 0
            run.font.color.rgb = WHITE if r == 0 else TEXT
    return shape


def ms(value, digits=1):
    return "n/a" if value is None else f"{value:.{digits}f} ms"


V0, P0 = SAVED["comparison"]["vulnerable"], SAVED["comparison"]["protected"]
V1, P1 = NEW2["comparison"]["vulnerable"], NEW2["comparison"]["protected"]
SIZES = SCALE["sizes"]
total_v = sum(len(s["vulnerable"]["runs"]) for s in SIZES)
total_dead = sum(s["vulnerable"]["deadlocked"] for s in SIZES)
total_full = sum(s["vulnerable"]["cycle_through_all_threads"] for s in SIZES)
total_rec = sum(s["vulnerable"]["recovered_one_victim"] for s in SIZES)
total_p = sum(len(s["protected"]["runs"]) for s in SIZES)
total_done = sum(s["protected"]["completed_all_threads"] for s in SIZES)
max_detect = max(s["vulnerable"]["detection_ms"]["max"] for s in SIZES)
first, last = SIZES[0], SIZES[-1]
per_thread = (last["vulnerable"]["detection_plus_recovery_runtime_ms"]["mean"] - first["vulnerable"]["detection_plus_recovery_runtime_ms"]["mean"]) / (last["threads"] - first["threads"])

# 1 · Title
s = new_slide(dark=True, notes="Introduce the team and the question: can we observe, warn about, prevent and recover from deadlocks with real threads? Stress that every result is measured, and the warning is a heuristic in a controlled experiment.")
text(s, "OPERATING SYSTEMS · BCSE303L · CASE STUDY", 0.8, 1.15, 7.4, 0.35, 14, SOFT, True)
text(s, "Predictive Deadlock Prevention", 0.8, 1.6, 7.4, 1.6, 44, WHITE, True, HEAD)
text(s, "Contention analysis, score forecasting, lock ordering and victim recovery with real operating-system threads", 0.8, 3.25, 6.9, 1.0, 19, SOFT)
text(s, [[("Midhun Gereketi", {"bold": True, "color": WHITE}), ("  ·  ", {}), ("P. Satya Mani Shraavanth", {"bold": True, "color": WHITE}), ("  ·  ", {}), ("M. Lakshman Sai", {"bold": True, "color": WHITE})]], 0.8, 4.75, 7.6, 0.4, 16, SOFT)
text(s, "Live: predictive-deadlock-lab.vercel.app", 0.8, 5.25, 7.4, 0.4, 15, RGBColor(0x7F, 0xD8, 0xC0))
import math
cx, cy, r = 10.35, 3.55, 1.75
pts = [(cx + r * math.cos(-math.pi / 2 + i * math.pi / 3), cy + r * math.sin(-math.pi / 2 + i * math.pi / 3)) for i in range(6)]
for i, (px, py) in enumerate(pts):
    nx, ny = pts[(i + 1) % 6]
    dx, dy = nx - px, ny - py
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    arrow(s, px + ux * 0.42, py + uy * 0.42, nx - ux * 0.45, ny - uy * 0.45, RED, 2.5)
for i, (px, py) in enumerate(pts):
    badge(s, px - 0.36, py - 0.36, 0.72, f"T{i + 1}", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 16)
text(s, "circular wait", cx - 1.0, cy - 0.2, 2.0, 0.4, 15, RGBColor(0xFF, 0x9A, 0xAA), True, align=PP_ALIGN.CENTER)

# 2 · Problem
s = new_slide("Deadlock needs four conditions at the same time", "THE PROBLEM", notes="All four Coffman conditions must hold. We make circular wait happen on purpose, then remove it with a global lock order, or break it at runtime by preempting one thread.")
conds = [("1", "Mutual exclusion", "A lock has one owner at a time"), ("2", "Hold and wait", "A thread keeps its lock while waiting for another"),
         ("3", "No preemption", "A held lock cannot be taken away"), ("4", "Circular wait", "Each thread waits for the next one in a cycle")]
for i, (n, head, body) in enumerate(conds):
    x, y = 0.6 + (i % 2) * 3.85, 1.75 + (i // 2) * 2.15
    hot = n == "4"
    card(s, x, y, 3.6, 1.9, RGBColor(0xFB, 0xEC, 0xEF) if hot else CARD)
    badge(s, x + 0.3, y + 0.3, 0.55, n, RED if hot else INK)
    text(s, head, x + 1.05, y + 0.36, 2.4, 0.45, 19, RED if hot else TEXT, True, HEAD)
    text(s, body, x + 0.3, y + 1.05, 3.1, 0.75, 15, TEXT)
card(s, 8.6, 1.75, 4.1, 4.05, INK)
text(s, "Opposite lock order", 8.9, 1.98, 3.6, 0.4, 18, WHITE, True, HEAD)
text(s, [[("T1:  ", {"color": SOFT}), ("A  →  B", {"bold": True, "color": WHITE})], [("T2:  ", {"color": SOFT}), ("B  →  A", {"bold": True, "color": WHITE})]], 8.9, 2.5, 3.6, 0.9, 20)
badge(s, 9.25, 3.75, 0.75, "T1", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 16)
badge(s, 11.35, 3.75, 0.75, "T2", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 16)
arrow(s, 10.05, 3.95, 11.3, 3.95, RED, 2.5)
arrow(s, 11.3, 4.35, 10.05, 4.35, RED, 2.5)
text(s, "waits for B", 10.05, 3.62, 1.25, 0.3, 11, SOFT, align=PP_ALIGN.CENTER)
text(s, "waits for A", 10.05, 4.42, 1.25, 0.3, 11, SOFT, align=PP_ALIGN.CENTER)
text(s, "Each holds the lock the other needs.", 8.9, 5.05, 3.6, 0.6, 15, SOFT)
text(s, "We break circular wait with one global lock order, or no preemption by aborting a victim thread.", 0.6, 6.25, 12.1, 0.5, 16, MUTED, italic=True)

# 3 · Architecture
s = new_slide("One stateless backend, real threads, one dashboard", "ARCHITECTURE", notes="The FastAPI app runs the experiments and serves the dashboard, so the same code runs locally and on Vercel. Nothing is stored between requests: each request runs its own bounded experiment and builds its own scorer.")
flow = [("Dashboard", "Lab · Analysis · Compare", BLUE), ("FastAPI", "Stateless, per-request scoring", INK), ("Experiments", "Two-thread · N-thread ring", RED),
        ("Event log", "perf_counter timestamps", AMBER), ("Analysis", "Wait-For Graph · score · heatmap", TEAL)]
for i, (head, body, colour) in enumerate(flow):
    x = 0.6 + i * 2.5
    card(s, x, 1.95, 2.1, 1.6, CARD, colour)
    text(s, head, x + 0.15, 2.15, 1.8, 0.45, 17, TEXT, True, HEAD, PP_ALIGN.CENTER)
    text(s, body, x + 0.15, 2.7, 1.8, 0.7, 13, MUTED, align=PP_ALIGN.CENTER)
    if i < 4:
        arrow(s, x + 2.12, 2.75, x + 2.48, 2.75, MUTED, 2)
arrow(s, 11.65, 3.62, 11.65, 4.1, MUTED, 2)
connector = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(11.65), Inches(4.1), Inches(1.65), Inches(4.1))
connector.line.color.rgb, connector.line.width = MUTED, Pt(2)
arrow(s, 1.65, 4.1, 1.65, 3.62, MUTED, 2)
text(s, "trial JSON, results and replay data back to the browser", 3.2, 4.18, 7.0, 0.35, 13, MUTED, align=PP_ALIGN.CENTER)
facts = [("Real OS threads", "Python threads and mutexes; every run reports distinct OS thread ids."), ("Bounded, cancellable waits", "Every lock wait has a timeout; the supervisor can cancel a victim's wait."),
         ("Same code everywhere", "uvicorn locally, app.py on Vercel; no server-side state between requests.")]
for i, (head, body) in enumerate(facts):
    x = 0.6 + i * 4.1
    card(s, x, 4.9, 3.85, 1.65)
    text(s, head, x + 0.3, 5.08, 3.3, 0.4, 17, TEXT, True, HEAD)
    text(s, body, x + 0.3, 5.55, 3.3, 0.9, 14, TEXT)

# 4 · Two-thread experiment
s = new_slide("Two threads, two locks: the cycle forms on cue", "ORIGINAL TWO-THREAD EXPERIMENT", notes=f"Walk through the staged schedule. The warning fires at step 3, before the cycle exists. Saved set: {V0['deadlock_count']}/{V0['total_trials']} deadlocked, mean warning lead {V0['mean_warning_lead_time_ms']} ms.")
steps = [("T1 takes A", "score low", MUTED), ("T2 takes B", "both locks held", MUTED), ("T1 requests B and must wait", "warning: score 72 (lock-order rule)", AMBER), ("T2 requests A: cycle T1 → T2 → T1", "deadlock confirmed: score 96", RED)]
for i, (head, body, colour) in enumerate(steps):
    y = 1.8 + i * 1.12
    badge(s, 0.6, y, 0.6, str(i + 1), colour if colour != MUTED else INK)
    text(s, head, 1.4, y - 0.02, 5.6, 0.4, 18, TEXT, True)
    text(s, body, 1.4, y + 0.42, 5.6, 0.35, 14, colour if colour != MUTED else MUTED)
card(s, 7.55, 1.75, 5.15, 3.95, INK)
text(s, "Wait-For Graph at step 4", 7.85, 1.98, 4.6, 0.4, 17, WHITE, True, HEAD)
badge(s, 8.25, 3.2, 0.95, "T1", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 18)
badge(s, 11.05, 3.2, 0.95, "T2", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 18)
arrow(s, 9.25, 3.45, 11.0, 3.45, RED, 2.75)
arrow(s, 11.0, 3.95, 9.25, 3.95, RED, 2.75)
text(s, "waits for B (held by T2)", 8.95, 3.02, 2.4, 0.35, 12, SOFT, align=PP_ALIGN.CENTER)
text(s, "waits for A (held by T1)", 8.95, 4.05, 2.4, 0.35, 12, SOFT, align=PP_ALIGN.CENTER)
text(s, "A cycle with single-instance locks is a confirmed deadlock.", 7.85, 4.85, 4.6, 0.65, 14, SOFT)
text(s, [[("Saved set: ", {"bold": True}), (f"{V0['deadlock_count']}/{V0['total_trials']} vulnerable runs deadlocked; the warning came {V0['mean_warning_lead_time_ms']} ms before the cycle on average.", {})]], 0.6, 6.2, 12.1, 0.45, 16, TEXT)

# 5 · Risk score
s = new_slide("The risk score is an early warning, not a proof", "SCORE FORECASTING", notes="Explain the four normalised factors and the two rules. The score only uses the current snapshot. Weights are tunable per visitor in the Analysis view and are never stored on the server.")
card(s, 0.6, 1.75, 6.6, 0.85, INK)
text(s, "Score = w_b·Blocked + w_w·Wait + w_c·Contention + w_r·Conflict", 0.85, 1.75, 6.2, 0.85, 17, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
factors = [("Blocked threads", 0.35, BLUE), ("Longest wait (full at 800 ms)", 0.30, RGBColor(0xC9, 0x5A, 0x20)), ("Contention events (full at 5)", 0.20, TEAL), ("Lock conflict (A and B held apart)", 0.15, AMBER)]
for i, (label, weight, colour) in enumerate(factors):
    y = 2.95 + i * 0.78
    text(s, label, 0.6, y, 4.3, 0.35, 15, TEXT)
    text(s, f"{weight:.2f}", 6.55, y, 0.65, 0.35, 15, TEXT, True, align=PP_ALIGN.RIGHT)
    track = card(s, 0.6, y + 0.4, 6.0, 0.16, LINE, radius=0.5)
    card(s, 0.6, y + 0.4, 6.0 * weight / 0.35, 0.16, colour, radius=0.5)
rules = [("≥ 72", "Different threads hold A and B and one waits (lock-order rule)", AMBER), ("≥ 96", "A cycle is confirmed in the Wait-For Graph", RED), ("70", "Default warning threshold; tunable", BLUE)]
for i, (big, body, colour) in enumerate(rules):
    y = 1.75 + i * 1.18
    card(s, 7.65, y, 5.05, 1.0)
    text(s, big, 7.9, y, 1.2, 1.0, 26, colour, True, HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, body, 9.15, y, 3.4, 1.0, 14, TEXT, anchor=MSO_ANCHOR.MIDDLE)
card(s, 7.65, 5.35, 5.05, 1.3, RGBColor(0xE8, 0xF5, 0xF0))
text(s, [[("Per visitor: ", {"bold": True, "color": TEAL}), ("weights live in your browser and travel with your own requests; the server stores nothing.", {})]], 7.9, 5.5, 4.6, 1.0, 14, TEXT)

# 6 · Prevention
s = new_slide("One global lock order removes circular wait", "PREVENTION", notes=f"Two-thread: the probe observes A before B and both workers adopt that order. Ring: lower-numbered lock first, so the last thread asks for R1 before RN. Results: two-thread protected {P0['completion_count']}/{P0['total_trials']} saved and {P1['completion_count']}/{P1['total_trials']} new; ring {total_done}/{total_p}.")
for i, (head, lines, stat) in enumerate([
        ("Two threads: learned order", ["A short probe lets T1 hold A while it waits for B, then stops before a cycle can form.", "The policy derives the order A → B from that observation.", "Both workers request A, then B, before taking any lock."], f"{P0['completion_count']}/{P0['total_trials']} saved · {P1['completion_count']}/{P1['total_trials']} new runs completed"),
        ("N-thread ring: ordered acquisition", ["Thread Ti needs locks Ri and Ri+1 (last thread wraps to R1).", "Every thread takes its lower-numbered lock first.", "The last thread asks for R1 before RN, so the circle cannot close."], f"{total_done}/{total_p} runs completed every thread")]):
    x = 0.6 + i * 6.25
    card(s, x, 1.75, 5.85, 4.55)
    badge(s, x + 0.35, 2.0, 0.6, "✓", TEAL, size=18)
    text(s, head, x + 1.15, 2.07, 4.5, 0.45, 20, TEXT, True, HEAD)
    bullets(s, lines, x + 0.4, 2.85, 5.1, 2.4, 16, TEXT, TEAL)
    card(s, x + 0.35, 5.35, 5.15, 0.7, WHITE, LINE)
    text(s, stat, x + 0.55, 5.35, 4.8, 0.7, 16, TEAL, True, anchor=MSO_ANCHOR.MIDDLE)
text(s, "If every thread acquires locks in the same order, no thread can hold a later lock while waiting for an earlier one.", 0.6, 6.45, 12.1, 0.4, 15, MUTED, italic=True)

# 7 · Ring and recovery
s = new_slide("N-thread ring: detect the cycle, abort a victim, unwind", "CONFIGURABLE 2–32 THREADS", notes=f"The screenshot is a real 8-thread run paused at detection. Across the scaling set, {total_full}/{total_v} vulnerable runs formed a cycle through all N threads, detection took at most {max_detect:.1f} ms, and {total_rec}/{total_v} recovered with exactly one aborted thread.")
s.shapes.add_picture(str(SCREENS / "replay-deadlock.png"), Inches(0.6), Inches(1.65), height=Inches(5.2))
steps = [("Every thread holds its lock and waits for the next", f"Cycle through all N threads in {total_full}/{total_v} runs", RED),
         ("Supervisor scans a consistent snapshot every 1 ms", f"Detected within {max_detect:.1f} ms (2–32 threads)", AMBER),
         ("Abort the highest-numbered thread; others finish in turn", f"{total_rec}/{total_v} runs: N−1 finished, 1 aborted", TEAL)]
for i, (head, body, colour) in enumerate(steps):
    y = 1.8 + i * 1.6
    badge(s, 7.0, y, 0.6, str(i + 1), colour)
    text(s, [[(head, {"bold": True})], [(body, {"color": colour, "size": 15})]], 7.8, y - 0.02, 4.9, 1.4, 17, TEXT)

# 8 · Dashboard
s = new_slide("Replay, Analysis and Compare make every run inspectable", "THE DASHBOARD", notes="Replay animates the real event log. Analysis shows when the warning fired and why, and re-scores live as weights change. Compare runs both modes, repeated trials and the scaling test, with CSV export.")
views = [("Replay", "Lock tiles move between threads; the deadlock flashes; recovery unwinds step by step.", RED),
         ("Analysis", "Peak score, first warning, lead time, per-event factor breakdown, live weight tuning.", BLUE),
         ("Compare", "Both modes side by side, repeated trials, 2–32 thread scaling, CSV export.", TEAL)]
for i, (head, body, colour) in enumerate(views):
    y = 1.8 + i * 1.6
    badge(s, 0.6, y, 0.6, head[0], colour, size=16)
    text(s, head, 1.4, y - 0.02, 3.4, 0.4, 19, TEXT, True, HEAD)
    text(s, body, 1.4, y + 0.45, 3.6, 1.0, 14, TEXT)
pic = s.shapes.add_picture(str(SCREENS / "analysis-chart.png"), Inches(5.35), Inches(1.75), width=Inches(7.35))
below = 1.75 + pic.height / 914400 + 0.15
findings = s.shapes.add_picture(str(SCREENS / "analysis-findings.png"), Inches(5.35), Inches(below), width=Inches(7.35))
text(s, "Live two-thread trial in the Analysis view: key findings and the risk chart (warning 121 ms before the deadlock).", 5.35, below + findings.height / 914400 + 0.12, 7.35, 0.4, 12, MUTED, italic=True)

# 9 · Evaluation protocol
s = new_slide("Evaluation protocol: repeated, bounded, fully recorded", "METHOD", notes="Every trial is a real run with a timeout. Failed runs are counted as inconclusive, never as successes. The saved and new sets are kept in separate, dated files with every raw run.")
for i, (head, lines) in enumerate([
        ("Two-thread experiment", [f"{V0['total_trials']} trials per mode, 3 s cap per trial", "120 ms observation window before the conflicting request", "Deadlock rate, completion rate, warning lead, detection latency", "Failed runs counted as inconclusive"]),
        ("N-thread scaling", [f"Sizes {', '.join(str(z['threads']) for z in SIZES)}; {SCALE['protocol']['trials_per_size_per_mode']} trials per size and mode", "Modes alternate so drift affects both equally", "Vulnerable time = detection + victim abort + others finishing", "Protected time = every thread completed"])]):
    x = 0.6 + i * 6.25
    card(s, x, 1.75, 5.85, 3.55)
    text(s, head, x + 0.35, 1.98, 5.2, 0.45, 20, TEXT, True, HEAD)
    bullets(s, lines, x + 0.35, 2.6, 5.2, 2.6, 16, TEXT, BLUE)
card(s, 0.6, 5.6, 12.1, 1.05, INK)
text(s, [[("Saved set ", {"bold": True, "color": WHITE}), ("collected 15 Oct 2026 (docs/results.json)   ·   ", {"color": SOFT}), ("New sets ", {"bold": True, "color": WHITE}), ("collected 26 Oct 2026 (two-thread re-run and scaling) in separate files", {"color": SOFT})]], 0.9, 5.6, 11.5, 1.05, 15, anchor=MSO_ANCHOR.MIDDLE)

# 10 · Two-thread results
s = new_slide("Two-thread results: saved and new sets agree", "RESULTS", notes="Read the outcome rows first: every vulnerable run deadlocked and every protected run completed in both sets. Small times differ partly because the saved set used a coarser clock.")
rows = [["Metric", "Saved · vulnerable", "Saved · protected", "New · vulnerable", "New · protected"],
        ["Trials", V0["total_trials"], P0["total_trials"], V1["total_trials"], P1["total_trials"]],
        ["Deadlocked / completed", f"{V0['deadlock_count']} / {V0['completion_count']}", f"{P0['deadlock_count']} / {P0['completion_count']}", f"{V1['deadlock_count']} / {V1['completion_count']}", f"{P1['deadlock_count']} / {P1['completion_count']}"],
        ["Inconclusive", V0["inconclusive_count"], P0["inconclusive_count"], V1["inconclusive_count"], P1["inconclusive_count"]],
        ["Mean runtime", ms(V0["mean_trial_runtime_ms"]), ms(P0["mean_trial_runtime_ms"]), ms(V1["mean_trial_runtime_ms"]), ms(P1["mean_trial_runtime_ms"])],
        ["Mean peak wait", ms(V0["mean_peak_wait_ms"]), ms(P0["mean_peak_wait_ms"]), ms(V1["mean_peak_wait_ms"]), ms(P1["mean_peak_wait_ms"])],
        ["Mean peak score", V0["mean_peak_score"], P0["mean_peak_score"], V1["mean_peak_score"], P1["mean_peak_score"]],
        ["Warning lead before cycle", ms(V0["mean_warning_lead_time_ms"]), "n/a", ms(V1["mean_warning_lead_time_ms"]), "n/a"],
        ["Detection latency", ms(V0["mean_detection_latency_ms"]), "n/a", ms(V1["mean_detection_latency_ms"]), "n/a"]]
table(s, rows, 0.6, 1.7, 12.1, [3.3, 2.2, 2.2, 2.2, 2.2], 14, row_h=0.47)
text(s, "Saved set used time.monotonic (≈15.6 ms ticks on Windows); the new set uses time.perf_counter. Protected runs reach 72 during the safe probe, before the policy applies.", 0.6, 6.2, 12.1, 0.6, 13, MUTED, italic=True)

# 11 · Scaling
s = new_slide("Scaling: every cycle spans all N threads", "RESULTS · NEW SET", notes=f"Line chart of mean times from the 26 Oct scaling set. Vulnerable time grows by about {per_thread:.0f} ms per extra thread because threads finish one after another after recovery; protected time stays near 100 ms. These are controlled runs, not a benchmark.")
chart_data = CategoryChartData()
chart_data.categories = [str(z["threads"]) for z in SIZES]
chart_data.add_series("Vulnerable: detection + recovery (mean ms)", [z["vulnerable"]["detection_plus_recovery_runtime_ms"]["mean"] for z in SIZES])
chart_data.add_series("Protected: completion (mean ms)", [z["protected"]["completion_runtime_ms"]["mean"] for z in SIZES])
frame = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.6), Inches(1.65), Inches(7.4), Inches(4.65), chart_data)
chart = frame.chart
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False
chart.legend.font.size, chart.legend.font.name = Pt(12), BODY
chart.font.name, chart.font.size = BODY, Pt(12)
for series, colour in zip(chart.series, (RED, TEAL)):
    series.format.line.color.rgb = colour
    series.format.line.width = Pt(2.25)
    series.smooth = False
    series.marker.style = XL_MARKER_STYLE.CIRCLE
    series.marker.size = 8
    series.marker.format.fill.solid()
    series.marker.format.fill.fore_color.rgb = colour
    series.marker.format.line.color.rgb = colour
value_axis = chart.value_axis
value_axis.has_major_gridlines = True
value_axis.major_gridlines.format.line.color.rgb = LINE
value_axis.tick_labels.font.size, value_axis.tick_labels.font.color.rgb = Pt(12), MUTED
value_axis.format.line.fill.background()
value_axis.has_title = True
value_axis.axis_title.text_frame.text = "milliseconds"
value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
category_axis = chart.category_axis
category_axis.tick_labels.font.size, category_axis.tick_labels.font.color.rgb = Pt(12), MUTED
category_axis.has_title = True
category_axis.axis_title.text_frame.text = "threads"
category_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
stats = [(f"{total_dead}/{total_v}", "vulnerable runs deadlocked; all with a cycle through every thread", RED),
         (f"{total_rec}/{total_v}", "recovered with exactly one aborted thread", AMBER),
         (f"{total_done}/{total_p}", "protected runs completed every thread", TEAL),
         (f"≈{per_thread:.0f} ms", "extra vulnerable time per added thread (sequential unwinding)", BLUE)]
for i, (big, body, colour) in enumerate(stats):
    y = 1.7 + i * 1.17
    card(s, 8.4, y, 4.3, 1.0)
    text(s, big, 8.6, y, 1.6, 1.0, 22, colour, True, HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, body, 10.25, y, 2.35, 1.0, 13, TEXT, anchor=MSO_ANCHOR.MIDDLE)
text(s, f"Run-to-run spread is small (vulnerable sd ≤ {max(z['vulnerable']['detection_plus_recovery_runtime_ms']['sd'] for z in SIZES):.1f} ms). Controlled ring workload on one machine; not a performance benchmark.", 0.6, 6.42, 12.1, 0.4, 13, MUTED, italic=True)

# 12 · Literature
s = new_slide("Related work, 2020–2025", "LITERATURE REVIEW", notes="All six works are verifiable; DOIs or official pages are in the report. The key point from Tunç et al.: sound and complete deadlock prediction is intractable in general, which is why our score is presented as a heuristic.")
rows = [["Work", "Idea", "Relevance here"],
        ["Qin et al., PLDI 2020", "Study of real Rust bugs, incl. blocking bugs; static detectors", "Lock-order deadlocks persist in safe languages"],
        ["Cai, Meng & Palsberg, ICSE 2020", "AirLock: cycle search in a small lock graph, ~3.5 % overhead", "Cheap cycle search, like our supervisor"],
        ["Liu et al., ASPLOS 2021", "GCatch detects, GFix repairs Go blocking bugs", "Detect then repair vs. our detect then recover"],
        ["Tunç et al., PLDI 2023", "Sound linear-time prediction of sync-preserving deadlocks", "General prediction is intractable: our score is a heuristic"],
        ["Qin et al., IEEE TSE 2024", "100 Rust concurrency bugs; five static detectors (lockbud)", "Supports lock ordering as prevention"],
        ["van den Heuvel et al., arXiv 2025", "Partial orders filter false deadlock warnings", "Why we report false alarms honestly"]]
table(s, rows, 0.6, 1.7, 12.1, [3.4, 4.5, 4.2], 14, row_h=0.62, left=True)
text(s, "Full references with DOIs or official links are in docs/FINAL_REPORT.md and the PDF report.", 0.6, 6.3, 12.1, 0.4, 13, MUTED, italic=True)

# 13 · Limitations and conclusion
s = new_slide("Limitations and conclusion", "WRAP-UP", dark=True, notes="Be explicit about what the results do not show. Close with the three demonstrated results.")
for i, (head, lines, colour) in enumerate([
        ("Limitations", ["Controlled schedules (barriers, 120 ms window): lead time is not general prediction accuracy", "Score ceilings are tuned for two threads", "Simple victim choice: highest-numbered thread", "Python threads under the GIL on one machine; timings vary", "Teaching prototype, not a process-isolated service"], AMBER),
        ("Conclusion", ["Real threads reproduce circular wait on demand, from 2 to 32 threads", "A Wait-For Graph confirms it; the score warns before it in the staged case", "A global lock order prevents it; aborting one victim recovers from it", "Every claim is backed by saved, repeatable measurements"], RGBColor(0x5F, 0xD4, 0xB0))]):
    x = 0.6 + i * 6.25
    card(s, x, 1.75, 5.85, 4.75, RGBColor(0x17, 0x20, 0x31))
    text(s, head, x + 0.4, 1.98, 5.0, 0.45, 22, colour, True, HEAD)
    bullets(s, lines, x + 0.4, 2.7, 5.1, 3.8, 17, WHITE, colour, 12)

# 14 · Team and testing
s = new_slide("Team roles and testing", "PROJECT", dark=True, notes="Each member presents their part in the demo. All automated tests pass; numbers are from the final run before submission.")
team = [("Midhun Gereketi", "Dashboard, replay, Analysis and Compare views, integration, deployment, documentation"),
        ("P. Satya Mani Shraavanth", "Threaded experiments, lock manager, protected policy, N-thread ring and recovery, REST API"),
        ("M. Lakshman Sai", "Wait-For Graph, risk score, trend and heatmap analysis, repeated-trial evaluation")]
for i, (name, role) in enumerate(team):
    x = 0.6 + i * 4.1
    card(s, x, 1.75, 3.85, 2.45, RGBColor(0x17, 0x20, 0x31))
    badge(s, x + 0.35, 2.0, 0.65, name.split()[0][0] if not name.startswith("P.") else "S", BLUE, size=18)
    text(s, name, x + 0.35, 2.82, 3.2, 0.45, 18, WHITE, True, HEAD)
    text(s, role, x + 0.35, 3.3, 3.2, 0.85, 13, SOFT)
for i, (big, label) in enumerate([(str(TESTS["python"]), "Python tests: experiments, API, ring, scoring consistency and isolation"), (str(TESTS["node"]), "Node tests: trial contract and browser scoring"), (str(TESTS["browser"]), "Browser tests with a real server: tabs, tuning, privacy, both modes, scaling, errors, CSV")]):
    x = 0.6 + i * 4.1
    text(s, big, x, 4.6, 1.3, 0.9, 40, RGBColor(0x5F, 0xD4, 0xB0), True, HEAD)
    text(s, label, x + 1.35, 4.62, 2.5, 1.5, 13, SOFT)
text(s, "github.com/midhungereketi/predictive-deadlock-lab", 0.6, 6.35, 12.1, 0.4, 15, WHITE, True)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print("Saved", OUT.relative_to(ROOT), "with", slide_no, "slides")
