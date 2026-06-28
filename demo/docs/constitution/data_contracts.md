# Data Contracts

> **Schema versioning and data flow contracts between repositories.**
> If repo A sends data to repo B, the contract is defined here.

---

## Why Data Contracts Matter

Without explicit contracts:
- Schema changes break downstream consumers silently
- Different repos interpret the same field differently
- Debugging requires reading code instead of documentation

This document ensures producers and consumers agree on data formats.

---

## Contract Principles

### Principle 1: Schema Versioning
Every data exchange has a versioned schema. Breaking changes require version bump.

### Principle 2: Producer Responsibility
The producing repo owns the schema definition. Consumers adapt to producers.

### Principle 3: Backward Compatibility
New fields may be added. Existing fields may not be removed or retyped without major version.

### Principle 4: Explicit Nullability
Fields are required unless explicitly marked optional.

---

## Data Flow Overview

```
① Taxonomy ──────────────────┬──→ ② Attack scenarios
                             ├──→ ③ Safeguard design
                             └──→ ⑦ RCA taxonomy

② Detection results ─────────────→ ⑤ Evaluation input

③ Safeguard signals ─────────┬──→ ④ Stress targets
                             └──→ ⑤ Evaluation input

④ Stress results ────────────┬──→ ⑤ Evaluation targets
                             ├──→ ⑥ Regression tests
                             └──→ ⑦ Failure patterns

⑤ Eval metrics ──────────────────→ ⑥ Gate input

⑦ Promoted regressions ──────────→ ⑥ Regression suite

⑥ Gate verdicts ─────────────────→ CI/CD
```

---

## Contract: ① → ② ③ ⑦ (Taxonomy)

**Producer**: when-rlhf-fails-quietly
**Consumers**: agentic-misuse-benchmark, agentic-safeguards-simulator, agentic-safety-incident-lab

### Schema v1.0

```yaml
# taxonomy/*.yaml
failure_type:
  id: string           # Required. Unique identifier (e.g., "hedging_leakage")
  category: string     # Required. Top-level category
  description: string  # Required. Human-readable description
  rlhf_artifact: string # Required. Which RLHF component causes this
  detection_layer: enum[pre_action, mid_trajectory, post_action]
  severity: enum[low, medium, high, critical]
  examples:            # Optional. List of example manifestations
    - scenario: string
      turns: int
      outcome: string
```

### Compatibility Rules
- New failure types may be added
- Existing IDs may not be reused
- Severity levels may not be changed without consumer notification

---

## Contract: ④ → ⑤ ⑥ ⑦ (Stress Results)

**Producer**: safeguards-stress-tests
**Consumers**: scalable-safeguards-eval-pipeline, model-safety-regression-suite, agentic-safety-incident-lab

### Schema v1.0

```json
{
  "$schema": "stress_results_v1.0",
  "run_id": "string",
  "timestamp": "ISO8601",
  "attack_template": "string",
  "safeguard_config": "string",
  "results": {
    "success_rate": "float[0,1]",
    "avg_turns_to_bypass": "float|null",
    "erosion_curve": [
      {"turn": "int", "compliance": "float[0,1]"}
    ]
  },
  "metadata": {
    "model_version": "string",
    "safeguard_version": "string",
    "seed": "int"
  }
}
```

### Compatibility Rules
- `erosion_curve` must have at least one data point
- `avg_turns_to_bypass` is null if no bypass achieved
- `seed` enables reproducibility

---

## Contract: ⑤ → ⑥ (Eval Metrics)

**Producer**: scalable-safeguards-eval-pipeline
**Consumers**: model-safety-regression-suite

### Schema v1.0

```json
{
  "$schema": "eval_metrics_v1.0",
  "run_id": "string",
  "timestamp": "ISO8601",
  "versions": {
    "model_version": "string",
    "safeguard_version": "string",
    "attack_suite": "string",
    "benchmark_version": "string"
  },
  "metrics": {
    "failure_rate": {
      "value": "float[0,1]",
      "ci_lower": "float",
      "ci_upper": "float",
      "n_samples": "int"
    },
    "avg_first_failure": {
      "value": "float|null",
      "ci_lower": "float|null",
      "ci_upper": "float|null"
    },
    "erosion_slope": {
      "value": "float",
      "ci_lower": "float",
      "ci_upper": "float"
    },
    "false_positive_rate": {
      "value": "float[0,1]",
      "ci_lower": "float",
      "ci_upper": "float",
      "n_samples": "int"
    }
  },
  "by_category": {
    "<category_name>": {
      "failure_rate": "float",
      "n_samples": "int"
    }
  }
}
```

### Compatibility Rules
- All governance metrics (see metric_definitions.md) must be present
- Confidence intervals are required for all metrics
- `by_category` breakdown enables regression debugging

---

## Contract: ⑥ → CI/CD (Gate Verdict)

**Producer**: model-safety-regression-suite
**Consumers**: CI/CD pipelines

### Schema v1.0

```json
{
  "$schema": "gate_verdict_v1.0",
  "run_id": "string",
  "timestamp": "ISO8601",
  "verdict": "enum[OK, WARN, BLOCK]",
  "exit_code": "int[0,2]",
  "versions": {
    "model_version": "string",
    "safeguard_version": "string",
    "baseline_version": "string"
  },
  "reasons": ["string"],
  "regressions": [
    {
      "metric": "string",
      "baseline": "float",
      "candidate": "float",
      "delta": "float",
      "status": "enum[OK, WARN, BLOCK]"
    }
  ],
  "trace_id": "string",
  "decision_trace_url": "string|null"
}
```

### Exit Codes
| Code | Verdict | CI/CD Action |
|------|---------|--------------|
| 0 | OK | Pass |
| 1 | WARN | Pass with warning |
| 2 | BLOCK | Fail |

### Compatibility Rules
- `verdict` and `exit_code` must be consistent
- `trace_id` enables audit trail lookup
- `reasons` must be human-readable

---

## Contract: ⑦ → ⑥ (Promoted Regressions)

**Producer**: agentic-safety-incident-lab
**Consumers**: model-safety-regression-suite

### Schema v1.0

```yaml
# regressions/INC_XXX.yaml
regression:
  incident_id: string       # Required. Source incident
  regression_type: enum[unit, e2e]
  severity: enum[low, medium, high, critical]
  promoted_date: ISO8601
  test_definition:
    scenario: string        # YAML scenario or Python test path
    expected_verdict: enum[OK, WARN, BLOCK]
    expected_detection_turn: int|null
  metadata:
    root_cause_category: string
    blast_radius: string
    jira_ticket: string|null
```

### Compatibility Rules
- All promoted regressions must pass before OK verdict
- `severity` determines ordering in test suite
- `incident_id` links to full incident analysis

---

## Schema Change Process

1. **Propose** change with rationale and migration plan
2. **Notify** all consumers with 14-day notice
3. **Version** bump (minor for additions, major for breaking)
4. **Document** changes here before implementation
5. **Migrate** consumers before removing old schema support

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial contracts |
