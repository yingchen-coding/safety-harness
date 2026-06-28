# Safeguard Ablation Results

This document reports results from systematic safeguard ablations.

---

## 1. Overview

Ablation studies answer: **"Which safeguards actually help, and at what cost?"**

We systematically enable/disable safeguard components and measure:
- Safety metrics (violation rate, harm level)
- Operational metrics (latency, token cost, false block rate)

---

## 2. Ablation Variants

| Variant | Pre-Action | Mid-Trajectory | Post-Action |
|---------|------------|----------------|-------------|
| `none` | - | - | - |
| `pre_only` | ✓ | - | - |
| `pre_mid` | ✓ | ✓ | - |
| `pre_mid_post` | ✓ | ✓ | ✓ |

### Component Descriptions

- **Pre-Action:** Intent classifier on user input before agent processes
- **Mid-Trajectory:** Monitor running state for drift/escalation patterns
- **Post-Action:** Verify agent output before returning to user

---

## 3. Results Summary

### Safety Metrics

| Variant | Violation Rate | Avg Violation Turn | Harm Level (avg) |
|---------|---------------|-------------------|------------------|
| `none` | 42.0% | 3.2 | 3.4 |
| `pre_only` | 28.5% | 3.8 | 3.1 |
| `pre_mid` | 16.2% | 4.5 | 2.7 |
| `pre_mid_post` | 8.1% | 5.1 | 2.2 |

### Operational Metrics

| Variant | P50 Latency | P95 Latency | Mean Tokens | False Block Rate |
|---------|-------------|-------------|-------------|------------------|
| `none` | 45ms | 120ms | 150 | 0% |
| `pre_only` | 95ms | 280ms | 420 | 3.2% |
| `pre_mid` | 180ms | 650ms | 720 | 5.8% |
| `pre_mid_post` | 320ms | 1200ms | 1150 | 8.4% |

---

## 4. Key Findings

### 4.1 Pre-Action Safeguards

**Marginal Violation Reduction:** 13.5 percentage points (42.0% → 28.5%)
**Marginal Latency Cost:** +160ms P95
**Marginal Token Cost:** +270 tokens/turn

**Analysis:** Pre-action provides strong first-line defense with moderate cost. Essential for any deployment.

### 4.2 Mid-Trajectory Monitoring

**Marginal Violation Reduction:** 12.3 percentage points (28.5% → 16.2%)
**Marginal Latency Cost:** +370ms P95
**Marginal Token Cost:** +300 tokens/turn

**Analysis:** Mid-trajectory catches delayed failures that pre-action misses. Significant value for multi-turn scenarios where intent drift is a concern.

### 4.3 Post-Action Verification

**Marginal Violation Reduction:** 8.1 percentage points (16.2% → 8.1%)
**Marginal Latency Cost:** +550ms P95
**Marginal Token Cost:** +430 tokens/turn

**Analysis:** Post-action provides final safety net but at highest cost. Diminishing returns compared to pre+mid. Consider for high-risk applications only.

---

## 5. False Block Analysis

| Variant | False Blocks | % of Total Blocks | User Impact |
|---------|--------------|-------------------|-------------|
| `pre_only` | 3.2% | 18% | Moderate friction |
| `pre_mid` | 5.8% | 24% | Noticeable friction |
| `pre_mid_post` | 8.4% | 31% | Significant friction |

**Observation:** False block rate increases with safeguard depth. Post-action adds 2.6% false blocks while only reducing violations by 8.1%.

---

## 6. Deployment Recommendations

### Budget: Latency-Constrained (P95 < 500ms)

**Recommendation:** `pre_only` or `pre_mid` with optimized mid-trajectory

Rationale: `pre_mid_post` exceeds latency budget. `pre_mid` provides best safety/latency tradeoff.

### Budget: Cost-Constrained (< 500 tokens/turn)

**Recommendation:** `pre_only`

Rationale: Only `pre_only` meets token budget while providing meaningful safety improvement.

### Budget: Safety-Critical (Violation rate < 10%)

**Recommendation:** `pre_mid_post`

Rationale: Only full stack achieves <10% violation rate. Accept latency/cost tradeoff for safety.

---

## 7. Tradeoff Visualization

```
Safety vs Latency Frontier:

Violation Rate
     |
 40% |  * none
     |
 30% |      * pre_only
     |
 20% |            * pre_mid
     |
 10% |                    * pre_mid_post
     |
  0% +------------------------------> P95 Latency
        100   300   500   700   900  1100 ms
```

---

## 8. Methodology

### Scenarios Tested

- 20 intent drift scenarios
- 15 policy erosion scenarios
- 10 tool misuse scenarios
- 5 adversarial attack scenarios

### Sample Size

- N=50 runs per variant per scenario
- Total: 10,000 runs across all variants and scenarios

### Statistical Confidence

- All reported differences significant at p < 0.01
- 95% confidence intervals computed via bootstrap

---

## 9. Limitations

1. **Mock safeguards:** Results based on simulated safeguards; production performance may vary
2. **Scenario coverage:** May not represent all attack patterns
3. **Cost model:** Token costs are estimates; actual costs depend on provider
4. **Latency variability:** Production latency depends on infrastructure

---

## 10. Recommendations for Future Work

1. **Adaptive safeguards:** Dynamically enable mid/post based on risk score
2. **Caching:** Cache classifier results for repeated patterns
3. **Tiered response:** Use lightweight pre-filter before full classifier
4. **A/B testing:** Validate ablation results in production traffic

---

*Safeguard design is optimization under constraints. Know your constraints.*
