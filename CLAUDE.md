# Claude Code Entry Point

Read [`AGENTS.md`](AGENTS.md) first, then follow the canonical [`skills/mobile-app-ship/SKILL.md`](skills/mobile-app-ship/SKILL.md). Load [`harness-onboarding.md`](skills/mobile-app-ship/references/harness-onboarding.md) before using provider tools.

Work from the repository root with an explicit `<target-app-dir>`. For an existing app, begin with read-only `preflight`; for a new app without `STATUS.json`, begin with `onboard`. Then use `doctor` and dry-run `bootstrap`. A clone does not install dependencies, configure MCP servers, or authenticate accounts automatically.

Do not perform an external mutation until you have inspected current state, shown the exact plan, and received an exact single-use approval. Apply once, read vendor state back, and record sanitized evidence. Treat timeouts as `outcome_unknown` and inspect before retrying.

Never write credentials, tokens, OAuth state, private keys, signing material, or secret output to the repository or target state. Use direct vendor-owner tools and validate changes with:

```bash
bash scripts/validate-playbook.sh
```

## Language policy

Reply in the user's latest clear language (natural Turkish or English); never ask when it is clear. Translate explanations, not identifiers, paths, or commands. Hide raw IDs in ordinary summaries; show them unchanged only when approval or debugging requires them, with a plain-language explanation. Keep exact single-use approval wording and safety boundaries unchanged. `preflight`/`onboard` human output follows `--language auto|tr|en` or `MOBILE_APP_SHIP_LANGUAGE`; pass the explicit `--language` matching the user, because `auto` reads only `LC_ALL`/`LC_MESSAGES`/`LANG` and cannot infer chat language. `--json` output stays machine-compatible and is never localized.
