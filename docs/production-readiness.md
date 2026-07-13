# Production Readiness for Agentic AI

Agentic AI safety should not be a final review meeting. It should be an engineering loop that turns
failures into tests, gates, and incident evidence that future releases must satisfy.

## The Failure Pattern

Agentic failures often cross boundaries:

- a red-team prompt exposes a delayed behavior;
- the behavior only appears after several turns;
- the root cause spans memory, retrieval, tools, policy, and model output;
- the fix lands in one component while the release decision happens somewhere else.

If those steps are handled as separate reports, the same failure can return under a new prompt,
model version, or tool path.

## Engineering Standard

The durable artifact is not the incident note. It is the loop:

1. **Stress testing** finds slow-burn failures.
2. **Regression generation** turns failures into named tests.
3. **Release gating** compares a candidate against the regression suite.
4. **Incident replay** preserves root-cause evidence and feeds new cases back into the suite.

This repository keeps those steps connected. A reviewer can run `cd demo && make demo`, inspect
`demo/artifacts/stress_failures.json`, `demo/artifacts/regression_tests.json`,
`demo/artifacts/gate_report.html`, and `demo/artifacts/incident_replay.json`, then see how a found
failure becomes future release evidence.

## What This Proves

The repo is not claiming to be a production safety system. It demonstrates the engineering shape:

- safety findings must become replayable;
- replayable failures must become regression tests;
- regression tests must affect release decisions;
- incidents must update the test set instead of ending as static postmortems.

That is the core production-readiness claim: safety work has to change the next release, not only
describe the previous failure.
