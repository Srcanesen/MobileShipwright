# Phase 0 — Setup and Readiness

Load at the start of every guided run. Scan silently, report only gaps, and then ask the first product question. Ask for independent, per-tool approval before every install, account change, payment, certificate/key change, or other machine-wide action. Use `doctor --platform ios|android|both`; only required tools in the selected scope are gaps, while optional or out-of-scope tools are deferred.

## Harness and authentication order

Start with [harness onboarding](harness-onboarding.md). First discover the selected harness and local Flutter/Firebase state read-only; choose exactly one harness before any adapter is copied. Then request one provider authentication at a time and record its gate/evidence before the next:

1. Apple: discover installed `asc` auth capabilities with `asc --help`, `asc search auth`, and command help; use native browser auth when available, then perform only read-only inventory.
2. XcodeBuildMCP: request install/activation approval before its persistent installed `xcodebuildmcp mcp` template is copied or used; discover live schemas only. It has no OAuth.
3. RevenueCat: prefer harness-native browser OAuth to the official MCP, then read-only project/app discovery from live schemas.
4. Firebase browser login starts only with backend work. Play/service-account credentials start only with Android work.

Allow skip/defer and resume from the recorded evidence. A deferred onboarding step does not count complete. A verified step requires a sanitized read-back claim and evidence ID; command exit alone never advances authentication. Authentication never authorizes writes. Never request tokens, passwords, `.p8` contents, private keys, service-account JSON, or redirect secrets in chat.

## Classify each check

- **PASS:** verify the success state and move on.
- **AGENT:** the agent can fix it after any required approval; run the fix and re-check.
- **HUMAN:** a browser, password, account owner, payment method, GUI, or physical device is required. Load [human-gates.md](human-gates.md), give one literal instruction and success check, and continue unrelated work.

Do not dump all gaps as homework. Explain one gate at a time and why it exists.

## Start slow gates immediately

If the target includes the platform, start these clocks in the first five minutes:

1. Apple Developer enrollment and the App Store Connect app record. Enrollment can take days or longer for organizations; the record blocks store products and RevenueCat store-product wiring.
2. Google Play personal-account closed testing. Revalidate the current tester count, duration, account eligibility, and production-access process against Play documentation; start when the first `.aab` is available.
3. Google Cloud billing approval when deployed Functions or other paid Firebase services are required.

Do not block product/design/local development while a release-only gate waits.

## Cost disclosure

Before the user commits, identify likely costs and verify current prices/terms on official pages: Apple Developer annual membership, one-time Play Console registration, Firebase billing-card/Blaze requirements, per-call AI spend, RevenueCat plan thresholds, and optional domain/hosting costs. Explain that a billing budget alert is not a spending cap. Do the AI unit economics before model/pricing decisions; route to [security-cost.md](security-cost.md).

## Machine scan — read-only discovery

Detect before proposing changes. Do not install, configure credentials, or activate adapters during Phase 0. Every tool below is inspected from the installed system — schema discovery and version query only.

```bash
df -h /
git --version
flutter --version && dart --version
flutter doctor -v
xcodebuild -version
xcode-select -p
xcrun simctl list runtimes
pod --version
node --version
firebase --version
gcloud --version
asc --version
java -version
sdkmanager --version
adb version
flutter devices
```

### Per-tool read-only schema discovery (Phase 0 only)

No installation, credential, or adapter activation is required or requested during discovery. If a tool is not yet installed, note the gap and move on; skip any discovery that requires authentication.

**Flutter**: `flutter --version`, `flutter doctor -v`, `flutter devices` (lists connected physical devices and running simulators). Read-only.

**Firebase**: `firebase --version`, `firebase projects:list` (lists accessible projects). Skip unless Firebase is already authenticated.

**XcodeBuildMCP**: If installed (`npm list --global xcodebuildmcp 2>/dev/null`), discover live tool schemas with:
```bash
xcodebuildmcp --help 2>/dev/null || echo "not installed"
# After adapter activation, discover schemas via the persistent MCP server:
#   — project/workspace listing
#   — scheme/target discovery
#   — build/test/simulator/device tool schemas
# The harness template runs 'xcodebuildmcp mcp' as a persistent MCP server.
# All schemas are read-only metalanguage; no build is triggered.
```

**asc CLI**: If installed (`asc --version`), discover command schema with:
```bash
asc --help
asc search auth 2>/dev/null
# Read-only inventory:
asc auth status 2>/dev/null --validate
asc apps list --output table 2>/dev/null || echo "auth required"
```

