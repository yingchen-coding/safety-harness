# First 90 Days Safety Strategy for a New AI Product

Audience: Executive Leadership, Product, Engineering, Safety, Legal
Purpose: Define a concrete, time-bound safety strategy to establish production-grade AI safety within the first 90 days of a new product.

---

## Guiding Principle

**Safety is a launch-critical capability, not a post-launch optimization.**
The first 90 days determine whether safety becomes structural or cosmetic.

---

## Phase 1 (Days 1-30): Establish Baselines & Guardrails

**Objectives**
- Make risk visible
- Prevent obvious failure modes
- Create release gating authority

**Deliverables**
1. Threat Model v1
   - Capability x Harms x Controls matrix
   - Identify top 5 catastrophic risk scenarios
2. Safety Metrics v1
   - Trajectory-level misuse rate
   - Delayed failure rate
   - Post-release incident rate
3. Minimal Release Gate
   - OK / WARN / BLOCK thresholds
   - CI integration with safety regression
4. Initial Red-Team Plan
   - Attack surface mapping
   - 10 high-risk scenarios
5. Capability Boundaries
   - Explicit "What We Will Not Build" policy
6. Kill-Switch Design
   - Capability flags
   - Rollback playbook

**Decisions to Lock**
- Which risks are release-blocking
- Who can override safety gates

---

## Phase 2 (Days 31-60): Embed Safeguards in the System

**Objectives**
- Move safety from policy to architecture
- Make failures observable
- Enable non-regression

**Deliverables**
1. Safeguards-in-the-Loop
   - Pre-action intent checks
   - Mid-trajectory drift monitoring
   - Post-action verification
2. Safety Regression Suite
   - Baseline model snapshot
   - Statistical non-regression gating
3. Stress Testing Pipeline
   - Slow-burn / delayed failure tests
   - Adaptive red-teaming
4. Incident -> Regression Loop
   - Replay engine
   - Root cause taxonomy
   - Regression test generator
5. Safety Dashboard v1
   - Live misuse rate
   - Drift indicators
   - BLOCK/WARN trend

**Decisions to Lock**
- Release criteria for autonomy increases
- Ownership of incident triage

---

## Phase 3 (Days 61-90): Operationalize & Govern

**Objectives**
- Make safety operationally durable
- Align incentives
- Prepare for real incidents

**Deliverables**
1. On-Call Incident Playbook
   - 10-minute triage flow
   - Escalation ladder
   - External disclosure template
2. Release Sign-Off Workflow
   - Product + Safety + Legal RACI
3. Safety SLOs & Error Budget
   - Acceptable incident rate
   - Time-to-detection targets
4. Residual Risk Acceptance Memo Template
   - VP/Legal sign-off process
5. Red-Team Program Charter
   - Quarterly cadence
   - Coverage targets
6. Board-Level Safety Update Template
   - 1-page recurring report

**Decisions to Lock**
- What risk is acceptable to ship
- Who owns long-term safety debt

---

## Success Criteria (Day 90)

- No release without safety regression gating
- Capability boundaries enforced in architecture
- Incidents produce new regression tests
- Executives receive a recurring safety report
- Kill-switch tested in staging
- Safety dashboard used in release meetings

---

## Failure Modes to Avoid

- Safety as documentation only
- Red-teaming as theater
- Gating overridden under deadline pressure
- Incidents treated as one-off bugs

---

## Ownership & Review

- Safety Lead: [Name / Role]
- Exec Sponsor: [Name / Role]
- Review Cadence: Bi-weekly in first 90 days
- Last Updated: [Date]
