# Privacy notice

**Effective date: 2026-10-31.** Approved by the project owner.

## Scope

This notice describes OCI Architecture Designer's skills and Python helpers. The public community package and Oracle-internal package have different asset permissions. This project does not represent Oracle, and this notice does not replace the policies or agreements of Oracle, your employer, your AI provider or your applications.

## Information used

Tasks can include prompts, requirements, architecture descriptions, diagrams, presentation files and selected source material. Helpers can read the local files and directories selected for a task, verify source hashes, search catalog metadata, validate artifacts and write outputs or evidence to the selected location.

The supplied helpers do not implement a project-operated account service, analytics endpoint or automatic telemetry collection. This does **not** mean that everything stays on your computer: the AI host can process prompts, attachments, tool results and selected file contents under its own settings and policies. Other connected tools may also process information when used for an authorized task.

## Network requests and applications

The optional toolkit-fetch helpers contact Oracle's official download host and verify returned files. The receiving service may receive ordinary request information such as an IP address and request headers. These download helpers are not designed to upload your architecture diagrams.

Draw.io, PowerPoint, browsers and other tools have their own processing and storage behavior. Some Draw.io export paths use an external rendering service. The recommended local Print to PDF path avoids that service for the diagram export. Cloud storage, sharing, publishing and connected-tool actions must be assessed separately for the task.

## Files and retention

Source files, output artifacts, local download caches and evidence remain in their selected locations until the user or an applicable system removes them. The project does not centrally retain those local files or set retention periods for an AI host, application, connected service or employer environment. Review those systems' own retention settings.

Evidence should contain only what is necessary to support the result. Do not include credentials, customer inputs or restricted information in public repositories, plugin packages, issue reports or release evidence.

## Oracle-internal material

Bundled internal toolkits, supplemental libraries and their notices remain subject to their existing audience and usage restrictions. Their presence does not authorize external disclosure. Public packages exclude Oracle artwork, font binaries and private package metadata.

## Questions and changes

Contact the project maintainer through the [repository](https://github.com/acedergren/oci-architecture-designer). Do not submit confidential information in public issues. Approved revisions should state their effective date and remain traceable in repository history.
