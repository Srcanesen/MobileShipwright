---
name: mobile-app-ship
description: Guide a Flutter and Firebase app from first scope through independent iOS App Store and Android Play release paths using XcodeBuildMCP, asc CLI, RevenueCat MCP, and explicit human gates. Use when planning, implementing, validating, distributing, submitting, releasing, recovering a rejection, or resuming a mobile app shipment.
---

# Mobile App Ship

Use this as the sole coordinator. This repository is the package: for an existing target, run read-only `scripts/mobile-app-ship preflight --target <app-dir> --language <tr|en>` first; use `coverage` only for read-only responsibility counts. Use `status-write` only with its mandatory current `--expect-sha256` precondition and POSIX directory lock to record an already-approved transaction; it fails closed on unsupported platforms and never authorizes, contacts, or executes a vendor. For a new target without `STATUS.json`, run `onboard` or `onboard-web`. Then use `doctor`, dry-run `bootstrap`, `validate`, and `next-auth` as needed; adapters and exact tested-version manifests remain inactive until scoped approval. Before delivery phases, run `onboard --target <app-dir> --interactive` or use repeatable `--set key=value` in scripts. It atomically stores sanitized non-secret decisions in target-local `.mobile-app-ship-decisions.json`, validated by [onboarding.schema.json](assets/onboarding.schema.json); it does not add that file to the target's ignore rules, so add it yourself. `next-auth` keeps its backward-compatible `.mobile-app-ship-onboarding.json` progress file and never stores secrets. Onboarding is strict-only. `--acknowledge-plan` records a SHA-256-bound, non-authorizing acknowledgement after complete decisions and read-backs; any decision change invalidates it. Selected scopes are future intent only. `--approve-plan` is a deprecated non-authorizing alias, and `--check-scope` never returns write approval. Use `--show` or `--json` for the secret-free status/plan. Keep target-app state outside this toolkit: `SPEC.md`, `DECISIONS.md`, and exactly one of `PROGRESS.md` or `STATUS.json`. Copy templates from [assets](assets/) before work.

## Harness onboarding

Before tool use, load [harness-onboarding.md](references/harness-onboarding.md). Complete the first-run connection checks for ASC, Firebase/gcloud, RevenueCat MCP transport, Flutter, Xcode, and XcodeBuildMCP before delivery phases. Select one harness, run the package doctor/bootstrap dry-run, keep repository templates inactive until approval, authenticate one provider at a time, and record each gate/evidence before continuing. Pi core has no built-in MCP; use this skill directly or the separately user-approved `pi-mcp-adapter` fallback documented in `harnesses/pi/README.md`.

## Core loop

1. Inspect repository and vendor state; record uncertainty.
2. Load the phase router and only the references needed for the next reversible step.
3. Classify the action and request an exact, single-use approval for every external mutation.
4. Apply once with the direct owner tool, read back, and record sanitized evidence.
5. Mark interruption/timeout `outcome_unknown`; query current state before retry.

Keep iOS and Android lifecycle/history/blockers independent. Upload, distribution, submission, and release remain separate actions/evidence with separate consumed gates. Never infer device, store-processing, submission, or release state from a build or command exit.

## Language

Reply in the user's latest clear language, natural Turkish or English; never ask when it is clear. Translate explanations, not identifiers, paths, or commands. Hide raw IDs from ordinary summaries; show them unchanged only when approval or debugging requires them, with a plain-language explanation. Keep exact single-use approval wording and safety boundaries unchanged. Summarize deep `doctor`/`bootstrap` diagnostics in the user's language while their JSON output stays raw. Human `preflight`/`onboard` output follows `--language auto|tr|en` or `MOBILE_APP_SHIP_LANGUAGE` (`auto` reads only `LC_ALL`/`LC_MESSAGES`/`LANG`, never chat language): pass the explicit `--language` matching the user when invoking or quoting human output. `--json` output is never localized.

## Canonical references

- [workflow-lifecycle.md](references/workflow-lifecycle.md): detailed Phase 0–15 router, rejection route, and lifecycle order.
- [state-evidence.md](references/state-evidence.md): canonical target, action, evidence, blocker, and gate record model.
- [human-gates.md](references/human-gates.md): canonical action classification and exact single-use gates.
- [failure-resume.md](references/failure-resume.md): unknown outcomes, retry limits, and resume.
- [tool-contracts.md](references/tool-contracts.md): direct-tool ownership boundaries.
- [field-tested-recoveries.md](references/field-tested-recoveries.md): exhaustive error → root cause → recovery → verification ledger from two shipping sessions; load before debugging or recovery.

## Load by phase or domain

- Setup: [setup-readiness.md](references/setup-readiness.md).
- Product, Flutter, Firebase, backend, and iteration: [flutter-firebase.md](references/flutter-firebase.md), [security-cost.md](references/security-cost.md), and conditional [admin-panel.md](references/admin-panel.md).
- Design and localization: [design-rules.md](references/design-rules.md) and [localization.md](references/localization.md).
- iOS/signing/store: [ios-app-store.md](references/ios-app-store.md), conditional [siwa-gates.md](references/siwa-gates.md), [store-submission.md](references/store-submission.md), [pre-submission-review.md](references/pre-submission-review.md), and [aso.md](references/aso.md) for metadata/ASO planning and review.
- Android/Play: [android-play.md](references/android-play.md); load [aso.md](references/aso.md) for Play metadata/ASO planning and review.
- Monetization: [revenuecat-implementation.md](references/revenuecat-implementation.md) after store products exist and read back; for ads load [admob-implementation.md](references/admob-implementation.md).
- Stability/compliance/debugging: [quality-compliance.md](references/quality-compliance.md), [stability-gate.md](references/stability-gate.md), [pitfalls.md](references/pitfalls.md), and [field-tested-recoveries.md](references/field-tested-recoveries.md) for field-tested error recovery.
- Tool operation: [xcodebuildmcp.md](references/xcodebuildmcp.md), [asc-cli.md](references/asc-cli.md), and [revenuecat-mcp.md](references/revenuecat-mcp.md).
- Harness selection and provider OAuth: [harness-onboarding.md](references/harness-onboarding.md).

## Non-negotiables

- Use vendor tools directly; do not build a release CLI, MCP proxy, REST wrapper, daemon, or store adapter.
- XcodeBuildMCP performs local discovery/build/test/simulator/device/log work only after signing exists; it cannot configure signing or profiles.
- Discover `asc` commands at runtime with installed `asc --help`, `asc search`, and command help. Use only verified examples and open a Human gate when parity is uncertain.
- Create and read back App Store/Play products before RevenueCat product/entitlement/offering/package wiring. Store SKU and RevenueCat `prod...` ID differ.
- Server-verify idempotent purchase grants. Test purchase, restore, relaunch, and deletion on distributed physical-device builds.
- Revalidate volatile platform requirements against official sources. Keep credentials and local state out of Git.

After changing this skill, run `bash scripts/validate-playbook.sh` from the toolkit repository root or `python3 scripts/validate_playbook.py` from the standalone skill directory.
