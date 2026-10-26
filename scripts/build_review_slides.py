"""Build docs/submission/Project_Review_Presentation.pptx (review format).

Sections: abstract, introduction, literature review (30 papers, 2020-2026),
problem statement, research gaps, existing system, objectives, proposed system,
system architecture, modules, results with project screenshots, and APA
references. Run from the repository root:
    python scripts/build_review_slides.py
Needs python-pptx. Measurements come from the JSON files in docs/; papers come
from scripts/literature.py.
"""

import json
import math
import sys
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from literature import PAPERS  # noqa: E402

DOCS = ROOT / "docs"
OUT = DOCS / "submission" / "Project_Review_Presentation.pptx"
SCREENS = DOCS / "submission" / "screens"
SAVED = json.loads((DOCS / "results.json").read_text(encoding="utf-8"))["comparison"]
NEW2 = json.loads((DOCS / "results_2026-10-26_two_thread.json").read_text(encoding="utf-8"))["comparison"]
SIZES = json.loads((DOCS / "results_2026-10-26_scaling.json").read_text(encoding="utf-8"))["sizes"]

INK = RGBColor(0x0E, 0x14, 0x20)
TEXT = RGBColor(0x1B, 0x24, 0x33)
MUTED = RGBColor(0x5B, 0x67, 0x78)
CARD = RGBColor(0xF1, 0xF4, 0xF8)
LINE = RGBColor(0xD5, 0xDC, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xB8, 0xC4, 0xD4)
PANEL = RGBColor(0x17, 0x20, 0x31)
RED = RGBColor(0xC8, 0x3A, 0x50)
TEAL = RGBColor(0x17, 0x8F, 0x6E)
AMBER = RGBColor(0xC7, 0x84, 0x14)
BLUE = RGBColor(0x2F, 0x6F, 0xC4)
MINT = RGBColor(0x5F, 0xD4, 0xB0)
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
        if index:
            paragraph.space_before = Pt(6)
        for run_text, opts in (line if isinstance(line, list) else [(line, {})]):
            run = paragraph.add_run()
            run.text = run_text
            run.font.name = opts.get("font", font)
            run.font.size = Pt(opts.get("size", size))
            run.font.bold = opts.get("bold", bold)
            run.font.italic = opts.get("italic", italic)
            run.font.color.rgb = opts.get("color", color)
    return box


def bullets(slide, items, x, y, w, h, size=16, color=TEXT, mark=TEAL, gap=9):
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
        segments = item if isinstance(item, list) else [(item, False)]
        for segment, bold in segments:
            run = paragraph.add_run()
            run.text = segment
            run.font.name, run.font.size, run.font.color.rgb, run.font.bold = BODY, Pt(size), color, bold
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
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER
    run = paragraph.add_run()
    run.text = label
    run.font.name, run.font.size, run.font.bold, run.font.color.rgb = BODY, Pt(size), True, color
    return shape


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=2.0):
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    line = connector.line._get_or_add_ln()
    line.append(line.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return connector


def picture(slide, name, x, y, w=None, h=None):
    kwargs = {}
    if w is not None:
        kwargs["width"] = Inches(w)
    if h is not None:
        kwargs["height"] = Inches(h)
    return slide.shapes.add_picture(str(SCREENS / name), Inches(x), Inches(y), **kwargs)


def new_slide(title=None, kicker=None, dark=False, notes=""):
    global slide_no
    slide_no += 1
    slide = prs.slides.add_slide(BLANK)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = INK if dark else WHITE
    if title:
        text(slide, kicker or "", 0.6, 0.36, 12.1, 0.3, 12, SOFT if dark else TEAL, True)
        text(slide, title, 0.6, 0.66, 12.1, 0.8, 32, WHITE if dark else TEXT, True, HEAD)
    text(slide, "Predictive Deadlock Prevention · Operating Systems (BCSE303L)", 0.6, 7.02, 8, 0.3, 10, SOFT if dark else MUTED)
    text(slide, str(slide_no), 12.23, 7.02, 0.5, 0.3, 10, SOFT if dark else MUTED, align=PP_ALIGN.RIGHT)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def table(slide, rows, x, y, col_widths, size=12, row_h=0.42, header_h=None, left=False):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(sum(col_widths)), Inches(row_h * len(rows)))
    tbl = shape.table
    for index, width in enumerate(col_widths):
        tbl.columns[index].width = Inches(width)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(header_h if (r == 0 and header_h) else row_h)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = INK if r == 0 else (CARD if r % 2 == 0 else WHITE)
            cell.margin_left = cell.margin_right = Inches(0.07)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            frame = cell.text_frame
            frame.word_wrap = True
            paragraph = frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.LEFT if (c == 0 or left) else PP_ALIGN.CENTER
            run = paragraph.add_run()
            run.text = str(value)
            run.font.name, run.font.size = BODY, Pt(size)
            run.font.bold = r == 0
            run.font.color.rgb = WHITE if r == 0 else TEXT
    return shape


