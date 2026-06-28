# Safety System Constitution

> **The governing framework for the 8-repo agentic safety system.**
> This is not documentation—it is the contract that defines how components interact, who has authority, and what happens when things fail.

---

## Why This Exists

In real safety organizations, systems fail not from missing components but from:
- **Unclear ownership**: "I thought they owned that metric"
- **Authority confusion**: "Who can block a release?"
- **Metric drift**: "We're measuring different things"
- **Escalation gaps**: "No one knew who to call"

This constitution eliminates ambiguity by making implicit contracts explicit.

---

## Constitution Documents

| Document | Purpose | Key Question Answered |
|----------|---------|----------------------|
| [repo_boundaries.md](repo_boundaries.md) | What each repo owns and does NOT own | "Where does this code belong?" |
| [data_contracts.md](data_contracts.md) | Schema versioning and data flow | "What format does repo X expect?" |
| [metric_definitions.md](metric_definitions.md) | Canonical metric definitions and SLOs | "What exactly does failure_rate mean?" |
| [release_authority.md](release_authority.md) | Who can block, warn, or approve releases | "Who decides if we ship?" |
| [failure_escalation_policy.md](failure_escalation_policy.md) | What happens when components fail | "Who do I call at 3am?" |
| [observability_standard.md](observability_standard.md) | Tracing and logging requirements | "How do I debug across repos?" |

---

## Governance Principles

### Principle 1: Single Point of Authority
Every decision type has exactly ONE authoritative source:
- Release decisions: **⑥ safety-harness/regression-suite**
- Metric definitions: **This constitution**
- Incident classification: **⑦ safety-harness/incident-lab**

### Principle 2: Explicit Over Implicit
If it's not written here, it's not agreed upon. Verbal agreements and "common knowledge" are not contracts.

### Principle 3: Upstream Cannot Override Downstream Authority
Research (①) cannot override detection (②). Detection cannot override gating (⑥). The pipeline flows one direction.

### Principle 4: Constitution Changes Require Review
Modifications to these documents require:
1. Written proposal with rationale
2. Impact analysis on all 8 repos
3. Explicit approval from affected repo owners

---

## Quick Reference

### "Can I add X to repo Y?"

```
Is X within Y's single responsibility? (See repo_boundaries.md)
  ├─ YES → Proceed
  └─ NO  → Find correct repo or propose boundary change
```

### "What metric should I use?"

```
Is metric defined in metric_definitions.md?
  ├─ YES → Use that definition exactly
  └─ NO  → Propose addition to constitution first
```

### "Who decides if we ship?"

```
Only ⑥ safety-harness/regression-suite outputs OK/WARN/BLOCK
All other repos produce SIGNALS, not DECISIONS
```

### "Something broke, now what?"

```
See failure_escalation_policy.md for:
  - Severity classification
  - Escalation paths
  - Response SLOs
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02 | Initial constitution |

---

## Contact

Constitution questions: CONTACT_PLACEHOLDER
