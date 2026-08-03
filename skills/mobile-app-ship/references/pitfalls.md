# Pitfalls — Known Silent Failures

Add to this table when something costs ≥15 min, the symptom lied about the cause, and you confirmed the root cause.

## Build/version hygiene

| Problem | Fix |
|---|---|
| **Dependency changes require clean build** | Adding/removing a pod → `flutter clean` + `rm -rf ios/Pods ios/Podfile.lock` + pod reinstall. Pure Dart changes skip this. |
| **Bump build number every upload** | `pubspec.yaml`: `1.0.0+1`, `+2`, `+3`… |
| **Disk fills up when iterating** (~10-15 GB per archive) | Clear `~/Library/Developer/Xcode/DerivedData/*` and `~/Library/Developer/Xcode/iOS DeviceSupport/*`. |
| **App icon rejected: has alpha channel** | 1024×1024 App Store icon must have **no alpha**. `flutter_launcher_icons` with `remove_alpha_ios: true`. Verify: `sips -g hasAlpha Icon-1024.png`. |
| **`pod install` says no Podfile** | Verify whether Flutter uses Swift Package Manager first; do not hand-create a Podfile. Run `flutter pub get`, discover current `flutter build ios --config-only` support, and regenerate project configuration before retrying — and only if CocoaPods is actually required. |

## Android SHA timing

Google Sign-In works in debug but fails after a Play upload (`DEVELOPER_ERROR` / statusCode 10). Play re-signs the app with Google's App Signing key. Add the **Play App Signing** SHA-1 AND SHA-256 to Firebase Console (on top of local `signingReport` SHAs). Only available after first upload + Play App Signing enrolment. Firebase applies fingerprints immediately.

## FCM / APNs / push token

iOS push fails silently on two bugs:
1. **APNs auth key must be UPLOADED** to Firebase Console → Cloud Messaging. Downloading the .p8 is not enough.
2. FCM token must be saved to `users/{uid}.fcmTokens` on **every launch** + on `onTokenRefresh` + when auth becomes available. Not only inside the sign-in handler — persisted-session users never re-run sign-in. Push fails on the Simulator (no APNs); test on a physical device.

## Offline-error diagnostic: the "saved offline" lie

A write that throws a synchronous exception (commonly `StateError` because `uid` is null) with a broad `catch` that labels it "offline" is misleading. **Firestore does not throw when offline — it queues the write to cache.** A thrown write error is never an offline condition.

**Fix:** show "offline" copy only for a genuine offline signal (`code == 'unavailable'`). Surface thrown errors with their real cause. Grep every "offline"/"çevrimdışı" branch and confirm it hangs off a real offline check, not a bare `catch`.

## Common pitfall table

| Problem | Fix |
|---|---|
| **Purchase completes but credits never arrive** | After SDK success, invoke the authenticated server reconciliation in `revenuecat-implementation.md`; server verifies current transaction/entitlement and idempotency before granting. Do not trust `{productId}` or use webhook-only delayed delivery. |
| Subscription price/trial mutation is unsupported or rejected by the current tool/account | Discover current `asc` support and role access. If parity is absent, prepare exact values and open a scoped Human gate; read the store state back afterward. |
| **Apple Sign In not working** — any symptom | Walk the five silent gates in `siwa-gates.md` in order. Do not guess. |
| **ASC review submit done but stuck at "Ready For Review"** | Finalizing is a separate step: `PATCH /v1/reviewSubmissions/{id}` with `attributes.submitted=true`. |
| **Resubmit after rejection → version not in valid state (30+ min)** | Old submission still holds the version hostage. Cancel it (`canceled=true`, wait for COMPLETE), create fresh submission. |
| **Paywall shows "plans could not load" / empty offerings on real device** | `Purchases.configure` is gated behind `uid != null`. Configure it at launch without a uid; call `logIn` later when auth resolves. |
| **Data screen spins forever on loading indicator** | A store that starts `loading = true` and has a guard `return` before clearing it. Fix: start `loading = false`, guard with a `_bound` flag. |
| **Modal/dialog action silently no-ops** | `showModalBottomSheet`/`showDialog` builds outside the Provider subtree. Read the value from the calling context and pass it in. |
| **`RenderFlex overflowed by N pixels` in non-English locale** | Turkish/German strings are longer than English. Replace bare `Row` with `Wrap` or use `Flexible`. Test in tr and de. |
| **Permission prompt routes to Settings on first use** | Called `openAppSettings()` before ever requesting. First tap must trigger the native OS prompt (`request()`). Settings is the fallback only for `permanentlyDenied`. |
| **App stuck on native splash screen** | `main()` awaits network-dependent init before `runApp()`. Await only `Firebase.initializeApp()` in main; run everything else as `unawaited(...)` with a `.timeout(...)` on each network call. |
| **Apple Sign In: `invalid-credential` on a valid token** | Confirmed affected `firebase_auth` versions require `accessToken` (authorization code) in addition to `idToken` + `rawNonce`; inspect the current package API before constructing the credential. |
| **`flutter_localizations` / `intl` version conflict** | Use the SDK-compatible constraint shown by the current Flutter toolchain; do not pin a remembered version. |
| **Web-UI state != API state for subscriptions** | ASC shows "Prepare for Submission" (yellow) = API `READY_TO_SUBMIT`. Trust a fresh per-product `info` over the list endpoint (list can be stale). |
| **Fresh Firebase auth API returns `CONFIGURATION_NOT_FOUND`** | Initialize Identity Platform auth first, then PATCH required providers; include the current quota-project header. Verify by creating/querying a real auth user, not only HTTP status. |
| **Billing project link returns 403** | Use an open billing account owned/managed by an identity authorized for the Firebase project; verify active project/account before linking. |
| **Headless iOS signing says no account / Pods reject provisioning profiles** | Use automatic signing authenticated with the approved ASC API key, or set manual signing on Runner only. Never pass profile/identity globally to Pod targets. |
| **Debug build works, Release archive fails after auth/push package changes** | Remove unused dependencies and Pods; dependency changes require a clean Pod rebuild. Do not keep social-auth or messaging packages after scope removes the feature. |
| **Host `defaults write` appears to seed simulator prefs but app ignores it** | Simulator `cfprefsd` owns the value. Prefer an in-app round-trip; if seeding is essential use `xcrun simctl spawn <udid> defaults ...`, then still verify through the app. |
| **App Store version submit 409s with vague associated errors** | Query version `meta.associatedErrors`; common missing durable fields include copyright, age rating, availability, base price, App Privacy, and IAP attachment. Fix the named state, do not retry. |
| **First version rejects `whatsNew` update** | `What's New` is for updates, not v1.0. Skip it when the current API says the field is not editable. |
| **Shell says `timeout: command not found` on macOS** | macOS has no GNU `timeout` by default. Use the command's native timeout or a bounded polling loop; do not add coreutils only for this. |
| **`adb shell monkey ...` exits 251** | Treat the monkey exit code as non-evidence. Read back the launch with `am start -W` plus `pidof` and resumed-activity state; inspect logcat for crash evidence. Keep device/activity placeholders generic. |
