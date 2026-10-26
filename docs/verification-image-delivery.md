# OpenAI profiles and image delivery verification

Date: 2026-10-26. Local source follow-up to the 0.2.0 candidate; no installation/publication or alteration of either pinned benchmark arm. Four skills and the existing native validators/CLIs are retained. No new API client, renderer, account setting, font installation or package dependency is introduced.

## Source and method

The [OpenAI profiles](../skills/oci-architecture-core/references/openai-model-profiles.md) cite official capabilities checked on this date. The user's [Oracle Redwood reference](https://redwood.oracle.com/) was read in a rendered browser because a text fetch returned only its JavaScript shell. The [style contract](../skills/oci-architecture-core/references/oracle-redwood-style.md) separates Redwood presentation guidance from OCI toolkit artwork/notation.

The [image exercises](../tests/image-delivery.md) were run as an explicitly instructed local create/edit trial, separately from the frozen architecture comparison. Raw evidence is in the external task directory `openai-image-delivery-2026-10-26`: model files, prompts, native sources, PNGs, validators, source snapshots/hashes, palette/font observations, per-artifact QA and earlier failed attempts. No binary artwork, fonts, generated files or private logs are distributed in this plugin.

## Observed results

| Check | Status | Evidence and limit |
| --- | --- | --- |
| Baseline offline tests/package | PASS | 70 tests, four skills, zero package errors before this work |
| Updated offline tests/package | PASS | 70 tests; four skills; zero package errors; JSON/YAML parsed; `git diff --check` passes |
| Native source integrity | PASS | Existing Draw.io/PPTX integration sources pass; both separate initial/second-Compute PPTX sources pass the PPTX validator |
| Technical PNG create/edit | PASS | Saved 1280x720 images decoded/opened and visually compared with the fixed model: three then four resources, two then four directed flows |
| Scoped edit/reference preservation | PASS | Existing shapes unchanged; only the architecture slide XML changes; the second slide renders to identical pixels before/after |
| Technical Oracle/Redwood style | PASS | Copied original icon groups/labels, source palette/grouping, thin open-arrow connectors; actual OracleSans fonts observed in exported PDF |
| Generated image create/edit semantics | PASS | Saved images inspected; required resources, exact labels, membership and directed flows preserved after adding the second Compute |
| Generated exact Oracle style/asset identity | NOT_VERIFIED | Generic first style rejected; source-referenced pair and color-only correction improve appearance but do not establish exact source palette/artwork identity; retain as drafts for exact requirements |
| Native opening/move/save/reopen | NOT_VERIFIED | Image viewing/conversion does not prove native PowerPoint/Draw.io behavior; native editability was not requested by this image trial |
| Exact-icon gap / unknown source hash | PASS | Real helper returns NO_EXACT_MATCH for a custom appliance; actual verified source label search has no hit. Unknown hash exits 1/SOURCE_NOT_VERIFIED |
| Hidden image backend handling | PASS | All five tool responses expose only image/result hint fields; observed model/usage left null/NOT_VERIFIED |
| Missing tools, unsupported SVG/current service claim | NOT_VERIFIED | Acceptance inputs added; independent agent scenarios not executed in this side conversation |
| Natural skill discovery/activation | NOT_VERIFIED | Current context is already explicitly instructed; no fresh natural-prompt agent run |
| Named model profiles / independent quality review | NOT_VERIFIED | No backend identity or independent/subagent/model comparison is available; author self-review only |
| Installation/publication | NOT_APPLICABLE | Excluded from this source task |

## Failures retained and resource limits

The first technical export passed parsing but attached connectors to unintended freeform sites. A task-local attachment-shape correction fixed visible endpoints. The next render exposed serif font substitution despite Oracle Sans declarations. A separate converter font configuration used existing system fonts, with actual font names verified in exported PDF; ordinary settings/cache were not changed. The distributed fixture builder is unchanged.

The user rejected the initial generic teal illustration style. This produced a durable instruction fix: both image routes now require inspected Oracle/OCI references, and visual QA includes font, palette, grouping and connector fidelity. Earlier images remain failed style counterexamples. Exact palette cannot be approved merely because an image prompt contains HEX values.

Five actual image calls took **184.398 seconds** in total, including superseded and correction attempts. This is image-tool elapsed time, not total task or operator time. Token/cache usage, monetary cost and actual image backend were not exposed and remain null/NOT_VERIFIED. Converter timings and failures are recorded separately outside Git. No general quality or resource-efficiency advantage of any named model is established.

All twelve QA dimensions retain their meanings. Image-only native editability is N/A only without a native editability requirement. No parser/converter result promotes native opening or connector behavior to PASS. Source implementation and local artifact evidence are distinct from full acceptance: natural activation, missing-tool agent behavior, exact generated styling and model-specific evaluation remain open.