def ms(value):
    return "n/a" if value is None else f"{value} ms"


V0, P0, V1, P1 = SAVED["vulnerable"], SAVED["protected"], NEW2["vulnerable"], NEW2["protected"]
total_v = sum(len(z["vulnerable"]["runs"]) for z in SIZES)
total_p = sum(len(z["protected"]["runs"]) for z in SIZES)
dead = sum(z["vulnerable"]["deadlocked"] for z in SIZES)
full = sum(z["vulnerable"]["cycle_through_all_threads"] for z in SIZES)
recovered = sum(z["vulnerable"]["recovered_one_victim"] for z in SIZES)
completed = sum(z["protected"]["completed_all_threads"] for z in SIZES)
max_detect = max(z["vulnerable"]["detection_ms"]["max"] for z in SIZES)

# 1 · Title
s = new_slide(dark=True, notes="Introduce the project and the team.")
text(s, "OPERATING SYSTEMS · BCSE303L · PROJECT REVIEW", 0.8, 1.2, 7.6, 0.35, 14, SOFT, True)
text(s, "Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting", 0.8, 1.65, 7.6, 2.5, 34, WHITE, True, HEAD)
text(s, "Real operating-system threads · Wait-For Graph detection · early-warning score · lock ordering · victim recovery", 0.8, 4.3, 7.0, 0.9, 17, SOFT)
text(s, [[("Midhun Gereketi", {"bold": True, "color": WHITE}), ("  ·  ", {}), ("P. Satya Mani Shraavanth", {"bold": True, "color": WHITE}), ("  ·  ", {}), ("M. Lakshman Sai", {"bold": True, "color": WHITE})]], 0.8, 5.4, 7.8, 0.4, 16, SOFT)
text(s, "Live: predictive-deadlock-lab.vercel.app", 0.8, 5.9, 7.4, 0.4, 15, MINT)
cx, cy, r = 10.35, 3.55, 1.75
pts = [(cx + r * math.cos(-math.pi / 2 + i * math.pi / 3), cy + r * math.sin(-math.pi / 2 + i * math.pi / 3)) for i in range(6)]
for i, (px, py) in enumerate(pts):
    nx, ny = pts[(i + 1) % 6]
    length = math.hypot(nx - px, ny - py)
    ux, uy = (nx - px) / length, (ny - py) / length
    arrow(s, px + ux * 0.42, py + uy * 0.42, nx - ux * 0.45, ny - uy * 0.45, RED, 2.5)
for i, (px, py) in enumerate(pts):
    badge(s, px - 0.36, py - 0.36, 0.72, f"T{i + 1}", RGBColor(0x3A, 0x14, 0x20), RGBColor(0xFF, 0xB3, 0xC0), 16)
text(s, "circular wait", cx - 1.0, cy - 0.2, 2.0, 0.4, 15, RGBColor(0xFF, 0x9A, 0xAA), True, align=PP_ALIGN.CENTER)

