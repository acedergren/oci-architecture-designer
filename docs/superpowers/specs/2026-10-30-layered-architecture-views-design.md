# Layered architecture views — design

Status: proposed implementation specification; planning only. Date: 2026-10-30.

## Goal and scope

Make OCI diagrams easier to understand, maintain, edit and review through optional layers, explicit views and controlled exports. Retain the four existing skills, one architecture model, stable semantic IDs, native artwork groups, attached connectors and editable PowerPoint output. Retain Redwood as the style reference and the OCI toolkit as the icon/notation reference.

The user's latest baseline choice includes reconciling the existing project Git checkout with the inspected, artwork-free public 0.2.1 source before implementing the extension. Internal/shared runtime behavior is based on the inspected 0.2.4 sources. No new release version is selected.

## Decisions

| Area | Decision |
| --- | --- |
| Proportionality | Use layers only for a concrete independent hide/show, edit-protection or export need. A simple drawing may keep its single default layer. No numeric complexity threshold. |
| Pages versus layers | Pages separate audience questions, abstraction levels and materially different architectures. Layers organize presentation/editing within a page; they do not encode OCI containment or architectural correctness. |
| Layer vocabulary | Prefer Infrastructure, Workloads, Flows and Annotations when applicable; create only needed layers. A containment tree may combine infrastructure and workloads on one layer. Preserve existing meaningful names/IDs. |
| Containment | An object has one layer through its ancestry. Keep every native container/group and its descendants together. Never pull a workload out of its VCN/subnet or split original icon groups merely to satisfy layer names. Keep geographic, network and compartment semantics distinct. |
| Scoped edits | Inventory existing IDs, parents, geometry, artwork and visibility/lock states before editing. Protect accepted content outside the requested scope. Locks reduce accidental editing; normalized before/after comparison supplies preservation evidence. If a lock also freezes workloads that must change, choose a safe smaller unit or explicitly unlock the necessary layer within scope. |
| Current/proposed | Prefer separate labeled pages for substantial changes. Same-page variant layers are optional for small alternatives with compatible placement. Duplicate a complete safe subtree, assign unique graph IDs, retain semantic mappings, switch its associated flows/labels together, and never save/export both alternatives as an unlabeled mixture. |
| Views and exports | Name each delivered view and declare every layer visible or hidden. Specify its purpose/status, required cells/flows and deliberate omissions. Check the selected state immediately before each export. Restore the declared saved view afterward. Hidden content remains in the native file and is not a redaction boundary. |
| PowerPoint | One native editable slide per selected view, using the same semantic model and view ID. Native text, boundaries and attached connectors remain editable; disclosed source SVG/images retain their existing limitations. No whole-diagram rasterization or promise of Draw.io layer interaction in PPTX. |
| Interaction | Ordinary Layers controls only in this upgrade. Custom links, animations and in-diagram toggles require a separate demonstrated use case. |
| Typography | Oracle Sans for native diagram labels, boundaries, flow labels, legends and annotations. Use real Regular/Semibold/Bold faces as appropriate. Preserve a verified Oracle template's Georgia title treatment only for its presentation title areas; it does not replace Oracle Sans diagram text. No silent Arial, Calibri, Helvetica or Open Sans fallback. |
| Font fidelity | Check explicit styles, inherited theme/layout/run formatting, application resolution and exports. Naming a font is not proof it rendered. Preserve original artwork/SVG/logo lettering; normalize only native text in the output copy, preserving content and geometry and inspecting reflow. Do not modify source toolkits or distribute/install/embed font binaries as part of this change. Missing fonts leave typography unverified and block a corporate-font acceptance claim. |
| Verification | Extend the existing Draw.io validator for declared layer/view structure. Retain independent opening, visual, editability, export, typography and architecture judgments. Do not build a renderer, automatic exporter or general font-resolution engine. |

## Approaches considered

1. Guidance alone: smallest change, but cannot catch stale view declarations or required flows hidden during delivery.
2. **Selected proposal: compact guidance plus an optional view sidecar and focused validator checks.** Makes intent reviewable while keeping legacy/simple files usable. The user supplied this direction; the exact sidecar contract is the planner's recommendation.
3. Mandatory layer templates, interactive toggles and full export automation: add maintenance and runtime complexity without a demonstrated need; excluded.

## Acceptance

- Existing single-layer, compressed and wrapped-cell files retain their existing structural outcomes without a sidecar.
- Declared views reject missing/unknown/overlapping layer states, stale required IDs, incorrect saved visibility/locks and visible flows with hidden endpoints. Valid attached cross-layer connectors pass.
- A representative artifact keeps native VCN/subnet ancestry and icon groups, protects content outside scope, and proves visibility, locking, export, save/reopen and one connector-following edit in a test copy.
- Each selected view's PPTX slide matches its declared semantic subset. All changed pages/slides and exports have readable native text and verified corporate typography.
- Public code contains no Oracle artwork, font files, internal supplemental catalog/metadata or account-specific package identifiers. Internal/shared copies retain their own distribution and provenance procedures.
- Missing checks remain NOT_VERIFIED. Quality benefit and token savings remain hypotheses; no broad benchmark is required.

## Exclusions and evidence limits

No implementation, baseline import, dependency/font installation, worktree, push, release bump, packaging publication or account update occurs during planning. Preserve unrelated work, source material, ordinary installations and caches. Future implementation uses the existing Git tree with scoped commits. Release preparation is a later step after acceptance.

Layer locks are editing aids, not access control. The view sidecar cannot infer whether an author omitted a necessary architectural dependency; QA must compare it with the accepted model. A passing structural check cannot prove rendering, font substitution behavior, reachability or deployment readiness.

## Primary references

- [Oracle: Layered architecture diagrams with Draw.io](https://blogs.oracle.com/cloud-infrastructure/layered-architecture-diagrams-drawio), 2023-04-03; checked 2026-10-30. Supports naming, hiding, locking and deliberate exports; its example layering is not an OCI containment rule.
- [Draw.io: How layers work](https://www.drawio.com/docs/manual/layers/how-layers-work/), checked 2026-10-30. Establishes single-layer ancestry, container/group constraints and cross-layer connectors.
- [Draw.io graph model](https://github.com/jgraph/drawio/wiki/Graph-Model), checked 2026-10-30. Layer cells are root children; persisted visibility and lock styles must be read correctly.
- [Draw.io: Interactive diagrams](https://www.drawio.com/docs/tutorials/interactive-diagram-layers/), checked 2026-10-30. Documents optional custom links and visibility/style interactions; deferred here.
- [Oracle toolkit source page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm). Inspected pinned PowerPoint toolkit slide 5 specifies Oracle Sans for diagram text; actual source template/theme roles require inspection rather than assuming every legacy font is current guidance.
- [Oracle on its primary font](https://blogs.oracle.com/marketingcloud/email-marketing-font-stacks-defining-your-font-family). Supports Oracle Sans identity; diagram-specific rules come from the toolkit.
