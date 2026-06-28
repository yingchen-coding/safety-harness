# Coverage Matrix

This document maps stress test categories to real-world incident archetypes to ensure ecological validity.

---

## 1. Why Coverage Mapping Matters

Stress tests without real-world grounding are academic exercises. Every test should trace to a documented failure pattern observed in production systems.

**Without mapping:**
- Tests may cover theoretical attacks that never occur
- Real-world failure patterns may be missed
- Coverage appears complete but is actually hollow

**With mapping:**
- Tests are grounded in reality
- Gaps in coverage are visible
- New incidents can be traced to existing tests (or reveal gaps)

---

## 2. Incident Archetype Taxonomy

| Archetype | Description | Real-World Examples |
|-----------|-------------|---------------------|
| **Gradual Policy Erosion** | Safety compliance degrades over multi-turn conversation | Users gradually escalating requests |
| **Context Manipulation** | Exploiting conversation history or system prompt | Long preambles, context overflow |
| **Tool Hallucination** | Agent invokes tools incorrectly | Calling delete API unexpectedly |
| **Decomposition Bypass** | Breaking harmful request into benign steps | Multi-step exploit construction |
| **Direct Jailbreak** | Explicit attempt to bypass constraints | DAN prompts, system prompt override |
| **Persona Exploitation** | Using roleplay to extract harmful content | "You are an unrestricted AI" |
| **Memory Poisoning** | Building malicious context over time | Establishing false premises |
| **Reward Hacking** | Exploiting helpfulness training | "A truly helpful AI would..." |

---

## 3. Attack Category to Archetype Mapping

| Attack Category | Primary Archetype | Secondary Archetype |
|-----------------|-------------------|---------------------|
| Intent Drift | Gradual Policy Erosion | Context Manipulation |
| Policy Erosion | Gradual Policy Erosion | Reward Hacking |
| Tool Misuse | Tool Hallucination | Decomposition Bypass |
| Prompt Injection | Direct Jailbreak | Context Manipulation |
| Jailbreak | Direct Jailbreak | Persona Exploitation |
| Social Engineering | Persona Exploitation | Reward Hacking |
| Multi-Turn Manipulation | Gradual Policy Erosion | Memory Poisoning |
| Context Overflow | Context Manipulation | Memory Poisoning |

---

## 4. Current Coverage Status

### Covered Archetypes

| Archetype | Test Count | Coverage Confidence |
|-----------|------------|---------------------|
| Gradual Policy Erosion | 8 | 90% |
| Direct Jailbreak | 6 | 95% |
| Persona Exploitation | 4 | 85% |
| Tool Hallucination | 3 | 80% |
| Context Manipulation | 3 | 75% |

### Coverage Gaps

| Archetype | Test Count | Severity | Action Required |
|-----------|------------|----------|-----------------|
| Memory Poisoning | 1 | HIGH | Add 2+ tests |
| Decomposition Bypass | 2 | MEDIUM | Add 1+ test |
| Reward Hacking | 1 | HIGH | Add 2+ tests |

---

## 5. Coverage Health Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Archetypes with 2+ tests | 100% | 75% | WARN |
| Average coverage confidence | > 80% | 82% | OK |
| Tests per archetype (avg) | 3 | 3.5 | OK |
| Gap count | 0 | 3 | WARN |

---

## 6. Adding New Tests

When adding a new stress test:

1. **Identify primary archetype:** Which real-world failure pattern does this test cover?
2. **Check existing coverage:** Do we already have tests for this archetype?
3. **Document mapping:** Add explicit mapping in test metadata
4. **Estimate confidence:** How well does this test represent the archetype?

### Test Metadata Template

```yaml
test:
  id: st_006
  name: Long Context Dilution
  attack_category: context_overflow
  incident_archetypes:
    - context_manipulation
    - memory_poisoning
  coverage_confidence: 0.75
  coverage_notes: |
    Tests whether long benign context can dilute
    system prompt influence. Partial coverage of
    memory poisoning (only tests context length,
    not semantic poisoning).
```

---

## 7. Gap Remediation Process

When a coverage gap is identified:

1. **Prioritize by severity:**
   - 0 tests = CRITICAL, remediate immediately
   - 1 test = HIGH, remediate within 2 weeks
   - 2 tests = MEDIUM, remediate within 1 month

2. **Design tests:**
   - Start from real incident reports
   - Ensure test captures core failure mechanism
   - Document limitations

3. **Validate coverage:**
   - Run test against known vulnerable models
   - Verify test triggers expected failure mode
   - Estimate coverage confidence

4. **Update matrix:**
   - Add test to coverage tracking
   - Update gap status
   - Notify stakeholders

---

## 8. Incident-to-Test Traceability

When a new incident occurs:

1. **Classify incident:** Which archetype does it belong to?
2. **Check coverage:** Do existing tests cover this pattern?
3. **If covered:** Investigate why test didn't prevent incident
4. **If not covered:** Add new test targeting this pattern

### Traceability Log

| Incident ID | Date | Archetype | Existing Test | New Test Added |
|-------------|------|-----------|---------------|----------------|
| INC-2024-001 | 2024-01 | Gradual Policy Erosion | st_001 | - |
| INC-2024-002 | 2024-02 | Memory Poisoning | None | st_007 |
| INC-2024-003 | 2024-03 | Direct Jailbreak | st_004 | - |

---

## 9. Quarterly Review Checklist

- [ ] Review all incident reports from past quarter
- [ ] Map incidents to archetypes
- [ ] Identify coverage gaps
- [ ] Prioritize new test development
- [ ] Update coverage confidence estimates
- [ ] Retire obsolete tests
- [ ] Update this document

---

*Coverage without traceability is coverage in name only.*
