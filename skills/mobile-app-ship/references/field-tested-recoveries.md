# Field-Tested Recoveries

This is a derived public ledger, not a transcript. Its material comes from two complete shipping sessions (Session 1: toolkit build/autoresearch; Session 2: real Flutter app from store records through TestFlight and submission prep) and from the current references and validator. Runtime/tool versions drift: treat every historical observation as a starting hypothesis. Runtime discovery (`--help`, `asc search`, `tools/list`, schemas) and vendor read-back remain authoritative over anything recorded here.

Repeated events across the two sessions are merged into single ledger rows; each row names the generic source labels only (for example `Session 2 / ASC recovery`), never private identifiers. This ledger is a derived, public reference: current runtime and vendor schemas always override historical observations recorded here.

## How to use this ledger

For every failure: stop blind retry; classify; inspect state; make one targeted change; obtain fresh scoped approval for any external mutation; apply once; read back; record sanitized evidence. Distinguish three classes:

- **Expected negative state** — the error is the current vendor state: availability not found before creation, `MISSING_METADATA` before metadata, empty inventory before create. Verify and continue the sequence; never recreate blindly.
- **Environment/tooling failure** — transport, versions, local layout, timeouts. Fix locally; a retry is allowed only after state inspection, at most once per deliberate warm-cache retry.
- **Real product/store failure** — vendor-side data or policy blocker: missing declaration, wrong platform, bad asset. Fix the named state, read back, then continue.

Worked classifications from the sessions:

- Expected negative: A11 availability/price read returned not-found before the resource existed; the sequence continued after the create/read-back.
- Environment: X1 CLI-UI subcommands timed out with no runtime snapshot; the stdio MCP path after `tools/list` succeeded.
- Product/store: A5 submission preflight found missing age-rating/privacy declarations that doctor/validate had not surfaced.

### Timeout recovery loop

1. Mark the action `outcome_unknown`; never infer from exit code or a timed-out tool report.
2. Inspect vendor state (or the expected artifact on disk for local builds) before anything else.
3. Classify: present and complete, absent (failure), or unknown.
4. For local builds only: at most one deliberate retry may benefit from warmed caches.
5. For external mutations: request a fresh scoped approval per retry; apply once; read back.

### Decision table

| Observed class | First action | Retry policy | Evidence to record |
|---|---|---|---|
| Expected negative state | Read the exact vendor record the error names | None; continue the sequence | Read-back plus sequence position |
| Environment/tooling | Inspect versions, transport, layout, artifact on disk | One deliberate warm-cache retry for local builds only | Artifact hash, tool versions, limitation note |
| Real product/store | Fix the named field/declaration exactly | Fresh scoped approval per retry, then read back | Vendor read-back after the fix |
| Timeout | Mark `outcome_unknown`, inspect state | Never blind; one inspected retry for local builds | State inventory plus classification |
| Infrastructure (O7) | Classify; stop repeated blind retry | Provider/model change only with user direction | Limitation note, not a shipping rule |

## Group recovery patterns

- **Setup/toolchain (S1–S12):** diagnose local-first; resolve tools by explicit executable and environment variables, never by editing global PATH or profiles; record environment limitations and never silently alter the target; keep artifacts out of the tree because the validator enforces it.
- **ASC (A1–A12):** never trust remembered syntax or echoed intent; read back immediately after every create/update; a bare 409 usually means the error names the current state — read `associatedErrors` and fix exactly that.
- **RevenueCat (R1–R5):** transport and auth errors are client-side until proven otherwise; re-auth only through the supported client; catalog wiring stays capability-gated and read-only until exact approval.
- **Monetization (M1–M2):** generated ad-SDK sources are not app source; privacy and binary changes from adding or removing ads require a fresh build/upload/privacy read-back chain.
- **Firebase (F1–F3):** list APIs converge late, so use project-scoped reads; Hosting readiness means deployed HTTPS 200s, not project creation or list convergence.
- **XcodeBuildMCP (X1–X6):** rendered-UI evidence requires the full build/launch/snapshot/screenshot sequence with fresh snapshots; signing is a separate pre-requirement the MCP does not create; archive success is not store processing.
- **Android runtime (D1–D2):** emulator exit codes are non-evidence; verify with boot poll, `am start -W`, `pidof`, resumed activity, and logcat; physical-device-only claims stay unverified.
- **Workflow/agent (O1–O7):** approval is exact single-use gates, not blanket intent; tooling races are fixed with readiness waits; compressed handoffs are rejected after inspecting the real diff; infrastructure failures are not shipping rules.

