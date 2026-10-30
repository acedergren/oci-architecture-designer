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

## Optional presentation evidence (v1 compatible)

Keep existing artifact fields and `schema_version: 1`. An optional `presentation` object contains `views_file` (task-relative), `views_sha256`, `exports` (list of `{view_id, file, sha256, format}`) and `slide_views` (list of `{view_id, slide_number}`). These record actual outputs, never planned exports. The [view sidecar contract](layered-views.md) declares purpose/status, required cells and omissions.

Use independent `checks` dimensions `layer_view_integrity`, `scoped_edit_preservation`, `view_exports` and `typography`. Evidence records application/version, changed page/slide, selected visibility, export options, font family/face and actual resolution/substitution findings. A font declaration/file inventory is not a rendering check. Keep normalized protected-subtree comparisons and original asset payload hashes. Record missing checks as NOT_VERIFIED; lock state does not prove preservation, and declared view validity does not prove architectural completeness. Restore the saved view after export and keep original versus movement-test copies separate.
