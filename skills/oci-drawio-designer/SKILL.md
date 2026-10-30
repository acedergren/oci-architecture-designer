---
name: oci-drawio-designer
description: "Use when creating or editing native editable OCI .drawio diagrams from requirements, IaC, or existing diagrams with verified official stencils."
---

# OCI Draw.io Designer

Read [Core](../oci-architecture-core/SKILL.md) for model, provenance, selective icon lookup and topology. Use the official toolkit's Icons, Physical and Logical pages as appropriate; the older OCI Library.xml has different coverage. Reuse verified inputs/cache or run, relative to this skill:

```sh
python3 ../oci-architecture-core/scripts/fetch_drawio_toolkit.py --cache-dir /path/to/task/cache/official-oci
python3 ../oci-architecture-core/scripts/lookup_assets.py --service 'Compute virtual machine' --format drawio --sha256 SOURCE_FILE_HASH
```

Use the extracted .drawio file hash, not the ZIP hash. Reindex new verified inputs using `catalog_assets.py --drawio /path/to/toolkit.drawio --output /path/to/catalog.json`. Catalogs contain metadata, not artwork.

For a substantive design, draw the selected model and reference its requirement/decision IDs. Keep competing alternatives in separately labeled views; do not mix proposed alternatives with deployed components.

## Build the native graph

Copy complete original groups and descendants with embedded stencil/image payloads. Remap IDs, parent, source and target references; preserve internal relative coordinates, labels and aspect ratio. Move/scale each group as a unit; add resource-specific text separately. Record node-to-source locators in delivery evidence. Support plain mxCell and UserObject/object wrappers; compressed pages are base64, raw DEFLATE, then URL-decoded UTF-8.

Use named mxfile pages, native containers/text and attached mxCell edges. Preserve geographic/network semantics when boundaries cross. Use readable orthogonal connectors and sufficient space for labels/CIDRs; split dense drawings into linked detail pages. Never flatten the whole graph to an image or use neutral boxes in place of available exact icons. Make scoped edits without replacing unrelated content.

## Verify

Run `python3 validate_drawio.py /path/to/result.drawio`. Exit 0 means structural checks passed; 1 means failure. Intentional annotation lines flagged as unattached require separate manual review and must not be mistaken for proven traffic paths.

Open in draw.io, inspect every changed page and labels, export a preview and inspect it. Move a node, save and reopen: confirm its connector remains attached and follows the node. Retain the original deliverable separately from this test copy. Record opening, visual and editability checks independently; absent tools mean NOT_VERIFIED. Apply [QA](../architecture-qa/SKILL.md), deliver the native file and evidence.
