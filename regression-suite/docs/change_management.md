# Change Management & Metric Lifecycle

## Threshold Change Process

### Who Can Change What

| Change Type | Approver | Review Required |
|-------------|----------|-----------------|
| Threshold relaxation | Safety Council | 2-person rule |
| Threshold tightening | Tech Lead | Single approval |
| New metric addition | Tech Lead | Single approval |
| Metric retirement | Safety Council | 2-person rule |
| Suite version bump | VP Engineering | Executive sign-off |

### Change Request Template

```markdown
## Threshold Change Request

**Metric:** violation_rate
**Current threshold:** warn=0.03, block=0.05
**Proposed threshold:** warn=0.04, block=0.06

### Justification
[Why this change is necessary]

### Evidence
- Historical false positive rate: X%
- Natural variance analysis: Y
- Impact simulation: Z

### Risk Assessment
- Risk of missed regression: [Low/Medium/High]
- Mitigation if regression occurs: [Plan]

### Approvals
- [ ] Tech Lead
- [ ] Safety Council Member 1
- [ ] Safety Council Member 2 (for relaxation)
```

### Change Audit Trail

All changes are logged:
```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "change_type": "THRESHOLD_RELAXATION",
    "metric": "violation_rate",
    "old_value": {"warn": 0.03, "block": 0.05},
    "new_value": {"warn": 0.04, "block": 0.06},
    "justification": "Historical data shows 3.5% natural variance",
    "approvers": ["alice@example.com", "bob@example.com"],
    "ticket": "SAFE-1234"
}
```

## Metric Retirement

### When a Metric Becomes Untrustworthy

| Signal | Indicates | Action |
|--------|-----------|--------|
| Gaming detected | Teams optimizing metric, not safety | Retire or redesign |
| Concept drift | Metric no longer measures intended property | Recalibrate or retire |
| Saturation | All models score same | Retire (not discriminative) |
| High noise | Variance > signal | Improve or retire |

### Retirement Process

```
1. Flag metric as UNDER_REVIEW
2. Collect evidence of untrustworthiness
3. Propose retirement to Safety Council
4. If approved:
   - Remove from blocking decisions
   - Keep in monitoring mode for 90 days
   - Archive after monitoring period
5. Document lessons learned
```

### Metrics We've Retired

| Metric | Retirement Date | Reason |
|--------|-----------------|--------|
| simple_jailbreak_rate | 2024-Q1 | All models saturated |
| raw_refusal_count | 2024-Q2 | Gaming via verbose refusals |

## Negative Results

### Change Management Failures

1. **Threshold changes without documentation**
   - Problem: Lost institutional knowledge
   - Learning: Mandatory commit messages with justification

2. **Emergency relaxations that became permanent**
   - Problem: Technical debt accumulation
   - Learning: Automatic review trigger for temp changes

3. **Metric additions without retirement plan**
   - Problem: Suite bloat
   - Learning: Sunset date required for new metrics
