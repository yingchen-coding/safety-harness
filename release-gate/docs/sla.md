# Service Level Agreements & Incident Response

## SLA Definitions

### Evaluation Pipeline SLAs

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Batch eval completion | < 1 hour | 1-2 hours | > 2 hours |
| Streaming eval latency | < 5 min | 5-15 min | > 15 min |
| Data freshness | < 15 min | 15-30 min | > 30 min |
| Pipeline availability | 99.5% | 99-99.5% | < 99% |
| Drift alert latency | < 10 min | 10-30 min | > 30 min |

### Response Time SLAs

| Severity | Response | Resolution |
|----------|----------|------------|
| P1 (Critical) | 15 min | 4 hours |
| P2 (High) | 1 hour | 24 hours |
| P3 (Medium) | 4 hours | 72 hours |
| P4 (Low) | 24 hours | Best effort |

## Pipeline Incident Response

### Runbook: Pipeline Down

```
Trigger: No successful eval in 30 minutes

1. Check orchestrator health
   $ kubectl get pods -l app=orchestrator

2. If orchestrator down:
   $ kubectl rollout restart deployment/orchestrator

3. Check worker health
   $ kubectl get pods -l app=worker

4. If workers down:
   $ kubectl rollout restart deployment/worker

5. Check dependencies
   - Model API status
   - Database connectivity
   - Message queue health

6. If persistent, escalate to on-call

7. Post-incident: File incident report
```

### Runbook: Drift Alert Storm

```
Trigger: > 10 drift alerts in 1 hour

1. Verify alerts are genuine
   - Check recent model deployments
   - Check eval code changes

2. If false positive storm:
   - Temporarily raise threshold (+0.1)
   - Investigate root cause

3. If genuine drift:
   - Notify model team
   - Capture exemplars
   - Consider eval pause

4. Document in incident tracker
```

### Runbook: Data Pipeline Lag

```
Trigger: Data freshness > 30 minutes

1. Check ingestion service
   $ kubectl logs -l app=ingestion --tail=100

2. Check source system health

3. If ingestion backlog:
   - Scale up workers
   - Enable sampling mode

4. If source system issue:
   - Wait for upstream fix
   - Alert stakeholders

5. Resume normal operation when lag < 15 min
```

## Negative Results

### What Didn't Work in Operations

1. **Alert on every anomaly**
   - Problem: Alert fatigue, ignored alerts
   - Learning: Tiered alerting with suppression

2. **Single global threshold**
   - Problem: Different metrics have different baselines
   - Learning: Per-metric adaptive thresholds

3. **Manual scaling**
   - Problem: Slow response to load spikes
   - Learning: Auto-scaling with guardrails

4. **Synchronous eval**
   - Problem: Blocked on slow model responses
   - Learning: Async with timeout handling
