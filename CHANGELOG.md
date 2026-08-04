# Changelog

## Unreleased

## 0.2.0 — 2026-08-04

- Made STATUS consume-gate and action transitions authoritative: a `--consume-gate` consumption may change only the linked gate state, and an `approved -> started` action transition is allowed only for that consume gate.
- Added fail-closed black-box safety contracts covering the STATUS lifecycle, gate, evidence, secret, and transaction boundaries.
- Improved mutation-detection evidence from 8/29 (27.59%) to 29/29 (100%) killed mutants.
- Passed the full offline validation suite: 55/55 tests.
- Rebranded the playbook as MobileShipwright and improved READMEs, Discussions, community-health metadata, and the social preview.
- No STATUS schema migration and no provider mutation required.

## 0.1.0 — 2026-08-03

- Consolidated the repository into one public-facing Flutter/Firebase shipping skill.
- Added explicit tool contracts, role-aware human gates, target-app state/evidence/gate templates, schema, negative fixtures, and offline semantic validation.
- Restored detailed setup, phase routing, Firebase, design/localization, security, signing, store submission/rejection, stability, Play, RevenueCat, compliance, and pitfall guidance under flat progressive-disclosure references.
- Added harness-neutral onboarding and inactive, credential-free MCP adapter templates for Claude Code, Codex CLI, Cursor, VS Code/GitHub Copilot, Windsurf, and Gemini CLI.
- Documented Pi's core no-MCP boundary plus the optional pinned `pi-mcp-adapter` RevenueCat fallback with lazy OAuth/proxy operation.
- Added fail-closed legacy STATUS scope re-approval, POSIX writer locking, unknown-bootstrap-approval rejection, CI action pinning/concurrency, Dependabot coverage, and offline contract coverage.
- Added a sourced App Store Optimization (ASO) planning/review reference with official citations, fact-vs-heuristic labels, and revalidation guidance for Apple and Google metadata, keywords, visual assets, localization, experiments, and metrics.
