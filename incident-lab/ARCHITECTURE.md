# Agentic Safety Infrastructure: Architecture & Boundaries

> A single-responsibility, composable safety system for production LLM agents.

## Design Philosophy

Each repository serves exactly one layer in the safety lifecycle. Repositories communicate via minimal schemas, not shared code. This ensures:

- **Independent deployability** — Each repo can be used standalone
- **No functionality overlap** — Clear ownership of each capability
- **Composable pipeline** — Repos connect via well-defined interfaces
- **Testable boundaries** — Each layer can be validated independently

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLOSED-LOOP AGENTIC SAFETY SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  DISCOVERY  │───▶│  DETECTION  │───▶│ MITIGATION  │───▶│ VALIDATION  │  │
│  │             │    │             │    │             │    │             │  │
│  │ when-rlhf-  │    │ agentic-    │    │ agentic-    │    │ safeguards- │  │
│  │ fails-      │    │ misuse-     │    │ safeguards- │    │ stress-     │  │
│  │ quietly     │    │ benchmark   │    │ simulator   │    │ tests       │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                                                        │          │
│         │                                                        │          │
│         ▼                                                        ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        RELEASE GATING                                │   │
│  │                                                                      │   │
│  │  safety-harness/release-gate ◀──▶ safety-harness/regression-suite│   │
│  │                                                                      │   │
│  │  CI/CD Integration │ Regression Tests │ Version Comparison           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INCIDENT LEARNING                               │   │
│  │                                                                      │   │
│  │  safety-harness/incident-lab                                        │   │
│  │                                                                      │   │
│  │  Replay │ Root Cause │ Blast Radius │ Regression Promotion           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        GOVERNANCE                                    │   │
│  │                                                                      │   │
│  │  safety-harness/demo │ Safety Memos                                 │   │
│  │                                                                      │   │
│  │  Threat Models │ SLOs │ Playbooks │ Thought Leadership              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Loop: Discovery → Detection → Mitigation → Validation → Release            │
│        → Incident → Discovery                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Responsibilities

### Strict Single-Responsibility Rule

Each repository owns exactly one capability. Functionality that could belong to multiple repos is explicitly assigned to one owner.

| Repository | Layer | Single Responsibility | Explicitly Does NOT Do |
|------------|-------|----------------------|------------------------|
| **when-rlhf-fails-quietly** | Discovery | Define failure taxonomy & benchmark scenarios | CI/CD, infra, dashboards, runtime |
| **agentic-misuse-benchmark** | Detection | Evaluate misuse detection accuracy | Mitigation, gating, incident analysis |
| **safety-harness/simulator** | Mitigation | Runtime safeguard hooks & policy enforcement | Evaluation, benchmarking, CI/CD |
| **safety-harness/stress-testing** | Validation | Adversarial stress testing & erosion curves | Gating decisions, regression suites |
| **safety-harness/release-gate** | Release Gating | CI/CD orchestration & version comparison | Benchmark definition, runtime |
| **safety-harness/regression-suite** | Continuous Testing | Curated regression test collection | Running tests, infrastructure |
| **safety-harness/incident-lab** | Incident Learning | Post-hoc replay & root cause analysis | Real-time detection, evaluation |
| **safety-harness/demo** | Governance | Documentation templates & processes | Code, evaluation, runtime |
| **Safety Memos** | Communication | Technical writing & thought leadership | Implementation, experiments |

---

## Interface Contracts

Repositories communicate via minimal, versioned schemas. No shared code, no shared databases.

### Schema Exchange Protocol

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         INTERFACE CONTRACTS                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  when-rlhf-fails-quietly                                                  │
│  └── EXPORTS: benchmark_spec.json (scenarios, taxonomy, metrics)          │
│                                                                           │
│  agentic-misuse-benchmark                                                 │
│  └── EXPORTS: detector_results.json (accuracy, confusion matrix)          │
│                                                                           │
│  safety-harness/simulator                                             │
│  └── EXPORTS: safeguard_config.yaml (hooks, thresholds, policies)         │
│  └── IMPORTS: trajectory_events.jsonl                                     │
│                                                                           │
│  safety-harness/stress-testing                                                  │
│  └── EXPORTS: erosion_curves.json, failure_cases.jsonl                    │
│                                                                           │
│  safety-harness/release-gate                                        │
│  └── IMPORTS: benchmark_spec.json, safeguard_config.yaml                  │
│  └── EXPORTS: gate_verdict.json (OK/WARN/BLOCK)                           │
│                                                                           │
│  safety-harness/regression-suite                                            │
│  └── IMPORTS: failure_cases.jsonl (from stress-tests, incident-lab)       │
│  └── EXPORTS: regression_manifest.json                                    │
│                                                                           │
│  safety-harness/incident-lab                                              │
│  └── IMPORTS: production_logs.jsonl                                       │
│  └── EXPORTS: incident_report.json, regression_case.json                  │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Forward Path: Research → Production

