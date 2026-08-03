# Conditional Administration

Load only when app data needs external management (for example moderation, credits, catalog/pricing, or legal text), or when a one-off privileged data task is proposed.

## Hosted admin panel

1. Ask which management operations are needed. Do not build a panel for speculative use.
2. Build the selected scope as a hosted web app with admin authentication.
3. Grant an **admin role** through a custom claim or another server-controlled secure role. Check it in server-side functions and least-privilege rules. Do **not** use a client-writable Firestore `is_admin` flag.
4. Keep sensitive writes (credits, deletion, moderation) server-authorized and auditable; never trust the browser alone.
5. Treat enabling an auth provider, assigning the first role, and deployment as approved Human gates.

## One-off privileged task: last resort

Prefer a safer local/admin SDK path with constrained credentials first. If it cannot work, use a temporary server function only after explicit approval to deploy, call, and delete it:

- Require authenticated, authorized callers; a non-guessable token alone is not authorization.
- Grant only the minimum operation and scope, record an audit event, and do not expose broad admin access.
- Call it once, verify the result, then delete it immediately. Confirm deletion before closing the task.
