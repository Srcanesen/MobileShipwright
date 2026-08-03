# Android / Google Play Operational Flow

Same shape as iOS: automate everything possible; hand over each console-only gate with exact clicks.

## Precondition: closed-testing time gate

The source playbook records the personal-account rule as **≥12 opted-in testers for 14 continuous days** for affected newer accounts, with organization accounts exempt. Treat that as a planning baseline only: verify current eligibility, tester count/duration, engagement expectations, and production-access steps in official Play documentation/Console for this account. Start the applicable clock when the first `.aab` is available and tell the user in the first message if Android is in scope.

## Step 1 — Signing key (keystore)

```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 \
  -validity 10000 -alias upload
```
- User sets keystore passwords (🙋 gate — Claude cannot type them).
- `android/key.properties`: wire path + passwords. **`.gitignore` this file.**
- `android/app/build.gradle`: wire `signingConfigs.release` + `buildTypes.release`; set `minSdkVersion` to the highest minimum required by the app's current dependencies, `targetSdkVersion` to the current Play requirement, and verify `applicationId`.
- Build: `flutter build appbundle --release` → `.aab`. (`flutter build apk --release` for local testing.)

## Step 2 — Play Developer API service account (one-time)

After explicit approval for service-account/key creation, create the account + JSON key:
```bash
gcloud iam service-accounts create play-publisher
gcloud iam service-accounts keys create ~/play-sa.json \
  --iam-account=play-publisher@<project>.iam.gserviceaccount.com
```
🙋 **Human grant in Play Console**: Users and permissions → invite `client_email` → grant Admin (or Edit and manage store listings + Manage testing/production releases) → Save. Keep the JSON out of the repo.

## Step 3 — First upload (no API — must be in console)

Play Console → **Create app** (name, default language, app/game, free/paid). Open **Internal testing** track → upload the first `.aab` in the console. Enrol in **Play App Signing** when prompted. Create the required **Closed testing** track separately and add the verified cohort there.

The API generally cannot register a brand-new package. Revalidate this limitation in current Play API/Console behavior. After the first accepted manual upload, later uploads can use the approved CLI/service account.

## Step 4 — Play App Signing SHA → Firebase

Play re-signs the app with Google's key. The SHA on the user's device is neither your debug nor upload key. **After the first upload:**

1. Play Console → App integrity → Play app signing → copy **App signing key SHA-1 and SHA-256**.
2. Firebase Console → Project Settings → Android app → Add fingerprint (both SHA-1 and SHA-256).
3. Re-download `google-services.json` to be safe.

Without this, Google Sign-In gives `DEVELOPER_ERROR` (statusCode 10) on anything installed from Play. Firebase applies fingerprints immediately.

## Step 5 — Store listing (fastlane supply)

```bash
fastlane supply init --json_key ~/play-sa.json --package_name com.team.app
fastlane supply --json_key ~/play-sa.json --package_name com.team.app \
  --track internal --aab build/app/outputs/bundle/release/app-release.aab \
  --metadata_path fastlane/metadata/android
```
- One folder per BCP-47 locale under `fastlane/metadata/android/`, each with `title.txt` (≤30), `short_description.txt` (≤80), `full_description.txt` (≤4000). Reuse iOS translations — same 19 languages.
- Screenshots + graphics: PNGs per locale in `images/phoneScreenshots/`; the source baseline uses **featureGraphic 1024×500** and **icon 512×512**. Verify current required assets/dimensions before upload.
- `edits.commit` quirk: review state can determine whether `changesNotSentForReview` is accepted. On 400, inspect the error and current API docs before changing the flag; do not blindly retry.

## Step 6 — Monetization (subscriptions, IAP, prices)

**Unlike iOS, Play prices ARE API-writable.** Claude does all of it via `monetization.subscriptions.*` and `inappproducts.*` with per-region prices.

🙋 **RevenueCat Play Billing**: the service-account JSON must be connected in the RevenueCat dashboard (the one Play-side thing RevenueCat's API cannot upload).

## Step 7 — Declarations

### Data safety (API)
API-settable via `applications.dataSafety` CSV. Claude fills it.

### Console-only declarations (🙋 each blocks the release)
Guide the user through Play Console → App content:
- **Content rating**: IARC questionnaire. For no-mature-content → lowest rating.
- **Target audience & age**
- **Ads declaration**
- **App access**: reviewer login if the app gates content.
- **Privacy Policy URL**: agent publishes the approved page; user pastes the URL.

## Step 8 — Internal/closed test, physical checks, production access

1. Distribute the accepted bundle to the applicable internal/closed track only after approval.
2. Add license testers and the current required closed-test cohort; verify opt-in state and continuous-day clock in Play Console.
3. Install the Play-distributed build on a physical device. Test Google sign-in after the App Signing SHA handback, Billing purchase/restore, FCM, camera/permissions, persistence, account deletion, and Data Safety behavior.
4. For an affected personal account, complete the current closed-test requirement, then apply for production access in Console. Organization/other account rules may differ; verify live.
5. Promote/submit only with explicit approval. Read release/review state back; do not report production from a successful upload alone.

## Release-state evidence

Require: signed bundle and incremented version code, accepted first package, Play App Signing SHA-1/SHA-256 in Firebase, listing/assets per locale, products/base plans/offers, RevenueCat Play credentials when used, Data Safety CSV, all blocking App content declarations, privacy URL HTTP 200, tester/license configuration, and physical-device results.
