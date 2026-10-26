# Architecture image acceptance exercises

Use [image-requests.json](fixtures/image-requests.json) with the current Core/QA and relevant format instructions. The existing [synthetic architecture](fixtures/architecture.json) is the common model. Run these separately from the pinned architecture benchmark: do not change its tasks, profiles, runtime exports or results. No new model/API/renderer installation is required.

These are behavior and visual exercises, not tests asserting Markdown wording. Save prompts, tool output, source hashes, generated files, QA and usage outside the plugin/Git. Official artwork remains in external verified toolkits. Use a new conversation/workspace for natural-discovery tests; the natural prompts must not name skills. Full skill reads/tool use must be observed, not self-reported. Explicitly instructed/manual exercises can prove artifact behavior but cannot prove natural activation or an independent model-profile comparison.

## Procedure and acceptance

1. Give both image routes the same exact labels, regional VCN/subnets and two directed flows from the model. Request a technical export in Swedish and a generated illustration in English. Provide an inspected Oracle/OCI style reference and its source hash/locator. Record each route's actual tool/backend evidence and inspect the saved files.
2. Apply each route's follow-up in the same conversation: add `compute-2` / `Application VM 2` in the application subnet with load-balancer HTTPS/TCP 443 and database SQL/TCP 1521 flows. Keep the existing resources, original flows, style and unrelated pages/slides. Compare all four directed flows and the three original nodes after editing. Keep initial files and reference views separately.
3. Run existing native validators for export sources; decode/open images, record dimensions, inspect at delivery size and compare them with the model. Check every service, count, exact label, subnet membership and direction. Distinguish a converter, image viewer and native editor. When editability is required, perform native move/save/reopen separately.
4. Exercise the negative cases below. A missing check is NOT_VERIFIED; N/A requires a reason and cannot hide a violated requirement.

| Case | Acceptance |
| --- | --- |
| Technical PNG and generated illustration | Same resources/flow semantics; export uses verified originals, generated symbols disclosed as illustrations; actual files opened and visually inspected |
| Add a second Compute | Four resources and four directed flows; no unintended architecture/style/reference changes; export regenerated from edited native source |
| Exact official-icon gap | Run metadata lookup and search actual verified source; disclose exact gap/hash without a made-up Oracle symbol; missing toolkit is distinct |
| Unsupported/current service assertion | Specific primary source/section/date/scope, or bounded uncertainty; attractive artwork must not turn an unsupported endpoint/region claim into PASS |
| Exporter or image tool unavailable | Use a controlled environment exposing no route tool; retain useful model/native draft, leave missing delivery and visual checks open, no silent route/API substitution |
| Image backend hidden | Observed image model null/NOT_VERIFIED; do not infer it from the text model, prompt, installed guide or family name |
| Image-only vs editable requirement | Native editability N/A for image-only; bitmap alone fails an explicit editable requirement; no connector claim from image pixels |
| Unsupported SVG/tool parameters | Native SVG only through a supported exporter; pass no model/quality/size argument absent from the actual tool schema |
| Scoped image edit | Inspect input target first, distinguish reference roles, retain prior file and reinspect all preserved content |
| Oracle/Redwood style fidelity | Compare actual typography, palette, original icon treatment, grouping and connectors to recorded source samples; a generic teal/3D/server infographic fails even with correct topology; detect silent serif substitution and color drift after a color-only edit |

Report evidence per case with PASS/FAIL/NOT_VERIFIED and separate file, semantic, visual, model-identity, activation and usage outcomes. Record which model profiles were actually exercised. A single host execution does not establish every documented model profile or general model quality. If cache/image usage is hidden, leave it null; do not turn unknown values into zero or estimates into measurements.
