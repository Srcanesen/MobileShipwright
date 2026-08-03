#!/usr/bin/env python3
"""Offline structural and semantic validation for the mobile-app-ship toolkit."""
from __future__ import annotations

import ast
import json
import re
import tomllib
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "mobile-app-ship"
ASSETS = SKILL / "assets"
REFS = SKILL / "references"
HARNESSES = {
    "claude-code": "templates/.mcp.json",
    "codex": "templates/config.toml",
    "cursor": "templates/mcp.json",
    "vscode": "templates/mcp.json",
    "windsurf": "templates/mcp_config.json",
    "gemini-cli": "templates/settings.json",
    "pi": None,
}
NATIVE_HARNESSES = {name for name, template in HARNESSES.items() if template}
REVENUECAT_ENDPOINT = "https://mcp.revenuecat.ai/mcp"
XCODEBUILD_COMMAND = "xcodebuildmcp mcp"
TOOL_IDS = {"node", "flutter", "firebase", "gcloud", "fastlane", "asc", "xcodebuildmcp", "adb", "sdkmanager", "java", "xcodebuild", "pod"}
STATES = [
    "SCOPED", "IMPLEMENTING", "LOCALLY_VERIFIED", "DISTRIBUTION_READY",
    "ARTIFACT_BUILT", "UPLOADED", "STORE_PROCESSED", "DISTRIBUTED",
    "DEVICE_VERIFIED", "SUBMISSION_READY", "SUBMITTED", "IN_REVIEW",
    "APPROVED", "RELEASE_AUTHORIZED", "RELEASED",
]
EXCEPTION_STATES = {"ACTION_REQUIRED", "WITHDRAWN", "SUPERSEDED", "ABANDONED"}
ALL_STATES = set(STATES) | EXCEPTION_STATES
ACTION_CLASSES = {"inspect", "local_mutation", "external_mutation"}
ACTION_STATUSES = {"planned", "approved", "started", "outcome_unknown", "verified", "failed", "canceled"}
EVIDENCE_SOURCES = {"tool", "file", "store_readback", "human_observation"}
GATE_CLASSES = {"approval_required", "manual_execution", "approval_and_manual"}
GATE_STATES = {"pending", "approved", "consumed", "revoked"}
TARGETS = {"ios", "android", "shared"}
LEGACY = "asc" + "elerate"
LOCAL_USER_PATH = "/" + "Users/"
EVIDENCE_SECRET_RE = re.compile(
    r"-----BEGIN|\b(?:sk_(?:live|test)_|AIza|gh[pousr]_|xox[baprs]-)[A-Za-z0-9_-]+|"
    r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b|"
    r"(?i:\b(?:password|passwd|token|access[_-]?token|refresh[_-]?token|id[_-]?token|oauth[_-]?token|api[_-]?key|client[_-]?secret|session[_-]?secret|private[_-]?key)\b\s*[\"']?\s*[:=]\s*(?:[\"']|\S))|"
    r"(?i:\bauthorization\b\s*[\"']?\s*[:=]\s*(?:bearer|basic)\b)"
)


