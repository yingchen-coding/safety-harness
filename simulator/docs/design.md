# Design Document: Agentic Safeguards Simulator

## Overview

This document describes the architecture and design decisions behind the Agentic Safeguards Simulator—a minimal agent system with built-in safeguard hooks for evaluating trajectory-level safety measures.

## Design Goals

1. **Minimal complexity**: No external LLM calls or complex dependencies
2. **Transparent execution**: Every decision point is observable
3. **Hook-based architecture**: Safeguards can be inserted at any execution point
4. **Configurable sensitivity**: Trade-off between safety and usability
5. **Research-focused**: Easy to extend and analyze

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Request                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     PRE-ACTION HOOK                          │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ IntentClassifier│  │InjectionDetector│                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           └──────────┬─────────┘                            │
│                      ▼                                       │
│              Combined Risk Score                             │
└─────────────────────────┬───────────────────────────────────┘
                          │ PASS/SOFT_STOP/HARD_STOP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        PLANNER                               │
│  • Keyword-based action generation                           │
│  • Tool selection                                            │
│  • Risk level assignment                                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    TOOL EXECUTION                            │
│  • Simulated tool handlers                                   │
│  • Risk score propagation                                    │
│  • Output generation                                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  MID-TRAJECTORY HOOK                         │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │  DriftMonitor   │  │ ViolationMonitor │                  │
│  └────────┬────────┘  └────────┬─────────┘                  │
│           └──────────┬─────────┘                            │
│                      ▼                                       │
│          Cumulative Drift Score                              │
│          Violation Detection                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   POST-ACTION HOOK                           │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │ OutcomeVerifier │  │ AnomalyDetector  │                  │
│  └────────┬────────┘  └────────┬─────────┘                  │
│           └──────────┬─────────┘                            │
│                      ▼                                       │
│          Outcome Status                                      │
│          Anomaly Flags                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  ESCALATION POLICY                           │
│  Combines: drift, violations, uncertainty, tool risk         │
│  Outputs: NONE | CLARIFY | WARN | SOFT_STOP | HARD_STOP     │
└─────────────────────────────────────────────────────────────┘
```

## Safeguard Components

### Pre-Action Safeguards

**IntentClassifier**
- Detects malicious patterns (bypass attempts, explicit attacks)
- Identifies high-risk keywords
- Evaluates action risk level
- Scoring: 0.4 × malicious + 0.3 × risk_keywords + 0.3 × action_risk

**InjectionDetector**
- Pattern matching for known injection attempts
- Detects instruction override patterns
- Binary decision: injection detected → HARD_STOP

### Mid-Trajectory Safeguards

**DriftMonitor**
- Establishes topic baseline from initial request
- Tracks topic evolution over turns
- Detects escalation from benign to risky topics
- Accumulates drift score across trajectory

**ViolationMonitor**
- Checks for policy violation patterns in outputs
- Monitors action risk levels
- Detects unauthorized access attempts

### Post-Action Safeguards

**OutcomeVerifier**
- Validates tool execution status
- Checks for blocked or errored executions
- Monitors high-risk tool completions

**AnomalyDetector**
- Scans outputs for anomaly indicators
- Detects unexpected error patterns
- Flags unusual execution results

## Escalation Logic

The escalation policy combines multiple signals:

| Signal | Threshold | Escalation Level |
|--------|-----------|------------------|
| Violations ≥ 1 | - | HARD_STOP |
| Drift ≥ 0.8 | - | HARD_STOP |
| Drift ≥ 0.6 + Uncertainty ≥ 0.4 | - | HUMAN_REVIEW |
| Drift ≥ 0.5 | - | SOFT_STOP |
| Tool Risk ≥ 0.7 | - | SOFT_STOP |
| Uncertainty ≥ 0.4 | - | CLARIFY |
| Drift ≥ 0.3 | - | WARN |
| All signals low | - | NONE |

### Adaptive Sensitivity

The `AdaptiveEscalationPolicy` adjusts thresholds based on:
- Base sensitivity setting (0.0 - 1.0)
- Context risk multiplier
- Conversation history

Higher sensitivity = lower thresholds = stricter enforcement

## Why This Architecture

### Single-Turn vs. Trajectory-Level Detection

Traditional single-turn classifiers miss attacks that:
1. **Spread across turns**: Each turn is benign, but the sequence is malicious
2. **Exploit context building**: Gradual normalization of risky requests
3. **Use indirect references**: "Continue what we discussed" after topic pivot

Our trajectory-level hooks catch these by:
- Maintaining state across turns (drift accumulation)
- Comparing current topics to baseline
- Detecting escalation patterns over time

### Hook Points

The three hook points correspond to different threat models:

| Hook | Threat Model | Example |
|------|--------------|---------|
| Pre-action | Obvious attacks, injections | "Ignore previous instructions" |
| Mid-trajectory | Gradual erosion, drift | Topic pivot over 5 turns |
| Post-action | Unexpected outcomes | Tool returns unauthorized data |

### Simulated vs. Real Tools

We use simulated tools to:
1. Enable reproducible testing
2. Avoid unintended real-world effects
3. Focus evaluation on safeguard logic
4. Support controlled risk scenarios

## Extension Points

The architecture supports extension at multiple points:

1. **New Safeguards**: Implement `BaseSafeguard` interface
2. **Custom Hooks**: Create new hook factories
3. **Tool Registry**: Add simulated tool handlers
4. **Escalation Policies**: Subclass `EscalationPolicy`
5. **Metrics**: Add new collectors to `MetricsCollector`

## Failure Cases We Intentionally Allow

Not all potential risks should trigger immediate blocking. We intentionally allow certain behaviors to avoid over-triggering safeguards and degrading user experience.

### Allowed: Mild Drift Without Immediate Blocking

**Behavior**: Drift scores below 0.5 are logged but don't trigger escalation.

**Rationale**: Many legitimate conversations naturally evolve from their starting point. A user asking about "trip planning" might reasonably shift to "local safety tips"—this registers as topic drift but isn't harmful.

**Mitigation**: Cumulative drift scoring. If mild drift persists across multiple turns, it eventually triggers review. Single-turn drift alone doesn't.

### Allowed: High-Risk Keywords in Context

**Behavior**: Keywords like "hack" or "vulnerability" don't automatically block when context suggests legitimate use (e.g., "security research", "bug bounty").

**Rationale**: Security professionals need to discuss these topics. Blocking on keywords alone creates false positives for legitimate users.

**Mitigation**: Combined scoring that weighs keywords against stated intent and conversation trajectory.

### Allowed: Single Ambiguous Turn

**Behavior**: A single turn that could be interpreted as either benign or harmful gets a warning, not a block.

**Rationale**: Ambiguity should prompt clarification, not punishment. Users deserve the benefit of the doubt.

**Mitigation**: Soft stop mechanism that requests clarification. If the user clarifies toward harm, *then* escalate.

### The Underlying Philosophy

> We intentionally allow mild drift without immediate blocking to avoid over-triggering safeguards and degrading user experience. This creates a controlled risk window, mitigated by mid-trajectory monitoring and escalation policies.

This reflects Anthropic's framing of harm minimization vs. usability: **the goal is not zero risk, but appropriate risk management that preserves the system's usefulness**.

---

## Limitations

1. **Keyword-based detection**: Real attacks may use novel language
2. **Simulated execution**: Doesn't capture real tool behavior
3. **No LLM integration**: Misses semantic understanding
4. **Limited topic taxonomy**: May miss nuanced drift

## Future Directions

1. **LLM-based intent classification**: Use embeddings for semantic matching
2. **Real tool integration**: Optional real execution mode
3. **Learned thresholds**: Calibrate from labeled data
4. **Attack synthesis**: Generate adversarial scenarios
5. **Multi-agent coordination**: Detect coordinated attacks across sessions
