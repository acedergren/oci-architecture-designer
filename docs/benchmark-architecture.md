# Architecture quality comparison

This opt-in campaign compares the runtime content of source revisions `552dd48`
(0.1.3) and `7af1ba8` (0.2.0). It is not a Plugin Eval static-score comparison.
Quality takes priority; resource changes are reported as tradeoffs. No deployment,
publication or ordinary plugin installation is performed.

## Frozen experiment

The six original reasoning requests and one native workflow for each format run
three times against each revision: 48 primary workflows, grouped in 24 matched
pairs. The configuration fixes the order seed, model `gpt-6.1-sol`, effort `xhigh`,
and 1,200-second workflow limit. Two successful technical pilots are excluded from
the primary comparison; unsuccessful setup attempts remain in the raw evidence.

The runtime export includes manifests and the four skill directories. Development
documentation, test questions, grading rubrics and the campaign runner are not
exposed to the working agent. Each workflow receives a fresh directory, test
profile and conversation. File creation and its requested edit share that
workflow's conversation. No Git worktree is created.

Only authentication is copied into the temporary profile, with private file
permissions. Ordinary user configuration is not copied. Global standalone skills,
bundled skills, memory, apps and nested agents are disabled. The candidate is
registered in a temporary local marketplace. The catalog must contain exactly
the four candidate skills. Temporary authentication is removed on completion or
setup failure; credentials are never written to result JSON or Git.

Codex's native named permission profile extends its supported workspace profile.
It denies the control repository, evidence directory, ordinary Codex/agent homes
and neighboring trial data, while allowing the active workspace and task temp
directory. Inputs and plugin content are read-only to tool execution. Before
inference, app-server command queries prove controller/repository reads and
controller writes are denied and workspace writes work. The effective profile,
model and effort are recorded from persisted execution context.

Managed policy is authoritative. This environment permits `on-request` approvals,
cached search and workspace permissions; the runner does not override those
requirements. Direct fresh-source access is not established merely by cached
search. Missing current evidence stays unverified.

## Commands

Requires Python 3.11+, Git, a supported authenticated Codex CLI with native
permission profiles, and verified local official toolkit files. All evidence and
official/generated binaries must be outside this repository.

```sh
python3 scripts/benchmark_architecture.py preflight \
  --toolkits /path/to/verified/toolkits --output /path/outside/repo/campaign
python3 scripts/benchmark_architecture.py run \
  --toolkits /path/to/verified/toolkits --output /path/outside/repo/campaign
python3 scripts/benchmark_architecture.py review-pack --output /path/outside/repo/campaign
python3 scripts/benchmark_architecture.py review-pack --judge --output /path/outside/repo/campaign
# Complete the actual human reviews under reviews/human/, then:
python3 scripts/benchmark_architecture.py review-pack --lock-reviews --output /path/outside/repo/campaign
python3 scripts/benchmark_architecture.py report --output /path/outside/repo/campaign
```

`--config` selects a campaign file; the default is
`tests/benchmark/campaign.json`. The complete primary schedule is fixed before
inference. A changed configuration cannot reuse the pilot gate. Completed runs
are not silently repeated. `run` exits 2 when an artifact needs application
checks; perform those checks and call `run` again to continue the same workflow.
An infrastructure error stops execution and is retained, not graded as an
architecture mistake or removed from the denominator.

Preflight freezes the grading rubric under `frozen/`. Subsequent commands verify
its hash. Reviewer inputs bind that rubric and every answer, check and image to
the pair; duplicate pairs or changed inputs cannot satisfy the review lock.

`preflight --reprocess-pilots` reinterprets existing raw logs after a telemetry
correction without inference. It preserves original outcomes, records hashes of
its source events/outcomes, revalidates runtime content and checks the transferred
native file. It cannot turn a missing file or missing usage into a successful
pilot. There is no simulated benchmark or automatic model fallback.

## Measurement and application evidence

Each run preserves raw CLI JSONL, stderr, phase answers, source manifests,
effective execution context, file evidence and elapsed time. CLI terminal usage
is retained, but follow-up billing is calculated from the difference between
persisted per-thread `total_token_usage` counters. Counter resets or absent
values are unknown, not zero. Cached input is separate from total input; it is
not added a second time. Only verified complete samples can support resource
comparisons. Failed workflows retain their observed resource consumption.

Workspace evidence is copied outside temporary trial directories with a hash
manifest, including sources the agent actually saved. Supplied toolkits, plugin
runtime content and symlinks are excluded from that copy. Environment records
capture CLI/Python, available library versions, application versions and tool
paths. A web renderer version remains unverified until observed in its UI.

