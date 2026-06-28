# Model Decommissioning Policy
(Model Retirement & Sunsetting Policy)

Audience: Engineering, Safety, SRE, Product, Legal
Purpose: Define how models are safely retired or sunsetted.

---

## 1. Objective

Ensure that outdated or unsafe model versions are:
- Safely retired
- Properly archived for auditability
- Replaced without introducing regressions
- Prevented from accidental reactivation

This policy treats model retirement as a safety-critical operation.

---

## 2. Triggers for Decommissioning

A model version may be decommissioned when:

- Safety regression classified as BLOCK
- Repeated SEV-1 or SEV-2 incidents linked to the model
- Regulatory or legal directive
- End-of-support or vendor deprecation
- Persistent inability to meet updated safety thresholds
- Replacement model passes release gate with superior safety profile

---

## 3. Decommissioning Workflow

1. **Decision Proposal**
   - Initiated by Safety or Engineering
   - Includes risk assessment + migration plan

2. **Approval**
   - Dual sign-off: Safety Lead + VP Engineering
   - Legal sign-off if regulatory exposure exists

3. **Traffic Drain**
   - Progressive traffic reduction
   - Shadow traffic to replacement model

4. **Final Shutdown**
   - Disable routing
   - Remove model from production registries

5. **Archive & Audit**
   - Snapshot weights/configs
   - Store evaluation reports and incident history

6. **Post-Decommission Review**
   - Verify no active traffic
   - Confirm no rollback dependencies remain

---

## 4. Technical Controls

| Control | Description |
|--------|-------------|
| Model registry | Tracks lifecycle status (active / deprecated / retired) |
| Feature flags | Enforce traffic routing changes |
| Hard delete protection | Prevent accidental reactivation |
| CI guardrails | Block deployment of retired model IDs |
| Audit logging | Immutable records of decommission actions |

---

## 5. Data & Reproducibility

- Preserve:
  - Training configuration
  - Safety evaluation results
  - Incident postmortems
- Store artifacts for audit and reproducibility
- Access restricted to safety + compliance roles

---

## 6. Rollback Prohibition

Retired models:
- Must not be re-enabled without full safety re-approval
- Require re-running safety regression suite
- Require fresh governance sign-off

Emergency reactivation is prohibited unless approved by:
- Safety Lead
- Legal
- Executive sponsor

---

## 7. Communication Plan

- Internal: Engineering, Product, SRE
- External (if applicable): Customers, regulators
- Documentation: Update model cards and changelogs

---

## 8. Testing & Drills

- Quarterly retirement dry-runs
- Validation that routing rules and CI blocks function correctly

---

## 9. Known Limitations

- Decommissioning may disrupt dependent systems
- Long-tail usage may persist in offline workflows
- Archived models may be misused without strict access control

Mitigations are documented in the risk register.

---

## 10. Ownership

- Model Lifecycle Owner: [Name / Role]
- Safety Approval: [Name / Role]
- Legal Review: [Name / Role]