## How incidents became contracts

Most durable rows are now enforced by the semantic validator's prevention contracts, so a future regression fails `validate_playbook.py` rather than reaching a store:

- A3/A4/A8 and the IAP/version paths → `store-submission.md` tokens (review-screenshots endpoint, `whatsNew` omission, platform `IOS` read-back, localization read-back).
- A6/A7/A9/X4/X6 → `ios-app-store.md` tokens (Runner-only signing, per-build encryption declaration, zero-padded upload order, querying the set before retry).
- A5 → `pre-submission-review.md` token that doctor/validate output can miss server-side blockers.
- R1/R2/R3 → `revenuecat-mcp.md` tokens (Streamable HTTP not SSE, `405`, `browser_signature_banned`).
- S7/S8/F2 → `flutter-firebase.md` tokens (UTF-8 analyze, ASCII-path mirror, never hand-create a Podfile, global `**` header rule).
- O1 → `human-gates.md` tokens (future intent only, exact single-use approval, `--check-scope`).
- S9/S11 and this ledger itself → validator-enforced structure: forbidden-artifact scan, byte-identical schema copies, required-reference routing, and the content guard that keeps the headings and guard terms above present.

## Field evidence by group

| Group | Source labels | Owning reference for the durable procedure |
|---|---|---|
| S1–S6 | Session 1 / toolchain hardening, Session 2 / Android emulator runtime | setup-readiness.md, failure-resume.md |
| S7–S12 | Session 2 / local tooling, Session 1 / validator and schema work | flutter-firebase.md, state-evidence.md, status.schema.json |
| A1–A12 | Session 2 / ASC records, screenshots, metadata, submission prep | asc-cli.md, store-submission.md, pre-submission-review.md, ios-app-store.md, pitfalls.md |
| R1–R5 | Session 2 / RevenueCat transport and catalog, Session 1 / harness research | revenuecat-mcp.md, human-gates.md |
| M1–M2 | Session 1/2 / ads integration, privacy, and no-ads rebuild | admob-implementation.md, quality-compliance.md |
| F1–F3 | Session 2 / Firebase project and Hosting deploy | flutter-firebase.md |
| X1–X6 | Session 2 / XcodeBuildMCP runtime, signing, archive | xcodebuildmcp.md, ios-app-store.md |
| D1–D2 | Session 2 / Android emulator, Session 1 / pilot | pitfalls.md, human-gates.md |
| O1–O7 | Session 1 / agent workflow and onboarding browser work | human-gates.md, harness-onboarding.md |

## Exhaustive grouped incident ledger

