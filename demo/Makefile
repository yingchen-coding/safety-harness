# Agentic Safety Demo - Makefile
# One-command demo of the full closed-loop safety system

.PHONY: demo clean setup step1 step2 step3 step4 help

# Default target
.DEFAULT_GOAL := help

# Configuration
ROLLOUTS ?= 50
BASELINE ?= v1
CANDIDATE ?= v2

help:
	@echo "Agentic Safety Demo"
	@echo "==================="
	@echo ""
	@echo "Usage:"
	@echo "  make demo       Run full end-to-end demo"
	@echo "  make step1      Run stress tests only"
	@echo "  make step2      Generate regression tests"
	@echo "  make step3      Run release gate"
	@echo "  make step4      Replay incident"
	@echo "  make clean      Remove artifacts"
	@echo "  make setup      Install dependencies"
	@echo ""
	@echo "Options:"
	@echo "  ROLLOUTS=N      Number of stress test rollouts (default: 50)"
	@echo "  BASELINE=v      Baseline model version (default: v1)"
	@echo "  CANDIDATE=v     Candidate model version (default: v2)"

setup:
	pip install -r requirements.txt

clean:
	rm -rf artifacts/*.json artifacts/*.html
	@echo "Cleaned artifacts/"

step1:
	@echo ""
	@echo "=== Step 1: Stress Testing ==="
	@echo ""
	python scripts/step1_run_stress_tests.py --rollouts $(ROLLOUTS)

step2: artifacts/stress_failures.json
	@echo ""
	@echo "=== Step 2: Regression Generation ==="
	@echo ""
	python scripts/step2_generate_regression.py --input artifacts/stress_failures.json

step3: artifacts/regression_tests.json
	@echo ""
	@echo "=== Step 3: Release Gate ==="
	@echo ""
	-python scripts/step3_run_release_gate.py --baseline $(BASELINE) --candidate $(CANDIDATE)
	@echo ""
	@echo "Note: Exit code indicates verdict (0=OK, 1=WARN, 2=BLOCK)"

step4:
	@echo ""
	@echo "=== Step 4: Incident Replay ==="
	@echo ""
	python scripts/step4_replay_incident.py --incident artifacts/incident_example.json

demo: clean
	@echo "============================================================"
	@echo "       AGENTIC SAFETY DEMO - FULL CLOSED-LOOP SYSTEM        "
	@echo "============================================================"
	@echo ""
	@echo "This demo walks through:"
	@echo "  1. Discovering delayed failures via stress testing"
	@echo "  2. Converting failures into regression tests"
	@echo "  3. Gating a candidate model release"
	@echo "  4. Replaying a production incident"
	@echo ""
	@echo "Starting demo..."
	@echo ""
	$(MAKE) step1
	@echo ""
	$(MAKE) step2
	@echo ""
	$(MAKE) step3 || true
	@echo ""
	$(MAKE) step4
	@echo ""
	@echo "============================================================"
	@echo "                      DEMO COMPLETE                         "
	@echo "============================================================"
	@echo ""
	@echo "Generated artifacts:"
	@ls -la artifacts/ 2>/dev/null || echo "  (none)"
	@echo ""
	@echo "Next steps:"
	@echo "  - Review artifacts/gate_report.html in browser"
	@echo "  - Integrate step3 into CI/CD pipeline"
	@echo "  - Add incident replay to on-call runbooks"

# File dependencies
artifacts/stress_failures.json: step1
artifacts/regression_tests.json: step2
