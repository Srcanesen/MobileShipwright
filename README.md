<p align="center">
  <img src=".github/assets/logo.png" alt="MobileShipwright" width="110">
</p>

<p align="center"><b><a href="README.md">English</a> | <a href="README.tr.md">Türkçe</a></b></p>

<h1 align="center">MobileShipwright</h1>

<p align="center">An agent-guided mobile release playbook for Flutter and Firebase apps—covering App Store Connect, TestFlight, Google Play, RevenueCat, and safety-gated delivery.</p>

<p align="center">
  <a href="https://github.com/Srcanesen/MobileShipwright/actions/workflows/validate.yml"><img src="https://github.com/Srcanesen/MobileShipwright/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license"></a>
  <a href="VERSION"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version 0.1.0"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="Tested on macOS arm64">
</p>

## Contents

- [Give the playbook to an agent](#give-the-playbook-to-an-agent)
- [Project status](#project-status)
- [Safe end-to-end flow](#safe-end-to-end-flow)
- [What commands do—and do not do](#what-commands-doand-do-not-do)
- [Authentication: safe, ordered, and user-controlled](#authentication-safe-ordered-and-user-controlled)
- [Harnesses and inactive templates](#harnesses-and-inactive-templates)
- [State, resume, and evidence](#state-resume-and-evidence)
- [Approval taxonomy](#approval-taxonomy)
- [Common scenarios and troubleshooting](#common-scenarios-and-troubleshooting)
- [Validate this repository](#validate-this-repository)

## Give the playbook to an agent

The playbook is published as a tested Agent Skill. Install it with the skills CLI:

```bash
npx skills add Srcanesen/MobileShipwright --skill mobile-app-ship
```

Tell the agent the target path and desired scope. It must read in this order:

1. [AGENTS.md](AGENTS.md)
2. [the canonical SKILL.md](skills/mobile-app-ship/SKILL.md)
3. [harness-onboarding.md](skills/mobile-app-ship/references/harness-onboarding.md)
4. Only the phase or provider references routed by the skill

Use these copy-ready prompts after cloning `https://github.com/Srcanesen/MobileShipwright.git` and opening it in your chosen harness.

**Existing app**

> Use this playbook to inspect my existing app at `<target-app-dir>`. Read `AGENTS.md`, then `skills/mobile-app-ship/SKILL.md`, then `skills/mobile-app-ship/references/harness-onboarding.md`. Start with read-only preflight. Do not install, authenticate, configure, write, or contact a provider without my separate exact approval.

**New app**

> Use this playbook for a new app at `<target-app-dir>`. Read `AGENTS.md`, then the canonical skill and harness onboarding. Start with onboarding, keep templates inactive, and show me the dry-run plan. Do not apply any change or authenticate a provider until I approve that specific action.

**Read-only audit**

> Audit the app at `<target-app-dir>` using this playbook. Read the required onboarding chain and run read-only discovery only. Report missing readiness, unknown outcomes, and the next safe step. Do not write target files, install tools, authenticate, or call provider mutation tools.

## Project status

> **Active development.** This is a 0.x project. Its guidance and interfaces will continue to evolve as more real shipping workflows are exercised and reviewed.

- **iOS:** The iOS path has been used with a real app through submission to **App Review in App Store Connect**. This confirms that the workflow reached review submission; it does not claim App Store approval or public release.
- **Android:** The Google Play path is documented, but it has **not yet been tested end to end with a real Play submission**. Treat the Android guidance as not yet production-validated and report any gaps you find.

This repository is the playbook, not the app being shipped. Give it to your coding agent by cloning or opening **this repository in the agent harness**, then name the separate app directory explicitly as `<target-app-dir>`. The target app remains separate; repository templates are inactive examples and are not discovered, installed, copied, authenticated, or activated automatically.

The canonical entry point is [skills/mobile-app-ship/SKILL.md](skills/mobile-app-ship/SKILL.md). Product boundaries and metrics live in [PRODUCT.md](PRODUCT.md). Keep binaries, OAuth state, tokens, user configuration, credentials, target state, and raw vendor responses out of this repository and Git.

## Safe end-to-end flow

### 1. Choose the correct starting point

For an existing target with `STATUS.json`, begin with `preflight`. It validates and summarizes state without writing target files, creating gates, or calling vendors. For a new target—or one without `STATUS.json`—start `onboard` or `onboard-web`; they capture sanitized, resumable decisions and future intent only.

```bash
# Existing app: read-only state inspection.
scripts/mobile-app-ship preflight --target "<target-app-dir>" --platform ios --language en

# New app: choose one onboarding surface.
scripts/mobile-app-ship onboard --target "<target-app-dir>" --interactive --language en
scripts/mobile-app-ship onboard-web --target "<target-app-dir>" --no-open
```

### 2. Inspect readiness and a proposed setup

Select one harness. Run `doctor`, then inspect the default dry-run from `bootstrap`. Dry-run does not install tools, change configuration, or activate templates. An `--apply` operation is an external mutation and needs its own exact approval after you inspect the plan.

```bash
scripts/mobile-app-ship doctor --harness pi --target "<target-app-dir>" --platform both
scripts/mobile-app-ship bootstrap --harness pi --target "<target-app-dir>" --platform both
```

### 3. Authenticate one provider at a time

Use `next-auth` to identify the next connection. After user-controlled browser or native OAuth, perform a read-only inventory and record only sanitized read-back evidence. Authentication proves identity; it never authorizes a write.

```bash
# Show the next provider connection.
scripts/mobile-app-ship next-auth --harness pi --target "<target-app-dir>"

# After read-back, record a sanitized verified result. This still grants no write approval.
scripts/mobile-app-ship next-auth --harness pi --target "<target-app-dir>" --record --approve-progress --outcome verified --claim "Read-only inventory confirmed" --evidence-id "<evidence-id>" --limitation "No mutation attempted"
```

### 4. Optionally acknowledge a complete plan

After decisions and required read-backs are complete, this records a SHA-256-bound acknowledgement. It is not write approval. A decision change invalidates that acknowledgement.

```bash
scripts/mobile-app-ship onboard --target "<target-app-dir>" --acknowledge-plan
```

### 5. Approve each mutation separately

For every external mutation, repeat the approval loop below. Uploading a build, distributing to testers, submitting for review, and public release are separate actions with separate approvals and evidence. Public release is off by default.

## What commands do—and do not do

| Command | Does | Does **not** do |
|---|---|---|
| `preflight --target` | Read and semantically validate existing `STATUS.json`; choose the next resumable state. | Write files, create gates/plans, or call vendors. |
| `onboard --target` | Collect sanitized decisions and future scopes; `--show` reads the resumable plan. | Authenticate, authorize vendor writes, or make scopes reusable approval. |
| `onboard-web --target` | Serve the local, loopback-only, secret-free onboarding form. | Perform vendor work or serve target files other than the decision state. |
| `doctor --harness --target --platform` | Inspect local tool availability and drift. | Install tools, edit PATH/profile files, or authenticate. |
| `bootstrap --harness --target --platform` | Show a dry-run of missing/drift setup work by default. | Apply its plan, overwrite/merge adapters, or install automatically. |
| `next-auth --harness --target` | Route the next provider connection and, with explicit record flags, store sanitized progress after read-back. | Authenticate by itself, store secrets, or authorize mutations. |
| `status-write --target --expect-sha256 --transaction` | Atomically record an already-approved, hash-bound `STATUS` transaction. | Authorize, contact, or execute a vendor; it fails closed where safe POSIX locking is unavailable. |
| `coverage --target --platform` | Report read-only responsibility coverage, scope binding, and unknown outcomes. | Produce a readiness score or execute vendors. |
| `validate` | Validate the playbook locally. | Ship an app, contact vendors, or alter app/provider state. |

Use explicit `--language en` or `--language tr` for human `preflight` and `onboard` output. `--json` remains machine-readable and is never localized.

## Authentication: safe, ordered, and user-controlled

Use the harness's native browser or OAuth interface; never paste tokens, passwords, redirect secrets, `.p8` contents, private keys, or service-account JSON into chat, Git, or target state. Connect **one harness and one provider at a time**. First complete read-only inventory/read-back; then record the result as `verified`, `deferred`, or `not_needed` with sanitized evidence and limitations. `verified` needs a nonempty read-back claim and evidence ID. `deferred` is not complete and remains the next resumable step.

Follow this order when relevant, without inventing provider commands:

1. **Apple/App Store Connect:** discover the installed `asc` capabilities and use native browser authentication only when available; then perform read-only team/app inventory.
2. **XcodeBuildMCP:** after Apple read-back, separately approve installation and adapter activation when needed. It has no OAuth. Use it for local project/tool discovery and, once signing is configured, build/test/simulator/device/log work—not certificate, profile, or portal configuration.
3. **RevenueCat:** use its official MCP endpoint and native browser OAuth where the chosen harness supports it; discover live schemas and perform read-only project/app inventory first.
4. **Firebase:** start browser login only when backend work starts.
5. **Google Play:** start service-account credential work only when Android work starts.

A timeout is `outcome_unknown`, not success or failure. Read current vendor state before retrying or requesting another approval. Never infer vendor state from a command exit code.

### Pi is the primary documented path

Pi core has no built-in MCP. Its RevenueCat fallback requires a **separate local approval**: use the documented, credential-free entry in [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) and the instructions in [harnesses/pi/README.md](harnesses/pi/README.md). Keep it user-global, lazy, OAuth/proxy-only, and outside Git; do not create a project MCP file or run `pi-mcp-adapter init`. Start a separate Pi session for authentication, then perform read-only RevenueCat discovery before any write gate.

RevenueCat can reject an unregistered Pi OAuth client. That is provider-dependent: do not blindly retry; use RevenueCat allowlisting or the documented user-level bearer-token fallback.

## Harnesses and inactive templates

Templates remain inactive until a scoped approval. Pi is the primary documented route; the alternatives remain available when the user selects them.

| Harness | Template | Notes |
|---|---|---|
| **Pi** (primary) | [harnesses/pi/templates/mcp.json](harnesses/pi/templates/mcp.json) | Core has no native MCP; use the separately approved `pi-mcp-adapter` fallback. RevenueCat may reject an unregistered Pi OAuth client; do not blindly retry ([Pi notes](harnesses/pi/README.md)). |
| Claude Code | [harnesses/claude-code/templates/.mcp.json](harnesses/claude-code/templates/.mcp.json) | Uses project-local `.mcp.json`. |
| Codex | [harnesses/codex/templates/config.toml](harnesses/codex/templates/config.toml) | Uses project-local `.codex/config.toml`; optional. |
| Cursor | [harnesses/cursor/templates/mcp.json](harnesses/cursor/templates/mcp.json) | Uses project-local `.cursor/mcp.json`. |
| Gemini CLI | [harnesses/gemini-cli/templates/settings.json](harnesses/gemini-cli/templates/settings.json) | No fake native skill; only an approved manual context-transfer option. |
| VS Code | [harnesses/vscode/templates/mcp.json](harnesses/vscode/templates/mcp.json) | Uses workspace-local `.vscode/mcp.json`. |
| Windsurf | [harnesses/windsurf/templates/mcp_config.json](harnesses/windsurf/templates/mcp_config.json) | Review-only; bootstrap does not support it. A user-global merge is a Human gate. |

## State, resume, and evidence

All working state belongs in the target app directory, never this playbook. Keep exactly one canonical delivery record: `STATUS.json` **or** `PROGRESS.md`.

| Target-local file | Purpose | Safety rule |
|---|---|---|
| `.mobile-app-ship-decisions.json` | Sanitized onboarding decisions and requested future scopes. | Do not store secrets; add it to the target's ignore rules yourself if needed. A decision change invalidates plan acknowledgement. |
| `.mobile-app-ship-onboarding.json` | Backward-compatible `next-auth` connection progress. | Never store secrets; resume only from read-back-supported state. |
| `STATUS.json` **or** `PROGRESS.md` | Canonical delivery status, actions, evidence, blockers, and gates. | Keep exactly one. `status-write` needs the current `--expect-sha256` and records only an already-approved transaction. |

Use `onboard --show` or `--json` to inspect sanitized state. Do not claim an action is done because a command printed a step or exited zero. Record sanitized evidence after read-back instead.

## Approval taxonomy

A plan acknowledgement says: “I have reviewed these complete decisions and read-backs.” It does **not** say: “perform a vendor write.” A selected scope says only: “this may be wanted later.” It is not approval either.

Every provider mutation needs the exact, single-use approval for that action and current values:

**Inspect → Plan → exact single-use approval → Apply once → Read back → Evidence**

Stop when scope/value drift appears, a secret or manual 2FA/account/payment/legal task is required, destructive recovery/revocation is proposed, or the outcome is unknown. Request a new approval only after state is read back.

## Common scenarios and troubleshooting

- **Existing app with state:** run `preflight`; resolve `outcome_unknown` with read-back before retrying.
- **New app or no `STATUS.json`:** run `onboard` or `onboard-web`; complete required decisions before acknowledgement.
- **Need a tool or adapter:** inspect `doctor` and dry-run `bootstrap`; request approval for installation/activation separately. Nothing installs itself.
- **Provider is connected but no evidence exists:** run the provider's read-only inventory and record sanitized `verified`, `deferred`, or `not_needed` progress.
- **RevenueCat rejects Pi OAuth:** stop retrying and follow the Pi fallback guidance above.
- **Need to resume:** read the three target-local state records; retain the separate iOS and Android histories, blockers, and approvals.

## Validate this repository

```bash
PYTHONDONTWRITEBYTECODE=1 CI=true bash scripts/validate-playbook.sh
git diff --check
git status --short
```

For contributions, read [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues through [SECURITY.md](SECURITY.md). This project is [MIT licensed](LICENSE); see [PRODUCT.md](PRODUCT.md) for its boundary and success measures.
