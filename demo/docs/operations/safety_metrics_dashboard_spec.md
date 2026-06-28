# Safety Metrics Dashboard Spec (Agentic Systems)

This document defines the minimum viable dashboard for monitoring safety in production.
The goal is to detect **delayed failures, policy erosion, misuse drift, and safeguard degradation** in near real time.

---

## 1. Executive Overview (Top Panel)

**Purpose:** Let on-call and leadership answer: "Are we getting less safe right now?"

KPIs:
- Safety Violation Rate (last 1h / 24h / 7d)
- Delayed Failure Rate (multi-turn violations)
- Safeguard Trigger Rate (pre/mid/post)
- Kill-switch Activation Count
- Canary vs Baseline Safety Delta

Visualization:
- Time-series with baseline overlay
- Canary vs control comparison

Alerts:
- Violation rate spike > X sigma over 7-day baseline
- Canary safety delta < 0 with p < 0.05

---

## 2. Trajectory-Level Risk Panel

**Purpose:** Detect slow-burn failures invisible to single-turn metrics.

Metrics:
- First-violation turn distribution
- Mean time to violation (MTTV)
- Cumulative risk score per session
- Drift slope (risk accumulation rate)

Visualization:
- Delayed failure curve
- Histogram of violation turn index
- Trend line of MTTV

Alerts:
- MTTV decreasing week-over-week
- Tail risk (95th percentile turn-to-violation) worsening

---

## 3. Misuse & Adversarial Activity Panel

**Purpose:** Detect shifts in attacker behavior and detector erosion.

Metrics:
- Detector FN rate (by scenario family)
- Adaptive attacker success rate
- Novel pattern rate (embedding novelty)
- Attack category mix over time

Visualization:
- Stacked area chart (attack types)
- FN rate by detector version

Alerts:
- FN rate > threshold
- Sudden increase in coordinated misuse

---

## 4. Safeguards Health Panel

**Purpose:** Ensure safeguards are actually active and effective.

Metrics:
- Pre-action block rate
- Mid-trajectory intervention rate
- Post-action correction rate
- False positive rate (human override)
- Safeguard latency overhead

Visualization:
- Intervention funnel (pre -> mid -> post)
- Latency heatmap

Alerts:
- Intervention rate drops to zero
- FP backlog exceeds SLA
- Latency overhead > budget

---

## 5. Release Gating & Regression Panel

**Purpose:** Tie production behavior back to release quality.

Metrics:
- Safety regressions in last N releases
- Canary vs baseline regression deltas
- Escaped incidents per release
- Regression coverage growth

Visualization:
- Release timeline with safety deltas
- Escaped incident count per release

Alerts:
- Escaped incident after "OK" gate
- Coverage stagnation

---

## 6. Operational Panel

**Purpose:** Make safety visible as an operational cost center.

Metrics:
- Cost per safety eval
- Coverage vs cost curve
- Eval queue backlog
- On-call pages per week

Visualization:
- Cost vs coverage tradeoff curve
- Backlog trend

Alerts:
- Eval backlog > SLA
- Cost spike without coverage gain

---

## 7. Dashboard Hygiene

- All metrics versioned with policy + model hash
- Canary and baseline always comparable
- Every alert links to runbook
- Dashboards are part of release sign-off checklist
