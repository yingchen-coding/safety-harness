# Design Document: Scalable Safeguards Evaluation Pipeline

## Overview

This document describes the architecture decisions and tradeoffs in building a production-style evaluation pipeline for multi-turn safety metrics.

## Design Goals

1. **Scalability**: Handle thousands of evaluation scenarios
2. **Observability**: Real-time visibility into evaluation health
3. **Reproducibility**: Versioned datasets and deterministic runs
4. **Operability**: Clear alerting and drift detection
5. **Extensibility**: Easy to add new models, metrics, scenarios

## Architecture Decisions

### Batch vs. Streaming Split

**Decision**: Separate batch and streaming evaluation paths.

**Rationale**:
- Batch optimizes for throughput and completeness
- Streaming optimizes for latency and real-time monitoring
- Different reliability requirements (batch can retry, streaming needs low latency)
- Different resource patterns (batch is bursty, streaming is steady)

**Tradeoff**: Code duplication vs. optimization opportunity

### Storage: Parquet over JSON

**Decision**: Use Parquet as primary storage format.

**Rationale**:
- Columnar format efficient for analytical queries
- Built-in compression reduces storage costs
- Schema enforcement catches data issues early
- Widely supported in data ecosystem (pandas, Spark, DuckDB)

**Tradeoff**: Less human-readable than JSON, requires libraries

### Worker Pool: Threads over Processes

**Decision**: Thread-based worker pool.

**Rationale**:
- Model API calls are I/O-bound, not CPU-bound
- Threads have lower overhead than processes
- Shared memory simplifies state management
- GIL is not a bottleneck for network I/O

**Tradeoff**: Cannot utilize multiple CPUs for CPU-bound work

### Drift Detection: Heuristic Thresholds

**Decision**: Rule-based drift detection over learned models.

**Rationale**:
- No training data required to bootstrap
- Interpretable decisions (can explain why alert fired)
- Easy to tune and adjust thresholds
- Faster to implement and iterate

**Tradeoff**: May miss subtle patterns that learned models would catch

### Rate Limiting: Token Bucket

**Decision**: Token bucket algorithm for rate limiting.

**Rationale**:
- Allows bursting while respecting average rate
- Simple to implement and reason about
- Standard approach for API rate limiting
- Can be tuned per-model if needed

**Tradeoff**: Doesn't account for model-specific rate limits

## Production Considerations

### What This Demo Includes

| Capability | Implementation |
|------------|----------------|
| Job scheduling | Thread pool with queue |
| Rate limiting | Token bucket |
| Retries | Configurable attempts with backoff |
| Metrics storage | Parquet files |
| Drift detection | Threshold + trend analysis |
| Alerting | File-based + mock channels |
| Dashboard | Streamlit prototype |

### What Production Would Add

| Capability | Production Implementation |
|------------|--------------------------|
| Job scheduling | Celery, Ray, or Temporal |
| Storage | S3/GCS with Delta Lake or Iceberg |
| Alerting | PagerDuty, Slack, email integration |
| Dashboard | Grafana with Prometheus metrics |
| Authentication | OAuth/OIDC |
| Deployment | Kubernetes with autoscaling |
| CI/CD | Automated regression gating |

## Failure Modes

### Pipeline Failures We Handle

1. **Transient API errors**: Automatic retry with exponential backoff
2. **Rate limiting**: Token bucket prevents exceeding limits
3. **Partial failures**: Jobs are independent, failures don't cascade
4. **Data corruption**: Schema validation on storage

### Failure Modes We Accept

1. **Model unavailability**: No automatic failover to backup models
2. **Storage failures**: No redundant storage or replication
3. **Alert storms**: Cooldown only, no intelligent suppression
4. **Clock skew**: Assumes single-node deployment

## Metrics Design

### Why These Metrics

| Metric | Why It Matters |
|--------|----------------|
| `violation_rate` | Primary safety signal |
| `avg_first_failure_turn` | Measures resistance to multi-turn attacks |
| `erosion_slope` | Detects gradual policy degradation |
| `p99_latency` | Ensures acceptable user experience |
| `false_positive_rate` | Balances safety vs. usability |

### Alerting Philosophy

**Principle**: Alert on trends, not individual events.

- Single violations don't trigger alerts
- Sustained increases in violation rate do
- Erosion slope detects gradual degradation
- Cooldown prevents alert fatigue

## Future Directions

### Near-term

1. Real model API integration
2. More sophisticated drift detection (statistical tests)
3. Scenario mutation and augmentation
4. Cross-model comparison reports

### Long-term

1. Distributed evaluation with Ray
2. Learned anomaly detection
3. Automated threshold tuning
4. Integration with model training pipelines

## Relationship to Other Projects

```
┌─────────────────────────────────────────────────────────────┐
│                     SAFETY PORTFOLIO                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  when-rlhf-fails-quietly     → Understanding failures        │
│           │                                                  │
│           ▼                                                  │
│  agentic-misuse-benchmark    → Defining test scenarios       │
│           │                                                  │
│           ▼                                                  │
│  safety-harness/stress-testing     → Red-teaming attacks           │
│           │                                                  │
│           ▼                                                  │
│  THIS PIPELINE               → Running at scale              │
│           │                                                  │
│           ▼                                                  │
│  safety-harness/simulator → Mitigation strategies        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

This pipeline is the "how do we run this in production" piece of the portfolio.
