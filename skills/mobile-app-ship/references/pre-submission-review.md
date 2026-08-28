# Pre-Submission Review — PASS/FAIL Checklist

Run this right before submitting for review. Go through every item against **this specific app** (its actual screens, features, purchases, permissions, metadata). Decide PASS or FAIL. For every FAIL, fix it (or hand the exact human gate step) before submitting. Public `doctor`/`validate` output can miss privacy publication, medical-device classification, app price, and iPad screenshot blockers; verify those vendor states directly.

---

## PASS/FAIL checklist

### 2.1 App Completeness (crashes & placeholders)
- No placeholder/lorem text, broken links, visible debug text or TODOs.
- App runs on a **clean install** (delete + reinstall) without crashing.
- Every screen has real content.
- If login is required: provide a working **demo account** (email + password) directly in App Review notes. Never put its password in onboarding, repository files, or chat.
- **Screen recording** of full flow attached when useful or requested: launch → sign-in → core feature → purchase → gated IAPs → results → account deletion. Record on a physical device; discover current `asc` review-attachment support or use a manual gate, then verify the upload.

### 2.3 Accurate Metadata
- Screenshots show the **real current app** (not mockups/old UI).
- Final screenshot assets contain no IAP price or currency; verify with OCR before upload and read back each locale/device set in display order.
- Description matches what the app actually does.
- **No mention of other platforms** ("also on Android", "also on the web").
- No misleading claims or non-existent features.
- Run the ASO metadata/asset checklist in [aso.md](aso.md) (field limits, keyword budget without stuffing/trademarks, real-UI screenshots per locale, no ranking/price claims) and record one PASS/FAIL line per item.

### 3.1.1 In-App Purchase
- All digital content, credits, subscriptions sold through **Apple IAP** (RevenueCat over StoreKit).
- **No external payment links** / "buy on our website" / "pay via [link]" anywhere.

### 3.1.2 Subscriptions
- Paywall shows each plan's **title, price, duration**.
- Paywall has **functional links** to **Terms of Use (EULA)** and **Privacy Policy**.
- **Auto-renew disclosure text** present ("subscription auto-renews unless canceled at least 24h before the period ends…").
- Store **description bottom** states premium features require a purchase.
- If consumable credit IAPs are gated behind an active subscription: **spell this out in App Review Notes** — give exact step-by-step to reach the credit purchase screen. Without this note it is a near-automatic rejection.

### Guideline 4.8 — Sign in with Apple
- If the app offers **any** third-party or social login (Google, Facebook, etc.), it **also** offers Sign in with Apple.
- Run [siwa-gates.md](siwa-gates.md) and physically test link/sign-in when applicable.

### 5.1.1 / 5.1.2 Data Collection, AI Consent, and Privacy
- ASC **privacy nutrition labels** match the app's **actual** Firebase/AI/analytics behavior.
- **Privacy Policy URL** is set and reachable (HTTP 200); policy names processors, data, collection method, uses, and protection standard.
- Before first third-party AI send, the app names the provider and data, obtains affirmative permission, supports decline, and fail-closes at the shared network boundary.
- Settings provides equally easy withdrawal; a withdrawal test proves no later request leaves the device.
- If the app has **account creation**: in-app **account deletion** deletes owned data/auth and returns to clean first launch.

### 5.1.1 / 1.2 User-Generated Content (if applicable)
- EULA with zero-tolerance clause for objectionable content.
- Users can **report content** and **block abusive users**.
- Content moderation/filtering exists.
- Method to remove offending content within 24h of a report.
- Login screen requires affirmative, unchecked-by-default agreement to Terms + Privacy before any sign-in (checkbox, sign-in blocked until ticked).

### 4.2 Minimum Functionality
- App does something substantial and native — not a repackaged website or thin wrapper.

### 4.0 / 2.5 Design & Permissions
- No non-functional UI, no "beta"/"test"/"coming soon" labels.
- Every permission prompt has a clear **purpose string** in `Info.plist`.

### 2.3.10 Third-Party Trademarks & Brands
- No third-party trademark or AI model-provider brand shown to users unless licensed.

