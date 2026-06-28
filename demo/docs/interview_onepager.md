# How the Safety System Fits Together (Interview One-Pager)

## Portfolio Map

| Repo | Role |
|------|------|
| when-rlhf-fails-quietly | Silent failures diagnosed |
| agentic-misuse-benchmark | Threats benchmarked |
| agentic-safeguards-simulator | Safeguards designed |
| safeguards-stress-tests | Attacks automated |
| scalable-safeguards-eval-pipeline | Scaled eval |
| model-safety-regression-suite | Release gated |
| agentic-safety-incident-lab | Incidents closed-looped |
| safety-memos + whitepaper | Research communicated |

## Key Claim

Single-turn evals systematically underestimate risk.
Safety must be enforced at trajectory-level across the full lifecycle.

## The Loop

```
Discovery -> Regression -> Gating -> Incident -> Discovery
```

Each failure discovered feeds back into the regression suite.
Each incident generates new tests.
No statistically significant regression ships.
