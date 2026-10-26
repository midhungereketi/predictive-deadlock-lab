"""Capture dashboard screenshots for the report and slides from a running server.

Run from the repository root with the app running, e.g.:
    python -m uvicorn member2_backend.api:app --port 8000
    python scripts/capture_screenshots.py --url http://127.0.0.1:8000

Every screenshot shows a real run executed during capture (no mocked data).
Needs `pip install -r requirements-dev.txt` and an installed Chrome.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "submission" / "screens"


def shot(page, selector, name):
    """Screenshot one element with the floating navigation bar hidden."""
    page.evaluate("document.querySelector('header.island').style.visibility = 'hidden'")
    target = page.locator(selector).first
    # Panels fade in when scrolled into view; give the reveal time to finish.
    target.scroll_into_view_if_needed()
    page.wait_for_timeout(1200)
    target.screenshot(path=str(OUT / name))
    page.evaluate("document.querySelector('header.island').style.visibility = ''")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2, reduced_motion="reduce").new_page()
        page.set_default_timeout(120_000)
        page.goto(args.url + "/")
        page.wait_for_selector("#view-lab.is-visible")

        # 8-thread vulnerable ring, replay paused at the moment the cycle is detected.
        page.locator("#multi-thread-count").fill("8")
        page.locator("#multi-thread-count").dispatch_event("change")
        page.locator("#multi-thread-run-button").click()
        page.wait_for_selector("#multi-thread-results:not([hidden])")
        page.locator("#mt-jump").click()
        page.locator("#multi-thread-graph").scroll_into_view_if_needed()
        shot(page, "#multi-thread-results .mt-card", "replay-deadlock.png")

        # Analysis of a live two-thread vulnerable trial.
        page.locator(".nav-item", has_text="Analysis").click()
        page.wait_for_selector("#view-analysis.is-visible")
        page.locator("#an-run-live").click()
        page.wait_for_function("document.getElementById('an-run-label').textContent.includes('live')")
        shot(page, ".an-findings", "analysis-findings.png")
        shot(page, ".an-chart-card", "analysis-chart.png")

        # Compare: scaling test, 3 trials per size.
        page.locator(".nav-item", has_text="Compare").click()
        page.wait_for_selector("#view-compare.is-visible")
        for count in ("4", "16"):
            page.locator(f".cmp-count[data-count='{count}']").click()
        page.locator("#scale-trials").select_option("3")
        page.locator("#scale-run").click()
        page.wait_for_function("document.getElementById('scale-progress').textContent.startsWith('Finished')")
        shot(page, "#scale-section", "compare-scaling.png")

        # Compare: one live run of each mode, then repeated two-thread trials.
        page.locator("#cmp-run-both").click()
        page.wait_for_function("document.getElementById('compare-v-source').textContent === 'LIVE' && !document.getElementById('cmp-run-both').disabled")
        shot(page, "#compare-results", "compare-modes.png")
        page.locator("#batch-count").select_option("5")
        page.locator("#batch-compare-button").click()
        page.wait_for_function("!document.getElementById('batch-comparison-section').hidden && !document.getElementById('batch-compare-button').disabled")
        shot(page, "#batch-comparison-section", "compare-batch.png")

        # Analysis: factor breakdown and weight tuner for the live vulnerable trial.
        page.locator(".nav-item", has_text="Analysis").click()
        page.wait_for_selector("#view-analysis.is-visible")
        shot(page, ".an-grid", "analysis-breakdown.png")

        # Lab: live two-thread vulnerable trial played to the end.
        page.locator(".nav-item", has_text="Lab").click()
        page.wait_for_selector("#view-lab.is-visible")
        page.locator("[data-mode=vulnerable]").first.click()
        page.locator("#live-run-button").click()
        page.wait_for_function("document.getElementById('data-source-label').textContent.includes('Backend trial')")
        for _ in range(40):
            if page.locator("#step-button").is_disabled():
                break
            page.locator("#step-button").click()
        shot(page, "article:has(#graph-state-badge)", "lab-wait-for-graph.png")
        shot(page, "article:has(#chart-line)", "lab-risk-chart.png")

        # Protected 12-thread ring at its busiest moment: threads queue, no cycle.
        page.locator("[data-mode=protected]").first.click()
        page.locator("#multi-thread-count").fill("12")
        page.locator("#multi-thread-count").dispatch_event("change")
        page.locator("#multi-thread-run-button").click()
        page.wait_for_function("document.getElementById('multi-thread-status').textContent === 'COMPLETED'")
        page.locator("#mt-jump").click()
        shot(page, "#multi-thread-results .mt-card", "replay-protected.png")
        browser.close()
    print("Saved screenshots to", OUT)


if __name__ == "__main__":
    main()