| ID | Area | Symptom | Root cause | Recovery | Verification | Codification status |
|---|---|---|---|---|---|---|
| S1 | Setup | Firebase CLI engine warning on unsupported Node | firebase ran under an unsupported Node version | Switch to supported keg-only Node 24/npm and invoke the explicit executable; do not globally edit PATH | Explicit node/firebase `--version` read-back | Codified in setup-readiness.md |
| S2 | Setup | Keg-only Node relink failed ("Could not symlink") | Orphaned npm symlinks from a prior install | Inspect and remove only the stale orphan symlink, then relink and verify | npm/node version and relink output | Codified in setup-readiness.md |
| S3 | Setup | `avdmanager` resolved the wrong SDK root | cmdline-tools was a symlink into the SDK destination | Use a physical copy into the missing SDK destination, not a symlink | `sdkmanager --list_installed`, `avdmanager list avd`, doctor | Codified in setup-readiness.md |
| S4 | Setup | AVD create: `Package path is not valid` | `avdmanager` resolved a different SDK root than the installed system image | Use the SDK-local `avdmanager` with `ANDROID_SDK_ROOT`/`ANDROID_HOME` set | System image present, `emulator -list-avds`, boot poll | Codified in setup-readiness.md |
| S5 | Setup | Android licenses block first build | License acceptance requires a human | Record acceptance as a separate Human gate; never auto-accept | `flutter doctor --android-licenses` green | Codified in setup-readiness.md, human-gates.md |
| S6 | Setup | First Gradle/Flutter Android build exceeded tool timeout | Cold caches, slow first build | Inspect artifact on disk; classify unknown/failure; one deliberate warm-cache retry only; never infer from exit code | Artifact exists with hash; second build passes | Codified in failure-resume.md |
| S7 | Setup | `flutter analyze` FormatException under a non-ASCII path | Analyzer chokes on Unicode path characters | Try `LC_ALL=en_US.UTF-8`/`dart analyze`, then an ASCII-path mirror; record environment limitation, do not silently alter the target | Clean analyze on the mirror; limitation noted in evidence | Codified in flutter-firebase.md |
| S8 | Setup | `pod install`: `No Podfile found` | iOS project uses SPM, not CocoaPods | Verify SPM/CocoaPods mode first; never hand-create a Podfile; `flutter pub get`, discover current `flutter build ios --config-only`, regenerate only if needed | Project mode read-back; lockfile/SPM state | Codified in flutter-firebase.md |
| S9 | Setup | `.DS_Store`/`__pycache__`/build artifacts blocked validator | Local artifacts leaked into the tree | Remove local artifacts; keep the ignore/validator guard | `validate_playbook.py` passes | Validator-enforced |
| S10 | Setup | Target was not a Git repo and lacked SPEC/DECISIONS | Target has no baseline | Preserve target files; use the target-local onboarding/state contract; never invent product docs | Decision records written; STATUS validates | Codified in harness-onboarding.md, state-evidence.md |
| S11 | Setup | Schema/validator drift: wrong status key, lifecycle jump, evidence source/time, root-vs-assets schema copies | Canonical copies diverged | Use the canonical schema and fixtures; validator rejects invalid transitions; keep root and asset schema byte-identical | `validate_playbook.py` plus valid/invalid fixtures | Validator-enforced |
| S12 | Setup | AJV strict mode: `contains`/unknown date-time format | Schema used keywords/format unsupported under strict AJV | Add explicit schema type and a portable pattern; validate valid and invalid fixtures | AJV: valid passes, invalid fails | Codified in status.schema.json |
| A1 | ASC | Remembered command groups/subcommands failed | CLI schema changed | Discover at runtime with `asc --help`, `asc search`, command help/schema; never invent syntax | Command runs and read-back succeeds | Codified in asc-cli.md |
| A2 | ASC | App record create removed/renamed; bare HTTP 409 | Volatile create path and/or existing inventory conflict | Preflight exact app inventory; verify canonical locale via current help/schema; read vendor state before retry; fresh approval per retry; do not codify volatile command names as contracts | Inventory and app read-back | Codified in asc-cli.md, pitfalls.md |
| A3 | ASC | IAP review screenshot uploaded to the wrong version-image endpoint/dimensions | Endpoint confusion (version images vs product review screenshots) | Use the product review-screenshot endpoint discovered at runtime; verify dimensions and asset state; delete a failed asset only with a gate | Product review-screenshot read-back COMPLETE; version images zero | Codified in store-submission.md |
| A4 | ASC | Metadata apply partial failure: auto-created en-US localization, non-editable v1 `whatsNew` | Default locale auto-created; first-release `whatsNew` immutable | Read back localizations; update existing records; omit `whatsNew` for v1 | Per-locale read-back | Codified in store-submission.md |
| A5 | ASC | Review doctor/validate missed server-side blockers: age rating, privacy publish, regulated-medical declaration, free pricing, iPad families | Doctor/validate is not a submit gate | Run the direct pre-submission checklist and read version `meta.associatedErrors` | Checklist passes; associated errors empty | Codified in pre-submission-review.md, pitfalls.md |
| A6 | ASC | Screenshot dimension mismatch from wrong simulator | Captured on the wrong device family | Use the exact device-family dimensions and re-capture | Dimensions/hash read-back | Codified in ios-app-store.md |
| A7 | ASC | Screenshot fan-out timeout with partial completion | Parallel uploads with unknown completion | Mark unknown; query each set; create a missing-file recovery manifest; upload only missing set/files; read back completion/order/checksums | Per-set read-back with zero-padded order | Codified in ios-app-store.md |
| A8 | ASC | Review draft silently had the wrong platform | Create flag echoed intent | Read platform back immediately; correct the draft before adding items; never trust the create flag | Submission read-back platform `IOS` | Codified in store-submission.md |
| A9 | ASC | Build encryption declaration missing (`MISSING_EXPORT_COMPLIANCE`) | Export compliance undeclared | Declare per build and read back | Build update read-back clears the flag | Codified in ios-app-store.md |
| A10 | ASC | Web session expired for ASC web commands | Cached `asc web` auth expired | Discover current auth/login help; interactive re-auth under a Human gate; read vendor state before planning/applying | Re-auth plus vendor read-back | Codified in asc-cli.md |
| A11 | ASC | App/IAP availability or price read returned not-found before creation | Resource does not exist yet (expected sequence state) | Treat as expected; do not recreate blindly; create/read the product before schedules/availability | Create then read-back | Codified in store-submission.md, pitfalls.md |
| A12 | ASC | iOS-intent bundle ID read back `UNIVERSAL` | Platform attribute semantics differ from intent | Verify identifier/name and live semantics, not that attribute alone | App read-back | Codified in asc-cli.md |
| R1 | RevenueCat | SSE client received 405 on the Streamable HTTP endpoint | Transport mismatch, not an auth error | Use the supported native/browser OAuth MCP transport; inspect `tools/list` | `tools/list` plus a read call | Codified in revenuecat-mcp.md |
| R2 | RevenueCat | 403 Cloudflare `browser_signature_banned` | Inline client signature banned | Do not retry the same inline client; switch to a supported client/harness or a Human gate | Transport change plus read-back | Codified in revenuecat-mcp.md |
| R3 | RevenueCat | 401 invalid token | Stale stored session | Use supported OAuth re-auth/refresh/login only; never print/paste tokens or hand-edit keychain/refresh posts | Re-auth plus vendor read-back | Codified in revenuecat-mcp.md |
| R4 | RevenueCat | Create read-back parser assumed one-line JSON; output is field blocks | Parser/schema mismatch, not a missing/duplicate create | Parse according to the live schema/format before concluding; never repeat the mutation | Parsed read-back matches the created resource | Ledger-only (parser hygiene) |
| R5 | RevenueCat | Paywall offering association unavailable in the selected harness (draft `offering_id` null) | Capability/approval boundary, not a failure | Classify as read-only/Human-gate limitation; do not infer meaning of the null or publish without exact vendor capability/approval | Relationship read-back plus pending gate | Codified in revenuecat-mcp.md, human-gates.md |
| M1 | Monetization | Whole-project Flutter analysis reported duplicate ad-SDK/vendor-source errors after an SPM-generated copy appeared under `build/` | Generated dependency sources polluted the analysis scope | Do not edit generated files; exclude generated build output, clean, rerun app/lib analysis separately | Clean lib analysis plus generated-source limitation | Codified in admob-implementation.md |
| M2 | Monetization | Removing an ads SDK appeared to be only a metadata change | Ads SDK changes the binary, privacy posture, and dependency graph | Remove code/dependency, clean/rebuild/sign/upload, then re-apply and publish App Privacy as a separate chain | New build/privacy/vendor read-back | Codified in admob-implementation.md |
| F1 | Firebase | `projects:list` eventual-consistency lag after create while project-scoped reads work | List converges slower than the scoped API | Poll/re-query once; never recreate solely from list absence | Project-scoped Hosting/apps read-back | Ledger-only (listed in flutter-firebase.md flow) |
| F2 | Firebase | Hosting clean-URL security header glob did not apply | Header pattern too narrow | Use and verify the global `**` rule; local serve first, then HTTPS/HTTP 200 read-back with headers | Curl headers plus HTTP 200 | Codified in flutter-firebase.md |
| F3 | Firebase | Project create/list convergence is not Hosting readiness | Readiness differs from deployed state | Use project-scoped reads for the deploy target; read deployed URLs after deploy | HTTPS 200 on deployed URLs | Codified in flutter-firebase.md |
| X1 | XcodeBuildMCP | CLI UI subcommands/daemon/snapshot/screenshot timed out or returned no runtime snapshot | CLI UI transport or daemon state | Inspect boot/process state; prefer stdio MCP after `tools/list`; classify unknown; do not trust path/exit alone | `tools/list` plus a runtime snapshot | Codified in xcodebuildmcp.md |
| X2 | XcodeBuildMCP | `SNAPSHOT_EXPIRED` after navigation/timeout | Element refs stale after a UI change | Boot/verify the simulator; take a fresh snapshot before tap/touch and after timeout/navigation; use the live screen hash only if the schema exposes it | Fresh snapshot, tap, re-snapshot | Codified in xcodebuildmcp.md |
| X3 | XcodeBuildMCP | Simulator install/launch cannot prove UI | Process-level evidence only | Run the build/test/launch/snapshot/screenshot sequence and read the actual rendered UI | Snapshot text/elements plus screenshot | Codified in xcodebuildmcp.md |
| X4 | XcodeBuildMCP | Global signing profile on Pods/SPM targets caused archive failure | Signing applied too broadly | Sign the Runner target only; use the correct Distribution profile/capability; inspect archive/IPA | codesign/entitlements read-back | Codified in ios-app-store.md |
| X5 | XcodeBuildMCP | Signing identities/profiles absent at archive time | XcodeBuildMCP does not create signing | Inspect and prepare signing separately | `find-identity` plus profile decode | Codified in SKILL.md, ios-app-store.md |
| X6 | XcodeBuildMCP | Archive/IPA success is not store processing/TestFlight/device evidence | Local artifact differs from vendor state | Read bundle ID, version/build, team/profile/entitlements, encryption; then read separate vendor state | Store build inventory read-back | Codified in ios-app-store.md, state-evidence.md |
| D1 | Android | Emulator install/monkey exit 251 or silent launch | Exit code is non-evidence | Boot-poll, install, `am start -W`, `pidof`, resumed activity, logcat; simulator/emulator is not physical-device evidence | Resumed activity plus clean logcat | Codified in pitfalls.md |
| D2 | Android | Physical-device purchase/restore/notification remains unverifiable | No physical device available | Keep the limitation recorded; never mark device verified from emulator evidence | Limitation recorded in evidence | Codified in SKILL.md, human-gates.md |
| O1 | Workflow | Blanket/master/one-shot approval model conflicted with immutable single-use gates | Approval model mismatch | Use a non-authorizing plan acknowledgement plus a separate consumed gate for every attempted mutation, including failed/unknown | Gate states consumed per action | Codified in human-gates.md |
| O2 | Workflow | Browser textarea/input `type` property runtime error | Wrong element guard | Guard `HTMLInputElement` versus textarea and browser-smoke it | Browser smoke test passes | Ledger-only (tooling) |
| O3 | Workflow | Localhost onboarding server race/connection refusal | Server not ready when client connects | Wait for server readiness; save/read back; no vendor mutation | Readiness plus save/read-back | Ledger-only (tooling) |
| O4 | Workflow | Headless Chrome dump-dom hung | Unbounded process | Capture DOM to a file with a bounded process timeout and terminate; do not lose the captured DOM | DOM file plus bounded exit | Codified in test_onboarding_browser.py |
| O5 | Workflow | Clone does not install tools/MCP/auth | False assumption about installs | Onboarding/doctor/bootstrap dry-run must precede provider auth and installs | Doctor/bootstrap dry-run | Codified in harness-onboarding.md |
| O6 | Workflow | Worker over-compressed guidance or stopped early | Handoff compression | Inspect the real diff, test counts, and required tokens; reject the incomplete handoff; do not codify as product behavior | Diff plus test evidence reviewed | Ledger-only (process) |
| O7 | Workflow | Model/provider region or overload failures | Infrastructure | Classify; stop repeated blind retry; change provider/model only with user direction; this is not a shipping rule | State check before any re-run | Ledger-only (infrastructure) |

