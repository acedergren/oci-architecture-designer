# Verify service claims for this design

Read current primary documentation for the exact service, release, region/realm, endpoint mode and configuration before making a decision that depends on it. Start from [regions and availability domains](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm) and [service limits](https://docs.oracle.com/en-us/iaas/Content/General/service-limits/overview.htm), then open the applicable service page. An old architecture example or icon catalog is not current product evidence.

For material claims, record the property, value or uncertainty, source/section and access date, target scope, and what remains to verify. Separate source-documented capability, actual customer configuration, design inference and measured behavior. Framework/index pages identify where to look; they do not establish specific endpoint support or tenancy values.

Recheck volatile facts during the task: realm/region availability, private access/endpoint support, HA/failover mode, limits/quotas, shape/capacity assumptions, lifecycle/version support, pricing and entitlement. Do not convert a generic commercial-region capability into sovereign-realm availability. A documented service limit does not establish effective customer quota, headroom or current provisioning capacity.

Use authorized read-only configuration evidence when available. Never request or expose credentials to complete a diagram; absent access is a verification gap, not evidence that a capability is unsupported. Keep customer-specific identifiers/configuration outside the distributed plugin.

When current evidence is inaccessible or ambiguous, label the claim NOT_VERIFIED, explain the consequence for the proposed design and assign a validation owner. Ask a focused question only if the missing property changes the choice. Preserve a bounded proposal rather than inventing product support or marking an untested claim as passed.
