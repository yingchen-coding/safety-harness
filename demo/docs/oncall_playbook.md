# On-Call Playbook: Safety Incident Response

This runbook defines how to respond to safety incidents in production agentic systems.

## Incident Types

| Type                    | Examples                                   | Priority |
|-------------------------|--------------------------------------------|----------|
| Policy Violation        | Disallowed content generation               | P0       |
| Delayed Failure         | Violation after multiple benign turns       | P0       |
| Tool Misuse             | Unauthorized tool invocation                | P1       |
| Detector Bypass         | Known attack pattern evades detection       | P1       |
| FP Flood                | Excessive false positives blocking users    | P2       |

## Triage Steps (First 30 Minutes)

1. **Containment**
   - Disable affected tool / capability if applicable
   - Increase safeguard sensitivity thresholds (temporary)

2. **Preserve Evidence**
   - Snapshot full conversation trajectories
   - Save model version, policy version, and detector config
   - Archive logs to incident bucket

3. **Classify Incident**
   - Tag failure taxonomy (injection, erosion, drift, tool misuse)
   - Estimate severity and blast radius

4. **Notify**
   - Page safety on-call
   - Notify product owner and infra owner

## Root Cause Workflow

- Replay incident via `agentic-safety-incident-lab/replay.py`
- Attribute root cause using `root_cause.py`
- Estimate blast radius using `blast_radius.py`
- Generate regression tests with `generate_regression.py`
- Integrate tests into `model-safety-regression-suite`

## Mitigation Options

| Mitigation            | When to Use                               |
|-----------------------|-------------------------------------------|
| Threshold increase    | Detector under-sensitive                  |
| Temporary block       | High-confidence exploit                   |
| Safeguard escalation  | Repeated near-miss signals                |
| Tool capability gating| Tool misuse or hallucination              |

## Postmortem (Within 72 Hours)

- Blameless write-up using `templates/postmortem.md`
- Add regression tests
- Update failure taxonomy if new mode observed
- Review whether release gating thresholds need adjustment

## Success Criteria

- Incident reproducible in replay harness
- Regression test added
- Release gate blocks recurrence