Tool calls are deduplicated by turn/item identity and nested failures are counted.
Exact failed calls repeated with a new item ID are counted separately; semantic
repairs using different commands remain unverified. Human corrections are zero
only when no human correction was supplied in the fixed workflow. Application
validation and review work are separate from correction effort.

Skill discovery, reading and useful application are separate observations.
Successful tool output matching the complete immutable skill source is stronger
read evidence than an agent saying it used a skill. Reading still does not prove
good application; that is assessed against the resulting decisions/artifact.

Native workflows preserve initial and edited files. Structural validators run
separately from application opening, visual inspection and move/save/reopen.
For a pending run, store `application-evidence.json` in that run's evidence folder:
identify the edited artifact by SHA-256 and provide `application_opening`,
`visual_quality` and `editability`, each with status, method and evidence filenames.
PASS requires existing local evidence files; unavailable checks use NOT_VERIFIED.
The working agent cannot write this controller evidence. It receives a copy for
final QA reporting and is instructed not to alter the native artifact then.

Use Draw.io in Chrome and the existing PowerPoint installation. Do not install a
renderer to improve a result. Move a Compute node within its subnet in a test
copy, save a local file, close/reopen that file and inspect attached connectors.
Record the unchanged reference view and cross-format resources/flows separately.
A parser pass cannot promote any application or visual dimension to PASS.

## Blind assessment and release boundary

After all 48 workflows complete, `review-pack` creates 24 A/B pairs and one human
sample per scenario. The private version key is stored outside review packs.
Reviewers receive original requests, anonymized answers, normalized structural
evidence and checked renders. Native packages stay outside the blind pack because
their internal metadata can identify a generator. Preserve service facts, official
labels, source positions and meaningful source/version distinctions.

Use a fresh independent reviewer context per pair, with no candidate instructions
or access to other reviews/key. Grade consequential requirements, proportionality,
decisions, failure behavior, source scope, action boundaries and evidence honesty.
Report findings and A/B/tie preference; serious errors are not hidden by averages.
Assess nine shared QA dimensions and record the three new design dimensions
separately. Do not penalize an old skill for failing an instruction it did not have.

The versioned conclusion remains NOT_VERIFIED until 24 agent reviews and eight
human sample reviews, including critical findings, are locked. Review counts
alone cannot unblind results; actual review files and hashes are required.
Any conclusion is limited to this small workload sample. Metadata-only static
Plugin Eval findings and source/tool availability gaps are reported separately.

`--judge` starts a fresh profile and conversation per pair with no discoverable
skills, candidate content, prior review or version key. It saves review inference
usage separately. Failed judge attempts remain in `reviews/raw/` and stop the
loop; the runner does not silently replace them. Each valid review includes
mandatory checks, consequential findings, all twelve QA dimensions and a blind
preference. Human templates are deliberately incomplete. They cannot count as
reviews until the person supplies an actual assessment; any critical pair outside
the original eight becomes an additional required human check.

After locking, the report joins the private version key and reports per-task
repetitions, severe findings, acceptance, blind preferences and measured medians
and ranges. Architecture acceptance and timely delivery are separate. Unknown
usage prevents full token cost per accepted task; known failures still belong in
the denominator and measured cost. No currency estimate is manufactured.
Normalized `plugin-eval-before-usage.jsonl` and `plugin-eval-after-usage.jsonl`
contain only complete measured samples with cache counters. Plugin Eval static
budgets remain a separate signal and do not establish architectural quality.

Confirmed fixes follow the locked comparison, with reproduction and regression
evidence. Retain original runs, identify a corrected candidate by commit, and
repeat affected pairs three times. Privacy/terms links are added only if relevant
documents actually exist. No general diagram engine, OCI mutation or license
change belongs to this campaign.

## Current execution status

The offline check includes the inherited 17 regressions and the new measurement
tests. Native-profile pilots have demonstrated discovery, full-source skill reads,
measured usage and structurally valid file transfer for both revisions. A raw-log
reanalysis corrected an initial quoted-command read-detector miss without new
inference. No architecture-quality improvement is claimed from those pilots.
Primary and review status is recorded in the external campaign report.

The current campaign retains two limitations explicitly: application/operator
delays count toward the 20-minute wall deadline, and the rubric hash artifact was
materialized after primary execution began. The unchanged rubric definition was
reconstructed from the already committed controller and reasoning criteria; its
source commits and hash are recorded in external provenance. Post-deadline native
checks are forensic evidence and cannot reverse an original timeout.
