---
name: architecture-qa
description: "Use when reviewing OCI architecture decisions, diagrams, slides or architecture images (arkitekturbilder), and before delivery; check requirement fit, evidence, semantics and visual quality separately."
---

# Architecture QA

Read [Core](../oci-architecture-core/SKILL.md) and use [delivery evidence](../oci-architecture-core/references/delivery-evidence.md). For substantive design/review work, apply the [workload architecture review](../oci-architecture-core/references/architecture-review.md) and inspect requirements, material decisions and the actual model/deliverable. A review-only request reports findings; a layout-only edit checks the affected artifact without reopening the design. Metadata alone does not verify artwork; a parser pass does not verify layout or application behavior.

For model-specific review use the relevant [OpenAI profile](../oci-architecture-core/references/openai-model-profiles.md). For PNG/SVG exports or generated illustrations, apply [image delivery](../oci-architecture-core/references/image-delivery.md): compare the actual saved image with the fixed model, including exact resource counts/labels, boundary membership and each arrow's endpoints/direction. Inspect unchanged areas after edits. The generating agent's assurance, a plausible icon or a successful generation call is not evidence of correctness.

Report each dimension separately as PASS, FAIL or NOT_VERIFIED with method and evidence. Use NOT_APPLICABLE only for irrelevant dimensions, never missing tools.

| Dimension | Evidence required |
| --- | --- |
| Requirement fit | Identified requirements/constraints, accepted versus proposed scope, reused platform, unresolved conflicts and decision owners |
| Design decisions | Significant choices traced to requirements, realistic alternatives/tradeoffs, source applicability and validation; added complexity has a purpose and operator |
| Workload behavior | Relevant Well-Architected areas examined; critical request/data flow and failure/recovery dependencies reviewed; stated RTO/RPO are not presented as measured without evidence |
| Asset identity | Source bytes/hash; node, exact label and locator; preserved group geometry/colors; disclosed true icon gaps |
| Topology | Correct region/realm, regional versus AD placement, managed-service/endpoint scope, required routing/security dependencies; current sources for volatile facts |
| Connections | Trace each critical directed flow, purpose, protocol/port, endpoint and dependencies; distinguish data, administration and replication |
| File integrity | Native format validator with no dangling IDs/relationships; for images, decode actual bytes and inspect dimensions; validate an export's native source separately |
| Application opening | Actual saved/reopened file in a named application/viewer; distinguish an image viewer, a converter and the native editor |
| Visual quality | Rendered changed pages/slides inspected for clipping, overlap, label readability and unambiguous boundaries/connectors |
| Editability | Move a node in a test copy, save/reopen and observe connector attachment/following |
| Cross-format consistency | Compare stable IDs, service meaning, counts, boundaries, flows, status and icon meaning; NOT_APPLICABLE for a single format |
| Evidence honesty | Assumptions, missing checks, exact icon gaps and service availability uncertainty disclosed |

For an advisory review with no diagram, mark file/artwork/visual dimensions NOT_APPLICABLE with the reason; do not fabricate a deliverable. Missing evidence for an applicable requirement remains NOT_VERIFIED.

For an image-only request, native editability is NOT_APPLICABLE with reason. If editable nodes/connectors were required, an image alone fails requirement fit and editability. Generated illustration symbols do not pass official-asset identity; use NOT_APPLICABLE only when official artwork is outside the request. A technical export retains provenance but does not prove connector movement. For multiple delivered representations compare semantic consistency. Model identity is observed from tool/runtime evidence, otherwise null/NOT_VERIFIED; a model named in a prompt or the active text model does not identify the image backend.

Use available official toolkit retrieval before claiming stencils are unavailable. A neutral exact-service gap may be acceptable in a draft but cannot pass official icon coverage for that node. A drawing or NSG symbol does not prove reachability, rules, deployment or production readiness.

Fix confirmed defects within the requested edit scope. For review-only work, report findings without rewriting. Ask before changing a material architecture decision whose intended behavior is unknown. Deliver a short evidence table, actual files inspected, findings by consequence and unresolved assumptions. Critical topology/file-integrity failures block final-correctness claims; keep a useful draft when verification is blocked.
