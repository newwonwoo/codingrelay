# AI Baton

## Task Goal
- Implement relay dispatch support for generating a work prompt from the current relay state and plan.

## Current Agent
- codex

## Next Agent
- claude

## Work Completed
- Added `/relay plan` parsing so goal, scope, out-of-scope, and done fields are overlaid onto the latest hidden relay state.
- Added `/relay dispatch` handling that reads the latest hidden state/plan and posts a dispatch prompt comment without invoking any AI provider or loading skills.
- Added regression tests for plan/dispatch command matching, state formatting, and issue-comment handling.
- Renamed the workflow run step to reflect that the harness now handles multiple relay commands.
- Updated relay evidence, risks, decisions, and baton files for this work.

## Changed Files
- .github/scripts/ai_relay_harness.py
- tests/test_ai_relay_harness.py
- .github/workflows/ai-relay.yml
- AI_BATON.md
- AI_EVIDENCE.md
- AI_RISKS.md
- AI_DECISIONS.md

## Decision Reasons
- Keep dispatch as prompt rendering only, matching the MVP boundary and the requested out-of-scope limits.
- Preserve hidden comment state as the source of truth so dispatch can use the same PR-thread state model as status and verify.

## Evidence
- Test: `python3 -m pytest -q`
- Build: Not applicable for this Python harness change.
- Lint: `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- Typecheck: Not applicable for this Python standard-library script.
- Manual Check: Verified tests cover `/relay plan` capture and `/relay dispatch` prompt generation from latest hidden state.

## Known Risks
- `/relay dispatch` only creates a prompt comment; it does not notify or invoke the named current agent.
- Plan parsing remains line-oriented and only supports single-line values for each plan field.

## Six-Month Failure Risks
- GitHub comment ordering or pagination behavior could change, causing dispatch to read an older hidden state.
- Users may expect `/relay plan` to immediately dispatch work; the MVP separates plan capture from `/relay dispatch` prompt generation.

## Receiver Compatibility Risks
- Next Agent may assume provider mentions or skill loading were added; they remain intentionally out of scope.

## Do Not Touch
- Do not add live `@codex`/`@claude` invocation, skill loading, dashboards, merge automation, or multi-repository orchestration for this MVP step.

## Next Actions
- Consider adding `/relay dispatch` documentation examples if the command surface is documented in a future follow-up.
- Run the workflow on GitHub after pushing to verify live comment posting in the PR thread.

## Handoff Status
PASS