# 2 · Abstract
s = new_slide("Abstract", "01 · ABSTRACT", notes="Summarise the whole project in one minute.")
text(s, [
    "Deadlocks freeze concurrent programs when threads wait for each other in a circle. This project builds controlled deadlocks with real operating-system threads and studies how to detect, warn about, prevent and recover from them.",
    "A two-thread experiment (T1: A→B, T2: B→A) forms a cycle that a Wait-For Graph confirms, while a transparent 0–100 risk score raises an early warning before the cycle closes. Protected mode learns one global lock order and always completes. A configurable ring of 2–32 threads forms a cycle through every thread; a supervisor detects it and recovers by aborting one victim thread.",
    "A web dashboard replays every run and explains, compares and exports the results. The warning is a documented heuristic evaluated in a controlled experiment, not a predictor for arbitrary programs.",
], 0.6, 1.7, 7.6, 4.9, 16, TEXT)
for i, (big, label, colour) in enumerate([(f"{V0['deadlock_count'] + V1['deadlock_count']}/{V0['total_trials'] + V1['total_trials']}", "two-thread vulnerable runs deadlocked (saved + new sets)", RED),
                                          (f"{V1['mean_warning_lead_time_ms']} ms", "mean warning before the deadlock (new set)", AMBER),
                                          (f"{completed}/{total_p}", "protected ring runs (2–32 threads) completed", TEAL)]):
    y = 1.75 + i * 1.6
    card(s, 8.6, y, 4.1, 1.4)
    text(s, big, 8.85, y + 0.1, 3.6, 0.7, 30, colour, True, HEAD)
    text(s, label, 8.85, y + 0.8, 3.6, 0.55, 14, TEXT)

# 3 · Introduction
s = new_slide("Introduction: why deadlocks still matter", "02 · INTRODUCTION", notes="Explain deadlock and the four Coffman conditions; motivate with real-world studies.")
conds = [("1", "Mutual exclusion", "A lock has one owner at a time"), ("2", "Hold and wait", "Threads keep locks while waiting"),
         ("3", "No preemption", "Held locks cannot be taken away"), ("4", "Circular wait", "Each thread waits for the next")]
