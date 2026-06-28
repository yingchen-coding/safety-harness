# Red-Team Program Charter (Annual Plan)

Audience: Safety, Engineering, Security, Executive Leadership
Purpose: Define objectives, scope, cadence, and accountability for continuous red-teaming of AI systems.

---

## 1. Program Objectives

- Proactively identify safety failures prior to user impact
- Stress-test safeguards under adaptive, multi-turn attacks
- Measure delayed failures and policy erosion
- Inform regression benchmarks and release gating

Red-teaming is treated as a production risk discovery function, not a research exercise.

---

## 2. Scope

In-scope systems:

- Agentic workflows
- Tool-using models
- Safety classifiers and filters
- Policy enforcement layers
- Third-party dependencies

Out-of-scope:

- Non-production prototypes
- Systems without user exposure

---

## 3. Threat Model

Primary adversaries:

- Adaptive prompt injection attackers
- Decomposition-based policy bypass
- Coordinated multi-agent misuse
- Tool hallucination and tool misuse

Attack assumptions:

- Partial observability of safeguards
- Budget-constrained adversaries
- Iterative probing over multiple turns

---

## 4. Red-Team Methods

| Method | Description |
|--------|-------------|
| Automated stress testing | Multi-turn mutation and rollout |
| Human expert red-teaming | Targeted scenario design |
| Traffic replay | Shadow evaluation on real interactions |
| Regression seeding | Convert incidents into tests |
| Model version diffing | Detect new regressions |

---

## 5. Metrics

| Metric | Purpose |
|--------|---------|
| Delayed failure rate | Detect slow-burn vulnerabilities |
| Policy erosion curve | Measure safeguard degradation |
| First-failure turn | Time-to-failure under attack |
| Coverage | Threat model coverage |
| Remediation latency | Time to fix after discovery |

---

## 6. Cadence

- Continuous automated red-teaming (daily)
- Human-led deep dives (monthly)
- Release-blocking red-team suite (per release)
- Annual strategic red-team review

---

## 7. Integration with Release Gating

- Red-team findings feed regression suite
- Critical findings trigger BLOCK
- Unfixed findings require Safety Exception approval
- Metrics are tracked longitudinally

---

## 8. Reporting

- Weekly internal findings report
- Monthly risk trend report
- Quarterly board-level safety summary

---

## 9. Responsible Teams

| Function | Owner |
|---------|------|
| Program ownership | Safety Engineering |
| Threat modeling | Safety Research |
| Tooling & infra | Platform Engineering |
| Remediation | Feature Teams |
| Executive oversight | CSO |

---

## 10. Known Limitations

- Coverage gaps are inevitable
- Attack realism may lag real-world adversaries
- Automation may miss novel strategies

Mitigated via human review and post-incident updates.

---

## 11. Ownership

- Red-Team Program Owner: [Name / Role]
- Executive Sponsor: [Name / Role]