## Durable invariants

- **Vendor read-back** — a mutation is verified only by reading the vendor state, never by the tool's own report or exit code.
- **Exit code is not proof** — process exit does not prove upload, processing, distribution, submission, or release.
- **Timeout is unknown** — a timeout becomes `outcome_unknown`; inspect vendor state before any retry.
- **Exact single-use approvals** — one consumed gate per attempted external mutation, including failed and unknown attempts.
- **Runtime discovery** — `--help`, `asc search`, `tools/list`, and live schemas override remembered syntax.
- **Direct tool ownership** — use each provider's own tool; no wrapper, proxy, or invented adapter.
- **Secret-safe state** — credentials, tokens, and key material never enter Git, target state, or chat.
- **Simulator/device separation** — simulator and emulator evidence never substitutes for physical-device evidence.
- **Public-release separation** — upload, distribution, submission, and release stay independent actions with independent gates.

## Codification status legend

The `Codification status` column says where the durable rule now lives. `Codified in <file>` means the current reference owns the procedure and this row is the field-tested history behind it. `Validator-enforced` means the semantic validator (`validate_playbook.py`) fails without the behavior. `Ledger-only` marks environment, parser, process, or infrastructure observations that are real but not reusable product policy; they stay here so they are not mistaken for vendor behavior.

