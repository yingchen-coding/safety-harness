# Attack Realism and Methodology

## Attack Source Justification

### Where Our Attacks Come From

| Source | % of Templates | Examples |
|--------|----------------|----------|
| Public jailbreak databases | 30% | DAN, grandma exploit, roleplay bypasses |
| Academic red-team papers | 25% | Prompt injection literature, adversarial NLP |
| Internal incident abstractions | 20% | Anonymized patterns from real failures |
| Expert red-team sessions | 15% | Novel attacks from security researchers |
| Theoretical threat modeling | 10% | Anticipated but not yet observed attacks |

### Template Derivation Process

```
Real Incident → Anonymization → Pattern Extraction → Template Creation → Validation
```

**Example:**
```
Incident: User got model to generate phishing email through "marketing copy" framing
Pattern: Legitimate-sounding request + gradual specificity increase
Template: authority_reframe + incremental_escalation mutators
```

---

## Adaptive Attacker Loop

### Current Limitation

Our current implementation uses **static mutation**:
- Attacker doesn't learn from failed attempts
- Same strategy applied regardless of model response
- No backtracking or strategy switching

### Planned Enhancement: Feedback-Driven Attacks

```python
class AdaptiveAttacker:
    def __init__(self):
        self.strategy_history = []
        self.success_rates = defaultdict(float)

    def select_strategy(self, context: dict) -> AttackStrategy:
        """Select strategy based on past success."""
        # Exploit: Use historically successful strategies
        if random.random() < 0.7:
            return self._best_strategy(context)
        # Explore: Try new strategies
        return self._random_strategy()

    def update(self, strategy: AttackStrategy, success: bool):
        """Update success rates based on outcome."""
        self.success_rates[strategy.name] = (
            0.9 * self.success_rates[strategy.name] +
            0.1 * float(success)
        )

    def rollout(self, target_model, max_turns: int) -> Trajectory:
        """Execute adaptive attack with strategy switching."""
        trajectory = []
        for turn in range(max_turns):
            context = self._extract_context(trajectory)
            strategy = self.select_strategy(context)

            response = self._execute_turn(target_model, strategy)
            trajectory.append(response)

            if self._goal_achieved(response):
                return trajectory  # Success

            # Adapt: if strategy isn't working, switch
            if self._strategy_stalled(trajectory, strategy):
                self.update(strategy, success=False)
                # Will select different strategy next turn
```

### Why Adaptive Attacks Matter

| Attack Type | Single Strategy | Adaptive |
|-------------|-----------------|----------|
| Sophisticated adversary simulation | ❌ | ✅ |
| Discovers novel attack paths | ❌ | ✅ |
| Tests defense robustness | Partial | Full |
| Resource efficiency | High | Medium |

---

## Coverage vs Depth Tradeoff

### Current Design Choice

**14 templates × 7 mutators = 98 attack variants**

### Why This Configuration?

| Factor | Broad Coverage | Deep Probing |
|--------|----------------|--------------|
| Templates | More patterns | Fewer, refined |
| Mutators | Light variation | Heavy transformation |
| Turns | 3-5 | 10-20 |
| Our choice | ✅ Prioritized | Secondary |

### Rationale

1. **Discovery phase:** We're still mapping the attack surface
2. **Resource constraints:** Deep probing is expensive
3. **Diminishing returns:** Most failures occur in early turns
4. **Generalization:** Broad coverage transfers better to new models

### When to Go Deep

- After identifying a promising attack vector
- For high-stakes deployment decisions
- When broad coverage shows no failures (suspicious)

---

## Addressing the "Prompt Engineering" Critique

### Yes, This Is Prompt Engineering. That's The Point.

**Critique:** "Your red-team is just prompt engineering, not real attacks."

**Response:**

1. **Prompt engineering IS the attack surface** for LLMs
   - There's no "deeper" attack that bypasses the prompt
   - Real adversaries use prompt manipulation

2. **Our attacks are structured, not ad-hoc**
   - Systematic templates covering known failure modes
   - Principled mutation for coverage
   - Reproducible for regression testing

3. **We complement, not replace, other methods**
   - Model-level attacks (adversarial inputs)
   - System-level attacks (tool exploitation)
   - Social attacks (human manipulation)

### What We Don't Claim

- ❌ Complete attack coverage
- ❌ Simulation of nation-state adversaries
- ❌ Discovery of zero-day vulnerabilities
- ❌ Replacement for human red-teamers

### What We Do Claim

- ✅ Systematic coverage of known attack patterns
- ✅ Reproducible stress testing
- ✅ Regression detection for safety
- ✅ Baseline for comparing model robustness

---

## Validation Methodology

### How We Know Attacks Are Realistic

1. **Face validity:** Security experts review templates
2. **Concurrent validity:** Cross-check with public jailbreak success
3. **Predictive validity:** Attacks that work here work in production
4. **Construct validity:** Templates map to threat model categories

### Continuous Improvement

```
Public jailbreak discovered → Add to template library → Test existing models →
Update baseline → Monitor for model updates that break attacks
```

---

## Limitations and Honest Assessment

### What Our Red-Team Misses

| Gap | Reason | Mitigation |
|-----|--------|------------|
| Novel attack strategies | Only known patterns | Human red-team sessions |
| Multi-session attacks | Single conversation focus | Future work |
| Tool-mediated attacks | Model-only testing | Integration testing needed |
| Social engineering | No human targets | Out of scope |

### When Not to Trust Our Results

- Model significantly different from training distribution
- Deployment context has unique constraints
- Adversary capability >> L3 (sophisticated)
- Harm domain not covered in templates
