# Oracle Redwood and OCI visual fidelity

Checked on **2026-10-26**, including the user-supplied [Oracle Redwood site](https://redwood.oracle.com/). For a new OCI architecture image, use Oracle/OCI styling by default unless the user explicitly requests a different visual language. “Illustration” does not imply permission to invent a generic cloud style. Existing unrelated styling is preserved during scoped edits.

## Two sources with different responsibilities

- [Redwood Foundations](https://redwood.oracle.com/?landingPageId=foundations) covers visual hierarchy, layout, accessibility and communication through color. Its [Categorizing with color](https://redwood.oracle.com/?pageId=GUIDEG3&page=shell&shell=content-page&selectedSection=section1) guidance stresses restrained color and meaningful distinctions. Apply these principles to readability and presentation; do not interpret a UI illustration or categorical chart palette as a new OCI icon system.
- The **verified OCI Architecture Diagram Toolkit** is authoritative for architecture icons, labels, geographic/network boundaries and connectors. In the pinned `OCI_Icons.pptx`, slide 5 covers Redwood palette/typography, 18–19 grouping, 20–21 connectors and 23 icon preservation. Recheck positions and hash for a different source. Use [style](style.md) and the actual sample groups, not a recollection of the Oracle brand.

The Redwood site uses JavaScript. If a text fetch yields only an application shell, inspect the rendered official page or report it unread; do not claim that the shell verified detailed design rules. The pages above were read in a rendered browser. No artwork/font files or copied site manual are bundled.

## Style contract before generation/export

Record the selected source hash and source page/slide with the task evidence. Select only relevant example views, inspect them, and identify what must match:

| Element | Required treatment |
| --- | --- |
| Icons | Copy the complete official icon/group in an approved Ocean or Sienna variant; preserve shape, source label and aspect ratio. No 3D, gradients, shadows, rotation, generic server/cylinder substitutes or invented Oracle pictograms for an exact-artwork requirement. |
| Typography | Oracle Sans when legitimately available, otherwise the toolkit's Arial/Calibri/equivalent sans-serif fallback. Inspect actual rendering for silent serif substitution. Never package or install fonts for this task. |
| Palette | Use the source's Ocean `#2C5967`, Sienna `#AE562C`, Bark `#312D2A`, Air `#FCFBFA` and relevant neutral fills; Oracle Red `#C74634` only where the source/request calls for it. Keep source artwork colors, including small source encoding differences. |
| Boundaries | Copy the inspected location/network grouping conventions, preserving their distinct solid/dashed treatments and label hierarchy. Do not replace all boundaries with thick rounded teal cards. Geography and network membership remain different semantics. |
| Connections | Bark, approximately 1pt, open arrowheads for directed data flow, clear elbows/spacing and readable labels. Keep connector semantics from the source; avoid lines crossing service labels or disappearing into artwork. |
| Composition | Clear hierarchy, aligned resources, restrained fills and whitespace; prioritize exact labels and legible flow paths. Split density into views instead of decorative effects or dropped content. |

## Applying the contract to both image routes

**Technical export:** use native source groups and explicit text styles, inspect the saved image, and compare it against selected official samples. A correct RGB value alone is not style fidelity. Record any fallback font or intentional departure. Retain original source identity and separate architecture, visual and editability checks.

**Generated illustration:** provide inspected source renderings or icon references through the image tool's supported reference inputs, with roles explicitly marked. Add the style contract to the exact architecture prompt. Request flat official diagram language and preservation of reference glyphs/labels rather than a “modern cloud infographic”. Review every icon, text item, boundary and arrow. Generated pixels do not prove exact official artwork identity. If exact icons are mandatory, use technical export. If a generated result drifts, record visual FAIL, make a targeted correction and reinspect; never label an unreviewed approximation Oracle compliant.

When exact palette or typography is required, inspect actual output values/rendered fonts as well as appearance. A prompt containing HEX values or a color-only edit is not proof of faithful reproduction. Check non-antialiased stroke interiors or compare equivalent rendered samples; edge blends are not exact base colors. A generated image can preserve all architecture and still fail source-color fidelity. Retain that result as a draft with the specific failed check and offer the verified technical export. Do not keep regenerating indefinitely to imply a guarantee the tool does not provide.

For [QA](../../architecture-qa/SKILL.md), visual quality must include this source comparison. Record the actual reference, font/fallback, palette, grouping and connector findings in existing evidence; no new score may hide a style failure. “Source compared” is an executed check, not Oracle certification or legal/brand approval.
