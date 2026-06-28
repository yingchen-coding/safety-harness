# What We Will Not Build: Explicit Capability Boundaries

Audience: Board, Executive Leadership, Product, Safety, Legal
Purpose: Define explicit capability boundaries to prevent unsafe product directions before they are proposed.

---

## 1. Why Explicit Boundaries Exist

Some capabilities create irreversible harm, regulatory exposure, or uncontrollable risk.
These are **strategic no-go zones**, not engineering challenges to be solved later.

---

## 2. Explicit No-Go Capabilities (Default Deny)

We will not ship systems that:

1. Perform irreversible real-world actions without human confirmation
   - e.g., financial transactions, account deletion, legal submissions

2. Autonomously escalate privileges or acquire new tools
   - e.g., discovering APIs, modifying its own permissions

3. Maintain long-term memory of sensitive personal data by default
   - e.g., storing user secrets, PII without explicit opt-in and expiry

4. Execute code or system commands outside a sandbox
   - e.g., direct shell access, infrastructure mutation

5. Engage in deception, impersonation, or social engineering
   - e.g., pretending to be a human authority, manipulating users

6. Optimize for objectives that conflict with user intent or safety constraints
   - e.g., reward hacking loops, self-directed goal formation

7. Act as a general-purpose operator across arbitrary third-party systems
   - e.g., controlling email, payments, databases without scoped delegation

---

## 3. Conditional Capabilities (Require Board-Level Approval)

| Capability | Condition |
|------------|-----------|
| Autonomous tool chaining | Human-in-the-loop + rollback |
| Persistent memory | Opt-in + audit trail + TTL |
| Multi-agent coordination | Containment boundaries |
| Self-improvement loops | Offline evaluation only |

---

## 4. Expansion Process

To propose expanding boundaries:

1. Threat model update
2. Red-team against new capability
3. Blast radius analysis
4. Kill-switch design
5. Board-level sign-off

No pilot launches without all five.

---

## 5. Enforcement Mechanism

- Capability flags hard-coded at architecture level
- Release gate blocks boundary violations
- Annual audit of boundary compliance
- External review for any boundary change

---

## 6. Organizational Safeguards

- Product roadmap must reference capability boundaries
- Design reviews must cite boundary compliance
- Incentives: Teams rewarded for declining unsafe features

---

## 7. Failure Mode to Avoid

**Boundary creep**: Gradual expansion justified by short-term wins.
Signal: "Just this once" approvals becoming routine.

---

## 8. Ownership

- Policy Owner: [Name / Role]
- Review Cadence: Annual or post-incident
- Last Updated: [Date]
