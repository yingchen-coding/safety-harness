# Release Authority

> **Who can block, warn, or approve releases in the safety system.**
> This document defines decision rights. If it's not here, no one has the authority.

---

## Why Release Authority Matters

In real safety organizations, unclear authority causes:
- **Bystander effect**: "I assumed someone else would block it"
- **Authority creep**: Multiple repos claiming veto power
- **Overrides without accountability**: "We shipped anyway"

This document eliminates ambiguity about who decides.

---

## The One Rule

> **Only ⑥ model-safety-regression-suite outputs release verdicts.**

All other repositories produce **signals**, not **decisions**.

```
Signals (from ①②③④⑤⑦) ──→ ⑥ Regression Suite ──→ Verdict (OK/WARN/BLOCK)
                                                        │
                                                        ▼
                                                     CI/CD
```

---

## Verdict Definitions

| Verdict | Meaning | CI/CD Action |
|---------|---------|--------------|
| **OK** | Safe to proceed | Allow merge/deploy |
| **WARN** | Proceed with documented justification | Require approval comment |
| **BLOCK** | Cannot proceed | Fail pipeline |

---

## Authority Matrix

| Repo | Can Produce | Cannot Produce |
|------|-------------|----------------|
| ① when-rlhf-fails-quietly | Failure taxonomy, causal analysis | Any verdict |
| ② agentic-misuse-benchmark | Detection scores, benchmark results | Any verdict |
| ③ agentic-safeguards-simulator | Safeguard signals, bypass analysis | Any verdict |
| ④ safeguards-stress-tests | Erosion data, stress results | Any verdict |
| ⑤ scalable-safeguards-eval-pipeline | Metrics, drift alerts | Any verdict |
| ⑥ model-safety-regression-suite | **OK / WARN / BLOCK** | N/A |
| ⑦ agentic-safety-incident-lab | RCA, promoted regressions | Any verdict |
| ⑧ agentic-safety-demo | Demo status | Any verdict |

---

## Signal vs. Decision

### Signals (Inputs to Gating)

```yaml
# Example signal from ⑤ eval-pipeline
signal:
  source: scalable-safeguards-eval-pipeline
  type: drift_alert
  metric: failure_rate
  value: 0.11
  baseline: 0.08
  delta: +0.03
  confidence_interval: [0.09, 0.13]
  timestamp: 2026-02-01T03:00:00Z
```

### Decision (Output from Gating)

```yaml
# Example verdict from ⑥ regression-suite
verdict:
  source: model-safety-regression-suite
  decision: WARN
  reasons:
    - "failure_rate 11% within WARN band (8-12%)"
    - "erosion_slope -0.12 within WARN band"
  required_action: "Approval comment required before merge"
  trace_id: "gate_2026_02_01_001"
```

---

## Override Policy

### Can a BLOCK be overridden?

**Yes**, but only with:

1. **Written justification** in PR/commit
2. **Explicit approval** from safety lead
3. **Time-bounded exception** (max 7 days)
4. **Remediation plan** with tracking issue

### Override Audit Trail

All overrides must be logged:

```yaml
override:
  original_verdict: BLOCK
  override_to: WARN
  justification: "False positive due to benchmark bug INC_XXX"
  approved_by: "safety-lead@example.com"
  expires: 2026-02-08
  remediation_issue: "SAFETY-1234"
```

---

## Escalation Path

When verdicts are disputed:

```
1. Developer disagrees with BLOCK
   │
   ▼
2. Review verdict reasoning in decision trace
   │
   ├─ Trace shows bug → File issue against ⑥
   │
   └─ Trace is correct → Request override (see Override Policy)
       │
       ▼
3. Override requires safety lead approval
   │
   ▼
4. All overrides logged and time-bounded
```

---

## Authority Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|------------------|
| ⑤ eval-pipeline outputting BLOCK | Wrong authority | ⑤ produces metrics, ⑥ decides |
| ③ safeguards adding release logic | Scope creep | Keep safeguards pure |
| Verbal override of BLOCK | No audit trail | Written approval required |
| Permanent override | Bypasses safety | All overrides expire |

---

## Accountability

| Role | Responsibility |
|------|----------------|
| **Repo ⑥ owner** | Verdict accuracy, threshold calibration |
| **Safety lead** | Override approval, escalation resolution |
| **Developer** | Responding to verdicts, providing justification |
| **Oncall** | Investigating disputed verdicts |

---

## Change Process

Modifying release authority requires:

1. Written proposal with rationale
2. Impact analysis on CI/CD
3. Safety lead approval
4. 7-day notice before implementation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial authority definition |
