# Release Governance & Override Policy

## Human Override Framework

### Who Can Override

| Decision | Override Authority | Approval Required |
|----------|-------------------|-------------------|
| OK → proceed | Automatic | None |
| WARN → proceed | Tech Lead | Single approval |
| WARN → block | Anyone | Self |
| BLOCK → proceed | Safety Council | 2-person rule |
| BLOCK → permanent | VP Engineering | Executive sign-off |

### Override Process

```
BLOCK Triggered
    │
    ├─► Auto-notify: Safety Council, Release Owner
    │
    ├─► 24-hour waiting period (unless emergency)
    │
    ├─► Override Request
    │       │
    │       ├─► Justification required (written)
    │       ├─► Risk acceptance statement
    │       └─► Mitigation plan
    │
    ├─► Review by 2 Safety Council members
    │       │
    │       ├─► APPROVE: Release proceeds with audit
    │       └─► REJECT: Release blocked, escalate to VP
    │
    └─► Audit Log Entry (immutable)
```

### Override Justification Template

```markdown
## Override Request: [Model Version]

**Requested by:** [Name]
**Date:** [Date]
**Block reason:** [Automated reason]

### Justification
[Why this block should be overridden]

### Risk Assessment
- Probability of harm if released: [Low/Medium/High]
- Severity if harm occurs: [Low/Medium/High/Critical]
- Affected user population: [Estimate]

### Mitigation Plan
1. [Mitigation step 1]
2. [Mitigation step 2]
3. [Monitoring plan]

### Acceptance Statement
I accept responsibility for this override decision and acknowledge
the documented risks.

Signature: _______________
```

---

## Regression Triage Playbook

### When BLOCK Occurs

```
T+0: BLOCK triggered
    │
    ├─► Immediate Actions
    │   ├─► Halt deployment pipeline
    │   ├─► Notify release owner
    │   └─► Page on-call if after hours
    │
T+1h: Triage Meeting
    │   ├─► Review regression metrics
    │   ├─► Identify root cause hypothesis
    │   └─► Decide: Fix forward or rollback?
    │
T+4h: Decision Point
    │   ├─► Option A: Fix and re-test
    │   ├─► Option B: Rollback to previous version
    │   └─► Option C: Override with mitigation
    │
T+24h: Resolution
        ├─► Document decision and rationale
        └─► Update regression suite if needed
```

### Triage Decision Matrix

| Regression Severity | Time to Fix | Recommendation |
|---------------------|-------------|----------------|
| Minor (WARN) | < 1 day | Fix forward |
| Minor (WARN) | > 1 day | Ship with monitoring |
| Major (BLOCK) | < 1 day | Fix forward |
| Major (BLOCK) | > 1 day | Rollback or override |
| Critical | Any | Rollback, no override |

### Fix vs Rollback Criteria

**Fix Forward When:**
- Root cause is understood
- Fix is low-risk
- Regression is localized
- Time pressure is manageable

**Rollback When:**
- Root cause unclear
- Fix is complex or risky
- Regression is widespread
- Customer impact is occurring

---

## Anti-Gaming Protections

### The Gaming Problem

Teams under pressure may:
- Tune prompts to pass specific tests
- Adjust thresholds to reduce blocks
- Exclude failing scenarios from suite
- Game aggregate metrics while degrading edge cases

### Detection Mechanisms

#### 1. Held-Out Test Set

20% of regression scenarios are never visible to model teams.
- Randomly selected
- Rotated quarterly
- Results not shared until release decision

#### 2. Metric Decomposition

Don't trust aggregates alone:
```python
def check_for_gaming(metrics: dict) -> list[str]:
    warnings = []

    # Check for suspiciously uniform improvement
    if all(m['delta'] < 0 for m in metrics.values()):
        warnings.append("All metrics improved - verify not overfitted")

    # Check for high variance across categories
    deltas = [m['delta'] for m in metrics.values()]
    if np.std(deltas) > 0.1:
        warnings.append("High variance across categories - inspect outliers")

    # Check for improvement only on known test scenarios
    if metrics['held_out']['delta'] > 0 and metrics['public']['delta'] < 0:
        warnings.append("ALERT: Held-out degraded while public improved")

    return warnings
```

#### 3. Temporal Consistency

Compare against multiple baselines:
```
Current release vs:
  - Previous release (standard)
  - 3 releases ago (trend check)
  - Best historical (ceiling check)
```

Suspicious pattern: Improvement vs previous but degradation vs best historical.

#### 4. Out-of-Distribution Probes

Periodically inject novel scenarios:
- Not in any training or test set
- Designed to test generalization
- Results compared to baseline behavior

### Governance Controls

| Control | Purpose | Implementation |
|---------|---------|----------------|
| Threshold changes require approval | Prevent relaxation gaming | Git-controlled, reviewed |
| Scenario changes audited | Prevent exclusion gaming | Immutable audit log |
| Random scenario injection | Detect overfitting | Automated, unpredictable |
| Cross-team review | Prevent collusion | Different team validates |

### What Happens When Gaming Is Detected

1. **Flag:** Mark release as suspicious
2. **Investigate:** Review model changes and test history
3. **Escalate:** Notify safety council
4. **Block:** If gaming confirmed, block release
5. **Remediate:** Require process changes before re-submission

---

## Audit Trail Requirements

### What Gets Logged

| Event | Data Captured | Retention |
|-------|---------------|-----------|
| Regression run | Full metrics, verdicts | 2 years |
| Override request | Justification, approvers | Permanent |
| Threshold change | Old/new values, approver | Permanent |
| Scenario modification | Diff, approver | Permanent |
| Release decision | Verdict, evidence | Permanent |

### Audit Log Schema

```python
@dataclass
class AuditEntry:
    timestamp: datetime
    event_type: str  # RUN, OVERRIDE, THRESHOLD_CHANGE, etc.
    actor: str  # User or system
    target: str  # Model version, threshold name, etc.
    action: str  # APPROVE, REJECT, MODIFY, etc.
    evidence: dict  # Supporting data
    signature: str  # Cryptographic signature

    def verify(self) -> bool:
        """Verify entry hasn't been tampered with."""
        return verify_signature(self.to_bytes(), self.signature)
```

### Compliance Requirements

- SOC 2 Type II: Audit logs are complete and tamper-evident
- GDPR: Personal data in logs is minimized
- Internal: Logs are queryable for incident investigation
