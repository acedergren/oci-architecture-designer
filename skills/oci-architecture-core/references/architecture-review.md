# Workload architecture review

Use the [OCI Well-Architected framework](https://docs.oracle.com/en/solutions/oci-best-practices/) as the organizing reference. The questions below are local review prompts to connect decisions to workload evidence. Select depth by risk and scope; avoid mechanically adding services to satisfy a checklist.

| Area | Questions that change a design |
| --- | --- |
| Security | What data crosses which trust boundaries? Who can read/change it? Identify identity, privilege, secrets, encryption, ingress/egress and audit dependencies; map required controls to a concrete threat or customer policy. |
| Resilience | For each material failure, what continues, what is lost and how is service restored? Include dependencies, maintenance, backup recovery, client reconnection and owner actions. Use [resilience notes](resilience.md) for recovery decisions. |
| Performance and cost | What is the peak demand and limiting dependency? Identify a measurable sizing assumption, a way to validate it, and the drivers of compute, data, transfer, standby, licensing and operating effort. Use current sources for prices; do not fabricate estimates. |
| Operations | Who deploys, patches, observes, rolls back and responds? Describe health signals, alert ownership, restore tests, configuration changes and capacity/limit checks appropriate to the workload. |
| Distributed cloud | Where must processing, data and operations reside? If hybrid, sovereign or multicloud scope is relevant, examine latency, identity, network dependency, support and recovery across boundaries; otherwise explain why that area is not applicable. |

Trace a critical request and a critical data change from origin to outcome. Annotate protocol, identity, endpoint/access mode and dependency where established. Walk relevant failure scenarios: process/node outage, unavailable dependency, certificate expiry, lost connectivity, storage exhaustion and data restoration. Choose those relevant to the workload rather than requiring every scenario for a layout edit.

Report by requirement/decision: finding, consequence, evidence, remediation, owner and validation still needed. Mark each applicable dimension PASS, FAIL or NOT_VERIFIED; NOT_APPLICABLE means irrelevant, not untested. PASS means the reviewed model/evidence satisfies the stated check; it does not mean deployed behavior or a recovery target has been measured. Unsupported critical recovery or access assumptions prevent an unconditional final-correctness claim but should not block a useful labeled draft.

Compare the simplest viable option with the proposed design. Look for components without a requirement, a cost/operations owner, or a source-supported purpose; identify missing dependencies with the same rigor. Keep confirmed defects separate from suggestions and unresolved requirements. A single overall numeric score must not hide a critical failure or missing evidence.
