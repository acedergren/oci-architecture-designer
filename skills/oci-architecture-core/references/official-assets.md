# Official toolkit provenance and usage boundary

**Bundling status: NOT BUNDLED.** Both downloads were retrieved and inspected on 2026-10-16 from the links on [Oracle's OCI Architecture Diagram Toolkits page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm). No stencil artwork, extracted icons, complete templates, fonts, or source archives are included in this plugin.

The page invites use of the assets for OCI diagrams. However, the inspected downloads contain no separate license granting redistribution of the whole toolkit through a third-party plugin. [Oracle Web Sites Terms of Use, sections 1–5](https://www.oracle.com/legal/terms/) distinguish specific content terms and restrict redistribution under the general materials terms; [Oracle Legal Notices](https://docs.oracle.com/en-us/iaas/Content/legalnotices.htm) also describe license restrictions. We did not verify additional contractual rights for this workspace. This is a packaging constraint based on the available terms, not a claim that Oracle forbids every internal use or that a user's separate agreement grants no rights.

For draw.io output, use legitimately obtained official files from task inputs, a verified local cache, or the official Oracle download at runtime. Downloading for the current diagram does not require bundling the toolkit in this distributed plugin. Keep the cache outside the plugin package. Treat attached or downloaded files as task inputs; do not silently add them to a distributed plugin or relicense them. PowerPoint also supports verified runtime retrieval with `fetch_pptx_toolkit.py`; supplied official sources remain supported. If a separate authorization permits bundling, preserve its scope, provenance, copyright notices, and actual limits before making a new release. Private visibility by itself does not establish redistribution permission. Do not apply a permissive license to Oracle assets or imply Oracle endorsement.

## Download inventory

- [PowerPoint toolkit](https://docs.oracle.com/iaas/Content/Resources/Assets/OCI_Icons.pptx): 3,949,330 bytes; 48 slides. SHA-256 `e18615d90fbb38a3354e3a55d7d8baca59f6ba20de1af0a384addba73ede57ea`.
- [Draw.io toolkit ZIP](https://docs.oracle.com/iaas/Content/Resources/Assets/OCI-Style-Guide-for-Drawio.zip): 6,997,183 bytes; 9,280,487 expanded bytes. SHA-256 `8e20646de88b6197f7b2ce941219fdb61e88b2b6276e3e7b5e0ce046445174e8`.
- ZIP members: `OCI Style Guide for Drawio/OCI Library.xml` (1,472,484 bytes), `Read-ME.drawio` (3,131,773 bytes), and `OCI Architecture Diagram Toolkit v24.2.drawio` (4,676,230 bytes). The directory entry contains no data.
- The server reported Last-Modified `Mon, 29 Apr 2024 22:11:18 GMT` for both downloads. The PPTX cover says v24.1 January 2024; the Draw.io filename says v24.2 but internal text also says v24.1 March 2024. Preserve this ambiguity; do not call these a 2026 icon refresh.

[provenance.json](provenance.json) records original and extracted checksums. [toolkit-index.json](toolkit-index.json) contains labels and shape locators, no artwork. [icon-map.json](icon-map.json) provides a partial verified cross-format map, not a complete service inventory or a guarantee that later services have icons.

## Runtime procedure

For either format, reuse a verified local toolkit or run `python3 ../scripts/fetch_drawio_toolkit.py --cache-dir /path/to/task/cache/official-oci` relative to this references directory. The helper downloads only from Oracle over HTTPS, checks the archive hash, extracts only the three expected data files, and writes `toolkit-provenance.json`. It checks cached bytes again on reuse; use `--refresh` to retrieve again. Keep toolkit binaries out of plugin update/export ZIPs.

A checksum mismatch stops extraction: inspect the new official download, reindex and review its labels and geometry, then explicitly supply its reviewed SHA-256 with `--expected-sha256`. Do not silently retain stale cell IDs or disable verification. Record URL, retrieval time, hash, original labels, and selected source cells.

Only if download/file execution is unavailable, explain that limitation and request the relevant toolkit attachment. Continue topology review where useful, but do not call an icon-free draft complete when real stencils are required. A service absent from an inspected toolkit may remain a neutral component with the exact gap disclosed. Never fabricate an output file or claim a link was downloaded without accessing its bytes.

For PowerPoint, run `python3 ../scripts/fetch_pptx_toolkit.py --cache-dir /path/to/task/cache/official-oci` with the same hash-review and cache rules. Its provenance file is `pptx-toolkit-provenance.json`.

The standard-library helper `../scripts/catalog_assets.py` accepts `--drawio`, `--library`, `--pptx`, and `--output`; at least one input is required. It reads local attachments and writes metadata only. It neither downloads nor extracts artwork. Verify hashes against provenance before using pinned IDs; index and review a new version if hashes differ. Only open expected XML/OOXML data; never execute macros or scripts from a toolkit.

## Package constraints

The creation workflow limits each SKILL.md to 1 MiB and listing subtitle to 30 characters; any optional listing icons must satisfy the workflow's separate image limits. No overall archive limit was stated in the available workflow. Toolkit artwork is kept outside the package; the existing listing logo is separate from the diagram stencils. Inspect final archive contents and backend diagnostics; respect any limit actually returned rather than claiming an unknown limit was tested.
