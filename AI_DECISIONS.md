# AI Decisions

## 2026-05-09 — Phase 1 Skeleton First

- Decision: Implement the repository file structure and a thin GitHub Actions harness before parser, prompt, or state-machine work.
- Reason: The V1 design explicitly orders development as skeleton, command parser, prompt renderer, state machine, evidence checker, and Kakao notification.
- Consequence: The first workflow validates relay files and summarizes state, but does not yet post live `@claude` or `@codex` comments.

## 2026-05-10 — Dispatch Is Prompt Rendering Only

- Decision: Implement `/relay dispatch` as a comment prompt generator that reads the latest hidden state and plan, without live agent mentions, provider calls, or skill loading.
- Reason: The requested scope was to generate a work prompt from state and plan, while actual AI invocation and skill loading were explicitly out of scope.
- Consequence: Users must invoke or route the generated dispatch prompt themselves until a later orchestration phase adds safe live dispatch behavior.

## 2026-05-10 — Dispatch Command Does Not Mention Agents

- Decision: `/relay dispatch` renders a prompt addressed to the current agent by plain name and intentionally omits `@claude`/`@codex` mentions.
- Reason: The requested boundary is automatic-call-preparation, not actual agent invocation.
- Consequence: Humans can review/copy the generated dispatch prompt before any later automation step adds live mentions.
