---
name: oci-powerpoint-designer
description: "Create or edit editable .pptx OCI architecture slides using official Oracle architecture graphics and templates supplied by the user, preserving their visual language."
---

# OCI PowerPoint Designer

Read [OCI Architecture Core](../oci-architecture-core/SKILL.md) and use its shared architecture and icon mapping. This release does **not** bundle `OCI_Icons.pptx`. Obtain the official file from the user or create a clearly labeled icon-free draft; never claim an invented symbol is Oracle artwork.

## Start from the actual Oracle source

Inspect the source presentation, its real slide order, layouts, theme, and grouped shapes. For the pinned April 2024 file, slide 5 defines palette/fonts, slides 18–23 define physical notation and icon handling, slides 24–25 provide logical blank canvases, slides 27–28 physical blank canvases, and slides 34–47 contain icon categories. Pin and inspect actual bytes; slide numbers and shape IDs may change in newer files.

Use [icon-map.json](../oci-architecture-core/references/icon-map.json) to locate exact label/slide/shape IDs after confirming the source hash. The source can contain multiple same-label groups or color variants; inspect rather than arbitrarily substituting. Reindex with `catalog_assets.py --pptx /path/to/OCI_Icons.pptx --output /path/to/catalog.json` from the core scripts directory when needed.

## Keep the presentation editable

Clone a suitable source template slide, preserving slide size, theme, master/layout relationships, approved colors, typography, and copyright notices. Copy complete official icon groups including labels and internal geometry. Preserve aspect ratios. Remap OOXML relationships, media, shape IDs, and theme references when copying between presentations; copying an XML node without its dependencies can corrupt the file or silently change its look.

Use native editable text, containers, and connectors. Official vector group paths are preferred. Do not rasterize the complete architecture onto a slide. If a particular official asset is itself an image, preserve that asset faithfully while keeping the surrounding nodes, labels, and connectors editable, and disclose the limitation when relevant. Do not pretend a flat picture can be edited as individual OCI components.

Keep the architecture model consistent with any `.drawio` counterpart: same services, counts, boundaries, directions, and assumptions. Preserve the user's deck design unless asked to restyle it. An overview slide may abstract detail only with an explicit link or note identifying the more detailed view. Reduce clutter by using a detail slide, not by dropping a required route or security boundary.

## Verify and deliver

Check the PPTX ZIP and all internal relationship targets, reopen it in a presentation parser, and confirm slides, notes, text, shapes, groups, and connectors survive. Render all changed slides with a presentation renderer when available, then inspect readability at intended presentation size, overlaps, labels, connector paths, clipped shapes, fonts, and icon styling. Programmatic counts alone do not prove rendering or editability.

Apply [Architecture QA](../architecture-qa/SKILL.md). Deliver the `.pptx`, optional preview/PDF, source toolkit hash, assumptions, icon gaps, and actual checks. State when PowerPoint opening, rendering, or editability verification was unavailable; do not report an unperformed check as passed.
