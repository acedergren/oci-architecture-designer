# Layered views — implementation evidence

Date: 2026-10-30. Implementation is available locally; required application, export and typography acceptance gates remain open. No new release number, installation, push or publication is included.

## Changes

- Reconciled the reviewed public 0.2.1 runtime in the existing Git tree, retaining the existing CI hardening and smoke tests.
- Added optional layer/view guidance across the four skills, a selectively loaded reference, corporate font rules and backward-compatible v1 presentation evidence.
- Extended `validate_drawio.py` with optional `--views PATH`, layer inventories, effective visibility and saved-state checks. Legacy graph outcomes remain separate from view outcomes.
- Added synthetic regressions and an opt-in official-source fixture with overview/detail views, attached cross-layer flows and separate native editable PowerPoint slides. Protected native containment and unrelated content are checked independently of locks.
- Propagated only common code and reviewed instruction sections into the existing internal/shared sources. Their asset catalogs, toolkits, manifests, notices and listing artwork remain unchanged. Installed packages were not updated.

## Executed verification

| Check | Result | Scope |
| --- | --- | --- |
| Public `python3 -B scripts/check.py` | PASS — 36 tests | Includes existing CI smoke tests, synthetic helper regressions, links and public-package exclusion checks |
| Internal `python3 -B scripts/check_internal.py` | PASS — 41 tests | Includes bundle verification and internal-library regressions |
| Shared package inspection and offline suites | PASS — 31 tests, zero package errors | Shared variant retains its own metadata and internal asset boundary |
| Layer-view regressions | PASS | Includes compressed/wrapped cells, unnamed legacy layers, exact partitions, hidden/collapsed ancestry, cross-layer endpoints, saved visibility, malformed sidecars and current/proposed alternatives |
| Official-source representative generation | PASS | Both native formats pass their structural validators; Draw.io declarations pass layer/view validation |
| Scoped preservation | PASS — automated fixture | Annotation edits preserve normalized protected graph content, native group ancestry and unrelated page/slide content; negative tests detect reparenting/deletion |
| Typeface declarations | PASS — synthetic fixture assertions | Native output text declares Oracle Sans; this does not prove rendered typography |
| Platform Oracle Sans resolution | FAIL — prerequisite diagnostic | CoreText resolves the requested Oracle Sans family to Helvetica on this machine |
| Draw.io application, locking, export, save/reopen and connector movement | NOT_VERIFIED | No supported local Draw.io application/control surface was available for the planned interaction check |
| PowerPoint application round trip | NOT_VERIFIED | Bounded automation attempt and one corrective retry could not launch/control the native application (error -10827); raw evidence retained locally |
| Per-view export/visual inspection, actual font resolution and connector movement | NOT_VERIFIED | No claim that parser/fixture checks establish application behavior or corporate-font fidelity |

The counts overlap: layer/fixture cases are included in the package suites. Local raw command logs, source hashes, representative files and propagation evidence are retained outside the public package. No usage benchmark was run; quality and token benefits remain hypotheses.

## Independent review and decisions

One independent read-only reviewer found one Important issue and no Critical or Minor issues: the PowerPoint comparison excluded the entire detail slide. Fixed by comparing all package parts and normalized protected slide content while excluding only the specifically permitted annotation shape. A new regression was observed failing before the fix and passing afterward; it rejects deleted native groups, changed geometry and changed connector mappings on that same slide. All three distribution suites and the official-source fixture passed after the fix. No findings remain deferred.

| Review decision | Reason and cost if misapplied |
| --- | --- |
| Keep application/export/editability/typography acceptance open | Those behaviors need actual application evidence. Treating structure as proof would misstate artifact readiness. |
| Keep semantic completeness in model review | Authored required-cell lists cannot infer omitted dependencies. Skipping that review could deliver an incomplete architecture. |
| Limit font normalization helper to the fixed fixture | It is not a general inherited-font engine. Generalizing its declarations without checking actual outputs could leave font overrides unresolved. |

## Use and remaining acceptance

```sh
python3 skills/oci-drawio-designer/validate_drawio.py result.drawio --views architecture.views.json
python3 tests/integration_official.py --layered-views --toolkits /tmp/oci-task/toolkits --output /tmp/oci-task/representative
```

The fixture also accepts `--drawio-source PATH --pptx-source PATH` for verified source files. It checks both sources before generation. Outputs and their evidence remain outside the plugin. Default fixture behavior remains available without `--layered-views`.

Complete the bounded Draw.io/PowerPoint interaction check on a machine with working application control and properly available Oracle Sans fonts: inspect both views and every changed slide/export, test locked infrastructure, restore saved visibility, save/reopen and verify one node's attached connector follows movement in each format. Keep source fonts/toolkits and ordinary caches intact; do not silently fall back. Missing typography/application checks block a fully verified release claim.

After acceptance, choose a release version and separately authorize any installation, push or publication. Static checks cannot establish pixel occlusion, semantic completeness, customer reachability, deployment readiness or secure redaction of hidden content. Private source directories still require deliberate per-file propagation.
