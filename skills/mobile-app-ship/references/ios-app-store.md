# iOS, App Store Connect, Build, and Listing

Load for iOS Phases 8, 9, 11, and 11.5. Also load [quality-compliance.md](quality-compliance.md), [human-gates.md](human-gates.md), and, when applicable, [revenuecat-implementation.md](revenuecat-implementation.md) and [siwa-gates.md](siwa-gates.md). Verify current CLI/API syntax with `--help` and official documentation before use.

## Phase 8 — Signing and capabilities

1. Verify the bundle ID, team, existing signing identities, device family, and capabilities before changing state.
2. With approval, register the explicit bundle ID and enable only required capabilities (IAP, push, SIWA, associated domains). SIWA primary-App-ID configuration can require a Developer Portal Save whose effective provisioning state is not reliably proved by the capability record alone; follow [siwa-gates.md](siwa-gates.md).
3. Create or reuse the correct distribution certificate and App Store profile. Do not revoke or replace working credentials for convenience.
4. Keep `Runner.entitlements` aligned with capabilities. Ensure `CODE_SIGN_ENTITLEMENTS` is wired in every Runner build configuration. Include `aps-environment` only for push and `com.apple.developer.applesignin` only for SIWA.
5. Configure signing on the Runner target, never globally on Pods or Swift Package targets. Use either automatic signing authenticated with the ASC API key or manual Runner-only profile settings. Keep `ExportOptions.plist` consistent with the chosen method.
6. Add truthful `Info.plist` purpose strings for every requested permission and set export-compliance encryption state accurately. Declare encryption per build; do not reuse a prior build's answer.
7. Build and inspect the archive's signing identity, embedded profile, and entitlements. Test auth/push on a physical device.

A safe headless fallback is: build Flutter with `--no-codesign`, embed only the approved Runner profile, sign the app with the approved distribution identity, then use `xcodebuild -exportArchive`. Never pass provisioning-profile settings globally because Pod and Swift Package targets can reject them.

For push, create/download an APNs auth key only with approval, upload it to Firebase Cloud Messaging, save FCM tokens on launch, token refresh, and auth availability, and verify on a physical device.

## Phase 9 — App Store Connect objects and metadata

Start the app record on day 1 after bundle ID approval. Discover whether the installed `asc` version supports the needed app-record and metadata operations. If parity or permissions are uncertain, open a Human gate instead of inventing syntax. Automate only supported fields:

- app info: fixed brand + localized tagline, subtitle, privacy URL;
- version listing: description, keywords, promotional text, support/marketing URL;
- subscription groups/products and consumable IAP localizations;
- age rating, content-rights declaration, copyright, review contact, and app availability when supported.

Load [store-submission.md](store-submission.md) for locale mappings, field limits, subscription state, review screenshots, submission, and rejection. Prices/trials, subscription territory availability, App Privacy declarations, base price, and final submit may require approval or manual execution depending on current API support, account role, and app access. Use [human-gates.md](human-gates.md) as the canonical list and revalidate live.

### Legal and support surfaces

Publish before the first upload:

- an app-specific Privacy Policy that matches actual Firebase/AI data behavior and names processors;
- a branded support page with dedicated support email, short FAQ, and a working Name/Email/Message contact path;
- Terms links that follow the product's legal decision. For standard consumer App Store terms, use Apple's Standard EULA and leave the ASC license agreement at its default unless legal counsel/user requirements justify a custom agreement.

Set Support and Privacy URLs for every listing locale and verify each final URL returns HTTP 200. Tap-test the same Privacy/Terms links in the shipping paywall and Settings/Profile. Do not ship a fake form or dead link. Review third-party form processors before sending support data to them.

### Description and claims

Put the strongest human-written benefit in the first lines. Keep metadata accurate, avoid keyword stuffing, cross-platform mentions, unlicensed provider/trademark names, guarantees, and medical claims. For subscriptions, state duration, renewal/cancellation behavior, premium requirement, and explicit Terms/Privacy URLs at the bottom.

## Phase 11 — Build and distribution

Before the first upload, pass [stability-gate.md](stability-gate.md). Then obtain a separate exact single-use upload gate, consume it once, and read back the uploaded build:

```bash
flutter build ipa --export-options-plist=ios/ExportOptions.plist
asc builds upload --app "$ASC_APP_ID" --ipa build/ios/ipa/APP.ipa
# Discover the current build read-back command with `asc search builds` and command help.
```

Use the actual generated IPA path and current CLI syntax. Poll until Apple reports the build `Valid`; a successful upload command is not acceptance. Attach the valid build to the intended version only with approval. Bump the build number for every upload. Dependency/Pod changes require a clean dependency rebuild; pure Dart changes generally do not.

Create a sandbox tester and use TestFlight on a physical device for purchases, push, camera, auth, persistence, and the review path. Treat upload, TestFlight distribution, review submission, and release as four separate outward-facing approvals.

## Phase 11.5 — Screenshots and device family

Capture only the real shipping UI, localized to the same language as each store locale. Show the app in use, not splash/login/title art or invented features. If a status bar is visible, use truthful conventional values. Decorate around the real capture; never replace the in-app UI with generated mock content.

Choose iOS support before build:

- phone-only: set `TARGETED_DEVICE_FAMILY = "1"` in all Runner configurations and verify the archive;
- universal: provide the current required iPhone and iPad screenshot families.

Durable source examples are iPhone 6.9-inch portrait `1320×2868` (Apple may accept other documented sizes) and iPad 13-inch `2064×2752` or `2048×2732`. **Revalidate accepted dimensions and slot names in current App Store Connect documentation before export/upload.** Supply 1–10 screenshots per required size/locale. If full localization is not feasible, use correct default-language fallback rather than mismatched UI/caption languages.

Give finished assets an on-brand background, device framing, and short benefit headline. Use real UI captures with overlays around them, zero-padded upload order (`01`, `02`, ...), and no price/currency text that OCR could misread. Upload each device/locale set separately, read it back, and recover a timeout by querying that set before retrying. Do not preserve source vendor promotion or fixed pricing.

## Required store-state evidence before review

Verify, do not infer:

- build is `Valid` and attached to the intended version; cross-check that attached build separately from the TestFlight-distributed build;
- required device-family screenshots exist;
- localized listing fields and URLs are present within current limits;
- content rights, age rating, copyright, app availability, base price, Privacy URL/labels, review phone/notes/video, and demo access are complete;
- every IAP/subscription has review media and is attached with the version according to [store-submission.md](store-submission.md).
