# AdMob Implementation

Load when the user confirms monetization with ads (Phase 1) or during Phase 7 (Monetization). RevenueCat entitlement controls whether ads show — see [revenuecat-implementation.md](revenuecat-implementation.md).

## Ownership

| Owner | Owns | Does not own |
| --- | --- | --- |
| **google_mobile_ads** (Flutter SDK) | Ad serving (banner, interstitial, rewarded, native), initialization, platform configuration, test ads | AdMob Console account/app/ad unit creation; real IDs; payment/tax/identity |
| **AdMob API** (Google) | Read-only account/app/ad-unit inventory and reports via [v1](https://developers.google.com/admob/api/reference/rest/v1/accounts.apps/list); limited [v1beta writes](https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create) only after method/schema inspection, account eligibility/access confirmation, and separate scoped approval | Ad serving, mediation configuration, account enrollment, payment |
| **AdMob Console** (human) | Account enrollment, payment/tax/banking, identity verification, app-ads.txt, real ad unit IDs, store link | Ad serving, code-level ad integration |

Official sources (verified 2026-07-30, tested package `google_mobile_ads` 9.0.0):
- AdMob API root: https://developers.google.com/admob/api/reference/rest
- OAuth / getting started: https://developers.google.com/admob/api/v1/getting-started
- Flutter quick start: https://developers.google.com/admob/flutter/quick-start
- Test ads: https://developers.google.com/admob/flutter/test-ads
- Privacy / UMP: https://developers.google.com/admob/flutter/privacy
- Package: https://pub.dev/packages/google_mobile_ads
- v1beta app create: https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create
- v1beta ad-unit create: https://developers.google.com/admob/api/reference/rest/v1beta/accounts.adUnits/create

## Human gates

- **AdMob Console setup**: enrollment, payment/tax/banking, identity verification, app-ads.txt, real ad unit IDs, store-link assignment — a person must act in the AdMob Console.
- **Real ad unit IDs**: copy from AdMob Console after ad units are created. They are not secrets: configure them in platform release configuration (`AndroidManifest.xml`/`Info.plist`) or explicit compile-time flavor configuration. Do not fabricate or guess IDs.
- **v1beta writes**: the default create path is the AdMob Console Human Gate. API app/ad-unit creation is limited access: inspect the documented method/schema, confirm account eligibility and access, then obtain separate scoped approval for each create. Apply once. On `403`, do not retry blindly; route to a Human Gate and the account manager.
- **External mutation flow**: AdMob account/app/ad unit creation follows **Inspect → Plan → Scoped approval → Apply once → Read back → Record evidence** exactly as documented in [state-evidence.md](state-evidence.md) and [human-gates.md](human-gates.md). Use existing action/evidence/gate records; do not introduce new state fields.

## Test IDs — debug/test builds only

Use Google-provided sample IDs in debug and test builds. Source: https://developers.google.com/admob/flutter/test-ads

| Platform | App ID | Banner ad unit ID |
|---|---|---|
| Android | `ca-app-pub-3940256099942544~3347511713` | `ca-app-pub-3940256099942544/6300978111` |
| iOS | `ca-app-pub-3940256099942544~1458002511` | `ca-app-pub-3940256099942544/2934735716` |

For any other format, inspect that format's current official guide during implementation and use its current sample ID; do not infer one from this banner-only pilot table.

### Release build guard

- Ads-enabled release builds MUST use resolved real AdMob IDs from the production AdMob Console app entry. Shipping a sample ID in such a release is a configuration error.
- Debug/test builds MUST use the sample IDs above; a debug build MUST NOT load a real ID. Real IDs are not secrets, but using them in debug risks invalid traffic.
- Select ID sets with `kReleaseMode` or explicit flavor configuration; do not infer release mode from a custom environment flag.
- Make build/preflight fail when the resolved ads-enabled release App ID or ad-unit ID matches Google's sample prefix (`ca-app-pub-3940256099942544`) or an explicit sample-ID list.
- Record a resolved flavor/configuration readback as evidence for the selected release IDs. Artifact grep may supplement that readback, but is not proof by itself.

## UMP privacy consent flow

**Do not request or load an ad until the UMP update and required form callback complete, and `canRequestAds()` is true.** Follow https://developers.google.com/admob/flutter/privacy . Mobile Ads SDK initialization does not request an ad; initialize it only after this gate, then request/load ads.

1. Before integration, inspect the selected AdMob SDK/plugin privacy manifest and decide whether its Device ID/tracking and other declared collection match the approved App Privacy posture. If not, do not integrate ads. Adding or later removing the SDK changes the shipping binary and can require a clean dependency rebuild, new signed build/upload/attachment, and App Privacy re-apply/publish; do not treat removal as a metadata-only change.
2. Add `google_mobile_ads` to `pubspec.yaml`.
3. At app launch, call `ConsentInformation.instance.requestConsentInfoUpdate(...)`.
4. In its success callback, call `ConsentForm.loadAndShowConsentFormIfRequired(...)`.
5. Only after that callback completes, check `ConsentInformation.instance.canRequestAds()`; do not initialize or request an ad when it is false or the update/form failed.
6. If the app tracks users or accesses IDFA, make ATT a conditional iOS Human Gate: confirm current Apple and Google requirements, add `NSUserTrackingUsageDescription`, then request authorization at the appropriate point. Do not add ATT solely because the app serves ads.
7. When `canRequestAds()` is true, initialize `MobileAds.instance`; only then load an ad.

```dart
// Consent-first initialization — current Flutter UMP callback flow.
import 'package:google_mobile_ads/google_mobile_ads.dart';

void initializeAdsAfterConsent() {
  ConsentInformation.instance.requestConsentInfoUpdate(
    ConsentRequestParameters(),
    () {
      ConsentForm.loadAndShowConsentFormIfRequired((FormError? error) async {
        if (error != null) return;
        final canRequestAds = await ConsentInformation.instance.canRequestAds();
        if (!canRequestAds) return;
        await MobileAds.instance.initialize(); // Initialization is not an ad request.
        // Only here may BannerAd.load(), InterstitialAd.load(), etc. run.
      });
    },
    (FormError error) {
      // No initialization or ad request: consent information update failed.
    },
  );
}
```

## RevenueCat coexistence

RevenueCat decides whether the current user sees ads. RevenueCat does not own AdMob.

```dart
final customerInfo = await Purchases.getCustomerInfo();
final isPremium = customerInfo.entitlements.active.containsKey('premium');

if (!isPremium) {
  // RevenueCat signals "not premium" → show ads
  AdWidget(ad: bannerAd);
}
```

RevenueCat entitlement state is the signal; AdMob remains the ad-server owner. Do not use RevenueCat to serve, block, or configure ad networks.

## SDK wiring (Flutter)

```yaml
# pubspec.yaml
dependencies:
  google_mobile_ads: ^9.0.0
```

```dart
// After UMP consent completes
await MobileAds.instance.initialize();

// Platform requirements:
// Android: minSdkVersion 21 in android/app/build.gradle
// iOS: GoogleMobileAds via CocoaPods or SPM (handled by the Flutter plugin)
```

## Simulator/emulator test scenario

The sample test IDs work on iOS simulator and Android emulator without a real AdMob account:

1. Add `google_mobile_ads` as a dependency.
2. Implement consent-first initialization (see UMP section).
3. Create and load a test banner ad using the sample ad unit ID.
4. Verify the "Test Ad" label appears on the rendered creative.
5. Confirm `onAdFailedToLoad` is not called.
6. For another format required by the SPEC, first inspect its current official guide and use that guide's current sample ID.

Observed smoke test (2026-07-30): with Flutter 3.44.8 and `google_mobile_ads` 9.0.0, iOS SPM may place a generated package copy under `build/ios/SourcePackages`; a whole-project analyzer can then report duplicate vendor-source errors. Do not edit generated vendor files. Exclude `build/**` in the target app's analyzer configuration, clean, and rerun the full analysis. Keep `lib/` analysis as separate evidence so generated-source noise cannot hide app errors.

## External mutation flow for AdMob resources

AdMob write operations (API create, Console setup) follow the standard external mutation pattern from [human-gates.md](human-gates.md) and [state-evidence.md](state-evidence.md):

1. **Inspect** — list existing accounts, apps, and ad units with v1; this readback is vendor-state evidence.
2. **Plan** — identify the app entry or ad-unit format/name/placement to create.
3. **Human Gate by default** — create in the AdMob Console.
4. **Limited API exception** — before [app create](https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create) or [ad-unit create](https://developers.google.com/admob/api/reference/rest/v1beta/accounts.adUnits/create), inspect the current method/schema, confirm account eligibility and API access, and obtain separate scoped approval.
5. **Apply once** — on `403`, do not retry blindly; use the Human Gate and contact the account manager.
6. **Read back** — list apps/ad units and confirm the new resource and expected attributes.
7. **Record evidence** — sanitized read-back result, tool version, limitations. Use existing evidence schema.

Do not treat a successful create response as proof without separate readback.

## What does not exist in this reference

- RevenueCat does not own AdMob ads.
- AdMob API v1 is read-only; v1beta writes are limited access and require method/schema inspection, account eligibility/access confirmation, and separate scoped approval.
- This reference does not cover mediation, bidding, or third-party ad networks.
- Upload, submission, release, and public rollout remain separate actions/evidence outside this reference's scope; each needs its own exact single-use consumed gate and read-back.
- Real production IDs are not secrets, but they must not be fabricated, guessed, or placed where a debug build loads them.
