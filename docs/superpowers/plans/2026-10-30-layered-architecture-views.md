# Layered Architecture Views Implementation Plan

> For implementation: use `superpowers:executing-plans` task by task in the existing Git tree. Execution authorized by the user on 2026-10-30. Checkboxes record implementation progress; installation, push and publication remain excluded. See [verification](../../verification-layered-views.md) for acceptance gates.

**Goal:** Make OCI diagrams easier to understand, maintain, edit and review with optional layers, explicit exported views and verified corporate fonts.

**Architecture:** Keep the existing four skills and shared semantic model. Add one selectively loaded reference, an optional Draw.io view sidecar and focused structural checks; selected PowerPoint views remain separate native editable slides.

**Tech stack:** Python 3.11+ standard library, Markdown, Draw.io XML and existing OOXML tooling. No new dependency.

**Spec:** [Design and acceptance contract](../specs/2026-10-30-layered-architecture-views-design.md). Read both documents before implementation.

## Global constraints

- Same existing Git tree; preserve unrelated changes and commit each completed task using explicit file paths. No worktree, blanket staging, reset or forced history rewrite.
- Keep source toolkits, font binaries, ordinary installations and caches unchanged. Test copies and evidence belong outside the distributed plugin.
- Preserve Redwood style, OCI notation, native groups/containers, VCN/subnet membership, attached connectors and separate architecture evidence.
- Public and internal distributions retain their current asset/provenance boundaries. Never synchronize the internal package wholesale into the public repository.
- Existing baseline versions are evidence, not a choice of new release number. No broad 48/96-run benchmark or repeated PowerPoint movement exercise.

## Review focus

| Failure condition | Required behavior and owner |
| --- | --- |
| Legacy compressed/wrapped files and unnamed default layer | Preserve existing structural results; Tasks 2–3. |
| Hidden ancestor or collapsed container hides a required node/flow | Reject the declared view; do not claim renderer equivalence; Task 3. |
| Renamed page/layer or stale/incomplete view sidecar | Fail clearly when a sidecar is supplied; Task 3. |
| Scoped edit changes a protected subtree or splits an icon/container | Detect preservation failure independently of locking; Task 4. |
| Correct typeface name but inherited/substituted font in the application/export | Require application/export evidence before typography PASS; Tasks 2 and 4. |

## Task 1 — Reconcile the public source baseline

**Files:** Public `skills/**`, `scripts/check.py`, baseline `tests/**` and `docs/**`, both manifests and merged `README.md`. Preserve this checkout's `.github/workflows/ci.yml` and `tests/test_ci.py`.

**Interface:** Start from the inspected project checkout `a2bb39c` (public 0.1.1, one local commit ahead of its recorded remote). Read the clean public 0.2.1 export at `2798e29` as the source snapshot. Exact local roles/paths and inspection evidence are recorded in the separate local planning appendix.

- [x] Recheck applicable instructions, Git status and source identities. Inspect any new work before editing. Inventory an explicit tracked-file allowlist from `2798e29`; import its public runtime, tests and documentation using file-level changes, excluding its older `.github/workflows/check.yml`. Retain existing CI hardening and merge README verification instructions.
- [x] Retain the imported manifests' established 0.2.1 baseline identity without claiming a new release. Keep internal 0.2.4 manifests, artwork and catalog private and untouched during alignment.
- [x] Run `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check.py` and `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`. Run the public package scan against all staged/untracked source paths, inspect the diff and commit only this reconciliation. Expected: all tests pass, links resolve, manifests match, no private material or second CI workflow appears.

## Task 2 — Teach proportional views, safe editing and corporate typography

**Modify:** The four `skills/*/SKILL.md` files; Core's `references/style.md` and `references/delivery-evidence.md`; public `README.md`.

**Create:** `skills/oci-architecture-core/references/layered-views.md` (target at most 180 lines). Keep each skill entrypoint's addition to a short routing paragraph; do not preload the reference or whole catalogs for simple edits.

**Interface:** The new reference owns the view contract below. Core owns purpose/model/status; Draw.io owns safe ancestry and saved states; PowerPoint owns view-to-slide mapping; QA owns independent evidence. Existing entrypoint names and implicit-invocation metadata stay stable.

- [x] Implement the spec's decisions, including combined containment layers when independent Workloads layering would detach children. Explain explicit current/proposed labels, protected content, deliberate omission of detail, saved-view restoration and hidden content remaining in native deliverables.
- [x] Update typography: Oracle Sans native diagram text with real faces; verified template Georgia only in appropriate presentation title areas. Resolve inherited styles and HTML span overrides in Draw.io and theme/master/layout/run formatting in PPTX. Preserve artwork bytes and source files. Recheck native text after any targeted font normalization; permit no silent fallback.
- [x] Document source identity, font availability versus actual resolution, export inspection and missing-font outcomes. Existing diagrams keep unrelated styling; if that conflicts with a new whole-artifact typography requirement, report the limited scope rather than silently restyling unrelated pages.
- [x] Run public package/link checks and review the instructions against the simple, containment-heavy and current/proposed scenarios. Expected: each has one clear workflow, no mandatory layer retrofit and no claim of unmeasured benefit. Commit the guidance changes.

