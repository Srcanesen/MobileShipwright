# Claude Code adapter

Inactive template: [templates/.mcp.json](templates/.mcp.json). It is not loaded from this repository.

After approval, copy it to the chosen project's `.mcp.json`; Claude Code supports project-local configuration. Do not merge it into a user/global file from this toolkit. The RevenueCat entry uses the official remote endpoint and should use Claude Code's browser OAuth flow when prompted.

The XcodeBuildMCP entry runs persistent installed `xcodebuildmcp mcp`. Request explicit install and adapter-activation approval first; it never downloads at activation. After activation, discover its live tools before use. Never add secrets to this template.

Return to [the canonical skill](../../skills/mobile-app-ship/SKILL.md).
