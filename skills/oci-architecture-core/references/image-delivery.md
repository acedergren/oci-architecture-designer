# Architecture images: export and illustration

Use [Core](../SKILL.md) for architecture and [OpenAI model profiles](openai-model-profiles.md) only for the relevant model/tool guidance. Apply the [Oracle Redwood/OCI style contract](oracle-redwood-style.md) before either image route. An image is a presentation of the selected architecture, not a source of new service decisions. A small image task needs a compact model and checks, not a new design workshop.

## Route from the request

| User intent | Route and deliverable |
| --- | --- |
| Technical OCI diagram, PNG, “arkitekturbild” or “ritning som bild” without an illustration request | Export a checked native Draw.io/PowerPoint source; PNG by default |
| Exact official icons or editable nodes/connectors | Native source and technical export; include the editable file when requested |
| Explicit generated illustration, concept image or visual alternatives | Existing host image-generation tool; preserve the fixed architecture |
| SVG requested | Native export only when the existing tool supports it; do not rename a bitmap or wrap it as claimed vector artwork |
| Conflicting generated-illustration and exact/editable requirements | Explain the incompatibility, offer technical export for the hard requirements, and resolve the route before generating |

Use the requested route. If its renderer/image tool is missing, keep an available model/native draft and identify the blocked deliverable and checks. Do not silently switch routes or report missing tooling as an icon gap. Install nothing. A picture alone fails an explicit editable-file requirement. For an image-only request, deliver the image; retain a technical export's native source with the task evidence without requiring it as an extra customer deliverable.

## Fixed model and reference inputs

Before rendering, record stable resource IDs, exact display labels, service meanings, region/realm (or explicitly unspecified), regional VCN/subnet membership, directed flows with purpose/protocol/port, and relevant decisions/status. Preserve these across image and native views. Separate data, administration and replication paths. Do not add services for visual richness or imply unverified endpoint/region support.

For every input image identify its role: **edit target**, **style reference**, or **factual reference**. Inspect the actual target before editing. A screenshot with unclear labels or arrows is incomplete evidence: ask only for ambiguities that affect the architecture, otherwise label the uncertain parts. Do not infer hidden services or network routes from appearance. Use verified toolkit originals for official artwork; generated lookalikes do not establish identity.

## Technical export

1. Reuse or create a native source with [Draw.io](../../oci-drawio-designer/SKILL.md) or [PowerPoint](../../oci-powerpoint-designer/SKILL.md). Preserve unrelated pages/slides and style. Verify toolkit hashes and asset locators; run the existing format validator before export.
2. Use an already available application/renderer's real export controls. Save a separate PNG, or an explicitly requested supported SVG. Preserve the native graph rather than flattening its source into an image. Record source hash, page/slide and tool/version. File conversion is not proof of opening in the native application.
3. Inspect the exported file at intended display size, plus useful detail crops. Check text, counts, containment, complete arrows, contrast, clipping and margins. Split a dense view into labeled detail views instead of silently dropping content. Compare export to source/model; a native parser pass cannot approve a wrong or unreadable image.
4. Native move/save/reopen proof remains required when native editability is claimed or requested. A PNG/SVG export does not inherit interactive connector behavior.

## Explicit image generation and editing

Use the host's built-in image tool and its actual schema. Select reference/edit inputs through supported arguments; inspect local edit targets first. Do not synthesize unsupported model, quality or size fields or silently invoke an API/CLI requiring a key. Save the returned image in the task's output folder and open that actual file for inspection. A successful tool call is not visual acceptance.

Adapt this prompt template without inventing new requirements:

```text
Purpose and audience: <intended use and viewing size>
Action: <new illustration or exact change to the supplied edit target>
Input images: <each image number/name and its role>
Architecture status: <proposed/current; assumptions and exclusions>
Resources: <stable ID, exact service and verbatim display label; exact counts>
Boundaries: <region, regional VCN/subnets and exact membership>
Directed flows: <ID, source -> target, purpose and verbatim protocol/port label>
Composition: <Oracle Redwood/OCI source sample, hash and locator; requested layout>
Style: <source palette, Oracle Sans or allowed sans-serif fallback, source grouping,
        thin Bark connectors with open arrowheads; no generic cloud/3D/shadow style>
Text verbatim: <complete required text list>
Change only: <requested delta for an edit>
Preserve: <unaffected resources, labels, flows, boundaries and style>
Avoid: invented components, extra arrows, changed direction, implied HA/DR,
       claimed official artwork, illegible/truncated text, style drift from references
Output: <requested raster image; transparent background only if requested>
```

For an edit pass the current image as the target; retain the prior version separately. Make one targeted correction at a time and reinspect the whole result. Record actual corrections/failures and usage when exposed. If exact labels or flows still fail inspection, deliver a labeled draft with the failed checks and offer the technical route; never quietly lower acceptance or claim that a different backend was used.

## QA and evidence

Apply all twelve dimensions in [Architecture QA](../../architecture-qa/SKILL.md). For image-only delivery, native graph/connector editability is NOT_APPLICABLE with reason, unless explicitly required, in which case an image-only result fails requirement fit/editability. File integrity uses actual image decoding and observed dimensions; the native format validator applies separately to an export source. Application opening records the saved image opened in a named viewer; it does not mean Draw.io/PowerPoint was opened.

Compare every resource, exact label, count, boundary membership and directed flow against the fixed model, then inspect readability/overlap/cropping at delivery size. For illustration-only symbols, official-artwork identity is NOT_APPLICABLE only when official artwork is not required; generated lookalikes never pass official icon coverage. Cross-format consistency applies when more than one representation is delivered. Parser/model checks do not prove visual correctness or deployed behavior. Missing tools or missing inspection remain NOT_VERIFIED.

Visual quality also requires comparing typography, palette, icon treatment, groupings and connector style with the recorded Oracle references. Correct architecture with a generic teal/server infographic style still fails an Oracle/OCI style requirement. Disclose font substitution and other departures; a palette match alone cannot pass the style review.

Use [delivery evidence](delivery-evidence.md) beside actual files. Include route, native/source file and hash where relevant, image hash/dimensions, tool, observed model or null, retained prompt, reference roles/hashes, executed checks and measured usage/time or explicit unknowns. Keep raw tool output when available. A request or prompt naming Sunburst/Flare is not backend evidence; record only returned identity. Cache/image-token counts and price must not be inferred from absent usage fields.
