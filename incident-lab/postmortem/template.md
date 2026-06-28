# Incident Postmortem Template

> Standard template for safety incident postmortems.
> Complete all sections within 48 hours of incident resolution.

---

## Incident Identification

| Field | Value |
|-------|-------|
| **Incident ID** | INC_XXX |
| **Date Detected** | YYYY-MM-DD HH:MM UTC |
| **Date Resolved** | YYYY-MM-DD HH:MM UTC |
| **Severity** | SEV0 / SEV1 / SEV2 / SEV3 |
| **Incident Commander** | [Name] |
| **Author** | [Name] |
| **Review Date** | YYYY-MM-DD |

---

## Executive Summary

*2-3 sentences describing what happened, impact, and resolution.*

> Example: On [date], [model/system] produced [harmful output type] in response to
> [attack pattern]. This affected [N users/conversations]. The incident was resolved
> by [action taken] within [duration].

---

## Impact Assessment

### User Impact

| Metric | Value |
|--------|-------|
| Affected users | N |
| Affected conversations | N |
| User reports received | N |
| Estimated harm severity | Low / Medium / High / Critical |

### System Impact

| Metric | Value |
|--------|-------|
| SLO breach | Yes / No |
| Availability impact | None / Degraded / Outage |
| Performance impact | None / Degraded |
| Data integrity impact | None / Affected |

### Business Impact

| Area | Impact |
|------|--------|
| Revenue | None / Estimated $X |
| Reputation | None / Social mentions / Press coverage |
| Regulatory | None / Disclosure required / Fine possible |
| Legal | None / Review needed / Action required |

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | First harmful output generated |
| HH:MM | First user report received |
| HH:MM | Incident detected by [monitoring/user report] |
| HH:MM | Incident commander engaged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation deployed |
| HH:MM | Incident resolved |
| HH:MM | All-clear communicated |

---

## Root Cause Analysis

### Primary Root Cause

*Single sentence identifying the fundamental cause.*

> Example: Single-turn intent classification failed to detect capability accumulation
> across a coordinated multi-turn attack.

### Contributing Factors

1. **Factor 1**: [Description]
   - Why this mattered: [Explanation]

2. **Factor 2**: [Description]
   - Why this mattered: [Explanation]

3. **Factor 3**: [Description]
   - Why this mattered: [Explanation]

### Root Cause Category

Select one:
- [ ] Injection attack
- [ ] Policy erosion
- [ ] Tool hallucination
- [ ] Coordinated misuse
- [ ] Escalation delay
- [ ] Safeguard gap
- [ ] Configuration error
- [ ] Other: ___________

---

## Detection Analysis

### How was the incident detected?

- [ ] Automated monitoring
- [ ] User report
- [ ] Internal testing
- [ ] External report
- [ ] Other: ___________

### Why wasn't it detected earlier?

*Explain gaps in detection that allowed the incident to occur.*

### Detection latency

| Metric | Value |
|--------|-------|
| Time from first occurrence to detection | X minutes/hours |
| Time from detection to response | X minutes |

---

## Response Analysis

### What went well?

1. [Positive aspect of response]
2. [Positive aspect of response]

### What could have gone better?

1. [Area for improvement]
2. [Area for improvement]

### Response effectiveness

| Metric | Value |
|--------|-------|
| Time to mitigate | X minutes/hours |
| Time to resolve | X minutes/hours |
| Rollback required | Yes / No |

---

## Mitigation and Resolution

### Immediate mitigation

*What was done to stop the bleeding?*

### Permanent fix

*What was done to prevent recurrence?*

### Verification

*How was the fix verified?*

---

## Action Items

### Immediate (within 24 hours)

| ID | Action | Owner | Status |
|----|--------|-------|--------|
| 1 | [Action] | [Name] | Done / In progress / Not started |

### Short-term (within 1 week)

| ID | Action | Owner | Due Date | Status |
|----|--------|-------|----------|--------|
| 1 | [Action] | [Name] | YYYY-MM-DD | |

### Long-term (within 1 quarter)

| ID | Action | Owner | Due Date | Status |
|----|--------|-------|----------|--------|
| 1 | [Action] | [Name] | YYYY-MM-DD | |

---

## Regression Tests

### Tests promoted from this incident

| Test ID | Description | Type | Target |
|---------|-------------|------|--------|
| REG_INC_XXX_001 | [Description] | Unit / E2E | [Component] |
| REG_INC_XXX_002 | [Description] | Unit / E2E | [Component] |

### Existing tests that should have caught this

| Test ID | Why it missed | Fix needed |
|---------|---------------|------------|
| [ID] | [Reason] | [Fix] |

---

## Lessons Learned

### What did we learn about our system?

1. [Lesson]
2. [Lesson]

### What did we learn about the threat landscape?

1. [Lesson]
2. [Lesson]

### Process improvements identified

1. [Improvement]
2. [Improvement]

---

## Appendix

### Related Incidents

| Incident ID | Relationship |
|-------------|--------------|
| INC_YYY | Similar root cause |
| INC_ZZZ | Same attack pattern |

### References

- [Link to logs]
- [Link to monitoring dashboard]
- [Link to related documentation]

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Incident Commander | | | |
| Engineering Lead | | | |
| Safety Team Lead | | | |
| Management | | | |

---

*Template version: 1.0*
*Last updated: 2026-02*