for i, (n, head, body) in enumerate(conds):
    x, y = 0.6 + (i % 2) * 3.3, 1.75 + (i // 2) * 1.75
    hot = n == "4"
    card(s, x, y, 3.1, 1.55, RGBColor(0xFB, 0xEC, 0xEF) if hot else CARD)
    badge(s, x + 0.25, y + 0.25, 0.5, n, RED if hot else INK)
    text(s, head, x + 0.9, y + 0.3, 2.1, 0.4, 17, RED if hot else TEXT, True, HEAD)
    text(s, body, x + 0.25, y + 0.9, 2.7, 0.55, 14, TEXT)
text(s, "All four Coffman conditions must hold at once for a deadlock.", 0.6, 5.35, 6.4, 0.4, 14, MUTED, italic=True)
bullets(s, [
    "Multithreading is everywhere: OS kernels, databases, servers and mobile apps.",
    "Studies of real systems keep finding deadlocks: Linux kernel (54 found by DLOS), Go and Rust projects, distributed databases.",
    "Detection after the fact freezes the program; prevention by lock ordering needs discipline; prediction in general is intractable (Tunç et al., 2023).",
    "This project makes the whole lifecycle visible and measurable: form, warn, detect, prevent, recover.",
], 7.4, 1.8, 5.3, 4.6, 16, TEXT, BLUE)

# 4-9 · Literature review
for page in range(6):
    chunk = PAPERS[page * 5:(page + 1) * 5]
    first, last = chunk[0]["cite"].split("(")[-1][:4], chunk[-1]["cite"].split("(")[-1][:4]
    years = first if first == last else f"{first}–{last}"
    s = new_slide(f"Literature review ({page + 1}/6) · {years}", "03 · LITERATURE REVIEW", notes="Papers are verified against publisher, conference, arXiv or DBLP records. The drawback column is our assessment of each paper's scope and limits.")
    rows = [["#", "Authors (year)", "Title · venue", "Method / contribution", "Drawback (our assessment)"]]
    for offset, paper in enumerate(chunk):
        rows.append([str(page * 5 + offset + 1), paper["cite"], f"{paper['title']} · {paper['venue']}", paper["method"], paper["drawback"]])
    table(s, rows, 0.6, 1.6, [0.4, 2.15, 3.55, 3.15, 2.85], 11, row_h=0.92, header_h=0.42, left=True)

# 10 · Problem statement
s = new_slide("Problem statement", "04 · PROBLEM STATEMENT", notes="State the problem precisely and what is in scope.")
card(s, 0.6, 1.75, 12.1, 1.45, INK)
text(s, "How can we reproduce deadlocks with real OS threads, confirm them reliably, warn before they form, prevent them, and recover when they happen, while measuring every step honestly?", 0.95, 1.75, 11.4, 1.45, 20, WHITE, True, HEAD, anchor=MSO_ANCHOR.MIDDLE)
for i, (head, body, colour) in enumerate([
        ("Invisible until too late", "A deadlocked program simply stops; the cycle is hidden inside lock state.", RED),
        ("Detection ≠ warning", "A Wait-For Graph cycle proves deadlock only after it forms; earlier signals are heuristics.", AMBER),
        ("Fixes have trade-offs", "Ordering needs global discipline; recovery must pick a victim and release its locks.", BLUE),
        ("Claims need evidence", "Results must come from repeated, bounded runs, not one demonstration.", TEAL)]):
    x = 0.6 + i * 3.08
    card(s, x, 3.55, 2.85, 2.85)
    badge(s, x + 0.25, 3.8, 0.5, str(i + 1), colour)
    text(s, head, x + 0.25, 4.45, 2.4, 0.75, 17, TEXT, True, HEAD)
    text(s, body, x + 0.25, 5.2, 2.4, 1.15, 14, TEXT)

# 11 · Research gaps
s = new_slide("Research gaps identified from the literature", "05 · RESEARCH GAPS", notes="Each gap is tied to the reviewed papers.")
gaps = [("Language- or domain-specific tools", "Most detectors target one language or system (Go: GCatch, GFuzz, Goat, GoPV; Rust: Qin et al.; kernels: DLOS, Archerfish; databases: LCL).", "[1, 6, 10, 13, 14, 17, 20, 26]"),
        ("Static vs. dynamic trade-off", "Static tools report false positives (DLOS 17%); dynamic and trace-based tools see only executed paths (AirLock, GOLEAK, SPD).", "[13, 2, 18, 16]"),
        ("Detection without prevention or recovery", "Most work stops at reporting a bug; few combine warning, prevention and runtime recovery in one system.", "[2, 15, 16, 20]"),
        ("Prediction is hard in general", "Sound and complete prediction is intractable; heuristic warnings are rarely transparent or measured.", "[16, 25, 29]"),
        ("Little support for understanding", "Tools output reports, not an explanation of how a deadlock forms, which matters for teaching and debugging.", "[23, 24, 28]")]
for i, (head, body, refs) in enumerate(gaps):
    y = 1.7 + i * 1.02
    badge(s, 0.6, y + 0.12, 0.55, f"G{i + 1}", AMBER, size=13)
    text(s, head, 1.4, y, 3.6, 0.85, 17, TEXT, True, HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, body, 5.1, y, 5.6, 0.85, 14, TEXT, anchor=MSO_ANCHOR.MIDDLE)
    text(s, refs, 10.8, y, 1.9, 0.85, 12, MUTED, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)
text(s, "Numbers refer to the literature table (slides 4–9).", 0.6, 6.6, 12.1, 0.3, 11, MUTED, italic=True)

# 12 · Existing system
s = new_slide("Existing system", "06 · EXISTING SYSTEM", notes="Classical OS approaches and current tools, and their limits.")
rows = [["Approach", "How it works", "Limitation"],
        ["Ignore (ostrich)", "Most general-purpose OSs assume deadlocks are rare", "System hangs; manual restart needed"],
        ["Periodic detection", "Build a Wait-For Graph and look for cycles", "Acts only after the deadlock has happened"],
        ["Avoidance (Banker's)", "Grant a request only if the state stays safe", "Needs maximum demands in advance; costly"],
        ["Prevention by ordering", "All threads take locks in one global order", "Relies on programmer discipline"],
        ["Static / dynamic tools", "GCatch, DLOS, AirLock, SPD and others report likely deadlocks", "Language-specific; false positives or missed paths; no live recovery"]]
table(s, rows, 0.6, 1.7, [2.8, 4.9, 4.4], 14, row_h=0.62, left=True)
card(s, 0.6, 5.6, 12.1, 0.95, RGBColor(0xFB, 0xEC, 0xEF))
text(s, "No single existing setup lets students reproduce, warn about, prevent and recover from deadlocks on real threads while measuring each step.", 0.9, 5.6, 11.5, 0.95, 16, RED, True, anchor=MSO_ANCHOR.MIDDLE)

# 13 · Objectives
s = new_slide("Objectives", "07 · OBJECTIVES", notes="Each objective maps to a module and a measurement.")
objectives = [("Reproduce", "Create deadlocks on demand with real OS threads, from 2 to 32 threads.", RED),
              ("Detect", "Confirm deadlock exactly from a Wait-For Graph cycle.", BLUE),
              ("Warn", "Raise a transparent, tunable early-warning score before the cycle forms, and measure the lead time.", AMBER),
              ("Prevent", "Remove circular wait with a learned or global lock order.", TEAL),
              ("Recover", "Break a detected cycle by aborting one victim thread so the rest finish.", RED),
              ("Explain and evaluate", "Replay, analyse and compare runs; repeated, bounded trials with saved results.", BLUE)]
for i, (head, body, colour) in enumerate(objectives):
    x, y = 0.6 + (i % 2) * 6.15, 1.7 + (i // 2) * 1.6
    card(s, x, y, 5.95, 1.4)
    badge(s, x + 0.3, y + 0.42, 0.56, str(i + 1), colour)
    text(s, head, x + 1.1, y + 0.15, 4.6, 0.45, 18, TEXT, True, HEAD)
    text(s, body, x + 1.1, y + 0.6, 4.6, 0.75, 14, TEXT)

# 14 · Proposed system
s = new_slide("Proposed system", "08 · PROPOSED SYSTEM", notes="Two experiments, one scoring engine, prevention and recovery, one dashboard.")
for i, (head, lines, colour) in enumerate([
        ("Two-thread experiment", ["T1: A→B, T2: B→A on real threads", "Wait-For Graph confirms the cycle", "Risk score warns before it", "Protected: probe learns A→B order"], RED),
        ("N-thread ring (2–32)", ["Thread Ti needs locks Ri and Ri+1", "Vulnerable: one cycle through all N", "Supervisor detects it in ms and aborts a victim", "Protected: lower-numbered lock first"], AMBER),
        ("Dashboard", ["Replay of every real run", "Analysis: why and when it warned", "Compare: both modes, repeated trials, 2–32 scaling", "Per-visitor weights; CSV export"], TEAL)]):
    x = 0.6 + i * 4.1
    card(s, x, 1.7, 3.85, 3.65)
    badge(s, x + 0.3, 1.95, 0.55, str(i + 1), colour)
    text(s, head, x + 1.0, 2.0, 2.75, 0.5, 18, TEXT, True, HEAD)
    bullets(s, lines, x + 0.3, 2.8, 3.3, 2.5, 15, TEXT, colour)
card(s, 0.6, 5.6, 12.1, 0.95, INK)
text(s, [[("Key rule: ", {"bold": True, "color": MINT}), ("only a Wait-For Graph cycle confirms a deadlock. The risk score is an early-warning heuristic for this controlled experiment, not a general predictor.", {})]],
     0.95, 5.6, 11.4, 0.95, 16, WHITE, anchor=MSO_ANCHOR.MIDDLE)

# 15 · Architecture
s = new_slide("System architecture", "09 · SYSTEM ARCHITECTURE", notes="Stateless FastAPI backend; each request runs its own bounded experiment and builds its own scorer.")
flow = [("Dashboard", "Lab · Analysis · Compare", BLUE), ("FastAPI", "Stateless, per-request scoring", INK), ("Experiments", "Two-thread · N-thread ring", RED),
        ("Event log", "High-resolution timestamps", AMBER), ("Analysis", "Wait-For Graph · score · heatmap", TEAL)]
for i, (head, body, colour) in enumerate(flow):
    x = 0.6 + i * 2.5
    card(s, x, 1.95, 2.1, 1.6, CARD, colour)
    text(s, head, x + 0.15, 2.15, 1.8, 0.45, 17, TEXT, True, HEAD, PP_ALIGN.CENTER)
    text(s, body, x + 0.15, 2.7, 1.8, 0.7, 13, MUTED, align=PP_ALIGN.CENTER)
    if i < 4:
        arrow(s, x + 2.12, 2.75, x + 2.48, 2.75, MUTED, 2)
arrow(s, 11.65, 3.62, 11.65, 4.1, MUTED, 2)
back = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(11.65), Inches(4.1), Inches(1.65), Inches(4.1))
back.line.color.rgb, back.line.width = MUTED, Pt(2)
arrow(s, 1.65, 4.1, 1.65, 3.62, MUTED, 2)
text(s, "trial JSON, results and replay data back to the browser", 3.2, 4.18, 7.0, 0.35, 13, MUTED, align=PP_ALIGN.CENTER)
for i, (head, body) in enumerate([("Supervisor", "Polls a consistent lock snapshot every 1 ms and cancels a victim's wait."),
                                  ("Bounded runs", "Every lock wait and request has a timeout; nothing can hang."),
                                  ("Deployment", "Same code locally (uvicorn) and on Vercel; no server-side state.")]):
    x = 0.6 + i * 4.1
    card(s, x, 4.9, 3.85, 1.6)
    text(s, head, x + 0.3, 5.08, 3.3, 0.4, 17, TEXT, True, HEAD)
    text(s, body, x + 0.3, 5.55, 3.3, 0.9, 14, TEXT)

# 16 · Modules
s = new_slide("Modules", "10 · MODULES", notes="Six modules and who built them.")
mods = [("Experiment engine", "Vulnerable/protected two-thread trials; adaptive lock-order policy", "member2_backend · Shraavanth", RED),
        ("Lock manager", "Ownership, bounded and cancellable waits, consistent snapshots, cycle check", "member2_backend · Shraavanth", RED),
        ("N-thread ring & recovery", "2–32 threads on N locks; supervisor detection and victim abort", "member2_backend · Shraavanth", AMBER),
        ("Analysis & scoring", "Wait-For Graph, risk score, trend, heatmap, repeated-trial comparison", "member3_analysis · Lakshman", BLUE),
        ("API", "FastAPI endpoints with per-request scoring weights", "member2/member3 · Shraavanth, Lakshman", BLUE),
        ("Dashboard", "Replay, Analysis and Compare views, scaling test, CSV export", "frontend · Midhun", TEAL)]
for i, (head, body, owner, colour) in enumerate(mods):
    x, y = 0.6 + (i % 3) * 4.1, 1.7 + (i // 3) * 2.45
    card(s, x, y, 3.85, 2.2)
    badge(s, x + 0.3, y + 0.28, 0.55, str(i + 1), colour)
    text(s, head, x + 1.0, y + 0.32, 2.75, 0.5, 17, TEXT, True, HEAD)
    text(s, body, x + 0.3, y + 0.98, 3.3, 0.8, 14, TEXT)
    text(s, owner, x + 0.3, y + 1.75, 3.3, 0.35, 12, MUTED, italic=True)

# 17 · Results: two-thread deadlock
s = new_slide("Results · two-thread deadlock and early warning", "11 · RESULTS", notes="Real backend trial: the score crossed 70 before the cycle formed.")
picture(s, "lab-wait-for-graph.png", 0.6, 1.65, w=6.6)
picture(s, "lab-risk-chart.png", 7.5, 1.65, h=4.15)
text(s, "Wait-For Graph of a live vulnerable trial: T1 waits for B (held by T2), T2 waits for A (held by T1): the cycle confirms deadlock.", 0.6, 5.65, 6.6, 0.7, 13, MUTED, italic=True)
text(s, "Risk score of the same run crosses the warning threshold (70) before the deadlock.", 7.5, 5.9, 5.2, 0.6, 13, MUTED, italic=True)

# 18 · Results: compare modes
s = new_slide("Results · vulnerable vs. protected", "11 · RESULTS", notes="One live run of each mode, then repeated trials.")
picture(s, "compare-modes.png", 0.6, 1.6, h=5.15)
rows = [["Metric", "Saved V", "Saved P", "New V", "New P"],
        ["Trials", V0["total_trials"], P0["total_trials"], V1["total_trials"], P1["total_trials"]],
        ["Deadlocked", V0["deadlock_count"], P0["deadlock_count"], V1["deadlock_count"], P1["deadlock_count"]],
        ["Completed", V0["completion_count"], P0["completion_count"], V1["completion_count"], P1["completion_count"]],
        ["Warning lead", ms(V0["mean_warning_lead_time_ms"]), "n/a", ms(V1["mean_warning_lead_time_ms"]), "n/a"],
        ["Mean runtime", ms(V0["mean_trial_runtime_ms"]), ms(P0["mean_trial_runtime_ms"]), ms(V1["mean_trial_runtime_ms"]), ms(P1["mean_trial_runtime_ms"])]]
table(s, rows, 7.45, 1.7, [1.45, 0.95, 0.95, 0.95, 0.95], 12, row_h=0.5)
text(s, "Saved set: 15 Oct 2026 · new set: 26 Oct 2026 (10 trials per mode each). V = vulnerable, P = protected.", 7.45, 4.85, 5.25, 0.7, 12, MUTED, italic=True)
text(s, "Left: live dashboard comparison of one run per mode.", 7.45, 5.6, 5.25, 0.5, 12, MUTED, italic=True)

# 19 · Results: ring
s = new_slide("Results · N-thread ring: deadlock and recovery vs. ordering", "11 · RESULTS", notes="Left: 8 threads in one cycle at detection. Right: 12 protected threads queue but never form a cycle.")
picture(s, "replay-deadlock.png", 0.6, 1.6, h=4.65)
picture(s, "replay-protected.png", 6.75, 1.6, h=4.65)
text(s, f"Vulnerable, 8 threads: one cycle through all 8, detected within milliseconds; T8 is aborted. Across the scaling set: {full}/{total_v} full cycles, {recovered}/{total_v} recoveries.", 0.6, 6.32, 5.9, 0.6, 12, MUTED, italic=True)
text(s, f"Protected, 12 threads: threads queue behind neighbours, no cycle; {completed}/{total_p} protected runs completed.", 6.75, 6.32, 5.95, 0.6, 12, MUTED, italic=True)

# 20 · Results: scaling
s = new_slide("Results · scaling from 2 to 32 threads (new set)", "11 · RESULTS", notes="10 trials per size and mode. Vulnerable time includes detection and recovery; protected time is completion.")
chart_data = CategoryChartData()
chart_data.categories = [str(z["threads"]) for z in SIZES]
chart_data.add_series("Vulnerable: detection + recovery (mean ms)", [z["vulnerable"]["detection_plus_recovery_runtime_ms"]["mean"] for z in SIZES])
chart_data.add_series("Protected: completion (mean ms)", [z["protected"]["completion_runtime_ms"]["mean"] for z in SIZES])
chart = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.6), Inches(1.6), Inches(6.3), Inches(4.9), chart_data).chart
chart.has_legend = True
chart.legend.position, chart.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
chart.legend.font.size, chart.font.name, chart.font.size = Pt(12), BODY, Pt(12)
for series, colour in zip(chart.series, (RED, TEAL)):
    series.format.line.color.rgb, series.format.line.width, series.smooth = colour, Pt(2.25), False
    series.marker.style, series.marker.size = XL_MARKER_STYLE.CIRCLE, 8
    series.marker.format.fill.solid()
    series.marker.format.fill.fore_color.rgb = colour
    series.marker.format.line.color.rgb = colour
