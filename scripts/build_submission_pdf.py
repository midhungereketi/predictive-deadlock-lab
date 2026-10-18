"""Build a print-ready evaluation report from the saved measured results."""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "submission" / "Final_Report.pdf"
RESULTS = json.loads((ROOT / "docs" / "results.json").read_text(encoding="utf-8"))
V = RESULTS["comparison"]["vulnerable"]
P = RESULTS["comparison"]["protected"]

navy = colors.HexColor("#0c1727")
cyan = colors.HexColor("#057f91")
light = colors.HexColor("#e8f5f7")
red = colors.HexColor("#a23143")
green = colors.HexColor("#16705d")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=28, textColor=navy, spaceAfter=14))
styles.add(ParagraphStyle(name="SubCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor=cyan, spaceAfter=18))
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=navy, spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=cyan, spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=navy, spaceAfter=8))
styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=navy, spaceAfter=5))
styles.add(ParagraphStyle(name="KickerCustom", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=cyan, spaceAfter=8))
styles.add(ParagraphStyle(name="CenterCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, alignment=TA_CENTER, textColor=navy))


def para(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def section(title, body):
    return [para(title, "H1Custom"), para(body)]


def table(rows, widths):
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, cyan),
    ]))
    return t


def page_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(cyan)
    canvas.line(20 * mm, 17 * mm, w - 20 * mm, 17 * mm)
    canvas.setFillColor(navy)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 12 * mm, "Predictive Deadlock Lab | Operating Systems")
    canvas.drawRightString(w - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


story = [
    para("OPERATING SYSTEMS CASE STUDY - FINAL IMPLEMENTATION REPORT", "KickerCustom"),
    para("Predictive Deadlock Prevention Using Contention Analysis and Score Forecasting", "TitleCustom"),
    para("Measured experiment, integrated website, and evaluation", "SubCustom"),
    HRFlowable(width="100%", thickness=2, color=cyan), Spacer(1, 14),
    para("Team: Midhun Gereketi (frontend and integration); P. Satya Mani Shraavanth (threaded backend and API); M. Lakshman Sai (analysis and evaluation)."),
    para("Abstract", "H1Custom"),
    para("A controlled experiment shows how opposite acquisition orders create a two-thread deadlock and how an observed contention signal can activate a shared lock order. Real Python threads and mutexes produce timestamped events. A Wait-For Graph confirms cycles; a heuristic score warns before the cycle in a staged schedule. A FastAPI website renders the trace, score, heatmap, and repeated-trial comparison. In the saved sample, all 10 vulnerable runs deadlocked and all 10 protected runs completed. The result describes this controlled two-lock experiment, not arbitrary applications."),
    para("1. Problem and objectives", "H1Custom"),
    para("T1 requests locks A then B; T2 requests B then A. If each holds its first lock and requests the other, neither can proceed. The project records this dependency, distinguishes risk from confirmed deadlock, and applies a learned common order before protected workers acquire their main-work locks."),
    para("2. Implemented system", "H1Custom"),
    table([
        ["Module", "Implementation and output"],
        ["Threaded experiment", "Vulnerable and protected Python-thread trials with bounded mutex waits"],
        ["Observer", "Timestamped request, acquisition, wait, release, warning, and terminal events"],
        ["Analysis", "Wait-For Graph, cycle detection, score trend, contention matrix"],
        ["API and website", "FastAPI trial/batch endpoints and interactive browser dashboard"],
        ["Evaluation", "Per-trial results, aggregate rates, warning lead, latency, wait and runtime"],
    ], [43 * mm, 126 * mm]),
    Spacer(1, 7),
    para("The repository includes source code, tests, raw results, importable example trials, and a presentation guide. The integrated app runs locally or at https://predictive-deadlock-lab.vercel.app/.", "SmallCustom"),
    PageBreak(),
    para("3. Detection, warning, and prevention", "H1Custom"),
    para("Wait-For Graph", "H2Custom"),
    para("An edge T1 to T2 exists only when T1 waits for a lock currently owned by T2. With one instance of each lock, T1 to T2 and T2 to T1 form a cycle that confirms deadlock. A score warning alone does not confirm a cycle."),
    para("Threat score", "H2Custom"),
    para("The base 0-100 score combines normalized blocked-thread count (35%), observed wait duration (30%), contention count (20%), and resource conflict state (15%). The default high-risk threshold is 70. In this two-lock case, when A and B are held by distinct threads and one cross-resource wait exists, a structural rule raises the score to at least 72. It uses only state available at that timestamp. A confirmed cycle is marked separately."),
    para("Adaptive order", "H2Custom"),
    para("The protected run first creates a bounded, cycle-free probe: T1 holds A, T2 holds B, and T1 waits for B. The observed held/requested pair derives the total order A then B. T2 releases B before requesting A, so the probe never forms a cycle. The main protected workers then normalize both requested lock lists to the derived order before acquiring any main-work lock. An alternate observed B-to-A dependency would derive B then A."),
    para("Why this prevents the demonstrated cycle", "H2Custom"),
    para("When every worker acquires A before B, no worker can hold B while waiting for A. Thus the opposite edge needed for a circular wait cannot form in the protected main phase."),
    para("4. Experimental method", "H1Custom"),
    para("The saved comparison contains 10 vulnerable and 10 protected trials on Windows with Python. Each trial has two logical worker roles and single-instance mutexes A and B. A barrier controls the vulnerable interleaving. A staged 120 ms interval lets the observer record a warning after T1 begins waiting and before T2 requests A. The protected run includes a cycle-free probe in its measured runtime. Trial waits are bounded, and comparison calls use a 3-second per-trial ceiling. The exact collection timestamp and runtime environment are in docs/results.json."),
    para("Metrics", "H2Custom"),
    para("Deadlock rate counts trials with an observed WFG cycle. Completion rate counts trials in which both workers finish. Warning lead is the time from the first pre-cycle high score to first cycle observation. Detection latency is the time from first cycle observation to the supervisor notification. Inconclusive runs are counted separately. Full trial runtime includes cleanup after deadlock notification; the dashboard trial timeline ends at the notification."),
    PageBreak(),
    para("5. Measured results", "H1Custom"),
    para("Saved 10-trial-per-mode dataset", "SubCustom"),
    table([
        ["Metric", "Vulnerable", "Protected"],
        ["Trials", "10", "10"],
        ["Confirmed deadlocks", str(V["deadlock_count"]), str(P["deadlock_count"])],
        ["Completed trials", str(V["completion_count"]), str(P["completion_count"])],
        ["Inconclusive trials", str(V["inconclusive_count"]), str(P["inconclusive_count"])],
        ["Deadlock rate", f"{V['deadlock_rate_percent']}%", f"{P['deadlock_rate_percent']}%"],
        ["Mean full runtime", f"{V['mean_trial_runtime_ms']} ms", f"{P['mean_trial_runtime_ms']} ms"],
        ["Mean peak wait", f"{V['mean_peak_wait_ms']} ms", f"{P['mean_peak_wait_ms']} ms"],
        ["Mean peak score", str(V["mean_peak_score"]), str(P["mean_peak_score"])],
        ["Mean warning lead", f"{V['mean_warning_lead_time_ms']} ms", "Not applicable"],
        ["Mean detection latency", f"{V['mean_detection_latency_ms']} ms", "Not applicable"],
    ], [73 * mm, 48 * mm, 48 * mm]),
    Spacer(1, 12),
    para("The protected score peaks at 72 during its safe probe: this is a warning followed by prevention, not a protected deadlock. The vulnerable run continues through bounded waits and cleanup after the cycle is detected. That cleanup explains why full runtime is longer than the notification timeline."),
    Spacer(1, 8),
    para("6. Interpretation and limitations", "H1Custom"),
    para("The schedule deliberately makes the vulnerable cycle reproducible and provides an observation interval. The warning lead is therefore evidence about this staged case, not a measured general prediction rate. The learned order applies to the protected main phase; it does not repair locks already held by a running worker. The study has only two threads, two locks, one machine, and no larger-workload throughput test. Trials share the FastAPI process rather than isolated worker processes, although mutex waits and the supervisor are bounded."),
    PageBreak(),
    para("7. Reproduce and present", "H1Custom"),
    table([
        ["Step", "Command or action"],
        ["Install", "pip install -r member2_backend/requirements.txt"],
        ["Python tests", "python -m pytest member2_backend/tests member3_analysis/tests -q"],
        ["Frontend tests", "node --test frontend/tests/trial-data.test.js"],
        ["Start local app", "python -m uvicorn member2_backend.api:app --host 127.0.0.1 --port 8000"],
        ["Open dashboard", "http://127.0.0.1:8000/"],
        ["Regenerate data", "python scripts/collect_results.py --trials 10"],
    ], [40 * mm, 129 * mm]),
    Spacer(1, 12),
    para("Run a live vulnerable trial, then a live protected trial. On the Compare page, run the five-each batch and read the measured table. The two docs/sample-*.json files are fallback examples that can be imported if network access is unavailable. The integrated hosted FastAPI app is https://predictive-deadlock-lab.vercel.app/."),
    para("8. Files and evidence", "H1Custom"),
    para("The repository contains member2_backend/ for threaded experiments and API, member3_analysis/ for WFG/scoring/comparison, frontend/ for visualization, docs/results.json for aggregate and per-trial measurements, and docs/sample-vulnerable.json and docs/sample-protected.json for reproducible dashboard imports. The exact study protocol and additional limitations are documented in docs/FINAL_REPORT.md."),
    para("9. Conclusion", "H1Custom"),
    para("The prototype reproduces and detects a controlled circular wait, records a warning before the cycle in the staged vulnerable run, and completes both workers when a shared lock order is derived and applied before their protected main work. Repeated measurements support that conclusion for this scenario. Extending it to larger workloads would require broader schedules, more resources, false-warning analysis, and process isolation."),
]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                        topMargin=19*mm, bottomMargin=23*mm, title="Predictive Deadlock Lab - Final Report")
doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
print(OUT)
