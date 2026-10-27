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

After a controller interruption, `run` preserves the existing attempt and any
completed answer without another inference call. Missing timing remains unknown.
An interrupted setup with no inference is not counted as a completed workflow;
it requires explicit recovery. Setup time is deducted from the initial inference
budget, and an answer finishing after the wall deadline cannot be accepted as a
timely delivery.

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
effective execution context, file evidence and elapsed time. Raw private profile
session JSONL is also copied into content-addressed snapshots with a hash manifest;
follow-up snapshots retain prior bytes. Authentication/configuration files and
symlinks are excluded. These private execution logs stay outside Git and blind
review packs. Missing or malformed session evidence remains NOT_VERIFIED, and a
changed archived checksum stops archival without replacing the old evidence.
CLI terminal usage
is retained, but follow-up billing is calculated from the difference between
persisted per-thread `total_token_usage` counters. Counter resets or absent
values are unknown, not zero. Cached input is separate from total input; it is
not added a second time. Only verified complete samples can support resource
comparisons. Failed workflows retain their observed resource consumption.
`observed_usage` retains known phase counters as a possible lower bound even when
workflow completeness is unknown; `usage` and exact cost remain null in that case.

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
The initial artifact is frozen before the edit inference. Later overwrites are
reported without replacing that snapshot. Native files are hashed before and
after final QA; a reporting turn that changes them fails artifact integrity.

Use Draw.io in Chrome and the existing PowerPoint installation. Do not install a
renderer to improve a result. Move a Compute node within its subnet in a test
copy, save a local file, close/reopen that file and inspect attached connectors.
Record the unchanged reference view and cross-format resources/flows separately.
A parser pass cannot promote any application or visual dimension to PASS.

When a native view suggests a rendering failure, independently reopen the same
original file bytes before classifying it. Preserve the first suspect frame
outside the blind render selection and record any transient discrepancy. Numeric
serialization changes such as `512.0` to `512` do not establish changed geometry.
PowerPoint may add organizational classification banners when saving a test copy;
leave that policy untouched, compare the initial/edited originals first, and
record host-added markings separately from candidate changes.

## Blind assessment and release boundary

After all 48 workflows complete, `review-pack` creates 24 A/B pairs and one human
sample per scenario. The private version key is stored outside review packs.
Reviewers receive original requests, anonymized answers, normalized structural
evidence and checked renders. Native packages stay outside the blind pack because
their internal metadata can identify a generator. Preserve service facts, official
labels, source positions and meaningful source/version distinctions.

The pack includes saved worker QA reports and source registers, plus independent
catalog/read observations. Primary text, JSON and SVG design outputs are retained
even when the final message mainly links to attachments. SVG source is content
evidence and does not establish native opening or verified rendering. It excludes copies matching candidate instruction
files. The pack also extracts actual line-numbered web results from checksum-verified
private session snapshots, deduplicated across appended snapshots. These captures
retain retrieval time and content hashes while excluding other tool output. They
represent the cached or partial text the worker received, not a new fetch, full
HTML mirror or automatic confirmation of a service claim. Missing captures remain
NOT_VERIFIED; a worker source register alone is not independent source verification.
Source facts and access dates remain visible; execution metrics in QA JSON
are hidden. Operator checks do not prove that the candidate performed or knew
those checks when making an earlier claim. Useful skill application is judged
from the decisions and artifact, separately from observed reading.

Use a fresh independent reviewer context per pair, with no candidate instructions
or access to other reviews/key. Grade consequential requirements, proportionality,
decisions, failure behavior, source scope, action boundaries and evidence honesty.
Report findings and A/B/tie preference; serious errors are not hidden by averages.
Assess nine shared QA dimensions and record the three new design dimensions
separately. Do not penalize an old skill for failing an instruction it did not have.

The versioned conclusion remains NOT_VERIFIED until 24 agent reviews and eight
human sample reviews, including critical findings, are locked. Review counts
alone cannot unblind results; actual review files and hashes are required.
The pack also freezes result records, the version key, review index and the human
sample before grading. Changed conclusion inputs invalidate the lock. The human
sample must cover each of the eight scenarios. Human failed requirements and
Critical findings affect acceptance; their findings are included in severe totals
with reviewer provenance, alongside the agent assessment.
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
Plugin Eval 0.1.2 substitutes zero for missing cache/reasoning details. The adapter
excludes unknown-cache samples; its metadata explicitly marks reasoning tokens
unmeasured. A reasoning zero in Plugin Eval is therefore not an observed zero.
Workflow usage aggregates all actual model calls and phases, while static budgets
estimate instruction text; their difference does not isolate plugin overhead.
These token counters cover the isolated working session's initial, edit and QA
turns. Technical pilots, independent reviewers and controller/operator work are
separate. Controller model tokens and active application-operator time have not
been allocated to primary runs and remain null/NOT_VERIFIED. Consequently the
worker-token cost per accepted task is not a measured total cost for the complete
human/controller/application workflow. Wall time includes operator delays;
generation time is reported separately. No end-to-end resource-efficiency claim
is supported while those measurements remain missing.

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

