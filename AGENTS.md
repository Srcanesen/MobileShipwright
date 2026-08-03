# Agent Entry Point

Use this repository as an agent-guided mobile shipping playbook. Run commands from the repository root and use an explicit `<target-app-dir>`; never assume the current repository is the app being shipped.

## Required read order

1. Read the canonical [`skills/mobile-app-ship/SKILL.md`](skills/mobile-app-ship/SKILL.md).
2. Read [`skills/mobile-app-ship/references/harness-onboarding.md`](skills/mobile-app-ship/references/harness-onboarding.md).
3. Load only the phase or provider references routed by the canonical skill.

Do not treat this file as a replacement for the canonical skill.

## Start safely

For an existing app, check its current state first. For a new app, answer the short starting questions:

```bash
scripts/mobile-app-ship preflight --target "<target-app-dir>" --platform ios --language tr
scripts/mobile-app-ship onboard-web --target "<target-app-dir>"
scripts/mobile-app-ship doctor --harness <harness> --target "<target-app-dir>" --platform <ios|android|both>
scripts/mobile-app-ship bootstrap --harness <harness> --target "<target-app-dir>" --platform <ios|android|both>
```

`bootstrap` is dry-run by default. Cloning this repository does not install tools, configure MCP servers, or authenticate providers. Inspect the plan first; apply only explicitly approved items. Connect one harness and one provider at a time.

## Safety contract

- Every external mutation follows **Inspect → Plan → exact single-use approval → Apply once → Read back → sanitized evidence**.
- A timeout becomes `outcome_unknown`; read vendor state before requesting a new approval or retrying.
- Keep app state in the target directory: `.mobile-app-ship-decisions.json`, `.mobile-app-ship-onboarding.json`, and the target's canonical `STATUS.json` or `PROGRESS.md`.
- Never store credentials, tokens, OAuth state, private keys, signing material, or secret-bearing command output in Git or target state.
- Use each provider's direct owner tool. Do not invent wrappers or infer success from an exit code alone.

## Language policy

Reply in the user's latest clear language: natural Turkish or natural English. Never ask which language to use when it is clear; if unclear, default to the language of the latest user message. Translate explanations and summaries, never identifiers, paths, or commands. Do not show raw action/gate/evidence IDs in ordinary summaries; when they are needed for approval or debugging, show them verbatim with a plain-language explanation. Show technical detail only when needed or requested; summarize deep `doctor`/`bootstrap` diagnostics in the user's language instead of dumping raw output. Preserve exact single-use approval wording and never soften safety boundaries.

Human-facing `preflight` and `onboard` output follows `--language auto|tr|en` or `MOBILE_APP_SHIP_LANGUAGE=tr|en`; `auto` reads only `LC_ALL`/`LC_MESSAGES`/`LANG` and cannot infer conversational language. Pass the explicit `--language` that matches the user when you invoke or quote human output. `--json` output is never localized.

Before handing work back, run:

```bash
bash scripts/validate-playbook.sh
```
