# OCI topology checks

Use these invariants for design and QA. Verify service-specific details against current official docs for the intended region/realm and access mode. Sources were inspected 2026-10-16; a pinned icon toolkit is older than current product documentation.

## Scope is multidimensional

- A region contains one or more ADs; verify its actual count. Each AD contains fault domains. Do not duplicate three ADs from a template into a single-AD region. Fault domains reduce failures within an AD; they do not demonstrate resilience to a region failure.
- A VCN is regional. Subnets belong to a VCN and can be regional or AD-specific; regional subnets are recommended. Do not force a regional subnet below one AD/FD. Use overlays or a separate network and placement view when geographic and network boundaries intersect.
- Compartments express resource ownership and IAM scope, not traffic isolation or geographic placement. A compartment is not a subnet or firewall. Keep IAM/cross-region services distinct from regional and AD-specific resources.
- Managed services are not automatically inside a customer subnet. A private endpoint/VNIC may be in that subnet while the service is regional outside the VCN. Show the endpoint and access path separately; verify each service's actual endpoint model.

## Traffic paths

- Internet Gateway: direct public internet connectivity for appropriately addressed endpoints, routes, and security rules. A public subnet alone does not establish reachability. A private subnet cannot assign public IPv4 addresses; account for IPv6 separately when in scope.
- NAT Gateway: outbound connections from private resources plus their replies, not unsolicited inbound internet connectivity. Do not draw incoming client traffic through a NAT gateway as an ingress route.
- Service Gateway: private access to supported regional Oracle Services Network destinations, not a universal route to all SaaS, all Oracle APIs, arbitrary regions, or the internet.
- DRG: regional private-routing hub with VCN, VPN, FastConnect, and remote-peering attachment models as appropriate. Show routing/attachment intent; do not draw a DRG as a compute server inside a subnet. Same-region VCN connectivity can use upgraded DRG routing or LPG peering; the toolkit's older LPG-only example is not an exclusive product rule.
- LPG: local VCN peering in the same region with a paired LPG per relationship. Remote peering connects DRGs across regions. Validate non-overlapping connected CIDRs, routing, and explicit transit arrangements; neither peering nor a hub drawing implies all transitive traffic is enabled.
- Site-to-Site VPN: distinguish CPE, IPSec connection/tunnels, and DRG. FastConnect: show the relevant private connectivity path/virtual circuit, not a generic public internet arrow or guaranteed end-to-end encryption. Verify the chosen model's redundancy and encryption.
- NSGs apply security rules to supported resource VNICs; security lists attach at subnet scope. Neither replaces routing or IAM. Distinguish network access from application authorization; avoid drawing a security rule object as an inline appliance.
- Public/private load balancer, API Gateway, WAF, Bastion, database and OKE endpoints must use verified modes. Distinguish an OKE regional control plane from worker node/subnet/AD placement. Do not infer a supported private endpoint or HA mode from a similarly named icon.

## Availability and deployment claims

Show the actual replica count, load balancing, failure scope, data replication, failover direction, and dependencies that justify an HA/DR statement. A second icon without an established behavior is not an HA solution. A diagram does not establish a measured RTO/RPO, deployed IAM rules, capacity, supportability, compliance, or customer readiness. Treat unconfirmed facts as assumptions.

## Primary references

- [Regions, ADs, FDs, and resource scope](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm)
- [Networking components and subnet semantics](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm)
- [NAT Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/NATgateway.htm)
- Follow the Networking Overview's current links for DRG, LPG, service gateways, routes, and security rules. Verify the relevant service documentation for endpoint and lifecycle claims rather than extrapolating from icons.
