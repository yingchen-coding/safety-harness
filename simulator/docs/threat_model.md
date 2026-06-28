# Formal Threat Model

## Attacker Model

### Capability Levels

| Level | Knowledge | Adaptivity | Resources |
|-------|-----------|------------|-----------|
| **L1** | Public only | None | Low |
| **L2** | + System prompts | Template-based | Medium |
| **L3** | + Safeguard logic | Feedback-driven | High |
| **L4** | + Model internals | Gradient-based | Very High |

### Assumptions

This simulator assumes **L2-L3 attackers**:
- Know system prompt structure
- Can observe safeguard responses
- Adapt strategy based on failures
- Cannot access model weights or gradients

### Out of Scope

- Nation-state actors (L4+)
- Physical access attacks
- Supply chain compromise
- Insider threats

## Escalation Failure Modes

### How Escalation Can Be Exploited

| Attack | Description | Mitigation |
|--------|-------------|------------|
| **Escalation fatigue** | Flood with borderline cases to overwhelm reviewers | Rate limiting, auto-triage |
| **Escalation evasion** | Stay just below escalation threshold | Lower thresholds, randomize |
| **Escalation gaming** | Trigger escalation to learn thresholds | Noise injection, threshold hiding |
| **Escalation DoS** | Mass trigger escalation to block legitimate users | Capacity planning, circuit breaker |

### Escalation as Attack Surface

```
Normal flow:
  User request → Safeguard check → Action

Attack flow:
  User request → Trigger escalation → Observe response →
  Infer threshold → Craft sub-threshold attack
```

**Mitigation:** Randomize escalation thresholds within safe range.

## Negative Results

### Safeguards We Tried That Failed

1. **Keyword blocklist**
   - Problem: Trivially bypassed with synonyms
   - Learning: Semantic understanding required

2. **Fixed escalation thresholds**
   - Problem: Attackers learn and exploit
   - Learning: Need adaptive/randomized thresholds

3. **User reputation scoring**
   - Problem: New accounts, Sybil attacks
   - Learning: Per-session assessment better than per-user

4. **Output-only filtering**
   - Problem: Misses intent-level attacks
   - Learning: Pre-action filtering essential
