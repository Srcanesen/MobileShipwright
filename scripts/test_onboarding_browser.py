#!/usr/bin/env python3
"""Headless-browser smoke test for the local onboarding page."""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLKIT = ROOT / "scripts/toolkit.py"
spec = importlib.util.spec_from_file_location("mobile_app_ship_toolkit", TOOLKIT)
assert spec and spec.loader
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)


def browser() -> str:
    configured = os.environ.get("MOBILE_APP_SHIP_BROWSER")
    candidates = [
        configured,
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("Chrome or Chromium is required for the CI onboarding browser smoke test")


def render(executable: str, server_port: int, profile: Path, label: str, chrome_lang: str, tmp: Path) -> tuple[str, str, Path]:
    """One deterministic headless render with a forced Chrome locale."""
    url = f"http://127.0.0.1:{server_port}/"
    dom_path = tmp / f"dom-{label}.html"
    error_path = tmp / f"chrome-{label}.log"
    screenshot = tmp / f"mobile-{label}.png"
    timed_out = False
    with dom_path.open("wb") as stdout, error_path.open("wb") as stderr:
        process = subprocess.Popen(
            [
                executable,
                "--headless=new",
                "--no-sandbox",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-first-run",
                f"--lang={chrome_lang}",
                f"--accept-lang={chrome_lang}",
                f"--user-data-dir={profile}",
                "--window-size=390,844",
                f"--screenshot={screenshot}",
                "--virtual-time-budget=3000",
                "--dump-dom",
                url,
            ],
            cwd=ROOT,
            stdout=stdout,
            stderr=stderr,
        )
        try:
            returncode = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait(timeout=5)
    dom = dom_path.read_text(encoding="utf-8", errors="replace") if dom_path.exists() else ""
    if returncode and not (timed_out and dom):
        detail = error_path.read_text(encoding="utf-8", errors="replace")[-500:] if error_path.exists() else ""
        raise RuntimeError(f"headless browser failed with exit {returncode}: {detail}")
    rendered = re.sub(r"<(?:script|style)\b.*?</(?:script|style)>", "", dom, flags=re.DOTALL | re.IGNORECASE)
    return dom, rendered, screenshot


def assert_render(dom: str, rendered: str, screenshot: Path, expect: str, label: str) -> list[str]:
    failed: list[str] = []
    if f"<html lang=\"{expect}\">" not in dom:
        failed.append(f"{label}: initial html lang should be {expect}")
    other = "en" if expect == "tr" else "tr"
    if f'data-lang="{expect}" aria-pressed="true"' not in rendered:
        failed.append(f"{label}: language switcher shows {expect} pressed")
    if f'data-lang="{other}" aria-pressed="false"' not in rendered:
        failed.append(f"{label}: language switcher shows {other} unpressed")
    if len(re.findall(r'class="field(?:\s|\")', rendered)) != len(kit.ONBOARDING_ORDER):
        failed.append(f"{label}: 38 rendered fields")
    if len(re.findall(r'class="section"', rendered)) != 6:
        failed.append(f"{label}: six sections rendered")
    if 'id="f-authorization.public_release"' not in rendered or 'value="no" selected=""' not in rendered:
        failed.append(f"{label}: public release defaults to no")
    if not all(token in rendered for token in ("tr,en-US", "TR,US", "free", "non_consumable")):
        failed.append(f"{label}: guidance examples visible")
    if re.search(r'id="app"[^>]*class="[^"]*fatal', rendered):
        failed.append(f"{label}: no fatal UI state")
    if not screenshot.is_file() or screenshot.stat().st_size <= 1000:
        failed.append(f"{label}: mobile screenshot produced")
    return failed


def main() -> int:
    executable = browser()
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "target"
        target.mkdir()
        server = kit.create_onboarding_server(target)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            html_asset = (ROOT / "skills/mobile-app-ship/assets/onboarding.html").read_text(encoding="utf-8")
            runs = (("turkish", "tr-TR", "tr"), ("english", "en-US", "en"))
            failures: list[str] = []
            for label, chrome_lang, expect in runs:
                profile = Path(tmp) / f"profile-{label}"
                dom, rendered, screenshot = render(executable, server.server_port, profile, label, chrome_lang, Path(tmp))
                failures.extend(assert_render(dom, rendered, screenshot, expect, label))
                if expect == "tr":
                    for token in ("plan kabulü satıcı onayı değildir", "yalnızca gelecek niyetidir"):
                        if token not in rendered:
                            failures.append(f"turkish contract copy rendered: {token}")
                    for token in ("Strict approval contract", "Sıkı onay sözleşmesi"):
                        if token not in dom:
                            failures.append(f"bilingual contract copy in asset: {token}")
                else:
                    for token in ("plan acknowledgement is not vendor approval", "future intent only"):
                        if token not in rendered:
                            failures.append(f"english contract copy rendered: {token}")
            for token in (
                "navigator.languages",
                "localStorage",
                "mobile-app-ship-lang",
                "savedLanguage()",
                "browserLanguage()",
                "rememberLanguage(lang)",
            ):
                if token not in html_asset:
                    failures.append(f"language persistence wiring: {token}")
            if failures:
                raise RuntimeError("browser smoke failed: " + "; ".join(failures))
            print(
                "PASS: onboarding browser rendered 38 fields in 6 sections with strict defaults and guidance in "
                "deterministic Turkish (--lang=tr-TR) and English (--lang=en-US) startups, "
                "correct language-switch state, local persistence wiring, and mobile screenshots"
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
