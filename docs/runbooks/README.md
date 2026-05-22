# Runbooks

Operational runbooks for the lab. Each file is self-contained and written for someone on-call at 3am — preconditions, diagnostic steps before mitigation, decision trees, verification, rollback, postmortem.

| Runbook | Severity | Typical duration |
|---------|----------|-----------------|
| [GitLab CE Outage Recovery](gitlab-outage-recovery.md) | P1 | 15–60 min |

Future runbooks (not yet written):

- Runner registration rotation
- DR restore validation (restic)
- Network change checklist (VLAN/DHCP)
- Workstation onboarding/offboarding
