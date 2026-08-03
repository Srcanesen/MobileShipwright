# Product, Flutter, Firebase, and Iteration

Load for Phases 1, 3, 4, 5, 6, 13, and the conditional module scan. Use [design-rules.md](design-rules.md) in Phase 2, [localization.md](localization.md) from Phase 3 onward, and [security-cost.md](security-cost.md) whenever a backend or paid call exists.

## Phase 1 — Product scope and SPEC

Ask one question at a time:

1. What should the app do or produce, and for whom?
2. Which core screens and optional social/UGC features are required?
3. Is it free, ads, subscriptions, consumable credits, or a combination?
4. Ship iOS, Android, or both?
5. What brand and bundle/package identifier should be used?
6. Which AI provider/model is suitable, what user data leaves the device, and what does one action cost?
7. Which languages and account model are required?

Push back on generic category-only names. The user owns scope, name, price, design, language, and platform decisions. Write `SPEC.md` with the product outcome, audience, screens, model/provider, data flow, monetization, platforms, account architecture, languages, and explicit non-goals. Record rationale in `DECISIONS.md` and treat the SPEC as the scope boundary.

## Phase 3 — Flutter foundation

1. Create the project with the approved organization, package IDs, and device-family choice.
2. Add only packages required by the SPEC. Verify current package names and APIs before adding them; remove unused auth/push packages before archive.
3. Use a simple feature-oriented layout such as `lib/app`, `lib/features`, `lib/services`, `lib/models`, `lib/widgets`, and `lib/l10n`; do not scaffold speculative layers.
4. Write `.gitignore` before credentials/generated configuration. Initialize Git and commit a working scaffold.
5. Add the approved theme tokens, launcher icon, splash, accessibility defaults, and localization foundation. Verify the 1024×1024 iOS icon has no alpha.
6. Run the empty app. Require `flutter analyze` with zero errors and inspect a real simulator/device screenshot. If a shell locale causes Unicode analyzer output to fail, first rerun with a UTF-8 locale (for example `LC_ALL=en_US.UTF-8 flutter analyze`). If Flutter still throws before diagnostics from a Unicode-containing project path, run `dart analyze` there and independently run `flutter analyze` from an ASCII-path mirror of the same sources; record the path limitation and matching source hashes. Do not alter source encoding or move the user's project to hide it.

Decide phone-only versus universal iOS support before the first build because it changes required screenshot families. Add haptics centrally for meaningful taps, selections, page changes, and success/error moments only where the platform convention supports them.

## Phase 4 — Firebase setup

Use the current FlutterFire/Firebase CLI flow; a typical sequence is:

```bash
firebase projects:list
firebase use --add
dart pub global activate flutterfire_cli
flutterfire configure --project=PROJECT_ID
firebase init firestore functions storage
```

`projects:list` may lag immediately after project creation while project-scoped API reads already work; re-query after a short delay before concluding a project is missing, and never recreate one based only on temporary list absence.

Initialize only used products. Select the current supported Functions runtime after checking Firebase documentation. Link an approved open billing account when deployment requires it; verify project/account ownership before linking.

Auth providers and some attestation/push configuration are Human gates; route to [human-gates.md](human-gates.md). For Android Google sign-in, add local signing SHA-1/SHA-256 now and schedule the Play App Signing SHA step after first Play upload; see [android-play.md](android-play.md).

A fresh CLI-created project can lack Identity Platform auth configuration. If reads/PATCH return `CONFIGURATION_NOT_FOUND`, initialize auth first with the documented Identity Toolkit initialization endpoint, then enable only required providers. Include the current quota-project header when the API requires it. Verify end to end after the app runs: an anonymous-first app must create/read an auth user, not merely return a successful configuration request.

Store AI keys with server-side secret management. Never put provider secrets in Flutter assets, Dart defines, Remote Config, or Firestore readable by clients.

## Phase 5 — State, persistence, and app flow

