# AI Decisions

## 2026-05-09 — Phase 1 Skeleton First

- Decision: Implement the repository file structure and a thin GitHub Actions harness before parser, prompt, or state-machine work.
- Reason: The V1 design explicitly orders development as skeleton, command parser, prompt renderer, state machine, evidence checker, and Kakao notification.
- Consequence: The first workflow validates relay files and summarizes state, but does not yet post live `@claude` or `@codex` comments.
