# Requirements to decisions

Use this when creating a design, comparing options or changing material architecture. For a layout-only edit, preserve the established model and decisions; do not reopen discovery or redesign the solution.

## Build a compact workload brief

Use supplied requirements and inspect available IaC, source diagrams and platform standards before asking questions. Record only fields that affect this assignment:

| Field | Capture |
| --- | --- |
| Outcome and boundary | Business task, users, integrations, current/proposed scope and success checks |
| Demand | Normal/peak load, growth, latency/throughput objectives and measurement source |
| Data | Sensitivity, ownership, retention, residency and deletion requirements |
| Recovery | Tolerable outage and data loss, affected failures, maintenance windows and restore dependencies |
| Existing platform | Region/realm, tenancy foundation, network/DNS/identity, data services, delivery pipeline and operations |
| Constraints | Budget range, skills, support/licensing, delivery deadline and explicit exclusions |
| Ownership | Who operates each component, pays for it and accepts remaining risks |

Give requirements stable IDs when several decisions depend on them. Distinguish a supplied requirement, verified current fact, assumption and unresolved decision. Ask about a missing fact when it changes the recommendation; otherwise state a bounded assumption and proceed with a reviewable proposal. Do not invent load, budget, residency or availability objectives.

## Choose proportionately

Read only the relevant reference: [workload patterns](workload-patterns.md), [cloud foundation](cloud-foundation.md), [resilience](resilience.md) or [service verification](service-verification.md). The [source index](architecture-sources.md) records provenance and limitations. Use existing capabilities when they satisfy the workload and ownership constraints. Each additional service, replica or region needs a requirement and an operator. Technical capability alone is not a reason to add it.

For significant choices compare the smallest viable approach with realistic alternatives. Consider failure behavior, security boundaries, total operating cost, skills, dependency/support burden, portability and reversibility. Do not force multiple alternatives for a trivial or already-mandated decision. If requirements conflict, identify the conflict and the smallest decision needed from its owner; never resolve it by quietly weakening a requirement.

Maintain a compact decision record, adapting [Michael Nygard's ADR approach](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

| Item | Content |
| --- | --- |
| Decision ID and status | Proposed, accepted by a named owner, or superseded; authoring a proposal is not acceptance |
| Context | Requirement IDs, constraints and verified facts that drove the choice |
| Options and decision | Feasible options, selected approach and reason; distinguish recommendation from a mandated choice |
| Consequences | Tradeoffs, operating/cost responsibility, residual risks and reversal trigger |
| Evidence and validation | Specific source/section, version/access date, scope, confidence and checks still required |

Keep accepted history when superseding a decision. A source can establish a product capability; applying that capability to this workload is a design inference and needs its own reasoning.

## Select useful views

Use [Simon Brown's C4 model](https://c4model.com/) to separate the audience's questions. A context view describes people, system boundary and external systems; a container view describes major applications and data stores. A C4 container is an application/data boundary, not necessarily a Docker container or Kubernetes workload. Add a deployment view for OCI regions, compute, networks and endpoints; a dynamic view can explain a critical interaction. Component/code views are optional and useful only when the task needs them. These are notation-independent viewpoints, not additional OCI resources.

Keep stable model IDs and decision references across logical and physical views. Do not mix a conceptual relationship with a claimed network route. Draw the selected proposed/accepted model; show alternatives separately so a viewer cannot mistake them for deployed components.

## Handoff

Provide the workload brief, material decisions, selected model/views and [architecture review](architecture-review.md), proportionate to the request. A small drawing may need only a few sentences and one decision row. A design review without a supplied diagram can deliver a useful model and findings without inventing a file. Review-only work reports recommendations without silently changing accepted architecture.
