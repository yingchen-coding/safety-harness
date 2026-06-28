# Post-Mortem Methodology for Safety Incidents

## Overview

This document describes the structured approach for analyzing safety incidents in agentic AI systems—from initial detection through prevention of recurrence.

## The 7-Step Framework

### 1. Contain: Stop Ongoing Harm

**Immediate actions:**
- Pause affected model/agent deployments
- Revoke compromised access tokens
- Isolate affected systems

**Questions to answer:**
- Is the incident still ongoing?
- What is the current blast radius?
- Who has been notified?

### 2. Reproduce: Replay the Incident

**Using the replay tool:**
```bash
python replay.py --incident incidents/INC_XXX.json
```

**Goals:**
- Confirm the failure can be reproduced
- Identify the exact turn where failure occurred
- Document the full conversation trajectory

**Artifacts:**
- Replay log with turn-by-turn status
- Screenshot or recording of failure
- Environment configuration at time of incident

### 3. Analyze: Identify Root Causes

**Using the root cause analyzer:**
```bash
python root_cause.py --incident incidents/INC_XXX.json
```

**Categories of root causes:**
- **Safeguard gaps**: Missing or insufficient safeguards
- **Policy gaps**: Policy doesn't cover this scenario
- **Design flaws**: Fundamental architecture issues
- **Edge cases**: Rare combinations not anticipated

**Output:**
- Structured list of contributing factors
- Severity rating for each factor
- Candidate mitigations

### 4. Scope: Estimate Blast Radius

**Using the blast radius estimator:**
```bash
python blast_radius.py --incident incidents/INC_XXX.json
```

**Questions to answer:**
- How many scenarios share this vulnerability?
- Which evaluation suites are affected?
- Is this localized or systemic?

**Risk levels:**
- **Localized**: < 15% of scenarios affected
- **Moderate**: 15-25% of scenarios affected
- **Systemic**: > 25% of scenarios affected

### 5. Mitigate: Implement Fixes

**Short-term mitigations:**
- Tighten thresholds
- Add blocklist patterns
- Disable high-risk tools

**Long-term mitigations:**
- Architecture changes
- New safeguard implementations
- Policy updates

**Validation:**
- Confirm fix prevents reproduction
- Run regression suite
- Monitor for side effects

### 6. Prevent: Generate Regression Tests

**Using the regression generator:**
```bash
python generate_regression.py --incident incidents/INC_XXX.json
```

**Test requirements:**
- Must reproduce original failure pattern
- Must pass after fix is applied
- Must be included in release gating

**Integration:**
- Add to `model-safety-regression-suite`
- Include in CI/CD pipeline
- Document expected behavior

### 7. Review: Document Lessons Learned

**Post-mortem document should include:**
- Incident summary
- Timeline
- Root cause analysis
- Blast radius assessment
- Mitigations applied
- Lessons learned
- Action items

**Distribution:**
- Safety team
- Relevant engineering teams
- Leadership (for critical incidents)

## Severity Classification

| Severity | Definition | Response Time |
|----------|------------|---------------|
| **Critical** | Data exposure, policy bypass, potential for real-world harm | Immediate |
| **High** | Significant policy violation, no data exposure | < 24 hours |
| **Medium** | Minor policy violations, edge cases | < 1 week |
| **Low** | Theoretical vulnerabilities, minimal risk | Next sprint |

## Incident Report Template

```markdown
# Incident Report: INC_XXX

## Summary
[One paragraph summary of what happened]

## Timeline
- HH:MM - Incident detected
- HH:MM - Containment actions taken
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Incident resolved

## Impact
- Users affected: N
- Data exposed: Yes/No
- Duration: X hours

## Root Cause
[Structured root cause analysis]

## Mitigations
- Short-term: [list]
- Long-term: [list]

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]

## Action Items
- [ ] Action 1 (Owner, Due date)
- [ ] Action 2 (Owner, Due date)
```

## Integration with Evaluation Pipeline

```
Incident Detected
       │
       ▼
┌──────────────┐
│   Contain    │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────────────┐
│  Reproduce   │─────▶│ agentic-safeguards-  │
└──────┬───────┘      │ simulator            │
       │              └──────────────────────┘
       ▼
┌──────────────┐      ┌──────────────────────┐
│   Analyze    │─────▶│ Structured root      │
└──────┬───────┘      │ cause database       │
       │              └──────────────────────┘
       ▼
┌──────────────┐      ┌──────────────────────┐
│    Scope     │─────▶│ misuse-benchmark     │
└──────┬───────┘      │ stress-tests         │
       │              └──────────────────────┘
       ▼
┌──────────────┐
│   Mitigate   │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────────────┐
│   Prevent    │─────▶│ regression-suite     │
└──────┬───────┘      │ release gating       │
       │              └──────────────────────┘
       ▼
┌──────────────┐
│   Review     │
└──────────────┘
```

## Why This Matters

Pre-deployment evaluation prevents known failure modes.
Post-incident analysis prevents **unknown** failure modes from recurring.

Every incident is an opportunity to:
1. Improve safeguards
2. Expand evaluation coverage
3. Strengthen release gating

The goal is not zero incidents—it's **continuous improvement** in safety coverage.
