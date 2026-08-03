# Platform Compliance — Revalidate Live

These change on Apple's and Google's schedule. **Check the live sources before each first submission** — the notes below are durable patterns, not current versions.

## iOS SDK Requirements

**Source of truth:** https://developer.apple.com/news/upcoming-requirements/

- Uploads must be built against the current minimum iOS SDK version.
- Building against a newer SDK does **not** raise `IPHONEOS_DEPLOYMENT_TARGET`.
- Symptom of wrong version: asset validation rejects with *"built with the iOS <old> SDK"*.

```bash
xcodebuild -version
# Check the SDK version the archive was built against.
```

## iOS Privacy Manifests (PrivacyInfo.xcprivacy)

### ITMS-91053 — Missing API declaration
Your binary calls a *required-reason API* (UserDefaults, file timestamps, disk space, boot time, active keyboards) that no manifest declares.

### ITMS-91061 — Missing privacy manifest
You bundled a third-party SDK from Apple's privacy-impacting list that ships no manifest. **Blocks submission.** Fix: update the SDK.

Inspect the current plugin versions: modern plugins often ship their own manifests, but do not assume. Declare `NSPrivacyTracking`, tracking domains, collected data, and required-reason APIs for the app's **actual** behavior. Add `NSPrivacyAccessedAPITypes` only when the app's own native code uses an API and the selected Apple reason truthfully applies; never paste example reason codes speculatively.

**Wiring:** put the app manifest at `ios/Runner/PrivacyInfo.xcprivacy` and add it to the Runner target's Copy Bundle Resources. Plugin manifests remain in their pods/packages. Verify before upload:

```bash
unzip -l App.ipa | grep -i privacyinfo
# If the app owns a manifest, it must include Payload/Runner.app/PrivacyInfo.xcprivacy
```

Generate Xcode's Privacy Report from the final archive to inspect the merged app + SDK declarations. The manifest does not replace App Privacy nutrition labels.

**Reason codes are a fixed vocabulary** (`CA92.1`, `1C8F.1`, `C617.1`, `3B52.1`, `0A2A.1`, `E174.1`, `35F9.1`…). There is no `C617.2`. Source: https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api

## Android Target API Level

**Source of truth:** https://developer.android.com/google/play/requirements/target-sdk

- New apps and updates must meet the current minimum API level.
- Play Console blocks the upload if below requirement.
- Check `android/app/build.gradle` → `targetSdkVersion`.

## Privacy: AI Provider = Data Processor

An app sending user data to an AI provider must:
1. **Ask in-app before first send** — name the actual provider company and exact data, obtain affirmative opt-in, and offer a real decline path that leaves non-AI use available. A policy page alone does not satisfy 5.1.1(i)/5.1.2(i).
2. **Enforce at the shared outbound boundary** — default to denied; persist and recheck consent at the last shared function before every network send. Withdrawal in Settings must immediately block future transfers without requiring account deletion.
3. **Describe reality everywhere** — the policy names the processor, data, purposes, retention/deletion, and protection; store privacy labels match Firebase and AI behavior. Never select "Data Not Collected" when Firestore or an AI API runs.
4. **Minimize before transfer** — strip uid, email, device ID, and unrelated content. Say so in the consent screen; never log prompts or responses by default.

## Account Deletion (Required)

Every auth identity, including a silent anonymous user, is an account for this purpose. Provide in-app account deletion. Write `deleteAccount` onCall that:
1. Deletes user data (Firestore docs, Storage files).
2. Deletes the auth record.
3. Signs in a fresh anonymous user.
4. Returns to clean first launch (onboarding, `onboarded=false`).

## Health / Medical Disclaimer

If the app touches health topics:
- Explicit "general information, not medical advice, not a medical device" disclaimer in app + legal text + store description.
- Emergency-symptoms escalation line in AI system prompt.
- **Avoid the word "doctor" in marketing labels** ("Doctor-ready report") — prefer neutral wording ("Detailed PDF report").

## Android Closed-Testing Requirement

Personal developer accounts created after **13 November 2023** must run a **closed test with ≥12 testers for 14 continuous days** before production. Org accounts exempt. Start day the first `.aab` builds.

## App Tracking Transparency

Only add ATT when actual cross-app tracking/IDFA use requires it (for example attribution/ad SDK behavior or RevenueCat ATT status collection). Then add a truthful `NSUserTrackingUsageDescription`, request authorization before tracking starts but after the first valuable moment, and align nutrition labels. Do not add ATT "just in case." Verify the current SDK configuration; Firebase Analytics without IDFA-related ad components generally does not itself require ATT.

## Accessibility Minimums

- Dynamic Type: never hardcode font size; test at 200% text scale.
- Contrast ≥ 4.5:1 for body text.
- Tap targets ≥ 44×44 pt.
- Semantics on icon-only buttons (semanticLabel/tooltip).
- Never signal state by color alone.