chart.value_axis.major_gridlines.format.line.color.rgb = LINE
chart.value_axis.tick_labels.font.size = chart.category_axis.tick_labels.font.size = Pt(12)
for axis, label in ((chart.category_axis, "threads"), (chart.value_axis, "milliseconds")):
    axis.has_title = True
    axis.axis_title.text_frame.text = label
    font = axis.axis_title.text_frame.paragraphs[0].runs[0].font
    font.size, font.bold, font.name, font.color.rgb = Pt(12), False, BODY, MUTED
rows = [["Threads", "Deadlocked", "Detect (mean)", "Vuln. time", "Protected done", "Prot. time"]]
for z in SIZES:
    v, p = z["vulnerable"], z["protected"]
    rows.append([z["threads"], f"{v['deadlocked']}/{len(v['runs'])}", f"{v['detection_ms']['mean']:.1f} ms", f"{v['detection_plus_recovery_runtime_ms']['mean']:.0f} ± {v['detection_plus_recovery_runtime_ms']['sd']:.0f} ms",
                 f"{p['completed_all_threads']}/{len(p['runs'])}", f"{p['completion_runtime_ms']['mean']:.0f} ± {p['completion_runtime_ms']['sd']:.0f} ms"])
table(s, rows, 7.15, 1.7, [0.7, 1.05, 0.85, 1.1, 0.95, 0.9], 11, row_h=0.5)
text(s, f"Every vulnerable run formed a cycle through all N threads; detection ≤ {max_detect:.1f} ms. Vulnerable time grows ~30 ms per thread (threads finish one by one after recovery). Mean ± SD of 10 trials per size and mode. Controlled runs, not a benchmark.", 7.15, 4.95, 5.55, 1.4, 12, MUTED, italic=True)

