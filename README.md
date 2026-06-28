# Agentic Safety System

A **closed-loop safety system for agentic LLMs** — find failures, lock them in as regressions, gate
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

## License

CC BY-NC 4.0 — see [LICENSE](LICENSE).