def iso_time(value: object, nullable: bool = False) -> bool:
    if nullable and value is None:
        return True
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def exact_keys(value: object, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def python_constants(path: Path, names: set[str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names:
            values[node.targets[0].id] = ast.literal_eval(node.value)
    return values


def markdown_links(root: Path, errors: list[str]) -> None:
    link_re = re.compile(r"(?<!!)\[[^]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
    for path in root.rglob("*.md"):
        for raw in link_re.findall(path.read_text(encoding="utf-8")):
            target = unquote(raw.split("#", 1)[0])
            if target and "://" not in target and not target.startswith("mailto:") and not (path.parent / target).exists():
                errors.append(f"broken Markdown link: {path.relative_to(root)} -> {raw}")


def active_reference_authorization_errors(refs: Path) -> list[str]:
    forbidden = re.compile(r"(?i)\b(?:master scope|master approval|matching current master scopes)\b")
    return [f"active authorization alternative: {path.name}" for path in refs.glob("*.md") if forbidden.search(path.read_text(encoding="utf-8"))]


def scope_valid(scope: object) -> bool:
    if not exact_keys(scope, {"resource", "operation", "sideEffects", "verificationQuery"}):
        return False
    assert isinstance(scope, dict)
    text = lambda value: isinstance(value, str) and 1 <= len(value) <= 500 and "\n" not in value and "\r" not in value and not EVIDENCE_SECRET_RE.search(value)
    side_effects = scope["sideEffects"]
    return (text(scope["resource"]) and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*:[^\s\r\n]+", scope["resource"]))
            and text(scope["verificationQuery"])
            and isinstance(scope["operation"], str) and bool(re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", scope["operation"]))
            and isinstance(side_effects, list) and 1 <= len(side_effects) <= 20
            and all(text(item) for item in side_effects) and side_effects == sorted(set(side_effects)))


def status_errors(data: object) -> list[str]:
    errors: list[str] = []
    top = {"schemaVersion", "toolkitVersion", "app", "targets", "actions", "evidence", "gates"}
    if not exact_keys(data, top):
        return ["status top-level shape"]
    assert isinstance(data, dict)
    version = data["schemaVersion"]
    if version not in {"1.0.0", "1.1.0"} or not isinstance(data["toolkitVersion"], str) or not data["toolkitVersion"]:
        errors.append("status versions")
    app = data["app"]
    if not exact_keys(app, {"name", "bundleId", "packageName"}) or not isinstance(app["name"], str) or not app["name"]:
        errors.append("app identity")
    elif any(value is not None and not isinstance(value, str) for value in (app["bundleId"], app["packageName"])):
        errors.append("target identifiers")

    evidence = data["evidence"]
    actions = data["actions"]
    gates = data["gates"]
    if not isinstance(evidence, list) or not isinstance(actions, list) or not isinstance(gates, list):
        return errors + ["actions/evidence/gates arrays"]

    evidence_by_id: dict[str, dict] = {}
    for item in evidence:
        keys = {"id", "claim", "source", "timestamp", "toolVersion", "sanitizedResult", "limitations"}
        if not exact_keys(item, keys):
            errors.append("evidence shape")
            continue
        if not all(isinstance(item[k], str) and item[k] for k in ("id", "claim", "sanitizedResult")):
            errors.append("evidence required values")
            continue
        if not isinstance(item["source"], str) or item["source"] not in EVIDENCE_SOURCES or not iso_time(item["timestamp"]):
            errors.append(f"evidence source/time: {item.get('id')}")
        if item["toolVersion"] is not None and not isinstance(item["toolVersion"], str):
            errors.append(f"evidence toolVersion: {item.get('id')}")
        if not isinstance(item["limitations"], str):
            errors.append(f"evidence limitations: {item.get('id')}")
        elif any(EVIDENCE_SECRET_RE.search(item[field]) for field in ("claim", "sanitizedResult", "limitations")):
            errors.append(f"evidence contains possible secret: {item.get('id')}")
        if item["id"] in evidence_by_id:
            errors.append(f"duplicate evidence id: {item['id']}")
        evidence_by_id[item["id"]] = item

    gate_by_id: dict[str, dict] = {}
    consumed_gate_ids: set[str] = set()
    for gate in gates:
        keys = {"id", "class", "action", "target", "state", "approvedAt"}
        if version == "1.1.0" and isinstance(gate, dict) and "scope" in gate:
            keys.add("scope")
        if not exact_keys(gate, keys):
            errors.append("gate shape")
            continue
        if not isinstance(gate["id"], str) or not gate["id"] or not isinstance(gate["action"], str) or not gate["action"]:
            errors.append("gate required values")
            continue
        if (not isinstance(gate["class"], str) or gate["class"] not in GATE_CLASSES
                or not isinstance(gate["target"], str) or gate["target"] not in TARGETS
                or not isinstance(gate["state"], str) or gate["state"] not in GATE_STATES):
            errors.append(f"gate enum: {gate.get('id')}")
        if isinstance(gate["state"], str) and gate["state"] in {"approved", "consumed"} and not iso_time(gate["approvedAt"]):
            errors.append(f"approved gate lacks timestamp: {gate.get('id')}")
        if isinstance(gate["state"], str) and gate["state"] in {"pending", "revoked"} and not iso_time(gate["approvedAt"], nullable=True):
            errors.append(f"gate timestamp: {gate.get('id')}")
        if "scope" in gate and not scope_valid(gate["scope"]):
            errors.append(f"gate scope: {gate.get('id')}")
        if gate["id"] in gate_by_id:
            errors.append(f"duplicate gate id: {gate['id']}")
        gate_by_id[gate["id"]] = gate

    action_by_id: dict[str, dict] = {}
    for action in actions:
        keys = {"id", "intent", "target", "tool", "classification", "status", "gateId", "verificationQuery", "evidenceIds"}
        if version == "1.1.0" and isinstance(action, dict) and "scope" in action:
            keys.add("scope")
        if not exact_keys(action, keys):
            errors.append("action shape")
            continue
        if not all(isinstance(action[k], str) and action[k] for k in ("id", "intent", "tool")):
            errors.append("action required values")
            continue
        if (not isinstance(action["target"], str) or action["target"] not in TARGETS
                or not isinstance(action["classification"], str) or action["classification"] not in ACTION_CLASSES
                or not isinstance(action["status"], str) or action["status"] not in ACTION_STATUSES):
            errors.append(f"action enum: {action.get('id')}")
        if action["gateId"] is not None and not isinstance(action["gateId"], str):
            errors.append(f"action gateId: {action.get('id')}")
        if not isinstance(action["verificationQuery"], str) or not isinstance(action["evidenceIds"], list):
            errors.append(f"action verification/evidence shape: {action.get('id')}")
            continue
        if not all(isinstance(eid, str) for eid in action["evidenceIds"]):
            errors.append(f"action evidence reference: {action.get('id')}")
        elif any(eid not in evidence_by_id for eid in action["evidenceIds"]):
            errors.append(f"action evidence reference: {action.get('id')}")
        if all(isinstance(eid, str) for eid in action["evidenceIds"]) and len(action["evidenceIds"]) != len(set(action["evidenceIds"])):
            errors.append(f"duplicate action evidenceIds: {action.get('id')}")
        if "scope" in action and not scope_valid(action["scope"]):
            errors.append(f"action scope: {action.get('id')}")
        attempted_external = action["classification"] == "external_mutation" and action["status"] in {"started", "outcome_unknown", "verified", "failed"}
        if attempted_external:
            if not action["verificationQuery"].strip():
                errors.append(f"attempted external mutation lacks verification query: {action.get('id')}")
            gate = gate_by_id.get(action["gateId"]) if isinstance(action["gateId"], str) else None
            if not gate or gate["state"] != "consumed" or not iso_time(gate["approvedAt"]):
                errors.append(f"attempted external mutation lacks consumed gate: {action.get('id')}")
            elif gate["target"] != action["target"]:
                errors.append(f"external mutation gate target mismatch: {action.get('id')}")
            elif gate["id"] in consumed_gate_ids:
                errors.append(f"consumed gate reused: {gate['id']}")
            else:
                consumed_gate_ids.add(gate["id"])
        if action["classification"] == "external_mutation" and action["status"] == "failed" and not action["evidenceIds"]:
            errors.append(f"failed external mutation lacks sanitized evidence: {action.get('id')}")
        if action["classification"] == "external_mutation" and action["status"] == "verified":
            if not action["verificationQuery"] or not action["evidenceIds"]:
                errors.append(f"verified external mutation lacks query/evidence: {action.get('id')}")
            elif not any(evidence_by_id[eid]["source"] in {"store_readback", "human_observation"} for eid in action["evidenceIds"] if isinstance(eid, str) and eid in evidence_by_id):
                errors.append(f"verified external mutation lacks read-back evidence: {action.get('id')}")
        if action["id"] in action_by_id:
            errors.append(f"duplicate action id: {action['id']}")
        action_by_id[action["id"]] = action

    links: dict[str, list[dict]] = {}
    for action in action_by_id.values():
        if action.get("classification") == "external_mutation" and isinstance(action.get("gateId"), str):
            links.setdefault(action["gateId"], []).append(action)
    for gate_id, linked in links.items():
        if len(linked) > 1:
            errors.append(f"gate linkage reused: {gate_id}")
        gate = gate_by_id.get(gate_id)
        if not gate:
            if linked[0].get("scope") is not None:
                errors.append(f"one-sided scope binding: {linked[0].get('id')}")
            continue
        action = linked[0]
        action_scope, gate_scope = action.get("scope"), gate.get("scope")
        if (action_scope is None) != (gate_scope is None):
            errors.append(f"one-sided scope binding: {action.get('id')}")
        elif action_scope is not None and gate_scope is not None:
            if action_scope != gate_scope:
                errors.append(f"scope binding mismatch: {action.get('id')}")
            if action.get("verificationQuery") != action_scope.get("verificationQuery"):
                errors.append(f"scope verification query mismatch: {action.get('id')}")
            if action.get("target") != gate.get("target"):
                errors.append(f"scope target mismatch: {action.get('id')}")
            expected = {"planned": "pending", "approved": "approved", "started": "consumed", "outcome_unknown": "consumed", "verified": "consumed", "failed": "consumed", "canceled": "revoked"}.get(action.get("status"))
            if expected and gate.get("state") != expected:
                errors.append(f"structured gate state mismatch: {action.get('id')}")
            if expected in {"approved", "consumed"} and not iso_time(gate.get("approvedAt")):
                errors.append(f"structured gate timestamp missing: {action.get('id')}")

    targets = data["targets"]
    if not exact_keys(targets, {"ios", "android"}):
        return errors + ["independent target shape"]
    for target_name in ("ios", "android"):
        target = targets[target_name]
        if not exact_keys(target, {"state", "blocker", "history"}) or not isinstance(target["state"], str) or target["state"] not in ALL_STATES:
            errors.append(f"target shape/state: {target_name}")
            continue
        blocker = target["blocker"]
        if blocker is not None:
            if (not exact_keys(blocker, {"id", "summary", "since", "gateId"})
                    or not isinstance(blocker["id"], str) or not blocker["id"]
                    or not isinstance(blocker["summary"], str) or not blocker["summary"]
                    or not iso_time(blocker["since"])):
                errors.append(f"blocker overlay: {target_name}")
            elif blocker["gateId"] is not None and (not isinstance(blocker["gateId"], str) or blocker["gateId"] not in gate_by_id):
                errors.append(f"blocker gate reference: {target_name}")
        history = target["history"]
        if not isinstance(history, list) or not history:
            errors.append(f"history missing: {target_name}")
            continue
        previous = None
        for event in history:
            if (not exact_keys(event, {"state", "at", "actionId", "evidenceIds"})
                    or not isinstance(event["state"], str) or event["state"] not in ALL_STATES
                    or not iso_time(event["at"])):
                errors.append(f"history event shape: {target_name}")
                continue
            state = event["state"]
            if previous in {"WITHDRAWN", "SUPERSEDED", "ABANDONED"}:
                errors.append(f"terminal lifecycle continued: {target_name} {previous}->{state}")
            elif previous in STATES and state in STATES and STATES.index(state) != STATES.index(previous) + 1:
                errors.append(f"illegal lifecycle jump: {target_name} {previous}->{state}")
            elif previous == "ACTION_REQUIRED" and state == "ACTION_REQUIRED":
                errors.append(f"duplicate ACTION_REQUIRED transition: {target_name}")
            previous = state
            if event["actionId"] is not None and (not isinstance(event["actionId"], str) or event["actionId"] not in action_by_id):
                errors.append(f"history action reference: {target_name}")
            if (not isinstance(event["evidenceIds"], list) or not event["evidenceIds"]
                    or not all(isinstance(eid, str) for eid in event["evidenceIds"])
                    or any(eid not in evidence_by_id for eid in event["evidenceIds"] if isinstance(eid, str))):
                errors.append(f"history evidence reference: {target_name}")
            if isinstance(event["evidenceIds"], list) and all(isinstance(eid, str) for eid in event["evidenceIds"]) and len(event["evidenceIds"]) != len(set(event["evidenceIds"])):
                errors.append(f"duplicate history evidenceIds: {target_name}")
        if not isinstance(history[-1], dict) or history[-1].get("state") != target["state"]:
            errors.append(f"history/current mismatch: {target_name}")
        if target["state"] == "RELEASED":
            states = [event.get("state") if isinstance(event, dict) else None for event in history]
            if len(states) < 2 or states[-2:] != ["RELEASE_AUTHORIZED", "RELEASED"]:
                errors.append(f"RELEASED lacks RELEASE_AUTHORIZED history: {target_name}")
            release_event = history[-1] if isinstance(history[-1], dict) else {}
            release_action_id = release_event.get("actionId")
            action = action_by_id.get(release_action_id) if isinstance(release_action_id, str) else None
            gate_id = action.get("gateId") if action else None
            gate = gate_by_id.get(gate_id) if isinstance(gate_id, str) else None
            release_evidence = [evidence_by_id[eid] for eid in release_event.get("evidenceIds", []) if isinstance(eid, str) and eid in evidence_by_id]
            if not action or action.get("classification") != "external_mutation" or action.get("status") != "verified":
                errors.append(f"RELEASED lacks verified release action: {target_name}")
            if not gate or gate.get("state") != "consumed" or not iso_time(gate.get("approvedAt")) or gate.get("target") != target_name:
                errors.append(f"RELEASED lacks consumed release gate: {target_name}")
            if not any(item["source"] in {"store_readback", "human_observation"} for item in release_evidence):
                errors.append(f"RELEASED lacks release evidence: {target_name}")
    return errors


def main() -> int:
    errors: list[str] = []
    required_root = {"AGENTS.md", "CLAUDE.md", "README.md", "PRODUCT.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md", "VERSION"}
    onboarding_schema_path = ASSETS / "onboarding.schema.json"
    onboarding_html_path = ASSETS / "onboarding.html"
    toolkit_path = ROOT / "scripts" / "toolkit.py"
    if not onboarding_html_path.is_file():
        errors.append("missing onboarding HTML")
    else:
        onboarding_html = onboarding_html_path.read_text(encoding="utf-8")
        if (
            re.search(r"https?://", onboarding_html)
            or "<script src=" in onboarding_html
            or re.search(r"[—–]", onboarding_html)
            or "data-lang=\"tr\"" not in onboarding_html
            or "/api/state" not in onboarding_html
            or "/api/save" not in onboarding_html
            or "--acknowledge-plan" not in onboarding_html
            or "not vendor approval" not in onboarding_html
            or "future intent only" not in onboarding_html
        ):
            errors.append("onboarding HTML local/bilingual/live-choice contract")
    if not onboarding_schema_path.is_file():
        errors.append("missing onboarding schema")
    else:
        try:
            onboarding_schema = json.loads(onboarding_schema_path.read_text(encoding="utf-8"))
            constants = python_constants(toolkit_path, {"PROGRESS", "ONBOARDING", "ONBOARDING_SCHEMA_VERSION", "AUTHORIZATION_SCOPES", "FIELD_DESCRIPTORS", "NONCANONICAL_APPLE_LOCALES"})
            toolkit_text = toolkit_path.read_text(encoding="utf-8")
            descriptors = constants.get("FIELD_DESCRIPTORS", {})
            properties = onboarding_schema.get("properties", {})
            decision_properties = properties.get("decisions", {}).get("properties", {})
            locale_exclusions = onboarding_schema.get("$defs", {}).get("locale", {}).get("not", {}).get("enum", [])
            price_pattern = onboarding_schema.get("$defs", {}).get("price", {}).get("properties", {}).get("amount", {}).get("pattern", "")
            acknowledgement_schema = properties.get("planAcknowledgement", {}).get("oneOf", [{}, {}])[1].get("properties", {})
            if (
                properties.get("schemaVersion", {}).get("const") != constants.get("ONBOARDING_SCHEMA_VERSION")
                or onboarding_schema.get("additionalProperties") is not False
                or properties.get("decisions", {}).get("additionalProperties") is not False
                or set(decision_properties) != set(descriptors)
                or len(descriptors) != 38
                or any(not isinstance(item, tuple) or len(item) != 4 or any(not isinstance(text, str) or len(text.split()) < (1 if index < 2 else 7) for index, text in enumerate(item)) for item in descriptors.values())
                or properties.get("approvalMode", {}).get("const") != "strict"
                or set(onboarding_schema.get("required", [])) != {"schemaVersion", "decisions", "approvalMode", "planAcknowledgement"}
                or set(acknowledgement_schema) != {"acknowledgedAt", "canonicalSha256"}
                or set(locale_exclusions) != set(constants.get("NONCANONICAL_APPLE_LOCALES", set()))
                or constants.get("PROGRESS") == constants.get("ONBOARDING")
                or not re.fullmatch(price_pattern, "0.99")
                or re.fullmatch(price_pattern, "0")
                or re.search(r"[—–]", toolkit_text)
                or any(token not in toolkit_text for token in ("Content-Security-Policy", "default-src 'none'", "X-Frame-Options", "Permissions-Policy", "--acknowledge-plan", "future_intent_only"))
            ):
                errors.append("onboarding schema/runtime/bilingual/security contract")
        except (OSError, SyntaxError, ValueError, json.JSONDecodeError, re.error) as exc:
            errors.append(f"invalid onboarding schema/runtime contract: {exc}")

    required_refs = {
        "workflow-lifecycle.md", "state-evidence.md", "human-gates.md", "failure-resume.md", "tool-contracts.md",
        "xcodebuildmcp.md", "asc-cli.md", "revenuecat-mcp.md", "setup-readiness.md", "flutter-firebase.md",
        "design-rules.md", "localization.md", "security-cost.md", "admin-panel.md", "ios-app-store.md",
        "siwa-gates.md", "store-submission.md", "pre-submission-review.md", "android-play.md",
        "quality-compliance.md", "stability-gate.md", "pitfalls.md", "revenuecat-implementation.md", "admob-implementation.md",
        "harness-onboarding.md", "field-tested-recoveries.md",
    }
    for name in required_root:
        if not (ROOT / name).is_file():
            errors.append(f"missing root file: {name}")
    for name in required_refs:
        if not (REFS / name).is_file():
            errors.append(f"missing canonical reference: {name}")
    errors.extend(active_reference_authorization_errors(REFS))

    skill_path = SKILL / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.S)
    if not frontmatter:
        errors.append("SKILL.md frontmatter missing")
    else:
        keys = [line.split(":", 1)[0] for line in frontmatter.group(1).splitlines() if ":" in line]
        if keys != ["name", "description"] or "name: mobile-app-ship" not in frontmatter.group(1):
            errors.append("SKILL.md frontmatter must contain only name and description")
    skill_ref_links = set(re.findall(r"\(references/([^)#]+\.md)(?:#[^)]*)?\)", skill_text))
    missing_routes = required_refs - skill_ref_links
    if missing_routes:
        errors.append("SKILL.md does not route canonical references: " + ", ".join(sorted(missing_routes)))
    if "harness-onboarding.md" not in skill_text:
        errors.append("SKILL.md does not route harness onboarding")

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    if "harness-onboarding.md" not in readme:
        errors.append("README does not route harness onboarding")
    if "onboard --target" not in readme or ".mobile-app-ship-decisions.json" not in readme:
        errors.append("README does not start with target-local onboarding")
    if "PRODUCT.md" not in readme:
        errors.append("README does not link PRODUCT.md")
    product_path = ROOT / "PRODUCT.md"
    if product_path.is_file():
        product = product_path.read_text(encoding="utf-8")
        product_tokens = ("Product Boundary", "Coverage Matrix", "Success Metrics", "high-risk mobile shipping workflow coordinator", "not a release/upload wrapper", "not an autonomous shipping system", "terminal_managed", "terminal_guided", "vendor_readback", "physical_review_wait", "no numeric score", "gate violations", "unknown retries", "rework incidents", "time-to-first-preflight", "release-cycle duration")
        if any(token not in product for token in product_tokens):
            errors.append("PRODUCT.md boundary/coverage/metrics contract")

    agent_entrypoints = {
        "AGENTS.md": ("skills/mobile-app-ship/SKILL.md", "onboard", "doctor", "bootstrap", "exact single-use approval", "Never store credentials"),
        "CLAUDE.md": ("AGENTS.md", "skills/mobile-app-ship/SKILL.md", "onboard", "doctor", "bootstrap", "exact single-use approval", "Never write credentials"),
    }
    for name, tokens in agent_entrypoints.items():
        path = ROOT / name
        if path.is_file() and any(token not in path.read_text(encoding="utf-8") for token in tokens):
            errors.append(f"{name} agent entry contract regression")

    legacy_paths = [ROOT / "SKILL.md", ROOT / "references"]
    if any(path.exists() for path in legacy_paths):
        errors.append("legacy root skill/reference remains")
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.name == ".DS_Store":
            continue
        if path.name in {".auto", "node_modules", "__pycache__"}:
            errors.append(f"forbidden local artifact: {path.relative_to(ROOT)}")
        elif path.is_file() and path.suffix in {".pyc", ".pyo", ".p8", ".pem", ".key"}:
            errors.append(f"forbidden artifact: {path.relative_to(ROOT)}")
    markdown_links(ROOT, errors)

    text_files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix in {".md", ".py", ".json", ".toml", ".yml", ".yaml", ""}]
    secret_patterns = [
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"\bsk_(?:live|test)_[A-Za-z0-9]{8,}", r"\bAIza[\w-]{20,}",
        r'(?i)(api[_-]?key|client[_-]?secret|private[_-]?key)\s*[:=]\s*["\'][A-Za-z0-9_\-]{16,}',
    ]
    for path in text_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if LEGACY in text.lower():
            errors.append(f"legacy CLI reference: {path.relative_to(ROOT)}")
        if LOCAL_USER_PATH in text or re.search(r"[A-Za-z]:\\\\Users\\\\", text):
            errors.append(f"absolute local path: {path.relative_to(ROOT)}")
        if any(re.search(pattern, text) for pattern in secret_patterns):
            errors.append(f"possible secret: {path.relative_to(ROOT)}")

    for path in ROOT.rglob("*.json"):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON: {path.relative_to(ROOT)} ({exc})")

    for name, template in HARNESSES.items():
        harness = ROOT / "harnesses" / name
        readme_path = harness / "README.md"
        if not readme_path.is_file():
            errors.append(f"missing harness README: {name}")
            continue
        harness_readme = readme_path.read_text(encoding="utf-8")
        if "inactive" not in harness_readme.lower() or "approval" not in harness_readme.lower():
            errors.append(f"harness README lacks inactive/approval boundary: {name}")
        if name == "pi":
            pi_readme_lower = harness_readme.lower()
            pi_tokens = ("no native mcp", "pi-mcp-adapter", "user-global", "~/.pi/agent/mcp.json", "lifecycle", "auth", "directtools", "read-only", "do not run `pi-mcp-adapter init`")
            if any(token not in pi_readme_lower for token in pi_tokens):
                errors.append("Pi adapter boundary/fallback contract")
            template_path = harness / "templates" / "mcp.json"
            asset_path = ASSETS / "revenuecat.mcp.json"
            if not template_path.is_file() or not asset_path.is_file():
                errors.append("Pi RevenueCat template/asset missing")
            else:
                try:
                    pi_template_text = template_path.read_text(encoding="utf-8")
                    template = json.loads(pi_template_text)
                    entry = template.get("mcpServers", {}).get("revenuecat")
                    if (not isinstance(entry, dict)
                            or entry.get("url") != REVENUECAT_ENDPOINT
                            or entry.get("lifecycle") != "lazy"
                            or entry.get("auth") != "oauth"
                            or entry.get("directTools") is not False
                            or "npx" in pi_template_text
                            or re.search(r"(?i)[\"']?(?:api[_-]?key|token|client[_-]?secret|private[_-]?key|password)[\"']?\s*[:=]", pi_template_text)
                            or template_path.read_bytes() != asset_path.read_bytes()):
                        errors.append("Pi RevenueCat template contract")
                except (OSError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid Pi RevenueCat template: {exc}")
            continue
        assert template is not None
        template_path = harness / template
        if not template_path.is_file():
            errors.append(f"missing harness template: {name}")
            continue
        template_text = template_path.read_text(encoding="utf-8")
        if REVENUECAT_ENDPOINT not in template_text or "xcodebuildmcp" not in template_text or ("@" + "latest") in template_text or "npx" in template_text:
            errors.append(f"harness template lacks pinned MCP entries: {name}")
        if re.search(r'(?i)["\']?(?:api[_-]?key|token|client[_-]?secret|private[_-]?key|password)["\']?\s*[:=]', template_text):
            errors.append(f"harness template contains credential field: {name}")
        if LOCAL_USER_PATH in template_text or re.search(r"[A-Za-z]:\\Users\\|file://|~[/\\]", template_text):
            errors.append(f"harness template contains local path: {name}")
        if name == "codex":
            try:
                data = tomllib.loads(template_text)
                if data.get("mcp_servers", {}).get("xcodebuildmcp", {}).get("command") != "xcodebuildmcp" or data.get("mcp_servers", {}).get("xcodebuildmcp", {}).get("args") != ["mcp"]:
                    errors.append("Codex XcodeBuildMCP command is not pinned")
            except tomllib.TOMLDecodeError as exc:
                errors.append(f"invalid Codex TOML: {exc}")
        else:
            try:
                data = json.loads(template_text)
                servers = data.get("mcpServers", data.get("servers", {}))
                entry = servers.get("xcodebuildmcp")
                if not isinstance(entry, dict) or entry.get("command") != "xcodebuildmcp" or entry.get("args") != ["mcp"]:
                    errors.append(f"{name} XcodeBuildMCP command is not pinned")
            except json.JSONDecodeError as exc:
                errors.append(f"invalid harness JSON: {name} ({exc})")

    manifest_path = ASSETS / "tool-manifest.json"
    manifest_schema_path = ASSETS / "tool-manifest.schema.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        schema = json.loads(manifest_schema_path.read_text(encoding="utf-8"))
        tools = manifest.get("tools", [])
        if manifest.get("schemaVersion") != "1.1.0" or manifest.get("verifiedOn") != "2026-07-30" or manifest.get("platform") != "macOS arm64":
            errors.append("tool manifest metadata")
        if set(tool.get("id") for tool in tools) != TOOL_IDS or any(
            not tool.get("testedVersion")
            or not tool.get("ownerDomain")
            or tool.get("requirement") not in {"required", "optional"}
            or not set(tool.get("platforms", [])) <= {"ios", "android", "shared"}
            or not tool.get("platforms")
            or not tool.get("sourceUrl", "").startswith("https://")
            or not tool.get("install", {}).get("macos")
            for tool in tools
        ):
            errors.append("tool manifest semantic contract")
        required_tool_fields = ["id", "command", "testedVersion", "ownerDomain", "platforms", "requirement", "sourceUrl", "install"]
        if schema.get("properties", {}).get("tools", {}).get("items", {}).get("required") != required_tool_fields:
            errors.append("tool manifest schema contract")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid tool manifest/schema: {exc}")

    toolkit = ROOT / "scripts/toolkit.py"
    launcher = ROOT / "scripts/mobile-app-ship"
    tests = ROOT / "scripts/test_toolkit.py"
    if not toolkit.is_file() or not launcher.is_file() or not tests.is_file():
        errors.append("toolkit entry points/tests missing")
    else:
        toolkit_text = toolkit.read_text(encoding="utf-8")
        if not all(token in toolkit_text for token in ('"doctor"', '"bootstrap"', '"validate"', '"next-auth"', '"onboard"', '"onboard-web"', '"status-write"', '"coverage"', '"approvalMode"', '"strict"', '"--acknowledge-plan"', '"--approve-plan"', '"--check-scope"', '"--no-open"', '"dry-run: no writes"', '"--platform"', '"android-sdk-cmdline"', 'status_write_lock', 'fcntl', 'STATUS writes require POSIX directory locking')):
            errors.append("toolkit commands/dry-run/platform contract")
        if ".windsurf/mcp_config.json" in toolkit_text or "write_text(\"# Mobile App Ship" in toolkit_text:
            errors.append("unsupported harness fallback write contract")
        if "curl|bash" in toolkit_text or ("@" + "latest") in toolkit_text or "sudo" in toolkit_text:
            errors.append("unsafe toolkit install contract")

    contracts = (REFS / "tool-contracts.md").read_text(encoding="utf-8")
    for source in ("https://asccli.sh/", "https://www.revenuecat.com/docs/tools/mcp", "https://mcp.revenuecat.ai/mcp", "https://xcodebuildmcp.com/docs", "https://developers.google.com/admob/api/reference/rest", "https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create", "https://developers.google.com/admob/api/reference/rest/v1beta/accounts.adUnits/create", "https://pub.dev/packages/google_mobile_ads"):
        if source not in contracts:
            errors.append(f"missing official source URL: {source}")
    for owner in ("XcodeBuildMCP", "`asc` CLI", "RevenueCat MCP", "Flutter", "Firebase/Google", "Fastlane/Play", "**google_mobile_ads**", "**AdMob API**"):
        if owner not in contracts:
            errors.append(f"missing tool owner: {owner}")

    admob = (REFS / "admob-implementation.md").read_text(encoding="utf-8")
    required_admob = (
        "google_mobile_ads` 9.0.0",
        "google_mobile_ads: ^9.0.0",
        "ConsentInformation.instance.requestConsentInfoUpdate",
        "ConsentForm.loadAndShowConsentFormIfRequired((FormError? error) async",
        "final canRequestAds = await ConsentInformation.instance.canRequestAds();",
        "if (!canRequestAds) return;",
        "`kReleaseMode` or explicit flavor configuration",
        "If the app tracks users or accesses IDFA",
        "Do not add ATT solely because the app serves ads",
        "ca-app-pub-3940256099942544/6300978111",
        "ca-app-pub-3940256099942544/2934735716",
        "Ads-enabled release builds MUST use resolved real AdMob IDs",
        "a debug build MUST NOT load a real ID",
        "Real IDs are not secrets",
        "resolved flavor/configuration readback",
        "Artifact grep may supplement that readback, but is not proof by itself",
        "Initialization is not an ad request",
        "Only here may BannerAd.load()",
        "AdMob Console Human Gate",
        "method/schema inspection",
        "account eligibility/access confirmation",
        "On `403`, do not retry blindly",
        "https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create",
        "https://developers.google.com/admob/api/reference/rest/v1beta/accounts.adUnits/create",
    )
    if any(token not in admob for token in required_admob):
        errors.append("AdMob safety semantics")
    wrong_ad_unit_url = "https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps." + "adUnits/create"
    forbidden_att_claim = "iOS ATT is a " + "univer" + "sal requirement"
    declared_versions = re.findall(r"google_mobile_ads:\s*\^?(\d+\.\d+\.\d+)", admob)
    if wrong_ad_unit_url in admob + contracts or forbidden_att_claim in admob or "FLUTTER" + "_RELEASE" in admob or any(version != "9.0.0" for version in declared_versions):
        errors.append("AdMob forbidden regression")
    if not all(token in contracts for token in ("AdMob Console is the default Human Gate", "method/schema inspection", "403` is a Human Gate/account-manager escalation")):
        errors.append("AdMob tool ownership safety contract")

    schema = json.loads((ASSETS / "status.schema.json").read_text(encoding="utf-8"))
    required_model = {"schemaVersion", "toolkitVersion", "app", "targets", "actions", "evidence", "gates"}
    if set(schema.get("required", [])) != required_model or not required_model <= set(schema.get("properties", {})):
        errors.append("status schema missing required logical model")
    schema_states = set(schema.get("$defs", {}).get("lifecycleState", {}).get("enum", []))
    if schema_states != ALL_STATES:
        errors.append("status schema lifecycle states differ from validator")
    if set(schema.get("$defs", {}).get("gateBase", {}).get("properties", {}).get("class", {}).get("enum", [])) != GATE_CLASSES:
        errors.append("status schema gate classes differ from validator")
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() != json.loads((ASSETS / "STATUS.json").read_text(encoding="utf-8"))["toolkitVersion"]:
        errors.append("STATUS toolkitVersion differs from VERSION")

    # Root copies must be byte-identical to skill assets
    root_schema = ROOT / "schemas" / "status.schema.json"
    if root_schema.is_file():
        if root_schema.read_bytes() != (ASSETS / "status.schema.json").read_bytes():
            errors.append("schemas/status.schema.json differs from skill asset")
    else:
        errors.append("schemas/status.schema.json missing")

    root_fixtures_dir = ROOT / "tests" / "fixtures"
    valid_fixture = root_fixtures_dir / "status-valid.json"
    invalid_release = root_fixtures_dir / "status-invalid-release.json"
    structured_fixture = root_fixtures_dir / "status-structured.json"
    for name, path in [("status-valid.json", valid_fixture), ("status-invalid-release.json", invalid_release), ("status-structured.json", structured_fixture)]:
        if not path.is_file():
            errors.append(f"root test fixture missing: tests/fixtures/{name}")

    for name in ("STATUS.json", "valid-status.fixture.json"):
        for issue in status_errors(json.loads((ASSETS / name).read_text(encoding="utf-8"))):
            errors.append(f"{name}: {issue}")
    invalid_paths = sorted(ASSETS.glob("invalid*.fixture.json"))
    if len(invalid_paths) < 3:
        errors.append("meaningful negative fixtures missing")
    for path in invalid_paths:
        if not status_errors(json.loads(path.read_text(encoding="utf-8"))):
            errors.append(f"invalid fixture accepted: {path.name}")

    # Root test fixtures same Python-level validation
    if valid_fixture.is_file():
        for issue in status_errors(json.loads(valid_fixture.read_text(encoding="utf-8"))):
            errors.append(f"root fixture status-valid.json: {issue}")
    if structured_fixture.is_file():
        for issue in status_errors(json.loads(structured_fixture.read_text(encoding="utf-8"))):
            errors.append(f"root fixture status-structured.json: {issue}")
    if invalid_release.is_file():
        if not status_errors(json.loads(invalid_release.read_text(encoding="utf-8"))):
            errors.append(f"root fixture status-invalid-release.json should fail but passed")

    ios = (REFS / "pre-submission-review.md").read_text(encoding="utf-8")
    android = (REFS / "android-play.md").read_text(encoding="utf-8")
    prevention_contracts = {
        "field-tested-recoveries.md": ("Field-Tested Recoveries", "Exhaustive grouped incident ledger", "Durable invariants", "Intentionally excluded noise", "SNAPSHOT_EXPIRED", "browser_signature_banned", "outcome_unknown", "single-use", "read back", "never hand-create a Podfile"),
        "store-submission.md": ("canonical `tr`", "product review-media endpoint", "asc iap review-screenshots create --iap-id", "platform is `IOS`", "`TV_OS`", "Immediately read back after submit", "auto-create version localizations", "Omit `whatsNew` for the first version"),
        "ios-app-store.md": ("Runner target, never globally on Pods or Swift Package targets", "Declare encryption per build", "attached build separately from the TestFlight-distributed build", "real UI captures with overlays", "zero-padded upload order", "no price/currency text", "querying that set before retrying"),
        "pre-submission-review.md": ("doctor`/`validate` output can miss", "no IAP price or currency", "OCR before upload"),
        "revenuecat-mcp.md": ("Streamable HTTP, not SSE", "`405`"),
        "admob-implementation.md": ("Device ID/tracking", "metadata-only change", "requestConsentInfoUpdate", "loadAndShowConsentFormIfRequired", "canRequestAds"),
        "flutter-firebase.md": ("LC_ALL=en_US.UTF-8 flutter analyze", "ASCII-path mirror", "`dart analyze`", "global `**` rule"),
        "human-gates.md": ("future intent only", "SHA-256-bound", "not vendor approval", "exact single-use approval", "Public release", "--check-scope", "future_intent_only"),
    }
    expected_field_recovery_ids = (
        {f"S{i}" for i in range(1, 13)}
        | {f"A{i}" for i in range(1, 13)}
        | {f"R{i}" for i in range(1, 6)}
        | {f"M{i}" for i in range(1, 3)}
        | {f"F{i}" for i in range(1, 4)}
        | {f"X{i}" for i in range(1, 7)}
        | {f"D{i}" for i in range(1, 3)}
        | {f"O{i}" for i in range(1, 8)}
    )
    for name, tokens in prevention_contracts.items():
        text = (REFS / name).read_text(encoding="utf-8")
        if any(token not in text for token in tokens):
            errors.append(f"confirmed prevention rule regression: {name}")
        if name == "field-tested-recoveries.md":
            actual_ids = set(re.findall(r"^\| ([SARFXDOM]\d+) \|", text, re.M))
            if actual_ids != expected_field_recovery_ids:
                errors.append("field-tested recovery incident coverage regression")
    if "Guideline 4.8" not in ios:
        errors.append("Guideline 4.8 regression")
    if "Closed testing" not in android or "planning baseline" not in android:
        errors.append("Closed testing regression")
    for canonical in ("human-gates.md", "workflow-lifecycle.md", "state-evidence.md"):
        if canonical not in skill_text:
            errors.append(f"canonical authority not routed: {canonical}")

    ci = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    root_validator = (ROOT / "scripts" / "validate-playbook.sh").read_text(encoding="utf-8")
    if (not re.search(r"permissions:\s*\n\s+contents:\s*read", ci)
            or ci.count("- run:") != 1
            or "scripts/validate-playbook.sh" not in ci
            or not re.search(r"actions/checkout@[0-9a-f]{40}", ci)
            or "persist-credentials: false" not in ci
            or "timeout-minutes: 10" not in ci
            or "concurrency:" not in ci
            or "cancel-in-progress: true" not in ci):
        errors.append("CI must be read-only, time-bounded, SHA-pinned, deduplicated, and run only the root validator")
    dependabot = ROOT / ".github" / "dependabot.yml"
    if (not dependabot.is_file()
            or "package-ecosystem: github-actions" not in dependabot.read_text(encoding="utf-8")
            or "interval: weekly" not in dependabot.read_text(encoding="utf-8")):
        errors.append("GitHub Actions Dependabot update contract missing")
    browser_test = ROOT / "scripts" / "test_onboarding_browser.py"
    if "scripts/test_toolkit.py" not in root_validator or "validate_playbook.py" not in root_validator:
        errors.append("root validator must run offline toolkit tests and semantic validation")
    if not browser_test.is_file() or '"${CI:-}" == "true"' not in root_validator or "scripts/test_onboarding_browser.py" not in root_validator:
        errors.append("CI must run the dependency-free onboarding browser smoke test")
    elif any(token not in browser_test.read_text(encoding="utf-8") for token in ("--headless=new", "--dump-dom", "38 rendered fields", "public release defaults to no", "no fatal UI state")):
        errors.append("onboarding browser smoke contract regression")

    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    root_fixture_count = (valid_fixture.is_file() + structured_fixture.is_file() + invalid_release.is_file())
    print(f"PASS: structure, links, tool ownership, state semantics, {len(invalid_paths)} negative fixtures, {root_fixture_count} root fixtures, and regressions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
