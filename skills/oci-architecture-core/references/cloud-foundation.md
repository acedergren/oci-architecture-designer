# Fit the existing cloud foundation

Use [OCI CAF](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/home.htm) to relate technical choices to ownership, working practices and business constraints. Compare [OCI Core Landing Zone](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/oci-core-landing-zone.htm) only when evaluating or extending a foundation. A workload can reuse an existing adequate landing zone without recreating its service inventory.

Inventory what is already available: identity/federation, IAM delegation and compartments, region/realm, address allocation, routing/connectivity, DNS, administration access, key/secrets management, audit/telemetry, delivery pipeline and cost allocation. Identify owners and evidence; do not infer deployed policy from a labeled diagram.

For each requirement, classify a capability as reusable, needs adaptation, missing, or not relevant. A dedicated VCN, hub/spoke topology, central firewall, Security Zone or extra region needs a demonstrated isolation, policy, scale, connectivity or recovery requirement. Assess alternatives and operational consequences. Do not treat a local checklist's absolute service recommendations as verified Oracle requirements.

Changes to shared networking must preserve established private DNS, administration and application paths, or document a reviewed replacement. Check connected address ranges before peering/routing changes. Compartments are ownership/policy scopes, not network boundaries. Keep workload responsibilities separate from platform responsibilities and record any proposed change's affected owners.

Data residency/sovereignty requirements must identify the relevant data, processing, operations and support boundaries. Verify the intended realm and service availability explicitly; an OCI region name or encryption symbol does not establish customer/regulatory acceptance. Do not alter a customer's governance design, IAM policy or infrastructure while performing a design-only review.
