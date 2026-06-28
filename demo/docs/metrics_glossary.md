# Safety Metrics Glossary

This glossary defines all safety metrics used across the portfolio.

## Core Metrics

**Policy Erosion Rate**
Rate at which compliance probability degrades over conversation turns.
Used to measure slow-burn vulnerabilities.

**Delayed Failure Rate**
Fraction of violations occurring after >= N turns.
Captures failures invisible to single-turn evaluation.

**Trajectory-Level Failure Rate**
Probability of any violation over a full multi-turn rollout.

**Detection FNR (False Negative Rate)**
Fraction of misuse trajectories not flagged by detectors.

**Risk Grade (OK/WARN/BLOCK)**
Release gating verdict based on statistically significant regressions.

**Erosion Slope**
Linear trend of compliance vs. turn index.

## Supporting Metrics

- Mean Time To Violation (MTTV)
- Attack Success Rate (red-teaming)
- Safeguard Escalation Rate
- Human Review Rate
- False Positive Block Rate

## Metric Caveats

- All metrics are stochastic -> evaluated with multi-seed bootstrapping
- Single-run metrics are not used for gating
- Metrics are tracked longitudinally to avoid Goodharting

## Interpretation Guidance

- Improving single-turn accuracy does **not** imply improved safety
- Decreasing MTTV is a regression even if overall failure rate is flat
- Stability over time is more important than absolute scores
