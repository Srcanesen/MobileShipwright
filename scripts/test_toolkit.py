#!/usr/bin/env python3
"""Deterministic, offline safety checks for scripts/toolkit.py."""
from __future__ import annotations

import argparse
import copy
import http.client
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
TOOLKIT = ROOT / "scripts/toolkit.py"
spec = importlib.util.spec_from_file_location("mobile_app_ship_toolkit", TOOLKIT)
assert spec and spec.loader
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
VALIDATOR = ROOT / "skills/mobile-app-ship/scripts/validate_playbook.py"
validator_spec = importlib.util.spec_from_file_location("mobile_app_ship_validator", VALIDATOR)
assert validator_spec and validator_spec.loader
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)


def cli(*args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(TOOLKIT), *args], cwd=ROOT, env=env, text=True, capture_output=True, timeout=30, check=False)


ONBOARDING_ASSIGNMENTS = {
    "tooling.harness": "pi",
    "project.platforms": "ios",
    "connection.asc": "ready",
    "connection.firebase": "ready",
    "connection.revenuecat": "not_needed",
    "connection.flutter": "ready",
    "connection.xcode": "ready",
    "connection.xcodebuildmcp": "ready",
    "connection.gcloud_play": "not_needed",
    "app.name": "Example App",
    "app.bundle_id": "com.example.mobileapp",
    "app.package_name": "com.example.mobileapp",
    "support.email": "support@example.com",
    "review.first_name": "Ada",
    "review.last_name": "Lovelace",
    "review.email": "review@example.com",
    "review.phone": "+15551234567",
    "review.demo_access_required": "manual",
    "listing.primary_locale": "tr",
    "listing.locales": "tr,en-US",
    "listing.territories": "TR,US",
    "pricing.app": "0.99|USD|US",
    "pricing.iaps": "com.example.mobileapp.premium|non_consumable|4.99|USD|US;com.example.mobileapp.tip|consumable|0.99|USD|US",
    "distribution.release_mode": "manual",
    "screenshots.device_families": "iphone,ipad",
    "privacy.readiness": "ready",
    "distribution.build_policy": "latest_testflight",
    "authorization.firebase_create_deploy": "yes",
    "authorization.app_store_records_metadata": "yes",
    "authorization.iap_catalog": "yes",
    "authorization.pricing_availability": "yes",
    "authorization.revenuecat_config": "no",
    "authorization.signing_assets": "yes",
    "authorization.screenshot_upload_replace": "yes",
    "authorization.build_upload": "yes",
    "authorization.testflight_distribution": "yes",
    "authorization.review_submission": "yes",
    "authorization.public_release": "no",
}


def complete_onboarding_command(target: str) -> list[str]:
    command = ["onboard", "--target", target]
    for key, value in ONBOARDING_ASSIGNMENTS.items():
        command.extend(("--set", f"{key}={value}"))
    return command


def write_auth_progress(target: str) -> None:
    steps = [
        {"id": "apple", "outcome": "verified", "claim": "ASC inventory read back", "evidenceId": "ev-apple", "limitation": ""},
        {"id": "xcodebuildmcp", "outcome": "verified", "claim": "Live tools discovered", "evidenceId": "ev-xcode", "limitation": ""},
        {"id": "revenuecat", "outcome": "not_needed", "claim": "", "evidenceId": "", "limitation": "Not used"},
        {"id": "firebase", "outcome": "verified", "claim": "Project inventory read back", "evidenceId": "ev-firebase", "limitation": ""},
    ]
    (Path(target) / kit.PROGRESS).write_text(json.dumps({"schemaVersion": "1.0.0", "steps": steps}), encoding="utf-8")


def read_status_fixture() -> dict:
    return json.loads((ROOT / "tests/fixtures/status-valid.json").read_text(encoding="utf-8"))