### Optional sidecar contract

Use a task-relative JSON file such as `architecture.views.json`; no separate schema dependency. Version 1 has `schema_version: 1` and `pages: [...]`. Each page entry contains:

| Field | Exact contract |
| --- | --- |
| `page_name` | Exact unique Draw.io page name; bare mxGraphModel uses the existing `Page-1` convention. Only declared pages are checked. |
| `layers` | Ordered complete list of `{id, name, locked}` for that page, back to front. IDs/names unique and nonempty for a managed page; `locked` is Boolean. |
| `saved_view_id` | Exactly one of that page's view IDs; this is the persisted deliverable state. |
| `views` | Nonempty list; IDs unique across the sidecar. Each entry has `id`, `purpose`, `status`, `visible_layer_ids`, `hidden_layer_ids`, `required_cell_ids` and `omissions`. |
| visibility lists | Disjoint, duplicate-free, exact partition of the page's actual layer IDs. No implicit remainder. |
| `required_cell_ids` | Nonempty unique cell IDs covering the view label/status, required boundaries, nodes and critical flow edges; compare the selection with the semantic model in QA. |
| `omissions` | List of `{model_id, reason}` for deliberately excluded semantic detail; empty when none. Reviewed by a person, not inferred by the validator. |

Preserve original names/IDs in unmanaged legacy files; using the sidecar opts only its listed pages into this stricter contract. Views are a delivery convention, not a promise of a built-in Draw.io preset feature. A single-layer drawing needs no sidecar unless multiple explicit exports are requested.

## Task 3 — Add minimal layer-aware validation

**Modify:** `skills/oci-drawio-designer/validate_drawio.py`.

**Create:** `tests/test_layer_views.py`; synthetic XML/JSON stays inline or in text fixtures, with no distributed artwork.

**Interfaces:** Preserve `check(path)`; extend to `check(path: Path, views_path: Path | None = None) -> dict`. Add CLI `--views PATH`. Reuse `catalog.models` and `catalog.cells_for`; do not change catalog indexing or PowerPoint's structural validator. Add `inspect_layers(cells: list[dict]) -> list[dict]` and `check_views(pages: list[tuple], manifest: dict) -> dict` locally in the Draw.io validator.

- [x] Write failing regressions for the matrix below; run `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_layer_views.py -v` and observe the intended failures.
- [x] Inventory root-child layers in document order and resolve cell ancestry. Read persisted `visible="0"` and `locked=1` style tokens, with visible/unlocked defaults; do not confuse style keys with XML visibility. For declared views, validate contract types/IDs/names/order/locks and the saved-view visibility. Evaluate every declared view without mutating the file.
- [x] A required cell must exist and be visible through its ancestors in that view; a collapsed ancestor cannot satisfy a required descendant. Every effective visible attached edge must have visible terminal ancestry. Accept attached cross-layer edges. Do not attempt pixel occlusion, custom-link execution or architecture inference.
- [x] Add JSON `layer_inventory` and `layer_view_integrity` (`PASS`, `FAIL`, `NOT_VERIFIED`) plus `layer_view_errors`. No sidecar means NOT_VERIFIED for declared-view checking. Keep `graph_integrity`, `file_integrity` and their existing errors scoped to their existing checks. Exit 1 for graph failure or supplied-sidecar failure; otherwise 0. Preserve all independent unverified review fields. Malformed/missing sidecars produce JSON failure, not a traceback.
- [x] Run the focused matrix and `scripts/check.py`; inspect CLI JSON/exit codes and commit the validator/tests.

| Regression group | Assertions |
| --- | --- |
| Legacy compatibility | Default layer, compressed pages, plain/UserObject/object cells retain original structural outcomes; no-sidecar view status is NOT_VERIFIED. |
| Valid layers | Nested VCN/subnet/icon ancestry and a cross-layer connector pass; inventory order and default lock/visibility values are correct. |
| Contract failures | Wrong schema/type, duplicate page/view/layer names or IDs, missing page, stale required ID, non-partitioned/unknown layer states, saved-state/lock/order mismatch fail with precise diagnostics. |
| Visibility failures | Required cell under hidden/collapsed ancestor, hidden critical edge, or visible edge with hidden terminal fails. Hiding only optional annotations passes. |
| Scope and honesty | Undeclared pages keep legacy behavior; validation changes no bytes; structural success leaves opening, exports, typography, visual quality and editability unverified. |

## Task 4 — Prove a bounded representative workflow

