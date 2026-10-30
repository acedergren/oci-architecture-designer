# Recovery decisions

Use [Oracle MAA on OCI](https://docs.oracle.com/en-us/iaas/Content/Database/Concepts/maxavailarch.htm) and the [MAA source library](https://www.oracle.com/database/maximum-availability-architecture/) for Oracle database/application protection. Select release/platform-specific references. Do not freeze tier counts, feature entitlements or promised recovery numbers into the plugin.

Record RTO (tolerable recovery time), RPO (tolerable data loss), critical business transaction, and the failure the objective applies to. Distinguish process/node, AD, region, data corruption/operator error and planned maintenance. A target without failure scope is insufficient to select HA/DR. Capture what the customer has accepted, not a value inferred from a service badge.

Compare protection mechanisms against the failure and objectives: backup/restore, local redundancy, data replication and site/region recovery where appropriate. Include failure detection, failover authority, application/client reconnect, DNS/identity/keys/network dependencies, data validation and return to normal operation. A replicated bad change can require a backup-based recovery; a backup alone does not demonstrate a short outage or zero data loss objective.

For a proposed MAA configuration, establish supported database version/platform, data protection behavior, maintenance implications, licensing/support and client/application prerequisites from the applicable source. A tier designation is a design reference, not a demonstrated end-to-end RTO/RPO. Do not infer region-disaster survival from replicas in one failure domain.

If the requirement is region-loss recovery with no acceptable data loss but the allowed design has no independent recovery location/copy, flag the unresolved protection gap. Do not silently weaken the objective or add another region against an explicit constraint; ask its owner to choose a permitted recovery arrangement or revise the target.

Document what would validate the proposed objective: representative data size/write rate, recovery procedure, controlled failure, measured recovery/data loss and evidence of restored application transactions. Mark performance and recovery claims NOT_VERIFIED until the relevant check is executed. Preserve a useful proposal when live testing is outside scope.
