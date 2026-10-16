---
name: architecture-qa
description: "Review OCI architecture diagrams and slides for service-to-icon accuracy, topology, boundary semantics, editable file integrity, and visual quality; apply before delivering OCI architecture drawings."
---

# Architecture QA

Read [OCI Architecture Core](../oci-architecture-core/SKILL.md) and [topology rules](../oci-architecture-core/references/topology.md). Review both the architecture model and the actual deliverable. Inspect the official source bytes when verifying artwork: metadata alone cannot prove icon fidelity.

Report each dimension separately as `PASS`, `FAIL`, or `NOT_VERIFIED`, with evidence and remaining assumptions. A failure or missing renderer must not be hidden behind one overall score.

| Dimension | Acceptance evidence |
| --- | --- |
| Asset identity | Official source provenance/hash; exact service label and source locator; no invented icon; aspect ratio, label, approved colors, and shape preserved |
| Topology | Region/realm and verified AD count; regional VCN/subnet versus AD/FD placement; correct managed-service/endpoint scope; required gateway, route, and security path; no unsupported HA/DR claim |
| Connections | Trace each critical flow from source to destination, direction, protocol/port, endpoint type, route and security dependency; distinguish data, administration, replication, and user interaction in the legend |
| File integrity | Native editable `.drawio` graph or `.pptx`; no dangling IDs/relationships; correct embedded media/stencils; file reopens; scoped changes preserve unrelated content |
| Visual quality | Rendered changed pages/slides inspected; readable labels/CIDRs, no clipping or unintended overlap, aligned elements, adequate padding, consistent connectors, unambiguous boundary crossings |
| Cross-format consistency | Compare stable model IDs, service meaning, instance counts, region, subnets, flows, status, and icon meaning across both formats when supplied; mark not applicable otherwise |
| Evidence honesty | Assumptions, unresolved icon mapping, unverified service availability, and unrun rendering/opening checks are visible; no claim of deployment, compliance, certification, or perfect architecture |

A neutral text box with a disclosed icon gap is acceptable for a draft, but cannot pass `official icon coverage` for that component. If toolkit files are unavailable in this release, do not claim asset identity was verified just because the catalog exists. The plugin includes no stencil binaries.

Distinguish a routing connection from demonstrated end-to-end reachability; a drawn NSG does not prove rules exist. Private endpoint support, lifecycle, realm/service availability, and region AD counts need current official documentation when they matter. Do not infer a production-ready topology from Oracle's toolkit examples.

Fix confirmed visual and structural defects within the requested edit scope. Ask before changing a material architecture decision when the source does not establish intended behavior. For review-only work, report findings without silently rewriting the design.

Deliver a short QA table with evidence, the actual files inspected, material findings ordered by consequence, assumptions needing an owner, and verification not run. Block claims of final correctness while a critical topology or artifact-integrity finding remains unresolved. Preserve a useful reviewable draft if a missing tool or source prevents full verification.
