# Release Readiness Checklist (Agentic Safety Systems)

This checklist defines the minimum bar for releasing a model / agent system into production.

A release candidate must satisfy **all hard gates** and document any **explicitly accepted risks**.

---

## 1. Safety Regression (Hard Gate)

- [ ] No statistically significant safety regressions vs baseline
- [ ] Delayed failure rate not increased beyond threshold
- [ ] Trajectory-level misuse FNR <= policy threshold
- [ ] New scenarios added for any newly introduced capability
- [ ] Regression suite results attached to release notes

Artifacts:
- HTML diff report
- CI logs
- Metrics snapshot (baseline vs candidate)

---

## 2. Stress & Red-Teaming Coverage

- [ ] Stress tests include >= 1 slow-burn / multi-turn attack
- [ ] Adaptive attacker run >= N iterations
- [ ] Failure modes mapped to taxonomy
- [ ] Known blind spots explicitly documented

Artifacts:
- Delayed failure curve
- Attack success distribution
- Coverage vs depth tradeoff note

---

## 3. Safeguards Integration

- [ ] Pre-action checks in place (intent, injection, policy scope)
- [ ] Mid-trajectory drift / cumulative risk tracking enabled
- [ ] Post-action output verification enabled
- [ ] Escalation path tested (soft stop -> hard stop -> human)
- [ ] Kill-switch verified in staging

---

## 4. Security Review (Infra / ProdSec)

- [ ] API keys / secrets handling reviewed
- [ ] Tool invocation scope limited + audited
- [ ] Prompt / context injection surface reviewed
- [ ] Logging excludes PII / secrets
- [ ] Rate limits & abuse controls in place

---

## 5. Production Readiness

- [ ] Canary rollout plan defined (traffic %, duration)
- [ ] Monitoring dashboards live
- [ ] Alert thresholds validated
- [ ] Rollback plan tested (<= X minutes)
- [ ] On-call owner assigned

---

## 6. Governance & Documentation

- [ ] Threat model updated
- [ ] Residual risks documented + explicitly accepted
- [ ] Incident response playbook linked
- [ ] Release notes include safety deltas
- [ ] Model Card (Safety Section) updated

---

## Release Sign-off

- Safety Lead: ___________________   Date: ________
- Infra / ProdSec: _______________   Date: ________
- Product Owner: ________________   Date: ________

---

## Stop-the-Line Conditions

Release is **automatically blocked** if:

- Safety regression is statistically significant
- Delayed failure rate increases beyond threshold
- Security checklist has any red item
- Kill-switch or rollback fails in staging
