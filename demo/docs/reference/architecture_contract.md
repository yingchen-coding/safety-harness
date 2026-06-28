# Architecture Contract: 8-Repo Closed-Loop Safety System

> **Single source of truth for repository boundaries, ownership, and interface contracts.**
> Reference this document when unclear about where code belongs.

---

## Core Principle

**Each repository has ONE job. No repository makes decisions outside its domain.**

```
Research → Detection → Prevention → Testing → Evaluation → Gating → Learning → Demo
   ①          ②           ③          ④          ⑤          ⑥         ⑦        ⑧
```

---

## Repository Ownership Matrix

| Repo | Single Responsibility | Owns | Does NOT Own |
|------|----------------------|------|--------------|
| ① when-rlhf-fails-quietly | Why RLHF fails silently | Failure taxonomy, causal mechanisms | Attack generation, safeguard implementation |
| ② agentic-misuse-benchmark | Detect multi-turn attacks | Attack scenarios, detector benchmarks | Safeguard logic, release decisions |
| ③ safety-harness/simulator | How safeguards work | Policy hooks, bypass analysis | Stress testing, release gating |
| ④ safety-harness/stress-testing | How long safeguards survive | Adversarial pressure, erosion curves | Safeguard implementation, evaluation infra |
| ⑤ safety-harness/release-gate | Production evaluation infra | Orchestration, SLOs, drift detection | Release decisions, safeguard logic |
| ⑥ safety-harness/regression-suite | Should we ship this model? | OK/WARN/BLOCK verdicts, baselines | Evaluation execution, incident analysis |
| ⑦ safety-harness/incident-lab | What failed in production? | RCA, blast radius, regression promotion | Release gating, safeguard design |
| ⑧ safety-harness/demo | Show the complete system | Orchestration, documentation | All of the above |

---

## Hard Boundary Rules

### Rule 1: Research Does Not Touch Production
- ① studies failure modes but does NOT implement detectors or safeguards
- Research outputs (taxonomy, mechanisms) are consumed by other repos

### Rule 2: Evaluation Does Not Write Policy
- ⑤ runs evaluations but does NOT decide thresholds
- Evaluation outputs (metrics, drift signals) feed into ⑥ for decisions

### Rule 3: Only One Repo Makes Release Decisions
- ⑥ is the ONLY repo that outputs OK/WARN/BLOCK
- All other repos produce signals, not decisions

### Rule 4: Incident Lab Does Not Gate
- ⑦ analyzes incidents and promotes regressions
- Gating decisions remain in ⑥

### Rule 5: Demo Does Not Implement
- ⑧ orchestrates and visualizes but implements nothing
- All logic must live in repos ①-⑦

---

## Interface Contracts

### Data Flow

```
① Taxonomy/Mechanisms
   ├──→ ② Attack scenarios (from failure types)
   ├──→ ③ Safeguard design (from causal analysis)
   └──→ ⑦ RCA taxonomy (from failure classification)

④ Stress Results
   ├──→ ⑤ Evaluation targets
   ├──→ ⑥ Regression tests
   └──→ ⑦ Failure patterns

⑦ Incident Analysis
   ├──→ ⑥ Promoted regressions
   └──→ ① Failure taxonomy updates

⑥ Gate Decisions
   └──→ CI/CD (OK/WARN/BLOCK)
```

### Output Schemas

| Repo | Primary Output | Schema Location | Consumers |
|------|---------------|-----------------|-----------|
| ① | `taxonomy.yaml`, `mechanisms.json` | `taxonomy/*.yaml` | ②, ③, ⑦ |
| ② | Detection benchmarks | `scenarios/output_schema.json` | ⑤ |
| ③ | Safeguard hooks, bypass patterns | `config/policy_dsl.yaml` | ④, ⑤ |
| ④ | `stress_failures.json`, erosion curves | `config/output_schema.json` | ⑤, ⑥, ⑦ |
| ⑤ | Eval metrics, drift alerts | `config/release_gate.yaml` | ⑥ |
| ⑥ | `gate_report.html`, verdict | Gate JSON output | CI/CD |
| ⑦ | RCA, blast radius, regressions | `schemas/root_cause_schema.yaml` | ⑥ |

---

## Anti-Patterns (Do Not Do This)

| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| Adding release logic to ③ | Couples safeguards to governance | Keep in ⑥ |
| Adding safeguard code to ④ | Conflates testing with implementation | Keep in ③ |
| Adding orchestration to ① | Research should stay pure | Use ⑧ for demos |
| Adding evaluation infra to ⑥ | Gating should be thin | Keep infra in ⑤ |
| Adding RCA to ⑥ | Conflates gating with learning | Keep in ⑦ |
| Any repo importing ⑧ | Demo is a leaf node | ⑧ imports others, not vice versa |

---

## Reviewer Checklist

Before merging any PR, ask:

- [ ] Does this change belong in THIS repo according to the ownership matrix?
- [ ] Does this PR introduce cross-boundary coupling?
- [ ] Are interface contracts respected (correct input/output formats)?
- [ ] If adding new functionality, is it within the repo's single responsibility?

---

## Boundary Violation Examples

### Example 1: Adding release gate to safeguards-simulator
**Wrong**: `safeguards/release_gate.py` in ③
**Right**: Move to ⑥ safety-harness/regression-suite

### Example 2: Adding incident replay to stress-tests
**Wrong**: `replay/incident_replay.py` in ④
**Right**: Move to ⑦ safety-harness/incident-lab

### Example 3: Adding evaluation scheduler to regression-suite
**Wrong**: `orchestrator/scheduler.py` in ⑥
**Right**: Move to ⑤ safety-harness/release-gate

---

## Why Boundaries Matter

Blurring boundaries causes:

1. **Harder root cause analysis** — Which component failed?
2. **Harder regression isolation** — Which change broke it?
3. **Harder audits** — Who owns this decision?
4. **Harder onboarding** — Where does this code go?

Clean boundaries enable:

1. **Independent deployment** — Update one repo without breaking others
2. **Clear ownership** — One team per repo
3. **Auditable decisions** — Trace any verdict to its source
4. **Testable components** — Unit test each repo in isolation

---

## Governance

### Change Process
1. Boundary changes require explicit approval
2. New repos require architecture review
3. Cross-repo interfaces require schema versioning

### Exception Process
If a boundary must be crossed temporarily:
1. Document the exception with rationale
2. Create tracking issue for remediation
3. Set deadline for proper separation

---

## Version

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial contract |

---

## Contact

Architecture questions: blueoceanally@gmail.com
