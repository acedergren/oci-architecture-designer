# Architecture reasoning acceptance exercises

Use the requests in [architecture-requests.json](fixtures/architecture-requests.json) with the current Core/QA skills. These are synthetic, human-reviewed behavior exercises; they are not another automated Python test suite. Preserve raw responses and review evidence outside the distributed plugin. Do not infer general architecture quality from a small sample.

A reviewer should check consequences and decision traceability, not match words or headings:

| Case | Acceptance evidence |
| --- | --- |
| internal-existing-platform | Uses established foundation and supported capabilities or explains a requirement-based departure; preserves private DNS/administration dependencies; makes a proportionate runtime choice; recovery targets remain unmeasured until tested. |
| region-loss-constraint-conflict | Does not approve region-loss RTO/RPO from same-AD nodes/backups or a MAA label; exposes the contradictory protection/location constraints; asks the responsible owner for the material decision and identifies version/entitlement/testing gaps without silently changing scope. |
| sovereign-ai-current-evidence-missing | Offers a bounded model; availability/private access remain unverified; per-team document authorization and evaluation matter; no automatic replication of every reference-architecture service. |
| layout-only-preserve-accepted-model | Limits work to alignment/labels and affected-file checks; requests the missing file; preserves page two and accepted decisions; no broad discovery questionnaire or fabricated artifact. |
| async-integration-business-completion | Separates durable acceptance from ERP completion; addresses idempotency, per-customer ordering, retry/replay and failure ownership; reuses relevant existing services; delivery/throughput claims need evidence. |
| c4-context-versus-deployment | Separates sponsor/context, application boundaries and OCI deployment; does not equate C4 containers with a runtime; selects only useful views and identifies a workload basis for runtime choice. |

For substantive design cases, inspect that material choices have requirement/context, plausible alternatives, consequences/owner and source applicability. A missing fact may stay a labeled assumption; a material conflict needs a decision. Current-fact claims require primary sources for the specific scope, not merely a generic index URL. For review-only and layout-only cases, respect their narrower action boundary.
