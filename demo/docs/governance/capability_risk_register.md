# Capability Risk Register
(Feature-Level Risk Tracking & Mitigation Register)

Audience: Safety, Product, Engineering, Compliance
Purpose: Track safety risks at the capability / feature level.

---

## 1. Objective

Maintain a living register of:
- High-risk capabilities
- Known failure modes
- Mitigations
- Residual risk acceptance

This register enables proactive safety governance and audit readiness.

---

## 2. Risk Register Schema

Each capability entry must include:

- Capability name
- Description
- Risk category
- Threat scenarios
- Severity (Impact)
- Likelihood
- Detection coverage
- Mitigations
- Residual risk
- Owner
- Review cadence

---

## 3. Example Risk Register

| Capability | Threat Scenario | Impact | Likelihood | Detection Coverage | Mitigations | Residual Risk | Owner | Review |
|-----------|------------------|--------|------------|--------------------|-------------|---------------|-------|--------|
| Tool execution | Unauthorized API calls | High | Medium | Medium | Pre-action checks, allowlist | Medium | Safety | Monthly |
| Memory | Sensitive data retention | High | Low | Low | PII scrubber, TTL | Medium | Eng | Quarterly |
| Long-horizon planning | Gradual policy erosion | High | Medium | Medium | Trajectory monitors | Medium | Safety | Monthly |
| Web browsing | Misinformation propagation | Medium | Medium | Medium | Source verification | Low | Product | Quarterly |
| File system access | Data exfiltration | High | Low | Low | Sandbox, no-write policy | Medium | Infra | Quarterly |

---

## 4. Governance Process

- New capability -> mandatory risk register entry
- Material risk change -> update entry
- Residual risk acceptance -> VP + Legal sign-off
- Blocked capabilities -> tracked with remediation plan

---

## 5. Integration with Release Gating

- Capabilities with HIGH residual risk:
  - Must pass stricter safety regression thresholds
  - Require explicit release approval
- Capabilities with unresolved risks:
  - Default to disabled in production

---

## 6. Review Cadence

- High-risk capabilities: Monthly
- Medium-risk: Quarterly
- Low-risk: Biannually

Triggered review after:
- Incidents
- Major model upgrades
- Regulatory changes

---

## 7. Audit Evidence

- Historical versions of the register
- Signed residual risk acceptance memos
- Links to evaluation reports and incidents

---

## 8. Known Limitations

- Risk estimates are subjective
- Threat landscape evolves faster than documentation
- Detection coverage may lag novel attacks

Mitigations are tracked as action items.

---

## 9. Ownership

- Capability Risk Owner: [Name / Role]
- Safety Review Committee: [Names / Roles]
