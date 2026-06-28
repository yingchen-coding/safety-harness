# Security Review Checklist for Agentic Safety Systems

This checklist is intended for pre-production security and safety reviews of agentic systems and their safeguards.

## Scope

- Agent loop implementation
- Safeguards hooks (pre-action, mid-trajectory, post-action)
- Evaluation pipelines and release gating
- Telemetry, logging, and incident response

## Data & Privacy

- [ ] PII is not logged in raw form
- [ ] Logs are redacted or hashed for sensitive fields
- [ ] Production traffic replay uses anonymized data
- [ ] Data retention policy is defined and enforced
- [ ] Access control on evaluation datasets is role-based

## Model & API Security

- [ ] API keys stored in secrets manager (not in code or CI logs)
- [ ] Rate limits enforced per user / per IP
- [ ] Model endpoints restricted to allow-listed domains
- [ ] Prompt templates sanitized against injection via user input
- [ ] Tool invocation inputs validated and schema-checked

## Safeguards Robustness

- [ ] Pre-action detectors are resilient to simple obfuscation
- [ ] Trajectory monitors track cumulative risk signals
- [ ] Post-action verifiers validate outputs against policy
- [ ] Escalation policies are auditable and versioned
- [ ] Human override workflow is documented

## Infrastructure & Reliability

- [ ] Backpressure handling for eval workers
- [ ] Circuit breakers for model API failures
- [ ] Graceful degradation when safeguards fail closed/open
- [ ] Canary deployment for new safeguard versions
- [ ] Observability dashboards for safeguard effectiveness

## Release Governance

- [ ] Safety regression gating enforced in CI/CD
- [ ] Threshold changes require approval and audit trail
- [ ] Noise handling (multi-seed, CI stability) enabled
- [ ] Historical trends reviewed before release sign-off

## Incident Response Readiness

- [ ] On-call playbook documented
- [ ] Incident replay harness tested
- [ ] Root cause taxonomy defined
- [ ] Blast radius estimation implemented
- [ ] Regression test generation automated

## Threat Model Coverage

- [ ] Prompt injection
- [ ] Policy erosion over turns
- [ ] Coordinated multi-turn misuse
- [ ] Tool hallucination and misuse
- [ ] Detector gaming / evasion

## Sign-Off

- Security: ____________________   Date: ________
- Safety:   ____________________   Date: ________
- Infra:    ____________________   Date: ________
- Product:  ____________________   Date: ________
