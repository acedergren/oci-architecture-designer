# OpenAI profiles and image delivery verification

Date: 2026-10-26. This is a local source follow-up to the 0.2.0 candidate, not an installed/published release or a change to either pinned benchmark arm. Four skills and the existing native validators/CLIs are retained. No new program/runtime behavior, API client, renderer, account setting or package dependency is introduced.

## Evidence boundaries

The [model profiles](../skills/oci-architecture-core/references/openai-model-profiles.md) cite official OpenAI sections checked on this date. These establish documented capabilities, not model access or measured quality. The image backend of an opaque host tool remains unknown. The [image exercises](../tests/image-delivery.md) are separate from the architecture benchmark. Official toolkits, images, prompts and raw execution evidence stay outside Git.

| Check | Status | Evidence and limit |
| --- | --- | --- |
| Baseline offline tests/package | PASS | 70 tests, four skills, zero package errors before this change |
| Updated offline tests/package | PASS | 70 tests, four skills, zero package errors; JSON/YAML parsed; `git diff --check` passes |
| Technical export, create/edit | NOT_VERIFIED | Requires actual native files and saved images inspected against the model |
| Generated illustration, create/edit | NOT_VERIFIED | Requires actual host image-tool output and full-image inspection |
| Negative cases | NOT_VERIFIED | Distinguish executed helper checks from manual instruction review |
| Natural skill discovery/activation | NOT_VERIFIED | This side conversation is already explicitly instructed; no isolated natural-prompt agent is run here |
| Independent/model-specific quality evaluation | NOT_VERIFIED | No subagents are used in this side conversation; named profile coverage requires observed executions |
| Installation/publication | NOT_APPLICABLE | Excluded from this source task |

All twelve QA dimensions retain their meanings. Image-only editability is N/A only when no native editability requirement exists. No parser/converter result promotes visual quality, native opening or connector behavior to PASS. Missing usage/model data stays null/NOT_VERIFIED.
