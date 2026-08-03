# Stability Gate — Before Upload and After Distribution

`flutter analyze == 0` proves none of what this checklist covers. Run items 1–11 before the first upload, using a physical device where local simulator behavior is not representative. Run item 12 only after store processing and tester distribution; only the distributed artifact can prove `DEVICE_VERIFIED`.

## Meta-lesson: the simulator lies about auth, payments, and gRPC

Anonymous/Apple sign-in can succeed in the simulator and silently fail on a real device. If the app gates RevenueCat, Firestore writes, and data loads behind `uid != null`, that one failure breaks multiple screens at once — and they look like four unrelated bugs.

**Two defenses from day one:**
- Do not gate every subsystem on `uid`. Configure RevenueCat at launch without a uid; let data stores resolve their loading state even when `uid` is null; never let one failed sign-in cascade into four dead screens.
- Provide a non-public diagnostics path in development/internal builds: show live `uid`, last auth error, RevenueCat configuration/entitlement summary, push-token state, and a one-shot Firestore read/write probe. Ensure it is not an obvious release affordance and contains no secrets. Open it on the first real-device test.

## Pre-upload checks

### 1. Cold start on clean install
Delete the app, reinstall, launch. First frame renders in < 2s. `main()` must `await` only `Firebase.initializeApp()`; every network-dependent bootstrap (`getToken`, RevenueCat, remote config, Firestore reads) is `unawaited(...)` with a `.timeout(...)` on each **network** call. Never put a cancelling timeout on `Firebase.initializeApp()` itself — that leaves Firebase half-initialised (intermittent device failures).

### 2. Kill and relaunch after creating data
In-memory state that never reached Firestore is the classic silent data-loss bug. Grep data notifiers for `TODO`/`// backend` before shipping.

### 3. Airplane mode
Every screen shows a real offline/error state. No infinite spinners, no raw exception strings.

### 4. Every locale renders — check longest for overflow
Turkish and German strings are ~30% longer than English. A `Row` of legal links/buttons/chips that fits in `en` overflows in `tr`/`de`. Open the app in **tr and de** and scan every screen (especially the paywall footer) for the yellow overflow bar. Use `Wrap`/`Flexible`/`FittedBox`, not a bare `Row`. Assert every ARB's non-`@` key set equals the template's programmatically.

### 5. Turkish uppercase
If any UI is all-caps, `İ`/`ı` must be right. Never call `.toUpperCase()` directly. Use a locale-aware helper: when active language is `tr`/`az`, use `s.replaceAll('i','İ').replaceAll('ı','I').toUpperCase()`.

### 6. RTL
If Arabic ships, run in `ar` and check layout mirrors, no icon/arrow points wrong way. Drop Arabic if you cannot verify RTL.

### 7. No debug affordances
Grep for skip-paywall / test buttons. Anything that must exist is behind `if (kDebugMode)`. Reviewers reject visible test controls (Guideline 4.0).

### 8. Purchase round-trip
On a sandbox account: buy → entitlement flips → kill app → relaunch → still premium → Restore works.

### 9. Account deletion round-trip
Delete → returns to clean first launch (onboarding, `onboarded=false`, fresh anonymous user), not into an empty app.

### 10. Legal/support surfaces exist IN the build
Paywall shows working **Terms of Use** and **Privacy Policy** links. Settings/Profile shows the same two. Privacy opens the approved live policy; Terms opens the selected standard/custom EULA destination. The store Support and Privacy URLs return HTTP 200 and the support contact path works. Do not upload with dead `#`, "coming soon", or unpublished pages.

### 11. Accessibility and interaction
Test at 200% text scale, VoiceOver semantics for icon-only controls, ≥44×44 pt tap targets, contrast, and state cues that do not rely on colour alone. Exercise haptics without excessive vibration.

## Post-distribution check

### 12. Physical-device platform round-trips
After `STORE_PROCESSED` and separate distribution approval, install the TestFlight/Play build on a physical device. Test auth/linking, sandbox purchase + restore + relaunch, APNs/FCM token and notification delivery, camera/photo permission first request and permanently-denied path, persistence/offline behavior, AI consent decline/withdrawal, deep links when used, and account deletion. Record the store build/version and observations. Simulator or locally installed success does not count.
