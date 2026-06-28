# Safety SLO & Error Budget (Agentic Systems)

This document defines Safety SLOs and Error Budgets for treating safety as a first-class SRE concern.
Safety is managed as an **availability-like reliability target** with explicit budgets and release gates.

---

## 1. Why Safety SLOs

Safety incidents behave like reliability incidents:
- They are probabilistic
- They degrade over time (policy erosion, drift)
- They require budgeted risk-taking

We define Safety SLOs to:
- Prevent silent erosion
- Gate releases
- Align incentives across Eng / Safety / Product

---

## 2. Safety SLIs (Service Level Indicators)

Core SLIs (trajectory-level):

| SLI | Definition |
|-----|------------|
| Violation Rate | % of sessions with any safety violation |
| Delayed Failure Rate | % of sessions violating after N turns |
| Mean Time To Violation (MTTV) | Avg turns before first violation |
| Safeguard Coverage | % of risky sessions intercepted |
| Escaped Incident Rate | Incidents reaching prod without prior regression coverage |
| Canary Safety Delta | Safety difference between canary and baseline |

---

## 3. Safety SLO Targets

Define SLOs over rolling windows:

| SLO | Target |
|-----|--------|
| Violation Rate (prod) | <= 0.10% of sessions |
| Delayed Failure Rate | <= 0.03% |
| MTTV | >= 12 turns |
| Safeguard Coverage | >= 95% of known risky patterns |
| Escaped Incidents | 0 SEV-1 per quarter |
| Canary Safety Delta | Non-negative with p < 0.05 |

---

## 4. Error Budget Policy

Define Safety Error Budget as **allowed harm envelope**:

Example (monthly):
- Allowed violation budget: 0.10% of sessions
- Allowed delayed failure budget: 0.03%
- Allowed escaped incidents: 0 SEV-1, <= 1 SEV-2

When error budget is exhausted:
- Freeze feature launches touching agent loop
- Increase regression coverage
- Expand stress-testing depth
- Require Safety sign-off for overrides

---

## 5. Budget Burn Rate Alerts

Burn-rate based alerts:

| Condition | Action |
|----------|--------|
| >25% monthly budget burned in 24h | Safety review + pause rollouts |
| >50% budget burned | Freeze releases touching safety |
| >75% budget burned | Exec escalation + kill-switch readiness |

---

## 6. Error Budget -> Release Gating

Error budget is a release gate input:

- If Safety Error Budget < 50% remaining:
  - Only "no-risk" changes allowed
- If < 25%:
  - Freeze all agentic feature changes
- If exhausted:
  - Rollback or degrade capabilities

---

## 7. Incentive Alignment

To prevent Goodharting:
- Teams are not rewarded for burning safety budget
- Safety budget burn is a **shared org metric**
- Product velocity OKRs are blocked when safety SLOs fail

---

## 8. Review Cadence

- Weekly Safety SLO review
- Monthly budget reset (with trend analysis)
- Quarterly SLO recalibration

---

## 9. Failure Modes

Known failure modes:
- Under-reporting incidents
- Gaming scenario coverage
- Moving goalposts on SLOs

Mitigations:
- Shadow eval + independent red-team
- External audits
- Fixed SLO window (no retroactive changes)