```
Scenario Design ──▶ Detection Eval ──▶ Safeguard Design ──▶ Stress Test
     │                    │                   │                  │
     ▼                    ▼                   ▼                  ▼
benchmark_spec.json  detector_results  safeguard_config    erosion_curves
     │                    │                   │                  │
     └────────────────────┴───────────────────┴──────────────────┘
                                    │
                                    ▼
                         scalable-eval-pipeline
                                    │
                                    ▼
                           gate_verdict.json
                                    │
                                    ▼
                         safety-harness/regression-suite
```

### Feedback Path: Production → Research

```
Production Incident ──▶ Incident Lab ──▶ Root Cause ──▶ Regression Case
         │                    │               │               │
         ▼                    ▼               ▼               ▼
   logs.jsonl        incident_report    taxonomy_update  failure_case.json
         │                    │               │               │
         └────────────────────┴───────────────┴───────────────┘
                                    │
                                    ▼
                         safety-harness/regression-suite
                                    │
                                    ▼
                    when-rlhf-fails-quietly (taxonomy update)
```

---

## Boundary Rules

### What Each Layer Owns

| Capability | Owner | Others Must NOT Do |
|------------|-------|-------------------|
| Failure taxonomy definition | when-rlhf-fails-quietly | Define new failure modes elsewhere |
| Scenario YAML format | when-rlhf-fails-quietly | Create competing formats |
| Detection accuracy metrics | agentic-misuse-benchmark | Report detection metrics elsewhere |
| Runtime policy enforcement | safety-harness/simulator | Inline policy checks in other repos |
| Erosion curve calculation | safety-harness/stress-testing | Compute erosion in eval pipeline |
| CI/CD orchestration | scalable-eval-pipeline | Build CI in benchmark repos |
| Regression test curation | safety-harness/regression-suite | Store regression tests elsewhere |
| Post-hoc incident analysis | safety-harness/incident-lab | Add RCA to stress tests |
| Governance templates | safety-harness/demo | Add docs to code repos |

### Boundary Violations to Avoid

```
❌ WRONG: when-rlhf-fails-quietly includes a CI/CD workflow
   → This belongs in scalable-eval-pipeline

❌ WRONG: agentic-misuse-benchmark includes safeguard hooks
   → This belongs in safety-harness/simulator

❌ WRONG: safety-harness/stress-testing makes release gating decisions
   → This belongs in scalable-eval-pipeline

❌ WRONG: scalable-eval-pipeline defines new failure taxonomy
   → This belongs in when-rlhf-fails-quietly

❌ WRONG: safety-harness/incident-lab runs real-time detection
   → This is for post-hoc analysis only
```

---

## Versioning Strategy

### Benchmark Versioning

```
when-rlhf-fails-quietly/
├── v1/
│   ├── benchmark_spec.json
│   └── scenarios/
└── v2/
    ├── benchmark_spec.json
    └── scenarios/
```

### Schema Versioning

```json
{
  "schema_version": "1.2.0",
  "benchmark_id": "when-rlhf-fails-quietly",
  "scenarios": [...],
  "taxonomy": {...},
  "metrics": {...}
}
```

### Compatibility Matrix

| Producer Repo | Consumer Repo | Schema Version |
|--------------|---------------|----------------|
| when-rlhf-fails-quietly | scalable-eval-pipeline | benchmark_spec v1.x |
| safety-harness/stress-testing | safety-harness/regression-suite | failure_case v1.x |
| safety-harness/incident-lab | safety-harness/regression-suite | regression_case v1.x |

---

## Interview Talking Points

### Why This Architecture?

> "I intentionally split the system into single-responsibility repos. Benchmarks discover failure modes, runtimes mitigate them, CI gates releases, and incident labs close the loop. None of these layers duplicate functionality; they only communicate via minimal schemas."

### Why Not a Monorepo?

> "Each layer has different release cadences and consumers. Benchmarks evolve with research; runtimes evolve with production needs; CI pipelines evolve with DevOps practices. Decoupling lets each evolve independently while maintaining clear interfaces."

### How Do They Compose?

> "The forward path flows from research to production: scenario design → detection eval → safeguard design → stress test → release gate. The feedback path flows from production to research: incidents → root cause → regression cases → taxonomy updates."

### What's the Key Insight?

> "Safety infrastructure is not a single tool—it's a system of systems. The architecture reflects this: discovery, detection, mitigation, validation, gating, and learning are distinct capabilities that must be owned by distinct components."

---

## File Locations

This document should be linked from:
- Each repository's README (in "Connection to Related Work" section)
- Portfolio overview page
- Interview preparation materials

---

## Contact

Ying Chen, Ph.D.
CONTACT_PLACEHOLDER

---

## License

CC BY-NC 4.0
