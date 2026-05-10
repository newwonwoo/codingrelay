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

## 2026-05-10 — Stage 7: Isolate kakao_notify Failures From Workflow Exit Code

- Decision: `kakao_notify` swallows all delivery exceptions and returns `False` instead of propagating. The HUMAN_REQUIRED branch already posts the GitHub comment before calling `kakao_notify`, so isolating the network failure preserves the relay state on GitHub while preventing a red workflow run from a transient kakao outage.
- Reason: A red workflow run after relay state was successfully persisted is a false positive that erodes trust in the relay status check. The kakao notification is best-effort by design (V1 boundary — "live kakao delivery is opt-in, secret-backed").
- Consequence: Operators who treat a red Actions run as the canary for "human attention needed" must instead read the `[AI Relay 사람 판단 필요]` GitHub comment. Stderr logs from a failed `kakao_notify` are visible in the Actions run logs for debugging.

## 2026-05-10 — Stage 6: Land Risks 7-10 Fixes In One Round

- Decision: Implement all four deferred risks (network retry, hidden-state hijack guard, DONE→start continuity, code-block marker collision) in a single round with their tests, since the prototype is still pre-formal.
- Reason: Each risk's fix is localized and testable in isolation; bundling them avoids four separate review cycles for a project still in V1.
- Consequence: 11 new tests, public signatures unchanged, 80 total tests passing. Risk 11 (kakao network failure cascading to red workflow) was identified during this stage and deferred since no test exercises the live network path.

## 2026-05-10 — Stage 1-5: V1 Surface Completion

- Decision: Land the remaining V1 commands (`accept`, `reject`, `stop`, `fix`), the automated baton/evidence gate, the limit-breach `HUMAN_REQUIRED` transition, the kakao notification interface, and the regression CI gate as five sequential commits, each with its own tests.
- Reason: Each stage's diff stays reviewable in isolation; if a regression is found later, `git bisect` lands on a single stage. Public signatures stay stable across stages so the test suite grows monotonically (26→35→47→56→65→69) without churning earlier assertions.
- Consequence: V1 of `ai_relay_orchestrator_v1.md` §24 is met except for live kakao delivery (interface only — opt-in via `KAKAO_WEBHOOK_URL`). Tragic-failure audit findings that needed more design (network retry, hidden-state hijack guard, DONE→start round continuity, code-block marker collision) are documented as Risks 7-10 for the next round.

## 2026-05-10 — Adopt f29e3c2 As Base For Merge Conflict Recovery

- Decision: After PR #16's bad merge left both `ai_relay_harness.py` and `test_ai_relay_harness.py` un-importable, restore both files verbatim from commit `f29e3c2` ("Add relay dispatch prompt command") rather than hand-merging `f29e3c2` and `0c6e662` ("Add relay dry-run fixture tests") in one round.
- Reason: `f29e3c2`'s design (separate `AI_RELAY_PLAN` hidden marker, `format_dispatch_comment(state, plan)` signature) matches what `AI_BATON.md`, `AI_DECISIONS.md`, and the existing `tests/fixtures/issue_comment_dispatch.json` already document as the intended direction. Smallest safe change per `AGENTS.md`. The dry-run CLI from `0c6e662` is purely additive and can be re-introduced cleanly on top of this base in a follow-up round.
- Consequence: The `--dry-run`, `--comments-path`, `--summary` flags from `0c6e662` are temporarily absent from `main`. Anyone who relied on the local dry-run path must wait for the follow-up round or invoke the harness via the GitHub Actions workflow path.
