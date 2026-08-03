# Contributing

Keep root public documentation outside the skill. Keep one Agent Skill at `skills/mobile-app-ship/SKILL.md`; frontmatter contains only `name` and `description`. Use concise progressive disclosure and flat `references/` files.

- Preserve one canonical authority each for lifecycle, state/evidence, human gates, and tool ownership.
- Restore durable operational detail; do not replace procedures with shallow summaries or duplicate the same authority.
- Use direct vendor tools. Do not add a release CLI, MCP proxy, REST wrapper, daemon, or store adapter.
- Do not invent commands or claim API/portal limitations without durable evidence. Discover volatile capability at runtime and use a Human gate when uncertain.
- Cite official primary-source URLs. For volatile platform, role, policy, command, price, version, or review claims, include a `verifiedAt: YYYY-MM-DD` note near the claim or label it a planning baseline that requires live verification.
- Keep validation Python-stdlib-only, offline, deterministic, and read-only. Update valid and meaningful invalid fixtures when state/lifecycle rules change.
- Never add credentials, raw credential paths, personal data, local absolute paths, build outputs, or outbound mutation automation. Pi MCP support must remain an optional user-global `pi-mcp-adapter` fallback; keep its server entry lazy, proxy-only, credential-free, and outside project configuration. Pin CI actions to reviewed commit SHAs and keep `persist-credentials: false`.

Run all commands in [README.md](README.md#validation) before proposing a change. Also run the repository's targeted secret scan, inspect CI permissions and action pins, validate both STATUS 1.0 and 1.1 fixtures, verify Pi template/asset parity, and inspect status/diff stat/reference sizes.
