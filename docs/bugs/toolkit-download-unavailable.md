# Toolkit download reported as a changed version

Investigated on 2026-10-28. The report described a toolkit-version mismatch,
followed by an Oracle "Site Unavailable" page and a request for an attachment.
The reporter's original command and response bytes were not supplied.

## Findings

Both links on the [official Oracle toolkit page](https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm)
returned valid toolkit bytes in the local probe, with the hashes already pinned
in 0.2.0:

| Format | HTTP | Content type | Bytes | Pinned checksum |
| --- | ---: | --- | ---: | --- |
| Draw.io | 200 | application/zip | 6,997,183 | MATCH |
| PowerPoint | 200 | application/vnd.openxmlformats-officedocument.presentationml.presentation | 3,949,330 | MATCH |

The server redirected both URLs to the documented `docs.oracle.com/en-us/`
paths. No artwork change or new checksum was observed. Original and patched
helper CLIs accepted the exact captured bytes from a separate verification
cache. Official binaries and raw responses remain outside Git.

The web-page reader could not consume either binary format and returned
`Unsupported content-type`. This is distinct from an unavailable Oracle site.
The specific cause of the reporter's Site Unavailable response is unverified;
it may depend on the download route, network or service state.

A concrete code defect was reproduced with a synthetic HTML Site Unavailable
response: both helpers checked its SHA-256 before recognizing that it was not
a toolkit, incorrectly suggesting a changed release. Supplying the HTML hash
instead produced a ZIP-parser exception. Failed downloads did not overwrite an
existing cache, and that protection is retained.

## Scoped correction

- Recognize HTML responses before checksum/version handling in both helpers.
- Report `DOWNLOAD_UNAVAILABLE`, preserve cached files and provenance, and
  retain the existing checksum guard for actual toolkit data.
- Tell the agent to use the format's binary helper before requesting an
  attachment. A web-reader failure or changed Last-Modified metadata does not
  prove changed artwork. Allow one bounded retry or an already verified local
  file; never weaken TLS or accept an error page's hash.

The shared HTML check remains in the existing Draw.io helper, which the
PowerPoint helper already imports. There is no new dependency, download mirror,
checksum, automatic hash acceptance, installation or publication.

## Verification

Two regression tests first reproduced the wrong checksum/parser errors, then
passed after the correction. They cover fresh downloads, failed refreshes and
cached HTML across both formats. Existing valid-file and real archive checksum
mismatch checks remain green.

```sh
python3 -m unittest tests.test_lookup_fetch.DownloadFailures tests.test_lookup_fetch.FetchPptx
python3 scripts/check.py
```

The complete offline check passed 97 tests and package checks with four skills
and zero errors. This verifies response classification and preserved integrity
checks, not availability from the reporter's environment or an improved
architecture benchmark result. The published plugin is unchanged by this local
source correction.
