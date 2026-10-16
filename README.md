# OCI Architecture Designer

A skills-only plugin for creating and reviewing editable Oracle Cloud Infrastructure architecture diagrams and PowerPoint slides.

| Skill | Purpose |
| --- | --- |
| OCI Architecture Core | Shared OCI semantics, resource scope, official icon constraints, and consistent mapping across formats. |
| OCI Draw.io Designer | Native editable `.drawio` diagrams with attached connectors and reusable official shape groups. |
| OCI PowerPoint Designer | Editable `.pptx` architecture slides that preserve the supplied Oracle template and artwork. |
| Architecture QA | Separate checks for topology, icon identity, native file integrity, visual quality, and cross-format consistency. |

All four skills declare `policy.allow_implicit_invocation: true` in their `agents/openai.yaml` metadata. Actual automatic selection depends on the host and has not been tested here. No MCP server is required.

## Contents

- `plugin.json`: Agent Plugins 1.0 manifest, version 0.1.1.
- `.codex-plugin/plugin.json`: compatibility manifest with matching identity and metadata.
- `skills/`: four skill entrypoints, invocation metadata, shared references, and two Python helpers.
- `skills/oci-architecture-core/references/icon-map.json`: 47 partial cross-format mappings verified against labels and IDs in the inspected toolkit files.
- `skills/oci-architecture-core/references/toolkit-index.json`: source labels and locators, without artwork.
- `skills/oci-architecture-core/references/provenance.json`: official source URLs, retrieval date, sizes, hashes, and version caveats.

Use a compatible plugin host to load this package. Keep the directory structure intact: the skills refer to shared files within this repository. This repository is a source export, not a public ChatGPT directory listing.

## Official artwork is supplied separately

Download the relevant files from [Oracle's OCI Architecture Diagram Toolkits page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm) and supply them to the task in an environment that can inspect and edit files.

Oracle stencil/template binaries, extracted icons, fonts, and the Oracle logo are **not included** in this public repository. Permission to redistribute those assets through this package was not established. The private workspace plugin's logo is separate from this public source export. See [Oracle's materials terms](https://www.oracle.com/legal/terms/), [logo guidelines](https://www.oracle.com/legal/logos/), and the package's [asset provenance notes](skills/oci-architecture-core/references/official-assets.md).

The inspected downloads were retrieved on 2026-10-16, but the server reports an April 2024 modification date. Internal version labels differ; this is not a claim of a 2026 icon refresh. Newer official files need reindexing and review before using pinned shape locators.

If an official icon is unavailable, the skills require a clearly labeled neutral text component and disclosure of the gap. They must not invent or substitute an Oracle pictogram.

## Helpers

Both helpers use the Python 3 standard library and read local files. They do not download assets or contact OCI.

Index official toolkit attachments as metadata:

```sh
python3 skills/oci-architecture-core/scripts/catalog_assets.py \
  --drawio /path/to/toolkit.drawio \
  --library '/path/to/OCI Library.xml' \
  --pptx /path/to/OCI_Icons.pptx \
  --output /path/to/catalog.json
```

At least one toolkit input is required; the others can be omitted.

Check native draw.io graph integrity:

```sh
python3 skills/oci-drawio-designer/validate_drawio.py /path/to/result.drawio
```

The graph check covers IDs, parent cycles, references, and attached edge endpoints. It does not prove topology, reachability, rendering, or visual quality. Intentional annotation lines without attached endpoints need manual review.

## Verification and limits

The originating package passed manifest/schema checks, skill metadata validation, internal reference checks, source checksum and icon-locator checks, deterministic indexing against the official downloads, and positive/negative graph-integrity cases. The public export is additionally checked for matching manifests, valid references, and exclusion of private workspace identifiers and artwork.

Full diagram generation, host automatic selection, PowerPoint opening, and rendered layout quality have not been verified end to end. The skills require those checks when the necessary source files and tools are available. A diagram is not evidence of deployment, production readiness, compliance, or Oracle certification.

Oracle names and marks belong to their respective owners. This project does not imply Oracle endorsement. No open-source license has been selected for this repository; public source availability does not itself grant a general redistribution license.
