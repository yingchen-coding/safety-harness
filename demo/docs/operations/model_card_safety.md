# Model Card - Safety Section (Template)

## Model Overview

- Model Name:
- Version / Checkpoint:
- Release Date:
- Intended Use:
- Deployment Context (agentic / tools / APIs):

## Safety Scope

This section documents safety properties and known limitations of the model in agentic, multi-turn settings.

## Evaluated Threat Models

| Threat Category        | Coverage | Evaluation Method                        |
|------------------------|----------|-------------------------------------------|
| Prompt Injection       | Yes      | Multi-turn misuse benchmark               |
| Policy Erosion         | Yes      | Trajectory-level erosion metrics          |
| Intent Drift           | Yes      | Longitudinal rollout analysis             |
| Coordinated Misuse     | Yes      | Automated red-teaming                     |
| Tool Misuse            | Yes      | Safeguards simulator + stress tests       |
| Detector Evasion       | Yes      | Adaptive attacker modeling                |

## Evaluation Summary

| Metric                       | Baseline | Current | Delta | Verdict |
|------------------------------|----------|---------|-------|---------|
| Trajectory Failure Rate      |          |         |       |         |
| Delayed Failure Rate (>= N)  |          |         |       |         |
| Policy Erosion Slope         |          |         |       |         |
| Mean Time To Violation       |          |         |       |         |
| Detection FNR (Misuse)       |          |         |       |         |

Statistical significance tested via bootstrapping and permutation tests.
Release gating verdict: **OK / WARN / BLOCK**

## Known Failure Modes

- Slow-burn policy erosion under repeated benign framing
- Tool hallucination under partial observability
- Intent drift in long-horizon planning tasks
- Detector blind spots under semantic paraphrasing

## Safeguards in Deployment

- Pre-action intent classification and injection detection
- Mid-trajectory drift and cumulative risk monitoring
- Post-action output verification and anomaly detection
- Escalation policy: Soft Stop -> Hard Stop -> Human Review

## Residual Risk

Despite safeguards, the following risks remain:

- Adaptive attackers can induce delayed failures
- Partial observability limits intent inference accuracy
- Safeguards trade off false positives vs. missed violations

## Monitoring & Governance

- Continuous evaluation via batch + streaming pipeline
- Safety regression gating enforced in CI/CD
- Incident replay and regression test generation enabled
- Threshold changes require audit and approval

## Limitations

- Benchmarks do not fully cover real-world attacker creativity
- Metrics are proxies and may not capture all harm dimensions
- Results may not generalize across deployment contexts

## Future Work

- Expand coordinated misuse scenarios
- Improve detector robustness to adaptive attackers
- Incorporate user harm modeling beyond policy compliance
- Add real-world traffic shadow evaluation at scale

## Contact

Safety Owner:
Infra Owner:
Incident On-Call:
