# Tool Contracts — Canonical Ownership

Use vendor tools directly. This playbook coordinates them; it is not a release wrapper.

| Owner | Owns | Does not own |
| --- | --- | --- |
| XcodeBuildMCP | Local Apple project/workspace discovery, build, test, simulator/device, archive inspection, and logs after signing is configured | Team enrollment/selection, code-signing configuration, certificates, profiles, portal capabilities |
| `asc` CLI | Installed-version-supported ASC remote/signing resources, metadata, TestFlight, submission, and release | Unsupported parity, account enrollment, legal decisions, AdMob monetization; discover then use a Human gate |
| RevenueCat MCP | RevenueCat projects, apps, catalog, entitlements, offerings, packages, paywalls, analytics, async task status | App Store/Play product creation and store credential handling |
| **google_mobile_ads** (Flutter SDK) | Ad serving (banner/interstitial/rewarded/native), initialization, platform configuration, test ads | AdMob Console account/app/ad unit creation; real IDs; payment/tax/identity |
| **AdMob API** (Google) | Read-only account/app/ad-unit inventory and reports via v1; limited v1beta writes only after method/schema inspection, account eligibility/access confirmation, and separate scoped approval | Ad serving, mediation config, account enrollment |
| Flutter | App implementation, analysis, tests, and local artifacts | Store records, processing, distribution, or release state |
| Firebase/Google | Firebase project/backend/rules/indexes/hosting and Google Cloud resources | Apple, RevenueCat, and Play release state |
| Fastlane/Play | Supported Android metadata/artifact/track operations; Play Console owns declarations, eligibility, testing, and production access | Apple work; `asc` and XcodeBuildMCP do not own Android |

For `asc`, start with installed `asc --help`, `asc search <topic>`, command help, and schema/workflow validation. Use verified examples from [asc-cli.md](asc-cli.md), never invented commands. If support or role parity is uncertain, stop at a Human gate.

Use [harness-onboarding.md](harness-onboarding.md) before connecting an MCP: select one harness, copy a supported inactive template only after approval, authenticate one provider at a time, and discover RevenueCat/XcodeBuildMCP live schemas before calling tools. XcodeBuildMCP uses persistent installed `xcodebuildmcp mcp` and still requires separate install/activation approval. Windsurf's template is manual review material for the user-global `~/.codeium/windsurf/mcp_config.json`; the toolkit writes neither project nor global Windsurf config. Gemini has no fake native skill or generated `GEMINI.md`. Pi core has no native MCP; the separately approved `pi-mcp-adapter` fallback is user-global, lazy, OAuth/proxy-only, and documented in `harnesses/pi/README.md`. It does not make RevenueCat writes safe or authorized.

The tool manifest names each owner domain, platform scope, and `required`/`optional` status. Doctor gaps only required tools in the selected scope. It reports the executable used and keeps broken generic PATH or build-environment inheritance as a separate gap/defer. Bootstrap skips exact tested versions, requests independent per-tool approval, uses verified Homebrew Node 24 npm for npm packages, and accepts installation only after version read-back.

RevenueCat MCP calls must be classified read/write/destructive/asynchronous before use. Store products must exist and read back before RevenueCat wiring.

AdMob Console is the default Human Gate for app/ad-unit creation. Use a v1beta write only after inspecting its current method/schema, confirming account eligibility and access, and receiving separate scoped approval; apply once. A `403` is a Human Gate/account-manager escalation, never a blind retry. v1 readback lists are vendor-state evidence.

Official sources: [asc](https://asccli.sh/), [App Store Connect CLI docs](https://github.com/rorkai/App-Store-Connect-CLI), [RevenueCat MCP](https://www.revenuecat.com/docs/tools/mcp), [RevenueCat MCP endpoint](https://mcp.revenuecat.ai/mcp), [XcodeBuildMCP](https://xcodebuildmcp.com/docs), [Flutter](https://docs.flutter.dev/), [Firebase](https://firebase.google.com/docs), [Google Play Console](https://support.google.com/googleplay/android-developer/), [AdMob API](https://developers.google.com/admob/api/reference/rest), [AdMob v1beta app create](https://developers.google.com/admob/api/reference/rest/v1beta/accounts.apps/create), [AdMob v1beta ad-unit create](https://developers.google.com/admob/api/reference/rest/v1beta/accounts.adUnits/create), [google_mobile_ads](https://pub.dev/packages/google_mobile_ads), and [AdMob Flutter quick start](https://developers.google.com/admob/flutter/quick-start).
