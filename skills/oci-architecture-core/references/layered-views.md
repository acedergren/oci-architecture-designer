# Optional layers and declared views

Load for independently hidden/locked detail or multiple exported views. Simple drawings may keep their default layer; do not retrofit layers without a concrete editing or audience need. Keep abstraction levels (context versus OCI deployment) on separate named pages. Layers organize presentation, not OCI semantics or correctness.

## Preserve the native graph

Prefer Infrastructure, Workloads, Flows and Annotations only where useful. Each object belongs to one layer through its ancestry; a container/group and all descendants must stay together. If workloads are native children of a VCN/subnet, keep their complete subtree on the same layer. Do not detach children or split original icon groups to achieve independent visibility. Cross-layer attached connectors are supported. Preserve geographic/network/compartment distinctions and original artwork payloads.

Before editing, inventory IDs, parents, geometry, payload hashes and visibility/lock states. Lock stable infrastructure when its descendants need no edits. If the same layer contains editable workloads, explicitly unlock the necessary unit within scope; locks are editing aids, not access controls or preservation proof. Compare normalized protected subtrees and unrelated pages/slides before and after scoped edits.

Prefer separate labeled pages for substantial current/proposed changes. A small same-page alternative can use complete duplicated subtrees with unique graph IDs and stable semantic mappings. Switch each alternative's associated flows and status labels together. Never save/export an unlabeled mixture of alternatives.

## Declare intent, then export

Use ordinary Layers controls. Custom-link toggles/animations are not required; they can create additional transient visibility/style states. Define each view's purpose, current/proposed status, required boundaries/nodes/critical flows and deliberate omissions. The view label/status must remain visible. Verify every layer state immediately before export, inspect the result, then restore the declared saved view and save/reopen. Hidden content stays in the native file and is not secure redaction.

An optional task-relative `architecture.views.json` declares managed pages. This is a delivery convention, not a built-in Draw.io preset system:

```json
{
  "schema_version": 1,
  "pages": [{
    "page_name": "Deployment",
    "layers": [
      {"id": "infra", "name": "Infrastructure", "locked": true},
      {"id": "flows", "name": "Flows", "locked": false},
      {"id": "notes", "name": "Annotations", "locked": false}
    ],
    "saved_view_id": "overview",
    "views": [{
      "id": "overview", "purpose": "Deployment overview", "status": "proposed",
      "visible_layer_ids": ["infra", "flows"], "hidden_layer_ids": ["notes"],
      "required_cell_ids": ["status", "vcn", "app", "db", "sql"],
      "omissions": [{"model_id": "optional-note", "reason": "Operational note belongs to detail view"}]
    }]
  }]
}
```

Contract v1:

- `schema_version` is integer 1; `pages` is nonempty. Each declared `page_name` resolves uniquely; bare mxGraphModel uses `Page-1`. Unlisted pages retain legacy checks.
- `layers` is the complete ordered inventory, back to front, of `{id, name, locked}`. IDs/names are unique nonempty strings and `locked` is Boolean. Existing unnamed legacy layers need no renaming unless that page opts into this contract.
- `views` is nonempty with IDs unique across the sidecar. `id`, `purpose` and `status` are nonempty strings. Visibility lists are duplicate-free disjoint exact partitions of actual layer IDs. `saved_view_id` selects that page's persisted visibility; declared locks apply to the saved artifact.
- `required_cell_ids` is nonempty and duplicate-free. Include labels/status, boundaries, nodes and critical edges from the semantic model. `omissions` is a list of `{model_id, reason}` nonempty strings, or empty. QA must justify omitted dependencies; a validator cannot infer completeness from authored declarations.

Run from the plugin root:

```sh
python3 skills/oci-drawio-designer/validate_drawio.py result.drawio --views architecture.views.json
```

Without a sidecar the original CLI works and layer-view checking is NOT_VERIFIED. With one, the validator checks inventory, saved states, required effective visibility and visible attached-edge endpoints in every declared view. Hidden/collapsed ancestors cannot satisfy required descendants. It does not execute links or prove pixels, exports, topology or application behavior. A PASS is structural only.

For PowerPoint, create a separate native editable slide per selected view; map view IDs to slide numbers and compare the same semantic subset, status, services and flows. Keep native text/boundaries/connectors and disclosed original SVG/image limitations. Do not flatten the whole architecture or promise Draw.io layer interaction in PPTX.

## Typography and evidence

Apply [style](style.md): Oracle Sans for native diagram text, with real Regular/Semibold/Bold faces. Check Draw.io HTML spans and PPTX theme/master/layout/run inheritance as well as explicit names. Georgia is reserved for a verified presentation template's title treatment. No silent generic fallback. Preserve source toolkits and original image/SVG/logo lettering; only normalize native output text and inspect reflow. File presence is not proof an application resolved the font. Missing fonts block a corporate-typography PASS; do not install, embed or distribute font files as a workaround.

Keep [delivery evidence](delivery-evidence.md) beside the artifacts: sidecar hash, selected view, actual export options/file hash, application/version, preservation comparison, font family/face and font-resolution findings. Opening, exported-view inspection, typography, editability and architecture each need separate evidence. A bounded test copy checks hide/show, locking, export, save/reopen and one connector-following movement. Missing checks remain NOT_VERIFIED.

Sources: [Oracle's layered-diagram article](https://blogs.oracle.com/cloud-infrastructure/layered-architecture-diagrams-drawio) (2023-04-03), [Draw.io containment/layers](https://www.drawio.com/docs/manual/layers/how-layers-work/), [persisted graph model](https://github.com/jgraph/drawio/wiki/Graph-Model), [optional interactivity](https://www.drawio.com/docs/tutorials/interactive-diagram-layers/). Checked 2026-10-30. These techniques do not establish architectural correctness or measured quality/token savings.
