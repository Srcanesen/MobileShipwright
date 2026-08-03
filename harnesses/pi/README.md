# Pi adapter

Pi core has no native MCP client. This repository uses the optional, separately approved `pi-mcp-adapter` extension instead of inventing a client or wrapper.

## Inactive RevenueCat template

The credential-free template is [`templates/mcp.json`](templates/mcp.json). It is inactive repository material; it is not copied or loaded automatically. The equivalent asset is [`../../skills/mobile-app-ship/assets/revenuecat.mcp.json`](../../skills/mobile-app-ship/assets/revenuecat.mcp.json).

The tested local adapter is `pi-mcp-adapter` `2.16.0`:

```bash
pi install npm:pi-mcp-adapter@2.16.0
```

Use the user-global Pi config at `~/.pi/agent/mcp.json`, not a project `.mcp.json`, after a separate approval. Merge only the RevenueCat entry from the template. Keep `lifecycle` lazy, `auth` OAuth, and `directTools` false. Pi must not start OAuth during repository validation.

In a new Pi session, run `/mcp` and confirm that RevenueCat is visible but not connected. Authentication is a separate step: `/mcp-auth revenuecat`. RevenueCat may reject an unregistered Pi OAuth client; do not retry blindly. Use RevenueCat support allowlisting or the documented read-only API v2 key through a user environment variable instead:

```json
{
  "auth": "bearer",
  "bearerTokenEnv": "REVENUECAT_API_V2_SECRET_KEY"
}
```

Never paste a key, token, redirect URL, or credential into chat or Git.

Pi's MCP adapter is a transport only. RevenueCat remains the owner of RevenueCat projects, apps, products, entitlements, offerings, packages, paywalls, and task state. Read-only discovery comes before any separately approved write. Every RevenueCat mutation still uses the playbook's exact single-use gate.

`/reload` is required after changing Pi MCP configuration. Do not run `pi-mcp-adapter init` during validation: it can import host-specific configs and write Pi-owned files. Review every proposed import before accepting it.

The package runs with full local permissions. Review the pinned package and config before activation. Do not add MCP credentials, OAuth state, generated caches, or local absolute paths to this repository.

Sources: [Pi MCP adapter](https://github.com/nicobailon/pi-mcp-adapter), [RevenueCat MCP setup](https://www.revenuecat.com/docs/tools/mcp/setup), and [RevenueCat MCP security guidance](https://www.revenuecat.com/docs/tools/mcp/best-practices-and-troubleshooting).
