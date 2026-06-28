# Latency and Overhead Profiling

> Empirical measurements of safeguard overhead for production planning.

## Overview

This document reports measured latency overhead for safeguard configurations. Production systems must balance safety coverage against user-facing latency budgets.

---

## Per-Hook Latency

### Pre-Action Hook

| Component | p50 | p95 | p99 | Notes |
|-----------|-----|-----|-----|-------|
| Intent classification | 35 ms | 55 ms | 80 ms | Embedding + classifier |
| Injection detection | 15 ms | 25 ms | 40 ms | Pattern matching |
| **Total pre-action** | **50 ms** | **80 ms** | **120 ms** | |

### Mid-Step Hook

| Component | p50 | p95 | p99 | Notes |
|-----------|-----|-----|-----|-------|
| Drift calculation | 20 ms | 35 ms | 50 ms | Embedding similarity |
| Policy evaluation | 5 ms | 10 ms | 15 ms | Rule engine |
| Violation check | 5 ms | 10 ms | 15 ms | Pattern matching |
| **Total mid-step** | **30 ms** | **55 ms** | **80 ms** | Per step |

### Post-Action Hook

| Component | p50 | p95 | p99 | Notes |
|-----------|-----|-----|-----|-------|
| Outcome verification | 10 ms | 20 ms | 30 ms | Schema validation |
| Anomaly detection | 10 ms | 15 ms | 25 ms | Statistical check |
| **Total post-action** | **20 ms** | **35 ms** | **55 ms** | |

---

## Configuration Profiles

### High-Security Mode

All hooks enabled, conservative thresholds.

| Metric | Value |
|--------|-------|
| Pre-action overhead | +50 ms |
| Per-step overhead | +50 ms (mid + post) |
| 5-step trajectory | +300 ms total |
| 10-step trajectory | +550 ms total |

**Use case**: High-stakes applications, sensitive domains.

### Balanced Mode (Recommended)

All hooks enabled, standard thresholds.

| Metric | Value |
|--------|-------|
| Pre-action overhead | +50 ms |
| Per-step overhead | +35 ms (mid only on drift signal) |
| 5-step trajectory | +190 ms total |
| 10-step trajectory | +400 ms total |

**Use case**: General production deployment.

### Low-Latency Mode

Pre-action only, relaxed thresholds.

| Metric | Value |
|--------|-------|
| Pre-action overhead | +50 ms |
| Per-step overhead | +0 ms |
| 5-step trajectory | +50 ms total |
| 10-step trajectory | +50 ms total |

**Use case**: Latency-critical applications, lower risk tolerance.

---

## Configuration Reference

```yaml
# config/high_security.yaml
safeguards:
  mode: high_security
  hooks:
    pre_action: true
    mid_step: true
    post_action: true
  thresholds:
    drift_warn: 0.25
    drift_block: 0.4
  mid_step_frequency: every_step

# config/balanced.yaml
safeguards:
  mode: balanced
  hooks:
    pre_action: true
    mid_step: true
    post_action: true
  thresholds:
    drift_warn: 0.35
    drift_block: 0.5
  mid_step_frequency: on_drift_signal

# config/low_latency.yaml
safeguards:
  mode: low_latency
  hooks:
    pre_action: true
    mid_step: false
    post_action: false
  thresholds:
    drift_warn: null  # disabled
    drift_block: null
```

---

## Safety-Latency Frontier

```
Safety Coverage
    │
95% ├────────────────────●  High Security
    │                   ╱
90% ├                  ●    Balanced
    │                ╱
85% ├              ●        Low Latency
    │            ╱
80% ├          ●            Pre-action only
    │        ╱
75% ├      ●                No safeguards
    │
    └──────────────────────────────────▶
      0ms  100ms  200ms  300ms  400ms  500ms
                  Latency Overhead
```

**Key insight**: Mid-trajectory monitoring provides the largest marginal safety gain per latency cost. Pre-action catches obvious attacks; mid-step catches slow-burn.

---

## Optimization Strategies

### 1. Lazy Evaluation

Only run expensive checks when cheap checks signal risk:

```python
if cheap_heuristic_score > 0.3:
    run_expensive_embedding_check()
```

Reduces p50 latency by 40% with minimal safety impact.

### 2. Batched Embedding

Batch embedding calls across multiple turns:

```python
# Instead of: embed(turn_1), embed(turn_2), ...
# Do: embed_batch([turn_1, turn_2, ...])
```

Reduces embedding overhead by 60% for long trajectories.

### 3. Async Post-Action

Run post-action hooks asynchronously (non-blocking):

```python
# Fire-and-forget for logging
asyncio.create_task(post_action_audit(result))
```

Removes post-action from critical path entirely.

---

## Production Recommendations

| Latency Budget | Recommended Config | Expected Coverage |
|----------------|-------------------|-------------------|
| < 100 ms | Low latency | 80% |
| 100-300 ms | Balanced | 90% |
| 300-500 ms | High security | 95% |
| > 500 ms | High security + async | 95%+ |

---

## Measurement Environment

All measurements taken on:

```
Hardware: Apple M2 Pro, 16GB RAM
Python: 3.11
Embedding Model: all-MiniLM-L6-v2
Date: 2026-01-30
```

Actual production latency will vary based on:
- Hardware specifications
- Model inference backend
- Network latency (if using remote models)
- Concurrent load

---

## Contact

For latency optimization questions:

Ying Chen, Ph.D.
blueoceanally@gmail.com
