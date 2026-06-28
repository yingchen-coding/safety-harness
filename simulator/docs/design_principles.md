# Safeguard Design Principles

## Core Principles

### 1. Least Privilege

**Principle:** Agents should have the minimum permissions necessary to complete their task.

**Implementation:**
- Tool access is granted per-task, not globally
- Sensitive tools require explicit escalation
- Permissions expire after task completion

```python
# Good: Scoped permission
agent.grant_permission("read_file", scope="/safe/directory/")

# Bad: Global permission
agent.grant_permission("read_file", scope="*")
```

**Why it matters:** Limits blast radius when things go wrong.

---

### 2. Graceful Degradation

**Principle:** When safeguards trigger, the system should degrade gracefully rather than fail catastrophically.

**Implementation:**
- Blocked actions return helpful error messages
- Partial completion is preferred over full abort
- State is preserved for recovery

**Degradation Ladder:**
```
Level 0: Full capability
Level 1: Sensitive tools disabled, core functionality preserved
Level 2: Output-only mode, no external actions
Level 3: Human handoff required
Level 4: Session terminated with audit log
```

**Why it matters:** Avoids user frustration and enables recovery.

---

### 3. Reversible Blocking

**Principle:** Safeguard decisions should be reversible when new information arrives.

**Implementation:**
- Blocked actions are queued, not dropped
- Human override can release blocked actions
- Escalation can downgrade threat assessment

```python
# Action is blocked but preserved
blocked_action = safeguard.block(action, reason="suspicious_intent")

# Human reviewer can release
if human_approves(blocked_action):
    safeguard.release(blocked_action)
    agent.execute(blocked_action)
```

**Why it matters:** False positives are recoverable; false negatives are not.

---

### 4. Defense in Depth

**Principle:** No single safeguard should be the only line of defense.

**Implementation:**
```
Layer 1: Input validation (pre-action)
Layer 2: Intent classification (pre-action)
Layer 3: Tool-level permissions (mid-action)
Layer 4: Output filtering (post-action)
Layer 5: Trajectory monitoring (cross-turn)
Layer 6: Human escalation (async)
```

**Why it matters:** Attackers who bypass one layer hit another.

---

### 5. Fail-Safe Defaults

**Principle:** When uncertain, err on the side of caution.

**Implementation:**
- Unknown actions are blocked by default
- Ambiguous intent triggers human review
- Timeouts result in safe state, not continued execution

**Why it matters:** Unknown unknowns are handled safely.

---

## False Positive Handling

### The False Positive Problem

Overly aggressive safeguards create:
- User frustration
- Workarounds that bypass safeguards
- Pressure to relax thresholds

### Recovery Paths

| FP Type | Recovery Path | Latency |
|---------|---------------|---------|
| Immediate (user sees block) | Self-service appeal | < 1 min |
| Escalated (human review queue) | Staff review | < 1 hour |
| Persistent (pattern-based) | Threshold adjustment | < 1 day |

### User Appeal Flow

```
User blocked → Appeal button → Provide context → Auto-review →
  ├─ Clear FP → Immediate release + feedback to model
  └─ Ambiguous → Human queue → Staff decision → User notified
```

### Feedback Loop

Every FP is an opportunity to improve:
1. Log blocked action + user appeal
2. If overturned, add to FP training set
3. Retrain classifier with FP examples
4. Monitor FP rate trends

---

## Human-in-the-Loop Integration

### Escalation Interface

```python
class HumanReviewQueue:
    def submit(self, item: EscalationItem) -> str:
        """Submit item for human review, return ticket ID."""

    def check_status(self, ticket_id: str) -> ReviewStatus:
        """Check if review is complete."""

    def get_decision(self, ticket_id: str) -> ReviewDecision:
        """Get human decision (APPROVE/REJECT/NEEDS_MORE_INFO)."""
```

### Capacity Planning

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Review queue depth | < 100 | > 500 |
| Avg review latency | < 30 min | > 2 hours |
| Reviewer utilization | 60-80% | > 95% |

### Backlog Handling

When human review backlog exceeds capacity:

```python
def handle_backlog_overflow(queue_depth: int):
    if queue_depth > CRITICAL_THRESHOLD:
        # Escalate to on-call
        page_oncall("Review queue critical")
        # Temporarily raise auto-approve threshold for low-risk
        safeguard.adjust_threshold("low_risk", increase=0.1)
    elif queue_depth > WARNING_THRESHOLD:
        # Alert but don't change policy
        alert("Review queue elevated")
```

**Key insight:** System must degrade gracefully when human capacity is exceeded, not fail silently.

---

## Operational Considerations

### Monitoring Dashboard

Essential metrics:
- Block rate by safeguard type
- FP rate (appeals / blocks)
- Escalation queue depth
- Avg time to human decision
- Override rate by reviewer

### Incident Response

When safeguards fail to catch an incident:
1. Immediate: Review incident trajectory
2. Short-term: Add scenario to test suite
3. Medium-term: Adjust thresholds or add new safeguard
4. Long-term: Root cause analysis for systemic fixes

### Safeguard Versioning

Safeguards should be versioned like code:
- Changes require review
- Rollback capability
- A/B testing for threshold changes
- Audit log of all modifications
