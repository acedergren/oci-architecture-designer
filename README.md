# OCI Architecture Designer

Four discoverable skills design and review OCI workload architectures and create editable Draw.io/PowerPoint deliverables. Version **0.2.1** is a focused patch release for toolkit download error handling. Installation and shared-plugin publication are separate actions.

| Skill | Responsibility |
| --- | --- |
| OCI Architecture Core | Requirements, decisions, scoped sources, shared model and asset provenance |
| OCI Draw.io Designer | Native graph, official groups and attached connectors |
| OCI PowerPoint Designer | Native shapes, source templates and OOXML dependencies |
| Architecture QA | Requirement fit, design/failure behavior and separate artifact-quality evidence |

Automatic discovery remains enabled for all four skills. Actual host selection is not established by static checks. No MCP server or OCI credentials are required.

## Architecture design and review

For a substantive design, Core captures a compact workload brief, evaluates realistic options and records why significant choices meet the requirements. Existing customer platforms, constraints and accepted decisions are inputs. A layout-only task preserves the established design; a review-only task reports findings without rewriting it.

The reference layer is loaded by need:

| Area | Local decision aid |
| --- | --- |
| Requirements, ADRs and C4 views | [Requirements to decisions](skills/oci-architecture-core/references/architecture-design.md) |
| OCI Well-Architected | [Workload review](skills/oci-architecture-core/references/architecture-review.md) |
| Architecture Center patterns | [Pattern selection](skills/oci-architecture-core/references/workload-patterns.md) |
| CAF and existing landing zone | [Cloud foundation](skills/oci-architecture-core/references/cloud-foundation.md) |
| MAA and recovery objectives | [Resilience](skills/oci-architecture-core/references/resilience.md) |
| Product/region/realm/endpoint/limit facts | [Service verification](skills/oci-architecture-core/references/service-verification.md) |

[Primary-source index](skills/oci-architecture-core/references/architecture-sources.md) records access date, applicability and refresh boundaries. These notes are original decision aids with links to primary references, not copied framework manuals, certification or a current service-availability database. Open the particular service/architecture article when a claim depends on it. Keep customer/internal inputs outside this public package.

Outputs can include a requirements brief, decision log, consistent model/views and review findings; a drawing is optional for advisory work. Every additional component needs a workload justification and operator. Keep a proposed RTO/RPO, documented product capability and measured deployed behavior distinct. No new external tool, account connection or runtime dependency is introduced.

## Requirements and verification

Shipped helpers use **Python 3.11+ and the standard library**. From the repository root:

```sh
python3 scripts/check.py
```

This runs synthetic helper regression tests, manifest identity/interface checks, internal Markdown-link checks and public-package checks. GitHub Actions runs the same offline command. It does not download Oracle assets or invoke renderers.

Architecture reasoning also has [six human-reviewed synthetic exercises](tests/architecture-reasoning.md). Package/metadata checks do not validate model decision quality. The exercise inputs are in [architecture-requests.json](tests/fixtures/architecture-requests.json); preserve raw responses outside the distributed package and evaluate consequences rather than matching words.

## Official toolkits

Reuse verified supplied files or download the official packages to a task-local cache **outside this repository/plugin**:

```sh
python3 skills/oci-architecture-core/scripts/fetch_drawio_toolkit.py --cache-dir /tmp/oci-task/toolkits
python3 skills/oci-architecture-core/scripts/fetch_pptx_toolkit.py --cache-dir /tmp/oci-task/toolkits
```

Both recheck cached bytes, limit download size and accept only HTTPS from docs.oracle.com, including redirects. A checksum change stops use: verify the new official source, reindex and review mappings before supplying a reviewed `--expected-sha256`. `--refresh` fetches again. Failure must not be hidden as an icon gap.

