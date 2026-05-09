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


### Risk 3
- Problem: Local validation can pass while live GitHub Actions dispatch remains unverified when the container has no `gh` CLI, no authenticated GitHub API context, and no configured remote.
- Future Symptom: The harness may appear ready locally, but the repository owner may still not see a Run workflow button or may see a GitHub-only workflow validation error.
- Fix: Push the branch to GitHub, run the PR check or `workflow_dispatch` from the GitHub UI/API, and record the live run result in `AI_EVIDENCE.md`.
