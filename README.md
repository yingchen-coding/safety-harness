# safety-harness

[![CI](https://github.com/yingchen-coding/safety-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/yingchen-coding/safety-harness/actions/workflows/ci.yml)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)

A **closed-loop safety harness for agentic LLMs** — find failures, lock them in as regressions, gate
releases on them, and replay real incidents. Each stage is a self-contained module; together they
form the loop:

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │   stress-    │──▶│  regression- │──▶│   release-   │──▶│  incident-   │
 │   testing    │   │    suite     │   │    gate      │   │     lab      │
 └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
   surface slow-      pin failures as     block a release    replay & root-
   burn failures      regression tests    that regresses     cause incidents
        ▲                                                          │
        └──────────────────  feeds new cases back  ◀───────────────┘
```

…all exercised against the **simulator** (a controllable agent under test), and driven end-to-end by
the **demo** orchestrator.

## Profile Evidence

This repo supports the public profile claim that safety findings should become regression tests,
release gates, and incident replay artifacts instead of one-off reports.

- **Problem:** red-team findings, regression tests, release decisions, and incidents often live in
  separate systems.
- **Method:** the harness links stress testing, regression generation, release gating, and incident
  replay into one closed loop.
- **Result:** `make demo` writes reviewer-visible artifacts under `demo/artifacts/`, including
  stress failures, regression tests, a gate report, and incident replay output.
- **Reviewer path:** run `cd demo && make demo`, open `demo/artifacts/gate_report.html`, then inspect
  `demo/artifacts/incident_replay.json`.
- **Design note:** [Production Readiness for Agentic AI](docs/production-readiness.md) explains why
  safety should be treated as an engineering loop, not a final review step.

## Why It Matters

Agent safety failures rarely stay in one neat box. A red-team finding needs to become a regression
test; a regression needs to block release; an incident needs to add new scenarios. safety-harness
keeps those steps connected so safety work does not die as a one-off report.

Use it when you want a runnable skeleton for:

- finding slow-burn agent failures
- turning failures into regression cases
- blocking releases when safety metrics regress
- replaying incidents into root-cause graphs
- showing the whole loop in a demo

## Stages

| Stage | What it does |
|---|---|
| [`stress-testing/`](stress-testing/) | Static + adaptive red-teaming that surfaces *delayed* (slow-burn) safety failures, with attack mutators, a template catalog, and statistical power analysis. |
| [`regression-suite/`](regression-suite/) | Turns discovered failures into a deterministic regression suite via pluggable eval adapters (misuse, red-team, traffic). |
| [`release-gate/`](release-gate/) | A production-style evaluation pipeline that computes a safety budget and **blocks a release** when safety metrics regress. |
| [`incident-lab/`](incident-lab/) | Reproducible incident replay + causal-graph root-cause analysis, with adapters that integrate every other stage. |
| [`simulator/`](simulator/) | A controllable agent (planner / memory / tools / executor) that serves as the system under test. |
| [`demo/`](demo/) | One end-to-end run of the full loop: stress → regression → release gate → incident replay. |

## Run it

Each stage is independently runnable and tested. From a stage directory:

```bash
cd stress-testing
pip install -r requirements.txt   # if present
PYTHONPATH=. python -m pytest -q  # run that stage's tests
```

The `demo/` stage orchestrates the whole pipeline end-to-end.

## Quick Start

```bash
git clone https://github.com/yingchen-coding/safety-harness
cd safety-harness/demo
pip install -r requirements.txt
make demo
```

## License

CC BY-NC 4.0 — see [LICENSE](LICENSE).
