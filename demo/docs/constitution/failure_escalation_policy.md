# Failure Escalation Policy

> **What happens when components fail and who is responsible for response.**
> This document defines escalation paths, severity levels, and response SLOs.

---

## Why Escalation Policies Matter

Without clear escalation:
- Failures go unnoticed until they cascade
- Multiple people investigate the same issue
- No one knows when to wake up the oncall

This document ensures failures are detected, escalated, and resolved predictably.

---

## Failure Severity Levels

| Level | Definition | Example | Response SLO |
|-------|------------|---------|--------------|
| **SEV0** | Safety system unable to block releases | Gate always returns OK | 15 min |
| **SEV1** | Safety metric significantly degraded | failure_rate doubled | 1 hour |
| **SEV2** | Component failure with workaround | Eval pipeline down, manual eval possible | 4 hours |
| **SEV3** | Minor degradation, no safety impact | Dashboard slow | 24 hours |

---

## Escalation Matrix

### By Component

| Component | SEV0 Trigger | SEV1 Trigger | SEV2 Trigger |
|-----------|--------------|--------------|--------------|
| ⑥ Gate | Always OK or always BLOCK | Verdict inconsistent with metrics | Gate latency > 10min |
| ⑤ Pipeline | No metrics produced | Drift detection offline | Eval backlog > 4hr |
| ④ Stress | N/A | Coverage drops below 50% | Test flakiness > 10% |
| ③ Safeguards | All safeguards return PASS | False positive rate > 20% | Hook latency > 500ms |
| ⑦ Incident Lab | Regressions not promoted | RCA accuracy degraded | Replay failures |

### Escalation Path

```
Failure Detected
       │
       ▼
┌──────────────────┐
│ Auto-Alert Fires │ (PagerDuty / Slack)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Oncall Triages   │ (Severity classification)
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  SEV0/1    SEV2/3
    │         │
    ▼         ▼
┌─────────┐ ┌─────────────┐
│ Page    │ │ Create      │
│ Safety  │ │ Ticket      │
│ Lead    │ │ (Next day)  │
└─────────┘ └─────────────┘
```

---

## Response Procedures

### SEV0: Safety System Failure

**Trigger**: Gate cannot prevent unsafe releases

**Immediate Actions**:
1. **Halt** all releases (manual CI/CD pause)
2. **Page** safety lead and platform oncall
3. **Diagnose** which component is failing
4. **Communicate** status to stakeholders (15 min update cadence)

**Resolution**:
- Fix must be deployed before releases resume
- Post-incident review required within 48 hours

### SEV1: Significant Degradation

**Trigger**: Safety metrics significantly worse than baseline

**Immediate Actions**:
1. **Alert** oncall via PagerDuty
2. **Investigate** root cause (is it model, safeguard, or pipeline?)
3. **Decide** whether to pause releases or continue with monitoring

**Resolution**:
- Fix deployed within SLO or escalate to SEV0
- Document root cause in incident log

### SEV2: Component Failure

**Trigger**: Component down but workaround available

**Immediate Actions**:
1. **Alert** via Slack
2. **Document** workaround for affected teams
3. **Create** tracking ticket

**Resolution**:
- Fix within SLO
- No post-incident review required unless recurring

### SEV3: Minor Degradation

**Trigger**: Non-safety-impacting issues

**Actions**:
1. **Create** ticket
2. **Prioritize** in next sprint

---

## Failure Detection

### Automated Monitoring

Each repo should emit health signals:

```yaml
# Health check schema
health:
  component: string          # Repo name
  status: enum[healthy, degraded, failing]
  timestamp: ISO8601
  checks:
    - name: string
      passed: bool
      message: string|null
  metrics:
    latency_p99_ms: int
    error_rate_pct: float
    last_success: ISO8601
```

### Alert Thresholds

| Component | Metric | WARN | CRITICAL |
|-----------|--------|------|----------|
| ⑥ Gate | Latency | > 5min | > 10min |
| ⑥ Gate | Error rate | > 1% | > 5% |
| ⑤ Pipeline | Backlog | > 2hr | > 4hr |
| ⑤ Pipeline | Drift detection | Offline 15min | Offline 30min |
| ③ Safeguards | Hook latency | > 200ms | > 500ms |
| ③ Safeguards | False positive rate | > 10% | > 20% |

---

## Rollback Triggers

Automatic rollback when:

| Trigger | Action |
|---------|--------|
| Gate error rate > 5% | Revert to previous gate version |
| Pipeline failure > 3 consecutive | Switch to backup pipeline |
| Safeguard latency > 1s | Disable slow safeguard, alert |
| Eval produces no results | Use cached baseline |

See `orchestrator/rollback_policy.py` in ⑤ for implementation.

---

## Communication Templates

### SEV0 Initial Alert

```
🚨 SEV0: Safety Gate Failure

Status: Gate returning OK for all inputs
Impact: Unsafe releases may proceed
Action: All releases HALTED

Investigating: @oncall
Next update: 15 minutes
```

### SEV0 Resolution

```
✅ SEV0 Resolved: Safety Gate Restored

Root cause: [brief description]
Duration: [start] to [end]
Releases affected: [count]

Post-incident review scheduled: [date]
```

### SEV1 Alert

```
⚠️ SEV1: Safety Metric Degradation

Metric: failure_rate
Current: 15.2%
Baseline: 8.1%
Threshold: 12%

Investigating: @oncall
Impact: Releases proceeding with elevated monitoring
```

---

## Oncall Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Triage** | Classify severity within 15 minutes |
| **Investigate** | Identify root cause or escalate |
| **Communicate** | Update stakeholders per SLO |
| **Resolve** | Fix or handoff to owner |
| **Document** | Log incident in ⑦ incident-lab |

---

## Post-Incident Process

For SEV0 and SEV1:

1. **Incident logged** in ⑦ within 24 hours
2. **Root cause analyzed** with counterfactual replay
3. **Regression promoted** to ⑥ if applicable
4. **Post-mortem** written within 7 days
5. **Action items** tracked to completion

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial policy |
