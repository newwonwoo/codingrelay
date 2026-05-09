# AI Risks

## Six-Month Failure Risks

### Risk 1
- Problem: GitHub event payload handling is currently skeletal.
- Future Symptom: `/relay` commands may be ignored or misclassified when Phase 2 begins.
- Fix: Add command-parser fixtures for issue comments, PR events, workflow runs, and manual dispatch.

### Risk 2
- Problem: Kakao notification is not wired to a provider yet.
- Future Symptom: HUMAN_REQUIRED status may not alert a human outside GitHub.
- Fix: Add a provider interface and secret-backed sender in the Kakao notification phase.

## Receiver Compatibility Risks

### Risk 1
- Problem: Phase 1 creates only the structure and validation harness, not the full orchestrator.
- Why Next Agent May Misunderstand: The presence of workflow files may look like complete automation.
- Fix: Keep MVP boundaries explicit in `docs/ai-relay-v1-implementation-plan.md` and relay evidence files.
