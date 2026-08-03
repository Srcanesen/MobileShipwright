# asc CLI

Use `asc` only for supported App Store Connect operations. It does not enroll a team or make legal/account decisions.

## Live schema first

Run `asc --help`, `asc search <topic>`, and the target command's `--help` before every action. These examples were checked against installed `asc` 3.1.3; re-discover volatile schemas and permissions at execution time.

```bash
asc auth status --validate
asc metadata apply --app "$ASC_APP_ID" --version "$VERSION" --dir ./metadata --dry-run
asc builds upload --app "$ASC_APP_ID" --ipa path/to/app.ipa --dry-run
asc release stage --app "$ASC_APP_ID" --version "$VERSION" --build "$BUILD_ID" --copy-metadata-from "$PREVIOUS_VERSION" --dry-run
asc publish appstore --app "$ASC_APP_ID" --ipa path/to/app.ipa --version "$VERSION" --submit --dry-run
asc validate --app "$ASC_APP_ID" --version "$VERSION" --platform IOS
asc review doctor --app "$ASC_APP_ID" --version "$VERSION"
```

Dry-run is preflight, not mutation evidence. Read back the vendor state after every approved action. Gate any command whose help indicates a reservation or state change. In particular, `builds upload --dry-run` help says it reserves upload operations: inspect the result and do not treat it as harmless proof of a no-op. As discovered (volatile, not a contract): a bundle ID created with iOS intent may read back platform `UNIVERSAL`; verify the exact identifier/name and live semantics instead of treating that attribute alone as a mutation failure. As discovered (volatile, not a contract): cached `asc web` sessions can expire; on session-expired/auth-required output, do not blind-retry. Discover current auth/login help, re-authenticate interactively under a Human gate, then re-read vendor state before planning or applying.

## Separate approval boundaries

Keep **upload**, **distribution**, **review submission**, and **release** as separate actions/evidence. Each operation needs its own exact single-use approval; onboarding scopes are future intent only. Do not use a combined workflow to bypass a gate. For each operation: inspect current vendor state, plan, apply once, read back vendor state, and retain that read-back as evidence. Treat a timeout as `outcome_unknown`; inspect state before retrying.

Use the official [asc site](https://asccli.sh/) and [source documentation](https://github.com/rorkai/App-Store-Connect-CLI).