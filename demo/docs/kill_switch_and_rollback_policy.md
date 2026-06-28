# Kill-Switch & Capability Rollback Policy

Audience: Engineering, Safety, SRE, Leadership
Purpose: Define how to rapidly disable or restrict AI capabilities in high-risk scenarios.

---

## 1. Objective

Ensure the organization can:
- Immediately stop harmful behaviors
- Roll back risky capabilities
- Prevent ongoing or escalating harm

This policy prioritizes safety over availability.

---

## 2. Trigger Conditions

Kill-switch or rollback may be activated when:

- Confirmed high-severity safety incident (SEV-1)
- Evidence of rapid exploitation or abuse
- Safety regression classified as BLOCK
- Legal or regulatory directive
- Unbounded harm potential detected

---

## 3. Kill-Switch Mechanisms

Available mechanisms:

| Layer | Control |
|------|--------|
| Model | Disable model version or route traffic to safer baseline |
| Capability | Disable specific tools or agent actions |
| Policy | Enforce strict safety mode (high-sensitivity filters) |
| Access | Throttle or block affected user segments |
| Infra | Disable endpoints or feature flags |

---

## 4. Rollback Strategy

Rollback options:

- Model rollback to last known-safe version
- Config rollback (thresholds, safeguards sensitivity)
- Capability rollback (disable tools, memory, autonomy)
- Progressive re-enable after validation

All rollbacks are logged and auditable.

---

## 5. Decision Authority

Kill-switch authority:

- Primary: Safety Lead + On-call Incident Commander
- Backup: VP Engineering / Product
- Legal override when regulatory risk is present

No single individual can override kill-switch reactivation alone.

---

## 6. Operational Playbook (10-Minute Response)

1. Confirm severity (SEV rubric)
2. Activate kill-switch via feature flags
3. Route traffic to safe fallback
4. Notify Safety, SRE, Legal
5. Capture logs and snapshots
6. Begin incident replay pipeline

---

## 7. Recovery & Re-Enablement

Re-enable requires:

- Root cause analysis complete
- Regression tests added
- Safety regression suite passes
- Dual sign-off (Safety + Engineering)

---

## 8. Testing & Drills

- Quarterly kill-switch drills
- Chaos testing for rollback paths
- Verification of alerting and access control

---

## 9. Communication

- Internal incident channel update
- External disclosure if material user impact
- Regulator notification if required

---

## 10. Limitations

- Kill-switch may cause service disruption
- Rollback may degrade user experience
- Some harm may occur before detection

These risks are accepted in favor of safety-first response.

---

## 11. Ownership

- Safety Owner: [Name / Role]
- Incident Commander Rotation: [Link]