**RevenueCat MCP**: Do not install, do not request credentials in Phase 0. The official MCP endpoint is `https://mcp.revenuecat.ai/mcp`. Read-only discovery means browsing the tool schemas after authentication in Phase 1. Refresh the official documentation at <https://www.revenuecat.com/docs/tools/mcp>.

**Android / Play tools**:
```bash
java -version
sdkmanager --version 2>/dev/null
sdkmanager --list 2>/dev/null | head -40  # package index (read-only listing)
adb version
flutter devices 2>/dev/null             # includes any connected Android
# Play Console/API: no read-only CLI screen. The official doc URL is
# https://developers.google.com/android-publisher . Identity verification
# and service-account setup are Human gates, not Phase 0 discovery.
```

Report the executable actually used for each tool. Never run a write command (build, upload, create, update, delete) during Phase 0.

Check only the platform tools in scope. Report the executable actually used. For keg-only Homebrew Node 24 and OpenJDK 17, inspect the verified formula prefix without modifying PATH, JAVA_HOME, or profiles. If a preferred candidate works but generic PATH is broken, report the candidate `PASS` and a separate operational environment `GAP`/`DEFER`; do not hide inheritance risk. npm-based installs must use verified Homebrew Node 24 npm and stop rather than run under unsupported Node versions. Verify adequate disk space for Xcode, simulators, Pods, archives, and Android SDK images. On Apple Silicon, check Rosetta only when a required tool needs it. Prefer current official installation instructions and each tool's `--help`; do not copy remembered package/platform versions.

For Android, obtain approval before installing the JDK, SDK packages, licenses, or emulator image. Prefer command-line tools unless the user wants Android Studio. Verify both `sdkmanager --version` and `<Android SDK>/cmdline-tools/latest/bin/sdkmanager`; a Homebrew command alone does not prove Flutter can find it. If only the Homebrew copy exists, bootstrap may copy it into a missing SDK destination after the separate `android-sdk-cmdline` approval and read-back. Do not use a symlink: `avdmanager` resolves the Homebrew location and can miss system images installed under the Flutter SDK root. A person must still review and accept licenses with `flutter doctor --android-licenses`. For the tested macOS arm64 toolchain on 2026-07-30, the verified emulator set was SDK package `emulator` 36.6.11 plus `system-images;android-36;google_apis;arm64-v8a` revision 7 and a Pixel 6 AVD. Revalidate package revisions with the installed `sdkmanager --list`; do not treat these as timeless requirements. End with a green Android toolchain in `flutter doctor -v` and at least one detected emulator/device before building an `.aab`.

For iOS, Xcode and its first-launch/license steps may require the App Store, GUI, or administrator password. Xcode is a release/build dependency, not a reason to idle during product work.

## Account and credential scan

Check for valid state without printing secret contents:

```bash
asc --help
# Discover the installed authentication/listing flow with `asc search auth` and command help.
firebase login:list
gcloud billing accounts list --filter=open=true
security find-identity -v -p codesigning
```

Also establish whether Apple Developer membership, Apple 2FA, Firebase/Google ownership, an AI-provider account, RevenueCat, and Play Console already exist. Never search broad user directories for secret values or echo keys. Ask the user for a secure credential location only when needed.

Success means:

- ASC authentication lists the team apps or a valid empty result.
- Firebase lists the intended account.
- An open billing account belongs to an identity authorized for the Firebase project.
- Apple membership is active when iOS distribution is in scope.
- Play Console identity verification is complete when Android distribution is in scope.

## App Store Connect API key

Treat key creation/download and moving the key as an approved Human gate; a Team API key is downloadable once. In App Store Connect use **Users and Access → Integrations → App Store Connect API → Team Keys**, create the least role that supports the required operations, and record Issuer ID + Key ID. Keep the `.p8` outside the repository with mode `600`; discover the installed `asc` authentication format from `asc search auth`, help, and schema output. Verify with the current supported read-only app/team query. Locate a freshly downloaded `.p8` only by filename, size, and modification time; never read its contents or macOS extended metadata such as Spotlight `kMDItemWhereFroms`, which can embed the complete key as a data URL in tool output. If any key material is exposed, treat the key as compromised: delete it and do not use it, then under a Human gate revoke and regenerate it with fresh exact single-use approval.

Do not create/revoke a distribution certificate or provisioning profile without approval. Verify existing signing identities first. Keep `.p8`, `.jks`, service-account JSON, `.env*`, and keystore properties out of Git before the first commit.

## Ready-to-build condition

Begin Phase 1 when the local Flutter path is usable and the Firebase/AI prerequisites required for development are available. Apple enrollment, ASC credentials, and Play production access block distribution, not design or implementation.