## Sanitization and placeholder convention

This ledger is public, so every edit must keep it free of session specifics. Use only these generic placeholders for anything that identifies a real deployment: `<target-app-dir>`, `<bundle-id>`, `<product-id>`, `<project-id>`, `<build-number>`, `<simulator>`, `<package-name>`. Never include personal names, email or phone values, home paths, vendor UUIDs or numeric account/app IDs, dates tied to the user, credentials, tokens, private key material, raw URLs containing secrets, or app-specific names. Cite generic phase/source labels only (for example `Session 2 / ASC recovery`), never raw session line dumps or the source JSONL paths.

## Intentionally excluded noise

These remain session evidence but are not reusable shipping policy, so they are excluded: transient context-mode workspace blocks, disk I/O and FTS errors, provider overload/fetch failures, Apple documentation 404/UA blocks, shell/edit/extraction mistakes, expected negative tests, raw App Review IDs and status values, and any app-specific or private data. Do not reintroduce raw session line dumps or private identifiers into this ledger.

## Regression checklist

| Category | Current reference | Validation |
|---|---|---|
| State/evidence/gate model | state-evidence.md, human-gates.md | `python3 skills/mobile-app-ship/scripts/validate_playbook.py` (semantic validator) |
| Timeouts/resume | failure-resume.md | Same validator plus fixtures |
| Tool transport/auth | revenuecat-mcp.md, asc-cli.md, xcodebuildmcp.md, harness-onboarding.md | Same validator; tool contracts |
| Store/submission | store-submission.md, pre-submission-review.md, ios-app-store.md | Same validator; prevention contracts |
| Platform/Android | android-play.md, pitfalls.md | Same validator |
| Whole toolkit | README.md, AGENTS.md | `bash scripts/validate-playbook.sh` (offline tests + semantic) |
| Whitespace/conflict hygiene | — | `git diff --check` |
| Guard-term presence | this file, SKILL.md | `rg -n 'Field-Tested Recoveries\|browser_signature_banned\|SNAPSHOT_EXPIRED\|never hand-create a Podfile\|single-use\|read back' skills/mobile-app-ship/references/field-tested-recoveries.md skills/mobile-app-ship/SKILL.md` |
| Schema/fixtures | status.schema.json, tests/fixtures/ | Optional AJV over root fixtures; Python validator is authority |
| Links/hygiene | all references | `git diff --check`; validator markdown-link and secret/local-path scans |

This document is public. It must never contain raw session dumps, private identifiers, or credential-shaped values; current runtime and vendor schemas always override historical observations recorded here.
