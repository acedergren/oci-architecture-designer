# Release 0.2.1

Focused patch to 0.2.0 (`7af1ba8`), retaining its four skills and runtime scope.
Later development features and benchmark tooling are not included in this release.

## Fix

Both toolkit download helpers now recognize HTML error pages, including Oracle
"Site Unavailable", before checksum/version handling. They report
`DOWNLOAD_UNAVAILABLE` and retain existing cached files. Real toolkit checksum
mismatches still require source inspection, reindexing and review.

The Core instructions require the format's binary helper before requesting a
manual attachment, distinguish web-reader limitations from Oracle availability,
and permit one bounded retry or an already verified local file. Toolkit hashes,
TLS checks, allowed download hosts and runtime dependencies are unchanged.

## Verification

`python3 scripts/check.py` passed all 19 release tests and package checks with
four skills and zero errors before tagging. The development branch has a larger
benchmark-support suite; its test count is not the release denominator.
The regression cases cover fresh HTML responses, failed refreshes, cached HTML,
valid packages and real checksum mismatches in both formats.

Live Oracle responses inspected during diagnosis matched the hashes already used
by 0.2.0. The specific cause of the reporter's remote Site Unavailable response
was not reproduced. See the [bug record](bugs/toolkit-download-unavailable.md).

No Oracle toolkit binaries, caches, credentials, private workspace identifiers
or private logs are included. This source release does not by itself update an
installed or shared account plugin. Native diagram behavior was not re-benchmarked.
