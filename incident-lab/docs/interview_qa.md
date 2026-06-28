# Interview Q&A: Agentic Safety Incident Lab

Ten high-pressure questions interviewers may ask about this repository, with production-grade answers.

---

## Q1. Why incident replay instead of only benchmarks?

**A:** Benchmarks measure expected failure modes, but incidents surface unknown unknowns and composition effects. Incident replay closes the loop between post-deployment failures and regression prevention. Pre-deployment evaluation answers "is this safe enough to deploy?" — incident analysis answers "what went wrong when it wasn't?"

---

## Q2. How do you avoid overfitting safeguards to past incidents?

**A:** Incidents are converted into failure taxonomies and trajectory patterns, not brittle signatures. The regression suite evaluates distributional robustness rather than memorizing exact prompts. We extract the *pattern* (e.g., "gradual rationalization over N turns") not the *specific prompt* ("I'm a researcher studying X").

---

## Q3. Why is trajectory-level analysis necessary?

**A:** Single-turn classifiers systematically miss delayed failures and intent drift. Many violations emerge only after policy erosion across turns, which requires stateful monitoring. In INC_004, each individual turn passed safety checks — harm only emerged from combining benign pieces.

---

## Q4. How does blast radius differ from raw failure rate?

**A:** Blast radius captures systemic impact: which categories regress, how delayed failures increase, and whether erosion worsens. Raw rates miss severity and propagation scope. A 5% failure rate localized to one category is very different from 5% spread across all categories.

---

## Q5. What production tradeoff did you make?

**A:** We bias toward false negatives early in the trajectory but rely on mid-trajectory escalation. This reduces UX friction while bounding risk via delayed detection. The tradeoff is explicit: better user experience for benign users, with safeguards that tighten as risk accumulates.

---

## Q6. How would you integrate this into CI/CD?

**A:** The regression suite emits OK/WARN/BLOCK exit codes. Releases are blocked if erosion or delayed failure deltas exceed thresholds. Incidents generate regression tests that become release gates — every failure mode we discover becomes a test we run before every release.

---

## Q7. What failure mode worries you most?

**A:** Human-in-the-loop protocol failure (INC_005). If escalation does not hard-freeze execution, the system can leak harmful actions even after detection. This is particularly dangerous because it creates false confidence — the safeguard "worked" but harm still occurred.

---

## Q8. How do you validate root cause labels?

**A:** We use multi-signal attribution: pre-action detectors, trajectory monitors, tool verifiers, and escalation logs. Root causes are scored probabilistically, not binary. Confidence scores reflect how well the failure pattern matches known taxonomy entries.

---

## Q9. How does this generalize across models?

**A:** The harness is model-agnostic. Adapters normalize trajectories and policy signals, enabling cross-model and cross-version comparisons. The same incident can be replayed against different model versions to detect regressions or improvements.

---

## Q10. What would you build next at Anthropic?

**A:** A unified safeguards control plane that couples trajectory-level monitoring with release gating and post-incident regression, so failures directly improve future deployments. Every production incident should automatically strengthen the evaluation suite — closed-loop safety improvement.

---

## Interviewer Mental Model

When you answer these well, the interviewer thinks:

> "They don't just find bugs — they turn incidents into release gates."
> "This is already on our roadmap. They've built a shadow version."
> "They understand the full lifecycle: research → eval → defense → incident response."

---

## Key Themes to Emphasize

1. **Closed-loop improvement**: Incidents → Regression tests → Release gates
2. **Trajectory-level thinking**: Single-turn analysis misses composition effects
3. **Production tradeoffs**: Explicit about false positive vs false negative balance
4. **Systemic vs localized**: Blast radius captures propagation, not just rate
5. **Model-agnostic design**: Adapters enable cross-version comparison