The earlier campaign retained two limitations explicitly: application/operator
delays count toward the 20-minute wall deadline, and the rubric hash artifact was
materialized after primary execution began. The unchanged rubric definition was
reconstructed from the already committed controller and reasoning criteria; its
source commits and hash are recorded in external provenance. Post-deadline native
checks are forensic evidence and cannot reverse an original timeout.

One primary workflow exposed a gap between wall time and the process monotonic
timer. Its cause was not established, and its TIMEOUT result is retained. New
controller processes check both clocks at least once per second and stop at the
earlier deadline. Phase records retain the original monotonic elapsed field and
add wall elapsed time and the deadline method. A host suspension cannot be
interrupted while the host is asleep; an expired process is stopped on resume.
Controller hashes identify which method each run actually used.

Blind packs include native screenshots from both application and independent
operator evidence, with an index connecting each original source position to its
anonymous review filename and byte hash. A screenshot documents rendering at the
observed time; independent checks do not prove an earlier worker claim.

CI fetches repository history because runtime-export regressions exercise the
pinned candidate commits. A default shallow checkout does not contain those
revisions. Local checks do not establish that a hosted CI run has passed.

Isolation protocol 2 denies the ordinary user home and shared `/tmp` and
`/private/tmp` directories, while permitting the trial's own files and bundled
dependency runtime. Before each model call sequence, native guard probes must
deny reading, listing and writing a synthetic other-candidate directory in shared
temporary storage, as well as the repository and controller checks. Legacy pilot
gates cannot authorize this protocol, and results without its proof cannot
produce a verified campaign conclusion.

An earlier campaign was stopped after an agent's shared-temporary-directory
inventory exposed filenames for another candidate and previous diagram files.
The original raw attempts and their resource consumption remain infrastructure
evidence. They are not mixed into a replacement primary comparison. A new output
directory and fresh technical pilots are required before restarting the fixed
48-run campaign. This isolation failure is a measurement defect, not evidence of
an architecture-quality difference between the candidates.
Known worker-token consumption for these failed technical attempts and pilots is
listed separately in the replacement report, including incomplete lower bounds.
This resource use is not erased when primary denominators restart. Unknown
interrupted/controller/operator costs still prevent a complete total-cost claim.

CLI version and executable hash are recorded per trial. For a long campaign, use
`--codex` with an unchanged external copy of the existing vendor CLI bundle, and
record its source/copy hashes. This prevents a desktop app update from silently
changing the measurement engine. The copy belongs outside the plugin and Git;
ordinary installation and settings remain untouched. Only that executable bundle
is allowed through the home-directory denial; other result files remain denied.
Copy the complete vendor `codex-cli` directory, including its sibling `bin/`
helpers and resources; copying only `CodexCLI.app` is insufficient. Preflight
requires the code-mode host and binds both executable and helper hashes to the
pilot gate. Main execution rejects another engine, and a missing code-mode host
stops the campaign as an infrastructure failure even when the model returns a
normal final answer. A copied runtime must pass its own functional pilots.

### Recorded execution milestone — 27 October 2026

The replacement campaign using the complete frozen vendor CLI has recorded all
48 primary workflows after two functional protocol-2 pilots. All 48 runs have
matching model/effort observations. Execution status is 36 PASS and 12 TIMEOUT;
these are process/workflow outcomes, not architecture acceptance grades.

Independent computer-use checks cover both original and edited deliveries:

| Native check | PASS | FAIL | NOT_VERIFIED |
| --- | ---: | ---: | ---: |
| Original file opening/rendering | 12 | 0 | 0 |
| Original move/save/close/reopen | 11 | 1 | 0 |
| Edited file opening/rendering | 8 | 1 | 3 |
| Edited move/save/close/reopen | 7 | 1 | 4 |

All twelve Draw.io move tests passed. PowerPoint movement passed for five
originals and one edited delivery; one original and its edited counterpart failed
actual connector endpoint translation despite retaining shape references. A
corrupt edited PowerPoint file was rejected by the application, and three edited
presentations were absent. The twenty native-saved test copies all pass their
pinned format validators, illustrating why parser success cannot establish
interactive editability. Visual collisions remain recorded independently.

These operator checks occurred after the workflow deadlines. They do not replace
or promote the twelve original TIMEOUT outcomes. Host UI interruptions, operator
waiting and worker generation are recorded separately. No human diagram
corrections were applied to the frozen deliverables.

Fifty private contexts (48 main runs and two pilots) have checksum-verified raw
session archives outside Git, with no remaining temporary authentication copies.
The blind pack has 24 pairs, 785 text files and 103 native screenshots. A text
audit found no candidate-version, pinned-commit or local-path leaks. The frozen
review index hash is
48ee4d703f3ad0eab8f058f4a36933e4c34c057de9ca3e600b28d61407390325.

The independent review sequence is running, and the eight actual human sample
reviews remain pending. The generated report still says NOT_VERIFIED and refuses
unblinding. No quality winner, complete resource-efficiency result or corrected
candidate is claimed. Original attempts and earlier infrastructure failures
remain separate evidence.

Measurement support at commit 00d5116 passes 88 tests and package checks. It
retains primary design attachments and actual retrieved source fragments while
excluding mixed/truncated tool wrappers and local paths from blind inputs.
No installation, push or publication was performed.
