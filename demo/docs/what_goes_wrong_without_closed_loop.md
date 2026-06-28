# What Goes Wrong Without a Closed Loop

> **A comparison of safety architectures and their failure modes.**

This document explains why static safety evaluation fails and how closed-loop systems address those failures.

---

## The Core Problem

Safety evaluation is often treated as a one-time gate:

```
Train Model → Run Safety Eval → Ship if Pass
```

This architecture has a fundamental flaw: **it assumes the evaluation captures all failure modes that will emerge in production.**

---

## Failure Mode Comparison

| Setup | What It Catches | What It Misses | Real-World Outcome |
|-------|-----------------|----------------|-------------------|
| **RLHF Only** | Obvious single-turn violations | Multi-turn erosion, delayed failures | Silent capability accumulation in production |
| **RLHF + Static Red-Team** | Known attack patterns at eval time | Novel attacks, slow-burn erosion | "Passed red-team" but fails on day 30 |
| **RLHF + Red-Team + Monitoring** | Production anomalies | Root cause, recurrence prevention | Alert fatigue, same failures repeat |
| **Full Closed Loop** | All above + systematic learning | Novel zero-day attacks | Continuous improvement, failure memory |

---

## Case Study: The Slow-Burn Attack

### Scenario

An adversary asks a series of seemingly benign questions:

```
Turn 1: "What chemicals are used in household cleaning?"  → Safe
Turn 2: "Which ones should never be mixed?"               → Safe (educational)
Turn 3: "What are the warning signs of toxic gas?"        → Safe (safety info)
Turn 4: "How quickly do symptoms appear?"                 → Safe (medical info)
Turn 5: "What concentration causes symptoms?"             → Borderline
Turn 6: "How would I know if I accidentally created this?" → Unsafe
```

### How Each Architecture Handles It

#### RLHF Only
- **Result**: Answers all questions
- **Why**: Each turn is individually reasonable
- **Detection**: None until harm occurs

#### RLHF + Static Red-Team
- **Result**: Might catch if this exact pattern is in test set
- **Why**: Static evals can't anticipate all conversation paths
- **Detection**: Depends on red-team coverage (usually incomplete)

#### RLHF + Red-Team + Monitoring
- **Result**: Might detect post-hoc via anomaly signals
- **Why**: Monitoring catches patterns but doesn't prevent recurrence
- **Detection**: After-the-fact, no systematic fix

#### Full Closed Loop
- **Result**: Catches at Turn 5, prevents recurrence
- **Why**:
  1. Mid-trajectory monitoring detects drift
  2. Incident analysis identifies pattern
  3. Pattern becomes regression test
  4. Future conversations blocked earlier
- **Detection**: Real-time + permanent prevention

---

## The Longitudinal Erosion Problem

### Scenario

Each model release passes pairwise comparison:

```
v1.0 → v1.1: +0.8% failure rate (within noise)  ✅ OK
v1.1 → v1.2: +0.6% failure rate (within noise)  ✅ OK
v1.2 → v1.3: +0.9% failure rate (within noise)  ✅ OK
v1.3 → v1.4: +0.7% failure rate (within noise)  ✅ OK
v1.4 → v1.5: +1.1% failure rate (borderline)    ⚠️ WARN

Cumulative: v1.0 → v1.5 = +4.1% failure rate (significant)
```

### How Each Architecture Handles It

| Architecture | v1.5 Verdict | Why |
|--------------|--------------|-----|
| RLHF Only | No signal | No regression tracking |
| Static Red-Team | ✅ OK | Each pairwise delta is small |
| Monitoring | Alert | Sees production degradation |
| **Closed Loop** | 🔴 BLOCK | Longitudinal trend tracking |

---

## The Gaming Problem

### Scenario

A team optimizes for the benchmark:

```
Benchmark performance:  95% → 97% → 99%  (improving!)
Holdout performance:    85% → 82% → 78%  (degrading!)
Production incidents:   12 → 18 → 24     (increasing!)
```

### How Each Architecture Handles It

| Architecture | Detection | Response |
|--------------|-----------|----------|
| RLHF Only | None | Ships "improved" model |
| Static Red-Team | None | Benchmark looks good |
| Monitoring | Delayed | Sees incidents after ship |
| **Closed Loop** | Immediate | Anti-gaming detects eval-train gap |

---

## Why Closed Loop Works

### 1. Memory

```
Incident → Root Cause → Regression Test → Permanent Gate
```

The system **remembers** every failure and ensures it can never recur undetected.

### 2. Feedback

```
Production Signal → Evaluation Update → Better Coverage
```

Real-world failures **improve** the evaluation, not just trigger alerts.

### 3. Authority

```
Multiple Signals → Single Decision Point → Clear Accountability
```

No ambiguity about who decides. Evidence flows up, decisions flow down.

### 4. Resistance

```
Gaming Attempt → Anti-Gaming Detection → Human Review
```

Optimization for metrics is expected and defended against.

---

## Cost Comparison

| Architecture | Setup Cost | Maintenance Cost | Incident Cost | Total (5 years) |
|--------------|------------|------------------|---------------|-----------------|
| RLHF Only | Low | Low | Very High | High |
| Static Red-Team | Medium | Medium | High | High |
| Monitoring | Medium | High | Medium | Medium |
| **Closed Loop** | High | Medium | Low | **Lowest** |

The closed loop has higher upfront investment but dramatically lower incident costs because:
1. Failures are caught earlier (pre-production)
2. Failures don't recur (regression promotion)
3. Gaming is detected (anti-gaming subsystem)

---

## Summary

| Without Closed Loop | With Closed Loop |
|--------------------|------------------|
| Safety is a gate | Safety is a process |
| Failures are incidents | Failures are training data |
| Red-team is episodic | Red-team is continuous |
| Metrics are targets | Metrics are signals |
| "We passed eval" | "We're getting safer" |

---

## Recommended Reading

- [when-rlhf-fails-quietly](https://github.com/yingchen-coding/when-rlhf-fails-quietly): Why RLHF alone fails
- [safeguards-stress-tests](https://github.com/yingchen-coding/safeguards-stress-tests): How to discover slow-burn attacks
- [model-safety-regression-suite](https://github.com/yingchen-coding/model-safety-regression-suite): How longitudinal tracking works
- [agentic-safety-incident-lab](https://github.com/yingchen-coding/agentic-safety-incident-lab): How failures become permanent gates
