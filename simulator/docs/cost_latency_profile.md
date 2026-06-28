# Cost and Latency Profile

This document characterizes the operational cost of safeguards and provides deployment guidance.

---

## 1. Why Cost/Latency Matters

Safety without deployability is safety theater. A safeguard that:
- Adds 5 seconds latency won't be enabled in production
- Costs $0.50 per turn won't scale to millions of users
- Causes 20% false blocks will be disabled after user complaints

**This document quantifies these tradeoffs.**

---

## 2. Cost Model

### Token Costs (Per Call)

| Component | Input Tokens | Output Tokens | Est. Cost |
|-----------|--------------|---------------|-----------|
| Intent Classifier | 200-400 | 20-50 | $0.005 |
| Mid-Trajectory Monitor | 300-600 | 50-100 | $0.012 |
| Post-Action Verifier | 400-800 | 100-200 | $0.020 |
| LLM Judge (full) | 1000-2000 | 200-500 | $0.050 |
| Rule Check | 0 | 0 | $0.000 |

### Cost Per Conversation

| Safeguard Config | 5-Turn | 10-Turn | 20-Turn |
|------------------|--------|---------|---------|
| `none` | $0.00 | $0.00 | $0.00 |
| `pre_only` | $0.025 | $0.050 | $0.100 |
| `pre_mid` | $0.085 | $0.170 | $0.340 |
| `pre_mid_post` | $0.185 | $0.370 | $0.740 |

---

## 3. Latency Model

### Component Latencies

| Component | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Intent Classifier | 45ms | 120ms | 250ms |
| Mid-Trajectory Monitor | 80ms | 220ms | 450ms |
| Post-Action Verifier | 150ms | 400ms | 800ms |
| LLM Judge | 500ms | 1500ms | 3000ms |
| Rule Check | 2ms | 5ms | 10ms |

### Cumulative Latency (Added per Turn)

| Config | P50 | P95 | P99 |
|--------|-----|-----|-----|
| `none` | 0ms | 0ms | 0ms |
| `pre_only` | 45ms | 120ms | 250ms |
| `pre_mid` | 125ms | 340ms | 700ms |
| `pre_mid_post` | 275ms | 740ms | 1500ms |

---

## 4. Latency Budget Framework

### Define Your Budget

```python
budget = LatencyBudget(
    p50_max_ms=200,   # Median response feels instant
    p95_max_ms=500,   # Most users don't notice
    p99_max_ms=2000   # Rare slow responses acceptable
)
```

### Budget Compliance Check

| Config | P95 Budget (500ms) | Status |
|--------|--------------------|--------|
| `none` | 0ms | ✅ PASS |
| `pre_only` | 120ms | ✅ PASS |
| `pre_mid` | 340ms | ✅ PASS |
| `pre_mid_post` | 740ms | ❌ FAIL |

---

## 5. Cost Budget Framework

### Define Your Budget

```python
cost_budget = CostBudget(
    max_tokens_per_turn=2000,
    max_cost_per_conversation_usd=0.50
)
```

### Budget Compliance Check (10-turn conversation)

| Config | Cost | Budget ($0.50) | Status |
|--------|------|----------------|--------|
| `none` | $0.00 | ✅ | PASS |
| `pre_only` | $0.05 | ✅ | PASS |
| `pre_mid` | $0.17 | ✅ | PASS |
| `pre_mid_post` | $0.37 | ✅ | PASS |

---

## 6. Deployment Guidance Matrix

| Priority | Budget | Recommended Config |
|----------|--------|-------------------|
| Safety-first | Flexible | `pre_mid_post` |
| Balanced | P95 < 500ms, $0.30/conv | `pre_mid` |
| Cost-optimized | P95 < 200ms, $0.10/conv | `pre_only` |
| Latency-critical | P95 < 100ms | `none` + async logging |

---

## 7. Optimization Strategies

### 7.1 Caching

Cache classifier results for identical inputs:
- Hit rate: ~15-25% in production
- Latency reduction: 40-60ms per cached call

### 7.2 Batching

Batch mid-trajectory checks across turns:
- Batch size 3: 40% token reduction
- Tradeoff: Delayed detection

### 7.3 Tiered Classification

Use cheap rule check first, expensive classifier only if needed:
- 60% of inputs resolved by rules
- 70% latency reduction for rule-resolved cases

### 7.4 Async Post-Action

Run post-action verification asynchronously:
- Response returns immediately
- Violation logged for later review
- Tradeoff: No real-time block

---

## 8. Monitoring Dashboards

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| P95 Latency | < 500ms | > 750ms |
| Mean Token Cost | < $0.02/turn | > $0.03/turn |
| False Block Rate | < 5% | > 8% |
| Cache Hit Rate | > 15% | < 10% |

### Sample Dashboard Query

```sql
SELECT
  safeguard_name,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
  avg(token_count) as avg_tokens,
  count(*) as call_count
FROM safeguard_metrics
WHERE timestamp > now() - interval '1 hour'
GROUP BY safeguard_name
ORDER BY p95_latency DESC;
```

---

## 9. Cost Attribution

### Per-Incident Cost Analysis

When a safety incident occurs, attribute costs:

| Cost Type | Calculation | Example |
|-----------|-------------|---------|
| Safeguard Cost | Tokens × rate | $0.037 |
| Investigation Cost | Human hours × rate | $150 |
| Remediation Cost | Engineering hours | $500 |
| Reputation Cost | Hard to quantify | ??? |

**Insight:** Safeguard costs are negligible compared to incident costs.

---

## 10. Tradeoff Summary

```
                    ┌─────────────────────────────┐
                    │      COST / LATENCY         │
                    │                             │
             LOW    │   * none                    │
                    │       * pre_only            │
                    │            * pre_mid        │
            HIGH    │                  * pre_mid_post
                    └─────────────────────────────┘
                         LOW ────── SAFETY ────── HIGH
```

**Choose based on your constraints. There is no free lunch.**

---

*The safest system is one that's actually deployed. Design for deployability.*
