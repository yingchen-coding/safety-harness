# Design Document: Model Safety Regression Suite

## Overview

This document describes the design philosophy and architecture of the Model Safety Regression Suite—a unified tool for detecting safety degradations across model versions as part of release gating.

## Why Safety Regression Matters

### The Problem

Safety can quietly degrade as models gain capability:

1. **Capability-safety tradeoff**: More capable models may be more susceptible to manipulation
2. **Training distribution shift**: New training data can erode safety behaviors
3. **Emergent vulnerabilities**: New capabilities may enable novel attack vectors

### Why Absolute Metrics Aren't Enough

A model might:
- Pass all absolute safety thresholds (e.g., < 10% violation rate)
- While representing a **regression** from the previous version (e.g., 8% → 10%)

Regressions are the critical signal for release gating because they indicate:
- Something changed in the wrong direction
- The change may compound over future versions
- Early intervention is easier than later correction

## Release Gating Philosophy

### Conservative Defaults

```
Better to block a safe release than to ship a regression.
```

We bias toward false positives (blocking releases that are actually fine) over false negatives (shipping regressions).

**Rationale**:
- Blocked releases can be reviewed and approved
- Shipped regressions are hard to recall
- Safety reputation is hard to rebuild

### Regression Over Absolute

We focus on **change** rather than **level**:

| Metric | v1 | v2 | Absolute Status | Regression Status |
|--------|----|----|-----------------|-------------------|
| violation_rate | 8% | 10% | ✓ Pass (< 15%) | ❌ Regression (+2%) |

Both signals matter, but regression is the gating signal.

### Human-in-the-Loop for BLOCK

Automated systems make recommendations, humans make decisions:

- **OK**: Auto-approve
- **WARN**: Flag for review, can proceed
- **BLOCK**: Requires human override to proceed

## Architecture

### Adapter Pattern

Each evaluation suite has an adapter that:
1. Runs the evaluation
2. Extracts standardized metrics
3. Returns results in common format

```python
class MisuseAdapter:
    def run(self, model: str) -> MisuseResult
    def get_metrics(self, result) -> dict
```

This allows adding new evaluation suites without changing core logic.

### Diff Engine

Computes deltas between baseline and candidate:

```python
diff = candidate_value - baseline_value
is_regression = diff > 0 if higher_is_worse else diff < 0
```

Handles both "higher is worse" (violation_rate) and "lower is worse" (avg_first_failure) metrics.

### Risk Grader

Applies thresholds to determine severity:

```python
if abs_delta >= block_threshold:
    severity = "block"
elif abs_delta >= warn_threshold:
    severity = "warn"
else:
    severity = "none"
```

Thresholds are configurable via YAML to allow tuning for different use cases.

## Threshold Governance

Thresholds are critical policy decisions, not arbitrary numbers.

### Calibration Process

1. **Initial thresholds** are calibrated from historical regression distributions
2. **Validation** against known regressions to ensure sensitivity
3. **Review** by safeguards owners before deployment

### Change Control

- All threshold changes require review from safeguards team
- Changes are versioned in git with justification in commit message
- Audit trail maintained for compliance

### Anti-Gaming Protections

- Thresholds cannot be modified by release requesters
- Overrides require explicit sign-off from safety leadership
- "Always pass" configurations are flagged and blocked

```yaml
# Example: Threshold change commit message
# "Relax violation_rate warn threshold 0.03 -> 0.04
#  Justification: Historical data shows 3% natural variance
#  Approved by: Safety Lead
#  Ticket: SAFE-1234"
```

---

## Design Tradeoffs

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Threshold source** | YAML config | Easy to tune without code changes |
| **Metric direction** | Explicit configuration | Avoids bugs from wrong assumptions |
| **Report format** | HTML | Human-readable, shareable |
| **Exit codes** | 0/1/2 for OK/BLOCK/WARN | CI/CD integration |
| **Adapter pattern** | Loose coupling | Easy to add new suites |

## Limitations

### Current Implementation

1. **Simulated models**: Uses simulated responses for demonstration
2. **Fixed scenarios**: No scenario mutation or augmentation
3. **Single-pass evaluation**: No statistical significance testing
4. **Manual threshold tuning**: No automated threshold discovery

### What Production Would Add

1. **Real model integration**: Connect to actual model APIs
2. **Statistical significance**: Run multiple trials, compute confidence intervals
3. **Threshold learning**: Calibrate thresholds from historical data
4. **Ensemble evaluation**: Multiple evaluators with voting
5. **Human review queue**: BLOCK decisions routed to safety reviewers
6. **Audit logs**: Full traceability of release decisions
7. **Rollback triggers**: Automatic rollback if post-release metrics degrade
8. **Cost-aware sampling**: Adaptive scenario selection to minimize API costs
9. **Slack/PagerDuty integration**: Real-time alerts for regressions
10. **Dashboard**: Historical regression trends across releases

## Integration Points

### CI/CD Pipeline

```yaml
# Example GitHub Actions integration
- name: Run safety regression
  run: |
    python run_regression.py \
      --baseline ${{ github.event.pull_request.base.sha }} \
      --candidate ${{ github.sha }} \
      --report report.html
  continue-on-error: false
```

### Release Checklist

1. ✅ Unit tests pass
2. ✅ Integration tests pass
3. ✅ Performance benchmarks pass
4. ✅ **Safety regression suite: OK or WARN (reviewed)**
5. ✅ Human sign-off

## Relationship to Other Projects

```
when-rlhf-fails-quietly
        │
        │ Understanding WHY regressions happen
        ▼
agentic-misuse-benchmark ─────┐
        │                     │
        │ Detection scenarios │
        ▼                     │
safeguards-stress-tests ──────┤
        │                     │
        │ Attack templates    │
        ▼                     ▼
scalable-safeguards-eval-pipeline
        │
        │ Run evaluations at scale
        ▼
MODEL SAFETY REGRESSION SUITE ← YOU ARE HERE
        │
        │ Compare versions, gate releases
        ▼
    [Release Decision]
```

This suite is the final aggregation point that combines all evaluation signals into a release decision.
