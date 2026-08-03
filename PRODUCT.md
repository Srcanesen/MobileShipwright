# Product Boundary

This repository is a **high-risk mobile shipping workflow coordinator**. It coordinates evidence, state, and human gates for app shipping. It is **not a release/upload wrapper** and **not an autonomous shipping system**. Direct vendor tools remain responsible for vendor operations.

## Coverage Matrix

| Work area | Coordinator coverage |
| --- | --- |
| terminal_managed | Local inspection, validation, and coordination records. |
| terminal_guided | External mutations plus approval/manual gates. |
| vendor_readback | Verification queries and sanitized store read-back evidence. |
| physical_review_wait | Human observation and device/store-review waiting states. |

Coverage reports responsibility counts, not readiness: no numeric score, percentage, or 10-of-10 claim is emitted.

## Success Metrics

Measure gate violations, unknown retries, rework incidents, time-to-first-preflight, and release-cycle duration for each project.
