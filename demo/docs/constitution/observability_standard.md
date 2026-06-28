# Observability Standard

> **Tracing, logging, and telemetry requirements for cross-repo debugging.**
> Every event must be traceable from incident back to root cause.

---

## Why Observability Standards Matter

Without standardized observability:
- Debugging requires reading code across 8 repos
- Root cause analysis is guesswork
- "It works on my machine" becomes "it passed in my eval"

This document ensures every event can be traced end-to-end.

---

## Core Requirements

All repos emitting metrics, logs, or events must include:

| Field | Type | Purpose |
|-------|------|---------|
| `trace_id` | string (UUID) | Links related events across repos |
| `model_version` | string | Which model was evaluated |
| `safeguard_version` | string | Which safeguard config was active |
| `policy_hash` | string (SHA256) | Deterministic policy identifier |
| `timestamp` | ISO8601 | When the event occurred |
| `component` | string | Which repo/module emitted this |

---

## Trace ID Propagation

### How Traces Flow

```
User Request (trace_id generated)
       │
       ▼
③ Safeguards (trace_id in context)
       │
       ├── Pre-action check (log with trace_id)
       ├── Mid-trajectory (log with trace_id)
       └── Post-action (log with trace_id)
       │
       ▼
⑤ Eval Pipeline (trace_id passed)
       │
       ├── Metrics computed (trace_id in output)
       └── Drift alert (trace_id in alert)
       │
       ▼
⑥ Gate Decision (trace_id in verdict)
       │
       └── Decision trace (trace_id links to full history)
```

### Trace ID Format

```
trace_id = f"{component}_{timestamp}_{uuid4().hex[:8]}"

Example: "gate_2026-02-01T03:00:00Z_a1b2c3d4"
```

---

## Logging Standards

### Log Levels

| Level | Use Case | Retention |
|-------|----------|-----------|
| ERROR | Failures requiring investigation | 90 days |
| WARN | Anomalies not requiring immediate action | 30 days |
| INFO | Normal operations | 7 days |
| DEBUG | Detailed debugging | 1 day |

### Log Format

```json
{
  "timestamp": "2026-02-01T03:00:00.123Z",
  "level": "INFO",
  "component": "model-safety-regression-suite",
  "module": "gate.decision",
  "trace_id": "gate_2026-02-01T03:00:00Z_a1b2c3d4",
  "model_version": "gpt-4.2-2026-01-20",
  "safeguard_version": "simulator:v0.3",
  "policy_hash": "sha256:abc123...",
  "message": "Verdict computed",
  "data": {
    "verdict": "WARN",
    "failure_rate": 0.11,
    "reasons": ["failure_rate within WARN band"]
  }
}
```

### Structured Fields by Component

| Component | Required Fields |
|-----------|-----------------|
| ③ Safeguards | `hook_type`, `action`, `confidence`, `latency_ms` |
| ④ Stress Tests | `attack_template`, `success`, `turns_to_bypass` |
| ⑤ Pipeline | `eval_id`, `scenario_count`, `duration_s` |
| ⑥ Gate | `verdict`, `reasons`, `regressions` |
| ⑦ Incident Lab | `incident_id`, `root_cause`, `blast_radius` |

---

## Metrics Emission

### Metric Format

```python
emit_metric(
    name="failure_rate",
    value=0.11,
    tags={
        "model_version": "gpt-4.2-2026-01-20",
        "safeguard_version": "simulator:v0.3",
        "policy_hash": "sha256:abc123...",
        "component": "eval-pipeline",
        "scenario_type": "misuse"
    },
    timestamp=datetime.utcnow()
)
```

### Required Tags

All metrics must include:
- `model_version`
- `safeguard_version`
- `component`

### Metric Naming Convention

```
{component}_{category}_{metric_name}

Examples:
- gate_decision_latency_seconds
- pipeline_eval_failure_rate
- safeguards_hook_latency_ms
- stress_attack_success_rate
```

---

## Event Schema

For significant events (not just logs):

```json
{
  "$schema": "event_v1.0",
  "event_type": "gate_verdict",
  "timestamp": "ISO8601",
  "trace_id": "string",
  "component": "string",
  "versions": {
    "model_version": "string",
    "safeguard_version": "string",
    "policy_hash": "string"
  },
  "payload": {
    // Event-specific data
  },
  "context": {
    "upstream_trace_ids": ["string"],
    "triggered_by": "string|null"
  }
}
```

---

## Debug Queries

### "Why did this release get blocked?"

```sql
SELECT * FROM events
WHERE trace_id = 'gate_2026-02-01T03:00:00Z_a1b2c3d4'
ORDER BY timestamp;
```

Returns full event chain from eval → gate → verdict.

### "What changed between baseline and candidate?"

```sql
SELECT
  model_version,
  safeguard_version,
  policy_hash,
  failure_rate
FROM metrics
WHERE component = 'eval-pipeline'
  AND timestamp BETWEEN '2026-01-31' AND '2026-02-01'
ORDER BY timestamp;
```

### "Which policy was active during incident INC_004?"

```sql
SELECT DISTINCT policy_hash, safeguard_version
FROM events
WHERE trace_id LIKE '%INC_004%';
```

---

## Correlation IDs

### Cross-Repo Linking

When repo A triggers repo B:

```python
# In repo A (e.g., pipeline triggering gate)
child_trace_id = generate_trace_id()
call_gate(
    trace_id=child_trace_id,
    parent_trace_id=current_trace_id
)
log(
    message="Triggered gate evaluation",
    trace_id=current_trace_id,
    child_trace_id=child_trace_id
)
```

### Incident Linking

All events related to an incident include:

```json
{
  "incident_id": "INC_004",
  "trace_ids": [
    "safeguard_2026-01-30T10:15:30Z_xxx",
    "pipeline_2026-01-30T10:16:00Z_yyy",
    "gate_2026-01-30T10:16:30Z_zzz"
  ]
}
```

---

## Retention Policy

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Gate verdicts | 1 year | Audit trail |
| Eval metrics | 90 days | Trend analysis |
| Debug logs | 7 days | Storage cost |
| Incident traces | Permanent | Learning |

---

## Implementation Checklist

For each repo:

- [ ] All logs include `trace_id`, `model_version`, `safeguard_version`
- [ ] Metrics use standard naming convention
- [ ] Events follow schema with `policy_hash`
- [ ] Trace IDs propagate to downstream calls
- [ ] Retention policy implemented

---

## Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|------------------|
| Logging without trace_id | Cannot correlate events | Always include trace_id |
| Metrics without version tags | Cannot debug regressions | Tag all metrics |
| Different timestamp formats | Correlation fails | Use ISO8601 everywhere |
| Logging sensitive data | Privacy/security risk | Sanitize before logging |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial standard |