### Physical-device and distributed-build evidence
- Test auth, purchase + restore, push, camera/permissions, persistence, consent withdrawal, and deletion on a physical device from TestFlight/Play distribution.
- For IAP, the physical sandbox test must assert that tapping Buy opens the StoreKit purchase sheet, then completes and cancels visibly; verify the button recovers and non-cancel failures show localized retry feedback. Product and price visibility alone is insufficient.
- Confirm no first-frame stall, infinite loading state, raw exception, or false "offline" message.
- If App Review reports that a product and price loaded but Buy did nothing, treat the app rejection as primary; an associated IAP rejection can be secondary. Inspect the displayed-package purchase path before changing store metadata.

### Support URL & Age Rating
- **Support URL** (`/support.html`) set for all localizations, returns HTTP 200.
- Support page visibly provides a support email, a working **support form** with **Name / Email / Message** fields, and an FAQ. An optional no-backend form action (for example, an email form service) is acceptable only after privacy review; do not ship a dead form.
- **Age Rating** set in ASC (web UI or API PATCH).

---

### 2.1(b) IAP attachment hard stop
- Every subscription/IAP has review media and complete metadata.
- **Before submit:** products expected in the submission read `READY_TO_SUBMIT` and the draft visibly/API-confirmably contains version + group + products.
- **After submit:** every included product reads `WAITING_FOR_REVIEW`; any `READY_TO_SUBMIT` is FAIL and requires recovery via [store-submission.md](store-submission.md).
- Never submit or report success when attachment cannot be proved.

## Required to start review checklist

These are the items ASC blocks on before it lets you submit.

### 1. Screenshots for every required display size
- Decide phone-only versus universal in Phase 3 and verify `TARGETED_DEVICE_FAMILY` in every Runner configuration/archive.
- The source baseline uses iPhone 6.9-inch and, for universal apps, iPad 13-inch slots. Revalidate current required device families, slot names, dimensions, and screenshot counts in App Store Connect before export.

### 2. Content Rights Information
API: `PATCH /v1/apps/{id}` with `attributes.contentRightsDeclaration = "DOES_NOT_USE_THIRD_PARTY_CONTENT"` (or `USES_THIRD_PARTY_CONTENT`).

### 3. Base Price Tier
Even a free app must pick the Free tier. Web UI: Pricing and Availability → Price Schedule → Free. Or API via `POST /v1/appPriceSchedules`.

### 4. App Privacy — Privacy Policy URL
Set and read back every locale's Privacy Policy URL. Discover current `asc`/API support for the app-level App Privacy page; if parity is uncertain, confirm it with a role-aware manual gate.

### 5. App Privacy — Nutrition Labels
Complete with a currently permitted Account Holder, Admin, or App Manager role as applicable to the app and current App Store Connect policy; revalidate live. Declare honestly — never tick "Data Not Collected" if Firestore or AI API runs. Declare the data types you send: Health & Fitness, Coarse Location, User Content, etc. "Linked to the user" = No if anonymous account. "Not used for tracking."

### 6. Age Rating
API PATCH every field in one request or it 409s listing what is missing. Set `copyright` on the version too (`PATCH /v1/appStoreVersions/{id}`) or submit 409s.

### 7. Review Information, Contact, and Demo Access
Contact phone is required (409 without it). Format: `+<country code><number>`. Discover the current `asc` review-information flow with `asc search` and command help; if unavailable, use a manual gate. Provide demo credentials only through App Store Connect for password login, never through onboarding or chat; for SIWA explain that the reviewer uses their Apple ID. Notes must cover app purpose/audience, exact access/core/purchase/deletion path, external services (Firebase, RevenueCat, AI provider, storage/CDN), every permission and why, any region constraints, and physical device/OS evidence. Verify the full-flow video upload reads complete.

### 8. Terms of Use
Use Apple's **standard EULA** (`https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`) when that is the product's approved legal choice. Point in-app Terms links and the store-description EULA line to the chosen standard or counsel-approved custom terms. Keep an app-specific Privacy Policy. Leave ASC License Agreement at its default unless the user/legal decision requires a custom agreement.

### 9. Standard Apple EULA guidance
- Standard-EULA choice: in-app Terms links → `https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`
- Privacy Policy → the approved app-specific live page (hosting provider is not prescribed)
- App-level License Agreement in ASC → default Standard EULA unless a specific legal decision requires custom terms
- Verify every in-app and listing URL from the shipping build
