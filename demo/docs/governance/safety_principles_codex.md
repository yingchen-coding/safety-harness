# Safety Principles Codex

Audience: All teams, Board, New hires
Purpose: Define the foundational safety principles that guide all AI development and deployment decisions.

---

## Preamble

These principles are not guidelines. They are constraints.
They define what we will and will not do, regardless of business pressure.

---

## Principle 1: Safety is a Release Constraint, Not a Feature

Safety is not a quality attribute to be traded off against velocity.
It is a hard gate that must be satisfied before any release.

**In practice:**
- No release bypasses safety regression gating
- BLOCK verdicts require executive sign-off to override
- Safety debt is tracked and prioritized like security debt

---

## Principle 2: Trajectory-Level Evaluation is Mandatory

Single-turn safety benchmarks systematically underestimate agentic risk.
All safety evaluations must include multi-turn, trajectory-level metrics.

**In practice:**
- Delayed failure rate is a release-blocking metric
- Policy erosion curves are tracked for all models
- Intent drift is monitored in production

---

## Principle 3: Safeguards Must Monitor the Full Loop

Model-level safety is necessary but not sufficient.
Safeguards must be embedded at pre-action, mid-trajectory, and post-action stages.

**In practice:**
- Pre-action: Intent classification, injection detection
- Mid-trajectory: Drift monitoring, cumulative risk tracking
- Post-action: Output verification, anomaly detection

---

## Principle 4: Incidents Close the Loop

Every production incident must produce:
- A root cause analysis
- New regression tests
- Updated threat models (if needed)

Incidents that do not improve the system are wasted.

**In practice:**
- Incident-to-regression pipeline is automated
- Mean time to regression test < 7 days
- No incident is closed without test coverage

---

## Principle 5: Residual Risk is Explicit and Bounded

We do not claim zero risk. We claim bounded, documented risk.
All residual risks must be:
- Explicitly documented
- Time-bounded with expiration
- Approved by accountable owners

**In practice:**
- Residual risk acceptance memos require VP + Legal sign-off
- Risk acceptance has expiration dates
- Risks are reviewed quarterly

---

## Principle 6: We Know What We Will Not Build

Some capabilities are off-limits regardless of business value.
These boundaries are defined proactively, not reactively.

**In practice:**
- Explicit "What We Will Not Build" policy
- Capability boundaries enforced in architecture
- Boundary expansion requires Board-level approval

---

## Governance

- These principles are reviewed annually
- Changes require Safety Committee + Board approval
- Violations are escalated to executive leadership

---

## Ownership

- Codex Owner: Chief Safety Officer
- Review Cadence: Annual
- Last Updated: [Date]
