---
name: oci-architecture-core
description: "Use for shared semantics and icon decisions when creating, editing, or reviewing OCI architecture drawings or architecture slides. Establish a consistent resource and connection model across draw.io and PowerPoint."
---

# OCI Architecture Core

Read [asset provenance and usage](references/official-assets.md) before using Oracle artwork. **This release contains no Oracle stencil or template binaries.** It contains source URLs, checksums, and metadata locators only. Never say stencils are bundled or generate a replacement Oracle icon.

## Start from the user's architecture

Infer purpose, audience, logical versus physical view, output format, and existing styling. Ask only for missing facts that materially change the design. For unknown region, service availability, CIDR, endpoint mode, or HA requirements, label an assumption or unresolved decision. Do not quietly add a landing zone, gateway, subnet, security appliance, or extra region.

Before drawing, maintain one compact architecture model with stable node IDs, exact service names, resource scope, region/realm, AD/FD where relevant, VCN/subnet membership, and directed edges with purpose/protocol/port where known. Record current/proposed status and sources. Use this same model and the same service-to-icon mapping for both formats. Review IaC or the supplied source diagram when available; a drawing alone does not prove runtime configuration.

## Resolve official icons deterministically

Use [icon-map.json](references/icon-map.json), a partial mapping verified against the pinned toolkit versions, and [toolkit-index.json](references/toolkit-index.json) for metadata lookup. Require an exact match between service meaning and the asset's own identification label. Check the source hash before trusting cell IDs or PowerPoint shape IDs; a hash mismatch calls for reindexing and review, not automatic rejection of a newer official toolkit.

The current Draw.io toolkit's **Icons** page is preferred over the older `OCI Library.xml`. Never substitute the Internet Gateway, NAT Gateway, Service Gateway, DRG, and Local Peering Gateway for each other. Treat Oracle Generative AI, Generative AI Agents, Agent Development Kit, and application agents as separate things; this snapshot does not establish an icon for every newer service. IDCS is not automatically a current IAM Identity Domains icon. A generic private endpoint icon does not prove a service supports private access.

For draw.io, first obtain the real official toolkit using the runtime procedure in [official-assets.md](references/official-assets.md): reuse verified task inputs/cache or download it from Oracle with `scripts/fetch_drawio_toolkit.py`. Do not treat a missing attachment as a reason to skip available official stencils.

If the verified toolkit has no exact matching icon, use a clearly labeled neutral text component and record `icon unavailable in verified official toolkit` with the searched labels and toolkit hash. A missing toolkit is not an icon gap. If the user explicitly requires official stencils and retrieval fails, report the blocker and preserve a draft; do not claim an icon-free draft satisfies that requirement. Do not draw an invented pictogram, guess a `mxgraph` shape name, relabel an unrelated icon, scrape an unofficial icon collection, or claim the neutral box is an official icon.

## Keep scope and connectivity correct

Apply [topology rules](references/topology.md). Geographic placement, network membership, and compartment ownership are different relationships, not one universal nesting tree. Prefer an explicit overlay or linked views when boundaries intersect. A regional VCN or regional subnet must not appear constrained to a single AD/FD. Place service endpoints separately from regional managed services, with their access paths made clear.

Consult current official OCI docs for named-region AD counts, service availability, endpoint behavior, lifecycle, or unfamiliar connectivity. The toolkit is a visual source, not evidence that an example topology is technically correct. Record what was verified and what remains assumed.

## Preserve Oracle's visual language

Use [style rules](references/style.md) and inspect the supplied template. Keep approved source artwork, aspect ratios, shape geometry, labels, theme, and connector conventions. Preserve the user's existing layout/style unless a requested change or concrete defect warrants an adjustment. Do not claim a supplied nonstandard drawing meets Oracle conventions until reviewed.

Route to [Draw.io Designer](../oci-drawio-designer/SKILL.md) for `.drawio`, [PowerPoint Designer](../oci-powerpoint-designer/SKILL.md) for `.pptx`, and [Architecture QA](../architecture-qa/SKILL.md) before delivery. Include editable files, a short list of assumptions and icon gaps, source toolkit identity, and actual verification performed. Do not promise perfect architecture or certification.