[Oracle's toolkit page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm) is the source of the official downloads. No toolkit archives, artwork, fonts or Oracle logo are included here. Original version labels/date ambiguity and hashes are in [provenance](skills/oci-architecture-core/references/official-assets.md). Runtime access does not establish permission to redistribute the toolkit through a plugin.

## Selective metadata lookup

Hash the actual source file (the extracted .drawio file, not its ZIP). Query an exact service meaning or source label:

```sh
python3 skills/oci-architecture-core/scripts/lookup_assets.py --service 'Compute virtual machine' --format drawio --sha256 b544991da988625e147dbeb7623bacc1be96699e2415d7f4d548f0d2a532d59e
python3 skills/oci-architecture-core/scripts/lookup_assets.py --service 'Oracle Base Database' --format pptx --sha256 e18615d90fbb38a3354e3a55d7d8baca59f6ba20de1af0a384addba73ede57ea
```

JSON returns only relevant candidates and locators. `MATCH` does not prove artwork identity. `NO_EXACT_MATCH` requires searching the verified source before declaring a service gap; it does not mean the toolkit is missing. Unknown hashes exit 1 with `SOURCE_NOT_VERIFIED`; review updated metadata instead of reusing pinned IDs. Multiple color/label groups require source inspection. Full catalogs remain reference data and need not enter ordinary model context.

Index supplied source files when needed:

```sh
python3 skills/oci-architecture-core/scripts/catalog_assets.py --drawio /tmp/oci-task/toolkits/toolkit.drawio --pptx /tmp/oci-task/toolkits/OCI_Icons.pptx --output /tmp/oci-task/catalog.json
```

## Structural checks and delivery

```sh
python3 skills/oci-drawio-designer/validate_drawio.py /tmp/oci-task/result.drawio
python3 skills/oci-powerpoint-designer/validate_pptx.py /tmp/oci-task/result.pptx
```

Both print JSON and exit 0 for a structural pass, 1 for failure. Draw.io covers IDs, references, cycles and attached edge endpoints. PowerPoint covers ZIP/XML integrity, OPC content types and entrypoint, internal relationship targets and references, slide order, shape IDs, connector references and markup-compatibility prefix bindings. External relationships are reported and never fetched. These are focused checks, not complete OOXML schema validation.

A parser pass does not establish application opening, visual quality, editability, topology or reachability. Use [delivery evidence v1](skills/oci-architecture-core/references/delivery-evidence.md) and report each dimension as PASS, FAIL or NOT_VERIFIED; reserve NOT_APPLICABLE for irrelevant dimensions. For intentional unattached annotation lines, record manual review separately from validator output.

## Opt-in official integration exercise

With the downloaded files in an external cache:

```sh
python3 tests/integration_official.py --toolkits /tmp/oci-task/toolkits --output /tmp/oci-task/deliverables
```

This fixed synthetic fixture creates two-page/two-slide files with the same regional VCN, subnets, load balancer, Compute VM, Base Database and internal flows. It copies original source groups and template dependencies, makes a scoped test edit and checks preservation of the reference view. It is not a general diagram generator or a model-driven benchmark.

Render using an available external tool, for example:

```sh
soffice --headless --convert-to pdf --outdir /tmp/oci-task/deliverables /tmp/oci-task/deliverables/architecture.pptx
```

Open both formats in their applications, move a node, save a separate test copy, reopen and confirm that the connector follows. Record actual checks; the fixture builder deliberately leaves application, visual and editability checks NOT_VERIFIED. Oracle binaries and generated output must remain outside Git. [Verification record](docs/verification-0.1.3.md) lists executed checks and remaining acceptance gaps.

## Distribution and release boundaries

`plugin.json` is the Agent Plugins manifest; `.codex-plugin/plugin.json` is the compatibility manifest. Name, version, description, author, keywords and interface agree. The compatibility manifest alone carries `skills`. This public export omits the private workspace logo, contact email and backend IDs. Account-specific packaging is prepared separately; never copy a private manifest wholesale into this repository.

Only a real project website link is supplied. Privacy/terms URLs are omitted because no applicable project-specific documents have been established. Do not invent URLs to raise an evaluator score. No source-code license change is made; public availability does not itself grant redistribution rights. Oracle names and marks belong to their owners, and this plugin implies no Oracle endorsement.

See [0.2.1 release notes](docs/release-0.2.1.md), [0.2.0 release notes](docs/release-0.2.0.md) and [behavior verification](docs/verification-0.2.0.md). The [0.1.3 artifact verification](docs/verification-0.1.3.md) remains historical evidence; its unverified UI and model-usage checks are not resolved by the new reference layer. No deployment, production readiness, compliance, certification or customer acceptance is established by these diagrams.
