# XcodeBuildMCP

Use XcodeBuildMCP for local Apple project/workspace discovery, build, test, simulator/device work, logs, and local diagnostics after signing exists. It cannot configure a team, signing, certificates, provisioning profiles, or Developer Portal capabilities.

## Live schema first

Start the installed MCP server and call `tools/list` before use. The names below are examples verified on XcodeBuildMCP 2.7.0; re-discover the running server's tools and parameter schemas before every scenario. Read each tool result and inspect the running app UI; a successful tool call alone is not evidence.

## Simulator scenario

After `tools/list`, use this capability sequence:

1. `session_set_defaults`
2. `list_sims`
3. `build_sim` and `test_sim`, or `build_run_sim`
4. `snapshot_ui` and `screenshot`

Boot and verify the selected simulator before install/launch/UI work. UI element references come from the latest `snapshot_ui` result; after navigation, a timeout, or `SNAPSHOT_EXPIRED`, take a fresh snapshot before any tap/touch. If the live schema exposes a screen-hash/change detector, use it to verify the rendered UI changed; do not pin an unverified field as permanent schema.

Record build/test results, runtime logs, the UI snapshot, and the screenshot. Inspect the actual rendered app; failed tests, launch failures, or an unexpected UI block advancement.

## Physical-device scenario

Only after signing is configured, use this capability sequence:

1. `list_devices`
2. `build_device` and `test_device`
3. `get_device_app_path`
4. `install_app_device`
5. `launch_app_device`

Read back every result. Record physical-device observation and device-log evidence that the app launched and behaved as expected. A local build does not prove upload processing or distributed behavior.

Fallback to direct `xcodebuild` is outside these MCP scenarios. It remains local Apple-tooling work and is not evidence that XcodeBuildMCP was exercised.

Consult [official documentation](https://xcodebuildmcp.com/docs) and the running server's live schemas before invoking tools. The harness template runs persistent installed `xcodebuildmcp mcp`; it does not download code at activation. Request explicit install and adapter-activation approval before copying or using a template, then perform read-only tool discovery first. Templates live under [`harnesses/`](../../../harnesses/) and remain inactive in this repository; see [harness onboarding](harness-onboarding.md).