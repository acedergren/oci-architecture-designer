---
name: architecture-qa
description: "Use when reviewing OCI diagrams or slides, and before delivery, to check icon identity, topology, native file integrity and visual quality separately."
---

# Architecture QA

Read [Core](../oci-architecture-core/SKILL.md) and use [delivery evidence](../oci-architecture-core/references/delivery-evidence.md). Inspect both the model and actual deliverable. Metadata alone does not verify artwork; a parser pass does not verify layout or application behavior.

Report each dimension separately as PASS, FAIL or NOT_VERIFIED with method and evidence. Use NOT_APPLICABLE only for irrelevant dimensions, never missing tools.

| Dimension | Evidence required |
| --- | --- |
| Asset identity | Source bytes/hash; node, exact label and locator; preserved group geometry/colors; disclosed true icon gaps |
| Topology | Correct region/realm, regional versus AD placement, managed-service/endpoint scope, required routing/security dependencies; current sources for volatile facts |
| Connections | Trace each critical directed flow, purpose, protocol/port, endpoint and dependencies; distinguish data, administration and replication |
| File integrity | Format validator, no dangling IDs/relationships; embedded artwork and native graph preserved |
| Application opening | Actual application and saved/reopened file; parser-only checks are separate |
| Visual quality | Rendered changed pages/slides inspected for clipping, overlap, label readability and unambiguous boundaries/connectors |
| Editability | Move a node in a test copy, save/reopen and observe connector attachment/following |
| Cross-format consistency | Compare stable IDs, service meaning, counts, boundaries, flows, status and icon meaning; NOT_APPLICABLE for a single format |
| Evidence honesty | Assumptions, missing checks, exact icon gaps and service availability uncertainty disclosed |

Use available official toolkit retrieval before claiming stencils are unavailable. A neutral exact-service gap may be acceptable in a draft but cannot pass official icon coverage for that node. A drawing or NSG symbol does not prove reachability, rules, deployment or production readiness.

Fix confirmed defects within the requested edit scope. For review-only work, report findings without rewriting. Ask before changing a material architecture decision whose intended behavior is unknown. Deliver a short evidence table, actual files inspected, findings by consequence and unresolved assumptions. Critical topology/file-integrity failures block final-correctness claims; keep a useful draft when verification is blocked.
