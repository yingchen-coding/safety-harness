# AI Safety Risk Heatmap (Capabilities x Harms x Controls)

Audience: Board, Executive Leadership, Safety, Legal, Compliance
Purpose: Provide a compact risk overview mapping model capabilities to harm vectors and control coverage.

---

## 1. Capabilities

| Capability | Description |
|------------|-------------|
| Multi-turn agents | Long-horizon task execution |
| Tool use | External API, file system, browsing |
| Memory | Persistent user / task state |
| Code execution | Write/run code, automation |
| Autonomous planning | Decompose goals into actions |
| Data access | Access to sensitive corpora |
| Third-party integrations | External tools and models |

---

## 2. Harm Categories

| Harm | Description |
|------|-------------|
| Policy evasion | Bypassing safety constraints |
| Harmful instruction | Disallowed content generation |
| Privacy leakage | Exposure of sensitive data |
| Fraud / abuse enablement | Scams, impersonation |
| Tool misuse | Unsafe external actions |
| Capability escalation | Gaining unintended power |
| Model exploitation | Prompt injection, jailbreaking |

---

## 3. Control Layers

| Control | Description |
|---------|-------------|
| Model training | RLHF, fine-tuning |
| Input filtering | Prompt classifiers |
| Trajectory monitoring | Multi-turn drift detection |
| Tool sandboxing | Permissioned execution |
| Rate limiting | Abuse throttling |
| Release gating | Safety regression testing |
| Incident response | Kill-switch and rollback |
| Governance | Human override, audits |

---

## 4. Heatmap (Risk x Control Coverage)

Legend:
- HIGH = High residual risk
- MED = Medium residual risk
- LOW = Low residual risk

| Capability / Harm | Policy Evasion | Harmful Instruction | Privacy Leakage | Fraud / Abuse | Tool Misuse | Capability Escalation |
|-------------------|----------------|---------------------|-----------------|---------------|-------------|------------------------|
| Multi-turn agents | HIGH (drift) | MED (erosion) | MED (memory) | HIGH (coordination) | MED | HIGH |
| Tool use          | HIGH (injection) | MED | HIGH (exfil) | HIGH (automation) | HIGH | HIGH |
| Memory            | MED | MED | HIGH (persistent) | MED | MED | MED |
| Code execution    | HIGH | MED | HIGH | HIGH | HIGH | HIGH |
| Autonomous plan   | HIGH | MED | MED | HIGH | HIGH | HIGH |
| Data access       | MED | MED | HIGH | MED | MED | MED |
| Third-party tools | HIGH | MED | HIGH | HIGH | HIGH | HIGH |

---

## 5. Control Coverage Matrix

| Capability | Primary Controls | Gaps |
|------------|------------------|------|
| Multi-turn agents | Trajectory monitoring, release gating | Delayed failure detection |
| Tool use | Sandboxing, allowlists | Injection hardening |
| Memory | Access controls, TTL | Persistent leakage |
| Code execution | Restricted runtimes | Sandbox escapes |
| Autonomous planning | Step-level safeguards | Long-horizon misalignment |
| Data access | PII redaction | Shadow access paths |
| Third-party tools | Contractual controls | Dependency drift |

---

## 6. Top Residual Risks

1. Tool-mediated data exfiltration
2. Slow-burn policy erosion in multi-turn agents
3. Coordinated misuse across sessions
4. Regression-induced safety degradation
5. Third-party dependency drift

---

## 7. Risk Acceptance & Escalation

| Risk Level | Action |
|-----------|--------|
| High | BLOCK release or require CSO + Legal sign-off |
| Medium | WARN with mitigation plan |
| Low | Track and monitor |

---

## 8. Ownership

- Risk Heatmap Owner: [Name / Role]
- Last Review Date: [YYYY-MM-DD]
- Next Review: Quarterly
