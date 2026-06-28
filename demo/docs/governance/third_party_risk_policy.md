# Third-Party Model / Tool Risk Policy
(External Dependency Safety & Risk Governance)

Audience: Safety, Engineering, Procurement, Legal
Purpose: Govern the introduction and use of third-party models, tools, and services in safety-critical systems.

---

## 1. Objective

Ensure that external dependencies do not introduce unacceptable safety, security, or compliance risks.

All third-party models, APIs, tools, and datasets must undergo risk assessment prior to production use.

---

## 2. Scope

This policy applies to:

- Third-party foundation models
- External APIs used by agents
- Plugins and tools with execution privileges
- Data sources integrated into model workflows

---

## 3. Pre-Integration Risk Assessment

Each third-party dependency must be evaluated for:

- Safety posture and known failure modes
- Data handling and privacy practices
- Security guarantees
- Regulatory compliance
- Model card and documentation availability
- Incident history (if public)
- Update and deprecation policy

---

## 4. Risk Classification

| Risk Level | Criteria | Allowed Use |
|------------|----------|-------------|
| Low | Strong safety documentation, no execution privileges | Production |
| Medium | Partial safety controls, limited execution | Production with safeguards |
| High | Opaque safety posture, broad execution | Restricted / sandbox only |
| Critical | Unknown provenance, unsafe defaults | Prohibited |

---

## 5. Required Safeguards

| Risk Level | Mandatory Controls |
|------------|--------------------|
| Low | Monitoring, regression tests |
| Medium | Allowlisting, sandboxing, logging |
| High | Strict isolation, manual approval gates |
| Critical | Block integration |

---

## 6. Continuous Monitoring

- Shadow evaluations on external models
- Drift detection on third-party behavior
- Contractual SLAs on safety updates
- Automatic alerts on API behavior changes

---

## 7. Dependency Lifecycle Management

- Version pinning
- Scheduled re-evaluations
- Decommissioning plan
- Kill-switch integration
- Traffic isolation for high-risk dependencies

---

## 8. Incident Response

If a third-party dependency is implicated in an incident:

- Immediate isolation
- Blast radius analysis
- Vendor notification (if applicable)
- Temporary suspension pending review

---

## 9. Procurement & Legal Controls

- Security and safety clauses in vendor contracts
- Right-to-audit provisions
- Breach notification SLAs
- Termination clauses for safety violations

---

## 10. Known Limitations

- Limited visibility into proprietary models
- Delayed disclosure of vendor incidents
- Risk of silent behavior changes

Mitigations include isolation, monitoring, and staged rollout.

---

## 11. Ownership

- Third-Party Risk Owner: [Name / Role]
- Safety Review Committee: [Roles]
- Legal & Procurement: [Roles]
