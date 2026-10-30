# OCI Architecture Designer 0.2.5

Adds optional layered views for clearer editing and review while preserving the existing four skills, stable architecture model and editable native deliverables.

- Named views explicitly declare layer visibility, saved states, required nodes/flows and deliberate omissions. Simple drawings can keep one layer.
- Draw.io validation supports optional `--views PATH`, attached cross-layer connectors and effective visibility through hidden/collapsed ancestors. Layer results remain separate from graph results.
- Native VCN/subnet/container ancestry and original icon groups stay intact. Scoped-preservation checks protect unrelated content, including protected groups and connector mappings on an edited PowerPoint slide.
- Selected views use separate editable PowerPoint slides. Native diagram text requires Oracle Sans and actual application/export font verification; no silent fallback.
- An opt-in fixed representative fixture and focused regression tests cover the new contract. Source directories and ordinary installed plugins are separate; this release does not imply local installation.
- The latest upstream README style and documentation webhook are preserved. CI runs the full offline suite and includes referenced documentation/tests in its source archive.

## Verification and limitations

Public: 36 tests PASS. Internal: 41 tests PASS. Shared: 31 tests PASS. Both official-source representative formats pass structural checks. The independent review's PowerPoint preservation finding was fixed and regression-tested.

[Plugin Eval](plugin-eval-0.2.5.md) is complete: runtime bundle score **35/100 (F)** for both 0.2.5 and the previous internal 0.2.4. This is not called a pass; missing project policy URLs and static deferred-budget findings remain disclosed. The strongest individually scored skill is QA (100/A), the weakest Core (77/C).

Native application round trips, exported-view inspection, connector movement and actual typography remain NOT_VERIFIED. The local platform font lookup resolves Oracle Sans to Helvetica. These limitations prevent a fully verified artifact-quality claim; the source/helper release does not claim they were resolved. See [implementation evidence](verification-layered-views.md).

The public distribution excludes Oracle artwork, fonts and private metadata. The Oracle-internal distribution retains its pinned original toolkits, supplemental-library restrictions, notices, existing plugin identity and audience. No new license, Oracle endorsement, deployment proof or measured quality/token-saving claim is made.
