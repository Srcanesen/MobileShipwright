# RevenueCat Implementation

Use only when the user confirms monetization with subscriptions or purchases.

## Dashboard / object model

Walk the user through each object as they create it. These names appear in code five minutes later:

1. **Project** → one per app.
2. **App** → connect App Store: bundle id, shared secret, In-App Purchase key. Add Play later.
3. **Products** → one row per thing you sell. The matching product must exist and be read back in App Store Connect or Play first.
4. **Entitlement** (`premium`) → the permission the user buys. Attach every product that grants it.
5. **Offering** (`default`) → what the paywall shows. Inside it, **packages** keyed `$rc_monthly`, `$rc_annual`, `$rc_weekly`. Use exactly these keys or `purchases_flutter` will not find them.

Copy the platform's **public SDK key** (`appl_…` for Apple or the current Play prefix). Public SDK keys are safe to ship; secret RevenueCat keys are not.

RevenueCat MCP object creation can be automated after scoped approval. Prefer OAuth. If the client cannot use OAuth, use an existing scoped API v2 key from environment or user configuration outside Git. Credential creation and store-credential upload remain manual gates. Create objects in dependency order: project → platform app + store credentials → read-back of matching App Store/Play products → RevenueCat products → entitlement attachments → offering → packages → current offering → read public key. Store SKUs and RevenueCat `prod...` resource IDs are different identifiers. Read every relationship back; a successful create response does not prove an offering is sellable.

## Two RevenueCat-specific human gates

- **In-App Purchase `.p8` key** (separate from ASC API key): a permitted user generates/downloads it once and uploads it through the supported RevenueCat credential flow. Never expose it to chat or Git.
- **Play Service Account JSON** (from `android-play.md` step 2): a permitted user uploads it for Play Billing. Keep it outside Git.

## SDK wiring

```dart
// 1. Configure at launch — no uid needed (never gate this behind auth)
await Purchases.configure(PurchasesConfiguration('appl_...'));

// 2. Listen for real-time entitlement changes
Purchases.addCustomerInfoUpdateListener(_apply);

// 3. Log in when auth resolves (RC app_user_id == Firebase uid)
await Purchases.logIn(firebaseUid);

// 4. Fetch offerings (data-driven paywall)
final offerings = await Purchases.getOfferings();
final offering = offerings.getOffering('premium') ?? offerings.current;
// offering.weekly / .monthly / .annual are Package?; price = pkg.storeProduct.priceString

// 5. Purchase
final res = await Purchases.purchase(PurchaseParams.package(pkg));

// 6. Verify entitlement
final active = res.customerInfo.entitlements.active.containsKey('premium');
```

## Purchase flow invariant

Pass the exact `Package` used to render the price into `Purchases.purchase`; never call `getOfferings()` again after Buy is tapped. Model success, user cancellation, and operational failure as separate outcomes; never collapse a non-cancel error into a silent `false` result. Success requires an active `premium` entitlement. Cancellation may stay quiet, but every other failure must reset the button and show localized, actionable retry feedback. Product and price visibility alone does not prove that Buy works.

## Server-verified, client-invoked grant pattern

Do **not** trust `{productId}` or a client entitlement boolean as proof of payment. After the SDK reports success, call a thin authenticated server function with the minimum purchase/customer identifiers supported by the current RevenueCat/store APIs. The server must:

1. Bind the request to the authenticated Firebase uid / RevenueCat App User ID.
2. Query RevenueCat or validate store transaction/entitlement state server-side.
3. Allowlist the exact product-to-benefit mapping from server-controlled configuration.
4. Use transaction ID/event ID + user as an idempotency key.
5. Apply credits/premium in a Firestore transaction and record a ledger row.

For subscriptions, drive access from the current active entitlement (including expiry) and period-guard recurring credit grants. For consumables, increment once per verified transaction. Recheck active entitlement on launch to catch renewals/restores.

Do not make a webhook-only flow the purchase-success path: dashboard misconfiguration/delivery delay can make a valid purchase look broken. A verified callable gives immediate reconciliation; a signed RevenueCat webhook remains the durable renewal/refund/reconciliation backstop when subscription state must stay correct without an app launch.

## Purchase / restore / deletion tests

Verify on a **physical device** with a sandbox test account:

1. Purchase → entitlement flips immediately → close app → relaunch → still premium.
2. Restore purchases → entitlement restores on a fresh install.
3. Delete account → remove app/backend account data and auth, clear local premium state, disassociate/log out the RevenueCat app user as documented, create a fresh anonymous app identity, and return to onboarding. Do not erase the user's underlying App Store/Play purchase history; Restore must recover eligible purchases under the store account. Test deletion and restore behavior on a physical device.

## Credit economy

Model `provider cost per action × expected monthly actions`, store fees/tax, free usage, refund/abuse risk, and target margin before setting prices or quotas. The source heuristic `credit_cost = ceil(cost_USD / $0.01)` is a starting denomination, not a security or profitability guarantee. Keep approved benefit mappings server-controlled so a change needs no binary, but never let clients edit them.
