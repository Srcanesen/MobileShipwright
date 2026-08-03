# Store Submission & Rejection

For the complete catalog of browser/account/payment steps, see [human-gates.md](human-gates.md) — this reference covers submission mechanics and rejection response only.

## Locale mappings and listing mechanics

Use this section when preparing or changing ASC listing/subscription localizations. Locale mappings and field limits below are planning baselines; verify all of them against current App Store Connect help/schema before mutation.

- Map Flutter locales to ASC locales deliberately: `de`→`de-DE`, `es`→`es-ES`, `fr`→`fr-FR`, `pt`→`pt-BR`, `nl`→`nl-NL`, `zh`→`zh-Hans`, `ar`→`ar-SA`; `tr`, `it`, `ja`, `ko`, `ru`, `hi`, `pl`, `uk`, `id`, `vi`, and `th` stay unchanged. Apple app creation uses canonical `tr`, **not** `tr-TR`. Verify the current ASC mapping for every other locale.
- Keep Name and Subtitle at **30 characters** or fewer, Promotional Text at **170** or fewer, and Keywords at **100** or fewer. Write keywords comma-separated with no spaces after commas.
- Keep the translated brand guard: build `Brand: translated tagline` yourself. The brand token never changes, translates, transliterates, or declines by locale.
- Import listing text per locale, but update Support and Marketing URLs separately per locale when the chosen ASC workflow does not include them. Metadata workflows can auto-create version localizations; read them back. Omit `whatsNew` for the first version rather than sending an empty/invalid first-release value. Verify the URLs afterward; do not assume an import updated them.
- Localize the subscription group and each product for every shipped locale. Subscription display names are **≤30** characters and descriptions **≤45**. A missing group localization can leave otherwise-complete products at **Missing Metadata**; trust a fresh per-product read over a stale list result.

## The Trap: Subscriptions Must Go In WITH the Version

The most common first-submission failure: **Guideline 2.1(b)** — "In-App Purchase products have not been submitted for review." The version submitted without its IAPs.

### 🛑 HARD STOP — never submit without passing this check

```bash
# Before submit: every product must be READY_TO_SUBMIT
# After submit: every product must be WAITING_FOR_REVIEW
GET /v1/subscriptionGroups/{gid}/subscriptions?fields[subscriptions]=productId,state
```

- Discover the installed `asc` submission flow and inspect the draft contents. The version, new subscription group when applicable, and every intended product must be attached before finalization.
- **If you cannot confirm attachment → do not submit. Open a Human gate.**

### Order That Works

1. **Every subscription and review-submitted IAP needs its own App Review screenshot** (usually a truthful paywall/purchase shot). This uses the product review-media endpoint, not the app-version image endpoint. In `asc` 3.1.3 the working relationship was `asc iap review-screenshots create --iap-id <IAP_ID>`; discover current syntax with `asc search` and command help rather than substituting `iap versions images`. If unavailable, upload manually. Verify each media item is complete.
2. Build or inspect the review submission so it contains the version, required group, and every product. Immediately read a newly created submission back and verify its platform is `IOS` before adding items; do not trust the create command's echoed intent. If Apple reports `TV_OS` or another mismatch, correct that same empty draft's platform with separately approved current CLI/API support, read it back, and only then add iOS items. For the supported high-level path, `asc publish appstore --app "$ASC_APP_ID" --version "$VERSION" --submit --confirm` is an official example; run its current help and workflow validation first, and never assume it attaches products without read-back.
3. **Immediately read back after submit:** every product reads `WAITING_FOR_REVIEW`. Any `READY_TO_SUBMIT` left over means it did not go in; correct the submission before proceeding.

### If It Goes Wrong

**Products still `READY_TO_SUBMIT` after submit → the version will be rejected 2.1(b).**

