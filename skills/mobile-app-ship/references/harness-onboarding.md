# Harness Onboarding — One Harness, One Provider at a Time

Start here before any tool call. This toolkit is harness-neutral and has one canonical skill: [SKILL.md](../SKILL.md). The repository templates are inactive examples; they are never discovered from the repository root.

## Preflight first

When the target already has a `STATUS.json`, run the read-only preflight before anything else:

```bash
scripts/mobile-app-ship preflight --target <app-dir> --platform ios
scripts/mobile-app-ship preflight --target <app-dir> --platform ios --json
```

`preflight` loads and semantically validates `STATUS.json` without writing it, reports sanitized action/evidence/gate counts and gate states, and selects the next state by strict priority: any `outcome_unknown` action -> `read_back_before_retry`; any pending gate linked to a planned/approved/started external mutation -> `approval_required`; any planned/approved/started action -> `resume_action`; otherwise no pending action. The first IAP version action (`act-asc-iap-version-create` / `gate-asc-iap-version-create`) is reported as `already_verified` when verified; when absent it is reported as a read-only `first_external_action_not_recorded` gap. Preflight never calls vendor tools, never creates plans or gates, and never writes target files. On a target without `STATUS.json` it reports a clear gap and exits nonzero instead.

## Safe sequence

For a new target without `STATUS.json`, run `scripts/mobile-app-ship onboard --target <app-dir> --interactive` first. For an existing target, run `preflight` first and ask only for information that is still missing. `onboard` records only sanitized decisions and requested future scopes; it neither authenticates nor authorizes writes. Complete provider authentication with the emitted `next-auth` command and vendor read-back evidence, then optionally run `onboard --acknowledge-plan`. Acknowledgement is not vendor approval; every external mutation requires its own exact single-use approval.

1. **Discover read-only.** Identify the current harness, local Flutter/Firebase tools, and available device/tool state. Do not install tools, log in, or inspect secret files.
2. **Choose one harness.** Read its `harnesses/<name>/README.md`. Copy only a supported project adapter after the user approves its activation. Do not mix adapters. Windsurf is a Human gate: review `harnesses/windsurf/templates/mcp_config.json` and let the user manually merge approved entries into `~/.codeium/windsurf/mcp_config.json`; bootstrap never writes a project or global Windsurf MCP file. Gemini has no supported native skill target, so use the canonical repository skill manually and do not generate `GEMINI.md`.
3. **Apple first when iOS is in scope.** Discover installed `asc` capability with `asc --help`, `asc search auth`, and command help. Use native browser authentication when available. Never invent an `asc` auth command. Run only a read-only team/app inventory after authentication.
4. **Activate XcodeBuildMCP next.** Its template runs persistent installed `xcodebuildmcp mcp`. Request separate install and adapter-activation approval before copying or using it. Discover live tool schemas and perform only local read-only project/tool discovery. It has no OAuth flow.
5. **Connect RevenueCat after that.** Prefer the official MCP endpoint and native browser OAuth where the chosen harness supports it. For Pi, core has no native MCP; use the separately approved `pi-mcp-adapter` fallback documented in [`harnesses/pi/README.md`](../../../harnesses/pi/README.md) and its inactive [`templates/mcp.json`](../../../harnesses/pi/templates/mcp.json). Keep it user-global, lazy, OAuth/proxy-only, and credential-free in Git. Discover live schemas, then run only read-only project/app discovery. API v2 fallback is user/environment configuration outside Git and should use a dedicated read-only key when writes are not needed.
6. **Defer other providers.** Start Firebase browser login only when backend work begins. Start Play/service-account credential work only when Android work begins. Do not request secrets in chat.
7. **Record each result.** Before moving forward, record an explicit `verified` or `deferred` outcome with sanitized evidence/limitations. `verified` requires a nonempty read-back claim and evidence ID. `deferred` requires a limitation, remains the next resumable step, and is not complete. Printing a step or receiving command exit zero is never evidence. Never record secrets.

Authentication proves identity only. It does not authorize writes. Every write still follows **Inspect → Plan → scoped approval → Apply once → Read back → Evidence**. Keep upload, tester distribution, review submission, and release approvals separate.

## Secret-safe interaction

Never ask users to paste tokens, passwords, redirect secrets, `.p8` contents, private keys, or service-account JSON into chat. Direct users to the harness browser OAuth UI or a secure local credential surface. Record only identifiers and sanitized success/failure evidence.

## Unsupported native MCP

If the selected harness lacks a native MCP path, do not improvise a client or wrapper. Use the skill directly, create a [Human gate](human-gates.md), and use only a separately user-approved documented extension/fallback. Pi core has **“No MCP”**; its optional `pi-mcp-adapter` path is documented separately and is not loaded, installed, authenticated, or copied automatically. Keep the RevenueCat template user-global at `~/.pi/agent/mcp.json`, never project-local. Do not run `pi-mcp-adapter init` during validation because it can import host configs and write Pi-owned files.

## Language

Reply in the user's latest clear language, natural Turkish or English; do not ask when it is clear. Translate explanations, not IDs, paths, or commands. Hide raw IDs from ordinary summaries; show them unchanged only when approval or debugging requires them, with a plain-language explanation. Preserve exact single-use approval wording and safety boundaries. Human `preflight` and `onboard` output is localized by `--language auto|tr|en` or `MOBILE_APP_SHIP_LANGUAGE`; `auto` reads only `LC_ALL`/`LC_MESSAGES`/`LANG`, so pass the explicit `--language` matching the user when quoting human output. `--json` output stays machine-compatible and is never localized.

Continue with [setup-readiness.md](setup-readiness.md) and [tool-contracts.md](tool-contracts.md) after selecting the harness.