# 21-22 · Results: analysis
s = new_slide("Results · when did the warning fire?", "11 · RESULTS", notes="The Analysis view of a live vulnerable trial: score per event, first warning, deadlock and lead time.")
picture(s, "analysis-chart.png", (13.333 - 11.2) / 2, 1.6, w=11.2)
text(s, "Live vulnerable trial in the Analysis view: the score crosses the threshold (70) at event 7 and the cycle is confirmed at event 9; the shaded band is the warning lead time.", 1.07, 6.32, 11.2, 0.6, 12, MUTED, italic=True, align=PP_ALIGN.CENTER)
s = new_slide("Results · why the score is what it is", "11 · RESULTS", notes="Per-factor breakdown of the selected event, and the weight tuner, whose values stay in that visitor's browser.")
picture(s, "analysis-breakdown.png", (13.333 - 4.75 * 2512 / 1208) / 2, 1.6, h=4.75)
text(s, "Per-factor contribution to the selected event's score (left) and the weight tuner (right). Weights are kept per browser and sent with each request; nothing is stored on the server.", 1.07, 6.42, 11.2, 0.5, 12, MUTED, italic=True, align=PP_ALIGN.CENTER)

# 22 · Conclusion
s = new_slide("Conclusion and future work", "CONCLUSION", dark=True, notes="Close with the main results and honest limits.")
for i, (head, lines, colour) in enumerate([
        ("Conclusion", ["Real threads reproduce circular wait on demand, from 2 to 32 threads", "A Wait-For Graph confirms it; the score warns before it in the staged case", "A global lock order prevents it; aborting one victim recovers from it", "Every result comes from repeated, saved measurements"], MINT),
        ("Future work", ["Calibrate the score for N-thread workloads and real programs", "Smarter victim choice (cost, priority, fairness)", "Process-level isolation and other languages", "Evaluate warnings on public bug benchmarks (e.g., GoBench)"], AMBER)]):
    x = 0.6 + i * 6.25
    card(s, x, 1.75, 5.85, 4.7, PANEL)
    text(s, head, x + 0.4, 1.98, 5.0, 0.45, 22, colour, True, HEAD)
    bullets(s, lines, x + 0.4, 2.7, 5.1, 3.6, 17, WHITE, colour, 12)

