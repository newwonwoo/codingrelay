# AI Relay Orchestrator V1 Implementation Plan

This plan follows `ai_relay_orchestrator_v1.md` and intentionally stays inside the MVP scope.

## MVP Boundaries

### Include

1. GitHub Issue/PR comment command parsing.
2. `AI_RELAY_STATE.json` read/write.
3. `AI_BATON.md` required-section checks.
4. GitHub Actions test result reading.
5. `@claude` / `@codex` comment generation.
6. Self Verification Prompt rendering.
7. Receiver Acceptance Prompt rendering.
8. `max_rounds` and related stop-control limits.
9. Kakao notification integration point.

### Exclude

1. Dashboard UI.
2. Automatic merge.
3. Token-balance detection.
4. Full security audit automation.
5. Multi-repository control.
6. Complex permissions.
7. Built-in code editor.
8. Model performance scoring.

## Implementation Status (as of 2026-05-10)

| Phase | Status |
|---|---|
| 1. Skeleton + workflow | done |
| 2. Command parser (`status`, `start`, `handoff`, `plan`, `verify`, `dispatch`, `accept`, `reject`, `stop`, `fix`) | done |
| 3. Prompt renderer (work, self-verification, receiver, self-fix) | done |
| 4. State machine + `HUMAN_REQUIRED` enforcement | done |
| 5. Evidence/baton gate (`evaluate_handoff_gate`) auto-attached to `/relay verify` | done |
| 6. Kakao notification interface (`kakao_notify`) — webhook-driven, silent without `KAKAO_WEBHOOK_URL` | interface only |
| Regression CI gate (`.github/workflows/ai-relay-tests.yml`) | done |

## Phase 1 — Skeleton and Harness

Status: implemented in this change.

1. Create root relay files:
   - `AGENTS.md`
   - `AI_RELAY_CONTRACT.md`
   - `AI_RELAY_STATE.json`
   - `AI_BATON.md`
   - `AI_DECISIONS.md`
   - `AI_EVIDENCE.md`
   - `AI_RISKS.md`
   - `CLAUDE.md`
   - `CODEX.md`
2. Create `.github/workflows/ai-relay.yml` with the V1 trigger set.
3. Add a thin harness script that validates file presence, loads state, checks Baton sections, and writes a GitHub Actions summary.

## Phase 2 — Command Parser

1. Parse `/relay start` with `start_agent`, `next_agent`, and `goal` fields.
2. Parse `/relay status`.
3. Parse `/relay stop` with `reason`.
4. Parse `/relay handoff claude|codex`.
5. Add event payload fixtures for issue comments and PR comments.

## Phase 3 — Prompt Renderer

1. Render work prompts.
2. Render self-verification prompts.
3. Render receiver-acceptance prompts.
4. Render self-fix prompts.
5. Keep generated comments inspectable before posting.

## Phase 4 — State Machine

1. Implement `READY → WORKING`.
2. Implement `WORKING → SELF_VERIFYING`.
3. Implement `SELF_VERIFYING → RECEIVER_REVIEWING`.
4. Implement `RECEIVER_REVIEWING → WORKING` with agent swap.
5. Implement limit checks that move to `HUMAN_REQUIRED`.

## Phase 5 — Evidence Checker

1. Verify `AI_EVIDENCE.md` exists.
2. Verify `Commands Run` exists.
3. Verify `Results` exists.
4. Verify `Not Verified` exists.
5. Preserve failed-test visibility.

## Phase 6 — Kakao Notification

1. Add start notification formatting.
2. Add verification-pass formatting.
3. Add BLOCK formatting.
4. Add HUMAN_REQUIRED formatting.
5. Add DONE formatting.
