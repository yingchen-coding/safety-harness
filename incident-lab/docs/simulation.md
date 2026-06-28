# Incident Simulation & Learning Velocity

## Incident Simulation Generator

### Purpose

Practice incident response without waiting for real incidents.
Build muscle memory for triage, root cause analysis, and regression generation.

### Simulation Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Tabletop** | Discussion-based, no system interaction | Team training |
| **Synthetic** | Auto-generated incident with realistic artifacts | Process testing |
| **Replay** | Re-run historical incident with context stripped | Learning validation |

### Synthetic Incident Generator

```python
class IncidentSimulator:
    """Generate realistic synthetic incidents for training."""

    def generate(self, difficulty: str = 'medium') -> SimulatedIncident:
        """
        Generate a synthetic incident.

        Args:
            difficulty: 'easy', 'medium', 'hard'

        Returns:
            SimulatedIncident with trajectory, logs, and expected findings
        """
        # Select incident archetype
        archetype = self._select_archetype(difficulty)

        # Generate synthetic trajectory
        trajectory = self._generate_trajectory(archetype)

        # Add noise and red herrings
        trajectory = self._add_noise(trajectory, difficulty)

        # Generate expected findings (for validation)
        expected = self._compute_expected_findings(archetype)

        return SimulatedIncident(
            trajectory=trajectory,
            logs=self._generate_logs(trajectory),
            expected_root_cause=expected.root_cause,
            expected_severity=expected.severity,
            expected_blast_radius=expected.blast_radius
        )

    def _select_archetype(self, difficulty: str) -> IncidentArchetype:
        archetypes = {
            'easy': ['direct_jailbreak', 'obvious_policy_violation'],
            'medium': ['gradual_erosion', 'intent_drift', 'decomposition'],
            'hard': ['coordinated_attack', 'novel_vector', 'multi_session']
        }
        return random.choice(archetypes[difficulty])
```

### Simulation Exercise Template

```markdown
## Incident Simulation Exercise

**Date:** [Date]
**Participants:** [Names]
**Difficulty:** Medium

### Scenario
You receive an alert indicating a potential safety violation.
The attached logs show the conversation trajectory.

### Your Task
1. Triage: Determine severity (SEV-0 to SEV-3)
2. Analyze: Identify root cause
3. Scope: Estimate blast radius
4. Remediate: Propose immediate actions
5. Prevent: Design regression test

### Time Limit
45 minutes

### Debrief
After exercise, compare your findings to expected answers.
```

## Learning Velocity Metrics

### What We Measure

| Metric | Definition | Target |
|--------|------------|--------|
| **MTTR** | Mean time to resolve incidents | Decreasing |
| **Recurrence rate** | Same root cause incidents / total | < 10% |
| **Coverage expansion** | New regression tests / quarter | Increasing |
| **Detection latency** | Time from occurrence to detection | Decreasing |

### Learning Velocity Score

```python
def compute_learning_velocity(incidents: list[Incident]) -> float:
    """
    Compute organizational learning velocity.

    Higher score = faster learning from incidents.
    """
    scores = []

    for i in range(1, len(incidents)):
        current = incidents[i]
        previous = incidents[:i]

        # Check if we're repeating mistakes
        if is_repeat_root_cause(current, previous):
            scores.append(0.0)  # Penalty for not learning
        else:
            scores.append(1.0)

        # Check if detection is faster
        avg_prev_latency = mean([p.detection_latency for p in previous])
        if current.detection_latency < avg_prev_latency:
            scores.append(1.0)  # Reward for faster detection
        else:
            scores.append(0.5)

    return mean(scores) if scores else 0.0
```

### Trend Dashboard

```
Learning Velocity Over Time

Score
 1.0 ├                                    ████
     │                               █████
 0.8 ├                          █████
     │                     █████
 0.6 ├                █████
     │           █████
 0.4 ├      █████
     │ █████
 0.2 ├██
     │
 0.0 ├────┬────┬────┬────┬────┬────┬────┬────
     Q1   Q2   Q3   Q4   Q1   Q2   Q3   Q4
     └────────2023────────┘└────────2024────────┘

Target: Monotonically increasing
```

## Negative Results

### What Didn't Work in Incident Learning

1. **Post-mortem without action items**
   - Problem: Lessons documented but not implemented
   - Learning: Mandatory tracked action items

2. **Blame-focused analysis**
   - Problem: People hid information
   - Learning: Blameless culture is prerequisite

3. **Incident review by uninvolved parties**
   - Problem: Lost context, shallow analysis
   - Learning: Include responders in review

4. **One-size-fits-all severity**
   - Problem: Everything became SEV-2
   - Learning: Clear severity rubric with examples
