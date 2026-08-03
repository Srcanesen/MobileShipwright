# Human gates

- **Approval-required:** the agent or tool can execute, but the user must approve one named external mutation first.
- **Manual-execution:** a person must perform the action.
- **Approval-and-manual:** both apply.

Onboarding decisions and selected scopes are future intent only. `--acknowledge-plan` records a SHA-256-bound acknowledgement of canonical decisions after complete readiness and read-back evidence. It is not vendor approval, cannot authorize Firebase, ASC, IAP, signing, screenshots, upload, TestFlight, submission, or release, and is invalidated by a decision change. `--approve-plan` is only a deprecated non-authorizing alias. `--check-scope` returns `future_intent_only` and cannot grant a write.

Every external mutation follows **Inspect -> Plan -> exact single-use approval -> Apply once -> Read back -> Evidence**. The gate names the exact mutation and target. In STATUS `1.1.0`, its linked action carries the same structured scope and verification query. A consumed gate backs at most one verified external mutation. Do not reuse it. A changed target, value, side effect, or read-back query requires a new gate.

`status-write --record-user-approval` only records an approval the human has already given. For an approved legacy pair without scope, it can record a fresh exact scope approval only when both action and gate gain the identical scope and a new approval timestamp. `status-write --consume-gate` only records the transition before a separately performed action; a legacy external action cannot start until that structured binding exists. Neither command authorizes a vendor request, contacts a vendor, or executes a mutation.

Public release defaults to `no` as future intent and always needs its own exact approval. Authentication proves identity only and never authorizes writes.
