"""Browser-level test fixtures: a real FastAPI server and a headless browser.

Run: python -m pytest tests/e2e
Needs `pip install -r requirements-dev.txt`. The tests use an installed Chrome by
default (E2E_BROWSER_CHANNEL=chrome); set E2E_BROWSER_CHANNEL="" to use the
Playwright-bundled Chromium after `python -m playwright install chromium`.
"""

import os
import socket
import threading
import time

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed (pip install -r requirements-dev.txt)")
uvicorn = pytest.importorskip("uvicorn")

from member2_backend.api import app  # noqa: E402


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def server_url():
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 20
    while not server.started:
        if time.monotonic() > deadline or not thread.is_alive():
            pytest.fail("The FastAPI test server did not start.")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def e2e_browser():
    channel = os.environ.get("E2E_BROWSER_CHANNEL", "chrome") or None
    with sync_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel=channel, headless=True)
        except Exception as first_error:  # fall back to the bundled Chromium
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception:
                pytest.skip(f"No browser could be launched: {first_error}")
        yield browser
        browser.close()


class Visitor:
    """One browser context: its own storage, so it behaves like a separate user."""

    def __init__(self, browser, base_url):
        # Reduced motion skips the intro and stops the replay from auto-playing.
        self.context = browser.new_context(accept_downloads=True, reduced_motion="reduce", viewport={"width": 1280, "height": 900})
        self.page = self.context.new_page()
        self.page.set_default_timeout(60_000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.base_url = base_url

    def open(self):
        self.page.goto(self.base_url + "/")
        self.page.wait_for_selector("#view-lab.is-visible")
        return self.page

    def tab(self, name):
        self.page.locator(".nav-item", has_text=name).click()
        self.page.wait_for_selector(f"#view-{name.lower()}.is-visible")


@pytest.fixture
def visitor_factory(e2e_browser, server_url):
    visitors = []

    def make():
        visitor = Visitor(e2e_browser, server_url)
        visitors.append(visitor)
        return visitor

    yield make
    for visitor in visitors:
        errors = list(visitor.errors)
        visitor.context.close()
        assert not errors, f"Uncaught page errors: {errors}"
