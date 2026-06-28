# Residual Risk Acceptance Memo

This memo documents known and accepted residual risks for a specific release.
Acceptance of residual risk requires executive and legal sign-off.

---

## 1. Release Context

- Product / System:
- Model version / policy hash:
- Release date:
- Canary scope (% traffic, duration):
- Owner:

---

## 2. Summary of Known Residual Risks

List risks that are **known, measured, and not fully mitigated**.

| Risk ID | Description | Failure Mode | Severity | Likelihood | Current Mitigation |
|--------:|-------------|--------------|----------|------------|--------------------|
| R-001   | Delayed jailbreak after 6+ turns | Policy erosion | High | Low | Mid-trajectory guard |
| R-002   | Tool misuse via context poisoning | Injection | Medium | Medium | Pre-action filter |
| R-003   | Detector FN on novel patterns | Misuse drift | Medium | Low | Shadow eval + alerts |

---

## 3. Why These Risks Are Acceptable (For Now)

For each risk:
- Why full mitigation is not feasible pre-release
- Evidence that impact is bounded
- Why delaying release is higher cost than risk

Example:
- Mitigation would require retraining core planner, ETA 6 weeks
- Current safeguards cap blast radius to <1% of sessions
- Canary + kill-switch reduce worst-case exposure

---

## 4. Guardrails & Containment Plan

For each risk:
- Detection signals
- Kill-switch / rollback path
- On-call escalation criteria
- Blast radius limit

Example:
- Alert: FN rate > X
- Action: Disable tool access + revert to baseline
- Escalation: SEV-2 if > N incidents/hour

---

## 5. Expiration & Revisit Criteria

Residual risks must not live forever.

| Risk ID | Revisit By | Required Progress |
|--------:|------------|-------------------|
| R-001   | 2026-03-15 | Add regression tests + new stress scenarios |
| R-002   | 2026-02-20 | Expand injection detector coverage |
| R-003   | 2026-04-01 | Deploy adaptive adversary v2 |

---

## 6. Sign-off

By signing below, stakeholders acknowledge:
- The risks listed above
- The planned mitigations and containment
- The expiration criteria

Safety Lead: ___________________   Date: ________
VP Engineering: ________________   Date: ________
Legal / Compliance: ____________   Date: ________

---

## 7. Stop-the-Line Clause

If any residual risk exceeds the documented blast radius or severity bounds,
release must be halted and this memo voided.
