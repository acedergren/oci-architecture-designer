# Delivery evidence v1

Keep evidence beside the deliverable, not inside the distributed plugin. All paths are task-relative. Do not store secrets or customer inputs in release evidence.

Use this JSON shape for each artifact:

```json
{
  "schema_version": 1,
  "file": "example.drawio",
  "model_id": "synthetic-three-tier-v1",
  "source_toolkits": [{"format": "drawio", "sha256": "actual source file hash"}],
  "assets": [{"node_id": "compute", "label": "Virtual Machine", "source_sha256": "actual hash", "locator": {"page": "Icons", "cell_id": "original source id"}}],
  "checks": [{"dimension": "file_integrity", "method": "validate_drawio.py", "status": "PASS", "evidence": "validator.json"}],
  "assumptions": [],
  "icon_gaps": []
}
```

For PPTX, locators contain slide_number, part and shape_id. Hash the actual source file before using pinned IDs. Document exact-service gaps with searched labels and toolkit identity. Unknown metadata is not proof that no exact source icon exists.

Statuses: PASS requires executed, inspected evidence; FAIL records a failed acceptance check; NOT_VERIFIED records missing or incomplete checks with reason; NOT_APPLICABLE records an irrelevant dimension with reason. Use the dimensions in Architecture QA. A structural validator emits NOT_VERIFIED for visual, architecture, opening and editability reviews; update only after the separate check occurred and preserve its raw report.

Keep original and edited test files separate. Record application/renderer versions, changed page/slide, node movement, save/reopen outcome and connector behavior. Missing rendering tools must not be reported as NOT_APPLICABLE. Record external links separately without fetching them.

Benchmark records include revision, identical scenario/environment, elapsed seconds, tool failures, manual corrections and observed token usage from a named usage log. With no usage log, token usage is null with NOT_VERIFIED, never an estimate labeled measured. Static token estimates and observed byte counts belong in separate fields.

For a new design or material architecture change, accompany artifact evidence with the [workload brief and decision records](architecture-design.md) and [architecture review](architecture-review.md). Link material node/flow decisions to requirement IDs and specific source sections/access dates. Keep documented capability, customer configuration, design inference and executed validation distinct. Existing schema_version 1 artifact fields remain unchanged; a layout-only task does not require a new brief.

## Optional image evidence (backward compatible)

For [image deliveries](image-delivery.md), keep the existing v1 fields and add `sha256` for the delivered image and an optional `image_delivery` object. Existing native records do not need this object. All referenced evidence files remain beside the deliverable, outside the plugin. This illustrative shape contains unknown values, not a successful execution:

```json
{
  "image_delivery": {
    "route": "generated_illustration",
    "source": null,
    "tool": "observed host tool name",
    "tool_version": null,
    "requested_model": null,
    "observed_model": null,
    "model_identity_status": "NOT_VERIFIED",
    "prompt": {"file": "prompt.txt", "sha256": "actual prompt file hash"},
    "references": [],
    "dimensions": {"width": null, "height": null},
    "elapsed_seconds": null,
    "usage": null,
    "usage_status": "NOT_VERIFIED"
  }
}
```

`route` is `technical_export` or `generated_illustration`. For technical export, `source` records task-relative `file`, `sha256` and the exported `page_or_slide`; `prompt` is null unless a prompt actually contributed. For image generation, retain the submitted prompt; keep any tool-reported revised prompt separately when available. Each reference records `file`, `sha256` and role (`edit_target`, `style_reference` or `factual_reference`). Record observed dimensions from the saved image, not requested dimensions. Hash the final delivered bytes; keep prior/edit versions separate.

`requested_model` is populated only when an interface actually accepted a model selection. A prompt mentioning a model is not a selection or observation. `observed_model` requires a named tool/runtime response; otherwise null and NOT_VERIFIED. Use the same rule for tool versions/settings and record the exact evidence for any verified value. Do not infer the image model from the active text model.

Measure elapsed time around the actual operation. Preserve raw usage fields with their documented units and originating log; absent usage is null/NOT_VERIFIED. Report text-model and image-tool usage separately unless documented fields support a non-duplicated total. Do not apply a GPT Image 2 calculator to GPT Image 2.5 or infer cached-image token counts from missing fields. The [OpenAI image guide](https://developers.openai.com/api/docs/guides/image-generation#cost-and-latency) notes that some cached image inputs are billed without exposed cache counts. Manual corrections count only actual human changes; program checks, visual review and agent correction attempts are separate.

Use all existing QA dimensions with method and evidence. Image file integrity/opening, semantic comparison and visual quality are separate checks. Native source validation does not approve the export's text or arrow placement. Mark native editability NOT_APPLICABLE only for image-only requests without that requirement; missing required native proof is NOT_VERIFIED, or FAIL when the provided artifact cannot meet it.