**Modify:** `tests/integration_official.py` with an opt-in `--layered-views` scenario; retain its default fixture and CLI. Accept optional `--drawio-source PATH` and `--pptx-source PATH`; otherwise retain the existing `--toolkits` directory convention. Require both resolved sources before generation. Add meaningful scenario tests to `tests/test_layer_views.py` using synthetic groups; no screenshots or exact prose assertions in unit tests.

**Interface:** Extend fixture `drawio(source, output, model, layered_views=False)` and `pptx(source, output, model, layered_views=False)` without changing their existing `(assets, edited_path)` return. The opt-in scenario writes sidecars, separate native selected-view slides and v1 evidence. Existing source hash/asset lookup rules still apply.

- [x] Add a fixed three-tier example: one complete regional VCN/subnet/workload subtree on Infrastructure, cross-layer attached Flows, optional Annotations and an always-visible proposed/synthetic status label. Use named overview/detail views; neither may hide the fixture's required HTTPS/SQL paths. Add a small labeled current/proposed variant to synthetic validator tests; no customer architecture or live availability claim.
- [x] Test that a scoped annotation edit preserves the protected subtree, parent/terminal mappings and unrelated page/slide using normalized XML comparison and artwork payload hashes. A deliberately changed protected parent or missing descendant must fail preservation. Assert Oracle Sans declarations on generated native text, no overriding fallback spans/runs, preserved icon payloads and the view-to-slide cell/model mapping. These assertions establish declarations, not actual font rendering.
- [x] Keep delivery evidence `schema_version: 1` and existing fields. Add optional `presentation` containing `views_file`, `views_sha256`, `exports` (`view_id`, `file`, `sha256`, `format`), and `slide_views` (`view_id`, `slide_number`). Add `checks` dimensions `layer_view_integrity`, `scoped_edit_preservation`, `view_exports` and `typography`. Record font family/face, application/version, export options and findings in referenced task-relative evidence. Never elevate UI checks from fixture output.
- [x] Run focused tests and both relevant offline package checkers. Generate this one official-source fixture outside the plugin, then run both format validators. Commit the fixture/evidence-contract changes after their automated tests pass.
- [ ] Perform one bounded computer-use session on test copies in available Draw.io and PowerPoint: inspect both views, attempt an edit with Infrastructure locked, toggle only optional annotations, export both declared views, restore the saved view, save and reopen. Inspect every changed page/slide and exported PNG/PDF for required routes, labels, clipping and actual Oracle Sans. Keep each exported view's state/options/hash. If PDF is produced, inspect its font information as supporting evidence.
- [ ] On a test copy only, explicitly unlock the required layer, move one native node once, save/reopen and confirm its connector follows; repeat one node movement on one native PowerPoint slide. Confirm other view/slide content and semantic containment survive. Allow at most one corrective retry per application after a concrete failure; otherwise record FAIL/NOT_VERIFIED and stop. Target 30 minutes for computer use, no new application/font installs. Missing tools or unresolved fonts leave applicable acceptance gates open, rather than triggering substitute proofs.

## Task 5 — Propagate deliberately and prepare the later release gate

**Modify later:** The matching allowlisted skill/reference/validator/test files in the existing internal and shared source directories; their variant-specific README paragraphs only. No ordinary installation/cache edits.

**Interface:** Public Git is authoritative for common code and presentation rules. Internal/shared entrypoints retain their bundle-first and supplemental-library sections; apply the shared guidance as reviewed sections, not whole-file replacement. Do not replace their catalogs, manifests, asset notices or toolkits with the public variants.

- [x] Apply common validator/tests/reference changes to both internal/shared sources and compare common file hashes. Merge the short skill/style/evidence additions around variant-specific content. Keep shared listing metadata distinct. Run `scripts/check_internal.py` in the private source; run its `package_errors(shared_root)` and the shared source's offline unit suites for the shared variant, because it currently lacks its own internal checker.
- [x] Run the public package scan, current CI tests and new focused regressions; verify the distribution diff explicitly. Keep internal evidence and generated binaries outside public Git. Record exact public Git revision and per-file internal/shared hashes in local release evidence; those directories are not Git repositories, so do not claim they contain commits.
- [x] Prepare a concise acceptance ledger with PASS/FAIL/NOT_VERIFIED for structural, preservation, application, per-view export, typography, editability and cross-format checks. Block a verified-release claim on unresolved required gates. Quality and token benefits stay unmeasured; do not restart the benchmark.
- [x] Commit only reviewed public changes with explicit paths. After acceptance, separately choose a release number, synchronize both manifests for each distribution, prepare internal/public packages and obtain any required install/push/publish authorization. Those release actions are outside this plan's execution scope.

## Completion and residual limits

Implementation is accepted only when Tasks 1–5 meet the spec's acceptance checks with traceable evidence; unavailable UI/font checks remain unfinished gates. Static layer checks do not prove visual occlusion, font resolution, semantic completeness, correctness of customer infrastructure or secure redaction. Shared/internal sources still need controlled per-file propagation until a separate source-governance change is approved.
