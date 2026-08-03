# Windsurf adapter

Inactive review template: [templates/mcp_config.json](templates/mcp_config.json). It is not loaded from this repository and the bootstrap adapter is unsupported/manual.

Windsurf's documented MCP file is user-global, `~/.codeium/windsurf/mcp_config.json`. There is no project MCP destination. Bootstrap must never create `.windsurf/mcp_config.json`, write the global file, or merge configuration. Human gate: review the repository template, manually merge only approved entries into the exact global destination, restart Windsurf, and confirm the servers appear without exposing credentials. Use native browser OAuth for RevenueCat when Windsurf offers it.

The XcodeBuildMCP entry runs persistent installed `xcodebuildmcp mcp`. Request explicit install and adapter-activation approval first; it never downloads at activation. Discover live tool schemas before use. Never add secrets to this template.

Return to [the canonical skill](../../skills/mobile-app-ship/SKILL.md).
