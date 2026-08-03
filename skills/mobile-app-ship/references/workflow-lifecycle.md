# Shipping Workflow and Phase Router

Follow phases in order, but execute only scope that the SPEC needs. At each phase, load the named references before acting. Keep `DECISIONS.md` plus exactly one progress record (`PROGRESS.md` guided or `STATUS.json` autonomous).

## Independent platform lifecycle

Track iOS and Android independently through `SCOPED`, `IMPLEMENTING`, `LOCALLY_VERIFIED`, `DISTRIBUTION_READY`, `ARTIFACT_BUILT`, `UPLOADED`, `STORE_PROCESSED`, `DISTRIBUTED`, `DEVICE_VERIFIED`, `SUBMISSION_READY`, `SUBMITTED`, `IN_REVIEW`, `APPROVED`, `RELEASE_AUTHORIZED`, and `RELEASED`. A blocker is an overlay, not a state. Advance one state at a time with evidence; follow [state-evidence.md](state-evidence.md).

Upload, tester distribution, review submission, and public release are separate external mutations and separate action/evidence records. Each requires an exact, single-use approval and consumed gate. Selected onboarding scopes are future intent only. A successful upload proves neither distribution nor submission.

## Phase 0 — Guided setup

**Load:** [setup-readiness.md](setup-readiness.md); load [human-gates.md](human-gates.md) for each gated account/browser/device action.

Silently scan toolchain, accounts, disk, and signing readiness. Start applicable Apple enrollment/app-record and Play closed-test clocks immediately. Ask before installs and all account/payment/key changes. Fix approved agent-owned gaps, verify each success state, and continue work not blocked by Human gates.

## Phase 1 — Idea and scope

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 1.

Ask one product question at a time. Let the user decide scope, name, platforms, monetization, languages, design direction, and account architecture. Write `SPEC.md` and record decision rationale. Do not begin implementation with unresolved trust-boundary or monetization assumptions.

## Phase 2 — Design

**Load:** [design-rules.md](design-rules.md); load [quality-compliance.md](quality-compliance.md) § Accessibility.

Understand audience and use case, ask design-direction questions, produce an app-specific brief, obtain approval, and translate the approved direction into theme tokens/components. Audit screenshots against the anti-slop bar. Resolve assets, licenses, onboarding, haptics, paywall, and visual states before calling design complete.

## Phase 3 — Flutter scaffold

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 3 and [localization.md](localization.md) § Foundation.

Create the smallest project/dependency set, write ignore rules before credentials, decide iOS device family, generate icon/splash, establish localization parity, and run/inspect the scaffold.

## Phase 4 — Firebase

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 4, [security-cost.md](security-cost.md), and [human-gates.md](human-gates.md) for console toggles/billing.

Configure only required Firebase products. Establish auth, rules/index files, Functions/Storage when needed, secret handling, and Android fingerprint timing. Prove auth end to end; configuration API success alone is insufficient.

## Phase 5 — App architecture

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 5, [design-rules.md](design-rules.md) § onboarding/paywall, and [localization.md](localization.md).

Choose one state system, default anonymous-first, persist every user-created record, prevent auth failure cascades, build only required services/screens, and add working legal surfaces.

## Phase 6 — Backend, rules, and indexes

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 6 and [security-cost.md](security-cost.md). Load [admin-panel.md](admin-panel.md) only for Phase 6.5 triggers.

Enforce the AI trust boundary, consent, server authorization, atomic credits/idempotency, least-privilege rules, indexes, account deletion, and evidence from deployed/emulated checks.

## Phase 6.5 — Conditional administration

**Load only if triggered:** [admin-panel.md](admin-panel.md).

Ask which external management operations are actually needed. Use server-controlled roles and auditable writes. Treat temporary privileged operations as approved, narrowly scoped, verified, and deleted.

## Phase 7 — Monetization

**Load when purchases or ads exist:** for purchases load [revenuecat-implementation.md](revenuecat-implementation.md), [revenuecat-mcp.md](revenuecat-mcp.md), [security-cost.md](security-cost.md) § unit economics, [design-rules.md](design-rules.md) § paywall, and [human-gates.md](human-gates.md) for dashboard/store credentials. For ads load [admob-implementation.md](admob-implementation.md).

Model unit economics. Create each App Store/Play product and read its store state back **before** creating the corresponding RevenueCat catalog object; then wire entitlement → offering → package → current offering. Configure the SDK independent of auth, securely grant value, and physically test purchase/restore/relaunch/deletion. If ads are in scope, integrate UMP consent-first initialization, test with sample IDs, and gate real IDs behind a Human Gate.

## Platform-requirements checkpoint

**Load:** [quality-compliance.md](quality-compliance.md).

