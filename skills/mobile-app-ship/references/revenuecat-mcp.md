# RevenueCat MCP

Use the official endpoint `https://mcp.revenuecat.ai/mcp`. Prefer native browser OAuth when the selected MCP harness supports it. The endpoint is Streamable HTTP, not SSE; an SSE client can receive `405`, which is a transport mismatch rather than an auth retry. An API v2 key fallback belongs in environment or user-level MCP configuration outside Git; never place it in this repository or transcript. Select one harness and copy only its inactive template after approval; see [harness onboarding](harness-onboarding.md). Never request a token, password, or redirect secret in chat.

For Pi, use the separately approved `pi-mcp-adapter` user-global entry from [`harnesses/pi/templates/mcp.json`](../../../harnesses/pi/templates/mcp.json): lazy lifecycle, OAuth, and proxy-only (`directTools: false`). If RevenueCat reports an unknown OAuth client, do not retry; RevenueCat documents client allowlisting as the remedy. The fallback is a dedicated read-only API v2 key through `bearerTokenEnv`, never a literal config value. The tested local adapter is `2.16.0`; revalidate before upgrading it.

On auth failure, classify before acting:

- **403 Cloudflare `Error 1010` / `browser_signature_banned`** is non-retryable for the same inline HTTP client. Do not retry it; switch to the supported MCP client/harness flow or native browser OAuth, or open a Human gate.
- **401 `invalid_token`** means the stored session is stale; re-authenticate through the harness/client-supported OAuth refresh or login flow.

Re-authentication goes through the supported client only. Never request, print, or paste tokens, and do not hand-write refresh-token POSTs, keychain rewrites, token extraction, or custom credential persistence. After re-auth, read vendor state again before acting.

Inspect current tool schemas/annotations before use and classify each call:

- **read:** projects, apps, products, entitlements, offerings, packages, paywalls, analytics, and task status;
- **write:** create/update catalog and paywall resources; requires scoped approval and read-back;
- **destructive:** delete/rewire resources that can break live purchases; requires explicit destructive approval;
- **asynchronous:** paywall generation/update may return a task ID; poll task completion and inspect the resulting resource before verification.

RevenueCat MCP does not create App Store/Play products. Dependency order is: create store SKU → read it back from the store → RevenueCat project/app and store credentials → RevenueCat product → entitlement attachment → offering → package → current offering → read public SDK key and relationships. A store SKU is not a RevenueCat `prod...` resource ID.

Store credentials remain manual-sensitive gates: IAP key material and Play service-account JSON stay outside Git. OAuth or API access to RevenueCat does not grant Apple/Google credential access.

Configure the Flutter SDK at launch, then identify/log in when auth resolves. For grants, bind the server request to the authenticated user, verify RevenueCat/store state, allowlist the benefit mapping, and use transaction/event plus user as an idempotency key. Keep a signed webhook as renewal/refund reconciliation, not the only immediate purchase-success path.

Test purchase, restore, relaunch, deletion, and restore-after-deletion on the distributed physical-device artifact. See [revenuecat-implementation.md](revenuecat-implementation.md).

Sources: [RevenueCat MCP documentation](https://www.revenuecat.com/docs/tools/mcp), [setup/authentication](https://www.revenuecat.com/docs/tools/mcp/setup), [security/troubleshooting](https://www.revenuecat.com/docs/tools/mcp/best-practices-and-troubleshooting), and [official endpoint](https://mcp.revenuecat.ai/mcp). Harness-specific inactive templates live under [`harnesses/`](../../../harnesses/); do not auto-load or copy them without approval.
