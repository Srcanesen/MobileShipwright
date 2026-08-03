# Security and Cost for Backend or Paid AI

Load only when the app has a backend or a paid AI call.

- Keep provider keys server-side. Authenticate callers, authorize each operation server-side, and apply least-privilege Firestore, Storage, IAM, and function access.
- Use Firebase App Check where it applies; register and validate before enforcing it. App Check complements, never replaces, authentication and authorization.
- Add server-side abuse controls appropriate to the product: per-user/IP rate limits, quotas, and bounded work. Do not trust a client credit balance or client-only entitlement.
- Before choosing a model or plan, calculate provider cost per user action × expected actions per user/month, then include store fees, free credits, retries, refunds, and target margin. Record prices/limits in `DECISIONS.md`.
- For paid AI, set a cloud budget alert and track provider spend before exposing the call. Alerts notify after measured spend; they do **not** cap, reverse, or guarantee prevention of charges. Set explicit provider limits/quotas where supported. A paid call reachable from anonymous/free paths must have server rate limits and a budget alert.
- Enforce consent at the last shared server/network boundary, default deny, and strip uid/email/device identifiers from AI payloads unless the feature strictly needs them and disclosure covers them.
- Design loading, error, bounded retry, quota-exhausted, provider-timeout, and consent-declined states. Ask for push permission only when a user understands its value, not at launch; use push only when relevant.
- Treat enabling App Check/auth providers and deploying changes as approved Human gates.