Fix only after reading the current version/submission state:
1. Developer-reject only when an in-review version must become editable. Use the current supported CLI/API/UI action and confirm `DEVELOPER_REJECTED`.
2. If the old submitted review submission still owns the version/items, cancel it with `PATCH /v1/reviewSubmissions/{old}` `{"attributes":{"canceled":true}}`; wait for `COMPLETE`. `ITEM_PART_OF_ANOTHER_SUBMISSION` means this ownership was not cleared.
3. Create a **fresh** review submission only after confirming there is no reusable open submission. Never stack drafts.
4. Add version + subscription group + every subscription/IAP. If supported automation leaves products behind, a permitted Account Holder, Admin, or App Manager with access uses ASC → version → In-App Purchases and Subscriptions → Edit → select all → Save; revalidate the current role requirement.
5. Finalize with approval, then re-read every product state.

A staged, never-submitted draft may not be cancelable/deletable with a p8 key; the account holder must discard it in the web UI. Do not stage speculative submissions.

### New Subscription Group Rule

A new group needs the **group AND at least one auto-renewable product** in the same submission. Group-only fails: *"New subscription groups must be submitted with an auto-renewable subscription."*

No high-level submit command is proof that products were attached. Verify the draft contents and product states; do not trust command intent.

### Exact manual fallback

When supported automation fails or omits products, instruct a currently permitted app-scoped role (Account Holder, Admin, or App Manager as applicable; revalidate live):

1. ASC → app → **Monetization → Subscriptions → group → Add for Review** (or open the version's draft submission).
2. Confirm the draft contains the app version, subscription group, and **every** subscription/IAP product. Add each product with **Add for Review** if missing.
3. Submit only when there are no blocking warnings.
4. Re-read API states. All included products must be `WAITING_FOR_REVIEW`.

A group-only draft fails because a new group must include at least one subscription product.

### Web UI Quirks

- ASC shows `READY_TO_SUBMIT` as yellow **"Prepare for Submission"** — same state. Do not panic; it is ready.
- Subscription state is eventually consistent. If the list endpoint shows `Missing Metadata` but the per-product `info` shows `Ready To Submit`, trust the per-product read.
- `PATCH submitted=true` can return `500` and still succeed. Read the submission before retrying; a blind retry can 409 because it is already in review.
- **Never create a second `reviewSubmission` blindly.** Always `GET` for an open one first; reuse only a valid open draft, otherwise clear stale ownership then create fresh.

## Rejection — First Hour Response

### Classify It

| Notice | Action |
|---|---|
| **2.1 — Information Needed** | App Review notes were thin. Answer in Resolution Center, attach demo video. No new build. |
| **2.1(b) — IAPs not submitted** | Products not in version. Fix per above. No new build needed. |
| **5.1.1(i) / 5.1.2(i) — data sent to third-party AI** | Missing in-app consent screen naming the provider. Needs new build. |
| **2.3 — Metadata** | Fix metadata. No new build. |
| **Functional bug / crash** | Fix → bump build → upload → attach → resubmit. |
| **You disagree** | Reply to reviewer before rebuilding. Request a call if needed. |

### Resolution Order

1. Read the full Resolution Center text; reply in plain English with what changed or why no change is needed.
2. While the version remains editable, complete Human gates (App Privacy, IAPs attached, reply/video/demo access).
3. Upload and attach a new build only if binary behavior changed; bump its build number.
4. **Then** resolve issues, submit with approval, and re-verify product states.

**Do not silently resubmit.** Answer the question in Resolution Center first.

### Things That Block the Version Silently

- **App Privacy nutrition labels** incomplete or unpublished. Required role and API/UI support vary; revalidate current Account Holder/Admin/App Manager permissions and app access.
- **App availability** record missing. Create via the current App Store Connect v2 availability endpoint/schema; verify territory identifiers and read the record back.
- **Base price tier** not set (even "Free").
- **Age rating** not set.
- **Subscription not available for sale** (territory availability web-UI toggle).
- **Copyright** missing on version (`PATCH attributes.copyright`).
- **What's New** on v1.0 — 409s, skip it (only for updates).

### After Resubmit

A resubmission goes to the back of the queue (24-48h). Record as **blocked and owned by Apple**, never as `done`.
