# Production Operations Guide

## Data Governance & PII Handling

### Traffic Data Classification

| Data Type | Classification | Handling |
|-----------|----------------|----------|
| Raw user prompts | PII-HIGH | Never store, stream-only |
| Anonymized prompts | PII-LOW | Store with retention limits |
| Model responses | PII-MEDIUM | Depends on content |
| Aggregate metrics | NON-PII | Standard storage |

### Anonymization Pipeline

```python
class TrafficAnonymizer:
    def anonymize(self, conversation: dict) -> dict:
        """Remove PII before storage or eval."""
        return {
            'turns': [
                {
                    'role': t['role'],
                    'content': self._scrub_pii(t['content']),
                    'timestamp': self._bucket_timestamp(t['timestamp'])
                }
                for t in conversation['turns']
            ],
            'metadata': {
                'region': conversation.get('region'),  # OK to keep
                'user_id': None,  # Removed
                'session_id': self._hash_id(conversation['session_id'])
            }
        }

    def _scrub_pii(self, text: str) -> str:
        """Remove names, emails, phone numbers, etc."""
        text = self._redact_emails(text)
        text = self._redact_phones(text)
        text = self._redact_names(text)
        text = self._redact_addresses(text)
        return text
```

### Compliance Checklist

- [ ] Data retention policy defined (default: 90 days)
- [ ] PII scrubbing validated by privacy team
- [ ] Access controls implemented (RBAC)
- [ ] Audit logging enabled
- [ ] Data deletion capability tested
- [ ] Cross-border transfer restrictions honored

---

## Backpressure & Failure Handling

### Worker Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Worker crash | Heartbeat timeout | Auto-restart + requeue |
| Worker hang | Progress timeout | Kill + requeue |
| Worker overload | Queue depth | Scale up / backpressure |
| All workers down | No heartbeats | Alert + manual intervention |

### Backpressure Strategy

```python
class BackpressureController:
    def __init__(self):
        self.queue_depth_threshold = 1000
        self.reject_threshold = 5000

    def should_accept(self, queue_depth: int) -> tuple[bool, str]:
        if queue_depth > self.reject_threshold:
            return False, "Queue full, rejecting new work"
        elif queue_depth > self.queue_depth_threshold:
            return True, "Accepting with delay warning"
        else:
            return True, "Normal operation"

    def adjust_rate(self, queue_depth: int) -> float:
        """Return rate multiplier for incoming work."""
        if queue_depth > self.queue_depth_threshold:
            # Slow down intake proportionally
            return max(0.1, 1.0 - (queue_depth / self.reject_threshold))
        return 1.0
```

### Streaming Backlog Handling

```
Normal: Process in real-time
Elevated (>1000 pending): Sample 50%, queue rest
Critical (>5000 pending): Sample 10%, alert on-call
Emergency (>10000 pending): Stop intake, drain queue
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

    def __init__(self):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = 5
        self.reset_timeout = 60  # seconds

    def call(self, func, *args, **kwargs):
        if self.state == self.OPEN:
            raise CircuitOpenError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            self._schedule_reset()

    def _on_success(self):
        self.failure_count = 0
        self.state = self.CLOSED
```

---

## Cost Model

### Compute Cost Breakdown

| Component | Cost Driver | Est. Cost per 1K Evals |
|-----------|-------------|------------------------|
| Model API calls | Tokens processed | $2-20 (model dependent) |
| Worker compute | CPU hours | $0.50-2.00 |
| Storage | GB stored | $0.10-0.50 |
| Network | Data transfer | $0.05-0.20 |
| **Total** | | **$2.65-22.70** |

### Cost Optimization Strategies

1. **Caching:** Cache model responses for identical inputs
2. **Batching:** Batch API calls to reduce overhead
3. **Sampling:** Evaluate subset when full coverage unnecessary
4. **Tiered models:** Use cheaper models for initial screening
5. **Spot instances:** Use preemptible compute for batch jobs

### Cost vs Coverage Tradeoff

```
Full coverage (100% traffic): $X per day
Sampled (10% traffic): $0.1X per day
Confidence interval: Wider but often sufficient

Recommendation: Sample unless regression detected, then full sweep
```

### Budget Alerts

```yaml
# monitoring/alerts/cost.yaml
alerts:
  - name: daily_cost_exceeded
    condition: daily_spend > $100
    action: notify_team

  - name: anomaly_detected
    condition: hourly_spend > 2x rolling_avg
    action: investigate

  - name: budget_exhausted
    condition: monthly_spend > $3000
    action: pause_non_critical + page_oncall
```

---

## Operational Runbooks

### Runbook: High Queue Depth

```
Trigger: Queue depth > 1000 for > 5 minutes

Steps:
1. Check worker health: `kubectl get pods -l app=eval-worker`
2. If workers healthy, scale up: `kubectl scale deployment eval-worker --replicas=10`
3. If workers unhealthy, check logs: `kubectl logs -l app=eval-worker --tail=100`
4. If model API issue, check status page
5. If persistent, enable sampling mode
6. Escalate if > 30 min unresolved
```

### Runbook: Spike in Safety Failures

```
Trigger: Safety failure rate > 2x baseline for > 10 minutes

Steps:
1. Verify not false positive: Check sample of flagged items
2. If real, identify pattern: Which scenarios? Which model?
3. Check for model update: Was model version changed?
4. Check for attack campaign: Correlated user IDs?
5. If attack, enable enhanced monitoring
6. If model regression, escalate to model team
7. Document in incident tracker
```

### Runbook: Cost Anomaly

```
Trigger: Hourly cost > 3x rolling average

Steps:
1. Identify cost driver: Model API? Compute? Storage?
2. If model API, check for infinite loop or prompt explosion
3. If compute, check for stuck workers
4. If storage, check for data retention policy violation
5. Kill runaway jobs if identified
6. Post-incident: Add guardrails to prevent recurrence
```

---

## SLA Commitments

| Metric | Target | Measurement |
|--------|--------|-------------|
| Eval availability | 99.5% | Uptime monitoring |
| Eval latency (batch) | < 1 hour | Job completion time |
| Eval latency (streaming) | < 5 min | End-to-end latency |
| Data freshness | < 15 min | Lag from production |
| Alert response | < 15 min | Ack time for P1 |
