```
 ██████╗  ██████╗██╗
██╔═══██╗██╔════╝██║
██║   ██║██║     ██║
██║   ██║██║     ██║
╚██████╔╝╚██████╗██║
 ╚═════╝  ╚═════╝╚═╝
   A R C H I T E C T U R E   D E S I G N E R
```

# OCI Architecture Designer

> **Community project.** It has no affiliation with Oracle, and Oracle does not endorse it. Oracle names and marks belong to their respective owners.

**Editable OCI architecture diagrams and slides from your agent, using only official Oracle artwork that you supply.**

A skills-only plugin for creating and reviewing editable Oracle Cloud Infrastructure architecture diagrams (`.drawio`) and PowerPoint slides (`.pptx`). No MCP server is required.

![version](https://img.shields.io/badge/version-0.2.5-blue)
![Agent Plugins](https://img.shields.io/badge/Agent%20Plugins-1.0-informational)
![Python](https://img.shields.io/badge/helpers-Python%203.11%2B%20stdlib-3776AB)
![license](https://img.shields.io/badge/license-not%20selected-lightgrey)

## Why this

Agents tend to make up cloud icons and add gateways, subnets or regions nobody asked for. These skills make the agent build one architecture model first, take icons only from Oracle's official toolkits, and report every check as PASS, FAIL or NOT_VERIFIED.

```text
You:   Create an editable OCI architecture diagram using official Oracle toolkits I provide.
Agent: oci-architecture-core  -> model + icon mapping (hash-checked)
       oci-drawio-designer    -> result.drawio (validate_drawio.py: PASS)
       architecture-qa        -> Topology PASS · Visual quality NOT_VERIFIED · ...
```

## Getting started

1. **Clone** the repository and keep the directory structure intact, because the skills refer to shared files in it:
   ```sh
   git clone https://github.com/acedergren/oci-architecture-designer.git
   ```
2. **Load** it in a compatible plugin host. `plugin.json` is an Agent Plugins 1.0 manifest, and `.codex-plugin/plugin.json` is a compatibility manifest. This repository is a source export, not a public ChatGPT directory listing.
3. **Download the official artwork** from [Oracle's OCI Architecture Diagram Toolkits page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm) and supply it to the task in an environment that can inspect and edit files (see below).
4. **Ask** for a diagram, a slide or a review. The agent can also select the skills automatically, depending on the host (see the note under Skills catalog).

## Official artwork is supplied separately

Download the relevant files from [Oracle's OCI Architecture Diagram Toolkits page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm) and supply them to the task in an environment that can inspect and edit files.

Oracle stencil/template binaries, extracted icons, fonts, and the Oracle logo are **not included** in this public repository. Permission to redistribute those assets through this package was not established. The private workspace plugin's logo is separate from this public source export. See [Oracle's materials terms](https://www.oracle.com/legal/terms/), [logo guidelines](https://www.oracle.com/legal/logos/), and the package's [asset provenance notes](skills/oci-architecture-core/references/official-assets.md).

The inspected downloads were retrieved on 2026-10-16, but the server reports an April 2024 modification date. Internal version labels differ, so this is not a claim of a 2026 icon refresh. Newer official files need reindexing and review before using pinned shape locators.

If an official icon is unavailable, the skills require a clearly labeled neutral text component and disclosure of the gap. They must not invent or substitute an Oracle pictogram.

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

## Features

- **One model, two formats** - stable node IDs and one service-to-icon mapping shared by draw.io and PowerPoint.
- **Official icons only** - 47 partial cross-format mappings verified against labels and IDs in the inspected toolkit files.
- **Checksum pinning** - source URLs, retrieval date, sizes and SHA-256 hashes are kept in `provenance.json`.
- **Native editable output** - `.drawio` graphs with attached connectors and `.pptx` slides that keep the Oracle template.
- **Honest QA** - each QA dimension is reported separately as PASS, FAIL or NOT_VERIFIED.
- **Offline validation** - structural validators use Python 3.11+ and local files. Separate fetch helpers support verified official downloads to an external cache.
- **Optional layers** - declared views check saved visibility and required flows while preserving native containment; PowerPoint uses separate editable slides.
- **Corporate typography** - Oracle Sans is required for native diagram text, with actual application/export resolution checked separately.

## Skills catalog

| Skill | Purpose |
| --- | --- |
| `oci-architecture-core` | Shared OCI semantics, resource scope, official icon constraints, and consistent mapping across formats. |
| `oci-drawio-designer` | Native editable `.drawio` diagrams with attached connectors and reusable official shape groups. |
| `oci-powerpoint-designer` | Editable `.pptx` architecture slides that preserve the supplied Oracle template and artwork. |
| `architecture-qa` | Separate checks for topology, icon identity, native file integrity, visual quality, and cross-format consistency. |

All four skills declare `policy.allow_implicit_invocation: true` in their `agents/openai.yaml` metadata. Whether a host actually selects them automatically has not been tested.

## Helpers

The validators and catalog helpers use Python 3.11+ and local files. Fetch helpers can retrieve verified Oracle toolkits into a cache outside the plugin; no OCI credentials are needed.

Index official toolkit attachments as metadata (at least one toolkit input is required; you can omit the others):

```sh
python3 skills/oci-architecture-core/scripts/catalog_assets.py \
  --drawio /path/to/toolkit.drawio \
  --library '/path/to/OCI Library.xml' \
  --pptx /path/to/OCI_Icons.pptx \
  --output /path/to/catalog.json
```

Check native draw.io graph integrity:

```sh
python3 skills/oci-drawio-designer/validate_drawio.py /path/to/result.drawio
```

The graph check covers IDs, parent cycles, references, and attached edge endpoints. It does not prove topology, reachability, rendering, or visual quality. Intentional annotation lines without attached endpoints need manual review.

## Optional layers and named views

Use [layered views](skills/oci-architecture-core/references/layered-views.md) for independent visibility, editing protection or selected exports. Preserve VCN/subnet ancestry and complete icon groups. A simple diagram can keep one default layer.

```sh
python3 skills/oci-drawio-designer/validate_drawio.py result.drawio --views architecture.views.json
python3 skills/oci-powerpoint-designer/validate_pptx.py result.pptx
```

Structural PASS does not prove rendering, font resolution, architectural completeness or editability. See [delivery evidence](skills/oci-architecture-core/references/delivery-evidence.md), [release notes](docs/release-0.2.5.md) and [Plugin Eval assessment](docs/plugin-eval-0.2.5.md).

## Documentation

**Start here**
- [User Manual](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual): installation, using each skill, getting the official icons, troubleshooting

**Guides**
- [Create a draw.io diagram](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual#create-a-drawio-diagram-oci-drawio-designer)
- [Review a diagram](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual#review-a-diagram-architecture-qa)

**Reference**
- [Software Architecture](https://github.com/acedergren/oci-architecture-designer/wiki/Software-Architecture): skills, data flow, checksum pinning, decisions, risks
- [Asset provenance notes](skills/oci-architecture-core/references/official-assets.md)
- [Privacy notice](docs/privacy.md) and [usage terms](docs/terms.md): what the helpers process, and what the project does and does not permit

**Contributing**
- [Developer Handbook](https://github.com/acedergren/oci-architecture-designer/wiki/Developer-Handbook): setup, checks, layout, conventions, how changes flow

## Development

Offline package, link and synthetic regression checks run in CI. Run the complete public suite locally with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check.py
```

The existing CI and documentation-webhook workflows are retained. Neither publishes a plugin. See [layered-view verification](docs/verification-layered-views.md) for executed checks and outstanding application/font gates.

## Project structure

```
oci-architecture-designer/
├── plugin.json                  # Agent Plugins 1.0 manifest, v0.2.5
├── .codex-plugin/plugin.json    # compatibility manifest
└── skills/
    ├── oci-architecture-core/   # SKILL.md, agents/, scripts/catalog_assets.py
    │   └── references/          # icon-map.json (47), toolkit-index.json, provenance.json, ...
    ├── oci-drawio-designer/     # SKILL.md, agents/, validate_drawio.py
    ├── oci-powerpoint-designer/ # SKILL.md, agents/
    └── architecture-qa/         # SKILL.md, agents/
```

`toolkit-index.json` holds source labels and locators without artwork. `provenance.json` holds official source URLs, the retrieval date, sizes, hashes and version caveats.

## Verification and limits

Current checks: 36 public, 41 internal and 31 shared-source tests pass. Native application, exported-view, connector-movement and actual typography acceptance remain open; the local font resolver substitutes Helvetica for Oracle Sans. This release does not claim those checks passed.


GitHub Actions runs one offline validation job on pull requests, pushes to `main`,
and manual dispatch. It checks Python syntax, JSON files, matching manifests,
skill entrypoints, and helper smoke tests, then builds a downloadable source ZIP
retained for seven days in the workflow run. No secrets,
Oracle downloads, deployment, or plugin publication are required. Run the same
checks locally with:

```sh
python3 -m compileall -q skills tests
python3 -m unittest discover -s tests -v
```

The originating package passed manifest/schema checks, skill metadata validation, internal reference checks, source checksum and icon-locator checks, deterministic indexing against the official downloads, and positive/negative graph-integrity cases. The public export is additionally checked for matching manifests, valid references, and exclusion of private workspace identifiers and artwork.

Full diagram generation, automatic selection by a host, PowerPoint opening, and rendered layout quality have not been verified end to end. The skills require those checks when the necessary source files and tools are available. A diagram is not evidence of deployment, production readiness, compliance, or Oracle certification.

No open-source license has been selected for this repository. Public source availability does not itself grant a general redistribution license.

---

Created by **Alexander Cedergren**. Built with Agent Skills (Markdown), JSON references and Python 3.
