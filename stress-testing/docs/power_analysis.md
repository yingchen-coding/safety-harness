# Power Analysis for Stress Testing

This document describes how to size red-teaming experiments to reliably detect safety regressions.

---

## 1. Motivation

Delayed failures are rare events. Underpowered experiments lead to:
- **False negatives:** "We didn't see a difference" when one exists
- **Overconfident conclusions:** Publishing results that don't replicate
- **Wasted resources:** Running experiments that can't answer the question

**Power analysis tells you how many samples you need before you run the experiment.**

---

## 2. Key Concepts

### Effect Size

The difference you want to detect:
- **Small effect:** 3% change (e.g., 10% → 13%)
- **Medium effect:** 5% change (e.g., 10% → 15%)
- **Large effect:** 10% change (e.g., 10% → 20%)

### Power

Probability of detecting an effect if it exists:
- **Underpowered:** Power < 50% (coin flip)
- **Acceptable:** Power 50-80%
- **Well-powered:** Power ≥ 80% (standard target)
- **Highly powered:** Power ≥ 90%

### Alpha (Significance Level)

Probability of false positive:
- **Standard:** α = 0.05 (5% false positive rate)
- **Stringent:** α = 0.01 (1% false positive rate)

---

## 3. Sample Size Formula

For two-proportion comparison:

```
N = 2 * ((z_α + z_β)² * p̄ * (1 - p̄)) / (p₁ - p₂)²

Where:
  z_α = Z-value for significance level
  z_β = Z-value for power
  p̄ = pooled proportion = (p₁ + p₂) / 2
  p₁ = baseline (control) proportion
  p₂ = expected (treatment) proportion
```

---

## 4. Reference Table

Sample sizes needed per group (α = 0.05, power = 0.80):

| Baseline Rate | 3% Effect | 5% Effect | 10% Effect |
|---------------|-----------|-----------|------------|
| 5% | 1,067 | 435 | 137 |
| 10% | 863 | 343 | 103 |
| 15% | 752 | 296 | 87 |
| 20% | 680 | 265 | 77 |
| 30% | 582 | 223 | 63 |

**Interpretation:** To detect a 5% increase from 10% baseline with 80% power, you need 343 samples per condition (686 total).

---

## 5. When to Use Power Analysis

### Before Running Experiment

1. Estimate baseline failure rate from prior data
2. Define minimum effect you care about
3. Calculate required sample size
4. Allocate resources accordingly

### After Running Experiment

1. If result is significant: Report effect size and CI
2. If result is not significant: Report achieved power
3. If underpowered: Explicitly state "inconclusive"

---

## 6. Common Mistakes

### Mistake 1: Post-hoc Power Analysis

**Wrong:** "We got p = 0.08, but power was only 60%, so it's still meaningful"

**Right:** Power analysis should be done BEFORE the experiment. Post-hoc power is meaningless.

### Mistake 2: Ignoring Effect Size

**Wrong:** "p < 0.05, so the effect is important"

**Right:** A tiny effect can be significant with enough samples. Report effect size.

### Mistake 3: Underpowered "Negative" Results

**Wrong:** "We found no difference (N=50)"

**Right:** "With N=50, we had only 25% power to detect a 5% effect. Results are inconclusive."

---

## 7. Reporting Guidelines

All stress test results should include:

### Required

- [ ] Sample size per condition
- [ ] Observed effect size
- [ ] 95% confidence interval
- [ ] P-value
- [ ] Pre-specified power target

### Recommended

- [ ] Power analysis calculation
- [ ] Sensitivity analysis (what effect could we detect?)
- [ ] Subgroup analyses if pre-registered

### Example Report

```markdown
## Results

- **Control:** 10.2% violation rate (N=500)
- **Treatment:** 15.8% violation rate (N=500)
- **Effect:** +5.6 percentage points
- **95% CI:** [+1.8%, +9.4%]
- **P-value:** 0.004
- **Pre-specified power:** 80% to detect 5% effect
- **Conclusion:** Statistically significant increase in violation rate
```

---

## 8. Special Considerations for Safety Testing

### Rare Events

Safety violations may be rare (< 5%). For rare events:
- Need larger samples to achieve power
- Consider exact tests (Fisher's exact) instead of z-test
- Report confidence intervals even if wide

### Multiple Comparisons

Testing many attack categories inflates false positive rate:
- Apply Bonferroni correction: α_adjusted = α / k
- Or use False Discovery Rate (FDR) control
- Pre-register primary comparisons

### Sequential Analysis

Running experiments until significant is p-hacking:
- Pre-specify sample size
- If sequential testing is needed, use group sequential designs
- Adjust alpha for interim analyses

---

## 9. Tools

### Python

```python
from stats.power_analysis import PowerAnalyzer

analyzer = PowerAnalyzer(alpha=0.05, power=0.80)

# Before experiment
result = analyzer.calculate_sample_size(
    baseline_rate=0.10,
    minimum_detectable_effect=0.05
)
print(f"Need {result.required_n} per group")

# After experiment
exp = analyzer.analyze_experiment(
    n_control=500, n_treatment=500,
    failures_control=51, failures_treatment=79
)
print(f"Effect: {exp.effect_size:.1%}, p={exp.p_value:.4f}")
```

### Command Line

```bash
# Calculate sample size
python -m stats.power_analysis --baseline 0.10 --effect 0.05

# Analyze results
python -m stats.power_analysis --analyze \
    --control 500 51 \
    --treatment 500 79
```

---

## 10. Checklist

Before running experiment:
- [ ] Defined baseline rate estimate
- [ ] Defined minimum effect of interest
- [ ] Calculated required sample size
- [ ] Confirmed resources available
- [ ] Pre-registered analysis plan

After running experiment:
- [ ] Reported sample sizes
- [ ] Reported effect size with CI
- [ ] Reported p-value
- [ ] Interpreted in context of power
- [ ] Flagged if underpowered

---

*An underpowered experiment is not a cheap experiment—it's a waste of resources that answers nothing.*
