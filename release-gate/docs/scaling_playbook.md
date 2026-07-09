# Scaling Playbook: From Demo to Production

This document provides a migration path from the demo implementation to production-grade deployment.

---

## Overview

The demo implementation demonstrates architectural patterns with local, single-machine implementations. Production deployments require distributed execution, cloud storage, and real alerting. This playbook documents the migration path for each component.

---

## 1. Worker Pool → Distributed Execution

### Demo Implementation
```python
# workers/worker.py
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(evaluate_scenario, scenarios)
```

### Production Migration

**Option A: Ray (Recommended)**

```python
import ray

@ray.remote
def evaluate_scenario(scenario):
    return run_evaluation(scenario)

ray.init(address="auto")
futures = [evaluate_scenario.remote(s) for s in scenarios]
results = ray.get(futures)
```

Advantages:
- Scales across machines automatically
- Built-in fault tolerance
- Supports heterogeneous resources (GPU/CPU)

**Option B: Celery + Redis**

```python
from celery import Celery
app = Celery('eval', broker='redis://localhost')

@app.task
def evaluate_scenario(scenario):
    return run_evaluation(scenario)
```

Advantages:
- Well-established, battle-tested
- Good monitoring tools (Flower)
- Easy to integrate with existing Django/Flask apps

### Resource Estimation

| Scenarios/day | Workers Needed | Memory (GB) | Cost/month (AWS) |
|---------------|----------------|-------------|------------------|
| 1,000 | 4 | 16 | $150 |
| 10,000 | 16 | 64 | $600 |
| 100,000 | 64 | 256 | $2,400 |

Assumptions: 30s/scenario average, 8-hour workday, m5.xlarge instances.

---

## 2. Local Parquet → Cloud Storage

### Demo Implementation
```python
# storage/metrics_store.py
df.to_parquet("results/metrics.parquet")
```

### Production Migration

**Option A: S3 + PyArrow**

```python
import pyarrow.parquet as pq
import s3fs

fs = s3fs.S3FileSystem()
pq.write_table(table, "s3://bucket/results/metrics.parquet", filesystem=fs)
```

**Option B: Delta Lake**

```python
from delta import DeltaTable

df.write.format("delta").save("s3://bucket/results/metrics")
```

Advantages:
- ACID transactions
- Time travel for auditing
- Schema evolution

### Retention Policy

| Data Type | Retention | Storage Class |
|-----------|-----------|---------------|
| Raw results | 90 days | S3 Standard |
| Aggregated metrics | 2 years | S3 IA |
| Audit logs | 7 years | S3 Glacier |

Estimated monthly cost: $50-200 depending on eval volume.

---

## 3. Mock Alerts → Real Alerting

### Demo Implementation
```python
# monitoring/alerts.py
def alert(message, severity):
    print(f"[{severity}] {message}")
```

### Production Migration

**Slack Integration**

```python
import requests

def alert_slack(message, severity, channel="#safety-alerts"):
    severity_emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}
    payload = {
        "channel": channel,
        "text": f"{severity_emoji[severity]} {message}",
        "attachments": [{"color": "danger" if severity == "critical" else "warning"}]
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)
```

**PagerDuty Integration**

```python
import pypd

def alert_pagerduty(message, severity, dedup_key):
    pypd.EventV2.create(data={
        "routing_key": PAGERDUTY_ROUTING_KEY,
        "event_action": "trigger",
        "dedup_key": dedup_key,
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "safety-eval-pipeline"
        }
    })
```

### Escalation Policy

| Severity | Initial | 15 min | 30 min | 1 hour |
|----------|---------|--------|--------|--------|
| Critical | Slack + PD | Page on-call | Page lead | Page VP |
| Warning | Slack | - | - | - |
| Info | Log only | - | - | - |

---

## 4. Dashboard → Production Deployment

### Demo Implementation
```bash
streamlit run dashboard/app.py
```

### Production Migration

**Option A: Kubernetes Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: safety-dashboard
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: dashboard
        image: safety-eval:latest
        command: ["streamlit", "run", "dashboard/app.py"]
        ports:
        - containerPort: 8501
```

**Option B: AWS App Runner**

```yaml
# apprunner.yaml
services:
  - name: safety-dashboard
    source:
      image: <ecr-image>
    port: 8501
    cpu: 1024
    memory: 2048
```

### Authentication

Add authentication via:
- Okta/Auth0 for SSO
- Streamlit's native auth (streamlit-authenticator)
- API Gateway + Cognito for AWS deployments

---

## 5. CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Safety Gate
on:
  pull_request:
    branches: [main]

jobs:
  safety-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run safety evaluation
        run: python run_release_gate.py --baseline main --candidate ${{ github.sha }}

      - name: Block on BLOCK verdict
        run: |
          if grep -q '"gate_decision": "BLOCK"' gate_output.json; then
            echo "::error::Safety gate returned BLOCK"
            exit 2
          fi
```

### Exit Codes

| Code | Verdict | Action |
|------|---------|--------|
| 0 | OK | Merge allowed |
| 1 | WARN | Merge allowed with warning |
| 2 | BLOCK | Merge blocked |

---

## 6. Monitoring & Observability

### Metrics to Export (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

eval_duration = Histogram('eval_duration_seconds', 'Evaluation duration')
violations_total = Counter('safety_violations_total', 'Total violations')
drift_score = Gauge('drift_score', 'Current drift score')
```

### Dashboards (Grafana)

Key panels:
- Evaluation throughput (scenarios/hour)
- Failure rate over time
- Drift score trending
- Alert frequency by severity
- Worker utilization

### Log Aggregation

Structure logs for queryability:

```json
{
  "timestamp": "2026-02-01T10:00:00Z",
  "event": "evaluation_complete",
  "scenario_id": "SC_001",
  "verdict": "BLOCK",
  "failure_rate": 0.12,
  "correlation_id": "abc123"
}
```

Export to: CloudWatch Logs, Datadog, Splunk.

---

## 7. Cost Optimization

### Compute Scheduling

- Run batch evals during off-peak hours (50% cost savings on spot)
- Use reserved instances for baseline capacity
- Spot instances for burst capacity

### Storage Tiering

- Hot: Last 7 days (S3 Standard)
- Warm: 7-90 days (S3 IA)
- Cold: 90+ days (S3 Glacier)

Implement via S3 Lifecycle policies.

### Caching

- Cache model inference results for identical inputs
- Cache embedding computations
- Use Redis for hot data

Estimated savings: 30-50% on compute costs.

---

## Migration Checklist

### Phase 1: Infrastructure
- [ ] Provision Ray/Celery cluster
- [ ] Set up S3 buckets with lifecycle policies
- [ ] Configure Slack/PagerDuty integrations
- [ ] Deploy Kubernetes cluster or App Runner

### Phase 2: Integration
- [ ] Migrate worker pool to distributed execution
- [ ] Update storage paths to S3
- [ ] Wire alerting to real channels
- [ ] Add authentication to dashboard

### Phase 3: Operations
- [ ] Set up Prometheus + Grafana
- [ ] Configure log aggregation
- [ ] Create runbooks for common alerts
- [ ] Train on-call team

### Phase 4: Validation
- [ ] Run parallel execution (demo + prod)
- [ ] Verify metrics match
- [ ] Test failure scenarios
- [ ] Load test at 2x expected volume

---

## Contact

For questions about production deployment, contact:

Ying Chen, Ph.D.
CONTACT_EMAIL
