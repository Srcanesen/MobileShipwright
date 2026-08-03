<p align="center">
  <img src=".github/assets/logo.png" alt="Mobile App Ship Playbook" width="110">
</p>

<h1 align="center">Mobile App Ship Playbook</h1>

<p align="center">
  An evidence-first, cloneable toolkit for shipping Flutter/Firebase apps through independent iOS App Store and Android Play paths — coordinating state, approvals, and human gates without giving up safety.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license"></a>
  <a href="VERSION"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version 0.1.0"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Tested on macOS arm64">
</p>

## What this is

One cloneable package: a canonical skill, manifests, inactive harness adapters, workflows, and validation for shipping mobile apps through separate App Store and Play paths. Its sole entry point is [skills/mobile-app-ship/SKILL.md](skills/mobile-app-ship/SKILL.md).

Tools install outside Git; no binary, token, OAuth state, user configuration, or credential belongs in this repository. See [PRODUCT.md](PRODUCT.md) for the product boundary, measurable coverage, and success metrics.

## Features

- **One canonical skill** — drives preflight, onboarding, bootstrap, and evidence recording for any target app.
- **Safe bootstrap** — dry-run by default; proposes only missing or drifted tools and never overwrites existing adapters.
- **Evidence-first state** — `status-write` records hash-bound, lock-protected STATUS transactions only after human approval.
- **Harness-agnostic** — inactive, credential-free templates for Pi, Claude Code, Codex, Cursor, Gemini CLI, VS Code, and Windsurf.
- **Offline validation** — Python standard library only; no runtime dependencies.
- **No secrets in Git** — credentials, OAuth state, and raw vendor responses never enter the repository.

## Quick start

```bash
git clone https://github.com/Srcanesen/mobile-app-ship-playbook.git
cd mobile-app-ship-playbook

# 1. Existing target: inspect its state read-only first.
scripts/mobile-app-ship preflight --target /path/to/app --platform ios --json

# New target, or a target without STATUS.json: fill the resumable form.
scripts/mobile-app-ship onboard-web --target /path/to/app --no-open
# Or use the terminal flow when a browser is unavailable.
scripts/mobile-app-ship onboard --target /path/to/app --interactive
# Onboarding stores .mobile-app-ship-decisions.json in the target; keep it target-local and ignored.

scripts/mobile-app-ship doctor --harness claude-code --target /path/to/app --platform both
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both
# bootstrap is dry-run by default; --apply only after inspecting the plan.
scripts/mobile-app-ship bootstrap --harness claude-code --target /path/to/app --platform both --apply --approve skill --approve adapter

# 2. Complete provider connections and record only vendor read-back evidence.
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app
scripts/mobile-app-ship next-auth --harness claude-code --target /path/to/app --record --approve-progress --outcome verified --claim "Sanitized read-back claim" --evidence-id evidence-001 --limitation "Sanitized limitation"
# Use --outcome not_needed --limitation "Out of scope" for providers the initial form excludes.

# 3. Optionally acknowledge the complete plan. This is not write approval.
scripts/mobile-app-ship onboard --target /path/to/app --acknowledge-plan
```

Every external mutation still needs its own exact single-use approval. Read the [canonical skill](skills/mobile-app-ship/SKILL.md) in the selected target, follow [harness onboarding](skills/mobile-app-ship/references/harness-onboarding.md), and connect providers one at a time.

## Supported harnesses

All adapter templates are inactive repository material; they are never loaded or copied automatically. Pi is the primary documented path; every other harness is optional.

| Harness | Template | Notes |
|---|---|---|
| **Pi** (primary) | [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) | Pi core has no native MCP client; uses the separately approved `pi-mcp-adapter` extension. RevenueCat may reject an unregistered Pi OAuth client — provider-dependent; do not retry blindly ([harness notes](harnesses/pi/README.md)). |
| Claude Code | [harnesses/claude-code/templates/.mcp.json](harnesses/claude-code/templates/.mcp.json) | Project-local `.mcp.json`. |
| Codex | [harnesses/codex/templates/config.toml](harnesses/codex/templates/config.toml) | Project-local `.codex/config.toml`; optional, not required. |
| Cursor | [harnesses/cursor/templates/mcp.json](harnesses/cursor/templates/mcp.json) | Project-local `.cursor/mcp.json`. |
| Gemini CLI | [harnesses/gemini-cli/templates/settings.json](harnesses/gemini-cli/templates/settings.json) | No fake skill; only an approved manual-context fallback. |
| VS Code | [harnesses/vscode/templates/mcp.json](harnesses/vscode/templates/mcp.json) | Workspace/project `.vscode/mcp.json`. |
| Windsurf | [harnesses/windsurf/templates/mcp_config.json](harnesses/windsurf/templates/mcp_config.json) | Review-only; unsupported for bootstrap; manual Human-gate merge into user-global config. |

**Pi primary path.** After a separate local approval, install the tested `pi-mcp-adapter` and merge only the credential-free RevenueCat entry from `harnesses/pi/templates/mcp.json` into `~/.pi/agent/mcp.json` — lazy lifecycle, OAuth, proxy-only. Never create a project `.mcp.json`, run the adapter's init, or paste credentials. Authenticate in a separate session and perform read-only RevenueCat discovery before any write gate.

## Safety model

- Authentication and plan acknowledgement never authorize writes; selected scopes are future intent only.
- Every external mutation follows **Inspect → Plan → exact single-use approval → Apply once → Read back → Evidence**.
- Upload, tester distribution, submission, and release are separate actions with separate consumed gates.
- Public release defaults to no and requires its own exact approval.
- Stop for scope/value drift, secrets, manual 2FA/account/payment/legal work, destructive recovery, or unknown timeouts.
- This repository is the playbook, not a shipped target app: keep every target in a separate directory and never copy target state, credentials, OAuth state, or raw vendor responses here. Never use `git reset`, `git clean`, or force checkout to hide or remove someone else's work.

## Project structure

```
├── scripts/mobile-app-ship          # CLI: preflight, onboard, doctor, bootstrap, next-auth, validate
├── skills/mobile-app-ship/          # Canonical skill, references, fixtures, browser onboarding page
│   └── SKILL.md
├── harnesses/                       # Inactive per-harness MCP templates (Pi, Codex, Windsurf, ...)
├── schemas/status.schema.json       # STATUS transaction schema (byte-identical to the skill asset)
├── tests/fixtures/                  # Valid and invalid STATUS fixtures
├── .github/workflows/validate.yml   # CI: offline validation plus browser smoke
├── Brewfile                         # macOS arm64 install inventory
├── PRODUCT.md                       # Product boundary and success metrics
├── CONTRIBUTING.md                  # Contribution guidelines
├── SECURITY.md                      # Vulnerability reporting
└── LICENSE                          # MIT license
```

## Validation

```bash
python3 scripts/test_toolkit.py
python3 scripts/test_onboarding_browser.py
scripts/mobile-app-ship validate
bash scripts/validate-playbook.sh
python3 skills/mobile-app-ship/scripts/validate_playbook.py
git diff --check
```

Validation is offline and read-only. CI runs the root wrapper, which also runs the onboarding browser smoke when `CI=true`.

## Contributing

Contributions are welcome — read [CONTRIBUTING.md](CONTRIBUTING.md) first. Report vulnerabilities through the process in [SECURITY.md](SECURITY.md). This project is [MIT licensed](LICENSE). See [PRODUCT.md](PRODUCT.md) for the product boundary and success metrics.
