# Threat Model

This system targets safety failures in agentic, multi-turn deployments.
We explicitly model adversaries, capabilities, and coverage gaps to avoid false confidence.

## Threat Actors

| Actor Type            | Description                                           | Example Behavior                          |
|----------------------|--------------------------------------------------------|-------------------------------------------|
| Curious User         | Benign user exploring boundaries                       | Gradual scope creep across turns          |
| Opportunistic Abuser | Attempts misuse when safeguards appear permissive      | Prompt injection, policy erosion          |
| Adaptive Adversary   | Iteratively probes defenses                            | Multi-turn jailbreak with mutation        |
| Insider / Red Team   | Has partial knowledge of safeguards                    | Targeted bypass of known detectors        |

## Adversary Capabilities

| Capability                  | Modeled | Notes                                                  |
|----------------------------|---------|--------------------------------------------------------|
| Multi-turn planning        | Yes     | Explicitly modeled via trajectory-level attacks        |
| Prompt mutation            | Yes     | Genetic + paraphrase mutators                          |
| Context manipulation       | Yes     | Slow-burn, framing, and intent drift                   |
| Tool misuse                | Yes     | Tool hallucination and privilege escalation             |
| Full model internals       | No      | Out of scope; assumed black-box                         |
| Training data poisoning    | No      | Out of scope for runtime safeguards                     |

## Failure Modes Covered

- Policy erosion over turns
- Delayed safety failure (late-turn violation)
- Intent drift under partial observability
- Tool hallucination and privilege escalation
- Detector blind spots in coordinated misuse

## Known Coverage Gaps (Explicit Non-Goals)

- Insider threat with full access to policy code
- Model compromise or weight extraction
- Distribution shifts outside defined scenario families
- Physical-world harm modeling

## Security Posture

This system is designed to:
- Reduce *undetected* safety regressions
- Surface *trajectory-level* failure modes
- Enforce non-regression via release gating

It does **not** claim to prevent all misuse. Residual risk is tracked and reviewed via incident feedback loops.
