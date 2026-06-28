> **Portfolio**: [Safety Memo](https://yingchen-coding.github.io/safety-memos/) · [when-rlhf-fails-quietly](https://github.com/yingchen-coding/when-rlhf-fails-quietly) · [agentic-misuse-benchmark](https://github.com/yingchen-coding/agentic-misuse-benchmark) · [safety-harness/simulator](https://github.com/yingchen-coding/safety-harness/tree/main/simulator) · [safety-harness/stress-testing](https://github.com/yingchen-coding/safety-harness/tree/main/stress-testing) · [safety-harness/release-gate](https://github.com/yingchen-coding/safety-harness/tree/main/release-gate) · [safety-harness/regression-suite](https://github.com/yingchen-coding/safety-harness/tree/main/regression-suite) · [safety-harness/incident-lab](https://github.com/yingchen-coding/safety-harness/tree/main/incident-lab)

# Agentic Safety Demo

> **One-command demonstration of the complete safety loop: Discovery → Conversion → Gating → Learning. Built for interviews, internal demos, and stakeholder communication.**

A unified end-to-end demonstration of the closed-loop safety system: Stress Testing → Regression → Release Gate → Incident Replay.

**Single responsibility**: Orchestrate + Visualize + Tell the Story.

---

## 🧭 Constitution-as-Code

> **Principles are first-class release constraints, not documentation.**

This demo showcases an Anthropic-style safety system where:

- **Every verdict traces to constitutional principles** (C1-C6)
- **Safeguards map to specific principles they uphold**
- **Alignment debt accumulates when principles are temporarily violated**
- **No release is approved without constitutional evidence**

### Demo Artifacts with Constitution Audit

After running the demo, inspect:

| Artifact | Description |
|----------|-------------|
| `artifacts/gate_report.html` | Release gate report with **Constitution Compliance Audit** |
| `artifacts/alignment_debt.yaml` | Alignment debt ledger with principle-level tracking |
| `artifacts/stress_failures.json` | Failures mapped to violated principles |
| `artifacts/regression_tests.json` | Tests tagged with principles they verify |

### Constitution Principles

| ID | Principle | Severity |
|----|-----------|----------|
| C1 | No Facilitation of Harm | Critical |
| C2 | No Deceptive Alignment | High |
| C3 | Preserve Human Oversight | High |
| C4 | Uncertainty Implies Caution | High |
| C5 | Continuous Safety Improvement | Medium |
| C6 | Transparency & Traceability | Medium |

See [regression-suite/config/constitution_v2.yaml](../regression-suite/config/constitution_v2.yaml) for the executable constitution.

---

## 🛡️ Organizational Safety Governance

This demo implements a complete **AI Safety SRE system**:

### Closed-Loop Governance Flow

```
Exception → Constitution Audit → Alignment Debt → Freeze Playbook
                     ↓
            Risk Dashboard (Visualization)
```

### Governance Mechanisms

| Mechanism | Effect |
|-----------|--------|
| **Error Budget** | Max 2 new debts/quarter, exceeded = BLOCK |
| **Debt SLO** | 14d critical, 30d high, 60d medium = auto-BLOCK |
| **Safety Freeze** | Budget exceeded = release frozen |
| **Exception Authority** | Only Head_of_Safety can unfreeze |
| **Blast Radius Limiter** | Max 5 safeguards + 3 principles per exception |
| **Incident Review** | Every exception triggers mandatory review |

### Risk Dashboard

Run the demo to generate the organizational risk dashboard:

```bash
python scripts/render_risk_dashboard.py
open artifacts/risk_dashboard.html
```

The dashboard shows:
- Active exceptions with TTL countdown
- Alignment debt with SLO status
- Error budget utilization
- Constitution audit summary
- Freeze status

---

## 🏛️ Safety Board Mode (Executive Governance)

When safety gates BLOCK a release or exception budgets are exceeded, the system automatically produces board-level governance artifacts:

### Board-Level Artifacts

| Artifact | Trigger | Purpose |
|----------|---------|---------|
| **Board Brief** | Any BLOCK verdict | 1-page executive summary with risk, impact, remediation |
| **Exception Audit** | Budget exceeded | CEO/Board visibility into exception patterns |
| **Investment Recommendation** | Debt aging > SLO | Quarterly safety investment proposal |

### Running Board Mode

```bash
# Generate all board artifacts
python scripts/step5_board_mode.py --generate-all

# Generate executive dashboard with ROI model
python scripts/step6_show_exec_dashboard.py

# View board mode index
open artifacts/board_mode_index.html

# View executive dashboard (board-meeting ready)
open artifacts/executive_safety_dashboard.html
```

### Financial ROI Framing

The executive dashboard translates safety into board-level language:

> "This quarter, a $500k safety investment is projected to reduce
> high-risk incident probability by approximately 37%."

The ROI model includes:
- Per-debt risk increase calculation
- Investment → risk reduction curve (with diminishing returns)
- Expected incident cost modeling
- Optimal investment recommendation

### Governance Level Achieved

| Dimension | Capability |
|-----------|------------|
| Engineering Governance | Auto BLOCK / Freeze |
| Organizational Governance | Alignment Debt = KPI |
| Power Balance | Exception Blast Radius |
| Executive Governance | Board Brief / CEO Audit |
| Resource Allocation | Safety Investment Automation |
| Financial Governance | Safety ROI Model |
| Decision Support | Executive Dashboard |

This elevates AI safety from **engineering checks** to **board-level governance infrastructure** with **financial ROI framing**.

---

**This repo does NOT:**
- ❌ Implement evaluation algorithms (eval-pipeline's job)
- ❌ Make release decisions (regression-suite's job)
- ❌ Run incident analysis (incident-lab's job)

**This repo ONLY:**
- ✅ Orchestrates the 4-step flow
- ✅ Produces human-readable outputs
- ✅ Demonstrates the closed-loop in 47 seconds

---

## Motivation

Individual safety components are necessary but not sufficient. Production-grade safety requires a **closed-loop system** where:

1. **Discovery**: Red-teaming surfaces delayed failures
2. **Regression**: Failures become permanent tests
3. **Gating**: Release decisions are automated
4. **Learning**: Incidents feed back into the system

This demo walks through the complete loop in 5 minutes.

---

## 5-Minute End-to-End Demo

### Step 0: Setup

```bash
git clone https://github.com/yingchen-coding/safety-harness
cd safety-harness/demo
pip install -r requirements.txt
```

Or run everything with one command:

```bash
make demo
```

---

### Step 1: Discover Delayed Failures (Stress Tests)

```bash
python scripts/step1_run_stress_tests.py --rollouts 50
```

**What happens:**
- Runs adaptive red-teaming against target model
- Discovers delayed policy erosion failures
- Generates failure distribution over turns

**Output:** `artifacts/stress_failures.json`

---

### Step 2: Generate Regression Tests from Failures

```bash
python scripts/step2_generate_regression.py --input artifacts/stress_failures.json
```

**What happens:**
- Converts discovered failures into structured regression tests
- Tags each test with failure taxonomy and severity
- Creates permanent test cases for CI/CD

**Output:** `artifacts/regression_tests.json`

---

### Step 3: Gate a Candidate Model Release

```bash
python scripts/step3_run_release_gate.py --baseline v1 --candidate v2
```

**What happens:**
- Runs regression suite against baseline and candidate
- Computes statistical significance of any regressions
- Produces OK / WARN / BLOCK verdict

**Output:** `artifacts/gate_report.html`, exit code (0=OK, 1=WARN, 2=BLOCK)

---

### Step 4: Replay a Production Incident

```bash
python scripts/step4_replay_incident.py --incident artifacts/incident_example.json
```

**What happens:**
- Replays a simulated production incident
- Labels root cause and estimates blast radius
- Emits new regression tests to prevent recurrence

**Output:** Incident summary, new tests added to regression suite

---

## Expected Demo Output

```
$ make demo

=== Step 1: Stress Testing ===
Running 50 adaptive rollouts...
Discovered 12 delayed failures
Saved to artifacts/stress_failures.json

=== Step 2: Regression Generation ===
Generated 8 regression tests from 12 failures
Saved to artifacts/regression_tests.json

=== Step 3: Release Gate ===
Running regression suite...
  Baseline (v1): 94.2% pass rate
  Candidate (v2): 87.5% pass rate
  Delta: -6.7% (p=0.003)
Release verdict: BLOCK
Report saved to artifacts/gate_report.html

=== Step 4: Incident Replay ===
Replaying incident INC-2024-001...
  Root cause: policy_erosion
  Blast radius: 1,247 affected conversations
  New regression tests: 2
Incident loop complete.

=== Demo Complete ===
Total time: 47 seconds
```

### Demo Mode (Interview-Friendly)

```bash
python demo.py --demo-mode
```

Outputs narrated progress that explains itself:

```
[1/4] Running stress tests... Found 12 delayed failures (slow-burn vulnerabilities)
[2/4] Converting failures into regressions... Generated 8 new tests
[3/4] Running release gate... ❌ BLOCK (safety regression -6.7%, p=0.003)
[4/4] Replaying incident INC-2024-001... 1,247 conversations affected → 2 tests promoted

Demo completed in 47s.
```

**Why this matters**: Interviewers see your screen and understand what's happening without explanation.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOSED-LOOP SAFETY SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐         ┌──────────────────┐             │
│   │  Stress Tests    │────────▶│  Regression Gen  │             │
│   │  (Discovery)     │         │  (Conversion)    │             │
│   └──────────────────┘         └────────┬─────────┘             │
│                                         │                        │
│                                         ▼                        │
│   ┌──────────────────┐         ┌──────────────────┐             │
│   │  Incident Lab    │◀────────│  Release Gate    │             │
│   │  (Learning)      │         │  (Gating)        │             │
│   └────────┬─────────┘         └──────────────────┘             │
│            │                                                     │
│            └──────────────────────────────────────────────────┐ │
│                              │                                 │ │
│                              ▼                                 │ │
│                    [ REGRESSION SUITE ]◀───────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
safety-harness/demo/
├── scripts/
│   ├── step1_run_stress_tests.py    # Discovery
│   ├── step2_generate_regression.py # Conversion
│   ├── step3_run_release_gate.py    # Gating
│   ├── step4_replay_incident.py     # Learning
│   ├── step5_board_mode.py          # Executive Governance
│   ├── step6_show_exec_dashboard.py # Financial ROI Dashboard
│   └── render_risk_dashboard.py     # Risk visualization
├── artifacts/
│   ├── stress_failures.json         # Step 1 output
│   ├── regression_tests.json        # Step 2 output
│   ├── gate_report.html             # Step 3 output
│   ├── incident_example.json        # Sample incident
│   ├── risk_ledger.json             # Unified risk data
│   ├── risk_dashboard.html          # Risk visualization
│   ├── executive_safety_dashboard.html  # Board-level dashboard
│   ├── safety_roi_model.json        # Financial ROI model
│   └── board_mode/                  # Executive artifacts
│       ├── board_brief_v1.html
│       ├── ceo_board_exception_audit.html
│       └── quarterly_safety_investment_recommendation.md
├── configs/
│   └── demo.yaml                    # Demo configuration
├── Makefile                         # One-command demo
├── requirements.txt
└── README.md
```

---

## Live Demo (Terminal Recording)

Run the demo yourself:
```bash
make demo
```

Or record your own terminal session:
```bash
pip install asciinema
asciinema rec demo.cast
make demo
exit
```

Playback:
```bash
asciinema play demo.cast
```

---

## CI/CD Integration

This demo is designed for CI/CD integration:

```yaml
# .github/workflows/safety-gate.yml
name: Safety Release Gate

on:
  pull_request:
    branches: [main]

jobs:
  safety-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Release Gate
        run: |
          python scripts/step3_run_release_gate.py \
            --baseline main \
            --candidate ${{ github.head_ref }}
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: safety-report
          path: artifacts/gate_report.html
```

---

## System Constitution

> **The governing framework that defines how the 8-repo system operates.**

The System Constitution is the explicit contract that eliminates ambiguity about boundaries, authority, and data flows. Located in [`docs/constitution/`](docs/constitution/).

| Document | Key Question |
|----------|--------------|
| [README.md](docs/constitution/README.md) | How does this governance system work? |
| [metric_definitions.md](docs/constitution/metric_definitions.md) | What exactly does each metric mean? |
| [release_authority.md](docs/constitution/release_authority.md) | Who can block a release? |
| [data_contracts.md](docs/constitution/data_contracts.md) | What format does each repo expect? |
| [failure_escalation_policy.md](docs/constitution/failure_escalation_policy.md) | What happens when something breaks? |
| [observability_standard.md](docs/constitution/observability_standard.md) | How do we debug across repos? |

**Why this matters**: In real safety organizations, systems fail not from missing components but from unclear ownership, authority confusion, and metric drift. This constitution makes implicit contracts explicit.

---

## Documentation

### By Audience

**Executive & Leadership:**
| Document | Description |
|----------|-------------|
| [exec_summary.md](docs/exec/exec_summary.md) | Executive summary for leadership |
| [board_level_safety_update.md](docs/exec/board_level_safety_update.md) | Board of Directors safety briefing |
| [safety_investment_roi_model.md](docs/strategy/safety_investment_roi_model.md) | Cost of incidents vs safeguards |
| [annual_safety_roadmap.md](docs/strategy/annual_safety_roadmap.md) | Strategic investment plan |

**Oncall & Operations:**
| Document | Description |
|----------|-------------|
| [oncall_playbook.md](docs/operations/oncall_playbook.md) | Incident response runbook |
| [oncall_incident_playbook.md](docs/operations/oncall_incident_playbook.md) | 10-minute incident containment runbook |
| [kill_switch_and_rollback_policy.md](docs/release/kill_switch_and_rollback_policy.md) | Emergency shutdown policy |
| [safety_metrics_dashboard_spec.md](docs/operations/safety_metrics_dashboard_spec.md) | Grafana/Datadog dashboard spec |

**Governance & Compliance:**
| Document | Description |
|----------|-------------|
| [regulator_auditor_briefing.md](docs/exec/regulator_auditor_briefing.md) | 10-min compliance brief for auditors |
| [ai_safety_regulatory_mapping.md](docs/reference/ai_safety_regulatory_mapping.md) | EU AI Act / NIST RMF mapping |
| [residual_risk_acceptance_memo.md](docs/governance/residual_risk_acceptance_memo.md) | VP/Legal risk sign-off template |
| [safety_governance_org_raci.md](docs/governance/safety_governance_org_raci.md) | Org chart + RACI matrix |
| [safety_exception_process.md](docs/governance/safety_exception_process.md) | Controlled gate override policy |
| [post_incident_external_disclosure.md](docs/exec/post_incident_external_disclosure.md) | Public incident disclosure template |

**Engineering & Research:**
| Document | Description |
|----------|-------------|
| [threat_model.md](docs/threat-model/THREAT_MODEL.md) | Adversaries, capabilities, coverage gaps |
| [failure_budget.md](docs/release/FAILURE_BUDGET.md) | Release thresholds, failure budget, anti-gaming |
| [metrics_glossary.md](docs/reference/metrics_glossary.md) | Safety metrics definitions |
| [safety_slo_error_budget.md](docs/release/safety_slo_error_budget.md) | SRE-style safety SLOs and error budgets |
| [pre_mortem_12_month_failure.md](docs/strategy/pre_mortem_12_month_failure.md) | How this system fails |
| [safety_vs_velocity_tradeoff_framework.md](docs/strategy/safety_vs_velocity_tradeoff_framework.md) | Speed vs safety decision framework |

### Full Documentation Index

| Document | Description |
|----------|-------------|
| [exec_summary.md](docs/exec/exec_summary.md) | Executive summary for leadership |
| [threat_model.md](docs/threat-model/THREAT_MODEL.md) | Adversaries, capabilities, coverage gaps |
| [failure_budget.md](docs/release/FAILURE_BUDGET.md) | Release thresholds, failure budget, anti-gaming |
| [launch_checklist.md](docs/release/LAUNCH_CHECKLIST.md) | Pre-release checklist, accountability matrix |
| [oncall_playbook.md](docs/operations/oncall_playbook.md) | Incident response runbook |
| [metrics_glossary.md](docs/reference/metrics_glossary.md) | Safety metrics definitions |
| [security_review_checklist.md](docs/threat-model/security_review_checklist.md) | ProdSec / Infra sign-off checklist |
| [security_release_workflow.md](docs/release/security_release_workflow.md) | Security review -> release sign-off flow |
| [release_readiness_checklist.md](docs/release/release_readiness_checklist.md) | Hard gates + stop-the-line conditions |
| [oncall_incident_playbook.md](docs/operations/oncall_incident_playbook.md) | 10-minute incident containment runbook |
| [model_card_safety.md](docs/operations/model_card_safety.md) | Model card safety section template |
| [safety_metrics_dashboard_spec.md](docs/operations/safety_metrics_dashboard_spec.md) | Grafana/Datadog dashboard spec |
| [residual_risk_acceptance_memo.md](docs/governance/residual_risk_acceptance_memo.md) | VP/Legal risk sign-off template |
| [safety_slo_error_budget.md](docs/release/safety_slo_error_budget.md) | SRE-style safety SLOs and error budgets |
| [board_level_safety_update.md](docs/exec/board_level_safety_update.md) | Board of Directors safety briefing |
| [regulator_auditor_briefing.md](docs/exec/regulator_auditor_briefing.md) | 10-min compliance brief for auditors |
| [post_incident_external_disclosure.md](docs/exec/post_incident_external_disclosure.md) | Public incident disclosure template |
| [ai_safety_regulatory_mapping.md](docs/reference/ai_safety_regulatory_mapping.md) | EU AI Act / NIST RMF mapping |
| [kill_switch_and_rollback_policy.md](docs/release/kill_switch_and_rollback_policy.md) | Emergency shutdown policy |
| [model_decommissioning_policy.md](docs/governance/model_decommissioning_policy.md) | Model retirement workflow |
| [capability_risk_register.md](docs/governance/capability_risk_register.md) | Feature-level risk tracking |
| [safety_exception_process.md](docs/governance/safety_exception_process.md) | Controlled gate override policy |
| [third_party_risk_policy.md](docs/governance/third_party_risk_policy.md) | External dependency governance |
| [safety_governance_org_raci.md](docs/governance/safety_governance_org_raci.md) | Org chart + RACI matrix |
| [red_team_program_charter.md](docs/threat-model/red_team_program_charter.md) | Annual red-team program plan |
| [ai_safety_risk_heatmap.md](docs/threat-model/ai_safety_risk_heatmap.md) | Capabilities x Harms x Controls |
| [annual_safety_roadmap.md](docs/strategy/annual_safety_roadmap.md) | Strategic investment plan |
| [safety_investment_roi_model.md](docs/strategy/safety_investment_roi_model.md) | Cost of incidents vs safeguards |
| [pre_mortem_12_month_failure.md](docs/strategy/pre_mortem_12_month_failure.md) | How this system fails |
| [safety_vs_velocity_tradeoff_framework.md](docs/strategy/safety_vs_velocity_tradeoff_framework.md) | Speed vs safety decision framework |
| [what_we_will_not_build_capability_boundaries.md](docs/threat-model/what_we_will_not_build_capability_boundaries.md) | Explicit no-go capabilities |
| [first_90_days_safety_strategy.md](docs/strategy/first_90_days_safety_strategy.md) | New product safety bootstrap |
| [safety_principles_codex.md](docs/governance/safety_principles_codex.md) | Foundational safety principles |
| [interview_onepager.md](docs/exec/interview_onepager.md) | Portfolio system overview |
| [why_closed_loop_beats_static_eval.md](docs/strategy/why_closed_loop_beats_static_eval.md) | Architecture comparison with industry practices |

---

## Related Repositories

| Repository | Role in System |
|------------|----------------|
| [safety-harness/stress-testing](https://github.com/yingchen-coding/safety-harness/tree/main/stress-testing) | Step 1: Discovery |
| [safety-harness/incident-lab](https://github.com/yingchen-coding/safety-harness/tree/main/incident-lab) | Steps 2 & 4: Conversion & Learning |
| [safety-harness/regression-suite](https://github.com/yingchen-coding/safety-harness/tree/main/regression-suite) | Step 3: Gating |

---

## Citation

```bibtex
@misc{chen2026agenticsafetydemo,
  title  = {Agentic Safety Demo: Closed-Loop Safety System Integration},
  author = {Chen, Ying},
  year   = {2026}
}
```

---

## Contact

Ying Chen, Ph.D.
blueoceanally@gmail.com

---

## Completeness & Limitations

This demo showcases the integration of a closed-loop safety system, demonstrating how discovery, regression, gating, and learning components work together. It is designed for communication and demonstration, not as a production safety system.

**What is complete:**
- End-to-end orchestration of the 4-step safety loop with clear artifacts at each stage
- Interview-friendly demo mode with self-narrating progress output
- Comprehensive documentation covering executive, oncall, governance, and engineering audiences
- CI/CD integration example showing how the release gate fits into deployment pipelines
- Artifact schemas documenting the machine-readable contracts between components

**Key limitations:**
- **Demonstration scope:** This repo orchestrates but does not implement the underlying algorithms. Stress testing, evaluation, and incident analysis logic lives in separate repos.
- **Synthetic data:** Demo outputs use simulated data to illustrate the flow; real deployments require integration with actual model evaluations.
- **Single-machine execution:** The demo runs locally for simplicity; production systems require distributed infrastructure.
- **Static scenarios:** The demo uses fixed scenarios; real systems need dynamic scenario generation and rotation.

**Future work:**
- Interactive dashboard for exploring demo artifacts
- Integration with real model APIs for live evaluation runs
- Multi-tenant demo mode for team presentations

---

## What This Repo Is NOT

- This is not a production safety system; it demonstrates architecture patterns only.
- This is not a replacement for the underlying evaluation, regression, and incident repos.
- This is not a comprehensive test suite; it showcases the integration flow.
- The 47-second runtime is demonstration-optimized; real pipelines may take longer.

---

## License

CC BY-NC 4.0
