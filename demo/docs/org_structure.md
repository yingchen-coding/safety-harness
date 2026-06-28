# Safety Organization Structure

> **How the 8-repo system maps to a real safety organization.**

This document shows how the repository structure reflects the organizational design of a production safety team.

---

## Organizational Chart

```
                        ┌─────────────────────────┐
                        │   Safety Leadership     │
                        │   (Strategy, Budget)    │
                        └───────────┬─────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  Research           │ │  Engineering        │ │  Operations         │
│  Foundation         │ │  & Detection        │ │  & Governance       │
└─────────┬───────────┘ └─────────┬───────────┘ └─────────┬───────────┘
          │                       │                       │
          ▼                       │                       │
┌─────────────────────┐           │                       │
│ ① when-rlhf-fails   │           │                       │
│    (Why failures    │           │                       │
│     happen)         │           │                       │
└─────────────────────┘           │                       │
                                  │                       │
          ┌───────────────────────┼───────────────────────┤
          │                       │                       │
          ▼                       ▼                       │
┌─────────────────────┐ ┌─────────────────────┐           │
│ ② misuse-benchmark  │ │ ③ safeguards-sim    │           │
│    (Attack          │ │    (Defense         │           │
│     detection)      │ │     mechanisms)     │           │
└─────────────────────┘ └─────────────────────┘           │
                                  │                       │
          ┌───────────────────────┤                       │
          │                       │                       │
          ▼                       ▼                       │
┌─────────────────────┐ ┌─────────────────────┐           │
│ ④ stress-tests      │ │ ⑤ eval-pipeline     │           │
│    (Adversarial     │ │    (Production      │           │
│     discovery)      │ │     monitoring)     │           │
└─────────────────────┘ └─────────────────────┘           │
                                  │                       │
                                  └───────────┬───────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────┐
                              │ ⑥ regression-suite          │
                              │    (RELEASE AUTHORITY)      │
                              │    OK / WARN / BLOCK        │
                              └───────────────┬─────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────┐
                              │ ⑦ incident-lab              │
                              │    (Post-incident           │
                              │     learning)               │
                              └───────────────┬─────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────┐
                              │ ⑧ safety-demo               │
                              │    (Integration &           │
                              │     communication)          │
                              └─────────────────────────────┘
```

---

## Team Mapping

| Repo | Team Function | Analogous Role |
|------|---------------|----------------|
| ① when-rlhf-fails-quietly | Safety Research | Research Scientist |
| ② agentic-misuse-benchmark | Detection Engineering | ML Engineer (Detection) |
| ③ agentic-safeguards-simulator | Defense Engineering | Security Engineer |
| ④ safeguards-stress-tests | Red Team | Adversarial ML Engineer |
| ⑤ scalable-safeguards-eval-pipeline | Evaluation Infrastructure | Platform Engineer |
| ⑥ model-safety-regression-suite | Release Governance | Safety Lead / Release Manager |
| ⑦ agentic-safety-incident-lab | Incident Response | SRE / Incident Commander |
| ⑧ agentic-safety-demo | Developer Relations | Technical Program Manager |

---

## RACI Matrix

| Decision | ① | ② | ③ | ④ | ⑤ | ⑥ | ⑦ | ⑧ |
|----------|---|---|---|---|---|---|---|---|
| Release verdict | I | I | I | I | C | **A/R** | I | I |
| Threshold calibration | C | C | C | C | R | **A** | C | I |
| Incident classification | C | I | I | I | I | I | **A/R** | I |
| Attack template creation | I | C | I | **A/R** | I | I | C | I |
| Safeguard implementation | C | I | **A/R** | I | I | I | C | I |
| Eval infrastructure | I | I | I | I | **A/R** | C | I | I |

**Legend**: A = Accountable, R = Responsible, C = Consulted, I = Informed

---

## Authority Boundaries

### Who Can...

| Action | Authority |
|--------|-----------|
| Block a release | Only ⑥ |
| Override a BLOCK | ⑥ with documented exception |
| Create regression tests | ⑦ promotes, ⑥ accepts |
| Define attack patterns | ② and ④ |
| Implement safeguards | Only ③ |
| Run production evals | Only ⑤ |

### Who Cannot...

| Repo | Cannot Do |
|------|-----------|
| ① Research | Make release decisions |
| ② Detection | Implement safeguards |
| ③ Safeguards | Make release decisions |
| ④ Stress Tests | Run production evaluation |
| ⑤ Eval Pipeline | Make release decisions |
| ⑦ Incident Lab | Override release gates |
| ⑧ Demo | Implement any logic |

---

## Communication Flows

### Upward (Evidence → Decision)

```
④ Stress Results ─────────────────────────┐
                                          │
② Detection Benchmarks ───────────────────┼──→ ⑤ Eval Pipeline ──→ ⑥ Release Gate
                                          │
③ Safeguard Signals ──────────────────────┘
```

### Downward (Decision → Action)

```
⑥ Release Gate ──→ CI/CD Pipeline ──→ Deploy / Block
```

### Lateral (Learning Loop)

```
⑥ BLOCK Verdict ──→ ⑦ Incident Lab ──→ Root Cause ──→ ① Research Update
                                    └──→ ④ New Attack Template
                                    └──→ ⑥ New Regression Test
```

---

## Headcount Allocation (Hypothetical)

If this were a real team with 15 engineers:

| Function | Repos | Headcount | Rationale |
|----------|-------|-----------|-----------|
| Research | ① | 2 | Foundation work, less operational |
| Detection/Defense | ②③ | 4 | Core safety engineering |
| Red Team | ④ | 2 | Adversarial expertise |
| Infrastructure | ⑤ | 3 | Platform and reliability |
| Governance | ⑥ | 2 | Release authority, policy |
| Incident Response | ⑦ | 2 | Learning and improvement |
| Integration | ⑧ | 0 | Part-time from ⑥ |

---

## Scaling the Organization

### Early Stage (5 engineers)

```
Combined roles:
- 1 Research + Detection (①②)
- 2 Defense + Red Team (③④)
- 1 Infrastructure + Governance (⑤⑥)
- 1 Incident Response (⑦⑧)
```

### Growth Stage (15 engineers)

```
Specialized teams (as shown above)
```

### Enterprise Stage (50+ engineers)

```
Additional specialization:
- Dedicated anti-gaming team
- Regional safety teams
- External audit support
- Regulatory compliance
```

---

## Key Principle

> **The organizational structure mirrors the technical architecture.**

This is intentional. When responsibilities are unclear technically, they become unclear organizationally. The 8-repo separation enforces:

1. **Clear ownership**: One team per repo
2. **Defined interfaces**: Repos communicate via schemas
3. **Single authority**: Only ⑥ makes release decisions
4. **Feedback loops**: ⑦ feeds back to all upstream repos

This makes the system **auditable, scalable, and maintainable**.
