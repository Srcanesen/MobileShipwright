# State and evidence

`targets.ios` and `targets.android` each own a current lifecycle state, ordered history, and nullable blocker overlay. A blocker does not replace or advance lifecycle state. Each history event names its action when applicable and evidence IDs. Follow lifecycle order in [workflow-lifecycle.md](workflow-lifecycle.md).

A timeout/interruption becomes `outcome_unknown`; read vendor state before retry. `verified` means the verification query ran and supports the claim. Every verified `external_mutation` references one consumed standard gate with a UTC `approvedAt`, an exact matching target, a non-empty verification query, and read-back or human-observation evidence. A consumed gate can back one verified external mutation only. Gate `action` is the exact approved action; an action `intent` may remain concise.

`RELEASED` requires prior `RELEASE_AUTHORIZED`, a verified external release action, a separately consumed matching release gate, and release/storefront read-back evidence. Onboarding acknowledgement and selected future scopes never replace a gate.

Each gate has a stable `id`, class (`approval_required`, `manual_execution`, or `approval_and_manual`), action, target, state (`pending`, `approved`, `consumed`, or `revoked`), and approval timestamp. A pending manual step belongs in the blocker overlay. Follow [human-gates.md](human-gates.md) for canonical classification.

STATUS `1.0.0` records remain valid unchanged. In `1.1.0`, a structured external mutation may bind action and gate with the same `scope`: provider-qualified resource, canonical operation, sorted side effects, and verification query. Both sides must carry exactly the same scope; the action target and query must match it. Scope-less historical pairs are legacy/unbound, not invalid or migrated automatically. A planned legacy pair may gain scope during its first approval; an approved legacy pair requires a fresh exact approval and a new approval timestamp before it can gain scope or be consumed. Coverage reports binding counts only; it does not emit a readiness score or infer vendor state.
