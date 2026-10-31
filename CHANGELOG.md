# OCI Architecture Designer — Changelog

Entries marked **Oracle-internal** apply only to Oracle-internal packages.

## 0.2.5 — Layered views and stronger review checks

- Added optional layer/view guidance while preserving native containers, VCN/subnet membership and complete icon groups.
- Added Draw.io --views validation for declared visibility, saved states, required elements and cross-layer connector endpoints.
- Defined separate native editable PowerPoint slides for selected views.
- Added scoped-edit regression checks protecting Draw.io content and PowerPoint groups, geometry and connector mappings.
- Required Oracle Sans for native diagram text, with explicit verification of actual font resolution.
- Added representative layered fixtures, release evidence and a Plugin Eval assessment.
- Updated CI to run the full offline suite and include referenced documentation and tests in source archives.

**Verification:** 36 public, 41 internal and 31 shared-source tests passed.

**Known limitations:** Application round trips, exported-view inspection, connector movement and actual typography remain unverified. Plugin Eval scored the runtime package 35/100 (F), unchanged from 0.2.4; missing project policy URLs and static budget findings remain disclosed.

Public packages continue to exclude Oracle artwork, fonts and private metadata. Oracle-internal packages retain their existing distribution restrictions.

## 0.2.4 — Provenance correction · **Oracle-internal**

- Corrected metadata to identify both included toolkits as bundled.
- Preserved the functionality and toolkit bytes tested for 0.2.3.

## 0.2.3 — Bundled toolkits and supplemental library · **Oracle-internal**

- Bundled pinned Draw.io and PowerPoint toolkits for offline use, with checksum verification.
- Extended selective lookup to supplemental marketing/UI symbols and logo variants, distinguishing them from official OCI service icons.
- Added SVG extraction with provenance for use as movable PowerPoint image objects.
- Expanded regression coverage for indexing, lookup, extraction and source integrity.

## 0.2.2 — Plugin branding · **Oracle-internal**

- Updated the listing and composer icon using an official Oracle asset, with recorded provenance.
- Preserved the four skills, runtime behavior, plugin identity and sharing settings.
- Kept Oracle branding outside the public source export.

## 0.2.1 — Toolkit download reliability

- Recognized HTML error responses, including Oracle “Site Unavailable”, before checksum validation.
- Reported DOWNLOAD_UNAVAILABLE while preserving existing cached files.
- Clarified verified-file reuse and bounded retries without weakening TLS, host or checksum checks.
