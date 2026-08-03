# Sign in with Apple — The Five Silent Gates

Each kills Sign in with Apple. **None produces a build error.** Symptom is almost always the same: Apple's modal shows **"Sign Up Not Completed"** / "Kaydolma Tamamlanamadı". Check in order.

**Diagnostic first:** print the raw provider error code on screen. Apple reports its own server-side refusal as `canceled` — a "user cancelled, stay silent" branch swallows the bug.

## Gate 1 — App ID capability (Developer Portal) ⚠️ THE ONE THAT COSTS A DAY

The `APPLE_ID_AUTH` capability must be enabled for the explicit App ID. Discover current support in `asc` before changing it; if capability setup or primary-App-ID selection is not supported or its parity is uncertain, use the Developer Portal Human gate.

Confirmed operational caveat: after capability creation/update, open **Developer Portal → Identifiers → <App ID> → Sign In with Apple → Edit**, confirm the intended primary App ID, and **Save**. A capability record or successful mutation alone has historically failed to prove that the primary-App-ID provisioning step took effect. Treat portal Save plus a physical-device sign-in as the durable success evidence; revalidate current Apple behavior rather than assuming API invisibility.

**Symptom of inert capability:** Apple's sheet shows "Sign Up Not Completed" and sits there. Dismissing returns `canceled` (1001). The app reports user cancel and you debug the wrong thing.

**Fix:** after creating by API, always hand the user the portal Save click.

## Gate 2 — Xcode entitlements wiring

`ios/Runner/Runner.entitlements` existing is not enough. `CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements` must be present in **all three** Runner build configurations. Otherwise the archive signs without `com.apple.developer.applesignin`.

## Gate 3 — Manual signing on ALL THREE configurations

With automatic signing Xcode picks the team wildcard profile (`iOS Team Provisioning Profile: *`), which carries **no** Sign in with Apple capability. Release/Profile → App Store profile; Debug → a development profile for this App ID.

This is why it "works on TestFlight but not with `flutter run`" (or the reverse if only Debug was fixed).

## Gate 4 — Firebase provider enabled

```bash
GET /admin/v2/projects/{id}/defaultSupportedIdpConfigs
```
Must list `apple.com` as enabled. Anonymous auth keeps working, so "auth works" feels true.

Enable + configure:
```json
PATCH .../apple.com?updateMask=enabled,appleSignInConfig
{"appleSignInConfig":{"bundleIds":["<bundleId>"]}}
```

For native iOS: **no Services ID `clientId`, no `codeFlowConfig`.** Adding them sends code-exchange validation to the wrong client_id.

## Gate 5 — credential construction

Confirmed affected `firebase_auth` versions reject an Apple credential built from `idToken` + `rawNonce` alone. Inspect the current package API; when it requires the authorization code as access token, construct it as follows:

```dart
final oauth = OAuthProvider('apple.com').credential(
  idToken: appleCredential.identityToken,
  rawNonce: rawNonce,
  accessToken: appleCredential.authorizationCode,   // required by affected/current API
);
```

## Also seen (Vizebo run)

A **stale App ID** for the same app (old bundle id) still registered as primary App ID for SIWA. Deleting the old App ID fixed it.

## Ruling out the device

If **another app in the same team** signs in with Apple on that same device/Apple ID, the device is fine. Stop debugging the phone and go back to Gates 1-5.

## Linking onto anonymous user

Use `linkWithCredential` so data carries over. Listen to **`userChanges()`**, not `authStateChanges()` — linking keeps the same `User`, so `authStateChanges` never fires.
