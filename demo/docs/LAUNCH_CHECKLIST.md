# Internal Launch Checklist (Safety)

This checklist defines the minimum safety bar for deploying a new model or major policy change.

## Pre-Release (Before Gate)

- [ ] Run full regression suite (misuse, red-team, trajectory, traffic replay)
- [ ] Verify no BLOCK verdicts
- [ ] Review WARN verdicts and document mitigations
- [ ] Validate thresholds and significance assumptions
- [ ] Update failure taxonomy if new failure modes observed

## Release Gate

- [ ] Safety regression suite exit code = OK or WARN
- [ ] Risk owner approval for WARN cases
- [ ] HTML regression report archived
- [ ] Metrics snapshot versioned

## Post-Release Monitoring

- [ ] Streaming evaluation enabled
- [ ] Drift alerts configured
- [ ] Delayed failure monitoring enabled
- [ ] Incident intake channel on-call assigned

## Incident Readiness

- [ ] Replay pipeline tested
- [ ] Root cause attribution rubric ready
- [ ] Regression test generator validated
- [ ] Blast radius scanner configured

## Accountability

| Role              | Responsibility                     |
|-------------------|------------------------------------|
| Safety Owner      | Final release sign-off              |
| Infra Owner       | CI/CD + eval pipeline reliability  |
| On-call Engineer  | Incident response                   |
| Research Lead     | Taxonomy + benchmark evolution      |

## Philosophy

This checklist enforces that:
- Safety is not a pre-release checklist item.
- Safety is a continuous production constraint with ownership.
