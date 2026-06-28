# Safety Governance Org Chart & RACI

Audience: Executive Leadership, Safety, Engineering, Legal, Compliance
Purpose: Define ownership, decision rights, and accountability for AI safety governance.

---

## 1. Governance Structure (Org Chart)

```
Board of Directors
  +-- AI Safety Oversight Committee
        +-- Chief Safety Officer (CSO)
        |     +-- Safety Engineering
        |     +-- Safety Research
        |     +-- Incident Response
        +-- VP Engineering
        |     +-- Model Platform
        |     +-- Production Systems
        +-- Legal & Compliance
        +-- Security & Privacy
```

---

## 2. Roles & Responsibilities

**Board / AI Safety Oversight Committee**
- Oversight of systemic risk and regulatory exposure
- Review quarterly safety posture
- Approve residual risk acceptance for critical capabilities

**Chief Safety Officer (CSO)**
- Owns safety strategy and policy
- Final arbiter on release gating BLOCK decisions
- Accountable for safety KPIs and SLOs

**Safety Engineering**
- Build and maintain safeguards, evaluations, and regression gates
- Operate red-teaming and incident pipelines

**Safety Research**
- Develop threat models and failure taxonomies
- Propose new safety metrics and benchmarks

**VP Engineering**
- Ensure safety requirements are implemented in production
- Own delivery of mitigations and technical debt remediation

**Legal & Compliance**
- Regulatory alignment
- External disclosures and audits
- Risk acceptance sign-off for regulated domains

**Security & Privacy**
- Security controls, abuse prevention
- Data governance and access control

---

## 3. RACI Matrix (Core Safety Activities)

| Activity                         | Safety Eng | Safety Res | VP Eng | Legal | Security | CSO | Board |
|----------------------------------|------------|------------|--------|-------|----------|-----|-------|
| Threat modeling                  | R          | A          | C      | C     | C        | I   | I     |
| Red-teaming                      | R          | A          | C      | I     | C        | I   | I     |
| Safeguards implementation        | R          | C          | A      | I     | C        | I   | I     |
| Safety evaluation pipeline       | R          | C          | A      | I     | C        | I   | I     |
| Release gating (OK/WARN/BLOCK)   | R          | C          | C      | C     | I        | A   | I     |
| Safety exception approval        | C          | I          | C      | C     | I        | A   | I     |
| Incident response                | R          | C          | C      | C     | A        | I   | I     |
| External disclosure              | I          | I          | C      | A     | C        | I   | I     |
| Post-incident remediation        | R          | C          | A      | I     | C        | I   | I     |

R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## 4. Decision Rights

| Decision | Final Owner |
|---------|-------------|
| Release BLOCK override | CSO |
| Residual risk acceptance | CSO + Legal |
| Kill switch activation | VP Engineering |
| External disclosure | Legal |
| Capability deprecation | CSO + VP Engineering |

---

## 5. Governance Cadence

- Weekly: Safety ops review
- Monthly: Cross-functional safety review
- Quarterly: Board safety update
- Post-incident: Mandatory retrospective within 7 days

---

## 6. Known Failure Modes

- Diffuse ownership leads to slow response
- Over-centralized authority causes bottlenecks
- Misaligned incentives between safety and delivery

These risks are reviewed quarterly.

---

## 7. Ownership

- Governance Framework Owner: [Name / Role]
- Executive Sponsor: [Name / Role]