- Pick one state-management approach and keep it. Do not mix Provider and Riverpod without a demonstrated need.
- Default flow: splash → visual onboarding → paywall when monetized → home. Add login only for durable cross-device identity. Use silent anonymous auth otherwise.
- If linking social credentials onto an anonymous user, preserve that user's data and purchase identity. On iOS, apply current Guideline 4.8 before adding third-party primary-account login.
- Persist every user-created record to Firestore/Storage. In-memory state is a cache, not the source of truth. Test create → kill → relaunch.
- Keep network services independent enough that an auth delay does not leave offerings, stores, and loading states permanently unresolved.
- Use a DB-driven model/catalog/pricing document only when operators must change it without a release.
- Put working Privacy and Terms entries in Settings/Profile and the paywall. Follow the canonical legal-surface rules in [ios-app-store.md](ios-app-store.md).

Typical services can include auth/current-user, generation, RevenueCat, notifications, locale, and social only if their features exist. Do not create unused services or screens.

## Phase 6 — Backend, rules, indexes

Implement the smallest server boundary that enforces trust:

1. Authenticate and authorize a generation request.
2. Check consent, quota/credits, input bounds, model allowlist, and idempotency.
3. Deduct credits atomically with the operation or reserve/refund safely.
4. Call the provider server-side; use polling/webhooks for genuinely long jobs.
5. Persist result metadata and owned Storage paths; do not expose provider secrets or arbitrary endpoints.
6. Keep a transaction ledger for credit mutations and an audit trail for privileged changes. If welcome credits exist, grant them once through an idempotent server record with App Check/rate-limit defenses; never trust a resettable client flag as the only guard.

Write least-privilege Firestore/Storage rules per collection and test deny cases in the emulator. Create a composite index for each actual `where + orderBy` query. Do not copy permissive rules to make a missing document readable; express ownership without dereferencing absent data and test both absent and foreign-owned cases.

If social/UGC exists, make share/vote actions idempotent, aggregate server-side, and add report/block/moderation from the conditional modules below. Use push for user-valued critical events; keep low-value social noise in-app.

Implement confirmed in-app account deletion across owned Firestore documents, Storage objects, backend records, and Firebase Auth. Clear local state, create a fresh anonymous identity if the app requires one, set onboarding false, and return to clean first launch. Test it on a physical device.

Deploy only with approval, then verify deployed rules/functions/index state rather than trusting the CLI exit code. For Firebase Hosting clean URLs, put required security/cache headers in a global `**` rule as well as any extension-specific rule; read the deployed headers back from clean and extension URL forms.

## Phase 13 — Iteration loop

For each request: update SPEC/DECISIONS if scope changes → make one focused change → analyze/test → deploy backend only if required → bump build when uploading → upload only with approval → record evidence and next owner. Use Firestore for approved runtime-configurable catalog/text changes; do not use it to bypass store review for binary behavior.

## Phase 14 — Conditional modules

Evaluate every trigger; keep a skipped item out of the build and record why.

| Trigger | Required module |
|---|---|
| Public UGC/social | Report, block, filtering, moderation queue, removal process within 24h, zero-tolerance terms, AI-content disclosure when applicable |
| Login-gated review path | Review notes plus working demo account or exact SIWA access instructions |
| Backend/paid AI | App Check after registration/testing, server authz, rate limits/quotas, budget alert and provider-spend monitoring |
| Subscriptions/credits | Paywall placement, restore, price/duration/legal visibility, optional experiment only when measurement is requested |
| Measurement requested | Minimal activation/conversion events such as signup, first core action, paywall view, purchase, share |
| Sharing/invites | Universal Links/App Links to the exact in-app destination |
| Notifications | APNs key for iOS, token lifecycle, permission after the first valuable moment |
| Critical/complex flow | Widget/integration coverage plus Firestore Rules emulator tests |
| Frequent/team releases | CI/CD with protected signing credentials and explicit publication approval |
| Every release | Loading/empty/error/offline states, build-number bump, natural release notes, staged/phased rollout where appropriate |

Load [admin-panel.md](admin-panel.md) only for external operations or privileged one-off data work.