# 23+ · References (APA 7, alphabetical)
def surname_key(paper):
    return "".join(text for text, _ in paper["apa"]).lower()


refs = sorted(PAPERS, key=surname_key)
for page in range(4):
    chunk = refs[page * 8:(page + 1) * 8]
    if not chunk:
        break
    s = new_slide(f"References ({page + 1}/4)", "12 · REFERENCES · APA 7TH EDITION", notes="APA 7th edition, alphabetical by first author.")
    box = s.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.25))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    for index, paper in enumerate(chunk):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        if index:
            paragraph.space_before = Pt(7)
        props = paragraph._p.get_or_add_pPr()
        props.set("marL", str(int(Inches(0.4))))      # APA hanging indent
        props.set("indent", str(-int(Inches(0.4))))
        for segment, italic in paper["apa"]:
            run = paragraph.add_run()
            run.text = segment
            run.font.name, run.font.size, run.font.italic, run.font.color.rgb = BODY, Pt(13), italic, TEXT

# Last · Thank you
s = new_slide(dark=True, notes="Invite questions; offer a live demo.")
text(s, "Thank you", 0.8, 2.4, 11.7, 1.2, 54, WHITE, True, HEAD, PP_ALIGN.CENTER)
text(s, "Questions and live demo: predictive-deadlock-lab.vercel.app", 0.8, 3.75, 11.7, 0.5, 20, MINT, align=PP_ALIGN.CENTER)
text(s, "Midhun Gereketi · P. Satya Mani Shraavanth · M. Lakshman Sai", 0.8, 4.5, 11.7, 0.5, 16, SOFT, align=PP_ALIGN.CENTER)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print("Saved", OUT.relative_to(ROOT), "with", slide_no, "slides")
