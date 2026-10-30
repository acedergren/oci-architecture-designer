# Plugin Eval — 0.2.5

Evaluated 2026-10-30 with the installed Plugin Eval analyzer (reported CLI engine version 0.1.0). This is a deterministic static assessment, not a behavior benchmark or release certification.

## At a glance

| Evaluated target | Score | Grade |
| --- | ---: | --- |
| Public runtime package 0.2.5 | 35/100 | F |
| Internal runtime package 0.2.5 | 35/100 | F |
| Previous internal runtime package 0.2.4 | 35/100 | F |
| Architecture QA skill | 100/100 | A |
| Draw.io Designer skill | 86/100 | B |
| PowerPoint Designer skill | 86/100 | B |
| Architecture Core skill | 77/100 | C |

QA is the strongest individually scored skill. Core is the weakest, primarily because its deferred resource inventory includes the large toolkit catalog. Initial whole-source scans scored 31/100 and additionally included development documents/scratch files and a working-directory naming mismatch; the release assessment uses clean component-only packages named `oci-architecture-designer`.

## Why it matters

The three failing bundle checks are the same in 0.2.4 and 0.2.5: no `privacyPolicyURL`, no `termsOfServiceURL`, and a deferred-file inventory above the analyzer's generic token threshold. Additional warnings concern instruction size, Python complexity/function length and long lines. No coverage artifact or observed model-usage log was provided.

The internal runtime estimates are 251 trigger tokens, 5,265 invocation tokens and 250,587 deferred tokens. The 0.2.4 estimates are 251, 4,912 and 246,601 respectively. These are static inventory estimates: the tool sums all four implicit skills for the invocation ceiling and counts catalog/reference files that the skills explicitly query selectively. They are not measured request consumption, savings or latency.

## Fix first — dispositions

| Finding | Disposition |
| --- | --- |
| Missing project privacy/terms URLs | Retained as explicit metadata limitations. No applicable project-specific policies have been established; adding an unrelated Oracle policy or an invented URL would misrepresent the community plugin. These optional ingestion fields are not structural component failures under the package format. |
| Excessive deferred token inventory | Retain the verified metadata catalogs and selective lookup helpers. They are required for source identity; the workflow forbids loading full catalogs into context. Runtime consumption remains unmeasured. |
| Aggregate invocation size | Preserve the four established skill entrypoints and conditional routing. New layer guidance is a separate selectively loaded reference. |
| Complexity/length/line warnings | Recorded as maintenance limitations; existing focused validators and fixed integration fixtures are covered by positive and negative regressions. No broad pre-release rewrite was made to chase the static grade. |
| Source-directory naming/scratch artifacts | Evaluate the actual runtime package with its correct name and component allowlist. This improves input fidelity, not measured runtime efficiency. |

The static grade remains F and is not represented as a pass. The author releases the additive source/helper functionality with these known limitations and the separate application/typography acceptance gates disclosed. The user explicitly requested evaluation followed by the next release; this assessment does not assert production readiness or Oracle endorsement.

## Recommended next step

Finish the bounded Draw.io/PowerPoint opening, export, movement and actual corporate-font checks described in [implementation verification](verification-layered-views.md). Establish legitimate project policies before adding their URLs. If measured usage is later needed, use a small paired scenario with an actual usage log; the earlier broad benchmark is not restarted for this release.

Reusable Plugin Eval request: “Evaluate this plugin.” The router is `plugin-eval start <plugin-root> --request "Evaluate this plugin." --format markdown`; the underlying assessment is `plugin-eval analyze <plugin-root> --format json`. Local raw JSON reports are retained separately from the distributed plugin.
