# Security Policy

Never commit, paste into documentation, or add to fixtures:

- API keys, OAuth tokens, passwords, shared secrets, or webhook secrets;
- private keys, certificates, provisioning profiles, keystores, signing passwords, or `key.properties`;
- Apple IAP/ASC key files, Play/Firebase service-account JSON, `.env*`, or raw credential paths;
- personal data, unsanitized vendor responses, target-app state, or built app artifacts.

Use OAuth where supported. Otherwise keep scoped credentials in vendor-approved keychains, environment variables, or user-level configuration outside Git. Public mobile SDK keys may be shipped only when the vendor documents them as public; never confuse them with secret API keys. Evidence must contain sanitized results and explicit limitations.

Report a suspected vulnerability privately through the repository host's private vulnerability reporting channel when enabled, or directly to the repository owner. Do not open a public issue containing secrets or exploit details. Rotate exposed credentials with the owning vendor and keep incident records outside this repository.

The playbook requires scoped approval for external mutations and destructive actions. Credential creation/download/upload, billing/legal decisions, and physical-device observations remain manual-sensitive gates.

Pi MCP is an optional user-global integration. Pi core has no native MCP; if `pi-mcp-adapter` is enabled, pin the reviewed package version, keep configuration in `~/.pi/agent/mcp.json`, use lazy proxy mode, and never commit credentials or OAuth state. Project-local MCP configuration is executable after project trust and is not an acceptable substitute. CI actions must use reviewed immutable commit SHAs, disable unnecessary credential persistence, and keep least-privilege permissions.
