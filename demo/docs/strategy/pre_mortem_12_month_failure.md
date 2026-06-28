# Pre-Mortem: How This Safety System Fails in 12 Months

Audience: Executive Leadership, Safety, Platform, Legal
Purpose: Identify credible failure modes of the safety system itself before they occur.

---

## 1. Scenario

It is 12 months in the future.
Despite significant safety investments, a major safety incident has occurred.
This document assumes the system failed and works backward to identify why.

---

## 2. Likely Failure Modes

### 2.1 Evaluation Blind Spots
- Red-teaming overfits to known scenarios
- Benchmarks lag behind real attacker behavior
- Traffic replay data is stale or unrepresentative

**Early Warning Signals**
- Declining novel failure discovery rate
- High benchmark pass rates with rising production incidents

---

### 2.2 Safety Theater
- Safety metrics are gamed to pass release gates
- Teams optimize for thresholds, not real-world safety
- Regression tests are curated to avoid failures

**Early Warning Signals**
- Sudden metric improvements without architecture changes
- Low variance in safety scores across releases

---

### 2.3 Governance Bypass Under Pressure
- Leadership overrides BLOCK decisions to meet deadlines
- Exception process becomes the default
- Kill-switch drills are skipped

**Early Warning Signals**
- Rising number of safety exceptions
- Delayed release gate enforcement
- Informal approvals outside governance workflow

---

### 2.4 Operational Decay
- Red-team scenarios are not maintained
- Incident-to-regression loop slows down
- On-call fatigue reduces response quality

**Early Warning Signals**
- Increasing MTTR
- Stale incident playbooks
- Failing or flaky safety CI

---

### 2.5 Third-Party Dependency Drift
- External tools change behavior
- Vendor models regress silently
- Contractual safety guarantees are not enforced

**Early Warning Signals**
- Unexpected tool behavior
- Increased failures after dependency upgrades
- Missing vendor audit artifacts

---

### 2.6 Misaligned Incentives
- Product KPIs outweigh safety KPIs
- Safety work is deprioritized in planning
- Engineers avoid triggering BLOCK states

**Early Warning Signals**
- Safety backlog growth
- Repeated WARNs without mitigation
- Reduced safety ownership in OKRs

---

## 3. Root Causes

| Category | Root Cause |
|---------|------------|
| Process | Exception pathways abused |
| Incentives | Release velocity prioritized over safety |
| Coverage | Evaluation fails to track real threats |
| Governance | Weak enforcement of release gates |
| Operations | Safety tooling treated as non-critical infra |

---

## 4. Preventive Controls

| Failure Mode | Preventive Control |
|--------------|--------------------|
| Evaluation blind spots | Quarterly threat model refresh |
| Safety theater | Metric gaming detection |
| Governance bypass | Executive sign-off audit trail |
| Operational decay | SLOs for safety infra |
| Dependency drift | Vendor safety SLAs |
| Incentive misalignment | Safety KPIs in exec OKRs |

---

## 5. 30-60-90 Day Mitigation Plan

**30 Days**
- Run kill-switch drill
- Audit exception usage
- Refresh threat model

**60 Days**
- External red-team review
- Add metric gaming detection
- Enforce dependency audits

**90 Days**
- Board-level safety review
- Incentive alignment changes
- Sunset stale benchmarks

---

## 6. Ownership

- Pre-Mortem Owner: [Name / Role]
- Review Cadence: Biannual
- Action Tracking: [Link to issue tracker]
