---
name: oci-powerpoint-designer
description: "Use when creating or editing editable OCI .pptx architecture slides with verified official Oracle artwork and templates."
---

# OCI PowerPoint Designer

Read [Core](../oci-architecture-core/SKILL.md). Reuse a verified official local toolkit or fetch one, relative to this skill:

```sh
python3 ../oci-architecture-core/scripts/fetch_pptx_toolkit.py --cache-dir /path/to/task/cache/official-oci
python3 ../oci-architecture-core/scripts/lookup_assets.py --service 'Compute virtual machine' --format pptx --sha256 SOURCE_FILE_HASH
```

On retrieval failure request the relevant input and preserve a labeled draft. Follow Core's hash-change and icon-gap rules. Reindex new files with `catalog_assets.py --pptx /path/to/OCI_Icons.pptx --output /path/to/catalog.json`; inspect source groups, not just metadata.

For a substantive design, draw the selected model and reference its requirement/decision IDs. Keep competing alternatives in separately labeled views; do not mix proposed alternatives with deployed components.

## Keep the deck editable

Inspect actual source slide order, layouts and theme. In the pinned April 2024 source, slide 5 describes colors/fonts, 18–23 notation, 24–25 logical canvases, 27–28 physical canvases and 34–47 icon categories. These positions are not stable across new toolkits.

Clone a suitable source template preserving slide size, masters/layouts, colors, typography and copyright. Copy complete official groups with internal geometry and labels. Remap shape IDs and all OOXML relationships/media/theme dependencies. Preserve aspect ratio; add resource-specific labels separately. Do not rasterize the complete architecture. If an original asset is an image, preserve it faithfully and disclose that limitation.

Use native text, boundaries and attached connectors. Keep the same stable model IDs, services, counts, scope and flows as the .drawio view; put detail on another slide instead of dropping a route. Preserve unrelated slides and the user's design during edits.

Attach connectors to actual shape connection sites inside a copied group; a group ID alone can parse correctly without following group movement in PowerPoint. Preserve namespace bindings used in markup-compatibility Requires/Ignorable attributes when copying XML. Keep OPC content-type and relationship roots in their original default namespaces for renderer compatibility.

## Verify

Run `python3 validate_pptx.py /path/to/result.pptx`. JSON reports internal package/shape/connector checks, slide order and external relationships separately; exit 0/1 indicates structural pass/failure. External links are not fetched. This is not full OOXML schema validation and does not prove rendering or editability.

Reopen in a presentation parser and application when available. Render and inspect every changed slide at presentation size. On a test copy, move a node, save and reopen; confirm the attached connector follows. Record parser, application opening, rendering, visual inspection and editability separately. Missing tools leave NOT_VERIFIED. Apply [QA](../architecture-qa/SKILL.md) and deliver the editable file and evidence.
