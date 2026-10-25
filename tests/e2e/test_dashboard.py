"""Browser-level tests for the Analysis and Compare views against the real backend."""

import csv
import io
import json
import re

from playwright.sync_api import expect

SCORING_KEY = "deadlock-lab.scoring.v1"
RECOMPUTE_RECORDED = """(weights) => {
  // Re-score the loaded vulnerable run in the browser and pair it with the backend's recorded scores.
  return scenarios.vulnerable.map(frame => [frame.score, DeadlockScoring.scoreState({
    owners: frame.owners, waits: frame.waits, waitMs: frame.waitMs, contention: frame.heat,
    cycle: DeadlockTrialData.hasCycle(frame) }, weights).score]);
}"""


def read_download(download):
    with open(download.path(), encoding="utf-8") as handle:
        return list(csv.reader(io.StringIO(handle.read())))


def set_range(page, selector, value):
    page.locator(selector).fill(str(value))


def test_tabs_switch_and_each_view_renders(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Analysis")
    expect(page.locator("#an-f-peak")).to_have_text("96")
    expect(page.locator("#an-chart .ch-point")).to_have_count(6)
    visitor.tab("Compare")
    expect(page.locator("#compare-v-result")).to_have_text("DEADLOCK")
    expect(page.locator("#compare-p-result")).to_have_text("COMPLETE")
    visitor.tab("Method")
    visitor.tab("Lab")
    expect(page.locator("#view-analysis")).not_to_have_class(re.compile("is-visible"))


def test_weight_tuning_rescores_live_and_explains_where_settings_live(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Analysis")
    scope = page.locator("#an-scope")
    expect(page.locator("#an-verdict")).to_have_text("WARNED 400 MS EARLY")
    expect(scope).to_have_attribute("data-scope", "default")

    set_range(page, "#input-th", 80)
    expect(page.locator("#an-verdict")).to_have_text("DEADLOCK NOT FORESEEN")
    expect(page.locator("#an-f-warn")).to_have_text("none")
    expect(scope).to_have_attribute("data-scope", "temporary")
    expect(scope).to_contain_text("Temporary")

    set_range(page, "#input-wb", 0.6)
    expect(page.locator("#an-sum")).to_contain_text("1.25")
    expect(page.locator("#save-weights-btn")).to_be_disabled()
    page.locator("#an-normalize").click()
    expect(page.locator("#an-sum")).to_contain_text("1.00 ✓")

    page.locator("#save-weights-btn").click()
    expect(scope).to_have_attribute("data-scope", "saved")
    expect(scope).to_contain_text("Saved in this browser only")
    saved = json.loads(page.evaluate(f"localStorage.getItem('{SCORING_KEY}')"))
    assert saved["threshold"] == 80

    page.reload()
    page.wait_for_selector("#view-lab.is-visible")
    visitor.tab("Analysis")
    expect(page.locator("#val-th")).to_have_text("80")
    expect(scope).to_have_attribute("data-scope", "saved")

    page.locator("#an-reset").click()
    expect(page.locator("#val-th")).to_have_text("70")
    expect(scope).to_have_attribute("data-scope", "default")
    assert page.evaluate(f"localStorage.getItem('{SCORING_KEY}')") is None


def test_each_visitor_keeps_private_weights_including_backend_scores(visitor_factory):
    alice, bob = visitor_factory(), visitor_factory()
    alice_page, bob_page = alice.open(), bob.open()

    alice.tab("Analysis")
    set_range(alice_page, "#input-th", 60)
    alice_page.locator("#save-weights-btn").click()
    with alice_page.expect_request(re.compile(r"/api/trials/vulnerable")) as request:
        alice_page.locator("#an-run-live").click()
    assert "threshold_high=60" in request.value.url
    expect(alice_page.locator("#an-run-label")).to_contain_text("live backend trial")

    bob.tab("Analysis")
    expect(bob_page.locator("#val-th")).to_have_text("70")
    expect(bob_page.locator("#an-scope")).to_have_attribute("data-scope", "default")
    with bob_page.expect_request(re.compile(r"/api/trials/vulnerable")) as request:
        bob_page.locator("#an-run-live").click()
    assert "threshold_high" not in request.value.url
    expect(bob_page.locator("#an-run-label")).to_contain_text("live backend trial")

    # Each visitor's recorded backend scores match the browser formula with that visitor's own weights.
    alice_weights = alice_page.evaluate("readWeights()")
    for recorded, recomputed in alice_page.evaluate(RECOMPUTE_RECORDED, alice_weights):
        assert recorded == recomputed
    for recorded, recomputed in bob_page.evaluate(RECOMPUTE_RECORDED, {"w_b": 0.35, "w_w": 0.30, "w_c": 0.20, "w_r": 0.15, "threshold": 70}):
        assert recorded == recomputed


def test_run_both_modes_on_the_backend(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Compare")
    button = page.locator("#cmp-run-both")
    button.click()
    expect(button).to_be_enabled()
    expect(page.locator("#compare-v-source")).to_have_text("LIVE")
    expect(page.locator("#compare-p-source")).to_have_text("LIVE")
    expect(page.locator("#compare-v-result")).to_have_text("DEADLOCK")
    expect(page.locator("#compare-p-result")).to_have_text("COMPLETE")
    expect(page.locator("#compare-insight-text")).to_contain_text("Same two threads")
    assert page.locator("#cmp-chart .ch-point-vuln").count() > 2


def test_repeated_trials_report_rates_and_export_csv(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Compare")
    page.locator("#batch-count").select_option("3")
    button = page.locator("#batch-compare-button")
    button.click()
    expect(button).to_be_enabled()
    expect(page.locator("#batch-table-title")).to_contain_text("3 trials each")
    expect(page.locator(".cmp-trial")).to_have_count(6)
    expect(page.locator("#batch-rates")).to_contain_text("Deadlocked")
    with page.expect_download() as download:
        page.locator("#batch-export").click()
    rows = read_download(download.value)
    assert rows[0][:3] == ["mode", "trial", "status"]
    assert len(rows) == 1 + 6
    assert {row[0] for row in rows[1:]} == {"vulnerable", "protected"}


def test_scaling_runs_repeated_trials_per_size_and_exports_csv(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Compare")
    for count in ("4", "16", "32"):
        page.locator(f".cmp-count[data-count='{count}']").click()
    page.locator("#scale-trials").select_option("3")
    page.locator("#scale-run").click()
    expect(page.locator("#scale-progress")).to_contain_text("Finished. 12 of 12 runs attempted, 0 failed.")
    rows = page.locator("#scale-rows tr")
    expect(rows).to_have_count(2)
    first = rows.nth(0).locator("td")
    expect(first.nth(0)).to_have_text("2")
    expect(first.nth(1)).to_have_text("3 / 3")   # deadlocked
    expect(first.nth(2)).to_have_text("3 / 3")   # cycle through all threads
    expect(first.nth(5)).to_have_text("3 / 3")   # protected completed
    expect(first.nth(4)).to_contain_text("±")     # runtime spread, not a single timing
    assert page.locator("#scale-chart .ch-whisker-vuln").count() >= 2
    expect(page.locator(".cmp-disclaimer")).to_contain_text("not a performance benchmark")
    with page.expect_download() as download:
        page.locator("#scale-export").click()
    data = read_download(download.value)
    assert len(data) == 1 + 12
    meaning = {row[1]: row[5] for row in data[1:]}
    assert meaning == {"vulnerable": "detection + recovery", "protected": "completion"}


def test_backend_failures_show_useful_errors(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    page.route("**/api/trials/**", lambda route: route.fulfill(status=500, content_type="application/json", body='{"detail": "simulated failure"}'))
    page.route("**/api/experiments/multi-thread", lambda route: route.fulfill(status=503, content_type="application/json", body='{"detail": "server busy"}'))
    visitor.tab("Compare")

    page.locator("#cmp-run-both").click()
    expect(page.locator("#cmp-source-note")).to_contain_text("Could not run backend trials")
    expect(page.locator("#cmp-run-both")).to_be_enabled()

    for count in ("4", "8", "16", "32"):
        page.locator(f".cmp-count[data-count='{count}']").click()
    page.locator("#scale-run").click()
    expect(page.locator("#scale-progress")).to_contain_text("Stopped after 3 failed runs in a row")
    expect(page.locator("#scale-errors")).to_contain_text("server busy")
    expect(page.locator("#scale-rows tr td").last).to_have_text("3")
    expect(page.locator("#scale-run")).to_be_enabled()

    visitor.tab("Analysis")
    page.locator("#an-run-live").click()
    expect(page.locator("#an-run-detail")).to_contain_text("Could not run a backend trial")


def test_analysis_event_log_exports_csv(visitor_factory):
    visitor = visitor_factory()
    page = visitor.open()
    visitor.tab("Analysis")
    with page.expect_download() as download:
        page.locator("#export-button").click()
    rows = read_download(download.value)
    assert rows[0][-3:] == ["recorded_score", "formula_score", "level"]
    assert len(rows) == 1 + 6
    assert rows[-1][-1] == "DEADLOCK"
