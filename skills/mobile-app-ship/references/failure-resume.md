# Failure and Resume

Read the full failure, identify root cause, make one targeted change, then read state again. After two failed attempts, stop and reassess. Never blind-retry a remote mutation.

A timeout or interrupted command is `outcome_unknown`. Query the vendor's current state before retrying, especially for uploads, submissions, releases, cancellation, deploys, and review actions. Record the query and outcome.

For a local build/test timeout, read-back means inspecting the expected artifact on disk (existence and hash/metadata), not the exit code. If the artifact is absent, record failure or `outcome_unknown` as appropriate; after state inspection, at most one deliberate retry may benefit from warmed caches. An exit code alone is not evidence.

Resume by reading target-app `SPEC.md`, `DECISIONS.md`, and its one selected progress record. Confirm each platform lifecycle state and blocker, then choose the next reversible step. Use [pitfalls.md](pitfalls.md) for known symptoms.
