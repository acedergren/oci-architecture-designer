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

[![CI](https://github.com/acedergren/oci-architecture-designer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/acedergren/oci-architecture-designer/actions/workflows/ci.yml)
![version](https://img.shields.io/badge/version-0.1.1-blue)
![Agent Plugins](https://img.shields.io/badge/Agent%20Plugins-1.0-informational)
![Python](https://img.shields.io/badge/helpers-Python%203%20stdlib-3776AB)
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

## Features

- **One model, two formats** - stable node IDs and one service-to-icon mapping shared by draw.io and PowerPoint.
- **Official icons only** - 47 partial cross-format mappings verified against labels and IDs in the inspected toolkit files.
- **Checksum pinning** - source URLs, retrieval date, sizes and SHA-256 hashes are kept in `provenance.json`.
- **Native editable output** - `.drawio` graphs with attached connectors and `.pptx` slides that keep the Oracle template.
- **Honest QA** - each QA dimension is reported separately as PASS, FAIL or NOT_VERIFIED.
- **No network** - the helpers use the Python 3 standard library and only read local files.

## Skills catalog

| Skill | Purpose |
| --- | --- |
| `oci-architecture-core` | Shared OCI semantics, resource scope, official icon constraints, and consistent mapping across formats. |
| `oci-drawio-designer` | Native editable `.drawio` diagrams with attached connectors and reusable official shape groups. |
| `oci-powerpoint-designer` | Editable `.pptx` architecture slides that preserve the supplied Oracle template and artwork. |
| `architecture-qa` | Separate checks for topology, icon identity, native file integrity, visual quality, and cross-format consistency. |

All four skills declare `policy.allow_implicit_invocation: true` in their `agents/openai.yaml` metadata. Whether a host actually selects them automatically has not been tested.

## Helpers

Both helpers use the Python 3 standard library and read local files. They do not download assets or contact OCI.

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

## Documentation

**Start here**
- [User Manual](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual): installation, using each skill, getting the official icons, troubleshooting

**Guides**
- [Create a draw.io diagram](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual#create-a-drawio-diagram-oci-drawio-designer)
- [Review a diagram](https://github.com/acedergren/oci-architecture-designer/wiki/User-Manual#review-a-diagram-architecture-qa)

**Reference**
- [Software Architecture](https://github.com/acedergren/oci-architecture-designer/wiki/Software-Architecture): skills, data flow, checksum pinning, decisions, risks
- [Asset provenance notes](skills/oci-architecture-core/references/official-assets.md)

**Contributing**
- [Developer Handbook](https://github.com/acedergren/oci-architecture-designer/wiki/Developer-Handbook): setup, checks, layout, conventions, how changes flow

## Development

There is no build step. An offline test suite lives in `tests/` and runs in CI (`.github/workflows/ci.yml`) on pull requests and pushes to `main`. Run it locally:

```sh
python3 -m compileall -q skills tests
python3 -m unittest discover -s tests -v
```

## Project structure

```
oci-architecture-designer/
├── plugin.json                  # Agent Plugins 1.0 manifest, v0.1.1
├── .codex-plugin/plugin.json    # compatibility manifest
├── .github/workflows/
│   ├── ci.yml                   # syntax, unit tests, source ZIP artifact
│   └── docs-webhook.yml         # notifies the docs bot on push/PR
├── tests/test_ci.py             # offline package checks and helper smoke tests
└── skills/
    ├── oci-architecture-core/   # SKILL.md, agents/, scripts/catalog_assets.py
    │   └── references/          # icon-map.json (47), toolkit-index.json, provenance.json, ...
    ├── oci-drawio-designer/     # SKILL.md, agents/, validate_drawio.py
    ├── oci-powerpoint-designer/ # SKILL.md, agents/
    └── architecture-qa/         # SKILL.md, agents/
```

`toolkit-index.json` holds source labels and locators without artwork. `provenance.json` holds official source URLs, the retrieval date, sizes, hashes and version caveats.

## Verification and limits

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
