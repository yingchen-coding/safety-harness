# Red-Team Stopping Criteria & Learning Curves

## When Is Stress Testing "Enough"?

### Stopping Criteria Framework

| Criterion | Definition | Threshold |
|-----------|------------|-----------|
| **Coverage saturation** | New attacks don't find new failures | <5% new failures in last 100 attacks |
| **Budget exhaustion** | Resource limit reached | Configurable |
| **Time box** | Maximum testing duration | Configurable |
| **Confidence threshold** | Statistical confidence in failure rate | 95% CI width < 0.05 |

### Decision Tree

```
Start stress testing
    │
    ├─► Run N attacks (N=100 minimum)
    │
    ├─► Compute metrics
    │       ├─► Failure rate
    │       ├─► New failure discovery rate
    │       └─► Confidence interval
    │
    ├─► Check stopping criteria
    │       │
    │       ├─► Coverage saturated? → STOP
    │       ├─► Budget exhausted? → STOP
    │       ├─► Time box exceeded? → STOP
    │       ├─► Confidence sufficient? → STOP
    │       └─► Otherwise → Continue
    │
    └─► Report results
```

## Attacker Learning Curve

### Visualization: Attack Success Over Turns

```
Success Rate
    │
100%├────────────────────────────────────────
    │                              ████████
 80%├                         █████
    │                    █████
 60%├               █████
    │          █████
 40%├     █████
    │ ████
 20%├██
    │
  0%├────┬────┬────┬────┬────┬────┬────┬────
    Turn 1   2    3    4    5    6    7    8
```

### Key Observations

1. **Early turns:** Low success, safeguards effective
2. **Mid turns (3-5):** Rapid success increase, policy erosion
3. **Late turns (6+):** Saturation, most safeguards bypassed

### Implications for Defense

- Pre-turn-3 intervention is critical
- Post-turn-5 safeguards have limited value
- Trajectory truncation may be cost-effective defense

## Negative Results

### Attack Strategies That Didn't Work

1. **Rapid escalation (1-2 turns)**
   - Hypothesis: Quick attacks bypass detection
   - Result: Models catch direct attacks well
   - Learning: Gradual decomposition is necessary

2. **Very long trajectories (15+ turns)**
   - Hypothesis: More turns = higher success
   - Result: Diminishing returns after turn 8
   - Learning: Optimal attack length is 5-8 turns

3. **Random mutation without strategy**
   - Hypothesis: Diversity alone is sufficient
   - Result: Worse than strategic mutation
   - Learning: Directed mutation outperforms random

### Metrics We Abandoned

| Metric | Problem | Replacement |
|--------|---------|-------------|
| Attack success rate (binary) | Ignores partial success | Graduated harm score |
| First failure turn | Ignores severity | Weighted failure index |
| Template diversity | Doesn't predict success | Semantic coverage |