Before release signing/builds, revalidate current iOS SDK/privacy-manifest and Android target/closed-test requirements from official sources. Do not rely on source-playbook dates or fixed versions.

## Phase 8 — iOS signing

**Load when iOS ships:** [ios-app-store.md](ios-app-store.md) § Phase 8; load [siwa-gates.md](siwa-gates.md) if SIWA exists and [human-gates.md](human-gates.md) for keys/certificates/APNs.

Configure explicit capabilities, Runner-only signing, entitlements, privacy/permission metadata, archive evidence, and physical-device auth/push checks.

## Phase 9 — App Store Connect

**Load when iOS ships:** [ios-app-store.md](ios-app-store.md) § Phase 9, [store-submission.md](store-submission.md) § listing mechanics, [design-rules.md](design-rules.md) § store naming, and [aso.md](aso.md) for metadata/ASO planning.

Create/import localized metadata and store objects, publish legal/support pages, complete rating/rights/privacy/availability/review information, and read the resulting API/store states.

## Phase 10 — Android signing and Google Play

**Load when Android ships:** [android-play.md](android-play.md), [human-gates.md](human-gates.md), [quality-compliance.md](quality-compliance.md), and [aso.md](aso.md) for listing/ASO planning.

Create signing configuration, complete the manual first upload and Play App Signing SHA handback, wire service-account access, listing/monetization/Data Safety/declarations, run the current closed-test requirement, then apply for production access.

## Phase 11 — Build and distribution

**Load:** [stability-gate.md](stability-gate.md) **before first upload**; then [ios-app-store.md](ios-app-store.md) § Phase 11 for iOS or [android-play.md](android-play.md) for Android.

Run the pre-upload half of the stability gate, bump the build, produce and inspect the signed artifact, then request an exact upload approval. Upload once and poll until the store accepts processing. Request a separate exact distribution approval. After TestFlight/Play distribution, run the distributed-artifact half on a physical device before `DEVICE_VERIFIED`; upload-time checks cannot prove distributed behavior.

## Phase 11.5 — Store screenshots

**Load:** [ios-app-store.md](ios-app-store.md) § Phase 11.5 for iOS and [android-play.md](android-play.md) § Store listing for Play; also [design-rules.md](design-rules.md) § screenshots and [aso.md](aso.md) § visual assets.

Capture real localized UI, create truthful on-brand assets for every required device family, verify current dimensions, upload, and read media state back.

## Phase 12 — Localization

**Load:** [localization.md](localization.md), [store-submission.md](store-submission.md) § locale mappings, and [aso.md](aso.md) § localization.

Keep every ARB key and store locale aligned, generate localization code, render each locale, test longest strings and RTL, and verify imported listing fields/URLs.

## Phase 13 — Iteration

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 13 and [pitfalls.md](pitfalls.md) when a known symptom appears.

Make one scoped change, run relevant checks, deploy/upload only when required and approved, bump build numbers, and record actual state/evidence.

## Phase 14 — Conditional modules and quality

**Load:** [flutter-firebase.md](flutter-firebase.md) § Phase 14. Load each linked specialist reference only when its trigger is true.

Evaluate UGC, demo access, AI-content disclosure, App Check/abuse, analytics, deep links, notifications, tests, CI/CD, UX states, and release management. Preserve conditional safety/cost modules; skip only with a recorded reason.

## Phase 15 — Pre-submission review

**Load:** [pre-submission-review.md](pre-submission-review.md), [store-submission.md](store-submission.md), [human-gates.md](human-gates.md), and [aso.md](aso.md) § pre-submission ASO checks.

Run every applicable item against the actual app and emit one PASS/FAIL line per item. Fix every FAIL before submission. Enforce the IAP attach hard stop before and after submit. Submission and publication each need a separate exact single-use consumed gate and read-back; never infer release authority from submission or store approval.

## Exception and terminal states

Use `ACTION_REQUIRED` when review, metadata, agreement, credential, or store state needs intervention. After correction, return to the earliest invalidated ordered state: metadata-only work can return to `SUBMISSION_READY`; a binary change returns to `IMPLEMENTING`. Use `WITHDRAWN` for an explicitly withdrawn version, `SUPERSEDED` when a newer artifact/version replaces it, and `ABANDONED` only when the target is intentionally stopped. These states do not imply success and never advance the other platform.

## Rejection trigger

**Load immediately:** [store-submission.md](store-submission.md) § Rejection and [pitfalls.md](pitfalls.md) for the exact symptom.

Read the full reviewer message, classify it, set `ACTION_REQUIRED`, reply in Resolution Center, complete human gates while the version is editable, upload a new binary only for binary changes, resubmit with approval, and verify store/IAP state again.
