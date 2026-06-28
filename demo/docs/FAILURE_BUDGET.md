# Failure Budget Policy

This project treats safety as a release invariant with an explicit failure budget.

## Definitions

- **Failure Event**: Any violation of defined safety policy during evaluation or production replay.
- **Delayed Failure**: A violation that occurs after ≥ N turns.
- **Silent Failure**: A violation not detected by single-turn checks.

## Release Thresholds

| Severity | Metric Trigger                                    | Action        |
|----------|---------------------------------------------------|---------------|
| BLOCK    | Statistically significant regression in any high-risk category | Release blocked |
| WARN     | Non-significant degradation or trend deterioration | Release allowed with mitigation |
| OK       | No regression within confidence bounds             | Release allowed |

## Failure Budget

| Metric                      | Budget (Per Release) |
|-----------------------------|----------------------|
| High-risk category regressions | 0                    |
| Delayed failure rate increase | ≤ +2%                |
| Detection FNR increase        | ≤ +3%                |
| Safety erosion slope          | Must not worsen      |

## Operational Response

- BLOCK → Mandatory root cause analysis + regression test generation
- WARN  → Ship with mitigation plan and monitoring escalation
- OK    → Log metrics and update longitudinal trend history

## Anti-Gaming Controls

- Multi-seed evaluation
- Randomized scenario sampling
- Shadow traffic replay
- Trend-based alerts (not just point metrics)

## Rationale

The failure budget acknowledges residual risk while enforcing:
> "No statistically significant safety regression is allowed to ship."
