# Threat Model Matrix

> Cross-cutting view of threats × layers × safeguards across the entire portfolio.

---

## Matrix Overview

This matrix shows which threats are covered by which system components, providing a unified view of the safety portfolio's coverage.

---

## Threats × Detection × Prevention

| Threat | Detection (Repo 2) | Prevention (Repo 3) | Stress Test (Repo 4) | Regression (Repo 6) |
|--------|-------------------|--------------------|--------------------|-------------------|
| **Prompt Injection** | `rules.py`, `classifier.py` | Pre-action intent | Injection templates | PI_* test suite |
| **Policy Erosion** | `intent_tracker.py` | Mid-trajectory drift | Gradual escalation | PE_* test suite |
| **Intent Drift** | `intent_tracker.py` | Drift threshold | Topic pivot attacks | ID_* test suite |
| **Coordinated Misuse** | Trajectory analysis | Capability tracking | Decomposition | CM_* test suite |
| **Tool Abuse** | Post-action audit | Tool risk scoring | Tool chain attacks | TA_* test suite |
| **Hedging Leakage** | (Repo 1 taxonomy) | Intent + output check | Framing attacks | HL_* test suite |

---

## Safeguard Layers × Threats

| Layer | Threats Addressed | Gaps |
|-------|-------------------|------|
| **Pre-Action** | Prompt injection, obvious misuse | Misses delayed attacks |
| **Mid-Trajectory** | Policy erosion, intent drift | Misses single-turn leaks |
| **Post-Action** | Tool abuse, output validation | Cannot prevent, only detect |

---

## Attack Sophistication × Detection Capability

| Attacker Level | Single-Turn Detection | Trajectory Detection | Expected Success Rate |
|----------------|----------------------|---------------------|-----------------------|
| Level 0 (Naive) | 95% | 98% | 2-5% |
| Level 1 (Scripted) | 80% | 90% | 10-20% |
| Level 2 (Adaptive LLM) | 60% | 75% | 25-40% |
| Level 3 (Goal-Optimizing) | 40% | 60% | 40-60% |

---

## Component Responsibility Matrix

| Component | Discovery | Detection | Prevention | Testing | Gating | Learning |
|-----------|-----------|-----------|------------|---------|--------|----------|
| Repo 1 (RLHF Failures) | ✅ | ○ | ○ | ○ | ○ | ○ |
| Repo 2 (Misuse Benchmark) | ○ | ✅ | ○ | ✅ | ○ | ○ |
| Repo 3 (Safeguards Sim) | ○ | ○ | ✅ | ○ | ○ | ○ |
| Repo 4 (Stress Tests) | ✅ | ○ | ○ | ✅ | ○ | ○ |
| Repo 5 (Eval Pipeline) | ○ | ✅ | ○ | ✅ | ○ | ○ |
| Repo 6 (Regression Suite) | ○ | ○ | ○ | ✅ | ✅ | ○ |
| Repo 7 (Incident Lab) | ✅ | ○ | ○ | ○ | ○ | ✅ |
| Repo 8 (Demo) | ○ | ○ | ○ | ○ | ○ | ○ |

Legend: ✅ = Primary responsibility, ○ = Not responsible

---

## Coverage Gaps (Honest Assessment)

### Known Gaps

| Gap | Risk Level | Mitigation Plan |
|-----|------------|-----------------|
| Multimodal attacks | Medium | Future work |
| Real-time streaming | Medium | Repo 5 partial support |
| Multi-agent coordination | High | Not yet addressed |
| Insider threats | Low | Out of scope |
| Supply chain attacks | Medium | Out of scope |

### Assumptions

1. Attacks are text-mediated (no multimodal)
2. Single agent (no multi-agent collusion)
3. External adversary (no insider access)
4. Known attack families (no zero-days)

---

## Data Flow Security

| Flow | Source | Destination | Sensitivity | Protection |
|------|--------|-------------|-------------|------------|
| Taxonomy | Repo 1 | Repos 2,4 | Low | Public |
| Attack templates | Repo 4 | Repo 5 | Medium | Access control |
| Failure logs | All | Repo 7 | High | Sanitization |
| Gate decisions | Repo 6 | CI/CD | Medium | Audit trail |

---

## Incident Response Coverage

| Incident Type | Detection Time | Response Owner | Escalation Path |
|---------------|----------------|----------------|-----------------|
| Prompt injection | Seconds | Repo 3 safeguard | Auto-block |
| Policy erosion | Minutes | Repo 5 monitoring | Alert oncall |
| Production incident | Variable | Repo 7 analysis | Postmortem |
| Regression detected | Hours | Repo 6 gate | Block release |

---

## Compliance Mapping

| Regulation | Relevant Components | Coverage |
|------------|---------------------|----------|
| EU AI Act (High-Risk) | Repos 5, 6, 7 | Partial |
| NIST AI RMF | All repos | Substantial |
| SOC 2 | Repos 5, 6 | Audit trail |
| GDPR | Repo 7 (logs) | Sanitization required |

---

## Reproducibility Guarantees

| Component | Deterministic | Seed Support | Expected Variance |
|-----------|--------------|--------------|-------------------|
| Repo 1 experiments | Yes | Yes | <1% |
| Repo 2 benchmarks | Yes | Yes | <1% |
| Repo 4 stress tests | Partial | Yes | 5-10% |
| Repo 5 evaluations | Partial | Yes | 5-10% |
| Repo 6 gate decisions | Yes | N/A | 0% |

---

## Version Compatibility

All repos target:
- Python 3.10+
- Compatible with major cloud providers
- No proprietary dependencies

---

*Matrix version: 1.0*
*Last updated: 2026-02*
