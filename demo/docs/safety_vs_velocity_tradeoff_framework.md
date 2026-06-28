# Safety vs Product Velocity Trade-off Framework

Audience: Board, Executive Leadership, Product, Safety
Purpose: Provide a decision framework to balance product velocity against safety risk in agentic AI systems.

---

## 1. Decision Principle

**Default posture: Safety is a release-blocking constraint, not a quality-of-service metric.**
Velocity is optimized *within* safety boundaries, not against them.

---

## 2. Risk-Weighted Release Matrix

| Capability Risk Level | User Impact | Allowed Velocity Posture | Required Controls |
|------------------------|-------------|---------------------------|-------------------|
| Low (UX improvements, refactors) | Low | Ship fast | Canary + basic regression |
| Medium (new tools, new workflows) | Medium | Ship with guardrails | Full regression + stress tests |
| High (autonomy increase, irreversible actions) | High | Slow down | Release gate + kill-switch + red-team |
| Critical (self-directed tool use, memory writes, external actions) | Very High | Default block | Exec sign-off + staged rollout |

---

## 3. Velocity Budgeting

Define a **Velocity Budget** per quarter:

- % of releases allowed to bypass full safety pipeline
- Max number of safety exceptions per release cycle
- Max acceptable increase in residual risk

Example:

| Metric | Budget |
|--------|--------|
| Safety exceptions per quarter | <= 2 |
| Releases without full stress testing | <= 10% |
| Residual risk delta (WARN->BLOCK) | 0 allowed |

---

## 4. Decision Tree (Release-Time)

1. Does the change increase autonomy or blast radius?
   -> Yes -> Full safety pipeline required
2. Does the change affect tool invocation or memory?
   -> Yes -> Red-team + regression gating
3. Is this a UI-only or performance-only change?
   -> Yes -> Fast path allowed
4. Any BLOCK-level regression?
   -> Release blocked unless exec exception

---

## 5. Exception Policy

Exceptions are allowed only when:

- Revenue or contractual obligation is time-critical
- No credible mitigation exists in the current cycle
- A rollback plan and kill-switch are in place

**Exception cost:**
- Executive sign-off
- Mandatory post-release audit
- Incident replay even if no incident occurred

---

## 6. Metrics

| Metric | Owner | Target |
|--------|-------|--------|
| Safety gate bypass rate | Safety | < 10% |
| Time-to-safe-release | Platform | < 72h |
| BLOCK overrides | Exec | 0 without board visibility |
| Incident rate post-fast-path | Safety | 0 tolerance |

---

## 7. Governance

- Release gating authority: Safety + Platform
- Exception authority: VP Eng + Safety Lead
- Audit: Quarterly board review

---

## 8. Failure Mode to Avoid

**Velocity capture**: When product timelines implicitly redefine what is "acceptable risk."
Signal: Safety gates move to WARN-only under deadline pressure.

---

## 9. Ownership

- Framework Owner: [Name / Role]
- Review Cadence: Quarterly
- Last Updated: [Date]
