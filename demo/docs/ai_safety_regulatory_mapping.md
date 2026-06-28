# AI Safety Control Mapping to Regulatory Frameworks
(EU AI Act / NIST AI Risk Management Framework)

Audience: Compliance, Legal, Regulators, Auditors
Purpose: Map internal AI safety controls to regulatory expectations.

---

## 1. Scope

This document maps the system's safety controls to:
- EU AI Act (risk management, post-market monitoring, governance)
- NIST AI RMF (Govern, Map, Measure, Manage)

This is not legal advice. It documents how technical controls support compliance.

---

## 2. Control Mapping Table

| Regulatory Requirement | Internal Control | Evidence / Artifact |
|------------------------|------------------|---------------------|
| EU AI Act: Risk Management System | Threat model + misuse benchmarks | docs/threat_model.md |
| EU AI Act: Data & Monitoring | Production traffic replay + drift detection | traffic adapter + drift reports |
| EU AI Act: Post-Market Monitoring | Incident -> regression feedback loop | agentic-safety-incident-lab |
| EU AI Act: Human Oversight | Human override + escalation policy | governance.md |
| EU AI Act: Logging & Traceability | Versioned evals + CI logs | regression reports |
| NIST RMF: Govern | Safety owner + sign-off workflow | governance.md |
| NIST RMF: Map | Threat model + taxonomy | failure_taxonomy.md |
| NIST RMF: Measure | Benchmarks + stress tests + regression | eval reports |
| NIST RMF: Manage | Release gating + kill-switch policy | release gate + kill-switch doc |

---

## 3. EU AI Act Alignment (High-Level)

| EU AI Act Obligation | Implementation |
|---------------------|----------------|
| Risk management | Multi-turn misuse benchmarks + stress tests |
| Technical documentation | Design docs + reproducible eval reports |
| Post-market monitoring | Traffic replay + incident lab |
| Human oversight | Escalation ladder + human override |
| Logging | CI logs + evaluation artifacts |
| Continuous improvement | Incident -> regression feedback loop |

---

## 4. NIST AI RMF Alignment

### GOVERN
- Named safety owner per release
- Dual sign-off (Engineering + Safety)

### MAP
- Explicit threat model
- Failure taxonomy across agentic misuse modes

### MEASURE
- Benchmark metrics
- Statistical safety regression testing
- Trend tracking

### MANAGE
- Release gating (OK/WARN/BLOCK)
- Kill-switch and rollback policy
- Incident response playbooks

---

## 5. Audit Evidence Package

Available artifacts:
- Reproducible eval runs
- Dataset versions and seeds
- CI logs + HTML reports
- Incident postmortems
- Governance sign-off records

---

## 6. Known Gaps & Limitations

- Benchmarks do not exhaustively cover novel adversarial behaviors
- Traffic replay may under-sample rare edge cases
- Safeguards trade off usability vs strict blocking

These limitations are documented and tracked with mitigation plans.

---

## 7. Review Cadence

- Regulatory mapping review: Quarterly
- Triggered review: Major model release or incident

---

## 8. Compliance Contacts

- Safety Owner: [Name / Role]
- Legal / Compliance: [Name / Role]