class ToolkitSafetyTests(unittest.TestCase):
    def test_bootstrap_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            before = set(target.rglob("*"))
            result = cli("bootstrap", "--harness", "claude-code", "--target", tmp, "--platform", "ios")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("dry-run: no writes", result.stdout)
            self.assertEqual(before, set(target.rglob("*")))

    def test_bootstrap_rejects_unknown_approval_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = cli("bootstrap", "--harness", "claude-code", "--target", tmp, "--platform", "ios", "--apply", "--approve", "adpater")
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown bootstrap approval name", result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_skill_and_adapter_refuse_second_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            command = ("bootstrap", "--harness", "claude-code", "--target", tmp, "--platform", "ios", "--apply", "--approve", "skill", "--approve", "adapter")
            first = cli(*command)
            self.assertEqual(first.returncode, 0, first.stderr)
            skill = Path(tmp) / ".claude/skills/mobile-app-ship/SKILL.md"
            adapter = Path(tmp) / ".mcp.json"
            self.assertTrue(skill.is_file())
            self.assertTrue(adapter.is_file())
            skill_before, adapter_before = skill.read_bytes(), adapter.read_bytes()
            second = cli(*command)
            self.assertIn("refusing overwrite", second.stdout)
            self.assertEqual(skill_before, skill.read_bytes())
            self.assertEqual(adapter_before, adapter.read_bytes())

    def test_windsurf_never_writes_project_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = cli("bootstrap", "--harness", "windsurf", "--target", tmp, "--platform", "ios", "--apply", "--approve", "adapter")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("~/.codeium/windsurf/mcp_config.json", result.stdout)
            self.assertFalse((Path(tmp) / ".windsurf/mcp_config.json").exists())

    def test_gemini_never_writes_broken_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = cli("bootstrap", "--harness", "gemini-cli", "--target", tmp, "--platform", "ios", "--apply", "--approve", "gemini-context")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no GEMINI.md fallback is written", result.stdout)
            self.assertFalse((Path(tmp) / "GEMINI.md").exists())

    def test_onboarding_v3_acknowledgement_migration_and_invalidation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            legacy_decisions = {key: kit.onboarding_value(key, value) for key, value in ONBOARDING_ASSIGNMENTS.items()}
            legacy = {"schemaVersion":"2.0.0","decisions":legacy_decisions,"approvalMode":"one-shot","allowedBatchCategories":[],"masterApproval":{"version":"1.0.0","id":"ma-"+"a"*32,"approvedAt":"2026-01-01T00:00:00Z","canonicalSha256":"a"*64,"scopes":["build.upload"]}}
            (target / kit.ONBOARDING).write_text(json.dumps(legacy), encoding="utf-8")
            migrated = cli("onboard", "--target", tmp, "--set", "app.name=Example App v3", "--json")
            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            data = json.loads((target / kit.ONBOARDING).read_text())
            self.assertEqual(data["schemaVersion"], "3.0.0")
            self.assertEqual(data["approvalMode"], "strict")
            self.assertIsNone(data["planAcknowledgement"])
            self.assertNotIn("masterApproval", data)
            self.assertEqual(data["decisions"]["app.name"], "Example App v3")
            write_auth_progress(tmp)
            acknowledged = cli(*complete_onboarding_command(tmp), "--acknowledge-plan", "--json")
            self.assertEqual(acknowledged.returncode, 0, acknowledged.stderr)
            self.assertTrue(json.loads(acknowledged.stdout)["planAcknowledged"])
            self.assertIn("canonicalSha256", json.loads((target / kit.ONBOARDING).read_text())["planAcknowledgement"])
            self.assertEqual(cli("onboard", "--target", tmp, "--set", "app.name=Changed").returncode, 0)
            self.assertIsNone(json.loads((target / kit.ONBOARDING).read_text())["planAcknowledgement"])

    def test_deprecated_alias_and_scope_check_never_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_auth_progress(tmp)
            alias = cli(*complete_onboarding_command(tmp), "--approve-plan", "--json")
            self.assertEqual(alias.returncode, 0, alias.stderr)
            self.assertTrue(json.loads(alias.stdout)["planAcknowledged"])
            checked = cli("onboard", "--target", tmp, "--check-scope", "build.upload", "--json")
            self.assertEqual(checked.returncode, 2)
            self.assertEqual(json.loads(checked.stdout), {"approved": False, "reason": "future_intent_only", "scope": "build.upload"})

    def test_acknowledgement_requires_complete_readiness_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blocked = cli(*complete_onboarding_command(tmp), "--acknowledge-plan")
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("requires verified/not_needed next-auth evidence", blocked.stderr)

    def test_status_rejects_master_reuse_unconsumed_and_target_mismatch(self) -> None:
        data = json.loads((ROOT / "tests/fixtures/status-valid.json").read_text())
        evidence = {"id":"ev-write","claim":"readback","source":"store_readback","timestamp":"2026-07-31T10:00:00Z","toolVersion":"test","sanitizedResult":"matched","limitations":""}
        gate = {"id":"gate-write","class":"approval_required","action":"exact vendor action","target":"ios","state":"consumed","approvedAt":"2026-07-31T10:00:00Z"}
        action = {"id":"write","intent":"concise intent","target":"ios","tool":"asc","classification":"external_mutation","status":"verified","gateId":"gate-write","verificationQuery":"read back","evidenceIds":["ev-write"]}
        data["evidence"].append(evidence); data["gates"].append(gate); data["actions"].append(action)
        self.assertEqual(validator.status_errors(data), [])
        master = copy.deepcopy(data); master["gates"][-1]["class"] = "master_approval"; self.assertTrue(validator.status_errors(master))
        unconsumed = copy.deepcopy(data); unconsumed["gates"][-1]["state"] = "approved"; self.assertTrue(validator.status_errors(unconsumed))
        mismatch = copy.deepcopy(data); mismatch["gates"][-1]["target"] = "android"; self.assertTrue(validator.status_errors(mismatch))
        reused = copy.deepcopy(data); clone = copy.deepcopy(action); clone["id"] = "reused-action"; reused["actions"].append(clone); self.assertTrue(validator.status_errors(reused))
        failed_then_reused = copy.deepcopy(data); failed_then_reused["actions"][-1]["status"] = "failed"; failed_then_reused["actions"].append(clone); self.assertTrue(validator.status_errors(failed_then_reused))
        failed_without_evidence = copy.deepcopy(data); failed_without_evidence["actions"][-1]["status"] = "failed"; failed_without_evidence["actions"][-1]["evidenceIds"] = []
        self.assertIn("failed external mutation lacks sanitized evidence: write", validator.status_errors(failed_without_evidence))
        for status in ("started", "outcome_unknown", "failed"):
            attempted = copy.deepcopy(data); attempted["actions"][-1]["status"] = status; attempted["gates"][-1]["state"] = "approved"
            self.assertTrue(validator.status_errors(attempted), status)

    def test_duplicate_evidence_ids_rejected_in_actions_and_history(self) -> None:
        data = read_status_fixture()
        dup_action = copy.deepcopy(data)
        dup_action["actions"][0]["evidenceIds"] = ["ev-build", "ev-build"]
        self.assertIn("duplicate action evidenceIds: act-build", validator.status_errors(dup_action))
        dup_history = copy.deepcopy(data)
        dup_history["targets"]["ios"]["history"][1]["evidenceIds"] = ["ev-build", "ev-build"]
        self.assertIn("duplicate history evidenceIds: ios", validator.status_errors(dup_history))
        self.assertEqual(validator.status_errors(read_status_fixture()), [])

    def test_onboard_web_is_strict_bilingual_and_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = kit.create_onboarding_server(Path(tmp)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/api/state"); response = conn.getresponse(); state = json.loads(response.read())
                self.assertEqual(response.status, 200); self.assertEqual(state["approvalMode"], "strict"); self.assertEqual(len(state["fields"]), 38)
                self.assertTrue(all(set(field["label"]) == {"en", "tr"} for field in state["fields"]))
                body = json.dumps({"decisions": ONBOARDING_ASSIGNMENTS})
                conn.request("POST", "/api/save", body, {"Content-Type":"application/json"}); self.assertEqual(conn.getresponse().status, 200)
                self.assertIsNone(json.loads((Path(tmp) / kit.ONBOARDING).read_text())["planAcknowledgement"])
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_api_schema_returns_canonical_schema_distinct_from_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            server = kit.create_onboarding_server(Path(tmp)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/api/schema"); response = conn.getresponse(); schema = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
                self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy") or "")
                conn.request("GET", "/api/state"); state = json.loads(conn.getresponse().read())
                self.assertNotEqual(schema, state)
                for key in ("$schema", "title", "type", "properties", "$defs", "required", "additionalProperties"):
                    self.assertIn(key, schema)
                self.assertEqual(schema["required"], ["schemaVersion", "decisions", "approvalMode", "planAcknowledgement"])
                self.assertEqual(schema["properties"]["schemaVersion"]["const"], "3.0.0")
                self.assertEqual(schema["additionalProperties"], False)
                self.assertNotIn("fields", schema)
                self.assertIn("fields", state)
                canonical = json.loads((ROOT / "skills/mobile-app-ship/assets/onboarding.schema.json").read_text(encoding="utf-8"))
                self.assertEqual(schema, canonical)
                conn.request("GET", "/api/schema", headers={"Host": "example.com"})
                self.assertEqual(conn.getresponse().status, 403)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_onboard_schema_runtime_parity_has_38_fields_and_70_choices(self) -> None:
        schema = json.loads((ROOT / "skills/mobile-app-ship/assets/onboarding.schema.json").read_text(encoding="utf-8"))
        properties = schema["properties"]["decisions"]["properties"]
        fields = kit.web_field_schema()
        self.assertEqual(len(fields), 38)
        self.assertEqual(set(properties), set(kit.FIELD_DESCRIPTORS))
        self.assertEqual([field["key"] for field in fields], kit.ONBOARDING_ORDER)
        choice_count = 0
        for field in fields:
            choices = field["choices"] or []
            choice_count += len(choices) + len(field["valueOptions"])
            if choices:
                self.assertEqual({choice["value"] for choice in choices}, set(properties[field["key"]]["enum"]))
                for choice in choices:
                    self.assertEqual(kit.onboarding_value(field["key"], choice["value"]), choice["value"])
        self.assertGreaterEqual(choice_count, 70)

    def test_onboard_web_metadata_is_meaningfully_bilingual(self) -> None:
        metadata = []
        for field in kit.web_field_schema():
            self.assertEqual(set(field["label"]), {"en", "tr"})
            self.assertEqual(set(field["description"]), {"en", "tr"})
            self.assertGreaterEqual(len(field["description"]["en"].split()), 7)
            self.assertGreaterEqual(len(field["description"]["tr"].split()), 7)
            self.assertNotEqual(field["description"]["en"], field["description"]["tr"])
            guidance = field["guidance"]
            for lang in ("en", "tr"):
                self.assertEqual(set(guidance[lang]), {"format", "example", "why"}, field["key"])
                for value in guidance[lang].values():
                    self.assertIsInstance(value, str)
                    self.assertTrue(value)
            for choice in (field["choices"] or []) + field["valueOptions"]:
                self.assertEqual(set(choice["label"]), {"en", "tr"})
                self.assertEqual(set(choice["detail"]), {"en", "tr"})
                self.assertGreaterEqual(len(choice["detail"]["en"].split()), 5)
                self.assertGreaterEqual(len(choice["detail"]["tr"].split()), 5)
                self.assertNotEqual(choice["detail"]["en"], choice["detail"]["tr"])
                metadata.extend(choice["label"].values())
            metadata.extend(field["label"].values())
        self.assertRegex(" ".join(metadata), r"[çğıöşüÇĞİÖŞÜ]")

    def test_onboard_web_guidance_holds_exact_required_examples(self) -> None:
        examples = {field["key"]: field["guidance"]["en"]["example"] for field in kit.web_field_schema()}
        self.assertEqual(len(examples), 38)
        self.assertIn("tr,en-US", examples["listing.locales"])
        self.assertIn("TR,US", examples["listing.territories"])
        self.assertIn("free", examples["pricing.app"])
        self.assertIn("4.99|USD|US", examples["pricing.app"])
        self.assertIn("com.example.app.premium|non_consumable|4.99|USD|US", examples["pricing.iaps"])
        self.assertIn("[]", next(field for field in kit.web_field_schema() if field["key"] == "pricing.iaps")["guidance"]["en"]["format"])
        self.assertIn("com.example.app", examples["app.bundle_id"])
        self.assertIn("com.example.app", examples["app.package_name"])
        self.assertIn("support@example.com", examples["support.email"])
        self.assertIn("review@example.com", examples["review.email"])
        self.assertIn("+15551234567", examples["review.phone"])
        self.assertIn("Ada", examples["review.first_name"])
        self.assertIn("Lovelace", examples["review.last_name"])
        self.assertIn("Example App", examples["app.name"])

    def test_onboard_web_groups_are_six_with_bilingual_descriptions(self) -> None:
        state = kit.onboarding_web_state(Path(tempfile.mkdtemp()))
        self.assertEqual(len(state["groups"]), 6)
        self.assertEqual(list(state["groups"]), ["setup", "connections", "identity", "listing", "release", "authorization"])
        for group, info in state["groups"].items():
            self.assertEqual(set(info), {"en", "tr", "description"}, group)
            self.assertEqual(set(info["description"]), {"en", "tr"})
            self.assertGreaterEqual(len(info["description"]["en"].split()), 7)
            self.assertGreaterEqual(len(info["description"]["tr"].split()), 7)
            self.assertNotEqual(info["description"]["en"], info["description"]["tr"])
            self.assertRegex(info["description"]["en"], r"\b(?:does not|do not|never)\b")
            self.assertRegex(info["description"]["tr"], r"değil|kurmaz|yazmaz|vermez|yapmaz|saklamaz|dağıtmaz|yetkilendirmez")
        self.assertEqual(len(state["fields"]), 38)

    def test_onboard_rejects_unknown_secret_and_noncanonical_input(self) -> None:
        cases = (
            (("--set", "unknown.field=value"), "unknown onboarding decision"),
            (("--set", "app.name=token=do-not-store"), "never provide secrets"),
            (("--set", "listing.primary_locale=tr-TR"), "canonical App Store Connect locale"),
        )
        for arguments, message in cases:
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as tmp:
                result = cli("onboard", "--target", tmp, *arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)
                self.assertFalse((Path(tmp) / kit.ONBOARDING).exists())
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / kit.ONBOARDING).write_text("[]", encoding="utf-8")
            malformed = cli("onboard", "--target", tmp)
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("onboarding top-level shape", malformed.stderr)

    def test_onboard_interactive_tty_is_validated_and_resumable(self) -> None:
        def arguments(target: str) -> argparse.Namespace:
            return argparse.Namespace(target=target, set=[], check_scope=None, approval_mode=None, allow_batch_category=[], interactive=True, acknowledge_plan=False, approve_plan=False, json=False, language="tr")
        prompts: list[str] = []

        def fake_input(prompt: str = "") -> str:
            prompts.append(prompt)
            if len(prompts) == 1:
                return "pi"
            raise KeyboardInterrupt

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(kit.sys.stdin, "isatty", return_value=True), mock.patch("builtins.input", side_effect=fake_input):
            self.assertEqual(kit.onboard(arguments(tmp)), 2)
            saved = json.loads((Path(tmp) / kit.ONBOARDING).read_text(encoding="utf-8"))
            self.assertEqual(saved["decisions"], {"tooling.harness": "pi"})
            self.assertIn("Yapay zeka araç ortamı", prompts[0])
            self.assertIn("yerel kodlama araç ortamını seçer", prompts[0])
            self.assertNotIn("Select the local coding harness", prompts[0])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(kit.sys.stdin, "isatty", return_value=True), mock.patch("builtins.input", return_value="token=do-not-store"):
            self.assertEqual(kit.onboard(arguments(tmp)), 2)
            self.assertFalse((Path(tmp) / kit.ONBOARDING).exists())

    def test_onboard_web_runtime_contract_is_live_numeric_and_strict_only(self) -> None:
        html = (ROOT / "skills/mobile-app-ship/assets/onboarding.html").read_text(encoding="utf-8")
        for token in ("updateChoiceDetail", "Current choice consequence", "HTMLInputElement", "fieldset", "legend", "aria-live", "prefers-reduced-motion", "@media(max-width:767px)", "JSON.stringify({decisions:state.decisions})", "planAcknowledgementCommand", "authEvidenceBlockers"):
            self.assertIn(token, html)
        self.assertIn("option.value+']'", html)
        self.assertRegex(html, r"filled\+' / '\+state\.total")
        self.assertNotRegex(html, re.compile(r"<(?:meter|progress|svg)\b|progress[^\n]{0,30}track|approval.?mode|safe.?batched|one.?shot|allowedBatch", re.I))

    def test_onboard_web_asset_and_http_security_contract(self) -> None:
        html = (ROOT / "skills/mobile-app-ship/assets/onboarding.html").read_text(encoding="utf-8")
        self.assertNotRegex(html, re.compile(r"https?://|<script\s+src=|[—–]|<svg\b|fake.?screenshot", re.I))
        self.assertIn("secret-free", html)
        self.assertIn("never authenticates, contacts a vendor, or executes a release", html)
        with tempfile.TemporaryDirectory() as tmp:
            server = kit.create_onboarding_server(Path(tmp)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/"); response = conn.getresponse(); response.read()
                self.assertEqual(response.status, 200)
                self.assertIn("default-src 'none'", response.getheader("Content-Security-Policy"))
                self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
                self.assertIn("payment=()", response.getheader("Permissions-Policy"))
                conn.request("GET", "/", headers={"Host": "example.com"}); denied = conn.getresponse(); denied.read()
                self.assertEqual(denied.status, 403)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_onboard_web_save_readback_and_acknowledgement_invalidation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_auth_progress(tmp)
            acknowledged = cli(*complete_onboarding_command(tmp), "--acknowledge-plan", "--json")
            self.assertEqual(acknowledged.returncode, 0, acknowledged.stderr)
            server = kit.create_onboarding_server(Path(tmp)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/api/state"); current = json.loads(conn.getresponse().read())
                self.assertEqual(current["planAcknowledgementStatus"], "current")
                self.assertIsNone(current["planAcknowledgementCommand"])
                stale_data = json.loads((Path(tmp) / kit.ONBOARDING).read_text(encoding="utf-8"))
                stale_data["decisions"]["app.name"] = "Example App stale"
                kit.atomic_json(Path(tmp) / kit.ONBOARDING, stale_data)
                conn.request("GET", "/api/state"); stale = json.loads(conn.getresponse().read())
                self.assertEqual(stale["planAcknowledgementStatus"], "stale")
                self.assertTrue(stale["planAcknowledgementCommand"].endswith(" --acknowledge-plan"))
                changed = dict(ONBOARDING_ASSIGNMENTS, **{"app.name": "Example App 2"})
                conn.request("POST", "/api/save", json.dumps({"decisions": changed}), {"Content-Type": "application/json"})
                response = conn.getresponse(); saved = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(saved["state"]["decisions"]["app.name"], "Example App 2")
                self.assertEqual(saved["state"]["planAcknowledgementStatus"], "missing")
                self.assertEqual(saved["state"]["planAcknowledgementCommand"], f"scripts/mobile-app-ship onboard --target {tmp} --acknowledge-plan")
                persisted = json.loads((Path(tmp) / kit.ONBOARDING).read_text(encoding="utf-8"))
                self.assertIsNone(persisted["planAcknowledgement"])
                conn.request("POST", "/api/save", json.dumps({"decisions": {"app.name": "token=secret"}}), {"Content-Type": "application/json"})
                rejected = conn.getresponse(); self.assertEqual(rejected.status, 400); self.assertEqual(json.loads(rejected.read())["error"], "Invalid or secret-like onboarding value")
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_onboard_and_next_auth_use_distinct_compatible_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            auth = cli("next-auth", "--harness", "claude-code", "--target", tmp, "--record", "--approve-progress", "--outcome", "verified", "--claim", "Read-only app inventory returned", "--evidence-id", "asc-apps-001")
            self.assertEqual(auth.returncode, 0, auth.stderr)
            legacy_before = (Path(tmp) / kit.PROGRESS).read_bytes()
            self.assertEqual(cli("onboard", "--target", tmp, "--set", "connection.asc=ready").returncode, 0)
            self.assertNotEqual(kit.ONBOARDING, kit.PROGRESS)
            self.assertEqual((Path(tmp) / kit.PROGRESS).read_bytes(), legacy_before)
            self.assertIn("connection.asc", json.loads((Path(tmp) / kit.ONBOARDING).read_text())["decisions"])
            following = cli("next-auth", "--harness", "claude-code", "--target", tmp)
            self.assertIn("NEXT xcodebuildmcp:", following.stdout)

    def test_next_auth_not_needed_advances_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skipped = cli("next-auth", "--harness", "pi", "--target", tmp, "--record", "--approve-progress", "--outcome", "not_needed", "--limitation", "iOS is out of scope")
            self.assertEqual(skipped.returncode, 0, skipped.stderr)
            self.assertIn("out-of-scope provider apple", skipped.stdout)
            self.assertIn("NEXT xcodebuildmcp:", cli("next-auth", "--harness", "pi", "--target", tmp).stdout)

    def test_next_auth_requires_verified_readback_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = cli("next-auth", "--harness", "claude-code", "--target", tmp, "--record", "--approve-progress", "--outcome", "verified", "--claim", "Read-only app inventory returned")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(tmp) / kit.PROGRESS).exists())

    def test_next_auth_rejects_secret_like_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = cli("next-auth", "--harness", "claude-code", "--target", tmp, "--record", "--approve-progress", "--outcome", "verified", "--claim", "Read-back token=do-not-record", "--evidence-id", "evidence-001")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(tmp) / kit.PROGRESS).exists())

    def test_sanitize_report_masks_secret_assignment_values(self) -> None:
        pem = "-----BEGIN " + "PRIVATE KEY-----\nprivate-body-value\n-----END " + "PRIVATE KEY-----"
        report = {
            "app": {"name": "Example App"},
            "notes": "token=abc123 and api_key: xyz789",
            "vendor": {"detail": 'client_secret: "supersecret12"'},
            "quoted": {"detail": '"apiKey": "quoted-secret", "password": "hunter2"'},
            "escaped": {"detail": r'"token": "a\"b-escaped-secret"'},
            "pem": pem,
            "credentials": {"token": "sk_live_ab12", "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.sig123"},
            "plain_fields": {"token": "plain-secret-value", "api_key": "plain-api-value", "idToken": "identity-secret", "oauth_token": "oauth-secret", "session-secret": "session-value"},
        }
        cleaned = kit.sanitize_report(report)
        text = json.dumps(cleaned)
        for secret in ("abc123", "xyz789", "supersecret12", "quoted-secret", "hunter2", "escaped-secret", "private-body-value", "sk_live_ab12", "eyJhbGciOiJIUzI1NiJ9", "sig123", "plain-secret-value", "plain-api-value", "identity-secret", "oauth-secret", "session-value"):
            self.assertNotIn(secret, text)
        self.assertIn("Example App", text)
        self.assertIn("[redacted]", text)
        self.assertEqual(kit.sanitize_report("token=only-label-matches"), "[redacted]")
        # Rejection behavior at trust boundaries covers the label and quoted JSON assignments.
        self.assertTrue(kit.SECRET_RE.search('"token": "abc123"'))
        self.assertTrue(kit.SECRET_RE.search("token=abc123"))
        self.assertTrue(kit.SECRET_RE.search("api_key: abc123"))

    def test_access_refresh_and_authorization_secrets_are_rejected_and_masked(self) -> None:
        for value in ("access_token=value", "refresh-token=value", "accessToken=value", "refreshToken=value", "id_token=value", "idToken=value", "oauth-token=value", "oauthToken=value", "session_secret=value", "sessionSecret=value", "Authorization: Bearer value", "Authorization: Basic value"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    kit.safe_text(value, "claim")
        self.assertEqual(kit.safe_text("authorization: not required", "claim"), "authorization: not required")
        with tempfile.TemporaryDirectory() as tmp:
            rejected = cli("onboard", "--target", tmp, "--set", "app.name=access_token=value")
            self.assertEqual(rejected.returncode, 2)
        report = {
            "nested": {"access_token": "snake value", "refresh-token": "kebab value", "accessToken": "camel value", "refreshToken": "camel refresh", "Authorization": "Bearer header value"},
            "headers": "Authorization: Bearer header value; Authorization: Basic basic value",
            "assignment": "access_token=one two three, next=value",
            "quoted": r'accessToken: "a\\"b value"',
        }
        text = json.dumps(kit.sanitize_report(report))
        for value in ("snake value", "kebab value", "camel value", "camel refresh", "header value", "basic value", "one two three", r'a\\"b value'):
            self.assertNotIn(value, text)

    def test_status_evidence_rejects_secret_assignments_and_allows_benign_prose(self) -> None:
        data = read_status_fixture()
        self.assertEqual(validator.status_errors(data), [])
        for field, value in (("claim", "id_token=do-not-record"), ("sanitizedResult", "oauthToken: do-not-record"), ("limitations", "session_secret = do-not-record"), ("claim", "Authorization: Bearer do-not-record"), ("claim", "sk_live_ab12")):
            with self.subTest(field=field, value=value):
                leaked = copy.deepcopy(data)
                leaked["evidence"][0][field] = value
                self.assertIn("evidence contains possible secret: ev-scope", validator.status_errors(leaked))
        benign = copy.deepcopy(data)
        benign["evidence"][0]["claim"] = "The authorization is not required for this read-only check."
        self.assertEqual(validator.status_errors(benign), [])

    def test_timestamp_and_reference_validation_are_safe(self) -> None:
        self.assertTrue(validator.iso_time("2026-01-02T03:04:05Z"))
        for value in ("2026-01-02T03:04:05.123Z", "2026-01-02T03:04:05+00:00", "2026-02-30T03:04:05Z"):
            self.assertFalse(validator.iso_time(value), value)
        with tempfile.TemporaryDirectory() as tmp:
            refs = Path(tmp)
            (refs / "historical.md").write_text("The historical master/one-shot migration is retired.", encoding="utf-8")
            self.assertEqual(validator.active_reference_authorization_errors(refs), [])
            (refs / "active.md").write_text("A master scope authorizes this write.", encoding="utf-8")
            self.assertEqual(validator.active_reference_authorization_errors(refs), ["active authorization alternative: active.md"])
        with tempfile.TemporaryDirectory() as tmp:
            data = read_status_fixture()
            data["actions"][0]["evidenceIds"] = [{}]
            data["actions"][0]["gateId"] = {}
            data["targets"]["ios"]["history"][0]["actionId"] = {}
            (Path(tmp) / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            result = cli("preflight", "--target", tmp, "--platform", "ios", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(json.loads(result.stdout)["valid"])

    def test_deferred_stays_resumable_and_verified_advances_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deferred = cli("next-auth", "--harness", "claude-code", "--target", tmp, "--record", "--approve-progress", "--outcome", "deferred", "--limitation", "Account owner unavailable")
            self.assertEqual(deferred.returncode, 0, deferred.stderr)
            self.assertIn("not complete", deferred.stdout)
            again = cli("next-auth", "--harness", "claude-code", "--target", tmp)
            self.assertIn("NEXT apple:", again.stdout)
            verified = cli("next-auth", "--harness", "claude-code", "--target", tmp, "--record", "--approve-progress", "--outcome", "verified", "--claim", "Read-only app inventory returned", "--evidence-id", "asc-apps-001", "--limitation", "No mutation attempted")
            self.assertEqual(verified.returncode, 0, verified.stderr)
            following = cli("next-auth", "--harness", "claude-code", "--target", tmp)
            self.assertIn("NEXT xcodebuildmcp:", following.stdout)
            data = json.loads((Path(tmp) / kit.PROGRESS).read_text(encoding="utf-8"))
            self.assertEqual(data["steps"], [{"id": "apple", "outcome": "verified", "claim": "Read-only app inventory returned", "evidenceId": "asc-apps-001", "limitation": "No mutation attempted"}])

    def test_doctor_defers_out_of_scope_tools_without_probing(self) -> None:
        tool = {"id": "xcodebuild", "command": "xcodebuild", "testedVersion": "26.6", "ownerDomain": "Apple/Xcode", "platforms": ["ios"], "requirement": "required", "macosOnly": True}
        with mock.patch.object(kit, "resolve_tool") as resolve:
            check = kit.tool_check(tool, "android")
        self.assertEqual(check["status"], "DEFER")
        resolve.assert_not_called()

    def test_capability_aware_node_and_pod_checks_defer_without_signals(self) -> None:
        node = {"id": "node", "command": "node", "testedVersion": "24.18.0", "ownerDomain": "Node.js", "platforms": ["shared"], "requirement": "required"}
        pod = {"id": "pod", "command": "pod", "testedVersion": "1.17.0", "ownerDomain": "CocoaPods", "platforms": ["ios"], "requirement": "required", "macosOnly": True}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(kit, "resolve_tool") as resolve:
            target = Path(tmp)
            self.assertEqual(kit.tool_check(node, "ios", target)["status"], "DEFER")
            self.assertEqual(kit.tool_check(pod, "ios", target)["status"], "DEFER")
            resolve.assert_not_called()
            (target / "package.json").write_text("{}", encoding="utf-8")
            (target / "ios").mkdir()
            (target / "ios/Podfile").write_text("platform :ios", encoding="utf-8")
            resolve.return_value = (Path("/mock/tool"), "24.18.0 1.17.0", None)
            self.assertEqual(kit.tool_check(node, "ios", target)["status"], "PASS")
            self.assertEqual(kit.tool_check(pod, "ios", target)["status"], "PASS")
        with mock.patch.object(kit, "resolve_tool", return_value=(Path("/mock/node"), "24.18.0", None)):
            self.assertEqual(kit.tool_check(node, "ios")["status"], "PASS")

    def test_resolve_tool_uses_exact_alternate_and_reports_broken_path(self) -> None:
        tool = {"id": "java", "command": "java", "testedVersion": "17.0.20"}
        alternate, generic = Path("/opt/homebrew/opt/openjdk@17/bin/java"), Path("/usr/bin/java")
        def probe(_tool: dict, executable: Path) -> tuple[int, str]:
            return (0, "openjdk 17.0.20") if executable == alternate else (1, "Unable to locate a Java Runtime")
        with mock.patch.object(kit.shutil, "which", return_value=str(generic)), mock.patch.object(kit, "tool_candidates", return_value=[alternate, generic]), mock.patch.object(kit, "version_probe", side_effect=probe):
            path, output, path_problem = kit.resolve_tool(tool)
        self.assertEqual(path, alternate)
        self.assertIn("17.0.20", output or "")
        self.assertIn("/usr/bin/java", path_problem or "")

    def test_android_cmdline_missing_is_a_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(kit, "android_sdk_root", return_value=Path(tmp) / "sdk"), mock.patch.object(kit, "android_cmdline_source", return_value=None):
            check = kit.android_cmdline_check()
        self.assertEqual(check["status"], "GAP")
        self.assertIn("no installed sdkmanager source", check["detail"])

    def test_android_cmdline_copy_is_scoped_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, source = Path(tmp) / "sdk", Path(tmp) / "homebrew/cmdline-tools/latest"
            executable = source / "bin/sdkmanager"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            with mock.patch.object(kit, "android_sdk_root", return_value=root), mock.patch.object(kit, "android_cmdline_source", return_value=source):
                first = kit.install_android_cmdline()
                second = kit.install_android_cmdline()
            destination = root / "cmdline-tools/latest"
            self.assertEqual(first["status"], "PASS")
            self.assertEqual(second["status"], "PASS")
            self.assertFalse(destination.is_symlink())
            self.assertEqual((destination / "bin/sdkmanager").read_text(encoding="utf-8"), "#!/bin/sh\n")

    def test_npm_install_stops_without_homebrew_node24(self) -> None:
        tool = {"id": "firebase", "testedVersion": "15.24.0", "install": {"macos": "npm install --global firebase-tools@15.24.0"}}
        with mock.patch.object(kit, "node24_npm", return_value=None):
            self.assertIsNone(kit.install_argv(tool))

    def test_preflight_valid_read_only_preserves_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            fixture = ROOT / "tests/fixtures/status-valid.json"
            (target / "STATUS.json").write_bytes(fixture.read_bytes())
            before = (target / "STATUS.json").read_bytes()
            human = cli("preflight", "--target", tmp, "--platform", "ios", "--language", "en")
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertIn("I am only checking; nothing will be changed.", human.stdout)
            self.assertIn("2 recorded steps", human.stdout)
            self.assertIn("there is nothing waiting for action", human.stdout)
            self.assertIn("first in-app purchase step has not been recorded", human.stdout)
            structured = cli("preflight", "--target", tmp, "--platform", "ios", "--json")
            self.assertEqual(structured.returncode, 0, structured.stderr)
            report = json.loads(structured.stdout)
            self.assertTrue(report["valid"])
            self.assertTrue(report["readOnly"])
            self.assertEqual(report["validationErrors"], [])
            self.assertEqual(report["counts"], {"actions": 2, "evidence": 3, "gates": 0, "gatesPending": 0, "gatesApproved": 0, "gatesConsumed": 0, "gatesRevoked": 0})
            self.assertEqual(report["next"]["state"], "no_pending_action")
            self.assertEqual(report["iapVersion"]["status"], "first_external_action_not_recorded")
            self.assertEqual(before, (target / "STATUS.json").read_bytes())

    def test_preflight_missing_and_invalid_status_are_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = cli("preflight", "--target", tmp, "--json")
            self.assertEqual(missing.returncode, 2)
            self.assertFalse(json.loads(missing.stdout)["valid"])
            self.assertIn("missing STATUS.json", missing.stdout)
            self.assertFalse((Path(tmp) / "STATUS.json").exists())
            (Path(tmp) / "STATUS.json").write_text("{not json", encoding="utf-8")
            malformed = cli("preflight", "--target", tmp, "--json")
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("invalid STATUS.json", malformed.stdout)
            (Path(tmp) / "STATUS.json").write_text("[]", encoding="utf-8")
            shape = cli("preflight", "--target", tmp, "--json")
            self.assertEqual(shape.returncode, 2)
            self.assertIn("status top-level shape", shape.stdout)

    def test_preflight_semantic_invalid_status_never_tracebacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            data = read_status_fixture()
            data["actions"].append({"intent": "timed out vendor mutation", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "outcome_unknown", "gateId": None, "verificationQuery": "", "evidenceIds": []})
            (target / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            result = cli("preflight", "--target", tmp, "--platform", "ios", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertTrue(report["validationErrors"])
            self.assertEqual(report["next"], {"state": "no_pending_action", "actionIds": [], "gateIds": [], "detail": "no usable STATUS model"})
            human = cli("preflight", "--target", tmp, "--platform", "ios", "--language", "tr")
            self.assertEqual(human.returncode, 2)
            self.assertNotIn("Traceback", human.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            data = read_status_fixture()
            del data["targets"]["android"]
            (Path(tmp) / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            result = cli("preflight", "--target", tmp, "--platform", "ios", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(json.loads(result.stdout)["targets"], {"ios": {"state": "LOCALLY_VERIFIED"}, "android": {"state": None}})

    def test_preflight_missing_invalid_status_human_messages_localized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_tr = cli("preflight", "--target", tmp, "--language", "tr")
            missing_en = cli("preflight", "--target", tmp, "--language", "en")
            self.assertEqual(missing_tr.returncode, 2)
            self.assertIn("uygulama durum dosyası bulunamadı", missing_tr.stdout)
            self.assertNotIn("status file", missing_tr.stdout)
            self.assertEqual(missing_en.returncode, 2)
            self.assertIn("the app status file is missing", missing_en.stdout)
            (Path(tmp) / "STATUS.json").write_text("{bad", encoding="utf-8")
            invalid_tr = cli("preflight", "--target", tmp, "--language", "tr")
            invalid_en = cli("preflight", "--target", tmp, "--language", "en")
            self.assertEqual(invalid_tr.returncode, 2)
            self.assertIn("uygulama durum dosyası okunamadı", invalid_tr.stdout)
            self.assertNotIn("status file is not readable", invalid_tr.stdout)
            self.assertEqual(invalid_en.returncode, 2)
            self.assertIn("the app status file is not readable", invalid_en.stdout)

    def test_preflight_outcome_unknown_wins_over_pending_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            data = read_status_fixture()
            data["gates"].append({"id": "gate-pending", "class": "approval_required", "action": "exact vendor action", "target": "ios", "state": "pending", "approvedAt": None})
            data["actions"].append({"id": "act-pending", "intent": "planned vendor mutation", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "planned", "gateId": "gate-pending", "verificationQuery": "", "evidenceIds": []})
            data["gates"].append({"id": "gate-unknown", "class": "approval_required", "action": "exact vendor action", "target": "ios", "state": "consumed", "approvedAt": "2026-01-04T00:00:00Z"})
            data["actions"].append({"id": "act-unknown", "intent": "vendor mutation timed out", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "outcome_unknown", "gateId": "gate-unknown", "verificationQuery": "asc app read-back", "evidenceIds": []})
            (target / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validator.status_errors(data), [])
            report = json.loads(cli("preflight", "--target", tmp, "--platform", "ios", "--json").stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["next"]["state"], "read_back_before_retry")
            self.assertIn("act-unknown", report["next"]["actionIds"])

    def test_attempted_external_mutation_requires_verification_query(self) -> None:
        data = read_status_fixture()
        data["gates"].append({"id": "gate-attempt", "class": "approval_required", "action": "exact vendor action", "target": "ios", "state": "consumed", "approvedAt": "2026-01-04T00:00:00Z"})
        data["actions"].append({"id": "act-attempt", "intent": "timed out vendor mutation", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "outcome_unknown", "gateId": "gate-attempt", "verificationQuery": "", "evidenceIds": []})
        self.assertIn("attempted external mutation lacks verification query: act-attempt", validator.status_errors(data))

    def test_preflight_pending_gate_and_resume_priorities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = read_status_fixture()
            data["gates"].append({"id": "gate-pending", "class": "approval_required", "action": "exact vendor action", "target": "ios", "state": "pending", "approvedAt": None})
            data["actions"].append({"id": "act-pending", "intent": "approved vendor mutation", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "approved", "gateId": "gate-pending", "verificationQuery": "", "evidenceIds": []})
            (Path(tmp) / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validator.status_errors(data), [])
            report = json.loads(cli("preflight", "--target", tmp, "--platform", "ios", "--json").stdout)
            self.assertEqual(report["next"]["state"], "approval_required")
            self.assertIn("gate-pending", report["next"]["gateIds"])
            self.assertIn("act-pending", report["next"]["actionIds"])
        with tempfile.TemporaryDirectory() as tmp:
            data = read_status_fixture()
            data["actions"].append({"id": "act-resume", "intent": "resume local build", "target": "ios", "tool": "Flutter", "classification": "local_mutation", "status": "started", "gateId": None, "verificationQuery": "read back build log", "evidenceIds": ["ev-build"]})
            (Path(tmp) / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validator.status_errors(data), [])
            report = json.loads(cli("preflight", "--target", tmp, "--platform", "ios", "--json").stdout)
            self.assertEqual(report["next"]["state"], "resume_action")
            self.assertIn("act-resume", report["next"]["actionIds"])

    def test_preflight_verified_iap_action_never_proposes_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            data = read_status_fixture()
            data["evidence"].append({"id": "ev-iap", "claim": "IAP version read back", "source": "store_readback", "timestamp": "2026-01-04T00:00:00Z", "toolVersion": "asc test", "sanitizedResult": "version 1.0 created", "limitations": ""})
            data["gates"].append({"id": "gate-asc-iap-version-create", "class": "approval_required", "action": "create first IAP version", "target": "ios", "state": "consumed", "approvedAt": "2026-01-04T00:00:00Z"})
            data["actions"].append({"id": "act-asc-iap-version-create", "intent": "create first IAP version", "target": "ios", "tool": "asc", "classification": "external_mutation", "status": "verified", "gateId": "gate-asc-iap-version-create", "verificationQuery": "asc iap versions list", "evidenceIds": ["ev-iap"]})
            (target / "STATUS.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(validator.status_errors(data), [])
            report = json.loads(cli("preflight", "--target", tmp, "--platform", "ios", "--json").stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["iapVersion"]["status"], "already_verified")
            self.assertEqual(report["next"]["state"], "no_pending_action")
            self.assertNotIn("act-asc-iap-version-create", report["next"]["actionIds"])

    def test_onboard_show_is_read_only_resumable_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shown = cli("onboard", "--target", tmp, "--show", "--language", "en")
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertIn("Check only: this does not approve or change anything.", shown.stdout)
            self.assertIn("Starting information: 0/38 completed.", shown.stdout)
            self.assertFalse((Path(tmp) / kit.ONBOARDING).exists())
        with tempfile.TemporaryDirectory() as tmp:
            saved = cli("onboard", "--target", tmp, "--set", "tooling.harness=pi", "--language", "en")
            self.assertEqual(saved.returncode, 0, saved.stderr)
            before = (Path(tmp) / kit.ONBOARDING).read_bytes()
            shown = cli("onboard", "--target", tmp, "--show", "--json")
            self.assertEqual(shown.returncode, 0, shown.stderr)
            summary = json.loads(shown.stdout)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["next"], "project.platforms")
            self.assertFalse(summary["planAcknowledged"])
            self.assertIn("schemaVersion", summary)
            self.assertEqual(before, (Path(tmp) / kit.ONBOARDING).read_bytes())

    def test_language_flag_env_precedence_and_auto_resolution(self) -> None:
        base = argparse.Namespace()
        with mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8"}, clear=True):
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "en")
            base.language = None
            self.assertEqual(kit.resolve_language(base), "en")
        with mock.patch.dict(os.environ, {"MOBILE_APP_SHIP_LANGUAGE": "tr", "LANG": "tr_TR.UTF-8"}, clear=True):
            base.language = "en"
            self.assertEqual(kit.resolve_language(base), "en")
            base.language = "tr"
            self.assertEqual(kit.resolve_language(base), "tr")
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "tr")
        with mock.patch.dict(os.environ, {"LC_ALL": "tr_TR.UTF-8", "LANG": "en_US.UTF-8"}, clear=True):
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "tr")
        with mock.patch.dict(os.environ, {"LC_ALL": "C", "LANG": "tr_TR.UTF-8"}, clear=True):
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "en")
        with mock.patch.dict(os.environ, {"LANG": "tr_TR.UTF-8"}, clear=True):
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "tr")
        with mock.patch.dict(os.environ, {"LANG": "fr_FR.UTF-8"}, clear=True):
            base.language = "auto"
            self.assertEqual(kit.resolve_language(base), "en")
        # Backward compatible with Namespace objects that carry no language attribute.
        bare = argparse.Namespace()
        with mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8"}, clear=True):
            self.assertEqual(kit.resolve_language(bare), "en")

    def test_preflight_human_output_localized_and_json_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "STATUS.json").write_bytes((ROOT / "tests/fixtures/status-valid.json").read_bytes())
            tr_run = cli("preflight", "--target", tmp, "--platform", "ios", "--language", "tr")
            en_run = cli("preflight", "--target", tmp, "--platform", "ios", "--language", "en")
            self.assertEqual(tr_run.returncode, en_run.returncode)
            self.assertIn("Sadece kontrol yapıyorum; hiçbir şeyi değiştirmeyeceğim.", tr_run.stdout)
            self.assertIn("2 işlem kaydı", tr_run.stdout)
            self.assertIn("şu anda bekleyen bir iş yok", tr_run.stdout)
            self.assertIn("İlk uygulama içi satın alma adımı henüz kaydedilmedi", tr_run.stdout)
            self.assertIn("I am only checking; nothing will be changed.", en_run.stdout)
            self.assertIn("2 recorded steps", en_run.stdout)
            self.assertIn("there is nothing waiting for action", en_run.stdout)
            for run in (tr_run, en_run):
                self.assertNotRegex(run.stdout, r"\b(?:act|gate|ev)-[A-Za-z0-9_-]+")
                self.assertNotIn("no_pending_action", run.stdout)
                self.assertNotIn("first_external_action_not_recorded", run.stdout)
            tr_json = cli("preflight", "--target", tmp, "--platform", "ios", "--json", "--language", "tr")
            en_json = cli("preflight", "--target", tmp, "--platform", "ios", "--json", "--language", "en")
            self.assertEqual(tr_json.returncode, en_json.returncode)
            self.assertEqual(tr_json.stdout, en_json.stdout)
            self.assertIn("no_pending_action", tr_json.stdout)
            self.assertIn("first_external_action_not_recorded", tr_json.stdout)
            self.assertEqual(json.loads(tr_json.stdout)["next"]["state"], "no_pending_action")

    def test_onboard_show_and_summary_localized_without_persisting_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            saved = cli("onboard", "--target", tmp, "--set", "tooling.harness=pi", "--language", "tr")
            self.assertEqual(saved.returncode, 0, saved.stderr)
            self.assertIn("Başlangıç bilgileri: 1/38 tamamlandı.", saved.stdout)
            self.assertIn("Sıradaki bilgi: Yayın platformları", saved.stdout)
            data = json.loads((Path(tmp) / kit.ONBOARDING).read_text(encoding="utf-8"))
            self.assertNotIn("language", data)
            tr_show = cli("onboard", "--target", tmp, "--show", "--language", "tr")
            en_show = cli("onboard", "--target", tmp, "--show", "--language", "en")
            self.assertEqual(tr_show.returncode, en_show.returncode)
            self.assertIn("Sadece kontrol: hiçbir şeyi onaylamaz veya değiştirmez.", tr_show.stdout)
            self.assertIn("Başlangıç bilgileri: 1/38 tamamlandı.", tr_show.stdout)
            self.assertIn("Check only: this does not approve or change anything.", en_show.stdout)
            self.assertIn("Starting information: 1/38 completed.", en_show.stdout)
            tr_json = cli("onboard", "--target", tmp, "--show", "--json", "--language", "tr")
            en_json = cli("onboard", "--target", tmp, "--show", "--json", "--language", "en")
            self.assertEqual(tr_json.stdout, en_json.stdout)
            self.assertEqual(json.loads(tr_json.stdout)["next"], "project.platforms")

    def test_onboard_json_identical_across_languages_and_no_language_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_auth_progress(tmp)
            tr_run = cli(*complete_onboarding_command(tmp), "--acknowledge-plan", "--json", "--language", "tr")
            en_run = cli(*complete_onboarding_command(tmp), "--acknowledge-plan", "--json", "--language", "en")
            self.assertEqual(tr_run.returncode, en_run.returncode)
            self.assertEqual(tr_run.stdout, en_run.stdout)
            self.assertTrue(json.loads(tr_run.stdout)["planAcknowledged"])
            persisted = json.loads((Path(tmp) / kit.ONBOARDING).read_text(encoding="utf-8"))
            self.assertNotIn("language", persisted)

    def test_language_env_var_drives_auto_and_flag_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"MOBILE_APP_SHIP_LANGUAGE": "tr", "LANG": "en_US.UTF-8"}
            turkish = cli("preflight", "--target", tmp, "--platform", "ios", env_extra=env)
            english = cli("preflight", "--target", tmp, "--platform", "ios", "--language", "en", env_extra=env)
            self.assertIn("Sadece kontrol yapıyorum", turkish.stdout)
            self.assertIn("I am only checking", english.stdout)
            self.assertEqual(turkish.returncode, english.returncode)

    def test_onboard_web_language_initialization_and_persistence_wiring(self) -> None:
        html = (ROOT / "skills/mobile-app-ship/assets/onboarding.html").read_text(encoding="utf-8")
        for token in (
            "navigator.languages",
            "localStorage",
            "mobile-app-ship-lang",
            "savedLanguage()||browserLanguage()",
            "rememberLanguage(lang)",
            "initialLanguage()",
            'data-lang="en"',
            'data-lang="tr"',
            "text('langLabel')",
            "text('lang'+button.dataset.lang.toUpperCase())",
        ):
            self.assertIn(token, html)
        self.assertIn("langLabel:'Language'", html)
        self.assertIn("langLabel:'Dil'", html)

    def test_structured_status_writer_and_coverage_are_safe(self) -> None:
        structured = json.loads((ROOT / "tests/fixtures/status-structured.json").read_text(encoding="utf-8"))
        self.assertEqual(validator.status_errors(structured), [])
        for mutate in (lambda data: data["gates"][0].pop("scope"), lambda data: data["gates"][0]["scope"].update(resource="asc:other"), lambda data: data["gates"][0].update(state="approved", approvedAt="2026-01-02T00:00:00Z")):
            invalid = copy.deepcopy(structured); mutate(invalid)
            self.assertTrue(validator.status_errors(invalid))
        invalid_resource = copy.deepcopy(structured)
        invalid_resource["actions"][0]["scope"]["resource"] = "unqualified-resource"
        invalid_resource["gates"][0]["scope"]["resource"] = "unqualified-resource"
        self.assertIn("action scope: act-write", validator.status_errors(invalid_resource))
        invalid_order = copy.deepcopy(structured)
        for item in (invalid_order["actions"][0]["scope"], invalid_order["gates"][0]["scope"]):
            item["sideEffects"] = ["z side effect", "a side effect"]
        self.assertIn("action scope: act-write", validator.status_errors(invalid_order))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp); path = target / "STATUS.json"; path.write_text(json.dumps(structured), encoding="utf-8")
            before = path.read_bytes(); digest = __import__("hashlib").sha256(before).hexdigest()
            coverage_before = cli("coverage", "--target", tmp, "--platform", "ios", "--json")
            self.assertEqual(coverage_before.returncode, 0, coverage_before.stderr)
            self.assertEqual(json.loads(coverage_before.stdout)["scopeBinding"], {"legacy": 0, "structured": 1, "unbound": 0})
            self.assertEqual(before, path.read_bytes())
            approved = copy.deepcopy(structured); approved["gates"][0].update(state="approved", approvedAt="2026-01-02T00:00:00Z"); approved["actions"][0]["status"] = "approved"
            transaction = {"append": {"actions": [], "gates": [], "evidence": []}, "update": {"actions": approved["actions"], "gates": approved["gates"], "evidence": []}}
            tx = target / "tx.json"; tx.write_text(json.dumps(transaction), encoding="utf-8")
            result = cli("status-write", "--target", tmp, "--expect-sha256", digest, "--transaction", str(tx), "--record-user-approval", "gate-write")
            self.assertEqual(result.returncode, 0, result.stderr); self.assertIn("no vendor action executed", result.stdout)
            started = json.loads(path.read_text()); started["gates"][0]["state"] = "consumed"; started["actions"][0]["status"] = "started"
            transaction["update"] = {"actions": started["actions"], "gates": started["gates"], "evidence": []}; tx.write_text(json.dumps(transaction), encoding="utf-8")
            digest = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", digest, "--transaction", str(tx), "--consume-gate", "gate-write").returncode, 0)
            stable = path.read_bytes()
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", "0" * 64, "--transaction", str(tx)).returncode, 2)
            self.assertEqual(stable, path.read_bytes())
            transaction["append"]["evidence"] = [{"id": "ev-secret", "claim": "token=bad", "source": "file", "timestamp": "2026-01-02T00:00:00Z", "toolVersion": None, "sanitizedResult": "x", "limitations": ""}]; tx.write_text(json.dumps(transaction), encoding="utf-8")
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", __import__("hashlib").sha256(stable).hexdigest(), "--transaction", str(tx)).returncode, 2)
            self.assertEqual(stable, path.read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp); (target / "real").write_text("{}", encoding="utf-8"); (target / "STATUS.json").symlink_to(target / "real")
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", "0" * 64, "--transaction", "-").returncode, 2)

    def test_approved_legacy_scope_requires_fresh_approval_and_can_consume(self) -> None:
        structured = json.loads((ROOT / "tests/fixtures/status-structured.json").read_text(encoding="utf-8"))
        legacy = copy.deepcopy(structured)
        legacy["schemaVersion"] = "1.0.0"
        legacy["actions"][0]["status"] = "approved"
        legacy["actions"][0].pop("scope")
        legacy["gates"][0]["state"] = "approved"
        legacy["gates"][0]["approvedAt"] = "2026-01-01T00:00:00Z"
        legacy["gates"][0].pop("scope")
        self.assertEqual(validator.status_errors(legacy), [])
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp); path = target / "STATUS.json"; path.write_text(json.dumps(legacy), encoding="utf-8")
            old = path.read_bytes(); old_sha = __import__("hashlib").sha256(old).hexdigest()
            bad = copy.deepcopy(legacy)
            bad["actions"][0]["scope"] = structured["actions"][0]["scope"]
            bad["actions"][0]["verificationQuery"] = structured["actions"][0]["scope"]["verificationQuery"]
            bad["gates"][0]["scope"] = structured["gates"][0]["scope"]
            bad_tx = {"append": {"actions": [], "gates": [], "evidence": []}, "update": {"actions": bad["actions"], "gates": bad["gates"], "evidence": []}}
            bad_file = target / "bad.json"; bad_file.write_text(json.dumps(bad_tx), encoding="utf-8")
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", old_sha, "--transaction", str(bad_file), "--record-user-approval", "gate-write").returncode, 2)
            self.assertEqual(old, path.read_bytes())
            backdated_tx = copy.deepcopy(bad_tx); backdated_tx["update"]["gates"][0]["approvedAt"] = "2025-12-31T23:59:59Z"
            bad_file.write_text(json.dumps(backdated_tx), encoding="utf-8")
            self.assertEqual(cli("status-write", "--target", tmp, "--expect-sha256", old_sha, "--transaction", str(bad_file), "--record-user-approval", "gate-write").returncode, 2)
            self.assertEqual(old, path.read_bytes())

            bound = copy.deepcopy(bad)
            bound["gates"][0]["approvedAt"] = "2026-01-02T00:00:00Z"
            tx = target / "bind.json"; tx.write_text(json.dumps(bad_tx), encoding="utf-8")
            result = cli("status-write", "--target", tmp, "--expect-sha256", old_sha, "--transaction", str(tx), "--record-user-approval", "gate-write")
            self.assertEqual(result.returncode, 2)
            # The transaction must contain the fresh approval timestamp, not the stale candidate above.
            bind_tx = copy.deepcopy(bad_tx); bind_tx["update"]["gates"] = bound["gates"]
            tx.write_text(json.dumps(bind_tx), encoding="utf-8")
            result = cli("status-write", "--target", tmp, "--expect-sha256", old_sha, "--transaction", str(tx), "--record-user-approval", "gate-write")
            self.assertEqual(result.returncode, 0, result.stderr)
            current = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(current["schemaVersion"], "1.1.0")
            self.assertEqual(validator.status_errors(current), [])

            started = copy.deepcopy(current); started["actions"][0]["status"] = "started"; started["gates"][0]["state"] = "consumed"
            tx.write_text(json.dumps({"append": {"actions": [], "gates": [], "evidence": []}, "update": {"actions": started["actions"], "gates": started["gates"], "evidence": []}}), encoding="utf-8")
            result = cli("status-write", "--target", tmp, "--expect-sha256", __import__("hashlib").sha256(path.read_bytes()).hexdigest(), "--transaction", str(tx), "--consume-gate", "gate-write")
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(kit.fcntl is not None, "directory flock is unavailable")
    def test_status_writer_lock_has_no_target_artifact_and_serializes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            status = target / "STATUS.json"
            status.write_text(json.dumps(json.loads((ROOT / "tests/fixtures/status-valid.json").read_text(encoding="utf-8"))), encoding="utf-8")
            marker = target / "child-acquired"
            lock_script = """
import importlib.util
import sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('toolkit', sys.argv[3])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.status_write_lock(Path(sys.argv[1])):
    Path(sys.argv[2]).write_text('acquired', encoding='utf-8')
"""
            env = os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"] = "1"
            with kit.status_write_lock(status):
                child = subprocess.Popen([sys.executable, "-c", lock_script, str(status), str(marker), str(TOOLKIT)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(0.15)
                self.assertFalse(marker.exists())
                self.assertIsNone(child.poll())
            stdout, stderr = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0, stderr or stdout)
            self.assertEqual(marker.read_text(encoding="utf-8"), "acquired")
            self.assertFalse((target / ".STATUS.json.lock").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
