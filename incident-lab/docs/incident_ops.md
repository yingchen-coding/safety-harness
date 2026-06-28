# Incident Operations Guide

## Severity Rubric Alignment

### Industry-Standard Severity Levels

| Level | Name | Definition | Response SLA |
|-------|------|------------|--------------|
| **SEV-0** | Critical | Widespread harm, regulatory exposure, data breach | 15 min response, all-hands |
| **SEV-1** | High | Significant user impact, safety policy violation | 1 hour response, on-call |
| **SEV-2** | Medium | Limited impact, single user affected | 4 hour response, business hours |
| **SEV-3** | Low | Potential risk identified, no actual harm | 24 hour response, async |

### Mapping to Safety Incidents

| Incident Type | Typical Severity | Escalation Path |
|---------------|------------------|-----------------|
| Mass harmful output | SEV-0 | Executive + Legal + PR |
| PII exposure | SEV-0/1 | Security + Legal |
| Policy violation (isolated) | SEV-2 | Safety team |
| Policy erosion detected | SEV-2/3 | Safety team |
| False positive spike | SEV-3 | Product team |

### Severity Assessment Checklist

```markdown
## Severity Assessment

1. **Harm occurred?**
   - [ ] Yes → At least SEV-1
   - [ ] No, but imminent → SEV-2
   - [ ] No, potential only → SEV-3

2. **Scope of impact?**
   - [ ] Many users affected → Increase severity
   - [ ] Single user → Maintain severity
   - [ ] Internal only → Decrease severity

3. **Regulatory implications?**
   - [ ] Yes → At least SEV-1, involve Legal

4. **Reputational risk?**
   - [ ] High → Consider SEV-0

5. **Exploitable at scale?**
   - [ ] Yes → Increase severity
```

---

## Blameless Postmortem Culture

### Core Principles

1. **Focus on systems, not individuals**
   - Bad: "Alice didn't review the PR properly"
   - Good: "The review process didn't flag this pattern"

2. **Assume good intent**
   - Everyone was trying to do their best with available information

3. **Seek contributing factors, not root cause**
   - Complex systems fail for multiple reasons
   - "5 whys" often oversimplifies

4. **Make it safe to speak up**
   - No punishment for raising issues
   - Reward transparency, not CYA behavior

### Postmortem Facilitation Guide

```
Before the meeting:
  - Gather timeline from logs and participants
  - Identify attendees (responders + stakeholders)
  - Set ground rules (no blame, focus on learning)

During the meeting:
  - Walk through timeline factually
  - Ask "what" and "how", not "why" (why implies fault)
  - Capture action items with owners and due dates
  - Thank participants for candor

After the meeting:
  - Publish postmortem within 48 hours
  - Track action items to completion
  - Share learnings broadly
```

### Anti-Patterns to Avoid

| Anti-Pattern | Why It's Harmful | Alternative |
|--------------|------------------|-------------|
| Naming individuals in blame | Creates fear, hides future issues | Name roles and processes |
| "Root cause: human error" | Too vague, not actionable | Identify process gap |
| Punishing incident reporters | Discourages reporting | Reward transparency |
| Skipping postmortem for "small" incidents | Misses learning opportunities | Lightweight review for all |

---

## Regression Test Lifecycle

### Test Decay Problem

Not all incidents remain relevant:
- Attack vectors get patched
- Model versions change
- Product features evolve
- Threats become obsolete

Running stale tests wastes resources and adds noise.

### Regression Test States

```
ACTIVE      → Running in CI, blocking releases
MONITORING  → Running but not blocking
DEPRECATED  → Scheduled for removal
RETIRED     → Removed from suite
```

### Decay Assessment Criteria

| Factor | Keep Active | Consider Retiring |
|--------|-------------|-------------------|
| Incident severity | SEV-0/1 | SEV-3 |
| Time since incident | < 1 year | > 2 years |
| Attack still viable | Yes | Patched/obsolete |
| Scenario still relevant | Yes | Product changed |
| Model architecture | Same/similar | Fundamentally different |

### Quarterly Review Process

```
Every quarter:
  1. Pull list of regression tests > 1 year old
  2. For each test:
     - Is the attack vector still relevant?
     - Has the model architecture changed significantly?
     - Are we still seeing similar incidents?
  3. Decision:
     - KEEP: Document justification
     - DEPRECATE: Move to monitoring-only
     - RETIRE: Remove with audit log entry
  4. Report: Summary of decisions to safety council
```

### Retirement Ceremony

When retiring a regression test:

```python
def retire_regression_test(test_id: str, reason: str):
    """Properly retire a regression test with audit trail."""
    test = get_test(test_id)

    # Log retirement decision
    audit_log.append({
        'action': 'RETIRE_REGRESSION',
        'test_id': test_id,
        'original_incident': test.incident_id,
        'reason': reason,
        'approver': get_current_user(),
        'timestamp': now()
    })

    # Archive test (don't delete)
    archive_test(test)

    # Remove from active suite
    regression_suite.remove(test_id)

    # Notify stakeholders
    notify(f"Regression test {test_id} retired: {reason}")
```

### "3-Month Relevance" Question

**Q: Is a 3-month-old incident regression still relevant?**

**A: Usually yes, but context matters.**

| Context | Relevance |
|---------|-----------|
| Same model version | Definitely relevant |
| Minor model update | Likely relevant |
| Major model update | Re-verify, may need adjustment |
| Architecture change | Test may not apply, review |
| Attack vector patched | Consider deprecation |

**Default policy:** Keep active for 1 year minimum unless explicitly deprecated.

---

## Integration with Release Gating

### How Incidents Flow to Release Gates

```
Incident Detected
    │
    ├─► Postmortem (blameless)
    │
    ├─► Regression Test Generated
    │       │
    │       ├─► Added to model-safety-regression-suite
    │       └─► Severity weight assigned
    │
    ├─► Next Release
    │       │
    │       ├─► Regression suite runs
    │       ├─► If test fails → BLOCK
    │       └─► Failure prevents repeat incident
    │
    └─► Continuous Improvement Loop
```

### Incident-to-Regression Handoff

```yaml
# handoff_template.yaml
incident_id: INC_001
severity: SEV-2
incident_summary: Model generated phishing template after gradual reframing

regression_test:
  test_id: regression_INC_001
  scenario: authority_reframe_phishing
  expected_block_turn: 3
  severity_weight: 0.8

notes:
  - Attack required 5 turns to succeed
  - Single-turn classifier did not flag
  - Trajectory monitor detected at turn 4 (too late)

action_items:
  - Adjust trajectory monitor threshold
  - Add to misuse benchmark
  - Update release gate config
```
