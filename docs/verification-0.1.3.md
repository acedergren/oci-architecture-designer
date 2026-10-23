# Verification — 0.1.3 local candidate

Executed 2026-10-23. Synthetic internal-traffic scenario; no OCI changes, deployment, reachability or customer acceptance implied.

## Automated and official-input checks

- `python3 scripts/check.py`: 16 tests passed plus four-skill metadata, manifest, link and public-package checks.
- Five inherited 0.1.2 tests passed before changes. New tests cover exact metadata filtering/hash rejection, PowerPoint retrieval/cache tampering, cache location, compressed/wrapped graphs, malformed packages, slide ordering, duplicate IDs, broken connectors and markup-compatibility namespaces.
- Both official toolkits downloaded from Oracle with the pinned hashes verified; source URLs remain on [Oracle's toolkit page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm).
- The opt-in fixed fixture produced both formats with three official icon groups, the same VCN/subnets/services/flows, and separate source locators. Original and scoped-edited files pass format validators. The second reference page/slide is preserved byte-for-byte by the builder's scoped edit.
- Full toolkit examples are not a production topology reference: the unchanged PPTX source itself has an unrelated dangling connector on slide 21. Generated files retain only reachable dependencies for the selected template views.

## Actual application checks

| Check | Draw.io | PowerPoint |
| --- | --- | --- |
| Open generated file | PASS — Draw.io web editor | PASS — Microsoft PowerPoint for Mac, two slides, no repair prompt |
| Render/visual inspection | PASS — rendered architecture view inspected in editor | PASS — LibreOfficeDev 26.8 PDF export and native slide inspection |
| Node movement | Observed in editor; complete persisted round-trip remains NOT_VERIFIED | PASS — compute group moved with keyboard; both connector transforms changed and retained their child-shape references |
| Save and reopen movement test | NOT_VERIFIED — browser file/download event did not complete | PASS — saved native file reopened in PowerPoint and inspected; validator passed after native save |
| Scoped edit preservation | PASS — fixture reference page unchanged | PASS — fixture reference slide unchanged; native application saving may rewrite package metadata |

Raw structural reports deliberately retain NOT_VERIFIED for application/visual/editability reviews. The table records separately executed manual checks; it does not retroactively turn structural checks into those reviews. Official/generated binaries and UI test copies stay outside this repository.

## Failures found and corrected

- Copied XML lost a prefix used in markup-compatibility Requires. The new negative test failed before the validator correction and now passes. Fixture serialization retains those bindings.
- LibreOffice rejected prefixed OPC metadata roots even though the XML was namespace-equivalent. Keeping original default namespaces allowed direct PDF export.
- Connectors attached only to group IDs survived parsing but did not follow group movement. The fixture now references real child-shape connection sites, and PowerPoint movement/save/reopen was observed.
- Draw.io boundaries are swimlane containers so nested node selection does not select the entire regional grouping by default.

## Cost and timing evidence

[Machine-readable evaluation](evaluation-0.1.3.json) compares a fixed export of public commit 8c80a04 with the updated working source using Plugin Eval 0.1.2. Raw score: **13/100 → 35/100**. The earlier installed-cache score of 3/100 is a different target and is not the before value for this comparison.

Static trigger estimate: **309 → 247 tokens**. Sum of skill invocation estimates: **4,143 → 3,187 tokens** (about 23% lower). These are static estimates, not measured model usage or proof that every task loads all skills. Deferred-file estimate increased as tests/helpers/docs were added; files are not all read on an ordinary invocation. Selective lookup avoids full-catalog output.

Remaining evaluator deductions include absent project-specific privacy/terms URLs, deferred-file size and heuristic Python complexity/long-line warnings. A cache-directory/name warning applies to installed version directories, not this correctly named source root. The exact `Use when` trigger heuristic is now satisfied with meaningful descriptions; that does not establish host selection quality.

[Comparable helper benchmark](benchmark-0.1.3.json): three runs per revision of indexing the same official toolkit files and validating the same generated Draw.io graph, same Python/environment. All twelve tool invocations exited 0. Mean combined elapsed time: **6.521 s before / 6.573 s after**. This shows no supported speed improvement and is not an agent benchmark. Manual corrections are not applicable to those deterministic commands.

Actual model token consumption and model-driven task outcomes remain **NOT_VERIFIED**: no isolated before/after agent usage logs were available. Do not present byte counts, static estimates, this session's overall usage or deterministic helper timings as measured agent efficiency.

## Remaining release acceptance

- Complete Draw.io file save/reopen after node movement using a functioning download/native editor path.
- Run isolated representative agent tasks with per-run usage logs before making model-efficiency or first-pass-success claims.
- Installed-host automatic selection and CI execution on GitHub remain unverified; the local CI-equivalent command passes.
- This is a prepared local candidate, not an installed, pushed or published update.
