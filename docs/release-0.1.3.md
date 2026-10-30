# 0.1.3 — local release candidate

- Reconciled reviewed 0.1.2 skill changes into the public source; preserved artwork/private-metadata exclusions.
- Added verified PowerPoint retrieval, rechecked local caches and rejected caches inside the plugin.
- Added exact service/format/hash metadata lookup to avoid reading full catalogs into context.
- Added PowerPoint package/relationship/connector validation and a regression check for undeclared markup-compatibility prefixes.
- Standardized delivery evidence and separate structural, opening, visual and editability status.
- Added synthetic regression tests, an offline local/CI gate and an opt-in official-artwork scenario.

Compatibility: Draw.io fetch/index/validation commands remain supported. Validator review fields now use NOT_VERIFIED rather than NOT_RUN. PowerPoint CLI is additive. No network request occurs in offline tests. Full catalogs remain available; no mapping/IDs are silently accepted after a source hash change.

Distribution: source and compatibility manifests carry 0.1.3 and a real project website. No toolkit binaries, cache, private workspace identifiers or new license are included. No privacy/terms URLs are fabricated. Publishing, pushing and installation have not been performed.

See [verification and limitations](verification-0.1.3.md) before treating this candidate as accepted for release. Static Plugin Eval scores are not functional or security certification.
