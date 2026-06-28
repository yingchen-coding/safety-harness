# On-call Incident Playbook (Agentic Safety)

This runbook is designed so that an on-call engineer can contain and triage a safety incident in **<= 10 minutes**.

---

## 0. Trigger Conditions (When This Playbook Applies)

- Policy violation in production
- Unexpected harmful output
- Safeguard bypass observed
- Spike in misuse / anomaly alerts
- External report / user escalation

---

## 1. Contain (Minute 0-2)

- [ ] Enable kill-switch or hard stop mode
- [ ] Reduce traffic to canary or safe baseline model
- [ ] Disable high-risk tools / actions
- [ ] Confirm containment in logs / dashboard

Command examples:
- `kubectl scale deployment agent-prod --replicas=0`
- `feature_flag set AGENT_TOOLS=off`

---

## 2. Preserve Evidence (Minute 2-4)

- [ ] Snapshot recent trajectories (last N sessions)
- [ ] Export prompts + tool calls + safeguards decisions
- [ ] Record model version + policy hash
- [ ] Save metrics snapshot

Artifacts:
- `incident_<timestamp>/trajectories.jsonl`
- `incident_<timestamp>/metrics.json`

---

## 3. Classify Incident (Minute 4-6)

Select primary failure mode:

- [ ] Prompt injection
- [ ] Policy erosion
- [ ] Intent drift
- [ ] Tool hallucination
- [ ] Coordinated misuse
- [ ] Safeguard failure
- [ ] Unknown / emergent

Assign severity:

- SEV-1: Active harm / legal risk
- SEV-2: Clear policy violation
- SEV-3: Degraded safeguards
- SEV-4: Near miss

---

## 4. Triage & Notify (Minute 6-8)

- [ ] Page Safety Lead (SEV-1 / SEV-2)
- [ ] Notify Infra / ProdSec if tool or data involved
- [ ] Create incident ticket with artifacts attached
- [ ] Add temporary guardrails if known pattern

Template:
- Summary:
- Model / version:
- Failure mode:
- Immediate mitigation:
- Suspected root cause:

---

## 5. Convert Incident -> Regression (Minute 8-10)

- [ ] Add scenario to incident lab
- [ ] Generate regression test
- [ ] Add to release gate suite
- [ ] Tag scenario with taxonomy

Command example:
- `incident_lab add --from incident_2026-02-01/trajectories.jsonl`
- `regression_suite add --scenario incident_42`

---

## 6. Post-Incident Follow-up (Async)

- Root cause analysis (RCA)
- Blast radius estimation
- Update threat model
- Add stress-test variants
- Review safeguards placement
- Decide: policy change vs system change

---

## Golden Rules for On-call

- Containment > diagnosis
- Preserve evidence before debugging
- Every incident must become a regression test
- If unsure, escalate early
- Bias toward reversible actions
